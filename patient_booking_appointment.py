'''
Code for patient booking appointment module
Patients are user_id = 4 and 5 for testing purposes
'''
import sqlite3
import datetime
from contextlib import closing
import calendar
DATABASE_PATH = "therapy_link.db"
from sending_emails import send_out_email

#----------------- Appointment Menu ---------------------------------------------
#THIS IS THE VIEW THE PATIENT WILL SEE WHEN THEY PRESS 4 ON THE MAIN MENU
#OPTIONS ARE TO VIEW THE CALENDAR AND BOOK AN APPOINTMENT, VIEW APPOINTMENTS AND MAKE CANCELLATIONS, OR RETURN TO MAIN MENU

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
                #GOES BACK TO patient_menu
                return            
            case _:
                print("Please enter a number from 1 to 3.")



#----------------- User Input Functions ------------------------------------------------
#LISITNG HERE ALL THE INPUTS WE COULD POSSIBLY NEED FROM THE USER (E.G. DATES FOR CALENDAR SEARCHES)
max_number_of_days = 14 #Users can only look into booking appointments 2 weeks in advance
working_hours = range(9,17)

#MAKE THE DATE FORMAT LOOK PRETTY (CAN BE USED BY ANY TEAM)
def pretty_format(day):
    return day.strftime("%a %d/%m/%y")

#ASK THE USER FOR A DATE (MADE A FUNCTION TO REDUCE REPETITION WHEN ASKING FOR A DATE RANGE. ALSO CHECKS THE FORMAT OF THE DATE)
#CHECKS: WHETHER ITS A DIGIT, ONLY 2 VALUES (MONTH AND DAY), VALID DATE, IF ITS LESS THAN TODAYS DATE 
def ask_user_for_date(prompt):
    today_date = datetime.date.today()
    while True:
        result = input(prompt).strip()
        if result.lower() in ('b','back'):
            return None

        split_date = result.split("/") #CHECK THAT IT'S DIGIT AND ONLY 2 VALUES HAVE BEEN PROVIDED
        #print(split_date)
        if len(split_date) != 2 or not all(split_date[i].isdigit() for i in range(len(split_date))):
            print("Please enter a valid date as DD/MM - e.g. 11/12\n")
            continue

        day,month = int(split_date[0]),int(split_date[1]) 

        try:
            if month < today_date.month:
                year = today_date.year + 1 #DEFAULT YEAR = CURRENT YEAR BUT IF THE MONTH IS LESS THAN CURRENT MONTH THEN IT'S FOR NEXT YEAR
            else: 
                year = today_date.year
            chosen_date = datetime.date(year,month,day)
            #print(chosen_date)
        except ValueError:
            print("Thats not a valid date\n")
            continue

        if chosen_date < today_date: 
            print('Selected date is in the past\n')
            continue
    
        return chosen_date

#SELECTING A DATE RANGE TO ADD AS INPUT FOR VIEWING THE CALENDAR
#THE USER SHOULD ONLY ADD A RANGE BETWEEN NOW AND 2 WEEKS FROM NOW -- BECAUSE THEY CAN ONLY BOOK APPOINTMENTS WITHIN 2 WEEKS (THERES NO POINT IN LOOKING UP DATES BEYOND THAT)
def ask_user_for_date_range():
    today_date = datetime.date.today()
    max_date = today_date+datetime.timedelta(max_number_of_days)

    while True:
        start_date = ask_user_for_date("Enter the start date in DD/MM format or enter 'b' to go back to Appointment Menu\n")
        if start_date is None: 
            return None
        elif start_date > max_date:
            print(f"Appointments can only be booked up to {max_number_of_days} days ahead. Kindly enter a valid date")   
            return None 
       
        end_date = ask_user_for_date("Enter the end date in DD/MM format\n")
        if end_date is None: 
            return None
        
        if end_date < start_date:
            print("Your end date cannot be earlier than your start date")
        elif end_date > today_date + datetime.timedelta(max_number_of_days):
            print(f"Appointments can only be booked up to {max_number_of_days} days ahead,"+pretty_format(max_date))
        else:
            print("\nSearching for slots between: ",pretty_format(start_date),"--",pretty_format(end_date),'\n')
            return start_date,end_date

#ALLOW THE USER TO SELECT A SLOT TO BOOK 
def choose_slot(slots):
    while True:
        chosen = (input("\nWhich slot would you like to book? Enter 'b' to return to Appointment Menu\n")).strip()
        if chosen.lower() in ('b','back'):
            return None
        if chosen.isdigit() and int(chosen) in slots:
            return slots[int(chosen)]
        else:
            print(f"Please enter a number between 1 and {len(slots)}.")

#ASK USER CONFIRMATION (THIS FUNCTION TO BE USED BY THE TEAM) --> ONLY FOR YES OR NO QUESTIONS
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
#THIS SECTION REFERS TO APPOINTMENT BOOKING (WHEN THE USER PRESSES 1 ON THE APPOINTMENT MENU)

