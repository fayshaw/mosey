import os
import time
from pathlib import Path

import networkx as nx
import pandas as pd
from shapely.geometry import LineString
from shapely.ops import unary_union

from src.constants import ROAD_NETWORK_CACHE


def get_malden_road_network(cache_path=None):
    """
    Return the OSMnx road network for Malden, MA.
    Saves to disk on first download; subsequent calls load from the cache file.
    """
    import osmnx as ox
    path = Path(cache_path or ROAD_NETWORK_CACHE)
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
    import osmnx as ox
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
