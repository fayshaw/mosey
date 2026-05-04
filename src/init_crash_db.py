#!/usr/bin/env python3
"""
Initialize the crash database.
Run once from the project root to migrate the schema and load crash data:

    python src/init_db.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.constants import DB_PATH, CRASH_FILE
from src.load_data import ingest_csv_to_db

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS Crashes (
    crash_number                TEXT PRIMARY KEY,
    crash_date                  DATE,
    crash_year                  INTEGER,
    crash_time                  TEXT,
    crash_hour                  TEXT,
    crash_severity              TEXT,
    first_harmful_event         TEXT,
    first_harmful_event_location TEXT,
    latitude                    REAL,
    longitude                   REAL,
    max_injury_severity         TEXT,
    total_fatalities            INTEGER,
    total_nonfatal_injuries     INTEGER,
    most_harmful_event_all      TEXT,
    num_vehicles                INTEGER,
    age_driver_young            TEXT,
    age_driver_old              TEXT,
    age_vuln_user_young         TEXT,
    age_vuln_user_old           TEXT,
    driver_contrib_circumst     TEXT,
    manner_of_collision         TEXT,
    vehicle_action_pre_crash    TEXT,
    vehicle_configurations      TEXT,
    vehicle_towed_from_scene    TEXT,
    vehicle_travel_directions   TEXT,
    vuln_user_action            TEXT,
    vuln_user_location          TEXT,
    vuln_user_type              TEXT,
    vehicle_sequence_events     TEXT,
    vuln_user_sequence_events   TEXT,
    vuln_user_contrib_circumst  TEXT,
    speed_limit                 INTEGER,
    roadway                     TEXT,
    street_name_linked_rd       TEXT,
    from_street_name_linked_rd  TEXT,
    to_street_name_linked_rd    TEXT,
    near_intersection           TEXT,
    light_conditions            TEXT,
    weather_conditions          TEXT,
    road_surface                TEXT,
    hit_and_run                 TEXT,
    roadway_junction_type       TEXT,
    traffic_ctrl_device_type    TEXT,
    trafficway_description      TEXT,
    geocoding_method            TEXT,
    crash_report_ids            TEXT,
    in_malden                   INTEGER DEFAULT NULL
)
"""


def create_schema(db_path=DB_PATH):
    """Drop the old table and create the new schema."""
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS Crashes")
    conn.execute(CREATE_TABLE)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_crash_year ON Crashes(crash_year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_lat_lon ON Crashes(latitude, longitude)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_in_malden ON Crashes(in_malden)")
    conn.commit()
    conn.close()
    print(f"Schema created: {db_path}")


def add_malden_column(db_path=DB_PATH):
    """
    Add the in_malden column to an existing Crashes table.
    Safe to call on a table that already has the column — does nothing in that case.
    Run backfill_malden_flag() after this to populate the values.
    """
    conn = sqlite3.connect(db_path)
    existing = [row[1] for row in conn.execute("PRAGMA table_info(Crashes)")]
    if 'in_malden' not in existing:
        conn.execute("ALTER TABLE Crashes ADD COLUMN in_malden INTEGER DEFAULT NULL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_in_malden ON Crashes(in_malden)")
        conn.commit()
        print("Added in_malden column and index.")
    else:
        print("in_malden column already exists — skipping.")
    conn.close()


def add_columns_migration(csv_path=CRASH_FILE, db_path=DB_PATH):
    """
    Add first_harmful_event_location and vehicle_sequence_events to an existing
    Crashes table, then back-fill values from the source CSV.
    Safe to run multiple times — skips ALTER if columns already exist.
    """
    import pandas as pd
    from src.constants import COLUMN_MAP

    NEW_COLS = {
        'first_harmful_event_location': 'First Harmful Event Location',
        'vehicle_sequence_events':      'Vehicle Sequence of Events (All Vehicles)',
    }

    conn = sqlite3.connect(db_path)
    existing = [row[1] for row in conn.execute("PRAGMA table_info(Crashes)")]

    for db_col in NEW_COLS:
        if db_col not in existing:
            conn.execute(f"ALTER TABLE Crashes ADD COLUMN {db_col} TEXT")
            print(f"Added column: {db_col}")
        else:
            print(f"Column already exists, skipping ALTER: {db_col}")
    conn.commit()

    df = pd.read_csv(csv_path, skipfooter=5, engine='python')
    df = df.dropna(subset=['Crash Number'])
    csv_col_map = {v: k for k, v in NEW_COLS.items()}  # db_col -> csv_col (inverted)
    csv_cols = list(NEW_COLS.values())
    available = [c for c in csv_cols if c in df.columns]
    if not available:
        print("No matching CSV columns found — check column names.")
        conn.close()
        return

    df = df[['Crash Number'] + available].copy()
    df['Crash Number'] = df['Crash Number'].astype(str)
    df = df.where(df.notna(), None)

    for _, row in df.iterrows():
        updates = {csv_col_map[c]: row[c] for c in available if c in csv_col_map}
        set_clause = ', '.join(f"{k} = ?" for k in updates)
        vals = list(updates.values()) + [row['Crash Number']]
        conn.execute(f"UPDATE Crashes SET {set_clause} WHERE crash_number = ?", vals)

    conn.commit()
    conn.close()
    print(f"Back-filled {len(df):,} rows for: {', '.join(NEW_COLS.keys())}")


if __name__ == '__main__':
    create_schema()
    ingest_csv_to_db(CRASH_FILE)
