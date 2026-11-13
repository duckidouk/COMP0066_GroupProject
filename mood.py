from datetime import date, datetime
import sqlite3


MOOD_SCORE_OPTIONS = {"1", "2", "3", "4", "5", "6"}
MOOD_DESCRIPTORS = {
    1: "Excellent",
    2: "Very good",
    3: "Good",
    4: "Okay",
    5: "Low",
    6: "Very low",
}

def ensure_daily_mood_entry(connection: sqlite3.Connection, patient_id: int) -> None:
    today = date.today().isoformat()

    existing_entry = connection.execute(
        """
        SELECT 1
        FROM mood_entries
        WHERE patient_id = ? AND date(created_at) = ?
        LIMIT 1
        """,
        (patient_id, today),
    ).fetchone()

    if existing_entry is not None:
        print("You have already logged your mood today.\n")
        return

    print("\nDaily mood check-in")
    print("Choose the option that best describes your mood:\n")
    for mood_score, descriptor in MOOD_DESCRIPTORS.items():
        print(f"{mood_score}. {descriptor}")
    print(f"\n")

    while True:
        score_input = input("Mood score (1-6): ").strip()
        if score_input in MOOD_SCORE_OPTIONS:
            score = int(score_input)
            break
        print("Please enter a number from 1 to 6.")

    created_at = datetime.now().isoformat(timespec="seconds")
    connection.execute(
        """
        INSERT INTO mood_entries (patient_id, score, created_at)
        VALUES (?, ?, ?)
        """,
        (patient_id, score, created_at),
    )
    connection.commit()
    print(
        "\nYour mood entry has been saved.\n"
        f"\nMood score: {score} - {MOOD_DESCRIPTORS[score]}\n"
        f"Recorded at: {datetime.fromisoformat(created_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    input("Press Enter to continue to the main menu.")
