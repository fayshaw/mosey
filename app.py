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
st.write("The project is an examination of walkability with respect to pedestrian safety. \
It shows car crash data in Malden, MA, a city north of Boston with a population of 66,000. ")

########## SIDE BAR - INPUT MODE #############
mode = st.sidebar.radio("Find a location by:", ["Address", "Intersection", "Point of Interest"])

if mode == "Address":
    raw_addr = st.sidebar.text_input("Street address (e.g. 422 Main St)", "422 Main St", key="addr_input")
    if not raw_addr.strip():
        st.info("Enter a street address in the sidebar.")
        st.stop()
    try:
        lat_0, lon_0, label = map_plot.geocode_address(raw_addr)
    except ValueError as e:
        st.error(f"Address not found — try just the street number and name. Details: {e}")
        st.stop()

elif mode == "Intersection":
    street1 = st.sidebar.text_input("Street 1 (e.g. Main St)", key="st1_input")
    street2 = st.sidebar.text_input("Street 2 (e.g. Salem St)", key="st2_input")
    if not street1.strip() or not street2.strip():
        st.info("Enter both street names in the sidebar.")
        st.stop()
    try:
        lat_0, lon_0, label = map_plot.geocode_intersection(street1, street2)
    except ValueError as e:
        st.error(f"Intersection not found — check the street names. ({e})")
        st.stop()

else:  # Point of Interest
    places_dict = map_plot.malden_places
    place_list = list(places_dict.keys())
    st.sidebar.markdown("### Points of Interest")
    location = st.sidebar.radio("Points of Interest", place_list, label_visibility="collapsed")
    try:
        lat_0, lon_0, label = map_plot.geocode_address(places_dict[location])
    except ValueError as e:
        st.error(f"Could not geocode point of interest: {e}")
        st.stop()

########## END SIDE BAR - INPUT MODE #############

crash_df = map_plot.load_data()
m, map_year, score = map_plot.plot_points(lat_0, lon_0, label, crash_df)

##########  MAP ########## 

_start = map_plot.START_YEAR
_end   = map_plot.END_YEAR
_year_range = str(_start) if _start == _end else f"{_start}–{_end}"

st.subheader("Malden location with nearby car crashes")
st.write(f"⬅️ In the sidebar, input an address or choose a point of interest to visualize the number of \
nearby car crashes for {_year_range} (red number).")

st.markdown("""
<div style="display:flex; gap:20px; align-items:center; flex-wrap:wrap;
            margin:4px 0 10px 0; font-size:0.875rem;">
  <span><svg width="12" height="12" viewBox="0 0 12 12">
    <circle cx="6" cy="6" r="5" fill="blue"/>
  </svg>&nbsp;Car crash</span>
  <span><svg width="12" height="12" viewBox="0 0 12 12">
    <circle cx="6" cy="6" r="5" fill="red"/>
  </svg>&nbsp;Crash with pedestrian</span>
  <span><svg width="13" height="13" viewBox="0 0 13 13">
    <polygon points="6,1 12,12 1,12" fill="orange" stroke="saddlebrown" stroke-width="1"/>
  </svg>&nbsp;Crash with cyclist</span>
  <span><svg width="22" height="22" viewBox="0 0 22 22">
    <circle cx="11" cy="11" r="10" fill="none" stroke="red" stroke-width="2"/>
    <line x1="5" y1="5" x2="17" y2="17" stroke="maroon" stroke-width="3"/>
    <line x1="17" y1="5" x2="5" y2="17" stroke="maroon" stroke-width="3"/>
  </svg>&nbsp;Fatal pedestrian</span>
</div>
""", unsafe_allow_html=True)

folium_static(m, width=600)
st.markdown(f'<div class="my-caption">Map centered at input address with crashes for {_year_range}.<br><br></div>',
            unsafe_allow_html=True)


st.subheader("Interactive Map of Malden")
st.write(f"Map with car crash data for {_end}")
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

st.markdown(f'<div class="my-caption">Car crash data for {_end}, map centered at the address input. \
           The gray circle indicates the search radius used for the MOSEY crash count.<br><br></div>',
           unsafe_allow_html=True)

