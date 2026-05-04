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

#import geopandas as gpd
#from src.constants import CRS, DB_PATH
#from src.geo_filtering import filter_to_malden_geo, crashes_to_geodataframe



