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
import geopandas as gpd
from src.constants import CRS
from pathlib import Path

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


def filter_to_malden_geo(crash_gdf, malden_gdf, buffer_distance=100):
    """
    Keep crashes within Malden's boundary plus those within buffer_distance
    units of the border (catches crashes recorded just outside the boundary).

    Returns a plain DataFrame (geometry column dropped) so downstream
    functions don't need geopandas.
    """
    crash_gdf = crash_gdf.to_crs(malden_gdf.crs)

    malden_buffered = malden_gdf.copy()
    malden_buffered['geometry'] = malden_gdf.buffer(buffer_distance)

    crashes_within    = gpd.sjoin(crash_gdf, malden_gdf[['geometry']],    predicate='within')
    crashes_in_buffer = gpd.sjoin(crash_gdf, malden_buffered[['geometry']], predicate='within')

    border_indices = crashes_in_buffer.index.difference(crashes_within.index)
    keep_indices   = crashes_within.index.union(border_indices)

    result = crash_gdf.loc[keep_indices].drop(columns='geometry')
    print(f"filter_to_malden: {len(crashes_within)} within, "
          f"{len(border_indices)} on border, "
          f"{len(crash_gdf) - len(keep_indices)} outside and dropped")
    return result.reset_index(drop=True)

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


