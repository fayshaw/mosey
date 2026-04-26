import sqlite3
from pathlib import Path
import pandas as pd
from src.constants import COLUMN_MAP, DB_PATH, CRASH_FILE

# ── Core crash data loading (no geopandas required) ──────────────────────────

def load_crash_csv(filepath=CRASH_FILE):
    """Load a MassDOT crash CSV. Returns raw DataFrame with original column names."""
    df = pd.read_csv(filepath, skipfooter=5, engine='python')
    return df.dropna(subset=['Crash Number'])


def ingest_csv_to_db(csv_path=CRASH_FILE, db_path=DB_PATH):
    """
    Load a MassDOT crash CSV into the database.
    Safe to run on overlapping exports — INSERT OR IGNORE skips duplicate crash_numbers.
    """
    df = pd.read_csv(csv_path, skipfooter=5, engine='python')
    df = df.dropna(subset=['Crash Number'])  # remove any remaining footer/empty rows

    # Parse 2-digit year format: 12/1/25 → 2025-12-01
    df['Crash Date'] = pd.to_datetime(
        df['Crash Date'], format='%m/%d/%y'
    ).dt.strftime('%Y-%m-%d')

    # Keep only mapped columns, rename to DB names
    csv_cols = [c for c in COLUMN_MAP if c in df.columns]
    df = df[csv_cols].rename(columns=COLUMN_MAP)

    # Replace NaN with None so sqlite3 stores NULL
    records = df.where(df.notna(), None).values.tolist()
    cols = ', '.join(df.columns)
    placeholders = ', '.join(['?'] * len(df.columns))
    sql = f"INSERT OR IGNORE INTO Crashes ({cols}) VALUES ({placeholders})"

    conn = sqlite3.connect(db_path)
    conn.executemany(sql, records)
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM Crashes").fetchone()[0]
    conn.close()
    print(f"Ingested {csv_path.name if hasattr(csv_path, 'name') else csv_path}")
    print(f"Database now contains {total:,} rows.")


def load_crashes_from_db(db_path=DB_PATH, start_year=None, end_year=None):
    """
    Load crash data from the database into a DataFrame.
    Optionally filter by year range.
    """
    conditions = []
    if start_year:
        conditions.append(f"crash_year >= {int(start_year)}")
    if end_year:
        conditions.append(f"crash_year <= {int(end_year)}")

    query = "SELECT * FROM Crashes"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def load_walk_audit_excel(filepath=None):
    """Load raw walk audit responses from Excel. Returns unmodified DataFrame."""
    from src.constants import WALK_AUDIT_FILE
    path = filepath or WALK_AUDIT_FILE
    return pd.read_excel(path)


# ── Geospatial loading (requires geopandas) ──────────────────────────────────

def load_malden_boundary(shp_path=None):
    """
    Load the Malden town boundary from the MassGIS shapefile.
    Requires geopandas.
    """
    import geopandas as gpd
    from src.constants import TOWN_SURVEY_SHP
    path = shp_path or TOWN_SURVEY_SHP
    towns = gpd.read_file(path)
    return towns[towns['TOWN'] == 'MALDEN']


def load_malden_roads(shp_path=None):
    """
    Load the MassGIS statewide roads shapefile clipped to Malden's bounding box.
    Requires geopandas.
    """
    import geopandas as gpd
    from src.constants import ROADS_SHP
    path = shp_path or ROADS_SHP
    malden = load_malden_boundary()
    roads = gpd.read_file(path, bbox=malden.total_bounds)
    return roads.clip(malden)
