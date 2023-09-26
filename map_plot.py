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
import os
#from dotenv import load_dotenv


malden_places = {
    'Centre St & Main St'          : '205 Centre St, Malden, MA 02148',
    'Main St & Salem St'           : '442 Main Street Malden MA 02148',
    'Ferryway School'              : '150 Cross St, Malden, MA 02148',  
    'Beebe School'                 : '401 Pleasant St, Malden, MA 02148',
    'Early Learning Center'        : '257 Mountain Ave, Malden, MA 02148',
    'Malden Center T Station'      : '30 Commercial St, Malden, MA 02148',
    'MA 99 at Broadway Plaza '     : '62 Broadway, Malden, MA 02148'
    }



def load_data():    
    folder = 'data_sources/'
    crash_file = 'export_7_4_2023_16_43_30.csv' # 2003-2023
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


def get_addr_str(addr_dict):
    num = addr_dict['house_number']    
    new_road = re.sub(" ", "_", addr_dict['road'])
    addr_str = num + '_' + new_road
    return addr_str


def get_walk_score(lat, lon):
    apikey = os.getenv("WALK_API")
    url = 'http://api.walkscore.com/score?format=json&lat='+str(lat)+'&lon='+str(lon)+'&wsapikey='+apikey
    r = requests.get(url)
    data = r.json()
    return data['walkscore']


def find_box(lat, lon):    
    lat_conv = 0.000000274    #lat: 1 ft = 0.000000274 deg
    lon_conv = 0.000000347    #lon: 1 ft = 0.000000347 deg
    
    delta = 1000 # feet
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
    geo_zone_raw = geopandas.points_from_xy(zone_df.lat, zone_df.lon)
    geo_zone_raw_df = geopandas.GeoDataFrame(
        zone_df[["year", "lat", "lon", "first_hrmf_event_descr"]], geometry=geo_zone_raw)
    
    # Drop empty
    geo_zone_df = geo_zone_raw_df.loc[~geo_zone_raw_df.geometry.is_empty]
    geo_zone = geopandas.points_from_xy(geo_zone_raw_df.lat, geo_zone_df.lon)
    
    # Create a geometry list from the GeoDataFrame
    geo_zone_list = [[point.x, point.y] for point in geo_zone]
    return geo_zone_df, geo_zone_list


def plot_points(data, crash_df):
    address = data[0]['address']['house_number'] + ' ' + data[0]['address']['road']
    
    zone_df = pd.DataFrame()

    # Extract the latitude and longitude from the first result
    lat_0 = float(data[0]["lat"])
    lon_0 = float(data[0]["lon"])

    min_lat, max_lat, min_lon, max_lon = find_box(lat_0, lon_0)
    zone_df = crash_df[crash_df['lat'].between(min_lat, max_lat) & crash_df['lon'].between(min_lon, max_lon)]

    geo_zone_df, geo_zone_list = get_geo_points(lat_0, lon_0, zone_df)

#    thresh_year = 2002
#    thresh_year = 2013

#    thresh_zone_df = zone_df[zone_df['year'] >= thresh_year] 
    crash_count = zone_df.shape[0] # count number of accidents
 
    m = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=18)       
#                   zoom_control=False, scrollWheelZoom=False, dragging=False)    # to freeze navigation     
          
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
        if geo_zone_df.iloc[ind]['first_hrmf_event_descr'] == 'Collision with pedestrian':
            folium.CircleMarker(location=geo_zone_list[ind], radius=2, weight=3, color='red').add_to(m)
        else:
            folium.CircleMarker(location=geo_zone_list[ind], radius=2, weight=3, color='blue').add_to(m)
            
    
    
    # This code is to plot all points in 2022
    
    crash22_df = crash_df[crash_df['year'] == 2022]    
    m22 = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=15)

#    m22 = folium.Map(location=[lat_1, lon_1], tiles="OpenStreetMap", zoom_start=18, 
#                   zoom_control=False, scrollWheelZoom=False, dragging=False)         

#    start_address = '442 Main Street',    # Immigrant Learning Center
#    lat_1 = 42.427119
#    lon_1 = -71.067107


    # Create point geometries
    geometry22 = geopandas.points_from_xy(crash22_df.lat, crash22_df.lon)
    geo22_df = geopandas.GeoDataFrame(
        crash22_df[["year", "lat", "lon", "first_hrmf_event_descr"]], geometry=geometry22
    )
        
           
    # drop empty points
    geo22_df = geo22_df.loc[~geo22_df.geometry.is_empty]
    geometry22 = geopandas.points_from_xy(geo22_df.lat, geo22_df.lon)
    # Create a geometry list from the GeoDataFrame for all data points
    geo22_df_list = [[point.x, point.y] for point in geometry22]  # unused
    
    m22.add_child(
        folium.Marker(
            location = [lat_0, lon_0], popup=address, icon=folium.Icon(color='blue')        
        ))

    

    for ind, val in enumerate(geo22_df_list):
        if geo22_df.iloc[ind]['first_hrmf_event_descr'] == 'Collision with pedestrian':
            folium.CircleMarker(location=geo22_df_list[ind], radius=2, weight=3, color='red').add_to(m22)
        else:
            folium.CircleMarker(location=geo22_df_list[ind], radius=2, weight=3, color='blue').add_to(m22)

    
    return m, m22, crash_count



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
    m, m22, score = plot_points(data, crash_df)    
    m.save(addr_str + '_map.html')

