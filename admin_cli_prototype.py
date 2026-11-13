"""TherapyLink admin screens: a sketch of the command line interface, not the final app.

Run by itself:     python admin_cli_prototype.py            (real keyboard input)
Run the demo:      python admin_cli_prototype.py --demo     (scripted session, fixed date)

Needs only core Python (sqlite3), plus Pandas for the reports.
The schema is read from schema_stats.sql in the same folder.
"""
import calendar
import os
import random
import re
import sqlite3
import sys
from datetime import datetime, timedelta

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "schema_stats.sql")
DB = os.environ.get("DB_PATH", os.path.join(HERE, "therapylink_demo.db"))

# A fixed "now" keeps the demo repeatable. The real app would use datetime.now().
NOW = datetime(2026, 11, 12, 10, 0)

ROLE = {"admin": "admin", "practitioner": "MHWP", "patient": "patient"}
GENDERS = [("female", "female"), ("male", "male"),
           ("non_binary", "non binary"), ("prefer_not_to_say", "prefer not to say")]
GENDER_LABEL = dict(GENDERS)
MIN_GROUP = 3          # smaller groups are hidden in the reports
WIDTH = 58


class Refused(Exception):
    """A rule of the app says no. Nothing has been changed."""


# ---------------------------------------------------------------- small helpers
def ts(d):
    return d.strftime("%Y-%m-%d %H:%M")


def show(t):
    return datetime.strptime(t, "%Y-%m-%d %H:%M").strftime("%a %d %b %H:%M")


