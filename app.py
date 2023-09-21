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


st.title("Capstone")
st.text("An interactive map of Malden")

address = st.sidebar.text_input("Enter an address", "442 Main Street Malden MA 02148")
data = map_plot.geocode(address).json()  
crash_df = map_plot.load_data()

m = map_plot.plot_points(address, data, crash_df)

folium_static(m, width=725)

#m.save(address[:20]+'.html')