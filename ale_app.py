import streamlit as st
import sqlite3
import pandas as pd

# Create a connection object
conn = sqlite3.connect('db/app.db')
df = pd.read_sql('SELECT * FROM Crashes', conn).\
    dropna(subset=['lat', 'lon'])
st.write(df)

st.map(df[['lat', 'lon']], color='#0000FF', size=2)
conn.close()
