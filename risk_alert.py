"""TherapyLink: risk alert for journal entries.

When a patient saves a journal entry that looks like it may mean harm to themselves or to others,
the app (1) saves the entry, (2) writes an urgent email to the patient's MHWP and to every active
admin, and (3) shows the patient support contacts straight away. Steps 1 and 2 happen in ONE
transaction, so an entry can never be saved without its alert, and an alert can never be sent
for an entry that was not saved.

IMPORTANT LIMITS (say these in the report, they are part of doing this honestly):
  * This is keyword matching, not understanding. It will miss some real risks (different words,
    spelling mistakes, hints) and will raise some false alarms ("I don't want to die" matches).
    We choose to over alert, because a missed warning is worse than an unnecessary one.
  * Emails here are rows in the 'emails' table. A real person has to read them. The app cannot
    promise that anyone reads them quickly. It is a support tool, not a safety guarantee.

Core Python only. Uses the team tables: users, patient_profiles, journal_entries, emails.
"""
import re
import sqlite3
from datetime import datetime

TIME_FORMAT = "%Y-%m-%d %H:%M"
MAX_LENGTH = 5000

# Team decision: does the MHWP's email contain the entry text? The admin email never does,
# because admins do not need the content of a private journal to know that someone needs help.
INCLUDE_TEXT_FOR_MHWP = True

# The phrase bank lives in risk_phrase_bank.py. Phrases are matched on whole words, after the text is
# lower cased and cleaned. Each group is a list of (pattern, example) pairs, flattened here.
from risk_phrase_bank import BANK, WATCH_BANK
CATEGORIES = {category: [pattern for group in groups.values() for pattern, _example in group]
              for category, groups in BANK.items()}
WATCH_CATEGORIES = {"warning signs": [pattern for group in WATCH_BANK.values() for pattern, _example in group]}

SUPPORT_TEXT = """  If you are in danger right now, call 999 or go to A&E.
  For urgent mental health help, call 111 and choose the mental health option.
  Samaritans are there at any time of the day or night: call 116 123."""
# Source: NHS Every Mind Matters, urgent support page (nhs.uk/every-mind-matters/urgent-support).
# Check the numbers again before submission.


# ------------------------------------------------------------------ detection
def clean(text):
    """Lower case, straighten apostrophes, remove punctuation, collapse spaces."""
    text = text.lower().replace("’", "'").replace("‘", "'")
    text = text.replace("'", "")                      # dont, cant, im
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _find(text, categories):
    cleaned = clean(text)
    found = {}
    for category, patterns in categories.items():
        hits = []
        for pattern in patterns:
            # (?:...) makes the word boundaries apply to the WHOLE pattern, even if it contains a | alternative
            for m in re.finditer(r"\b(?:" + pattern + r")\b", cleaned):
                hits.append(m.group(0))
        if hits:
            found[category] = sorted(set(hits))
    return found


def detect_risk(text):
    """ALERT tier. Returns {category: [matched phrases]}. An empty dict means nothing found."""
    return _find(text, CATEGORIES)


def detect_watch(text):
    """WATCH tier: warning signs that do not trigger an email. Same return format."""
    return _find(text, WATCH_CATEGORIES)


# ------------------------------------------------------------------ saving and alerting
def now_text():
    return datetime.now().strftime(TIME_FORMAT)


def validate_entry(text):
    """Returns (cleaned text, None) or (None, problem). Used by the screen to re ask."""
    text = text.strip()
    if not text:
        return None, "The entry is empty. Please write something, or leave this screen."
    if len(text) > MAX_LENGTH:
        return None, f"The entry is too long. The limit is {MAX_LENGTH} characters."
    return text, None


def write_email(conn, to_user_id, to_address, subject, body):
    conn.execute("INSERT INTO emails (to_user_id, to_address, subject, body, sent_at) VALUES (?, ?, ?, ?, ?)",
                 (to_user_id, to_address, subject, body, now_text()))


def recipients(conn, patient_id):
    """(the patient's active MHWP or None, list of active admins)."""
    mhwp = conn.execute(
        """SELECT m.user_id, m.name, m.email FROM patient_profiles pp
           JOIN users m ON m.user_id = pp.assigned_practitioner_id
           WHERE pp.patient_id = ? AND m.account_status = 'active'""", (patient_id,)).fetchone()
    admins = conn.execute("SELECT user_id, name, email FROM users WHERE role = 'admin' AND account_status = 'active'"
                          ).fetchall()
    return mhwp, admins