def show_date(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y") if iso else "not given"


def week_bounds():
    monday = (NOW - timedelta(days=NOW.weekday())).replace(hour=0, minute=0)
    return monday, monday + timedelta(days=7)


def heading(text):
    print("\n" + "=" * WIDTH)
    print(" " + text)
    print("=" * WIDTH)


def frame(conn, sql, params=()):
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return pd.DataFrame([tuple(r) for r in cur.fetchall()], columns=cols)


# ---------------------------------------------------------------- input (A9)
SCRIPT = None          # a list of scripted answers when running the demo
CURRENT = {}           # name -> menu number, so the demo can say "@Hana Kim"


def set_menu(names):
    CURRENT.clear()
    CURRENT.update({n: i for i, n in enumerate(names, 1)})


def ask(prompt):
    if SCRIPT is None:
        return input(prompt).strip()
    if not SCRIPT:
        raise SystemExit("[demo script ended]")
    v = SCRIPT.pop(0)
    if v.startswith("@"):
        v = str(CURRENT[v[1:]])
    print(prompt + v)
    return v.strip()


def ask_number(prompt, lo, hi):
    while True:
        v = ask(prompt)
        if v.isdigit() and lo <= int(v) <= hi:
            return int(v)
        print(f"  Please type a number from {lo} to {hi}.")


def ask_yes_no(prompt):
    while True:
        v = ask(prompt).lower()
        if v in ("y", "n"):
            return v == "y"
        print("  Please type y or n (capital Y or N also work).")


def ask_valid(prompt, parser):
    while True:
        value, problem = parser(ask(prompt))
        if problem is None:
            return value
        print("  " + problem)


def parse_name(v):
    if not v or len(v) > 60:
        return None, "The name must be 1 to 60 characters."
    return v, None


def parse_email(v):
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
        return None, "That is not an email address. Example: name@example.org"
    return v, None


def parse_dob(v):
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", v)
    if not m:
        return None, "Use the form DD/MM/YYYY, for example 14/03/1992."
    day, month, year = map(int, m.groups())
    if year < 1900:
        return None, "The year must be 1900 or later."
    if not 1 <= month <= 12:
        return None, "The month must be from 1 to 12."
    last = calendar.monthrange(year, month)[1]     # knows leap years: February is 29 in 2024, 28 in 2026
    if not 1 <= day <= last:
        return None, f"{calendar.month_name[month]} {year} has {last} days, so {day} is not a valid day."
    d = datetime(year, month, day)
    if d > NOW:
        return None, "A date of birth cannot be in the future."
    return d.strftime("%Y-%m-%d"), None


# ---------------------------------------------------------------- database
def connect(path=DB):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")      # off by default, so set it on every connection
    conn.row_factory = sqlite3.Row
    return conn


def get_user(conn, uid):
    return conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()


def live_rows(conn, user_id=None, patient_id=None, practitioner_id=None):
    """Future requested or confirmed bookings, optionally filtered."""
    sql = """SELECT a.*, p.name AS pname, p.email AS pemail, m.name AS mname, m.email AS memail
             FROM appointments a
             JOIN users p ON p.user_id = a.patient_id
             JOIN users m ON m.user_id = a.practitioner_id
             WHERE a.status IN ('requested','confirmed') AND a.scheduled_time > ?"""
    params = [ts(NOW)]
    if user_id is not None:
        sql += " AND (a.patient_id=? OR a.practitioner_id=?)"
        params += [user_id, user_id]
    if patient_id is not None:
        sql += " AND a.patient_id=?"
        params.append(patient_id)
    if practitioner_id is not None:
        sql += " AND a.practitioner_id=?"
        params.append(practitioner_id)
    return conn.execute(sql + " ORDER BY a.scheduled_time", params).fetchall()


def write_email(conn, to_user_id, address, subject, body):
    conn.execute("INSERT INTO emails(to_user_id,to_address,subject,body,sent_at) VALUES (?,?,?,?,?)",
                 (to_user_id, address, subject, body, ts(NOW)))


def cancel_and_email(conn, rows, reason):
    """Call inside a transaction. Cancels each booking and emails both sides."""
    for r in rows:
        conn.execute("UPDATE appointments SET status='cancelled' WHERE appointment_id=?",
                     (r["appointment_id"],))
        when = show(r["scheduled_time"])
        subject = f"Appointment cancelled: {when}"
        body = (f"The appointment on {when} between {r['pname']} and {r['mname']} "
                f"was cancelled because {reason}.")
        write_email(conn, r["patient_id"], r["pemail"], subject, body)
        write_email(conn, r["practitioner_id"], r["memail"], subject, body)
    return len(rows)


def guard_admin(u):
    if u["role"] == "admin":
        raise Refused("The admin account is protected. It cannot be edited, disabled or deleted.")


def allocate(conn, patient_id, mhwp_id):
    with conn:
        conn.execute("UPDATE patient_profiles SET assigned_practitioner_id=? WHERE patient_id=?",
                     (mhwp_id, patient_id))


def reallocate(conn, patient_id, new_mhwp_id):
    with conn:                                    # one transaction: all or nothing
        old = conn.execute("SELECT assigned_practitioner_id FROM patient_profiles WHERE patient_id=?",
                           (patient_id,)).fetchone()[0]
        rows = live_rows(conn, patient_id=patient_id, practitioner_id=old) if old else []
        n = cancel_and_email(conn, rows, "the patient was reallocated to another MHWP")
        conn.execute("UPDATE patient_profiles SET assigned_practitioner_id=? WHERE patient_id=?",
                     (new_mhwp_id, patient_id))
    return n


def update_field(conn, uid, col, value):
    if col not in {"name", "email", "gender", "date_of_birth"}:
        raise ValueError(col)
    with conn:
        u = get_user(conn, uid)
        guard_admin(u)
        if u["account_status"] == "disabled":
            raise Refused("A disabled user cannot be edited. Re enable first.")
        conn.execute(f"UPDATE users SET {col}=? WHERE user_id=?", (value, uid))


def delete_user(conn, uid):
    with conn:
        u = get_user(conn, uid)
        guard_admin(u)
        rows = live_rows(conn, user_id=uid)
        n = cancel_and_email(conn, rows, f"the account of {u['name']} was deleted")
        conn.execute("DELETE FROM users WHERE user_id=?", (uid,))
    return n


def disable_user(conn, uid):
    with conn:
        u = get_user(conn, uid)
        guard_admin(u)
        if u["account_status"] == "disabled":
            raise Refused("This user is already disabled.")
        rows = live_rows(conn, user_id=uid)
        n = cancel_and_email(conn, rows, f"the account of {u['name']} was disabled")
        if u["role"] == "patient":
            conn.execute("UPDATE patient_profiles SET assigned_practitioner_id=NULL WHERE patient_id=?", (uid,))
        else:
            conn.execute("UPDATE patient_profiles SET assigned_practitioner_id=NULL "
                         "WHERE assigned_practitioner_id=?", (uid,))
        conn.execute("UPDATE users SET account_status='disabled', disabled_at=? WHERE user_id=?",
                     (ts(NOW), uid))
    return n


def reenable_user(conn, uid):
    with conn:
        u = get_user(conn, uid)
        if u["account_status"] != "disabled":
            raise Refused("This user is not disabled.")
        conn.execute("UPDATE users SET account_status='active', disabled_at=NULL WHERE user_id=?", (uid,))


# ---------------------------------------------------------------- seed data
def seed(conn):
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return                                    # seed only when users is empty
    rng = random.Random(7)
    created = "2026-09-01 09:00"

    def add_user(username, name, role, gender=None, dob=None, status="active", password=""):
        cur = conn.execute(
            "INSERT INTO users(username,password,name,email,role,account_status,created_at,disabled_at,"
            "gender,date_of_birth) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (username, password, name, f"{username}@example.org", role, status, created,
             "2026-10-20 09:00" if status == "disabled" else None, gender, dob))
        return cur.lastrowid

    with conn:
        add_user("admin1", "Alex Admin", "admin", password="admin")
        m = [add_user("mhwp1", "Dr Amara Okafor", "practitioner"),
             add_user("mhwp2", "Dr Ben Hughes", "practitioner"),
             add_user("mhwp3", "Dr Chloe Tan", "practitioner")]
        add_user("mhwp4", "Dr Dana Reid", "practitioner", status="disabled")

        names = ["Maya Patel", "Liam Walker", "Sofia Rossi", "Noah Green", "Hana Kim", "Omar Haddad",
                 "Ella Brooks", "Jack Murphy", "Zara Ahmed", "Grace Lee", "Tom Evans", "Robin Clarke",
                 "Isla Grant", "Ravi Menon", "Sam Doyle", "Lucy Fraser", "Kit Morgan", "Daniel Cole"]
        genders = "F M F N F M F M P F M N F M N F P M".split()
        gmap = {"F": "female", "M": "male", "N": "non_binary", "P": "prefer_not_to_say"}
        years = [2005, 2003, 2001, 1999, 1998, 1996, 1995, 1993, 1991, 1989,
                 1986, 1984, 1981, 1978, 1975, 1972, 1968, 1964]
        pid = []
        for i, nm in enumerate(names):
            dob = f"{years[i]}-{(i * 5) % 12 + 1:02d}-{(i * 7) % 27 + 1:02d}"
            status = "disabled" if nm == "Daniel Cole" else "active"
            pid.append(add_user(f"pat{i + 1:02d}", nm, "patient", gmap[genders[i]], dob, status))

        # allocations: 6 / 5 / 3, then three unallocated patients, then one disabled patient
        owner = [0] * 6 + [1] * 5 + [2] * 3 + [None] * 4
        for i, p in enumerate(pid):
            conn.execute("INSERT INTO patient_profiles(patient_id, emergency_contact_email, "
                         "assigned_practitioner_id) VALUES (?,?,?)",
                         (p, f"contact{i + 1}@example.org", m[owner[i]] if owner[i] is not None else None))

        def appt(pi, mi, when, status):
            conn.execute("INSERT INTO appointments(patient_id,practitioner_id,scheduled_time,status,created_at) "
                         "VALUES (?,?,?,?,?)", (pid[pi], m[mi], when, status, "2026-11-02 09:00"))

        for pi, mi, when, st in [
            (0, 0, "2026-11-09 10:00", "confirmed"), (0, 0, "2026-11-13 09:00", "confirmed"),
            (0, 0, "2026-11-11 09:00", "cancelled"),
            (1, 0, "2026-11-11 11:00", "confirmed"), (1, 0, "2026-11-17 14:00", "requested"),
            (2, 0, "2026-11-13 11:00", "confirmed"),
            (3, 0, "2026-11-13 14:00", "confirmed"), (3, 0, "2026-11-18 10:00", "requested"),
            (4, 0, "2026-11-13 15:00", "confirmed"), (4, 0, "2026-11-16 09:00", "confirmed"),
            (5, 0, "2026-11-19 13:00", "requested"),
            (6, 1, "2026-11-10 09:00", "confirmed"), (6, 1, "2026-11-13 10:00", "confirmed"),
            (7, 1, "2026-11-16 15:00", "confirmed"),
            (8, 1, "2026-11-12 14:00", "confirmed"),
            (9, 1, "2026-11-13 13:00", "requested"),
            (11, 2, "2026-11-12 16:00", "confirmed"),
            (12, 2, "2026-11-17 11:00", "confirmed"),
            (13, 2, "2026-11-09 13:00", "confirmed"), (13, 2, "2026-11-20 12:00", "requested"),
        ]:
            appt(pi, mi, when, st)

        # mood: one entry a day for 30 days, base 2 to 4 with noise of one point, so no accidental alerts
        series = {1: [2, 2, 3, 3, 5, 5, 5],       # Liam Walker: a rise of 3 inside 7 days
                  8: [3, 3, 4, 4, 6, 5, 4]}       # Zara Ahmed: a score of 6
        for i, p in enumerate(pid):
            if names[i] == "Daniel Cole":
                continue
            base = rng.randint(2, 4)
            for back in range(29, -1, -1):
                day = (NOW - timedelta(days=back)).replace(hour=8, minute=30)
                if back == 0 and i not in series and rng.random() < 0.25:
                    continue                      # some patients have not logged today yet
                score = base + rng.choice([-1, 0, 1])
                if i in series and back <= 6:
                    score = series[i][6 - back]
                conn.execute("INSERT INTO mood_entries(patient_id,score,comment,created_at) VALUES (?,?,?,?)",
                             (p, score, None, ts(day)))