#GET THE PRACTITIONERS ID 
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

#GET THE PRACTITIONERS NAME --> TO SHOW IN SOME OF THE NOTIFICATIONS
def get_practitioner_name(connection, practitioner_id):
    result = connection.execute(
        "SELECT name FROM users WHERE user_id = ?", (practitioner_id,)
    ).fetchone()
    return result["name"] if result else "Not Available"

#USING CALENDAR LIBRARY TO SHOW THE CALENDAR IN A NICE FORMAT. SHOWS ONLY MONDAY TO FRIDAY (BLANKED OUT SAT AND SUNDAY)
def show_month(connection, practitioner_id, patient_id, year, month, first_day, last_day):
    month_start = datetime.date(year, month, 1)
    month_end = month_start + datetime.timedelta(calendar.monthrange(year, month)[1])
    rows = connection.execute(
        """
        SELECT scheduled_time, patient_id FROM appointments
        WHERE practitioner_id = ? AND scheduled_time >= ? AND scheduled_time < ?
        AND status != 'cancelled'
        """,
        (practitioner_id, month_start.isoformat(), month_end.isoformat()),
    ).fetchall()
    busy_days, my_days = set(), set() #USING A SET HERE SO WE DONT GET ANY DUPLICATES IN THE DAYS/TIMINGS
    for row in rows:
        day = datetime.datetime.fromisoformat(row["scheduled_time"]).day
        busy_days.add(day)
        if row["patient_id"] == patient_id:
            my_days.add(day)

    print(f"{calendar.month_name[month]} {year}".center(27))
    print("Mo  Tu  We  Th  Fr  Sa  Su")
    for week in calendar.monthcalendar(year, month):      
        line = ""
        week[-2] = 0 #Saturday = empty --> PRACTIONERS DONT WORK ON WEEKENDS
        week[-1] = 0 #Sunday = empty
        
        for day in week:
            #print(day)
            if day == 0:
                line += "    "
            elif not (first_day <= datetime.date(year, month, day) <= last_day):
                line += " .  "                            
            else:
                mark = "+" if day in my_days else ("*" if day in busy_days else " ")
                line += f"{day:>2}{mark} "
        print(line)
    print("* = has bookings   + = includes your booking   . = not in your range") #PRINTING THE KEY FOR THE USER TO UNDERSTAND

#ABOVE WAS TO SHOW THE CALENDAR (ONLY FOR AESTHETICS AND TO SHOW A CALENDAR)
#THE ACTUAL BOOKING OF APPOINTMENTS IS DONE USING THE DISPLAY_AVAILABLE_SLOTS FUNCTION
  
def display_available_slots(connection,patient_id, practitioner_id, startdate,enddate):
    #GET ALL APPOINTMENTS BETWEEN THE TWO DATES THAT WERE INSERTED BY THE USER 
    #Example time in schema= 2026-11-13T11:00:00
    #SQL converts datetime into 2026-11-13<space>11:00:00 --> so all need to be converted using the isoformat to ensure that the time comparison can happen!!!

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

#USER SELECTS A SLOT --> APPOINTMENT IS MADE BY INSERTING THE APPOINTMENT INTO THE APPOINTMENTS TABLE IN SQL
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
#PUTTING TOGETHER ALL THE FUNCTIONS FOR THE APPOINTMENT BOOKING PROCESS (WHEN THE USER PRESSES 1)
'''
Appointment Booking Flow:
Patient selects to view the calendar/make an appointment from the menu page (press 1)
--> Patient views the calendar
--> Prompted if they would like to make a booking?
--> Patient enters the dates they want to view (the index/the number associated to the date and time of appointment)
--> Booking made
--> Patient told that the booking has been REQUESTED (confirmation will be sent by the practitioner)
--> Back to the menu page
'''

def booking_flow(connection,patient_id):

    today_date = datetime.date.today()

    practitioner_id = get_practitioner_id(connection,patient_id)
    #print(practitioner_id)
    if practitioner_id is None:
        print("You have not been assigned a practioner, kindly reach out to the Administration")
        return None
     
    practitioner_name = get_practitioner_name(connection, practitioner_id)
    #print(practitioner_name)

    default_last_date = today_date + datetime.timedelta(max_number_of_days)
    print(f"\nPlease note that you can only book {max_number_of_days} days in advance. You may check availabilty between",pretty_format(today_date),"and ",pretty_format(default_last_date),".\n")

    while True: 
        date_range = ask_user_for_date_range()
        #print(date_range)
        if date_range is None: 
            return None
        
        start_date,end_date = date_range
        #print(start_date)
        #print(end_date)

        #print("Showing you Calendar for:",practitioner_name,'\n')

        if start_date.month == end_date.month:
            (show_month(connection,practitioner_id,patient_id,start_date.year,start_date.month,start_date,end_date))
        else: 
            (show_month(connection,practitioner_id,patient_id,start_date.year,start_date.month,start_date,end_date))
            (show_month(connection,practitioner_id,patient_id,end_date.year,end_date.month,start_date,end_date))

        #display = show_month(connection,practitioner_id,patient_id,2026,12,start_date,end_date)
        #print(display)
        
        slots = display_available_slots(connection,patient_id,practitioner_id,start_date,end_date)
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
#THIS SECTION IS FOR VIEWING THE APPOINTMENTS (WHEN THE PATIENT PRESSES 2 ON THE APPOINTMENT MENU)

