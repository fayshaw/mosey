#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 16:38:54 2023

@author: fayshaw
"""

import streamlit as st
from streamlit_folium import folium_static  # st_folium
import map_plot
#import places

st.header("Move On Safely EverYone (MOSEY)")
st.subheader("A safety walk score for pedestrians")
st.write("Interactive map of Malden with car crash data")


### SIDE BAR - ADDRESS INPUT -----------
address_input = st.sidebar.text_input("Enter an address", "")

places_dict = map_plot.malden_places
place_list = list(places_dict.keys())

location = st.sidebar.radio(
    "Or choose from one of the points of interest", place_list)

if address_input:
    address = address_input
else:
    address = map_plot.malden_places[location]

st.sidebar.write('The address is: ', address)
### SIDE BAR - ADDRESS INPUT -----------


data = map_plot.geocode(address).json()  

#while not data:
#    error_message = st.sidebar.caption('<p style="text-align:right; color:pink;"> \
#                       Please enter a valid address.</p>', unsafe_allow_html=True)
#    address = st.sidebar.text_input("Enter an address", "442 Main Street Malden MA 02148")
#    data = map_plot.geocode(address).json()  
    
crash_df = map_plot.load_data()
m, score = map_plot.plot_points(data, crash_df)

folium_static(m, width=600)


### SIDE BAR -----------
#st.sidebar.write("<h2>MOSEY Score:</h2>", score, unsafe_allow_html=True)
st.sidebar.markdown(f"<h1 style='font-size: 36x;'>MOSEY Score: {score}</h1>", unsafe_allow_html=True)
st.sidebar.write("The MOSEY score was designed to capture walkability from the perspective of pedestrian safety. \
                 The score is calulated based on the number of car crashes in the recent years.")

lat_0 = float(data[0]["lat"])
lon_0 = float(data[0]["lon"])

# Walk score
walk_score = map_plot.get_walk_score(lat_0, lon_0)
st.sidebar.markdown(f"<h1 style='font-size: 36x;'>Walk Score: {walk_score}</h1>", unsafe_allow_html=True)
st.sidebar.markdown("Score from [Walkscore.com](https://www.walkscore.com). For methodology and definitions \
#                   visit https://www.walkscore.com/methodology.shtml")
### END SIDE BAR ----------


st.caption("Map of Malden centered around address.  The gray box indicates search space for \
           car accidents that go into the MOSEY calculation. Blue dots indicate car crashes\
           and red dots indicate car crashes involving pedestrians.")

st.subheader("Motivation")
st.write("Car crashes involving pedestrians are on the rise.")
st.image('data_sources/car_crash_plot.png', caption='Normalized car crash data of time.')


#st.write("About MOSEY")

st.write("Data from the Massachusetts Department of Transportation \
(MassDOT) Crash Data Portal \
https://apps.impact.dot.state.ma.us/cdp/home")