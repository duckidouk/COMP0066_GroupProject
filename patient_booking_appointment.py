'''
Code for patient booking appointment module
Patients are user_id = 4 and 5 for testing purposes
'''
import sqlite3
import datetime
from contextlib import closing
from datetime import date
import calendar
DATABASE_PATH = "therapy_link.db"

#----------------- User Input Functions ------------------------------------------------

max_number_of_days = 14 #Users can only look into booking appointments 2 weeks in advance

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
            return input("Enter a date (DD/MM) or B to go back:").strip()

        split_date = result.split("/")
        #print(splited_date)
        if len(split_date) != 2 or not all(split_date[i].isdigit() for i in range(len(split_date))):
            print("Please enter a valid date as DD/MM - e.g. 11/18")
            continue

        day,month = int(split_date[0]),int(split_date[1])
        year = today_date.year

        try:
            chosen_date = datetime.date(year,month,day)
            #print(chosen_date)
        except ValueError:
            print("Thats not a valid date")
            continue

        if chosen_date < today_date: 
            print('Selected date is in the past')
            continue
    
        return chosen_date

#Selecting a date range
def ask_user_for_date_range():
    today_date = datetime.date.today()
    while True:
        start_date = ask_user_for_date("Enter the start date in DD/MM format\n")
        if start_date is None: 
            return None
        end_date = ask_user_for_date("Enter the end date in DD/MM format\n")
        if end_date is None: 
            return None
        if end_date < start_date:
            print("Your end date cannot be earlier than your start date")
        elif end_date > today_date + datetime.timedelta(max_number_of_days):
            print(f"Appointments can only be booked up to {max_number_of_days} days ahead,"+str(today_date+datetime.timedelta(max_number_of_days)))
        else:
            print("Searching for slots between: ",pretty_format(start_date),"--",pretty_format(end_date))
            return start_date,end_date

def choose_slot(slots):
    while True:
        chosen = (input("Which slot would you like to book?")).strip()
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


#----------------- Appointment Booking / Checking Calendar Code ---------------------------------------------

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

#Display the calendar 
def display_calendar(connection,practitioner_id):
    practitioner_name = get_practitioner_name(connection,practitioner_id)
    print("\nShowing you Calendar for:",practitioner_name)
    today = datetime.datetime.now()
    month = today.month
    year = today.year

    #Number of days between in a month <------- BE ABLE TO LOOK AT NEXT MONTH's CALENDAR?
    no_of_days = calendar.monthrange(year,month)[1]
    month_beginning = datetime.date(year,month,1)
    month_end = month_beginning + datetime.timedelta(no_of_days)
    pract_calendar = connection.execute(
            """
            SELECT scheduled_time FROM appointments
            WHERE practitioner_id = ? 
            AND scheduled_time >= ? AND scheduled_time < ?
            AND status != 'cancelled'
            """,
            (practitioner_id, month_beginning, month_end),
        ).fetchall()

    return pract_calendar


#Display available appointment slots for a practitioner    
def display_available_slots(connection,practitioner_name, practitioner_id, startdate,enddate):
    #Get all appointments for the practitioner between 2 given dates
    #Example time in schema= 2026-11-13T11:00:00
    #SQL converts datetime into 2026-11-13<space>11:00:00 --> so all need to be converted using the isoformat to ensure that the time comparison can happen!!!

    print("\nShowing you Calendar for:",practitioner_name)

    start_of_day = datetime.datetime.combine(startdate, datetime.time(9,0)).isoformat(timespec="seconds") 
    end_of_day = datetime.datetime.combine(enddate, datetime.time(17,0)).isoformat(timespec="seconds")
    now = datetime.datetime.now()

    appointments = connection.execute(
                """
                SELECT scheduled_time FROM appointments
                WHERE practitioner_id = ? 
                AND scheduled_time >= ? AND scheduled_time < ?
                AND status != 'cancelled'
                """,
                (practitioner_id, start_of_day, end_of_day),
            ).fetchall()
    

    #Get a list of all the booked timings (from the SQL)
    booked_times = []
    for i in appointments:
        booked_times.append(datetime.datetime.fromisoformat(i["scheduled_time"]))

    #Get all the available slots (not in booked_times) as a dictionary
    dict_available_slots = {}
    num = 1
    while startdate <= enddate:
        if startdate.weekday() < 5: #Only working Monday-Friday <--- TO BE DISCUSSED
            for hour in range(9,17):
                slot = datetime.datetime.combine(startdate,datetime.time(hour,0))
                if slot not in booked_times and slot > now:
                    dict_available_slots[num] = slot
                    num += 1
        startdate += datetime.timedelta(1) 

    #If there are no available slots then user will be notified
    if not dict_available_slots:
        print("No available slots in that period.")
        return dict_available_slots
    
    #This is added to make it more readable for the user
    current_day = None
    for number, slot in dict_available_slots.items():
        if slot.date() != current_day:
            current_day = slot.date()
            print(f"\n{slot:%A %d %B}")
        print(f"  {number:>2}. {slot:%H:%M}")

    return dict_available_slots

#Function to make the appointment (INSERT into the appointment table on SQL)
def make_appointment(connection,patient_id,practioner_id,selected_appointment_time):

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
        print(error)
        if "UNIQUE" not in str(error):
            raise
        print("Sorry, that slot has just been taken. Please choose another.")
        return None
            
    print('Your appointment has been booked for:',selected_appointment_time)
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
        
        slots = display_available_slots(connection,practitioner_name,practitioner_id,start_date,end_date)
        if not slots: 
            return None
        
        chosen = choose_slot(slots)
        if chosen is None:
            return None
        
        if not user_confirmation(f"Book {chosen:%A %d %B} at {chosen:%H:%M} with {practitioner_name}?"):
            print("Nothing was booked.")
            return None

        appointment_id = make_appointment(connection, patient_id, practitioner_id, chosen)
        if appointment_id is not None:
            return appointment_id

#----------------- Running the Query ---------------------------------------------
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
            case "4":
                booking_flow(connection,patient_id)
            case "5":
                print("This feature will be available when its module is integrated.")
            case "6":
                print("You have been logged out.")
                return
            case _:
                print("Please enter a number from 1 to 6.")


with closing(sqlite3.connect(DATABASE_PATH)) as connection:
    connection.row_factory = sqlite3.Row  # lets you use row["column_name"]
    #print(get_practitioner_id(connection, 4))
    #(display_available_slots(connection,"mhwp1","2",date.today()+datetime.timedelta(1),date.today()+datetime.timedelta(2)))
    #booking_flow(connection,4)  
    

    user = connection.execute("SELECT * FROM users WHERE user_id = ?", (4,)).fetchone()
    patient_menu(connection, user)


