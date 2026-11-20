import sqlite3
from utils import is_valid_name, is_valid_email

from admin_db import (
    get_unallocated_patients,
    get_active_mhwps,
    allocate_patient,
    get_users_for_edit,
    update_user_detail,
    get_user_statuses,
    get_patient_allocations,
    get_mhwp_patient_counts,
    get_mhwp_weekly_bookings,
    get_weekly_booking_totals,
    get_users_for_disable,
    disable_user,
    get_disable_impact,
    delete_user
)

# Check that the Admin selects a valid menu number

def choose_number(prompt, maximum):
    while True:
        choice = input(prompt).strip()

        if choice.isdigit() and 0 <= int(choice) <= maximum:
            return int(choice)

        print(f"Please enter a number from 0 to {maximum}.")

# Ask the Admin to confirm an action

def confirm_action(prompt):
    while True:
        answer = input(prompt).strip().lower()

        if answer == "y":
            return True

        elif answer == "n":
            return False

        else:
            print("Please enter y or n.")



# A3 - Ask for a new value and validate it

def ask_new_value(field_number):
    while True:
        value = input("Enter new value (0 to cancel): ").strip()

        if value == "0":
            return None

        if field_number == 1:
            valid = 2 <= len(value) <= 60 and is_valid_name(value)

        elif field_number == 2:
            valid = is_valid_email(value)

        else:
            valid = value == "" or is_valid_email(value)

        if valid:
            return value

        print("Invalid value. Please try again.")




# A2a - Display patients and available MHWPs

def show_unallocated_patients(connection):
    patients = get_unallocated_patients(connection)
    mhwps = get_active_mhwps(connection)

    print("\n================================")
    print("       ALLOCATE PATIENT")
    print("================================")

    if not patients:
        print("All active patients have an assigned MHWP.")
        return

    print("\nUnallocated patients:\n")

    for number, patient in enumerate(patients, start=1):
        print(f"{number}. {patient[1]}")

    if not mhwps:
        print("\nNo active MHWPs are available.")
        return

    print("\nAvailable MHWPs:\n")

    for number, mhwp in enumerate(mhwps, start=1):
        print(f"{number}. {mhwp[1]}")

    print("\nEnter 0 to cancel.")


    # Step 1 - Select a patient
    patient_number = choose_number(
        "\nChoose a patient: ", len(patients)
    )

    if patient_number == 0:
        print("Allocation cancelled.")
        return

    # Step 2 - Select an MHWP
    mhwp_number = choose_number(
        "Choose an MHWP: ", len(mhwps)
    )

    if mhwp_number == 0:
        print("Allocation cancelled.")
        return

    # Step 3 - Retrieve the selected records
    patient = patients[patient_number - 1]
    mhwp = mhwps[mhwp_number - 1]

    print(f"\nSelected: {patient[1]} -> {mhwp[1]}")

    confirmed = confirm_action("Confirm allocation? (y/n): ")

    if not confirmed:
        print("Allocation cancelled. No changes saved.")
        return


    success = allocate_patient(connection, patient[0], mhwp[0])

    if success:
        print(f"Successfully allocated {patient[1]} to {mhwp[1]}.")
    else:
        print("Allocation failed. Please check that both users are eligible.")




# A3 - Display patients and MHWPs whose details can be managed

def show_users_for_edit(connection):
    users = get_users_for_edit(connection)

    print("\n================================")
    print("        EDIT USER DETAILS")
    print("================================")

    if not users:
        print("No patients or MHWPs found.")
        return

    print("\nRegistered users:\n")

    # Step 1 - Display all users
    for number, user in enumerate(users, start=1):
        print(f"{number}. {user[1]} ({user[2]}, {user[3]})")

    # Step 2 - Let the Admin choose a user
    print("\n0. Back")

    user_number = choose_number(
        "\nChoose a user: ", len(users)
    )

    if user_number == 0:
        print("Returning to Admin menu.")
        return

    # Step 3 - Retrieve the selected user
    selected_user = users[user_number - 1]

    # Step 4 - Check whether the account is disabled
    if selected_user[3] == "disabled":
        print("This account is disabled and cannot be edited.")
        return

    print(f"\nSelected: {selected_user[1]} ({selected_user[2]})")
    
    # Step 5 - Display fields that can be edited
    print("\nWhich detail would you like to edit?")
    print("1. Name")
    print("2. Email")

    if selected_user[2] == "patient":
        print("3. Emergency contact email")
        maximum = 3
    else:
        maximum = 2

    print("0. Back")

    # Step 6 - Let the Admin select a field
    field_number = choose_number(
        "\nChoose a field: ", maximum
    )

    if field_number == 0:
        print("Editing cancelled.")
        return

    fields = ["Name", "Email", "Emergency contact email"]
    selected_field = fields[field_number - 1]

    print(f"\nSelected field: {selected_field}")


    # Step 7 - Ask for a new, valid value
    new_value = ask_new_value(field_number)

    if new_value is None:
        print("Editing cancelled. No changes saved.")
        return


    # Step 8 - Save the new value
    success = update_user_detail(
        connection,
        selected_user[0],
        field_number,
        new_value
    )

    if success:
        print(f"\nSuccessfully updated {selected_field} for {selected_user[1]}.")
    else:
        print("Update failed. Please check that the account is active.")


# A4 - Display the Delete User workflow