def describe(found):
    return "; ".join(f"{category} (matched: {', '.join(hits)})" for category, hits in found.items())


def save_journal_entry(conn, patient_id, text):
    """Save the entry. If it looks risky, write the alert emails in the same transaction.

    Returns a dict: {entry_id, risk (dict), told_mhwp (name or None), told_admins (count)}.
    Raises sqlite3.Error if anything fails, and then NOTHING is saved (not the entry, not the emails)."""
    text, problem = validate_entry(text)
    if problem:
        raise ValueError(problem)
    found = detect_risk(text)
    result = {"entry_id": None, "risk": found, "watch": {} if found else detect_watch(text),
              "told_mhwp": None, "told_admins": 0}
    with conn:                                        # one transaction: all or nothing
        patient = conn.execute("SELECT name, email FROM users WHERE user_id = ? AND role = 'patient'",
                               (patient_id,)).fetchone()
        if patient is None:
            raise ValueError("Only a patient can write journal entries.")
        when = now_text()
        cur = conn.execute("INSERT INTO journal_entries (patient_id, content, created_at) VALUES (?, ?, ?)",
                           (patient_id, text, when))
        result["entry_id"] = cur.lastrowid
        if not found:
            return result

        mhwp, admins = recipients(conn, patient_id)
        subject = f"URGENT: possible risk in a journal entry by {patient['name']}"
        common = (f"{patient['name']} saved a journal entry on {when} that may suggest harm to themselves or to others.\n"
                  f"Reason for this alert: {describe(found)}.\n"
                  "This is an automatic keyword match. It is not a clinical assessment and may be a false alarm.\n"
                  "Please follow your clinic's safeguarding procedure. If anyone is in immediate danger, call 999.")
        if mhwp is not None:
            body = common + (f"\n\nThe entry:\n{text}" if INCLUDE_TEXT_FOR_MHWP else
                             "\n\nThe entry is saved in the patient's record.")
            write_email(conn, mhwp["user_id"], mhwp["email"], subject, body)
            result["told_mhwp"] = mhwp["name"]
        else:
            common += "\nThis patient has no MHWP allocated at the moment, so only the admins have been told."
        for admin in admins:
            write_email(conn, admin["user_id"], admin["email"], subject,
                        common + "\n\nThe text of the entry is not included in this email.")
            result["told_admins"] += 1
    return result


# ------------------------------------------------------------------ patient screen
def screen_new_journal_entry(conn, patient):
    """The patient writes a journal entry. 'patient' is the patient's row from users."""
    print("\n" + "=" * 58 + "\n NEW JOURNAL ENTRY\n" + "=" * 58)
    print("  Your entries are private. The one exception: if an entry suggests that you or")
    print("  someone else may be in danger, your MHWP and the clinic admins are told.")
    while True:
        text = input("Write your entry (or press Enter to go back): ")
        if not text.strip():
            print("  Nothing was saved.")
            return
        text, problem = validate_entry(text)
        if problem is None:
            break
        print("  " + problem)
    found = detect_risk(text)
    try:
        result = save_journal_entry(conn, patient["user_id"], text)
    except sqlite3.Error:
        print("\n  Your entry could not be saved. Please try again.")
        if found:
            print("\n  What you wrote sounds like you may be having a very hard time.\n" + SUPPORT_TEXT)
        return
    print("\n  Your entry has been saved.")
    if not found and result["watch"]:
        print("\n  Thank you for writing this down. It sounds like things feel very heavy right now.")
        print("  Nothing from this entry has been sent to anyone. If it gets worse, or you want to talk")
        print("  to someone, here is who can help:")
        print(SUPPORT_TEXT)
    if found:
        print("\n  Thank you for writing this down. What you wrote sounds like you may be having a very hard time.")
        if result["told_mhwp"]:
            print(f"  We have told {result['told_mhwp']} so that they can reach out to you.")
        else:
            print("  We have told the clinic administrators so that someone can reach out to you.")
        print(SUPPORT_TEXT)
