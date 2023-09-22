#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 16:38:54 2023

@author: fayshaw
"""

import streamlit as st
#import folium
from streamlit_folium import folium_static  # st_folium
#import requests 
#import pandas as pd
#import geopandas
import map_plot

st.title("MOSEY")
st.header("A safety walkscore for pedestrians")
st.write("Interactive map of Malden with car crash data")

address = st.sidebar.text_input("Enter an address", "442 Main Street Malden MA 02148")
data = map_plot.geocode(address).json()  

#while not data:
#    error_message = st.sidebar.caption('<p style="text-align:right; color:pink;"> \
#                       Please enter a valid address.</p>', unsafe_allow_html=True)
#    address = st.sidebar.text_input("Enter an address", "442 Main Street Malden MA 02148")
#    data = map_plot.geocode(address).json()  

    
crash_df = map_plot.load_data()
m = map_plot.plot_points(data, crash_df)

folium_static(m, width=725)
st.caption("Map of Malden centered around address.  Gray box indicates search space for \
           car accidents that go into the MOSEY calculation. Blue dots indicate car crashes\
           and red dots indicate car crashes involving pedestrians.")


st.subheader("Car crashes involving pedestrians are on the rise.")
st.image('data_sources/car_crash_plot.png', caption='Normalized car crash data of time.')


st.write("About MOSEY"
        
        
        
        )

st.write("Data from the Massachusetts Department of Transportation \
(MassDOT) Crash Data Portal \
https://apps.impact.dot.state.ma.us/cdp/home")