# ---------------------------------------------------------------- screens: login and menu
def login(conn):
    heading("THERAPYLINK LOGIN")
    while True:
        username = ask("Username: ")
        password = ask("Password: ")
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if row and row["password"] == password:
            break
        print("  Wrong username or password. Try again.\n")
    if row["role"] != "admin":
        print("  (The patient and MHWP menus are separate screens.)")
        return None
    return row


def admin_menu(conn, admin):
    while True:
        heading("ADMIN MENU")
        print(f"  Logged in as {admin['name']} ({admin['username']})")
        print("   1  Manage allocations\n   2  Manage users\n   3  View reports\n   4  Log out")
        c = ask_number("Choose 1 to 4: ", 1, 4)
        if c == 1:
            screen_allocations(conn)
        elif c == 2:
            screen_users(conn)
        elif c == 3:
            screen_reports(conn)
        else:
            heading("LOG OUT")
            print("  You have been logged out.")
            return


# ---------------------------------------------------------------- allocations (A2, A2b)
def bookings_block(rows):
    if not rows:
        print("Future bookings to cancel: none")
        return
    print(f"Future bookings to cancel, with an email to both sides: {len(rows)}")
    for r in rows:
        print(f"   {show(r['scheduled_time'])}  {r['pname']} with {r['mname']} ({r['status']})")


