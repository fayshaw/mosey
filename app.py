#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 16:38:54 2023

@author: fayshaw
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import requests 
import pandas as pd
import geopandas

#import altair as at
#import capstone

st.title("Capstone")
st.text("An interactive map of Malden")



def geocode(address):
    params = { 'format'        :'json', 
               'addressdetails': 1, 
               'q'             : address}
    headers = {'user-agent'    : 'TDI' }   #  Need to supply a user agent other than the default provided 
                                           #  by requests for the API to accept the query.
    return requests.get('http://nominatim.openstreetmap.org/search', 
                        params=params, headers=headers)


folder = 'data_sources'

crash_file =  'export_7_4_2023_16_43_30.csv' # 2003-2023
crash_df = pd.read_csv('data_sources/' + crash_file, skipfooter=3, engine='python',
    dtype={'year': 'Int32', 'speed_limit': 'Int32'})


address = '442 Main St, Malden, MA 02148' # city center
data = geocode(address).json()


# Extract the latitude and longitude from the first result
lat_0 = float(data[0]["lat"])
lon_0 = float(data[0]["lon"])


# City Centre and points around it
map = folium.Map(location=[lat_0, lon_0], tiles="OpenStreetMap", zoom_start=15)

map.add_child(
    folium.Marker(
        location = [lat_0, lon_0], popup='City Center', icon=folium.Icon(color='blue')        
    ))


# Create point geometries
geometry = geopandas.points_from_xy(crash_df.lat, crash_df.lon)
geo_df = geopandas.GeoDataFrame(
    crash_df[["year", "lat", "lon"]], geometry=geometry)


# drop empty points
geo_ok = geo_df.loc[~geo_df.geometry.is_empty]
geometry_ok = geopandas.points_from_xy(geo_ok.lat, geo_ok.lon)

# Create a geometry list from the GeoDataFrame
geo_df_list = [[point.x, point.y] for point in geometry_ok]

for ind, val in enumerate(geo_df_list[:100]):
    # Place the markers for car crash
    folium.CircleMarker(location=geo_df_list[ind], radius=2, color='red').add_to(map)


st_data = st_folium(map, width=725)


