## Set up the local database

From the root directory, run these commands to create the database tables and
populate them with sample data:

```
python3 schema.py
python3 sample_data.py
```

Can confirm the seed was successful by running:

```
sqlite3 therapy_link.db
```

Check for records in tables:

```
SELECT * FROM users;
SELECT * FROM appointments;
```
