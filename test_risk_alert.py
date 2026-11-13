"""Checks for risk_alert.py. Run: python test_risk_alert.py [path to schema .sql]"""
import builtins
import contextlib
import io
import os
import sqlite3
import sys
import tempfile

import risk_alert as ra

SCHEMA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_stats.sql")
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS  " if ok else "FAIL  ") + name + (f"   [{detail}]" if detail else ""))


def build():
    conn = sqlite3.connect(os.path.join(tempfile.mkdtemp(), "t.db"))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    conn.executescript(open(SCHEMA).read())
    mk = lambda u, n, r, s="active": conn.execute(
        "INSERT INTO users (username,name,email,role,account_status,created_at) VALUES (?,?,?,?,?,'2026-09-01 09:00')",
        (u, n, f"{u}@example.org", r, s)).lastrowid
    ids = {"a1": mk("admin1", "Alex Admin", "admin"), "a2": mk("admin2", "Bo Admin", "admin"),
           "a3": mk("admin3", "Old Admin", "admin", "disabled"),
           "m1": mk("m1", "Dr One", "practitioner"), "p1": mk("p1", "Pat One", "patient"),
           "p2": mk("p2", "Pat Two", "patient")}
    conn.execute("INSERT INTO patient_profiles (patient_id, assigned_practitioner_id) VALUES (?,?)", (ids["p1"], ids["m1"]))
    conn.execute("INSERT INTO patient_profiles (patient_id, assigned_practitioner_id) VALUES (?,NULL)", (ids["p2"],))
    conn.commit()
    return conn, ids


def one(conn, sql, *p):
    return conn.execute(sql, p).fetchone()[0]


# detection: things that must raise an alert
must_alert = [
    "I want to die", "I WANT TO DIE!!!", "i want   to... die", "I don’t want to be here anymore",
    "I keep thinking about suicide", "feeling suicidal today", "I am going to kill myself",
    "I’m thinking about ending my life", "I want to hurt myself", "everyone is better off without me",
    "I took an overdose", "I want to kill him", "I will hurt someone", "thinking of ways to harm others",
    "no reason to live", "I just want to end it all",
    "I don't want to die",                 # known false alarm: we choose to over alert
]
for text in must_alert:
    check(f"alerts: {text}", bool(ra.detect_risk(text)))
# detection: ordinary entries must not
must_not = [
    "I had a good day and went for a walk", "Work was hard but I am killing it at the gym",
    "The meeting killed my afternoon", "I want to kill the spider in my room", "My mood is low but I talked to a friend",
    "I am tired of this weather", "We watched a film about a shark attack",
]
for text in must_not:
    check(f"no alert: {text}", not ra.detect_risk(text))
check("categories are named", set(ra.detect_risk("I want to die and I want to kill him")) == {"harm to self", "harm to others"})


# the phrase bank checks itself: every pattern must match its own example, in the right category
import re
import risk_phrase_bank as bank
total = 0
for category, groups in bank.BANK.items():
    for group, entries in groups.items():
        for pattern, example in entries:
            total += 1
            re.compile(pattern)
            hit = ra.detect_risk(example)
            if category not in hit:
                check(f"bank example matches: {example}", False, f"{category} / {group}")
check(f"all {total} bank patterns match their own example in the right category",
      all(category in ra.detect_risk(example) for category, groups in bank.BANK.items()
          for entries in groups.values() for _p, example in entries))
for text in bank.NOT_ALERT_EXAMPLES:
    check(f"bank no alert: {text}", not ra.detect_risk(text))

# the WATCH tier: support contacts, no email
for group, entries in bank.WATCH_BANK.items():
    for pattern, example in entries:
        total += 1
        if not ra.detect_watch(example):
            check(f"watch example matches: {example}", False, group)
check("every WATCH pattern matches its own example",
      all(ra.detect_watch(example) for entries in bank.WATCH_BANK.values() for _p, example in entries))
