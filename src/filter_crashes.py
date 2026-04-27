"""
Spatial processing pipeline for crash data.

Requires geopandas:
    pip install geopandas

Typical usage:
    from src.data_loader import load_crashes_from_db, load_malden_boundary
    from src.process_crashes import crashes_to_geodataframe, filter_to_malden, classify_crashes

    malden_gdf = load_malden_boundary()
    crash_df   = load_crashes_from_db(start_year=2015)
    crash_gdf  = crashes_to_geodataframe(crash_df)
    malden_crashes = filter_to_malden(crash_gdf, malden_gdf)
    ped_df, bike_df = classify_crashes(malden_crashes)
"""
import sqlite3
import geopandas as gpd
from src.constants import CRS, DB_PATH
from src.geo_filtering import filter_to_malden_geo


def crashes_to_geodataframe(crash_df):
    """
    Convert a crash DataFrame (loaded from the database) to a GeoDataFrame.
    Uses the latitude/longitude columns and sets CRS to WGS84.
    Drops rows with missing coordinates before converting.
    """
    crash_df = crash_df.dropna(subset=['latitude', 'longitude']).copy()
    gdf = gpd.GeoDataFrame(
        crash_df,
        geometry=gpd.points_from_xy(crash_df['longitude'], crash_df['latitude']),
        crs=CRS
    )
    return gdf


def backfill_malden_flag(db_path=DB_PATH):
    """
    Run the geo-filter once and write the result back to the Crashes table
    as the in_malden column.

    - in_malden = 1  : crash is within Malden boundary (or within 100-unit buffer)
    - in_malden = 0  : crash has coordinates but lies outside the boundary
    - in_malden = NULL : crash has no coordinates — cannot determine

    Re-run after each new CSV ingestion to flag newly added rows.
    Requires geopandas and the MassGIS town boundary shapefile.
    """
    from src.load_data import load_crashes_from_db, load_malden_boundary

    print("Loading crashes and Malden boundary...")
    crash_df   = load_crashes_from_db(db_path)
    malden_gdf = load_malden_boundary()
    crash_gdf  = crashes_to_geodataframe(crash_df)        # drops NULL-coord rows
    inside_df  = filter_to_malden_geo(crash_gdf, malden_gdf)

    inside_numbers  = set(inside_df['crash_number'])
    has_coords      = set(crash_gdf['crash_number'])
    outside_numbers = has_coords - inside_numbers

    # Write flags using a temp table to avoid hitting SQLite variable limits
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TEMP TABLE _malden_flags (crash_number TEXT, flag INTEGER)")
    conn.executemany("INSERT INTO _malden_flags VALUES (?, 1)",
                     [(n,) for n in inside_numbers])
    conn.executemany("INSERT INTO _malden_flags VALUES (?, 0)",
                     [(n,) for n in outside_numbers])
    conn.execute("""
        UPDATE Crashes
        SET in_malden = (SELECT flag FROM _malden_flags
                         WHERE _malden_flags.crash_number = Crashes.crash_number)
        WHERE crash_number IN (SELECT crash_number FROM _malden_flags)
    """)
    conn.commit()
    conn.close()

    null_count = len(crash_df) - len(has_coords)
    print(f"in_malden=1: {len(inside_numbers):,}  "
          f"in_malden=0: {len(outside_numbers):,}  "
          f"in_malden=NULL (no coords): {null_count:,}")


def filter_crashes(df, **criteria):
    """
    Filter a crash DataFrame by column=value pairs.
    Column names are snake_case (DB schema).

    Example:
        ped_df = filter_crashes(df, first_harmful_event='Collision with pedestrian')
        fatal_ped_df = filter_crashes(df, first_harmful_event='Collision with pedestrian',
                                          crash_severity='Fatal injury')
    """
    result = df
    for column, value in criteria.items():
        result = result[result[column] == value]
    return result


