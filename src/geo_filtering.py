"""
Shared spatial filtering utilities for Malden boundary clipping.
"""
import sqlite3
import geopandas as gpd
from src.constants import CRS, DB_PATH

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


def within_malden_flag(db_path=DB_PATH):
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



def filter_to_malden_geo(gdf, malden_gdf, buffer_distance=100, keep_geometry=False):
    """
    Keep features within Malden's boundary plus those within buffer_distance
    units of the border (catches features recorded just outside the boundary).

    Args:
        gdf              — GeoDataFrame with geometry column
        malden_gdf       — GeoDataFrame of Malden boundary
        buffer_distance  — meters to buffer boundary (default 100)
        keep_geometry    — if True, keep geometry column; if False, drop it

    Returns:
        Filtered GeoDataFrame (or DataFrame if keep_geometry=False)
    """
    gdf = gdf.to_crs(malden_gdf.crs)

    malden_buffered = malden_gdf.copy()
    malden_buffered['geometry'] = malden_gdf.buffer(buffer_distance)

    within_boundary = gpd.sjoin(gdf, malden_gdf[['geometry']], predicate='within')
    in_buffer       = gpd.sjoin(gdf, malden_buffered[['geometry']], predicate='within')

    border_indices = in_buffer.index.difference(within_boundary.index)
    keep_indices   = within_boundary.index.union(border_indices)

    result = gdf.loc[keep_indices]

    if not keep_geometry:
        result = result.drop(columns='geometry')

    outside_count = len(gdf) - len(keep_indices)
    print(f"filter_to_malden_geo: {len(within_boundary)} within, "
          f"{len(border_indices)} on border, "
          f"{outside_count} outside (dropped)")

    return result.reset_index(drop=True)
