'''
Code for patient booking appointment module
Patients are user_id = 4 and 5 for testing purposes
'''
import sqlite3
import datetime
from contextlib import closing
import calendar
DATABASE_PATH = "therapy_link.db"

#----------------- Appointment Menu ---------------------------------------------

def appointment_menu(connection,patient_id):
    while True:
        prac_id = get_practitioner_id(connection,patient_id)
        practitioner_name = get_practitioner_name(connection,prac_id)

        print(
            "\n================================\n"
            "         APPOINTMENT MENU\n"
            "================================\n\n"
            f"1. View Calender and Book Appointment with {practitioner_name}\n"
            "2. My Appointments [View and Cancel]\n"
            "3. Back to Main Menu"
        )
        choice = input("Choose an option (1-3): ").strip()

        match choice:
            case "1":
                booking_flow(connection,patient_id)
            case "2":
                booking_summary_flow(connection,patient_id)
            case "3":
                #patient_menu(connection,patient_id)
                return            
            case _:
                print("Please enter a number from 1 to 3.")



#----------------- User Input Functions ------------------------------------------------

max_number_of_days = 14 #Users can only look into booking appointments 2 weeks in advance
working_hours = range(9,17)
now = datetime.datetime.now().isoformat(timespec="seconds")

#Make the dates look pretty
def pretty_format(day):
    return day.strftime("%a %d/%m/%y")

#Ask the user for the date (to be used in asking for a range --> this has rules to make sure its a valid date)
def ask_user_for_date(prompt):
    today_date = datetime.date.today()
    while True:
        result = input(prompt).strip()
        if result.lower() in ('b','back'):
            return None
        elif result == "":
            return input("Enter a date (DD/MM) or B to go back:")
            continue

        split_date = result.split("/")
        #print(splited_date)
        if len(split_date) != 2 or not all(split_date[i].isdigit() for i in range(len(split_date))):
            print("Please enter a valid date as DD/MM - e.g. 11/18\n")
            continue

        day,month = int(split_date[0]),int(split_date[1])
        year = today_date.year

        try:
            chosen_date = datetime.date(year,month,day)
            #print(chosen_date)
        except ValueError:
            print("Thats not a valid date\n")
            continue

        if chosen_date < today_date: 
            print('Selected date is in the past\n')
            continue
    
        return chosen_date

#Selecting a date range in the appointment booking section
def ask_user_for_date_range():
    today_date = datetime.date.today()
    print("\nYou may check availabilty between a date range. Please note that you can only book 14 days in advance\n")
    while True:
        start_date = ask_user_for_date("Enter the start date in DD/MM format or press 'B' to go back to Appointment Menu\n")
        if start_date == 'B':
            return appointment_menu
        elif start_date is None: 
            return None
       
        end_date = ask_user_for_date("Enter the end date in DD/MM format\n")
        if end_date is None: 
            return None
        
        if end_date < start_date:
            print("Your end date cannot be earlier than your start date")
        elif end_date > today_date + datetime.timedelta(max_number_of_days):
            print(f"Appointments can only be booked up to {max_number_of_days} days ahead,"+str(today_date+datetime.timedelta(max_number_of_days)))
        else:
            print("Searching for slots between: ",pretty_format(start_date),"--",pretty_format(end_date),'\n')
            return start_date,end_date

def choose_slot(slots):
    while True:
        chosen = (input("Which slot would you like to book?\n")).strip()
        if chosen.lower() in ('b','back'):
            return None
        if chosen.isdigit() and int(chosen) in slots:
            return slots[int(chosen)]
        else:
            print(f"Please enter a number between 1 and {len(slots)}.")

def user_confirmation(question_asked):
    while True:
        answer = input(f"{question_asked}: (y/n)\n").strip().lower()
        if answer in ('y','yes'):
            return True
        elif answer in ('n','no'):
            return False
        else: 
            print('Please answer y or n')

#----------------- Appointment Booking ---------------------------------------------

#Get the assigned practioner's id to check their calendar
def get_practitioner_id(connection, patient_id):
    practitioner_id = connection.execute(
        """
        SELECT p.assigned_practitioner_id
        FROM patient_profiles p
        WHERE patient_id = ?
        """,
        (patient_id,),
    ).fetchone()

    return practitioner_id["assigned_practitioner_id"] if practitioner_id else None

