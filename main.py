import getpass
import sqlite3
from contextlib import closing
DATABASE_PATH = "therapy_link.db"


def login(connection):
    print("\n--- Login ---")

    while True:
        print("Enter 'q' to quit.")
        username = input("Username: ").strip()

        if username.lower() == "q":
            return None
        if not username:
            print("Username cannot be empty.")
            continue

        user = connection.execute(
            """
            SELECT username, password, name, role, account_status
            FROM users
            WHERE username = ?
            LIMIT 1;
            """,
            (username,),
        ).fetchone()

        if user is None:
            print(f"\nNo account found for {username}. Please try again.\n")
            continue

        password = getpass.getpass("Password: ")
        if password != user["password"]:
            print("Incorrect password.")
            continue

        return user


def main():
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.row_factory = sqlite3.Row

        user = login(connection)

        if user is None:
            print("Login cancelled.")
            return

        print(f"\nWelcome, {user['name']}! You are logged in as {user['role']}.")

        if user["account_status"] == "disabled":
            print("This account is disabled; application features are unavailable.")


if __name__ == "__main__":
    main()