def show_delete_user(connection):
    users = get_users_for_edit(connection)

    print("\n================================")
    print("           DELETE USER")
    print("================================")

    if not users:
        print("No patients or MHWPs found.")
        return

    # Step 1 - Display users
    for number, user in enumerate(users, start=1):
        print(f"{number}. {user[1]} ({user[2]}, {user[3]})")

    print("\n0. Back")

    # Step 2 - Select a user
    user_number = choose_number(
        "\nChoose a user: ", len(users)
    )

    if user_number == 0:
        print("Deletion cancelled.")
        return

    selected_user = users[user_number - 1]

    # Step 3 - Show the consequences
    bookings, patients = get_disable_impact(
        connection, selected_user[0]
    )

    print(f"\nDeleting {selected_user[1]} will:")
    print("- Permanently remove their account and related records")
    print(f"- Remove {len(bookings)} future live booking(s)")

    if bookings:
        print("- Record cancellation emails for both sides")

    if selected_user[2] == "practitioner":
        print(f"- Unallocate {len(patients)} patient(s)")

    # Step 4 - Confirm deletion
    confirmed = confirm_action("\nDelete? (y/n): ")

    if not confirmed:
        print("Deletion cancelled. No changes saved.")
        return

    # Step 5 - Delete from the database
    try:
        success = delete_user(connection, selected_user[0])
    except (sqlite3.Error, RuntimeError) as error:
        print(f"Deletion failed. No changes saved: {error}")
        return

    if success:
        print(f"Successfully deleted {selected_user[1]}.")
    else:
        print("Unable to delete this user.")




# A5 - Disable User workflow

def show_disable_user(connection):
    users = get_users_for_disable(connection)

    print("\n================================")
    print("          DISABLE USER")
    print("================================")

    if not users:
        print("No active patients or MHWPs found.")
        return

    for number, user in enumerate(users, start=1):
        print(f"{number}. {user[1]} ({user[2]})")

    print("\n0. Back")

    user_number = choose_number(
        "\nChoose a user: ", len(users)
    )

    if user_number == 0:
        print("Action cancelled.")
        return

    selected_user = users[user_number - 1]


    # Show consequences before confirmation
    bookings, patients = get_disable_impact(
        connection, selected_user[0]
    )

    names = ", ".join(patient[0] for patient in patients)

    print(f"\nDisabling {selected_user[1]} will:")
    print(f"- Cancel {len(bookings)} future booking(s)")
    print("- Record cancellation emails for both sides")
    print(f"- Unallocate {len(patients)} patient(s): {names or 'None'}")

    confirmed = confirm_action("\nContinue? (y/n): ")


    if not confirmed:
        print("Action cancelled. No changes saved.")
        return

    success = disable_user(connection, selected_user[0])

    if success:
        print(f"Successfully disabled {selected_user[1]}.")
    else:
        print("Unable to disable this user.")




# A7 - Display the basic Admin summary

def show_admin_summary(connection):
    users = get_user_statuses(connection)

    print("\n================================")
    print("          ADMIN SUMMARY")
    print("================================")

    print("\nUSERS\n")

    for role in ["admin", "practitioner", "patient"]:
        total = 0
        disabled = 0

        for user in users:
            if user[0] == role:
                total += 1

                if user[1] == "disabled":
                    disabled += 1

        print(f"{role}: {total} total, {disabled} disabled")


    # Step 2 - Show number of patients per MHWP
    mhwps = get_mhwp_patient_counts(connection)

    print("\nMHWPs\n")

    for mhwp in mhwps:
        print(f"{mhwp[0]}: {mhwp[1]} patient(s)")


    # Step 3 - Display weekly appointments per MHWP
    bookings = get_mhwp_weekly_bookings(connection)

    print("\nBOOKINGS THIS WEEK BY MHWP\n")

    for booking in bookings:
        print(f"{booking[0]}: {booking[1]} confirmed, {booking[2]} requested")


    # Step 4 - Display patient allocations
    patients = get_patient_allocations(connection)

    print("\nALLOCATIONS\n")

    found = False

    for patient in patients:
        if patient[1] is not None:
            print(f"{patient[0]} -> {patient[1]}")
            found = True

    if not found:
        print("None")

    # Step 5 - Display unallocated patients
    print("\nUNALLOCATED PATIENTS\n")

    found = False

    for patient in patients:
        if patient[1] is None:
            name = patient[0]

            if patient[2] == "disabled":
                name += " (disabled)"

            print(name)
            found = True

    if not found:
        print("None")


    # Step 6 - Show total weekly bookings by status
    bookings = get_weekly_booking_totals(connection)

    totals = {
        "requested": 0,
        "confirmed": 0,
        "cancelled": 0
    }

    for booking in bookings:
        status = booking[0]
        count = booking[1]

        if status in totals:
            totals[status] = count

    print("\nBOOKINGS THIS WEEK BY STATUS\n")
    print(f"Requested: {totals['requested']}")
    print(f"Confirmed: {totals['confirmed']}")
    print(f"Cancelled: {totals['cancelled']}")



   





# Display admin menu

def admin_menu(connection, admin_id):
    while True:
        print(
            "\n================================\n"
            "          ADMIN MENU\n"
            "================================\n"
            "1. Allocate patient\n"
            "2. Edit user details\n"
            "3. Delete user\n"
            "4. Disable user\n"
            "5. Admin summary\n"
            "6. Log out\n"
        )

        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            show_unallocated_patients(connection)

        elif choice == "2":
            show_users_for_edit(connection)

        elif choice == "3":
            show_delete_user(connection)

        elif choice == "4":
            show_disable_user(connection)

        elif choice == "5":
            show_admin_summary(connection)


        elif choice == "6":
            print("You have been logged out.")
            return

        else:
            print("Please enter a number from 1 to 6.")