#Get the name of the practioner to show when they press to book the appointment
def get_practitioner_name(connection, practitioner_id):
    result = connection.execute(
        "SELECT name FROM users WHERE user_id = ?", (practitioner_id,)
    ).fetchone()
    return result["name"] if result else "Not Available"


#Display available appointment slots for a practitioner    
def display_available_slots(connection,patient_id,practitioner_name, practitioner_id, startdate,enddate):
    #Get all appointments for the practitioner between 2 given dates
    #Example time in schema= 2026-11-13T11:00:00
    #SQL converts datetime into 2026-11-13<space>11:00:00 --> so all need to be converted using the isoformat to ensure that the time comparison can happen!!!

    print("\nShowing you Calendar for:",practitioner_name,'\n')

    start_of_day = datetime.datetime.combine(startdate, datetime.time(9,0)).isoformat(timespec="seconds") 
    end_of_day = datetime.datetime.combine(enddate, datetime.time(17,0)).isoformat(timespec="seconds")

    appointments = connection.execute(
                """
                SELECT scheduled_time,patient_id FROM appointments
                WHERE practitioner_id = ? 
                AND scheduled_time >= ? AND scheduled_time < ?
                AND status != 'cancelled'
                """,
                (practitioner_id, start_of_day, end_of_day),
            ).fetchall()
    

    #Get a list of all the booked timings (from the SQL)
    booked_times = {}
    for i in appointments:
        booked_times[datetime.datetime.fromisoformat(i["scheduled_time"])] = i["patient_id"]

    #Get all the available slots (not in booked_times) as a dictionary
    free_slots = {}
    num = 1
    day = startdate
    while day <= enddate:
        if day.weekday() < 5:                       
            print(f"\n{day:%A %d %B}")
            for hour in working_hours:
                slot = datetime.datetime.combine(day, datetime.time(hour, 0))
                if slot <= datetime.datetime.now():
                    continue                       
                if slot not in booked_times:
                    print(f"  {num:>2}. {slot:%H:%M}  free")
                    free_slots[num] = slot
                    num += 1
                elif booked_times[slot] == patient_id:
                    print(f"      {slot:%H:%M}  booked (you)")
                else:
                    print(f"      {slot:%H:%M}  booked")
        day += datetime.timedelta(1)
    return free_slots

#Function to make the appointment (INSERT into the appointment table on SQL)
def make_appointment(connection,patient_id,practioner_id,selected_appointment_time,practioner_name):

    try: 
        with connection:
            booking = connection.execute(
                """
                INSERT INTO appointments
                (patient_id, practitioner_id, scheduled_time, status, created_at)
                VALUES (?, ?, ?,'requested', ?)
                """,
                (patient_id,
                practioner_id,
                selected_appointment_time.isoformat(timespec="seconds"),
                datetime.datetime.now().isoformat(timespec="seconds")
                )
            )

    #Added a check to ensure that the booking is unique and not double booked  
    except sqlite3.IntegrityError as error:
        #print(error)
        if "UNIQUE" not in str(error):
            raise
        print("Sorry, that slot has just been taken. Please choose another.")
        return None
            
    print(f"Your request for {selected_appointment_time:%A %d %B} at {selected_appointment_time:%H:%M} has been sent.")
    print(f"It will be confirmed once {practioner_name} accepts it.\n")
    return booking.lastrowid

#----------------- The flow of the Appointment booking process ---------------------------------------------

'''
Patient selects to view the calendar/make an appointment from the menu page
--> Patient views the calendar
--> Prompted if they would like to make a booking?
--> Patient enters the dates they want to view  
---> Booking made
--> Confirmation
--> Back to the menu page
'''

