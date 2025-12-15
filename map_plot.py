#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Created on Thu Sep 21 08:44:28 2023

@author: fayshaw
"""

import folium
import requests 
import pandas as pd
import geopandas
import re
import streamlit as st
from dotenv import load_dotenv

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


def load_data():    
    folder = 'data_sources/'
    crash_file =  'Malden_crashesJan2015-1Dec2025.csv' # 2015-2025 crash data
    crash_df = pd.read_csv(folder + crash_file, skipfooter=3, engine='python',
                    dtype={'year': 'Int32', 'speed_limit': 'Int32'})
    return crash_df


def geocode(address):
    params = { 'format'        :'json', 
               'addressdetails': 1, 
               'q'             : address}
    headers = {'user-agent'    : 'MOSEY' }   #  Need to supply a user agent other than the default provided 
                                           #  by requests for the API to accept the query.    
    return requests.get('http://nominatim.openstreetmap.org/search', params=params, headers=headers)    


def get_addr_str(addr_dict):
    num = addr_dict['house_number']    
    new_road = re.sub(" ", "_", addr_dict['road'])
    addr_str = num + '_' + new_road
    return addr_str


def get_walk_score(lat, lon):
    load_dotenv()
    apikey = st.secrets['WALK_API']
    url = 'http://api.walkscore.com/score?format=json&lat='+str(lat)+'&lon='+str(lon)+'&wsapikey='+apikey
    r = requests.get(url)
    data = r.json()
    return data['walkscore']


def find_box(lat, lon):    
    lat_conv = 0.000000274    #lat: 1 ft = 0.000000274 deg
    lon_conv = 0.000000347    #lon: 1 ft = 0.000000347 deg
    
    delta = 2000 # feet - units seem off
    d_lat = delta * lat_conv
    d_lon = delta * lon_conv
    
    return(lat-d_lat, lat+d_lat, lon-d_lon, lon+d_lon)


def count_zone_crashes(zone_df, thresh_year):    
    thresh_zone_df = zone_df[zone_df['year'] >= thresh_year] 
    crash_count = thresh_zone_df.shape[0] # count number of accidents
        
    # can try different scores
    return crash_count


def get_geo_points(lat_0, lon_0, zone_df):
    # Create point geometries
    geo_zone_raw = geopandas.points_from_xy(zone_df['Latitude'], zone_df['Longitude'])
    geo_zone_raw_df = geopandas.GeoDataFrame(
        zone_df[["Crash Year", "Latitude", "Longitude", "First Harmful Event"]], geometry=geo_zone_raw)

    #geo_zone_df, geo_zone_list = get_geo_points(lat_0, lon_0, zone_df)
    geo_zone_raw_df = geopandas.GeoDataFrame(
        zone_df[["Crash Year", "Latitude", "Longitude", "First Harmful Event"]],
        geometry=geo_zone_raw,
    )

    # Drop empty
    geo_zone_df = geo_zone_raw_df.loc[~geo_zone_raw_df.geometry.is_empty]
    geo_zone = geopandas.points_from_xy(geo_zone_raw_df['Latitude'], geo_zone_df['Longitude'])
    
    # Create a geometry list from the GeoDataFrame
    geo_zone_list = [(point.x, point.y) for point in geo_zone]
    return geo_zone_df, list(set(geo_zone_list))  # overcounts if don't have set


def plot_points(data, crash_df):
    address = data[0]['address']['house_number'] + ' ' + data[0]['address']['road']
    zone_df = pd.DataFrame()

    # Extract the latitude and longitude
    lat_0 = float(data[0]["lat"])
    lon_0 = float(data[0]["lon"])

    min_lat, max_lat, min_lon, max_lon = find_box(lat_0, lon_0)
    crash_lat = crash_df['Latitude'].between(min_lat, max_lat)
    crash_lon = crash_df['Longitude'].between(min_lon, max_lon)
    crash_year = crash_df['Crash Year'] >= START_YEAR
    zone_df = crash_df[crash_lat & crash_lon  & crash_year]
    geo_zone_df, geo_zone_list = get_geo_points(lat_0, lon_0, zone_df)

    crash_count = len(geo_zone_list) # count number of points
                      
    m = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=18)       
#                   zoom_control=False, scrollWheelZoom=False, dragging=False)    # uncomment to freeze navigation     
          
    m.add_child(
        folium.Marker(
            location = [lat_0, lon_0], popup=address, icon=folium.Icon(color='blue')        
        ))

    
    # Create a rectangle (bounding box) on the map
    folium.Rectangle(
        bounds=[(min_lat, min_lon), (max_lat, max_lon)],
        color='gray',
        fill=True,
        fill_color='gray',
        fill_opacity=0.2
    ).add_to(m)


    for ind, val in enumerate(geo_zone_list):
        if geo_zone_df.iloc[ind]['First Harmful Event'] == 'Collision with pedestrian':
            folium.CircleMarker(location=geo_zone_list[ind], radius=2, weight=3, color='red').add_to(m)
        else:
            folium.CircleMarker(location=geo_zone_list[ind], radius=2, weight=3, color='blue').add_to(m)
            
    # This code is to plot all points in a year
    crashes_end_year_df = crash_df[crash_df['Crash Year'] == END_YEAR]
    map_year = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=15)
    #                zoom_control=False, scrollWheelZoom=False, dragging=False)   # uncomment to freeze      

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
    
    map_year.add_child(
        folium.Marker(
            location = [lat_0, lon_0], popup=address, icon=folium.Icon(color='blue')        
        ))

    for ind, val in enumerate(geoyr_df_list):
        if geoyr_df.iloc[ind]['First Harmful Event'] == 'Collision with pedestrian':
            folium.CircleMarker(location=geoyr_df_list[ind], radius=2, weight=3, color='red').add_to(map_year)
        else:
            folium.CircleMarker(location=geoyr_df_list[ind], radius=2, weight=3, color='blue').add_to(map_year)
    
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

