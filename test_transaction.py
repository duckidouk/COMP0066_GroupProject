"""Checks for transaction() in admin_cli_prototype.py.

Run:  python3 test_transaction.py

Every check uses a temporary database FILE. A :memory: database exists only inside one connection,
so a test with two connections cannot work there.
"""
import ast
import builtins
import contextlib
import io
import os
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import admin_cli_prototype as app

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + (f"   [{detail}]" if detail else ""))


def setup():
    """A new database file with the prototype schema and sample data. Returns (path, conn, ids)."""
    path = os.path.join(tempfile.mkdtemp(), "test.db")
    conn = app.connect(path)
    conn.executescript(Path(app.SCHEMA).read_text(encoding="utf-8-sig"))
    app.seed(conn)
    ids = dict(conn.execute("SELECT username, user_id FROM users"))
    return path, conn, ids


def one(conn, sql, *params):
    return conn.execute(sql, params).fetchone()[0]


def run(conn, answers, fn, *args):
    """Run a screen with typed answers. Also records, for every prompt, if a transaction was open."""
    feed, out, real_input = iter(answers), io.StringIO(), builtins.input
    def fake_input(prompt=""):
        open_during_prompt.append(conn.in_transaction)
        print(prompt, end="", file=out)
        try:
            return next(feed)
        except StopIteration:                       # the screen asked more questions than expected
            raise EOFError("the test ran out of answers")
    builtins.input = fake_input
    try:
        with contextlib.redirect_stdout(out):
            fn(*args)
    except EOFError:
        out.write("\n[the test ran out of answers]\n")
    finally:
        builtins.input = real_input
    return out.getvalue()


def patient_no(conn, name):
    """The number of a patient in the patient lists (they are sorted by user_id)."""
    names = [r[0] for r in conn.execute("SELECT name FROM users WHERE role = 'patient' ORDER BY user_id")]
    return str(names.index(name) + 1)


def mhwp_no(conn, name, exclude_id=None):
    """The number of an MHWP in pick_mhwp (active MHWPs sorted by user_id, without the current one)."""
    names = [r[0] for r in conn.execute(
        "SELECT name FROM users WHERE role = 'practitioner' AND account_status = 'active' AND user_id != ? "
        "ORDER BY user_id", (exclude_id or -1,))]
    return str(names.index(name) + 1)


app.set_now(datetime(2026, 11, 12, 10, 0))
open_during_prompt = []

# ---------------------------------------------------------------- 1. the lock (two connections, one file)
path, A, ids = setup()
B = app.connect(path, timeout=0.2)
with app.transaction(A):
    A.execute("SELECT account_status FROM users WHERE user_id = ?", (ids["mhwp3"],)).fetchone()
    check("lock: A is in a transaction after its first read", A.in_transaction)
    try:
        B.execute("UPDATE users SET account_status = 'disabled' WHERE user_id = ?", (ids["mhwp3"],))
        check("lock: B cannot write between A's check and A's change", False, "B's write was allowed")
    except sqlite3.OperationalError as e:
        check("lock: B cannot write between A's check and A's change", "locked" in str(e), str(e))
check("lock: A's transaction is closed after the with block", not A.in_transaction)
B.execute("UPDATE users SET name = name WHERE user_id = ?", (ids["mhwp3"],))
check("lock: B can write again after A finished", True)

# ---------------------------------------------------------------- 2. never wait for input inside a transaction
# static check: no ask or input call is written inside any "with transaction(...)" block
tree = ast.parse(Path(app.__file__).read_text(encoding="utf-8"))
asks_inside = []
for node in ast.walk(tree):
    if isinstance(node, ast.With) and any(isinstance(i.context_expr, ast.Call)
                                          and getattr(i.context_expr.func, "id", "") == "transaction"
                                          for i in node.items):
        for call in ast.walk(node):
            if isinstance(call, ast.Call) and getattr(call.func, "id", "").startswith(("ask", "input")):
                asks_inside.append(call.func.id)
check("no input: no ask or input call is written inside a transaction block", not asks_inside, asks_inside)

# real screens: at every prompt, no transaction may be open
path, conn, ids = setup()
open_during_prompt.clear()
okafor = ids["mhwp3"]
flows = [
    ("allocate Sam Doyle", app.screen_allocations,
     lambda: [patient_no(conn, "Sam Doyle"), mhwp_no(conn, "Dr Chloe Tan"), "y", "0"]),
    ("reallocate Noah Green", app.screen_allocations,
     lambda: [patient_no(conn, "Noah Green"), mhwp_no(conn, "Dr Ben Hughes", exclude_id=okafor), "y", "0"]),
    ("edit Lucy Fraser's name", app.screen_users,
     lambda: ["2", patient_no(conn, "Lucy Fraser"), "1", "1", "Lucy Grey", "0", "0"]),
    ("disable Omar Haddad", app.screen_users, lambda: ["2", patient_no(conn, "Omar Haddad"), "3", "y", "0", "0"]),
    ("re enable Omar Haddad", app.screen_users, lambda: ["2", patient_no(conn, "Omar Haddad"), "1", "0", "0"]),
    ("delete Hana Kim", app.screen_users, lambda: ["2", patient_no(conn, "Hana Kim"), "2", "y", "0", "0"]),
]
done = 0
for name, screen, answers in flows:
    text = run(conn, answers(), screen, conn)
    if "Done." in text:
        done += 1
    else:
        check(f"no input: the flow '{name}' worked", False, text[-200:])
