import sqlite3

DATABASE_PATH = "therapy_link.db"


SAMPLE_USERS = [
    ("admin", "", "TherapyLink Administrator", "admin@therapylink.test", "admin", "2026-11-01T09:00:00"),
    ("mhwp1", "", "Dr Alex Brown", "alex.brown@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp2", "", "Dr Morgan Lee", "morgan.lee@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("patient1", "", "Jamie Taylor", "jamie.taylor@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient2", "", "Riley Morgan", "riley.morgan@therapylink.test", "patient", "2026-11-01T09:00:00"),
]

SAMPLE_PATIENT_PROFILES = [
    ("patient1", "emergency1@therapylink.test", "mhwp1"),
    ("patient2", "emergency2@therapylink.test", "mhwp2"),
]

SAMPLE_CONDITIONS = [
    ("Anxiety", "Persistent worry or fear that can affect daily life."),
    ("Depression", "Persistent low mood or loss of interest."),
    ("Stress", "Emotional or physical strain in response to demands."),
]

SAMPLE_PATIENT_CONDITIONS = [
    ("patient1", "Anxiety", "mhwp1"),
    ("patient2", "Stress", "mhwp2"),
]

SAMPLE_EMOTIONS = [
    ("Calm", "Feeling peaceful and settled."),
    ("Anxious", "Feeling worried or uneasy."),
    ("Stressed", "Feeling under pressure."),
    ("Hopeful", "Feeling optimistic about what is ahead."),
]

SAMPLE_RESOURCES = [
    ("Free Mindfulness Project", "https://www.freemindfulness.org/download"),
    ("Insight Timer Guided Meditations", "https://insighttimer.com/guided-meditations"),
]

SAMPLE_MOOD_ENTRIES = [
    ("patient1", 2, "Felt rested after a good night's sleep.", "2026-11-08T09:00:00"),
    ("patient1", 4, "A busy day left me feeling tense.", "2026-11-09T09:00:00"),
    ("patient1", 3, "A short walk helped me feel more settled.", "2026-11-10T09:00:00"),
    ("patient2", 5, "I felt overwhelmed by several things today.", "2026-11-08T09:00:00"),
    ("patient2", 4, "Talking with a friend helped a little.", "2026-11-09T09:00:00"),
    ("patient2", 3, "I made time to rest this afternoon.", "2026-11-10T09:00:00"),
]

SAMPLE_JOURNAL_ENTRIES = [
    ("patient1", "I took a break outside today and noticed that it helped me reset."),
    ("patient2", "Writing down one thing I handled well today made the evening feel easier."),
]

SAMPLE_PATIENT_NOTES = [
    ("patient1", "mhwp1", "Discussed grounding techniques and agreed to review them next session."),
    ("patient2", "mhwp2", "Patient identified taking regular breaks as a helpful coping strategy."),
]

SAMPLE_APPOINTMENTS = [
    ("patient1", "mhwp1", "2026-11-12T10:00:00", "confirmed"),
    ("patient1", "mhwp1", "2026-11-13T14:00:00", "requested"),
    ("patient2", "mhwp2", "2026-11-13T11:00:00", "confirmed"),
]


def seed_sample_data():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executemany(
            """
            INSERT OR IGNORE INTO users
                (username, password, name, email, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            SAMPLE_USERS,
        )

        user_ids = {
            username: connection.execute(
                "SELECT user_id FROM users WHERE username = ?", (username,)
            ).fetchone()[0]
            for username in ("mhwp1", "mhwp2", "patient1", "patient2")
        }

        connection.executemany(
            """
            INSERT OR IGNORE INTO patient_profiles
                (patient_id, emergency_contact_email, assigned_practitioner_id)
            VALUES (?, ?, ?)
            """,
            [
                (user_ids[patient], emergency_email, user_ids[practitioner])
                for patient, emergency_email, practitioner in SAMPLE_PATIENT_PROFILES
            ],
        )

        connection.executemany(
            "INSERT OR IGNORE INTO conditions (name, description) VALUES (?, ?)",
            SAMPLE_CONDITIONS,
        )
        condition_ids = {
            name: connection.execute(
                "SELECT condition_id FROM conditions WHERE name = ?", (name,)
            ).fetchone()[0]
            for name in ("Anxiety", "Depression", "Stress")
        }
        connection.executemany(
            """
            INSERT OR IGNORE INTO patient_conditions
                (patient_id, condition_id, practitioner_id)
            VALUES (?, ?, ?)
            """,
            [
                (user_ids[patient], condition_ids[condition], user_ids[practitioner])
                for patient, condition, practitioner in SAMPLE_PATIENT_CONDITIONS
            ],
        )

        connection.executemany(
            """
            INSERT OR IGNORE INTO emotions (name, description)
            VALUES (?, ?)
            """,
            SAMPLE_EMOTIONS,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO resources (name, url) VALUES (?, ?)",
            SAMPLE_RESOURCES,
        )

        for username, score, comment, created_at in SAMPLE_MOOD_ENTRIES:
            patient_id = user_ids[username]
            exists = connection.execute(
                """
                SELECT 1 FROM mood_entries
                WHERE patient_id = ? AND comment = ?
                """,
                (patient_id, comment),
            ).fetchone()
            if not exists:
                connection.execute(
                    """
                    INSERT INTO mood_entries (patient_id, score, comment, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (patient_id, score, comment, created_at),
                )

        for username, content in SAMPLE_JOURNAL_ENTRIES:
            patient_id = user_ids[username]
            exists = connection.execute(
                """
                SELECT 1 FROM journal_entries
                WHERE patient_id = ? AND content = ?
                """,
                (patient_id, content),
            ).fetchone()
            if not exists:
                connection.execute(
                    """
                    INSERT INTO journal_entries (patient_id, content, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (patient_id, content, "2026-11-10T10:00:00"),
                )

        for username, practitioner, content in SAMPLE_PATIENT_NOTES:
            patient_id = user_ids[username]
            practitioner_id = user_ids[practitioner]
            exists = connection.execute(
                """
                SELECT 1 FROM patient_notes
                WHERE patient_id = ? AND content = ?
                """,
                (patient_id, content),
            ).fetchone()
            if not exists:
                connection.execute(
                    """
                    INSERT INTO patient_notes
                        (patient_id, practitioner_id, content, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (patient_id, practitioner_id, content, "2026-11-10T10:30:00"),
                )

        for patient, practitioner, scheduled_time, status in SAMPLE_APPOINTMENTS:
            exists = connection.execute(
                """
                SELECT 1 FROM appointments
                WHERE patient_id = ? AND practitioner_id = ? AND scheduled_time = ?
                """,
                (user_ids[patient], user_ids[practitioner], scheduled_time),
            ).fetchone()
            if not exists:
                connection.execute(
                    """
                    INSERT INTO appointments
                        (patient_id, practitioner_id, scheduled_time, status, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_ids[patient],
                        user_ids[practitioner],
                        scheduled_time,
                        status,
                        "2026-11-10T11:00:00",
                    ),
                )

    print(f"Sample data is ready in {DATABASE_PATH}")
    print("Test logins: admin, mhwp1, mhwp2, patient1, patient2 (all passwords are blank).")


if __name__ == "__main__":
    seed_sample_data()
