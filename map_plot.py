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
import re
import streamlit as st
from dotenv import load_dotenv
from src.spatial_utils import crashes_near_point
from src.constants import SEARCH_RADIUS
from src.crash_utils import is_ped_crash, is_cycle_crash, is_fatal_ped_crash
from src.load_data import load_crashes_from_db

START_YEAR = 2021
END_YEAR = 2025
FEET_TO_METERS = 3.281
JITTER = 0.00003  # JITTER = 0.00003 is ~3 metres (~1 lane width) — separates stacked dots without leaving the road
MAX_ZOOM = 19

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
    """Load crash data from the database (columns already in DB schema names)."""
    return load_crashes_from_db(malden_only=True)


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

_S  = 13  # triangle size in pixels — change this one value to resize
_SW = 1   # stroke width in pixels
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

_FP_S = 22          # fatal-ped icon is larger than the cyclist triangle
_FP_C = _FP_S // 2  # centre coordinate
_FP_P = 5           # padding for X arms inside the circle

_FATAL_PED_ICON = folium.DivIcon(
    html=(
        f'<svg width="{_FP_S}" height="{_FP_S}" viewBox="0 0 {_FP_S} {_FP_S}">'
        f'<circle cx="{_FP_C}" cy="{_FP_C}" r="{_FP_C - 1}" '
        f'fill="none" stroke="red" stroke-width="2"/>'
        f'<line x1="{_FP_P}" y1="{_FP_P}" x2="{_FP_S-_FP_P}" y2="{_FP_S-_FP_P}" '
        f'stroke="maroon" stroke-width="3"/>'
        f'<line x1="{_FP_S-_FP_P}" y1="{_FP_P}" x2="{_FP_P}" y2="{_FP_S-_FP_P}" '
        f'stroke="maroon" stroke-width="3"/>'
        f'</svg>'
    ),
    icon_size=(_FP_S, _FP_S),
    icon_anchor=(_FP_C, _FP_C),
)


def _make_crash_layers(df, map_obj):
    """Add vectorized GeoJson crash layers.

    Jitter rules:
      - Car crashes: jitter when 2+ car crashes share exact coordinates.
      - Non-fatal ped / cyclist: jitter when their location is shared with
        any other crash (catches bike-over-fatal-ped stacking).
      - Fatal ped: never jittered — always plotted at the exact location.
    """
    crash_coords = df.dropna(subset=['latitude', 'longitude']).copy()

    ped_mask       = is_ped_crash(crash_coords)
    fatal_ped_mask = is_fatal_ped_crash(crash_coords)
    cycle_mask     = is_cycle_crash(crash_coords) & ~ped_mask

    # Total crashes at each location, all types combined
    loc_count = crash_coords.groupby(['latitude', 'longitude'])['latitude'].transform('size')

    rng = np.random.default_rng(seed=42)

    def _jitter(subset, overlap):
        """Return copy of subset with _jlat/_jlon; jitter rows where overlap is True."""
        out = subset.copy()
        out['_jlat'] = out['latitude']
        out['_jlon'] = out['longitude']
        n = int(overlap.sum())
        if n:
            out.loc[overlap, '_jlat'] += rng.uniform(-JITTER, JITTER, n)
            out.loc[overlap, '_jlon'] += rng.uniform(-JITTER, JITTER, n)
        return out

    car_mask = ~ped_mask & ~cycle_mask
    car_df   = _jitter(crash_coords[car_mask],
                       crash_coords[car_mask].groupby(['latitude', 'longitude'])['latitude'].transform('size') > 1)
    ped_df   = _jitter(crash_coords[ped_mask & ~fatal_ped_mask], loc_count[ped_mask & ~fatal_ped_mask] > 1)
    cycle_df = _jitter(crash_coords[cycle_mask],                 loc_count[cycle_mask] > 1)

    layers = [
        (car_df,                         '_jlat', '_jlon', folium.CircleMarker(radius=3, weight=3, color='blue',
                                                                               fill=True, fill_color='blue', fill_opacity=0.6)),
        (ped_df,                         '_jlat', '_jlon', folium.CircleMarker(radius=3, weight=3, color='red',
                                                                               fill=True, fill_color='red',  fill_opacity=0.6)),
        (cycle_df,                       '_jlat', '_jlon', folium.Marker(icon=_CYCLIST_ICON)),
        (crash_coords[fatal_ped_mask], 'latitude', 'longitude', folium.Marker(icon=_FATAL_PED_ICON)),
    ]
    for subset, lat_col, lon_col, marker in layers:
        if subset.empty:
            continue
        lats = subset[lat_col].to_numpy()
        lons = subset[lon_col].to_numpy()
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

    m = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=18, max_zoom=MAX_ZOOM)

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
    map_year = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=15, max_zoom=MAX_ZOOM)

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

