-- TherapyLink schema for the admin screens (admin_cli_prototype.py).
-- The tables are copied from schema.py; keep the two in step.
-- Changes from schema.py: usernames ignore case (COLLATE NOCASE),
-- users.gender and users.date_of_birth (for the admin reports),
-- and at the end, triggers so only an MHWP can be a patient's assigned practitioner.

CREATE TABLE IF NOT EXISTS users (
        user_id        INTEGER PRIMARY KEY,
        username       TEXT NOT NULL UNIQUE COLLATE NOCASE,  -- usernames ignore case
        password       TEXT NOT NULL DEFAULT '',
        name           TEXT NOT NULL,
        email          TEXT NOT NULL,
        role           TEXT NOT NULL CHECK (role IN ('admin', 'practitioner', 'patient')),
        account_status TEXT NOT NULL DEFAULT 'active'
                    CHECK (account_status IN ('active', 'disabled')),
        created_at     TEXT NOT NULL,
        disabled_at    TEXT,
        -- Added for the admin reports (mood by gender and age band). Both optional.
        gender         TEXT CHECK (gender IN ('female', 'male', 'non_binary', 'prefer_not_to_say')),
        date_of_birth  TEXT  -- YYYY-MM-DD
    );

    CREATE TABLE IF NOT EXISTS patient_profiles (
        patient_id                INTEGER PRIMARY KEY
            REFERENCES users(user_id) ON DELETE CASCADE,
        emergency_contact_email   TEXT,
        assigned_practitioner_id  INTEGER
            REFERENCES users(user_id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS mood_entries (
        mood_entry_id INTEGER PRIMARY KEY,
        patient_id    INTEGER NOT NULL
            REFERENCES users(user_id) ON DELETE CASCADE,
        score         INTEGER NOT NULL CHECK (score BETWEEN 1 AND 6),  -- 1 = best (green), 6 = worst (red)
        comment       TEXT,
        created_at    TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS journal_entries (
        journal_entry_id INTEGER PRIMARY KEY,
        patient_id       INTEGER NOT NULL
            REFERENCES users(user_id) ON DELETE CASCADE,
        content          TEXT NOT NULL,
        created_at       TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id  INTEGER PRIMARY KEY,
        patient_id      INTEGER NOT NULL
            REFERENCES users(user_id) ON DELETE CASCADE,
        practitioner_id INTEGER NOT NULL
            REFERENCES users(user_id) ON DELETE CASCADE,
        scheduled_time  TEXT NOT NULL,
        status          TEXT NOT NULL DEFAULT 'requested'
                        CHECK (status IN ('requested', 'confirmed', 'cancelled')),
        created_at      TEXT NOT NULL
    );

    -- An MHWP cannot have two live bookings in the same slot.
    CREATE UNIQUE INDEX IF NOT EXISTS idx_no_double_booking
        ON appointments (practitioner_id, scheduled_time)
        WHERE status != 'cancelled';

    CREATE TABLE IF NOT EXISTS conditions (
        condition_id INTEGER PRIMARY KEY,
        name         TEXT NOT NULL UNIQUE,
        description  TEXT
    );

    CREATE TABLE IF NOT EXISTS patient_conditions (
        patient_id      INTEGER NOT NULL
            REFERENCES users(user_id) ON DELETE CASCADE,
        condition_id    INTEGER NOT NULL
            REFERENCES conditions(condition_id),
        practitioner_id INTEGER
            REFERENCES users(user_id) ON DELETE SET NULL,
        PRIMARY KEY (patient_id, condition_id)
    );

    CREATE TABLE IF NOT EXISTS patient_notes (
        note_id         INTEGER PRIMARY KEY,
        patient_id      INTEGER NOT NULL
            REFERENCES users(user_id) ON DELETE CASCADE,
        practitioner_id INTEGER
            REFERENCES users(user_id) ON DELETE SET NULL,
        content         TEXT NOT NULL,
        created_at      TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS emotions (
        emotion_id  INTEGER PRIMARY KEY,
        name        TEXT NOT NULL UNIQUE,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS resources (
        resource_id INTEGER PRIMARY KEY,
        name        TEXT NOT NULL,
        url         TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS resource_emotions (
        resource_id INTEGER NOT NULL
            REFERENCES resources(resource_id) ON DELETE CASCADE,
        emotion_id  INTEGER NOT NULL
            REFERENCES emotions(emotion_id) ON DELETE CASCADE,
        PRIMARY KEY (resource_id, emotion_id)
    );

    CREATE TABLE IF NOT EXISTS emails (
        email_id    INTEGER PRIMARY KEY,
        to_user_id  INTEGER
            REFERENCES users(user_id) ON DELETE SET NULL,
        to_address  TEXT NOT NULL,
        subject     TEXT NOT NULL,
        body        TEXT NOT NULL,
        sent_at     TEXT NOT NULL
    );


-- Only a user with role 'practitioner' can be a patient's assigned MHWP.
CREATE TRIGGER IF NOT EXISTS trg_assigned_is_practitioner_insert
BEFORE INSERT ON patient_profiles
WHEN NEW.assigned_practitioner_id IS NOT NULL
 AND (SELECT role FROM users WHERE user_id = NEW.assigned_practitioner_id) IS NOT 'practitioner'
BEGIN
    SELECT RAISE(ABORT, 'assigned_practitioner_id must be a practitioner');
END;

CREATE TRIGGER IF NOT EXISTS trg_assigned_is_practitioner_update
BEFORE UPDATE OF assigned_practitioner_id ON patient_profiles
WHEN NEW.assigned_practitioner_id IS NOT NULL
 AND (SELECT role FROM users WHERE user_id = NEW.assigned_practitioner_id) IS NOT 'practitioner'
BEGIN
    SELECT RAISE(ABORT, 'assigned_practitioner_id must be a practitioner');
END;
