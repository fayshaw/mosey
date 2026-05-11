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
'''
Next steps:
Use Haversine Distance

from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two points"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 3959  # Radius of earth in miles
    return c * r * 5280  # Convert to feet

def plot_points(data, crash_df):
    """Plots an address on the map"""
    lat_0 = float(data[0]["lat"])
    lon_0 = float(data[0]["lon"])
    
    # Filter by actual distance instead of bounding box
    crash_df['distance_ft'] = crash_df.apply(
        lambda row: haversine(lat_0, lon_0, row['Latitude'], row['Longitude']), 
        axis=1
    )
    
    zone_df = crash_df[(crash_df['distance_ft'] <= SEARCH_RADIUS) & 
                       (crash_df['Crash Year'] >= START_YEAR)]
    
    crash_count = len(zone_df)
    # ... rest of code
'''

import numpy as np
import folium
import requests
import pandas as pd
import re
import streamlit as st
from dotenv import load_dotenv
from src.spatial_utils import crashes_near_point
from src.constants import SEARCH_RADIUS

START_YEAR = 2015
END_YEAR = 2025

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
    """Load crash data from CSV file"""
    folder = 'data_sources/'
    crash_file =  'Malden_crashesJan2015-1Dec2025.csv' # 2015-2025 crash data
    crash_df = pd.read_csv(folder + crash_file, skipfooter=3, engine='python',
                    dtype={'year': 'Int32', 'speed_limit': 'Int32'})
    return crash_df


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
    url = 'http://api.walkscore.com/score?format=json&lat='+str(lat)+'&lon='+str(lon)+'&wsapikey='+apikey
    r = requests.get(url)
    data = r.json()
    return data['walkscore']



def count_zone_crashes(zone_df, thresh_year):
    """Count number of crashes in zone_df after thresh_year"""
    thresh_zone_df = zone_df[zone_df['year'] >= thresh_year] 
    crash_count = thresh_zone_df.shape[0] # count number of accidents
        
    return crash_count


def _make_crash_layers(df, map_obj):
    """Add vectorized blue/red CircleMarker GeoJson layers to a Folium map."""
    clean = df.dropna(subset=['Latitude', 'Longitude'])
    is_ped = clean['First Harmful Event'] == 'Collision with pedestrian'
    for subset, color in [(clean[~is_ped], 'blue'), (clean[is_ped], 'red')]:
        if subset.empty:
            continue
        lats = subset['Latitude'].to_numpy()
        lons = subset['Longitude'].to_numpy()
        geojson = {
            'type': 'FeatureCollection',
            'features': [
                {'type': 'Feature',
                 'geometry': {'type': 'Point', 'coordinates': [float(lo), float(la)]},
                 'properties': {}}
                for la, lo in zip(lats, lons)
            ]
        }
        folium.GeoJson(
            geojson,
            marker=folium.CircleMarker(
                radius=3, weight=3, color=color,
                fill=True, fill_color=color, fill_opacity=0.6
            )
        ).add_to(map_obj)


'''
def get_geo_points(lat_0, lon_0, zone_df):
    """Create a GeoDataFrame of points from zone_df and return a list of coordinates """
    geo_zone_raw = geopandas.points_from_xy(zone_df['Latitude'], zone_df['Longitude'])
    geo_zone_raw_df = geopandas.GeoDataFrame(
        zone_df[["Crash Year", "Latitude", "Longitude", "First Harmful Event"]],
        geometry=geo_zone_raw,
    )

    # Drop empty
    geo_zone_df = geo_zone_raw_df.loc[~geo_zone_raw_df.geometry.is_empty]
    geo_zone = geopandas.points_from_xy(geo_zone_df['Latitude'], geo_zone_df['Longitude'])
    
    # Create a geometry list from the GeoDataFrame
    geo_zone_list = [(point.x, point.y) for point in geo_zone]
    return geo_zone_df, list(set(geo_zone_list))  # overcounts if don't have set
'''

def plot_points(data, crash_df):
    """Plots an address on the map"""
    address = data[0]['address']['house_number'] + ' ' + data[0]['address']['road']
    #zone_df = pd.DataFrame()

    # Extract the latitude and longitude
    lat_0 = float(data[0]["lat"])
    lon_0 = float(data[0]["lon"])

    zone_df = crashes_near_point(lat_0, lon_0, crash_df,
                                 lat_col='Latitude', lon_col='Longitude')
    zone_df = zone_df[zone_df['Crash Year'] >= START_YEAR]
    crash_count = len(zone_df)

    m = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=18)       
#                   zoom_control=False, scrollWheelZoom=False, dragging=False)    # uncomment to freeze navigation     
          
    m.add_child(
        folium.Marker(
            location = [lat_0, lon_0], popup=address, icon=folium.Icon(color='blue')        
        ))

    
    folium.Circle(
        location=[lat_0, lon_0],
        radius=SEARCH_RADIUS / 3.281,  # feet to metres
        color='gray',
        fill=True,
        fill_color='gray',
        fill_opacity=0.15
    ).add_to(m)

    # Extract as function - pedestrian indicator
    '''
    for ind, val in enumerate(geo_zone_list):
        if geo_zone_df.iloc[ind]['First Harmful Event'] == 'Collision with pedestrian':
            folium.CircleMarker(location=geo_zone_list[ind], radius=2, weight=3, color='red').add_to(m)
        else:
            folium.CircleMarker(location=geo_zone_list[ind], radius=2, weight=3, color='blue').add_to(m)
    '''

    _make_crash_layers(zone_df, m)

    ## This code is to plot all points in a year
    #crashes_end_year_df = crash_df[crash_df['Crash Year'] == END_YEAR]
    #map_year = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=15)
    ##                zoom_control=False, scrollWheelZoom=False, dragging=False)   # uncomment to freeze

    '''
    # Create point geometries
    geometry_yr = geopandas.points_from_xy(crashes_end_year_df['Latitude'], crashes_end_year_df['Longitude'])
    geoyr_df = geopandas.GeoDataFrame(
        crashes_end_year_df[["Crash Year", "Latitude", "Longitude", "First Harmful Event"]], geometry=geometry_yr
    )  
    
    
           
    # drop empty points
    geoyr_df = geoyr_df.loc[~geoyr_df.geometry.is_empty]
    geoyr_df = geoyr_df.dropna(subset=["Latitude", "Longitude"])

    geometry_yr = geopandas.points_from_xy(geoyr_df['Latitude'], geoyr_df['Longitude'])
    # Create a geometry list from the GeoDataFrame for all data points
    geoyr_df_list = [[point.x, point.y] for point in geometry_yr]
    '''
    # Plot all crashes for END_YEAR
    crashes_end_year_df = crash_df[crash_df['Crash Year'] == END_YEAR]
    map_year = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=15)

    map_year.add_child(
        folium.Marker(
            location=[lat_0, lon_0], popup=address, icon=folium.Icon(color='blue')
        ))

    '''
    # Extract as function - pedestrian indicator
    for ind, val in enumerate(geoyr_df_list):
        if geoyr_df.iloc[ind]['First Harmful Event'] == 'Collision with pedestrian':
            folium.CircleMarker(location=geoyr_df_list[ind], radius=2, weight=3, color='red').add_to(map_year)
        else:
            folium.CircleMarker(location=geoyr_df_list[ind], radius=2, weight=3, color='blue').add_to(map_year)
    '''

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

