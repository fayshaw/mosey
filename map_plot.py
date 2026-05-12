#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crash Data Visualization and Mapping Module for MOSEY.

This module provides functions to geocode addresses, load crash data from
MassDOT, and generate interactive Folium maps showing car crashes and
pedestrian collisions within a specified radius of a given location in
Malden, MA.

Main functionality:
    - Geocode addresses using OpenStreetMap Nominatim API
    - Load and filter crash data from CSV (2015-2025)
    - Create interactive maps with crash markers (blue=vehicle, red=pedestrian)
    - Calculate Walk Scores for locations
    - Generate zone-based and year-specific crash visualizations

Typical usage:
    crash_df = load_data()
    data = geocode("422 Main St, Malden, MA 02148").json()
    m, map_year, crash_count = plot_points(data, crash_df)

Author: fayshaw
"""

import numpy as np
import folium
import requests
import pandas as pd
import re
import streamlit as st
from dotenv import load_dotenv
from src.spatial_utils import crashes_near_point
from src.constants import SEARCH_RADIUS, COLUMN_MAP
from src.crash_utils import is_ped_crash, is_cycle_crash

START_YEAR = 2023
END_YEAR = 2023
FEET_TO_METERS = 3.281
JITTER = 0.00003  # JITTER = 0.00003 is ~3 metres (~1 lane width) — separates stacked dots without leaving the road

malden_places = {
    'Centre St & Main St'          : '205 Centre St, Malden, MA 02148',
    'Main St & Salem St'           : '442 Main Street Malden MA 02148',
    'Centre St & Charles St'       : '185 Centre St, Malden, MA 02148',
    'Beebe School'                 : '401 Pleasant St, Malden, MA 02148',
    'Ferryway School'              : '150 Cross St, Malden, MA 02148',  
    'Malden Center T Station'      : '30 Commercial St, Malden, MA 02148',
    'MA 99 at Broadway Plaza '     : '62 Broadway, Malden, MA 02148',
    }


@st.cache_data
def load_data():
    """Load crash data from CSV, columns renamed to DB schema names."""
    crash_df = pd.read_csv('data_sources/Malden_crashesJan2015-1Dec2025.csv',
                           skipfooter=3, engine='python',
                           dtype={'Crash Year': 'Int32', 'Speed Limit': 'Int32'})
    return crash_df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in crash_df.columns})


def geocode(address: str) -> requests.Response:
    """Geocode address using OpenStreetMap"""
    # add try/except for network errors
    params = { 'format'        :'json',
               'addressdetails': 1, 
               'q'             : address}
    headers = {'user-agent'    : 'MOSEY' }  #  Need to supply a user agent other than the default provided by
                                            #  requests for the API to accept the query.
    return requests.get('http://nominatim.openstreetmap.org/search', params=params, headers=headers)    


def get_addr_str(addr_dict):
    """Return a string of the address with spaces replaced by underscores"""
    num = addr_dict['house_number']    
    new_road = re.sub(" ", "_", addr_dict['road'])
    addr_str = num + '_' + new_road
    return addr_str


def get_walk_score(lat, lon):
    """Get walkability score from WalkScore API"""
    load_dotenv()
    apikey = st.secrets['WALK_API']
    params = {
        'format'   : 'json',
        'lat'     : lat,
        'lon'     : lon,
        'wsapikey': apikey,
    }

    r = requests.get('http://api.walkscore.com/score', params=params)
    data = r.json()
    return data['walkscore']

_S  = 16  # triangle size in pixels — change this one value to resize
_SW = 2   # stroke width in pixels
_P  = _SW # padding = stroke width keeps the outline inside the viewBox

_CYCLIST_ICON = folium.DivIcon(
    html=(
        f'<svg width="{_S}" height="{_S}" viewBox="0 0 {_S} {_S}">'
        f'<polygon points="{_S//2},{_P} {_S-_P},{_S-_P} {_P},{_S-_P}" '
        f'fill="orange" stroke="saddlebrown" stroke-width="{_SW}"/>'
        f'</svg>'
    ),
    icon_size=(_S, _S),
    icon_anchor=(_S//2, _S//2),
)


def _make_crash_layers(df, map_obj):
    """Add vectorized blue/red/orange GeoJson crash layers to a Folium map."""
    crash_coords = df.dropna(subset=['latitude', 'longitude']).copy()
    rng = np.random.default_rng(seed=42)
    crash_coords['_jlat'] = crash_coords['latitude']  + rng.uniform(-JITTER, JITTER, len(crash_coords))
    crash_coords['_jlon'] = crash_coords['longitude'] + rng.uniform(-JITTER, JITTER, len(crash_coords))

    ped_mask   = is_ped_crash(crash_coords)
    cycle_mask = is_cycle_crash(crash_coords) & ~ped_mask

    layers = [
        (crash_coords[~ped_mask & ~cycle_mask], folium.CircleMarker(radius=3, weight=3, color='blue',
                                                                    fill=True, fill_color='blue', fill_opacity=0.6)),
        (crash_coords[ped_mask], folium.CircleMarker(radius=3, weight=3, color='red',
                                                     fill=True, fill_color='red', fill_opacity=0.6)),
        (crash_coords[cycle_mask], folium.Marker(icon=_CYCLIST_ICON)),
    ]
    for subset, marker in layers:
        if subset.empty:
            continue
        lats = subset['_jlat'].to_numpy()
        lons = subset['_jlon'].to_numpy()
        geojson = {
            'type': 'FeatureCollection',
            'features': [
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [float(lo), float(la)]},
                 'properties': {}}
                for la, lo in zip(lats, lons)
            ]
        }
        folium.GeoJson(geojson, marker=marker).add_to(map_obj)


def plot_points(data, crash_df):
    """Plots an address on the map"""
    address = data[0]['address']['house_number'] + ' ' + data[0]['address']['road']

    # Extract the latitude and longitude
    lat_0 = float(data[0]["lat"])
    lon_0 = float(data[0]["lon"])

    zone_df = crashes_near_point(lat_0, lon_0, crash_df)
    zone_df = zone_df[zone_df['crash_year'].between(START_YEAR, END_YEAR)]
    crash_count = len(zone_df)

    m = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=18)

    m.add_child(
        folium.Marker(
            location = [lat_0, lon_0], popup=address, icon=folium.Icon(color='blue')        
        ))

    
    folium.Circle(
        location=[lat_0, lon_0],
        radius=SEARCH_RADIUS / FEET_TO_METERS,  # feet to metres
        color='gray',
        fill=True,
        fill_color='gray',
        fill_opacity=0.15
    ).add_to(m)

    _make_crash_layers(zone_df, m)
    # Plot all crashes for END_YEAR
    crashes_end_year_df = crash_df[crash_df['crash_year'] == END_YEAR]
    map_year = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=15)

    map_year.add_child(
        folium.Marker(
            location=[lat_0, lon_0], popup=address, icon=folium.Icon(color='blue')
        ))

    _make_crash_layers(crashes_end_year_df, map_year)

    return m, map_year, crash_count



if __name__ == '__main__':
    data = []
    address = input("Enter an address: ")
    data = geocode(address).json()

    # check address
    while not data:  # need better error handling - right now only in Malden
       address = input("Address not valid. Please enter an address: ")
       data = geocode(address).json()

    addr_str = get_addr_str(data[0]['address'])    
    crash_df = load_data()
    m, map_year, score = plot_points(data, crash_df)
    m.save(addr_str + '_map.html')  # save file with address

