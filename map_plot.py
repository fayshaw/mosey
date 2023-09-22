#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 21 08:44:28 2023

@author: fayshaw
"""

import folium
import requests 
import pandas as pd
#import numpy as np
import geopandas
import re

def load_data():    
    folder = 'data_sources/'
    crash_file =  'export_7_4_2023_16_43_30.csv' # 2003-2023
    crash_df = pd.read_csv(folder + crash_file, skipfooter=3, engine='python',
                    dtype={'year': 'Int32', 'speed_limit': 'Int32'})
    return crash_df


def geocode(address):
    params = { 'format'        :'json', 
               'addressdetails': 1, 
               'q'             : address}
    headers = {'user-agent'    : 'TDI' }   #  Need to supply a user agent other than the default provided 
                                           #  by requests for the API to accept the query.    
    return requests.get('http://nominatim.openstreetmap.org/search', params=params, headers=headers)    

def check_address():
    
    return True


def get_addr_str(addr_dict):
    num = addr_dict['house_number']    
    new_road = re.sub(" ", "_", addr_dict['road'])
    addr_str = num + '_' + new_road
    return addr_str


def find_box(lat, lon):    
    lat_conv = 0.000000274    #lat: 1 ft = 0.000000274 deg
    lon_conv = 0.000000347    #lon: 1 ft = 0.000000347 deg
    
    delta = 1000 # feet
    d_lat = delta * lat_conv
    d_lon = delta * lon_conv
    
    return(lat-d_lat, lat+d_lat, lon-d_lon, lon+d_lon)

def score_address(zone_df):
    
    thresh_year = 2012
    thresh_zone_df = zone_df[zone_df['year'] > 2012]
    
    score = thresh_zone_df.shape[0] # count number of accidents
        
    # can try different scores
    return score


def plot_points(data, crash_df):
    address = data[0]['address']['house_number'] + ' ' + data[0]['address']['road']
        
    # Extract the latitude and longitude from the first result
    lat_0 = float(data[0]["lat"])
    lon_0 = float(data[0]["lon"])

    m = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=18)

    m.add_child(
        folium.Marker(
            location = [lat_0, lon_0], popup=address, icon=folium.Icon(color='blue')        
        ))

    min_lat, max_lat, min_lon, max_lon = find_box(lat_0, lon_0)
#    box = np.array([[min_lat, min_lon], [min_lat, max_lon], [max_lat, min_lon], [max_lat, max_lon]])
#    box_x, box_y = box.T

    # Create point geometries
    geometry = geopandas.points_from_xy(crash_df.lat, crash_df.lon)
    geo_raw = geopandas.GeoDataFrame(
        crash_df[['year', 'lat', 'lon', 'first_hrmf_event_descr']], geometry=geometry)

    # drop empty points
    geo_df = geo_raw.loc[~geo_raw.geometry.is_empty]
    geometry = geopandas.points_from_xy(geo_df.lat, geo_df.lon)

    # Create a geometry list from the GeoDataFrame for all data points
    geo_df_list = [[point.x, point.y] for point in geometry]  # unused
    
    
    # Create a rectangle (bounding box) on the map
    folium.Rectangle(
        bounds=[(min_lat, min_lon), (max_lat, max_lon)],
        color='gray',
        fill=True,
        fill_color='gray',
        fill_opacity=0.2
    ).add_to(m)

    zone_df = crash_df[crash_df['lat'].between(min_lat, max_lat) & crash_df['lon'].between(min_lon, max_lon)]

    # Duplicate code???
    # Create point geometries
    geo_zone = geopandas.points_from_xy(zone_df.lat, zone_df.lon)
    geo_zone_df = geopandas.GeoDataFrame(
        zone_df[['year', 'lat', 'lon', 'first_hrmf_event_descr']], geometry=geo_zone)
    
    # drop empty points
    geo_zone_df = geo_zone_df.loc[~geo_zone_df.geometry.is_empty]
    geom_zone_pts = geopandas.points_from_xy(geo_zone_df.lat, geo_zone_df.lon)    
    
    # Create a geometry list from the GeoDataFrame
    geo_zone_df_list = [[point.x, point.y] for point in geom_zone_pts]

    for ind, val in enumerate(geo_zone_df_list):
        if geo_zone_df.iloc[ind]['first_hrmf_event_descr'] == 'Collision with pedestrian':
            folium.CircleMarker(location=geo_zone_df_list[ind], radius=3, weight=6, color='red').add_to(m)
        else:
            folium.CircleMarker(location=geo_zone_df_list[ind], radius=3, weight=6, color='blue').add_to(m)

    score = score_address(zone_df)
    print(score)    

    return m



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
    m = plot_points(data, crash_df)    
    m.save(addr_str + '_map.html')

