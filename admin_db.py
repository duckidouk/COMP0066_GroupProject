from datetime import date, timedelta, datetime

# A2a - Allocate an unallocated patient to an MHWP

def get_unallocated_patients(connection):
    return connection.execute(
        """
        SELECT u.user_id, u.name
        FROM users AS u
        JOIN patient_profiles AS p
            ON u.user_id = p.patient_id
        WHERE u.role = 'patient'
          AND u.account_status = 'active'
          AND p.assigned_practitioner_id IS NULL
        ORDER BY u.name
        """
    ).fetchall()



# A2a - Find active mental health practitioners

def get_active_mhwps(connection):
    return connection.execute(
        """
        SELECT user_id, name
        FROM users
        WHERE role = 'practitioner'
          AND account_status = 'active'
        ORDER BY name
        """
    ).fetchall()


# A2a - Save the patient allocation

def allocate_patient(connection, patient_id, mhwp_id):

    # Check that the patient is active and not already allocated
    patient = connection.execute(
        """
        SELECT u.user_id
        FROM users AS u
        JOIN patient_profiles AS p
            ON u.user_id = p.patient_id
        WHERE u.user_id = ?
          AND u.role = 'patient'
          AND u.account_status = 'active'
          AND p.assigned_practitioner_id IS NULL
        """,
        (patient_id,)
    ).fetchone()

    if patient is None:
        return False

    # Check that the selected MHWP is active
    mhwp = connection.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
          AND role = 'practitioner'
          AND account_status = 'active'
        """,
        (mhwp_id,)
    ).fetchone()

    if mhwp is None:
        return False

    # Save the allocation
    result = connection.execute(
        """
        UPDATE patient_profiles
        SET assigned_practitioner_id = ?
        WHERE patient_id = ?
          AND assigned_practitioner_id IS NULL
        """,
        (mhwp_id, patient_id)
    )

    connection.commit()

    return result.rowcount == 1


# A3 - Get patients and MHWPs for the Admin to manage

def get_users_for_edit(connection):
    return connection.execute(
        """
        SELECT user_id, name, role, account_status
        FROM users
        WHERE role IN ('patient', 'practitioner')
        ORDER BY role, name
        """
    ).fetchall()



# A3 - Update a patient's or MHWP's details

def update_user_detail(connection, user_id, field_number, new_value):

    # Check that the user exists and is active
    user = connection.execute(
        """
        SELECT role, account_status
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    if user is None:
        return False

    if user[0] == "admin" or user[1] != "active":
        return False

    # Update the selected field
    if field_number == 1:
        result = connection.execute(
            "UPDATE users SET name = ? WHERE user_id = ?",
            (new_value, user_id)
        )

    elif field_number == 2:
        result = connection.execute(
            "UPDATE users SET email = ? WHERE user_id = ?",
            (new_value, user_id)
        )

    elif field_number == 3 and user[0] == "patient":
        result = connection.execute(
            """
            UPDATE patient_profiles
            SET emergency_contact_email = ?
            WHERE patient_id = ?
            """,
            (new_value or None, user_id)
        )

    else:
        return False

    connection.commit()
    return result.rowcount == 1


# A5 - Get active patients and MHWPs

def get_users_for_disable(connection):
    return connection.execute(
        """
        SELECT user_id, name, role
        FROM users
        WHERE role IN ('patient', 'practitioner')
          AND account_status = 'active'
        ORDER BY role, name
        """
    ).fetchall()


# A4 - Delete a patient or MHWP