def pick_mhwp(conn, exclude_id=None):
    rows = conn.execute("""SELECT u.user_id, u.name,
             (SELECT COUNT(*) FROM patient_profiles pp WHERE pp.assigned_practitioner_id = u.user_id) AS n
             FROM users u WHERE u.role='practitioner' AND u.account_status='active' AND u.user_id != ?
             ORDER BY u.user_id""", (exclude_id or -1,)).fetchall()
    print("Active MHWPs (a disabled MHWP is not offered)")
    print(f"{'No':>3}  {'MHWP':<20}{'Patients':>8}")
    for i, r in enumerate(rows, 1):
        print(f"{i:>3}  {r['name']:<20}{r['n']:>8}")
    set_menu([r["name"] for r in rows])
    n = ask_number("Choose an MHWP number, or 0 to cancel: ", 0, len(rows))
    return rows[n - 1] if n else None


def screen_allocations(conn):
    while True:
        rows = conn.execute("""SELECT u.user_id, u.name, u.account_status, m.name AS mname
                 FROM users u LEFT JOIN patient_profiles pp ON pp.patient_id = u.user_id
                 LEFT JOIN users m ON m.user_id = pp.assigned_practitioner_id
                 WHERE u.role='patient' ORDER BY u.user_id""").fetchall()
        heading("MANAGE ALLOCATIONS")
        print(f"{'No':>3}  {'Patient':<18}{'Status':<10}{'MHWP'}")
        for i, r in enumerate(rows, 1):
            print(f"{i:>3}  {r['name']:<18}{r['account_status']:<10}{r['mname'] or 'none'}")
        set_menu([r["name"] for r in rows])
        n = ask_number("Choose a patient number, or 0 to go back: ", 0, len(rows))
        if n == 0:
            return
        p = rows[n - 1]
        try:
            if p["account_status"] == "disabled":
                raise Refused(f"{p['name']} is disabled. Re enable the account first.")
            if p["mname"] is None:
                a2_allocate(conn, p)
            else:
                a2b_reallocate(conn, p)
        except (Refused, sqlite3.Error) as e:
            print(f"\n  Nothing was changed. {e}")


def a2_allocate(conn, p):
    print(f"\nALLOCATE: {p['name']} has no MHWP")
    m = pick_mhwp(conn)
    if m is None:
        print("  Cancelled.")
        return
    print(f"\nAllocating {p['name']} to {m['name']}.")
    if not ask_yes_no(f"Are you sure? (y/n): "):
        print("  Nothing was changed.")
        return
    allocate(conn, p["user_id"], m["user_id"])
    print(f"\n  Done. {p['name']} is now allocated to {m['name']}.")


def a2b_reallocate(conn, p):
    cur = conn.execute("SELECT assigned_practitioner_id AS a FROM patient_profiles WHERE patient_id=?",
                       (p["user_id"],)).fetchone()["a"]
    print(f"\nREALLOCATE: {p['name']} is with {p['mname']}")
    m = pick_mhwp(conn, exclude_id=cur)
    if m is None:
        print("  Cancelled.")
        return
    rows = live_rows(conn, patient_id=p["user_id"], practitioner_id=cur)
    print(f"\nMoving {p['name']} from {p['mname']} to {m['name']}.")
    bookings_block(rows)                          # prints "none" when there are no bookings
    if not ask_yes_no("Are you sure? (y/n): "):
        print("  Nothing was changed.")
        return
    n = reallocate(conn, p["user_id"], m["user_id"])
    msg = f"  Done. {p['name']} is now allocated to {m['name']}."
    if n:
        msg += f"\n  {n} booking{'s' if n != 1 else ''} cancelled, {2 * n} emails written."
    print("\n" + msg)


# ---------------------------------------------------------------- users (A1, A3, A4, A5, A6)
def screen_users(conn):
    """First choose MHWPs or patients, then work in that list."""
    while True:
        heading("MANAGE USERS")
        counts = dict(conn.execute("SELECT role, COUNT(*) FROM users GROUP BY role").fetchall())
        print(f"   1  MHWPs ({counts.get('practitioner', 0)})")
        print(f"   2  Patients ({counts.get('patient', 0)})")
        print("   0  Back")
        print("  The admin account is protected and is not listed.")      # A1
        c = ask_number("Choose 1, 2 or 0: ", 0, 2)
        if c == 0:
            return
        user_list(conn, "practitioner" if c == 1 else "patient")


