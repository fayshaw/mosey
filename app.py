#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 16:38:54 2023

@author: fayshaw
"""

import streamlit as st
#import folium
from streamlit_folium import folium_static #st_folium
#import requests 
#import pandas as pd
#import geopandas
import map_plot


st.title("MOSEY")
st.header("A safety walkscore for pedestrians")
st.text("Interactive map of Malden with car crash data")

address = st.sidebar.text_input("Enter an address", "442 Main Street Malden MA 02148")

data = map_plot.geocode(address).json()  

if not data:
    st.sidebar.caption('<p style="text-align:right; color:pink;"> \
                         Please enter a valid address.</p>', unsafe_allow_html=True)


crash_df = map_plot.load_data()


m = map_plot.plot_points(address, data, crash_df)

folium_static(m, width=725)