check("watch phrases do not raise an ALERT",
      not any(ra.detect_risk(example) for entries in bank.WATCH_BANK.values() for _p, example in entries))
for text in ["I feel hopeless about my exam", "I can't take it anymore", "I feel like a burden to my family"]:
    check(f"watch only: {text}", bool(ra.detect_watch(text)) and not ra.detect_risk(text))
# alternation bug check: a pattern with | must still respect word boundaries
check("word boundary applies to the whole pattern (no match inside other words)",
      not ra.detect_risk("the unsuicidelike thing") and not ra.detect_risk("kmsx"))
# new slang, leet and variants from the published lexicons
for text in ["k1ll my3lf", "I want to unalive myself", "5uic1de", "I have enough pills to die", "I bought pills to die",
             "what is the easiest way to die", "I made a noose", "no one will miss me", "I deserve to die",
             "I wish I would not wake up", "I want to blow my brains out", "I might eat a bullet", "I want to end my suffering",
             "I want to sleep forever", "I am going to do myself in"]:
    check(f"alerts (new): {text}", bool(ra.detect_risk(text)))

# saving a normal entry
conn, ids = build()
r = ra.save_journal_entry(conn, ids["p1"], "A calm day.")
check("normal entry saved with a timestamp and no emails",
      one(conn, "SELECT COUNT(*) FROM journal_entries WHERE patient_id=? AND created_at IS NOT NULL", ids["p1"]) == 1
      and one(conn, "SELECT COUNT(*) FROM emails") == 0 and not r["risk"])

# risky entry with an MHWP
conn, ids = build()
r = ra.save_journal_entry(conn, ids["p1"], "I want to die tonight.")
check("risky entry is saved", one(conn, "SELECT COUNT(*) FROM journal_entries WHERE patient_id=?", ids["p1"]) == 1)
check("emails: 1 to the MHWP and 2 to the active admins, none to the disabled admin",
      one(conn, "SELECT COUNT(*) FROM emails") == 3
      and one(conn, "SELECT COUNT(*) FROM emails WHERE to_user_id=?", ids["m1"]) == 1
      and one(conn, "SELECT COUNT(*) FROM emails WHERE to_user_id IN (?,?)", ids["a1"], ids["a2"]) == 2
      and one(conn, "SELECT COUNT(*) FROM emails WHERE to_user_id=?", ids["a3"]) == 0)
check("MHWP email has the entry text, admin emails do not",
      "I want to die tonight." in one(conn, "SELECT body FROM emails WHERE to_user_id=?", ids["m1"])
      and "I want to die tonight." not in one(conn, "SELECT body FROM emails WHERE to_user_id=?", ids["a1"]))
check("subject says URGENT and names the patient",
      one(conn, "SELECT subject FROM emails WHERE to_user_id=?", ids["a1"]) == "URGENT: possible risk in a journal entry by Pat One")
check("email says it is only a keyword match", "keyword match" in one(conn, "SELECT body FROM emails WHERE to_user_id=?", ids["m1"]))
check("result reports who was told", r["told_mhwp"] == "Dr One" and r["told_admins"] == 2)

# no MHWP: admins only, and the email says so
conn, ids = build()
r = ra.save_journal_entry(conn, ids["p2"], "I want to hurt myself")
check("no MHWP: only the 2 active admins are emailed",
      one(conn, "SELECT COUNT(*) FROM emails") == 2 and r["told_mhwp"] is None)
check("no MHWP: the email says no MHWP is allocated",
      "no MHWP allocated" in one(conn, "SELECT body FROM emails WHERE to_user_id=?", ids["a1"]))

# a disabled MHWP is not emailed
conn, ids = build()
conn.execute("UPDATE users SET account_status='disabled' WHERE user_id=?", (ids["m1"],)); conn.commit()
ra.save_journal_entry(conn, ids["p1"], "I want to die")
check("disabled MHWP is not emailed, admins still are",
      one(conn, "SELECT COUNT(*) FROM emails WHERE to_user_id=?", ids["m1"]) == 0 and one(conn, "SELECT COUNT(*) FROM emails") == 2)

