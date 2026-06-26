"""
Spatial computation utilities: road network, routing, geocoding, and proximity queries.

No rendering here — functions return data or geometry. Plotting lives in plot_spatial.py.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.constants import ROAD_NETWORK, SEARCH_RADIUS


def get_malden_road_network(cache_path=None):
    """
    Return the OSMnx road network for Malden, MA.
    Saves to disk on first download; subsequent calls load from the cache file.
    """
    import osmnx as ox
    path = Path(cache_path or ROAD_NETWORK)
    if path.exists():
        return ox.load_graphml(path)
    print("Downloading Malden road network from OpenStreetMap...")
    G = ox.graph_from_place("Malden, MA", network_type="all")
    path.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, path)
    return G


def route_along_roads(G, start_lon, start_lat, end_lon, end_lat):
    """
    Return a Shapely geometry tracing the road-network path between two lon/lat points.
    Both points must be in EPSG:4326.
    Raises nx.NetworkXNoPath if no route exists between the two nodes.
    """
    import networkx as nx
    import osmnx as ox
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    orig = ox.distance.nearest_nodes(G, start_lon, start_lat)
    dest = ox.distance.nearest_nodes(G, end_lon, end_lat)
    route = nx.shortest_path(G, orig, dest, weight="length")

    edge_geoms = []
    for u, v in zip(route[:-1], route[1:]):
        edge_data = G.get_edge_data(u, v)
        # MultiDiGraph: edge_data is {key: attr_dict, ...}; take the first parallel edge
        attrs = edge_data[next(iter(edge_data))]
        if 'geometry' in attrs:
            edge_geoms.append(attrs['geometry'])
        else:
            edge_geoms.append(LineString([
                (G.nodes[u]['x'], G.nodes[u]['y']),
                (G.nodes[v]['x'], G.nodes[v]['y']),
            ]))
    return unary_union(edge_geoms)


def geocodio_geocode(intersection, client):
    """
    Geocode one intersection string using the Geocodio API.
    Returns a pd.Series with keys: lat, lon, geocoding_status.
    """
    try:
        response = client.geocode(intersection)
        if response and response.results:
            loc = response.results[0].location
            return pd.Series({'lat': loc.lat, 'lon': loc.lng, 'geocoding_status': 'success'})
        return pd.Series({'lat': None, 'lon': None, 'geocoding_status': 'null_returned'})
    except Exception as e:
        return pd.Series({'lat': None, 'lon': None, 'geocoding_status': f'error: {e}'})


def _haversine_ft(lat0, lon0, lats, lons):
    """Vectorized Haversine distance in feet from one point to arrays of points."""
    lat0, lon0 = np.radians(lat0), np.radians(lon0)
    lats = np.radians(np.asarray(lats, dtype=float))
    lons = np.radians(np.asarray(lons, dtype=float))
    dlat = lats - lat0
    dlon = lons - lon0
    a = np.sin(dlat / 2) ** 2 + np.cos(lat0) * np.cos(lats) * np.sin(dlon / 2) ** 2
    return 2 * np.arcsin(np.sqrt(a)) * 3959 * 5280


def crashes_near_point(lat, lon, crash_df, radius_ft=SEARCH_RADIUS,
                       lat_col='latitude', lon_col='longitude'):
    """
    Return crashes within radius_ft of (lat, lon) using Haversine distance.

    Adds a 'distance_ft' column to the result, sorted nearest-first.
    Uses vectorized numpy — no row-wise loop.

    Parameters
    ----------
    lat, lon   : center point coordinates (WGS84 degrees)
    crash_df   : DataFrame with at least lat_col and lon_col columns
    radius_ft  : search radius in feet (default: SEARCH_RADIUS from constants)
    lat_col    : name of the latitude column  (default 'latitude' for DB schema)
    lon_col    : name of the longitude column (default 'longitude' for DB schema)

    Returns
    -------
    DataFrame filtered to crashes within radius_ft, with 'distance_ft' column added.
    """
    crash_lat_lon = crash_df.dropna(subset=[lat_col, lon_col]).copy()
    dist = _haversine_ft(lat, lon, crash_lat_lon[lat_col].to_numpy(), crash_lat_lon[lon_col].to_numpy())
    crash_lat_lon['distance_ft'] = dist.round().astype(int)
    return crash_lat_lon[dist <= radius_ft].sort_values('distance_ft').reset_index(drop=True)