check("no input: all six action screens finished their change", done == len(flows), f"{done} of {len(flows)}")
check(f"no input: no transaction was open at any of the {len(open_during_prompt)} prompts",
      len(open_during_prompt) > 20 and not any(open_during_prompt))
check("no input: the six changes were saved",
      one(conn, "SELECT u.name FROM patient_profiles pp JOIN users u ON u.user_id = pp.assigned_practitioner_id "
                "WHERE pp.patient_id = ?", ids["patient17"]) == "Dr Chloe Tan"
      and one(conn, "SELECT name FROM users WHERE user_id = ?", ids["patient18"]) == "Lucy Grey"
      and one(conn, "SELECT account_status FROM users WHERE user_id = ?", ids["patient8"]) == "active"
      and one(conn, "SELECT COUNT(*) FROM users WHERE user_id = ?", ids["patient7"]) == 0)

# ---------------------------------------------------------------- 3. nested use joins the open transaction
path, conn, ids = setup()
pid = ids["patient3"]
try:
    with app.transaction(conn):
        conn.execute("UPDATE users SET name = 'Outer' WHERE user_id = ?", (pid,))
        with app.transaction(conn):
            conn.execute("UPDATE users SET email = 'inner@therapylink.test' WHERE user_id = ?", (pid,))
    nested_ok = True
except sqlite3.OperationalError as e:
    nested_ok = False
check("nested: a transaction inside a transaction gives no error", nested_ok)
check("nested: both changes are saved, and the transaction is closed",
      one(conn, "SELECT name || ' ' || email FROM users WHERE user_id = ?", pid) == "Outer inner@therapylink.test"
      and not conn.in_transaction)
try:
    with app.transaction(conn):
        conn.execute("UPDATE users SET name = 'Should go' WHERE user_id = ?", (pid,))
        with app.transaction(conn):
            conn.execute("UPDATE users SET email = 'gone@therapylink.test' WHERE user_id = ?", (pid,))
            raise app.Refused("a rule says no")
except app.Refused:
    pass
check("nested: an error in the inner part undoes the outer change too",
      one(conn, "SELECT name || ' ' || email FROM users WHERE user_id = ?", pid) == "Outer inner@therapylink.test"
      and not conn.in_transaction)
with app.transaction(conn):
    app.disable_user(conn, ids["patient4"])         # a real action function inside a transaction
check("nested: a real action (disable_user) works inside another transaction",
      one(conn, "SELECT account_status FROM users WHERE user_id = ?", ids["patient4"]) == "disabled")

# ---------------------------------------------------------------- 4. a busy database gives a friendly message
path, A, ids = setup()
B = app.connect(path, timeout=0.2)                  # short wait, so the test is fast
A.execute("BEGIN IMMEDIATE")                        # another writer holds the lock
open_during_prompt.clear()
text = run(B, [patient_no(B, "Sam Doyle"), mhwp_no(B, "Dr Chloe Tan"), "y", "0"], app.screen_allocations, B)
A.execute("ROLLBACK")
check("busy: the screen says the database is busy", "Nothing was changed. The database is busy, try again." in text)
check("busy: no Python error text on the screen", "Traceback" not in text and "OperationalError" not in text)
check("busy: nothing was saved",
      one(B, "SELECT assigned_practitioner_id FROM patient_profiles WHERE patient_id = ?", ids["patient17"]) is None)
text = run(B, [patient_no(B, "Sam Doyle"), mhwp_no(B, "Dr Chloe Tan"), "y", "0"], app.screen_allocations, B)
check("busy: after the other writer finished, the same action works", "Done. Sam Doyle is now allocated" in text)
check("busy: problem_text keeps other messages as they are", app.problem_text(app.Refused("No.")) == "No.")

# ---------------------------------------------------------------- 5. a crash in the middle saves nothing
path, conn, ids = setup()
pid = ids["patient4"]                               # Liam Walker: has a future booking with his MHWP
state = lambda c: (one(c, "SELECT assigned_practitioner_id FROM patient_profiles WHERE patient_id = ?", pid),
                   one(c, "SELECT COUNT(*) FROM appointments WHERE patient_id = ? AND status = 'cancelled'", pid),
                   one(c, "SELECT COUNT(*) FROM emails"))
before = state(conn)
real, calls = app.write_email, {"n": 0}
def flaky(*args):
    calls["n"] += 1
    if calls["n"] == 2:                             # the first email is written, the second one fails
        raise sqlite3.OperationalError("disk full (simulated)")
    return real(*args)
app.write_email = flaky
try:
    app.reallocate(conn, pid, ids["mhwp4"])
except sqlite3.OperationalError:
    pass
app.write_email = real
other = app.connect(path)                           # a second connection reads the file itself
check("crash: the reallocation reached the second email before it failed", calls["n"] == 2)
check("crash: a second connection sees the database exactly as before", state(other) == before,
      f"before {before}, after {state(other)}")
check("crash: the transaction is closed after the error", not conn.in_transaction)

print(f"\n{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
