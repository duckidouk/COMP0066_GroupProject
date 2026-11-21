'''
Code for patient to view their conversations module
Patients are user_id = 4 and 5 for testing purposes
'''


from contextlib import closing
import sqlite3
import datetime
DATABASE_PATH = "therapy_link.db"

def email_list(connection,patient_id):
    emails = connection.execute(
        """
        SELECT * FROM emails
        WHERE to_user_id = ?
        """,
        (patient_id,)).fetchall()

    email_id = emails[0]['to_address']

    if not emails:
        print("No notifications.")
        return None

    else:
        print(f"\nEmail notifications delivered to:",email_id,'\n')

        for number,rows in enumerate(emails,start=1):
            sent = (datetime.datetime.fromisoformat(rows['sent_at']))
            print(
                f"{number}",rows['subject'],"\n",
                f" Delivered on: {sent:%A %d %B %Y at %H:%M}\n ",
                rows['body'],"\n"
            )


#with closing(sqlite3.connect(DATABASE_PATH)) as connection:
#    connection.row_factory = sqlite3.Row 
#    print(email_list(connection,4))
