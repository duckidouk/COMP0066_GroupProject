# after login -- the menu should appear

import sqlite3

DATABASE_PATH = "therapy_link.db"

connection = sqlite3.connect(DATABASE_PATH)

cursor = connection.cursor()

# hardcoding the mhwp until we figure out logins
practitioner_id = 2

# intro message for practitioner :p
print('Hello dear [practitioner]! \nHere are your appointments for the day:')


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
    print(row)

# Showing patient dashboard:
print("Here is your patient dashboard:")

cursor.execute('''
    SELECT u.name, me.comment, me.score
    FROM mood_entries as me
    JOIN users as u on me.patient_id = u.user_id
    JOIN patient_profiles as pp on u.user_id = pp.patient_id
    WHERE assigned_practitioner_id = ? ;''',
    (practitioner_id,)
)

# Printing the rows so it can be shown in terminal
rows = cursor.fetchall()
for row in rows:
    print(row)

connection = sqlite3.connect("DATABASE_PATH")
cursor = connection.cursor()


cursor.close()
connection.close()