def delete_user(connection, user_id):

    # Ensure automatic foreign-key actions are enabled
    foreign_keys = connection.execute(
        "PRAGMA foreign_keys"
    ).fetchone()[0]

    if foreign_keys != 1:
        raise RuntimeError("Foreign keys must be enabled before deletion.")

    # Check that the user exists and is not an Admin
    user = connection.execute(
        """
        SELECT role
        FROM users
        WHERE user_id = ?
          AND role IN ('patient', 'practitioner')
        """,
        (user_id,)
    ).fetchone()

    if user is None:
        return False

    # Find future bookings that require notifications
    bookings, patients = get_disable_impact(connection, user_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Perform all changes in one transaction
    with connection:

        # Step 1 - Record cancellation emails
        for booking in bookings:
            booking_id, patient_id, mhwp_id, when, \
                patient_name, patient_email, mhwp_name, mhwp_email = booking

            subject = "Appointment cancelled"
            body = (
                f"The appointment on {when} between "
                f"{patient_name} and {mhwp_name} "
                "has been cancelled because an account was deleted."
            )

            for recipient_id, address in [
                (patient_id, patient_email),
                (mhwp_id, mhwp_email)
            ]:
                connection.execute(
                    """
                    INSERT INTO emails
                        (to_user_id, to_address, subject, body, sent_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (recipient_id, address, subject, body, now)
                )

        # Step 2 - Delete the user
        result = connection.execute(
            """
            DELETE FROM users
            WHERE user_id = ?
              AND role IN ('patient', 'practitioner')
            """,
            (user_id,)
        )

        if result.rowcount != 1:
            raise RuntimeError("Unable to delete the selected user.")

    return True


# A5 - Find bookings and allocations affected by disabling a user

def get_disable_impact(connection, user_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    bookings = connection.execute(
        """
        SELECT a.appointment_id, a.patient_id,
               a.practitioner_id, a.scheduled_time,
               p.name, p.email, m.name, m.email
        FROM appointments AS a
        JOIN users AS p ON a.patient_id = p.user_id
        JOIN users AS m ON a.practitioner_id = m.user_id
        WHERE (a.patient_id = ? OR a.practitioner_id = ?)
          AND a.status IN ('requested', 'confirmed')
          AND datetime(a.scheduled_time) > datetime(?)
        """,
        (user_id, user_id, now)
    ).fetchall()

    patients = connection.execute(
        """
        SELECT u.name
        FROM patient_profiles AS pp
        JOIN users AS u ON pp.patient_id = u.user_id
        WHERE (pp.patient_id = ?
               AND pp.assigned_practitioner_id IS NOT NULL)
           OR pp.assigned_practitioner_id = ?
        ORDER BY u.name
        """,
        (user_id, user_id)
    ).fetchall()

    return bookings, patients


# A5 - Disable a user and handle related records

def disable_user(connection, user_id):

    user = connection.execute(
        """
        SELECT role
        FROM users
        WHERE user_id = ?
          AND role IN ('patient', 'practitioner')
          AND account_status = 'active'
        """,
        (user_id,)
    ).fetchone()

    if user is None:
        return False

    bookings, patients = get_disable_impact(connection, user_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save all changes together
    with connection:

        # Step 1 - Cancel future live bookings
        for booking in bookings:
            booking_id, patient_id, mhwp_id, when, \
                patient_name, patient_email, mhwp_name, mhwp_email = booking

            connection.execute(
                """
                UPDATE appointments
                SET status = 'cancelled'
                WHERE appointment_id = ?
                """,
                (booking_id,)
            )

            # Step 2 - Record an email for both people
            subject = "Appointment cancelled"
            body = (
                f"The appointment on {when} between "
                f"{patient_name} and {mhwp_name} "
                "has been cancelled because an account was disabled."
            )

            for recipient_id, address in [
                (patient_id, patient_email),
                (mhwp_id, mhwp_email)
            ]:
                connection.execute(
                    """
                    INSERT INTO emails
                        (to_user_id, to_address, subject, body, sent_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (recipient_id, address, subject, body, now)
                )

        # Step 3 - Remove affected patient allocations
        if user[0] == "patient":
            connection.execute(
                """
                UPDATE patient_profiles
                SET assigned_practitioner_id = NULL
                WHERE patient_id = ?
                """,
                (user_id,)
            )

        else:
            connection.execute(
                """
                UPDATE patient_profiles
                SET assigned_practitioner_id = NULL
                WHERE assigned_practitioner_id = ?
                """,
                (user_id,)
            )

        # Step 4 - Disable the account
        result = connection.execute(
            """
            UPDATE users
            SET account_status = 'disabled',
                disabled_at = ?
            WHERE user_id = ?
              AND account_status = 'active'
            """,
            (now, user_id)
        )

        if result.rowcount != 1:
            raise ValueError("Unable to disable the account.")

    return True




# A7 - Get user information for the Admin summary

def get_user_statuses(connection):
    return connection.execute(
        """
        SELECT role, account_status
        FROM users
        """
    ).fetchall()



# A7 - Get patient allocations for the Admin summary

def get_patient_allocations(connection):
    return connection.execute(
        """
        SELECT p.name, m.name, p.account_status
        FROM users AS p
        LEFT JOIN patient_profiles AS pp
            ON p.user_id = pp.patient_id
        LEFT JOIN users AS m
            ON pp.assigned_practitioner_id = m.user_id
        WHERE p.role = 'patient'
        ORDER BY p.name
        """
    ).fetchall()



# A7 - Count patients assigned to each MHWP

def get_mhwp_patient_counts(connection):
    return connection.execute(
        """
        SELECT u.name, COUNT(p.patient_id)
        FROM users AS u
        LEFT JOIN patient_profiles AS p
            ON u.user_id = p.assigned_practitioner_id
        WHERE u.role = 'practitioner'
        GROUP BY u.user_id, u.name
        ORDER BY u.name
        """
    ).fetchall()


# A7 - Count weekly appointments for each MHWP

def get_mhwp_weekly_bookings(connection):

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    next_monday = monday + timedelta(days=7)

    return connection.execute(
        """
        SELECT u.name,
               COUNT(CASE WHEN a.status = 'confirmed' THEN 1 END),
               COUNT(CASE WHEN a.status = 'requested' THEN 1 END)
        FROM users AS u
        LEFT JOIN appointments AS a
            ON u.user_id = a.practitioner_id
            AND substr(a.scheduled_time, 1, 10) >= ?
            AND substr(a.scheduled_time, 1, 10) < ?
        WHERE u.role = 'practitioner'
        GROUP BY u.user_id, u.name
        ORDER BY u.name
        """,
        (monday.isoformat(), next_monday.isoformat())
    ).fetchall()


# A7 - Count all bookings this week by status

def get_weekly_booking_totals(connection):
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    next_monday = monday + timedelta(days=7)

    return connection.execute(
        """
        SELECT status, COUNT(*)
        FROM appointments
        WHERE substr(scheduled_time, 1, 10) >= ?
          AND substr(scheduled_time, 1, 10) < ?
        GROUP BY status
        """,
        (monday.isoformat(), next_monday.isoformat())
    ).fetchall()