st.subheader("Historical Car Crash Data for Malden, 2015-2025")
st.image('figures/Malden_crash_trends_2015-2025.png')
st.markdown('<div class="my-caption">Car crashes and pedestrian crashes from January 2015 to November 2025.</div>', unsafe_allow_html=True)
st.write("Car crash data is from the [Massachusetts Department of Transportation (MassDOT) Crash Data Portal](https://apps.crashdata.dot.mass.gov/cdp/home).")


st.subheader("Motivation")

st.markdown('##### US stats')
st.write("Pedestrian death in the US has risen at an alarming rate, peaking in 2022, a \
[40-year-high](https://www.npr.org/2023/06/26/1184034017/us-pedestrian-deaths-high-traffic-car). \
This figure shows pedestrian fatalities from 1980-2022 and is from the Governers Highway Safety Association (GSHA)'s report \
[Pedestrian Traffic Fatalities by State: 2024 Preliminary Data](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data).")
st.image('figures/GHSA_ped_death_1980-2022.png')


st.markdown('**Findings from the [(GHSA 2024 report)](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data)**')
st.markdown(' - Drivers struck and killed 7,148 people walking in the United States in 2024.')
st.markdown(' - Pedestrian deaths are increasing at a rate far faster than overall traffic fatalities. Between 2009 and 2023, pedestrian deaths rose a staggering 80%, while all other traffic fatalities increased 13%. ')
st.markdown(' - One in four pedestrian deaths (25%) is the result of a hit-and-run crash. In these fatal hit-and-runs, the vehicle that struck the pedestrian was the fleeing vehicle the vast majority (94%) of the time.')
st.markdown(' - The share of pedestrian deaths caused by SUVs and pickups has surged in recent years. Light trucks accounted for 54% of pedestrian fatalities where a vehicle type was known in 2023, compared to 37% for passenger cars.')
st.markdown(' - More than three-quarters of pedestrian fatalities occur after dark. The share of nighttime deaths has skyrocketed recently. Fatal pedestrian crashes at night rose 84% between 2010 and 2023, compared to a 28% increase in daytime fatalities.')
st.markdown(' - Nearly two-thirds (65%) of pedestrian deaths occurred in locations without a sidewalk in 2023. Sidewalks can help protect people walking by providing a physical separation between them and motor vehicle traffic, but they are missing or in poor condition in many parts of the country.')

st.image('figures/GHSA_2023_Pedestrian_Deaths_by_the_Numbers.jpg')
st.markdown(
    '<span style="font-size: 0.85rem;">'
    'Pedestrian deaths in 2023, figure from the GHSA \
    [Pedestrian Traffic Fatalities by State: 2024 Preliminary Data](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data)</span><br>',
    unsafe_allow_html=True)

st.markdown('##### Massachussets stats')
st.markdown(' - Older adult pedestrians were hit and killed at a higher rate than those in other age groups. 37.2% of pedestrian fatal \
crash victims were 65 or older, while this age group represents only 18.5% of the Commonwealth’s total population.')
st.markdown(" - Two of every three (66.7%) fatal pedestrian crashes took place in Environmental Justice Census Block Groups. \
Environmental Justice Population Data is based upon three demographic criteria developed by the state's Executive Office of Energy and Environmental Affairs (EEA).")
st.markdown(' - Just over half (53.3%) of the vehicles people were driving in these fatal crashes were passenger cars, while 38.7% were \
light trucks. (All vans, minivans, pickups, and SUVs are combined into the "light truck" category.)')
st.markdown(' - Approximately 61.5% of the fatal pedestrian crashes occurred in the dark (before sunrise or after sunset). \
[A July ArcGIS StoryMaps](https://storymaps.arcgis.com/templates/7c0051cfa7dd4ee49ede680c2561bb1d/preview/print) \
2024 NHTSA report found that in 2022, 78% of all pedestrian-related fatalities in the United States occurred in the dark.')


st.write("Code on [Github](https://github.com/fayzer/mosey).")

########## SIDE BAR #############
if score > 0:
    text_color = 'red'
else:
    text_color = 'black'
st.sidebar.markdown(f"<h2 style='font-size: 24px; color:{text_color}'>Car Crash Count: {score}</h1>", unsafe_allow_html=True)
st.sidebar.write(f"This is the count of nearby car crashes for {_year_range}. These points of interest have high Walk Scores, \
                  but poor safety. A walkability score needs to include pedestrian safety.")

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