def user_list(conn, role):
    """List the MHWPs or the patients, and act on the one chosen."""
    while True:
        if role == "practitioner":
            heading("MANAGE USERS: MHWPs")
            rows = conn.execute("""SELECT u.*,
                     (SELECT COUNT(*) FROM patient_profiles pp
                      WHERE pp.assigned_practitioner_id = u.user_id) AS extra
                     FROM users u WHERE u.role = 'practitioner' ORDER BY u.user_id""").fetchall()
            extra_label = "Patients"
        else:
            heading("MANAGE USERS: PATIENTS")
            rows = conn.execute("""SELECT u.*, COALESCE(m.name, 'none') AS extra
                     FROM users u
                     LEFT JOIN patient_profiles pp ON pp.patient_id = u.user_id
                     LEFT JOIN users m ON m.user_id = pp.assigned_practitioner_id
                     WHERE u.role = 'patient' ORDER BY u.user_id""").fetchall()
            extra_label = "MHWP"
        if not rows:
            print("  There is nobody in this list.")
            return
        print(f"{'No':>3}  {'Name':<18}{'Status':<10}{extra_label}")
        for i, r in enumerate(rows, 1):
            print(f"{i:>3}  {r['name']:<18}{r['account_status']:<10}{r['extra']}")
        set_menu([r["name"] for r in rows])
        n = ask_number("Choose a user number, or 0 to go back: ", 0, len(rows))
        if n == 0:
            return
        u = rows[n - 1]
        try:
            guard_admin(u)                         # A1: never true here, kept as a safety net
            user_actions(conn, u["user_id"])
        except (Refused, sqlite3.Error) as e:
            print(f"\n  Nothing was changed. {e}")


def user_actions(conn, uid):
    u = get_user(conn, uid)
    heading(f"{u['name']} ({ROLE[u['role']]}, {u['account_status']})")
    if u["account_status"] == "active":
        print("   1  Edit details\n   2  Delete user\n   3  Disable user\n   0  Back")
        c = ask_number("Choose an action: ", 0, 3)
        {0: lambda: None, 1: lambda: a3_edit(conn, uid), 2: lambda: a4_delete(conn, uid),
         3: lambda: a5_disable(conn, uid)}[c]()
    else:
        print(f"  This account has been disabled since {show(u['disabled_at'])} and is frozen.")
        print("   1  Re enable user\n   2  Delete user\n   0  Back")
        c = ask_number("Choose an action: ", 0, 2)
        {0: lambda: None, 1: lambda: a6_reenable(conn, uid), 2: lambda: a4_delete(conn, uid)}[c]()


def a3_edit(conn, uid):
    u = get_user(conn, uid)
    fields = [("name", "Name"), ("email", "Email")]
    if u["role"] == "patient":
        fields += [("gender", "Gender"), ("date_of_birth", "Date of birth")]
    heading(f"EDIT USER: {u['name']} ({ROLE[u['role']]})")
    for i, (col, label) in enumerate(fields, 1):
        v = u[col]
        v = show_date(v) if col == "date_of_birth" else GENDER_LABEL.get(v, v) if col == "gender" else v
        print(f"{i:>3}  {label:<15}{v or 'not given'}")
    print("  0  Cancel")
    n = ask_number("Choose a field number: ", 0, len(fields))
    if n == 0:
        print("  Nothing was changed.")
        return
    col, label = fields[n - 1]
    old = u[col]
    if col == "gender":
        for i, (_, text) in enumerate(GENDERS, 1):
            print(f"{i:>3}  {text}")
        new = GENDERS[ask_number("Choose a gender number: ", 1, len(GENDERS)) - 1][0]
    elif col == "date_of_birth":
        new = ask_valid("New date of birth (DD/MM/YYYY): ", parse_dob)
    elif col == "email":
        new = ask_valid("New email: ", parse_email)
    else:
        new = ask_valid("New name: ", parse_name)
    update_field(conn, uid, col, new)
    fmt = (lambda v: show_date(v)) if col == "date_of_birth" else (lambda v: GENDER_LABEL.get(v, v))
    print(f"\n  Done. {label} for {u['name']} changed from {fmt(old)} to {fmt(new)}.")


