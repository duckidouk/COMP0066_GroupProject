# after login -- the menu should appear
import sqlite3

DATABASE_PATH = "therapy_link.db"

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()

# hardcoding the mhwp until we figure out logins
# practitioner_id = 2

def mhwp_menu(connection: sqlite3.Connection, user: sqlite3.Row) -> None:
    # practitioner_id = user["user_id"]
    practitioner = mhwp(user["user_id"], connection)

    while True:
        print(
            "\n================================\n"
            "          MHWP MENU\n"
            "================================\n\n"
            "1. Show calendar\n"
            "2. Show patients\n"
            "3. Log out\n"
        )
        choice = input("Choose an option (1-3): ").strip()

        match choice:

            case "1":
                practitioner.calendar_show()
            case "2":
                practitioner.patient_dashboard()
            case "3":
                print("You have been logged out.")
                return
            case _:
                print("please print a number between 1-4: \n")



class mhwp:


    def __init__(self, practitioner_id, connection):
        self.practitioner_id = practitioner_id
        self.connection = connection

    def hi(self):

        print(f'Hello dear practitioner {self.practitioner_id}! \nHere are your appointments for the day:')


    def patient_dashboard(self):
        print("Here is your patient dashboard:\n")

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        dashboard_detail = cursor.execute('''
            SELECT pp.patient_id,
            u.name as patient_name,
            me.comment,
            me.score,
            me.created_at
            FROM patient_profiles AS pp
            JOIN users AS u
                ON u.user_id = pp.patient_id
            LEFT JOIN mood_entries AS me
                ON me.patient_id = pp.patient_id
            WHERE pp.assigned_practitioner_id = ?
            ORDER BY
                u.name,
                pp.patient_id,
                datetime(me.created_at),
                me.mood_entry_id;''',
            (self.practitioner_id,)
        )

        print("================================\n"
             "             PATIENT DASHBOARD\n"
             "================================\n"
             "Mood Scale: 1 = best, 6 = worst"

        )



        # Printing the rows so it can be shown in terminal



        rows = cursor.fetchall()
        for row in rows:
            print(row)

        cursor.close()
        connection.close()

    def calendar_show(self):
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()

        print("================================\n"
          "             CALENDAR\n"
          "================================")
        print("Enter 'q' to quit.\n")

        # SQL query to get the practitioner calendar
        cursor.execute('''
            SELECT u.name, a.scheduled_time, a.status
            FROM appointments as a
            JOIN users as u on a.patient_id = u.user_id
            WHERE practitioner_id = ? ;''',
            (practitioner_id,)
        )

        # Printing the rows so it can be shown in terminal
        rows = cursor.fetchall()
        for row in rows:
            print('\n\n',row)

        cursor.close()
        connection.close()

        print("================================\n"

            "================================")
        print("Enter 'q' to quit.\n")


# ghita = mhwp(practitioner_id)

# if __name__ == "__main__":
#
#    # ghita.calendar_show()
#    ghita.calendar_show()
#    mhwp_menu(connection, practitioner_id)
