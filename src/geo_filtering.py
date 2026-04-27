"""
Shared spatial filtering utilities for Malden boundary clipping.
"""
import geopandas as gpd


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
