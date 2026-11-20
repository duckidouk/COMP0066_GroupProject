import sqlite3
from datetime import datetime

SUICIDE_WARNING_KEYWORDS = (
    "suicide",
    "suicidal",
    "kill myself",
    "killing myself",
    "take my own life",
    "end my life",
    "end it all",
    "want to die",
    "wanna die",
    "wish i was dead",
    "wish i were dead",
    "don't want to live",
    "do not want to live",
    "dont want to live",
    "no reason to live",
    "nothing to live for",
    "better off dead",
    "can't go on",
    "cannot go on",
    "can't do this anymore",
    "cannot do this anymore",
    "can't keep living",
    "can't keep going",
    "life isn't worth living",
    "life is not worth living",
    "tired of living",
    "tired of being alive",
    "i give up on life",
    "i want everything to end",
    "i just want it to end",
    "there is no point in living",
    "goodbye forever",
    "final goodbye",
    "this is my last message",
    "you won't see me again",
    "everyone is better off without me",
    "you'd be better off without me",
    "people would be better off without me",
    "hurt myself",
    "harm myself",
    "self harm",
    "self-harm",
    "cut myself",
    "want to disappear",
    "wish i could disappear",
)


def contains_suicide_warning_language(text: str) -> bool:
    normalized_text = text.casefold().replace("’", "'")
    return any(keyword in normalized_text for keyword in SUICIDE_WARNING_KEYWORDS)


def create_suicide_warning_alert(
    connection: sqlite3.Connection,
    patient_id: int,
    *,
    mood_entry_id: int | None = None,
    journal_entry_id: int | None = None,
) -> None:
    if (mood_entry_id is None) == (journal_entry_id is None):
        raise ValueError("An alert must reference exactly one mood or journal entry.")

    practitioner = connection.execute(
        """
        SELECT assigned_practitioner_id
        FROM patient_profiles
        WHERE patient_id = ?
        """,
        (patient_id,),
    ).fetchone()

    practitioner_id = practitioner[0] if practitioner is not None else None
    recipient_type = "practitioner" if practitioner_id is not None else "admin_queue"
    created_at = datetime.now().isoformat(timespec="seconds")

    connection.execute(
        """
        INSERT INTO suicide_warning_alerts (
            patient_id, mood_entry_id, journal_entry_id,
            recipient_type, recipient_practitioner_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            patient_id,
            mood_entry_id,
            journal_entry_id,
            recipient_type,
            practitioner_id,
            created_at,
        ),
    )
