import sqlite3
import pandas as pd

# Create a connection to the database
conn = sqlite3.connect('db/app.db')
cur = conn.cursor()
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS
    Crashes(id INTEGER PRIMARY KEY, date DATE,
    time TIME, severity TEXT, lat FLOAT, lon FLOAT, 
    num_fatal_inj INTEGER)
    """
)
conn.commit()

# Load the data
crash_df = pd.read_csv('data_sources/export_7_4_2023_16_43_30.csv')
data = []
for row in crash_df.itertuples():
    data.append(
        (row.crash_date, row.crash_time_2, row.crash_severity_descr, row.lat, row.lon, row.numb_fatal_injr)
    )
print('Data loaded in memory. Loading into database.')
# Insert the data into the database
cur.executemany(
    """
    INSERT INTO Crashes(date, time, severity, lat, lon, num_fatal_inj)
    VALUES(?, ?, ?, ?, ?, ?)
    """, data
)
conn.commit()
conn.close()
print('Data loaded into database.')
