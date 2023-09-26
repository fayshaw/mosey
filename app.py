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
st.subheader("A safety walkability tool for pedestrians")

st.write("Location with nearby car crashes")


########## SIDE BAR - ADDRESS INPUT #############
address_input = st.sidebar.text_input("Enter an address in Malden", "")

places_dict = map_plot.malden_places
place_list = list(places_dict.keys())

location = st.sidebar.radio(
    "Or choose from one of the points of interest", place_list)

if address_input:
    address = address_input
else:
    address = map_plot.malden_places[location]

########## END SIDE BAR - ADDRESS INPUT #############


data = map_plot.geocode(address).json()  

crash_df = map_plot.load_data()
m, m22, score = map_plot.plot_points(data, crash_df)

# Map with bounding box
folium_static(m, width=600)

st.caption("Map of Malden centered around the address entered. The car crash count \
           is the number of crashes in the gray box. Blue dots indicate car crashes \
           and red dots indicate car crashes with pedestrians.")


st.subheader("Interactive Map of Malden")
st.write("Map of Malden with 2022 car crash data")

folium_static(m22, width=600)
st.caption("This map of Malden shows car crash data for 2022. Blue dots indicate car crashes\
           and red dots indicate car crashes with pedestrians.")
           

st.subheader("Motivation")
st.write("[Pedestrian death is on the rise](https://www.npr.org/2023/06/26/1184034017/us-pedestrian-deaths-high-traffic-car) in the US.\
         Massachussets reported a [35% increase in pedestrian death in 2022.](https://storymaps.arcgis.com/stories/5ef0c0ec60764c85a7e6ace69b752fd4)\
         This project is an examination of walkability with respect to pedestrian safety.  It uses car crash data in the Malden, a city north of Boston \
         with a population of 66,000.")

st.image('data_sources/car_crashes_pedestrian_pct.png', caption='Car crashes over time and pedstrian crashes as a percent of total crashes.')



st.write("Data from the [Massachusetts Department of Transportation (MassDOT) IMPACT Crash Data Portal.](https://apps.impact.dot.state.ma.us/cdp/home) \
         This analysis can be extended to other cities and towns across Massachusetts.")
st.write("Code on [Github.](https://github.com/fayzer/mosey)")



########## SIDE BAR #############
if score > 0:
    text_color = 'red'
else:
    text_color = 'black'
st.sidebar.markdown(f"<h2 style='font-size: 24px; color:{text_color}'>Car Crash Count: {score}</h1>", unsafe_allow_html=True)
st.sidebar.write("This is the count of nearby car crashes since 2003. These points of interest have high Walk Scores, \
                  but poor safety. A walkability score needs to include pedestrian safety.") 

lat_0 = float(data[0]["lat"])
lon_0 = float(data[0]["lon"])

# Walk score
walk_score = map_plot.get_walk_score(lat_0, lon_0)
st.sidebar.markdown(f"<h1 style='font-size: 24px;'>Walk Score: {walk_score}</h1>", unsafe_allow_html=True)

st.sidebar.write("[Walk Score](https://www.walkscore.com) has been developed by Redfin as a measure of walkability. It is largely based \
                    on proximity to restaurants and other amenities. [Methodology and definitions here.](https://www.walkscore.com/methodology.shtml)")
########## END SIDE BAR #############



