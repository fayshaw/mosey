#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOSEY: Move On Safely EverYone

@author: fayshaw
"""

import streamlit as st
from streamlit_folium import folium_static  # st_folium
import map_plot

st.header("Move On Safely EverYone (MOSEY)")
st.subheader("A safety walkability tool for pedestrians")

st.write("Location with nearby car crashes")


########## SIDE BAR - ADDRESS INPUT #############
def clear_text():
#    st.session_state.user_input = ""
    st.session_state["user_input"] = ""

address_input = st.sidebar.text_input("Type the full address in Malden and press enter.", 
                                      "422 Main St, Malden 02148", key="user_input")
st.sidebar.button("Clear", on_click=clear_text)


#address_input = st.sidebar.text_input("Enter a full address in Malden.", "422 Main St, Malden 02148")
#st.button("Clear address")
#if st.button:
#    address_input.("")

places_dict = map_plot.malden_places
place_list = list(places_dict.keys())

location = st.sidebar.radio(
    "To choose from one of the points of interest, clear text box.", place_list)
address = map_plot.malden_places[location]

if address_input:
    address = address_input # + " Malden MA 02148"
else:
    address = map_plot.malden_places[location]
       
########## END SIDE BAR - ADDRESS INPUT #############

data = map_plot.geocode(address).json()  

crash_df = map_plot.load_data()
m, map_year, score = map_plot.plot_points(data, crash_df)

##########  MAP ########## 
folium_static(m, width=600)


st.subheader("Interactive Map of Malden")
st.write("Map with car crash data from January - November 2025")
folium_static(map_year, width=600)

st.markdown(
    """
    <style>
    .my-caption {
        color: #000000;
        font-size: 0.85rem;
        opacity: 0.8;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="my-caption">Car crash data for 2025, map centered at the address input. Blue dots indicate car crashes\
           and red dots indicate car crashes with pedestrians. The gray box indicates search space for \
           car accidents that go into the MOSEY calculation. Blue dots indicate car crashes\
           and red dots indicate car crashes with pedestrians.</div>', unsafe_allow_html=True)


#st.caption("Car crash data for 2025, map centered at the address input. Blue dots indicate car crashes\
#           and red dots indicate car crashes with pedestrians. The gray box indicates search space for \
#           car accidents that go into the MOSEY calculation. Blue dots indicate car crashes\
#           and red dots indicate car crashes with pedestrians.")


st.subheader("Motivation")
st.write("[Pedestrian death peaked in 2022 ](https://www.npr.org/2023/06/26/1184034017/us-pedestrian-deaths-high-traffic-car) in the US.\
         Massachussets reported a [35% increase in pedestrian death in 2022.](https://storymaps.arcgis.com/stories/5ef0c0ec60764c85a7e6ace69b752fd4)\
         This project is an examination of walkability with respect to pedestrian safety.  It uses car crash data in the Malden, a city north of Boston \
         with a population of 66,000.")

#st.image('figures/car_crashes_2013-2023.png', caption='Car crashes and pedestrian crashes from 2013 to 2023.')
st.image('figures/Malden_crashes_2015-2025.png', caption='Car crashes and pedestrian crashes from 2015 to 2025.')


st.write("Data from the [Massachusetts Department of Transportation (MassDOT) Crash Data Portal](https://apps.impact.dot.state.ma.us/cdp/home).")
st.write("Code on [Github](https://github.com/fayzer/mosey).")



########## SIDE BAR #############
if score > 0:
    text_color = 'red'
else:
    text_color = 'black'
st.sidebar.markdown(f"<h2 style='font-size: 24px; color:{text_color}'>Car Crash Count: {score}</h1>", unsafe_allow_html=True)
st.sidebar.write("This is the count of nearby car crashes since 2013. These points of interest have high Walk Scores, \
                  but poor safety. A walkability score needs to include pedestrian safety.") 

lat_0 = float(data[0]["lat"])
lon_0 = float(data[0]["lon"])

# Walk score
walk_score = map_plot.get_walk_score(lat_0, lon_0)
#st.sidebar.image(['figures/walkscore-api-logo.png'](https://www.walkscore.com/how-it-works/))
#st.sidebar.markdown(f"<h1 style='font-size: 24px;'>Walk Score&#174: {walk_score}</h1>", unsafe_allow_html=True)


st.sidebar.markdown(f"<h1 style='font-size: 24px; color:#0476d0'>Walk Score&#174: {walk_score}</h1>", unsafe_allow_html=True)

#large_walkscore = '<p style="color:Blue; font-size: 24px;">New image</p>'
#st.sidebar.markdown(large_walkscore, unsafe_allow_html=True)

st.sidebar.write('''[Walk Score](https://www.walkscore.com)® has been developed by Redfin as a measure of walkability.
                 It is largely based on proximity to restaurants and other amenities. 
                 [Methodology and definitions here.](https://www.walkscore.com/methodology.shtml)''')
########## END SIDE BAR #############