def get_upcoming_appointments(connection, patient_id):
    return connection.execute(
        """
        SELECT appointment_id, practitioner_id, scheduled_time, status FROM appointments
        WHERE patient_id = ? AND scheduled_time >= ?
        ORDER BY scheduled_time
        """,
        (patient_id, datetime.datetime.now().isoformat(timespec="seconds")),
    ).fetchall()

def print_bookings(connection, title, rows, index=None):
    print(f"\n{title}:")
    if not rows:
        print("  None")
    for row in rows:
        when = datetime.datetime.fromisoformat(row["scheduled_time"])
        name = get_practitioner_name(connection, row["practitioner_id"])
        if index is None: #for those cancelled there should be no number so it doesn't affect when trying to cancel                                  
            print(f"     {when:%a %d %B at %H:%M}  with {name}")
        else:
            number = len(index) + 1                        
            index[number] = row["appointment_id"]
            print(f"  {number}. {when:%a %d %B at %H:%M}  with {name}")


def cancel_appointment(connection, appointment_id, patient_id):
#THE PATIENT CAN CANCEL THEIR APPOINTMENT >>> THIS TRIGGERS AN EMAIL TO BE SENT TO THE PATIENT AND THE PRACTITIONER
#THIS SECTION WOULD NEED TO BE COORDINATED WITH THE MHWP GROUP --> We need to make sure that the cancelled ones are shown as free slots.
# + Need to check that when a practioner makes a change to the status (i.e confirms it) it shows up correctly under Booking Summary
    
    with connection:                                  
        cancelled = connection.execute(
            """
            UPDATE appointments SET status = 'cancelled'
            WHERE appointment_id = ? AND patient_id = ? AND status != 'cancelled'
            """,
            (appointment_id, patient_id),
        )
        if cancelled.rowcount == 0: #Returns True if it was cancelled, False if there was nothing to cancel
            return False
        send_out_email(connection, appointment_id, 'cancellation') #Function under sending_emails.py to send out the email when the cancellation is done
    return True

#Show patients' upcoming and cancelled appointments in different sections 
def booking_summary_flow(connection, patient_id):
    while True:
        appointments = get_upcoming_appointments(connection, patient_id)
        if not appointments:
            print("\nYou have no appointments booked,requested or cancelled.")
            return

        #Sort the appointments into the three groups by their status
        confirmed = [row for row in appointments if row["status"] == "confirmed"]
        requested = [row for row in appointments if row["status"] == "requested"]
        cancelled = [row for row in appointments if row["status"] == "cancelled"]

        index = {}                                         
        print_bookings(connection, "Upcoming Bookings", confirmed, index)
        print_bookings(connection, "Requested Bookings", requested, index)
        print_bookings(connection, "Cancelled Bookings", cancelled) #no index parsed in the function call --> cancelled appointments wont be numbered as they cant be cancelled again
        print()

        if not index:                                      
            input("Press Enter to go back: ")
            return

        choice = input("Enter a number to cancel that appointment, or 'b' to go back: ").strip()
        if choice.lower() == 'b':
            return
        if not (choice.isdigit() and int(choice) in index):
            print(f"Please enter a number between 1 and {len(index)}, or 'b'.")
            continue

        if not user_confirmation("Cancel this appointment?"):
            print("Nothing was cancelled.")
            continue
        if cancel_appointment(connection, index[int(choice)], patient_id):
            print("Your appointment has been cancelled. A confirmation email has been sent.")
            return
        else:
            print("That appointment could not be cancelled.")
            return

#----------------- Running the Query / Testing ---------------------------------------------

#with closing(sqlite3.connect(DATABASE_PATH)) as connection:
    #connection.row_factory = sqlite3.Row  # lets you use row["column_name"]
    #print(display_calendar(connection, 4))
    #(display_available_slots(connection,"mhwp1","2",date.today()+datetime.timedelta(1),date.today()+datetime.timedelta(2)))
    #booking_flow(connection,4) 
    #appointment_menu(connection,4)
    #booking_summary_flow(connection,4) 
    #user = connection.execute("SELECT * FROM users WHERE user_id = ?", (4,)).fetchone()
    #patient_menu(connection,user)
    #appointment_menu(connection,4)