def a4_delete(conn, uid):
    u = get_user(conn, uid)
    heading(f"DELETE USER: {u['name']} ({ROLE[u['role']]}, {u['account_status']})")
    q = lambda sql: conn.execute(sql, (uid,)).fetchone()[0]
    if u["role"] == "patient":
        print("This permanently removes the account and all of its data:")
        print(f"   mood entries {q('SELECT COUNT(*) FROM mood_entries WHERE patient_id=?')},"
              f" journal entries {q('SELECT COUNT(*) FROM journal_entries WHERE patient_id=?')},"
              f" notes {q('SELECT COUNT(*) FROM patient_notes WHERE patient_id=?')},"
              f" appointments {q('SELECT COUNT(*) FROM appointments WHERE patient_id=?')}")
    else:
        pats = [r["name"] for r in conn.execute(
            "SELECT u.name FROM patient_profiles pp JOIN users u ON u.user_id=pp.patient_id "
            "WHERE pp.assigned_practitioner_id=? ORDER BY u.user_id", (uid,))]
        print("This permanently removes the account.")
        print(f"   appointments with this MHWP, all dates, are deleted: "
              f"{q('SELECT COUNT(*) FROM appointments WHERE practitioner_id=?')}")
        print(f"   notes written by this MHWP stay, with the author left empty: "
              f"{q('SELECT COUNT(*) FROM patient_notes WHERE practitioner_id=?')}")
        print(f"   patients left without an MHWP ({len(pats)}): {', '.join(pats) or 'none'}")
    bookings_block(live_rows(conn, user_id=uid))
    print("This cannot be undone.")
    if not ask_yes_no("Continue? (y/n): "):
        print("  Nothing was changed.")
        return
    n = delete_user(conn, uid)
    print(f"\n  Done. {u['name']} was deleted."
          + (f"\n  {n} booking{'s' if n != 1 else ''} cancelled, {2 * n} emails written." if n else ""))


def a5_disable(conn, uid):
    u = get_user(conn, uid)
    heading(f"DISABLE USER: {u['name']} ({ROLE[u['role']]}, active)")
    print("The account is frozen. Only log in and log out stay possible.")
    if u["role"] == "patient":
        cur = conn.execute("SELECT m.name FROM patient_profiles pp JOIN users m ON m.user_id=pp.assigned_practitioner_id "
                           "WHERE pp.patient_id=?", (uid,)).fetchone()
        print(f"   allocation cleared: {cur[0] if cur else 'none'}")
    else:
        pats = [r["name"] for r in conn.execute(
            "SELECT u.name FROM patient_profiles pp JOIN users u ON u.user_id=pp.patient_id "
            "WHERE pp.assigned_practitioner_id=? ORDER BY u.user_id", (uid,))]
        print(f"   patients who lose their MHWP ({len(pats)}): {', '.join(pats) or 'none'}")
    bookings_block(live_rows(conn, user_id=uid))
    print("Cancelled bookings are not restored if the account is re enabled.")
    if not ask_yes_no("Continue? (y/n): "):
        print("  Nothing was changed.")
        return
    n = disable_user(conn, uid)
    print(f"\n  Done. {u['name']} is disabled."
          + (f"\n  {n} booking{'s' if n != 1 else ''} cancelled, {2 * n} emails written." if n else ""))


def a6_reenable(conn, uid):
    u = get_user(conn, uid)
    reenable_user(conn, uid)
    print(f"\n  Done. {u['name']} is active again.")
    if u["role"] == "patient":
        print("  Allocation: none. Allocate an MHWP under Manage allocations.")
    else:
        print("  Patients allocated: none. Allocate patients under Manage allocations.")
    print("  Cancelled bookings are not restored.")


# ---------------------------------------------------------------- reports (A7, A8, A8b)
def screen_reports(conn):
    while True:
        heading("VIEW REPORTS")
        print("   1  Admin summary\n   2  Mood by gender and age band\n   3  Clinic overview\n"
              "   4  Mood trend\n   0  Back")
        c = ask_number("Choose a report: ", 0, 4)
        if c == 0:
            return
        [None, a7_summary, a8_mood_groups, a8b_overview, mood_trend][c](conn)