def booking_flow(connection,patient_id):

    practitioner_id = get_practitioner_id(connection,patient_id)
    #print(practitioner_id)
    if practitioner_id is None:
        print("You have not been assigned a practioner, kindly reach out to the Administration")
        return None
     
    practitioner_name = get_practitioner_name(connection, practitioner_id)
    #print(practitioner_name)

    while True: 
        date_range = ask_user_for_date_range()
        #print(date_range)
        if date_range is None: 
            return None
        
        start_date,end_date = date_range
        #print(start_date)
        #print(end_date)
        
        slots = display_available_slots(connection,patient_id,practitioner_name,practitioner_id,start_date,end_date)
        if not slots: 
            return None
        
        chosen = choose_slot(slots)
        if chosen is None:
            return None
        
        if not user_confirmation(f"Book {chosen:%A %d %B} at {chosen:%H:%M} with {practitioner_name}?"):
            print("Nothing was booked.")
            return None

        appointment_id = make_appointment(connection, patient_id, practitioner_id, chosen,practitioner_name)
        if appointment_id is not None:
            return appointment_id

#----------------- Booking Summary and Cancellation ---------------------------------------------

def get_upcoming_appointments(connection, patient_id):
    """The patient's future appointments that are not cancelled, earliest first, as a list of Rows."""
    return connection.execute(
        """
        SELECT appointment_id, practitioner_id, scheduled_time, status FROM appointments
        WHERE patient_id = ? AND status != 'cancelled' AND scheduled_time >= ?
        ORDER BY scheduled_time
        """,
        (patient_id, datetime.datetime.now().isoformat(timespec="seconds")),
    ).fetchall()

def cancel_appointment(connection, appointment_id, patient_id):
    """Cancel one of the patient's own appointments and write an email to the patient and the MHWP.
    Returns True if it was cancelled, False if there was nothing to cancel."""
    with connection:                                  # all or nothing
        cursor = connection.execute(
            """
            UPDATE appointments SET status = 'cancelled'
            WHERE appointment_id = ? AND patient_id = ? AND status != 'cancelled'
            """,
            (appointment_id, patient_id),
        )
        if cursor.rowcount == 0:
            return False
        appointment = connection.execute(
            "SELECT practitioner_id, scheduled_time FROM appointments WHERE appointment_id = ?",
            (appointment_id,),
        ).fetchone()
        when = datetime.datetime.fromisoformat(appointment["scheduled_time"])
        sent_at = datetime.datetime.now().isoformat(timespec="seconds")
        for user_id in (patient_id, appointment["practitioner_id"]):
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

def booking_summary_flow(connection, patient_id):
    """Show the patient's upcoming appointments and let them cancel one."""
    while True:
        appointments = get_upcoming_appointments(connection, patient_id)
        if not appointments:
            print("\nYou have no upcoming appointments.")
            return

        print("\nYour upcoming appointments:")
        numbered = {}
        for number, row in enumerate(appointments, start=1):
            when = datetime.datetime.fromisoformat(row["scheduled_time"])
            name = get_practitioner_name(connection, row["practitioner_id"])
            print(f"  {number}. {when:%a %d %B at %H:%M}  with {name}  -  {row['status']}")
            numbered[number] = row["appointment_id"]

        choice = input("Enter a number to cancel that appointment, or B to go back: ").strip()
        if choice.lower() in ('b', 'back'):
            return
        if not (choice.isdigit() and int(choice) in numbered):
            print(f"Please enter a number between 1 and {len(numbered)}, or B.")
            continue

        if not user_confirmation("Cancel this appointment?"):
            print("Nothing was cancelled.")
            continue
        if cancel_appointment(connection, numbered[int(choice)], patient_id):
            print("Your appointment has been cancelled. A confirmation email has been sent.")
        else:
            print("That appointment could not be cancelled.")


#----------------- Running the Query / Testing ---------------------------------------------

with closing(sqlite3.connect(DATABASE_PATH)) as connection:
    connection.row_factory = sqlite3.Row  # lets you use row["column_name"]
    #print(display_calendar(connection, 4))
    #(display_available_slots(connection,"mhwp1","2",date.today()+datetime.timedelta(1),date.today()+datetime.timedelta(2)))
    #booking_flow(connection,4) 
    #appointment_menu(connection,4)
    #booking_summary(connection,4) 
    #user = connection.execute("SELECT * FROM users WHERE user_id = ?", (4,)).fetchone()
    #patient_menu(connection,user)
    #appointment_menu(connection,4)

#if __name__ == "__main__":
#    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
#        connection.row_factory = sqlite3.Row
#        appointment_menu(connection,4)
