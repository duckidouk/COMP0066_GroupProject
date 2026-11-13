import sqlite3
from datetime import datetime
from typing import Callable
from utils import is_valid_email, is_valid_name
from patient_booking_appointment import appointment_menu

def prompt_for_personal_detail(prompt: str) -> str | None:
    value = input(f"{prompt}: ").strip()
    if value.casefold() == "b":
        print("Returning to personal details.")
        return None
    return value


def prompt_until_valid(
    prompt: str,
    validator: Callable[[str], bool],
    error_message: str,
) -> str | None:
    print(f"\nEnter 'b' to go back without saving.\n")

    while True:
        value = prompt_for_personal_detail(prompt)
        if value is None:
            return None
        if validator(value):
            return value
        print(error_message)


def log_journal_entry(connection: sqlite3.Connection, patient_id: int) -> None:
    print("\nJournal entry")
    print("\nEnter 'b' to go back without saving.\n")

    while True:
        content = input("Write your entry: ").strip()

        if content.casefold() == "b":
            return
        if not content:
            print("\nJournal entry cannot be empty.")
            continue

        created_at = datetime.now().isoformat(timespec="seconds")
        connection.execute(
            """
            INSERT INTO journal_entries (patient_id, content, created_at)
            VALUES (?, ?, ?)
            """,
            (patient_id, content, created_at),
        )
        connection.commit()
        formatted_timestamp = datetime.fromisoformat(created_at).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        print(
            "\nYour journal entry has been saved.\n"
            f'"{content}"\n'
            f"Recorded at: {formatted_timestamp}"
        )
        input("\nPress Enter to return to the patient menu.")
        return


def _show_personal_details(connection: sqlite3.Connection, patient_id: int) -> None:
    details = connection.execute(
        """
        SELECT users.name, users.email, patient_profiles.emergency_contact_email
        FROM users
        LEFT JOIN patient_profiles ON patient_profiles.patient_id = users.user_id
        WHERE users.user_id = ?
        """,
        (patient_id,),
    ).fetchone()

    print("\nYour personal details:")
    print(f"Name: {details['name']}")
    print(f"Email: {details['email']}")
    print(f"Emergency contact email: {details['emergency_contact_email'] or 'Not set'}")


def edit_personal_details(connection: sqlite3.Connection, patient_id: int) -> None:
    while True:
        _show_personal_details(connection, patient_id)
        print(
            "\n1. Change name\n"
            "2. Change email\n"
            "3. Change emergency contact email\n"
            "4. Go back to patient menu\n"
        )
        choice = input("Choose an option (1-4): ").strip()

        match choice:
            case "1":
                value = prompt_until_valid(
                    "New name",
                    is_valid_name,
                    "\nPlease enter a name containing letters; use only spaces or - ' . as punctuation.\n",
                )
                if value is None:
                    continue
                connection.execute(
                    "UPDATE users SET name = ? WHERE user_id = ?",
                    (value, patient_id),
                )
            case "2":
                value = prompt_until_valid(
                    "New email address",
                    is_valid_email,
                    "\nPlease enter a valid email address.\n",
                )
                if value is None:
                    continue
                connection.execute(
                    "UPDATE users SET email = ? WHERE user_id = ?",
                    (value, patient_id),
                )
            case "3":
                value = prompt_until_valid(
                    "New emergency contact email address",
                    is_valid_email,
                    "Please enter a valid email address.",
                )
                if value is None:
                    continue
                connection.execute(
                    """
                    INSERT INTO patient_profiles (patient_id, emergency_contact_email)
                    VALUES (?, ?)
                    ON CONFLICT(patient_id) DO UPDATE
                    SET emergency_contact_email = excluded.emergency_contact_email
                    """,
                    (patient_id, value),
                )
            case "4":
                return
            case _:
                print("Please enter a number from 1 to 4.")
                continue

        connection.commit()
        print("Your details have been updated.")


def show_urgent_support_numbers() -> None:
    print(
        "\nUrgent mental health support (England)\n\n"
        "NHS 111: Call 111 and select the mental health option for urgent advice.\n"
        "999 or A&E: Call 999 or go to A&E if someone's life is at risk or "
        "you cannot keep yourself or someone else safe.\n"
        "Samaritans: Call 116 123 for free, confidential listening support.\n"
        "Childline (under 19): Call 0800 1111."
    )
    input("\nPress Enter to return to the patient menu.")


def patient_menu(connection: sqlite3.Connection, user: sqlite3.Row) -> None:
    patient_id = user["user_id"]

    while True:
        print(
            "\n================================\n"
            "          PATIENT MENU\n"
            "================================\n\n"
            "1. Log a journal entry\n"
            "2. Amend personal details\n"
            "3. Urgent support numbers\n"
            "4. Appointments\n"
            "5. Meditation and relaxation resources (not yet integrated)\n"
            "6. Log out\n"
        )
        choice = input("Choose an option (1-6): ").strip()

        match choice:
            case "1":
                log_journal_entry(connection, patient_id)
            case "2":
                edit_personal_details(connection, patient_id)
            case "3":
                show_urgent_support_numbers()
            case "4":
                 appointment_menu(connection,patient_id)
            case "5":
                print("This feature will be available when its module is integrated.")
            case "6":
                print("You have been logged out.")
                return
            case _:
                print("Please enter a number from 1 to 6.")
