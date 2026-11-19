# after login -- the menu should appear
import sqlite3
import datetime
from patient_booking_appointment import user_confirmation

DATABASE_PATH = "therapy_link.db"

connection = sqlite3.connect(DATABASE_PATH)
cursor = connection.cursor()


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
                try:
                    practitioner.calendar_flow()
                except TypeError:
                    print("There is a type error, expecting tuple. Contact DB administraror")
                except Exception as e:
                    print(f"an error occured: {e}")

            case "2":
                practitioner.patient_dashboard()

            case "3":
                print("You have been logged out.")
                return

            case _:
                print("please print a number between 1-3: \n")



class mhwp:

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()


    def __init__(self, practitioner_id, connection):
        self.practitioner_id = practitioner_id
        self.connection = connection

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
#
#     def calendar_show(self):
#         connection = sqlite3.connect(DATABASE_PATH)
#         cursor = connection.cursor()


    def get_upcoming_appointments(self):
        # connection = sqlite3.connect(DATABASE_PATH)
        # cursor = connection.cursor()

        """The practitioner future appointments, earliest first as a list of Rows."""
        return self.connection.execute(
            """
            SELECT a.appointment_id, a.scheduled_time, a.status,
            u.name AS patient_name
            FROM appointments as a
            JOIN users as u on u.user_id = a.patient_id
            WHERE a.practitioner_id = ? AND a.scheduled_time >= ?
            ORDER BY a.scheduled_time
            """,
            (self.practitioner_id, datetime.datetime.now().isoformat(timespec="seconds")),
        ).fetchall()

        # cursor.close()
        # connection.close()
    def b_for_return(self):

        while True:
           choice = input("Press b to return at the main menu").strip().lower()

           if choice == 'b':
               return
           else:
               print('Please press b to return: ')
               continue
    def cancel_appointment(self, appointment_id):
        #Cancel one of the patient's own appointments and write an email to the patient and the MHWP.
        #Returns True if it was cancelled, False if there was nothing to cancel
        #THIS SECTION WOULD NEED TO BE COORDINATED WITH THE MHWP GROUP --> We need to make sure that the cancelled ones are shown as free slots.
        # + Need to check that when a practioner makes a change to the status (i.e confirms it) it shows up correctly under Booking Summary
        connection = self.connection

        with connection:
            cursor = connection.execute(
                """
                UPDATE appointments SET status = 'cancelled'
                WHERE appointment_id = ? AND practitioner_id = ? AND status != 'cancelled'
                """,
                (appointment_id, self.practitioner_id),
            )
            if cursor.rowcount == 0:
                return False
            appointment = connection.execute(
                "SELECT patient_id, scheduled_time FROM appointments WHERE appointment_id = ?",
                (appointment_id,),
            ).fetchone()
            when = datetime.datetime.fromisoformat(appointment["scheduled_time"])
            sent_at = datetime.datetime.now().isoformat(timespec="seconds")
            for user_id in (appointment["patient_id"], self.practitioner_id):
                user = connection.execute(
                    "SELECT email FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                connection.execute(
                    """
                    INSERT INTO emails (to_user_id, to_address, subject, body, sent_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, user["email"], "Appointment cancelled",
                    f"The appointment on {when:%A %d %B} at {when:%H:%M} has been cancelled.",
                    sent_at),
                )
        return True

    def confirm_appointment(self, appointment_id):
        connection = self.connection

        with connection:
            cursor = connection.execute(
                """
                UPDATE appointments SET status = 'confirmed'
                WHERE appointment_id = ? AND practitioner_id = ? AND status != 'confirmed'
                """,
                (appointment_id, self.practitioner_id),
            )
            if cursor.rowcount == 0:
                return False
            appointment = connection.execute(
                "SELECT patient_id, scheduled_time FROM appointments WHERE appointment_id = ?",
                (appointment_id,),
            ).fetchone()
            when = datetime.datetime.fromisoformat(appointment["scheduled_time"])
            sent_at = datetime.datetime.now().isoformat(timespec="seconds")
            for user_id in (appointment["patient_id"], self.practitioner_id):
                user = connection.execute(
                    "SELECT email FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                connection.execute(
                    """
                    INSERT INTO emails (to_user_id, to_address, subject, body, sent_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, user["email"], "Appointment cancelled",
                    f"The appointment on {when:%A %d %B} at {when:%H:%M} has been cancelled.",
                    sent_at),
                )
        return True



    def calendar_flow(self):
        actions_for_status = {
            "requested": ("confirm", "cancel", "back"),
            "confirmed": ("cancel", "back"),
            "cancelled": ("back",),
        }

        while True:
            appointments = self.get_upcoming_appointments()
            if not appointments:
                print("\nYou have no upcoming appointments.")
                self.b_for_return()
                return

            print("\nYour upcoming appointments:")
            numbered = {}
            for number, row in enumerate(appointments, start=1):
                when = datetime.datetime.fromisoformat(row["scheduled_time"])
                print(
                    f"  {number}. {when:%a %d %B at %H:%M} "
                    f"with {row['patient_name']} - {row['status']}"
                )
                numbered[str(number)] = row


            while True:
                choice = input("Enter an appointment number or B to go back: ").strip().lower()
                if choice in ("b", "back"):
                    return
                if choice in numbered:
                    break
                print(f"Please enter a number between 1 and {len(numbered)}, or press B to go back.")

            appointment = numbered[choice]
            actions = actions_for_status[appointment["status"]]

            while True:
                action = input(f"{' / '.join(actions)}: ").strip().lower()
                if action == "b":
                    action = "back"
                if action == "c":
                    print("please enter confirm or cancelled")
                    continue
                if action in actions:
                    break
                print("That action is unavailable for this booking.")

            if action == "back":
                continue
            if not user_confirmation(f"{action.capitalize()} this booking"):
                print("No change made.")
                continue

            appointment_id = appointment["appointment_id"]
            if action == "confirm":
                updated = self.confirm_appointment(appointment_id)
                new_status = "confirmed"
            else:
                updated = self.cancel_appointment(appointment_id)
                new_status = "cancelled"

            if updated:
                print(f"Appointment {new_status}.")
            else:
                print("This booking could not be updated.")






    #
    #         choice = input("Enter a number to cancel that appointment, or B to go back: ").strip()
    #         if choice.lower() in ('b', 'back'):
    #             return
    #         if not (choice.isdigit() and int(choice) in numbered):
    #             print(f"Please enter a number between 1 and {len(numbered)}, or B.")
    #             continue
    #
    #         if not user_confirmation("Cancel this appointment?"):
    #             print("Nothing was cancelled.")
    #             continue
    #         if cancel_appointment(connection, numbered[int(choice)], patient_id):
    #             print("Your appointment has been cancelled. A confirmation email has been sent.")
    #         else:
    #             print("That appointment could not be cancelled.")

    cursor.close()
    connection.close()