def mood_trend(conn, days=30):
    """Text bar chart of the average mood per day over the last `days` days."""
    start = (NOW - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    df = frame(conn, "SELECT date(created_at) AS day, score FROM mood_entries WHERE date(created_at) >= ?",
               (start,))
    heading(f"MOOD TREND: LAST {days} DAYS")
    if df.empty:
        print("  No mood entries in this period.")
        return
    daily = df.groupby("day")["score"].agg(["mean", "count"])
    print("  Average mood per day across all patients. 1 = best, 6 = worst,")
    print("  so a longer bar means a worse day.\n")
    print(f"  {'Day':<11}{'':<26}{'Average':>7}{'Entries':>9}")
    for day, r in daily.iterrows():
        bar = "█" * round(r["mean"] * 4)               # 4 characters per point, at most 24
        print(f"  {show_date(day):<11}{bar:<26}{r['mean']:>7.2f}{int(r['count']):>9}")
    if len(daily) >= 14:                                # compare whole weeks, so one odd day does not decide it
        first, last = daily["mean"].iloc[:7].mean(), daily["mean"].iloc[-7:].mean()
        change = "worse" if last > first else "better" if last < first else "the same"
        print(f"\n  First week average {first:.2f}, last week average {last:.2f}: mood is {change}.")


def a7_summary(conn):
    mon, nxt = week_bounds()
    heading("ADMIN SUMMARY")
    print(f"  Week: {mon:%a %d %b} to {nxt - timedelta(days=1):%a %d %b %Y}\n")
    print(f"  {'Role':<10}{'Active':>8}{'Disabled':>10}")
    for role in ("admin", "practitioner", "patient"):
        a, d = conn.execute("SELECT SUM(account_status='active'), SUM(account_status='disabled') "
                            "FROM users WHERE role=?", (role,)).fetchone()
        print(f"  {ROLE[role]:<10}{a or 0:>8}{d or 0:>10}")
    un = conn.execute("""SELECT COUNT(*) FROM users u JOIN patient_profiles pp ON pp.patient_id=u.user_id
                         WHERE u.account_status='active' AND pp.assigned_practitioner_id IS NULL""").fetchone()[0]
    print(f"\n  Active patients without an MHWP: {un}\n")
    rows = conn.execute("""SELECT u.name, u.account_status,
        (SELECT COUNT(*) FROM patient_profiles pp WHERE pp.assigned_practitioner_id = u.user_id) AS patients,
        (SELECT COUNT(*) FROM appointments a WHERE a.practitioner_id = u.user_id AND a.status='confirmed'
            AND a.scheduled_time >= ? AND a.scheduled_time < ?) AS confirmed,
        (SELECT COUNT(*) FROM appointments a WHERE a.practitioner_id = u.user_id AND a.status='requested'
            AND a.scheduled_time >= ? AND a.scheduled_time < ?) AS requested
        FROM users u WHERE u.role='practitioner' ORDER BY u.user_id""",
                        (ts(mon), ts(nxt), ts(mon), ts(nxt))).fetchall()
    print(f"  {'MHWP':<18}{'Status':<10}{'Patients':>9}{'Confirmed':>11}{'Requested':>11}")
    for r in rows:
        print(f"  {r['name']:<18}{r['account_status']:<10}{r['patients']:>9}{r['confirmed']:>11}{r['requested']:>11}")


def age_at(dob):
    if not dob:
        return None
    y, m, d = map(int, dob.split("-"))
    return NOW.year - y - ((NOW.month, NOW.day) < (m, d))


def patient_30day_averages(conn):
    """One row per active patient: their own 30 day average. Used by A8 and A8b."""
    df = frame(conn, """SELECT m.patient_id AS pid, m.score, u.gender, u.date_of_birth AS dob
                        FROM mood_entries m JOIN users u ON u.user_id = m.patient_id
                        WHERE u.role='patient' AND u.account_status='active'
                          AND m.created_at > ? AND m.created_at <= ?""",
               [ts(NOW - timedelta(days=30)), ts(NOW)])
    per = df.groupby("pid").agg(avg=("score", "mean"), entries=("score", "count"),
                                gender=("gender", "first"), dob=("dob", "first"))
    per["age"] = per["dob"].map(age_at)
    per["band"] = (pd.cut(per["age"], bins=[17, 24, 34, 49, 200],
                          labels=["18 to 24", "25 to 34", "35 to 49", "50 and over"])
                   .astype(object).fillna("not given"))
    per["gender"] = per["gender"].map(lambda g: GENDER_LABEL.get(g, "not given"))
    return per


def group_table(per, col):
    print(f"  {'Group':<20}{'Patients':>9}{'Average':>9}")
    for key, g in per.groupby(col):
        if len(g) < MIN_GROUP:
            print(f"  {key:<20}{'fewer than ' + str(MIN_GROUP):>18}")
        else:
            print(f"  {key:<20}{len(g):>9}{g['avg'].mean():>9.2f}")


def a8_mood_groups(conn):
    per = patient_30day_averages(conn)
    heading("MOOD BY GENDER AND AGE BAND")
    print("  Last 30 days, active patients. Score 1 is best, 6 is worst.")
    print("  Each patient counts once, using their own 30 day average.")
    print(f"  Groups with fewer than {MIN_GROUP} patients are hidden.\n")
    print("  By gender")
    group_table(per, "gender")
    print("\n  By age band")
    group_table(per, "band")
    print(f"\n  Based on {int(per['entries'].sum())} entries from {len(per)} patients.")


def alert_count(conn):
    df = frame(conn, """SELECT m.patient_id AS pid, m.score FROM mood_entries m
                        JOIN users u ON u.user_id=m.patient_id
                        WHERE u.account_status='active' AND m.created_at > ? AND m.created_at <= ?
                        ORDER BY m.patient_id, m.created_at""",
               [ts(NOW - timedelta(days=7)), ts(NOW)])
    n = 0
    for _, g in df.groupby("pid"):
        s = g["score"].tolist()
        rise = max((s[j] - s[i] for i in range(len(s)) for j in range(i + 1, len(s))), default=0)
        if 6 in s or rise >= 3:
            n += 1
    return n


def a8b_overview(conn):
    mon, nxt = week_bounds()
    per = patient_30day_averages(conn)
    active = frame(conn, """SELECT u.user_id AS uid, pp.assigned_practitioner_id AS mhwp FROM users u
                            JOIN patient_profiles pp ON pp.patient_id=u.user_id
                            WHERE u.account_status='active'""")
    mh = frame(conn, "SELECT user_id FROM users WHERE role='practitioner' AND account_status='active'")
    caseload = (active.dropna(subset=["mhwp"]).groupby("mhwp").size()
                .reindex(mh["user_id"], fill_value=0))
    today = conn.execute("""SELECT COUNT(DISTINCT patient_id) FROM mood_entries m JOIN users u ON u.user_id=m.patient_id
                            WHERE u.account_status='active' AND m.created_at >= ?""",
                         (ts(NOW.replace(hour=0, minute=0)),)).fetchone()[0]
    # only bookings of active MHWPs, so the numerator matches the capacity below
    conf, req = conn.execute("""SELECT SUM(a.status='confirmed'), SUM(a.status='requested')
                                FROM appointments a JOIN users m ON m.user_id = a.practitioner_id
                                WHERE m.account_status='active'
                                  AND a.scheduled_time >= ? AND a.scheduled_time < ?""",
                             (ts(mon), ts(nxt))).fetchone()
    capacity = len(mh) * 5 * 8                    # Monday to Friday, 8 one hour slots a day
    heading("CLINIC OVERVIEW")
    print(f"  Week: {mon:%a %d %b} to {nxt - timedelta(days=1):%a %d %b %Y}\n")
    print(f"  Active patients                       {len(active)}")
    print(f"  Active patients without an MHWP       {int(active['mhwp'].isna().sum())}")
    print(f"  Caseload per active MHWP              "
          f"lowest {int(caseload.min())}, average {caseload.mean():.1f}, highest {int(caseload.max())}")
    print(f"  Logged a mood today                   {today} of {len(active)}")
    if len(per) >= MIN_GROUP:
        print(f"  Average mood, last 30 days            {per['avg'].mean():.2f} (1 best, 6 worst)")
    print(f"  Patients with a mood alert, 7 days    {alert_count(conn)}")
    print(f"  Bookings this week                    {conf or 0} confirmed, {req or 0} requested")
    print(f"  Slot use this week                    {(conf or 0) / capacity:.0%} of {capacity} slots")
    print("  (Alert names go to the MHWP, not to the admin.)")


# ---------------------------------------------------------------- run
DEMO_SCRIPT = [
    # E1 login: one wrong try, then the right one (usernames ignore case)
    "admin1", "wrong", "ADMIN1", "admin",
    # main menu: two bad inputs, then Manage allocations
    "9", "x", "1",
    "@Sam Doyle", "@Dr Chloe Tan", "maybe", "Y",       # A2 allocate: bad input, then capital Y
    "@Lucy Fraser", "@Dr Ben Hughes", "N",             # A2 allocate: capital N, nothing changes
    "@Daniel Cole",                                    # disabled patient refused
    "@Noah Green", "@Dr Ben Hughes", "y",              # A2b reallocate, bookings, yes
    "@Ella Brooks", "@Dr Amara Okafor", "n",           # A2b reallocate, bookings, no
    "0",
    # Manage users
    "2",                                               # A1: the admin is protected and not listed
    "2",                                               # patients
    "@Lucy Fraser", "1", "2", "lucy.fraser", "lucy.fraser@example.org",       # A3 bad then good email
    "@Lucy Fraser", "1", "4", "29/02/2026", "29/02/1992",                     # A3 29 Feb refused in 2026, accepted in leap year 1992
    "@Hana Kim", "2", "maybe", "y",                    # A4 delete patient
    "0",
    "1",                                               # MHWPs
    "@Dr Chloe Tan", "2", "n",                         # A4 delete MHWP, no
    "@Dr Chloe Tan", "3", "y",                         # A5 disable MHWP
    "0",
    "2",                                               # patients
    "@Omar Haddad", "3", "y",                          # A5 disable patient
    "@Omar Haddad", "1",                               # A6 re enable
    "0",
    "0",
    # allocations again, to see the re enabled patient has no MHWP
    "1", "0",
    # reports
    "3", "1", "2", "3", "4", "0",
    # log out
    "4",
]


def main():
    global SCRIPT
    demo = "--demo" in sys.argv
    if demo:
        SCRIPT = list(DEMO_SCRIPT)
        if os.path.exists(DB):
            os.remove(DB)
    conn = connect()
    conn.executescript(open(SCHEMA).read())
    seed(conn)
    while True:
        admin = login(conn)
        if admin is not None:
            admin_menu(conn, admin)
        if demo:
            break
    conn.close()


if __name__ == "__main__":
    main()
