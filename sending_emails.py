'''
Code for patient sending out emails for appointment bookings ++ TO BE ADDED LATER ONCE DECIDED
Patients are user_id = 4 and 5 for testing purposes
'''

import os
import smtplib
import ssl
import datetime
from email.message import EmailMessage


#CONFIG TO SET UP THE EMAIL DELIVERY
#TEST_TO_ADDRESS = "salonipatni1206@gmail.com" ---> This will need to be changed if you want to test it locally to your own personal email
FROM_ADDRESS = "therapylink0066@gmail.com" 
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

#SUBJECT LINE AND END OF THE EMAIL TEXT
email_body = {
    "cancellation": ("Appointment cancelled", "has been cancelled."),
    "confirmation": ("Appointment confirmed", "has been confirmed."),
}

def send_real_email(to_address, subject, body):
    token = os.environ.get("THERAPYLINK_SMTP_TOKEN")   #the password is NOT written in the code --> FYI: WILL NEED TO SPECIFY THIS TO THE EXAMINER
    if not token:
        return False

    message = EmailMessage()
    message["From"] = FROM_ADDRESS
    message["To"] =  to_address #TEST_TO_ADDRESS if you are testing this locally on your side
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(FROM_ADDRESS, token)
            server.send_message(message)
        return True
    except (smtplib.SMTPException, OSError) as error:
        #print(error) -->> for us to view the error in case there is (the user should not see this)
        return False


def update_email_table(connection, to_user_id, subject, body):
    row = connection.execute(
        "SELECT email FROM users WHERE user_id = ?", (to_user_id,)
    ).fetchone()
    address, name = row["email"], row["name"]
    sent_at = datetime.datetime.now().isoformat(timespec="seconds")
    with connection:
        connection.execute(
            """
            INSERT INTO emails (to_user_id, to_address, subject, body, sent_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (to_user_id, address, subject, body, sent_at),
        )

    full_body = f"Dear {name},\n\n{body}\n\nSincerely,\nTherapyLink"

    #the row above is the patient's notification inside the app; below sends out the real email 
    if not send_real_email(address, subject, full_body):
        print("(The email could not be sent out, but it is saved under your notifications.)")


def send_out_email(connection, appointment_id, kind):
    #Emails the patient and the practitioner of an appointment. kind is either 'cancellation' or 'confirmation'
    subject, ending = email_body[kind]
    appointment = connection.execute(
        """
        SELECT patient_id, practitioner_id, scheduled_time FROM appointments
        WHERE appointment_id = ?
        """,
        (appointment_id,),
    ).fetchone()

    when = datetime.datetime.fromisoformat(appointment["scheduled_time"])
    body = f"The appointment on {when:%A %d %B} at {when:%H:%M} {ending}"

    for user_id in (appointment["patient_id"], appointment["practitioner_id"]):
        update_email_table(connection, user_id, subject, body)