# all or nothing
conn, ids = build()
real, calls = ra.write_email, {"n": 0}
def flaky(*a, **k):
    calls["n"] += 1
    if calls["n"] == 2:
        raise sqlite3.OperationalError("disk full (simulated)")
    return real(*a, **k)
ra.write_email = flaky
try:
    ra.save_journal_entry(conn, ids["p1"], "I want to die")
    failed = False
except sqlite3.Error:
    failed = True
ra.write_email = real
check("email failure: error raised, NOTHING saved (no entry, no emails)",
      failed and one(conn, "SELECT COUNT(*) FROM journal_entries") == 0 and one(conn, "SELECT COUNT(*) FROM emails") == 0)

# validation
for bad in ["", "   ", "x" * 5001]:
    try:
        ra.save_journal_entry(conn, ids["p1"], bad)
        check("bad entry refused", False)
    except ValueError:
        check(f"bad entry refused ({len(bad)} characters)", True)
try:
    ra.save_journal_entry(conn, ids["m1"], "hello")
    check("only a patient can journal", False)
except ValueError:
    check("only a patient can journal", True)
check("an entry of exactly 5000 characters is accepted", bool(ra.save_journal_entry(conn, ids["p1"], "x" * 5000)["entry_id"]))


# watch tier in saving and in the screen
conn, ids = build()
r = ra.save_journal_entry(conn, ids["p1"], "I feel hopeless and trapped about everything")
check("watch only: entry saved, NO emails, watch reported",
      one(conn, "SELECT COUNT(*) FROM journal_entries") == 1 and one(conn, "SELECT COUNT(*) FROM emails") == 0
      and r["watch"] and not r["risk"])
r = ra.save_journal_entry(conn, ids["p1"], "I feel hopeless and I want to die")
check("alert wins over watch: emails sent, watch not reported", one(conn, "SELECT COUNT(*) FROM emails") == 3 and not r["watch"])

# the screen
def run(conn, patient, answers):
    feed, out, real_input = iter(answers), io.StringIO(), builtins.input
    builtins.input = lambda prompt="": (print(prompt, end="", file=out) or next(feed))
    try:
        with contextlib.redirect_stdout(out):
            ra.screen_new_journal_entry(conn, patient)
    finally:
        builtins.input = real_input
    return out.getvalue()


conn, ids = build()
patient = conn.execute("SELECT * FROM users WHERE user_id=?", (ids["p1"],)).fetchone()
text = run(conn, patient, ["I want to die", ])
check("screen: tells the patient about the privacy exception BEFORE writing", text.index("private") < text.index("Write your entry"))
check("screen: risky entry shows who was told and all three support contacts",
      "We have told Dr One" in text and "999" in text and "111" in text and "116 123" in text)
text = run(conn, patient, ["Nice walk today."])
check("screen: normal entry shows no support block", "saved" in text and "116 123" not in text)
text = run(conn, patient, ["", ])
check("screen: pressing Enter saves nothing", "Nothing was saved" in text)
conn, ids = build()
patient = conn.execute("SELECT * FROM users WHERE user_id=?", (ids["p2"],)).fetchone()
text = run(conn, patient, ["I want to hurt myself"])
check("screen: no MHWP says the administrators were told", "told the clinic administrators" in text)


conn, ids = build()
patient = conn.execute("SELECT * FROM users WHERE user_id=?", (ids["p1"],)).fetchone()
text = run(conn, patient, ["I feel hopeless about everything"])
check("screen: watch only shows the support contacts and says nothing was sent",
      "Nothing from this entry has been sent to anyone" in text and "116 123" in text and "We have told" not in text
      and one(conn, "SELECT COUNT(*) FROM emails") == 0)

print(f"\n{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
