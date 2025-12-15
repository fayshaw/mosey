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

########## SIDE BAR - ADDRESS INPUT #############
def clear_text():
    st.session_state["user_input"] = ""

address_input = st.sidebar.text_input("Type the full address in Malden and press enter.", 
                                      "422 Main St, Malden 02148", key="user_input")
st.sidebar.button("Clear", on_click=clear_text)

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

st.subheader("Malden location with nearby car crashes.")
st.write("Input an address or choose a point of interest from the sidebar to visualize the number of \
nearby car crashes. This shows car crashes from 2015 - 2025.")
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

st.markdown('<div class="my-caption">Car crash data for 2025 (up to November 2025), map centered at the address input. Blue dots indicate car crashes\
           and red dots indicate car crashes with pedestrians. The gray box indicates search space for \
           car accidents that go into the MOSEY calculation. Blue dots indicate car crashes\
           and red dots indicate car crashes with pedestrians.<br><br></div>', unsafe_allow_html=True)

st.subheader("Historical Car Crash Data for Malden, 2015-2025")
st.image('figures/Malden_crashes_2015-2025.png')
st.markdown('<div class="my-caption">Car crashes and pedestrian crashes from January 2015 to November 2025.</div>', unsafe_allow_html=True)
st.write("Car crash data is from the [Massachusetts Department of Transportation (MassDOT) Crash Data Portal](https://apps.crashdata.dot.mass.gov/cdp/home).")


st.subheader("Motivation")

st.markdown('**US stats**')
st.write("Pedestrian death in the US has risen at an alarming rate, peaking in 2022, a \
[40-year-high](https://www.npr.org/2023/06/26/1184034017/us-pedestrian-deaths-high-traffic-car). \
This figure shows pedestrian fatalities from 1980-2022 and is from the Governers Highway Safety Association (GSHA)'s report \
[Pedestrian Traffic Fatalities by State: 2024 Preliminary Data](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data).")
st.image('figures/GHSA_ped_death_1980-2022.png')

#st.markdown(
#    '<span style="font-size: 0.85rem;">'
#    'Pedestrian death in the US from 1980 to 2022, figure from the GHSA \
#    [Pedestrian Traffic Fatalities by State: 2024 Preliminary Data](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data)</span>',
#    unsafe_allow_html=True)


#st.markdown('<div class="my-caption">Pedestrian death in the US from 1980 to 2022, figure from the \
#GHSA [Pedestrian Traffic Fatalities by State: 2024 Preliminary Data](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data)</div>', unsafe_allow_html=True)

st.markdown('**Findings from the GHSA 2024 report**')
st.markdown(' - Drivers struck and killed 7,148 people walking in the United States in 2024.')
st.markdown(' - Pedestrian deaths are increasing at a rate far faster than overall traffic fatalities. Between 2009 and 2023, pedestrian deaths rose a staggering 80%, while all other traffic fatalities increased 13%. ')
st.markdown(' - One in four pedestrian deaths (25%) is the result of a hit-and-run crash. In these fatal hit-and-runs, the vehicle that struck the pedestrian was the fleeing vehicle the vast majority (94%) of the time.')
st.markdown(' - The share of pedestrian deaths caused by SUVs and pickups has surged in recent years. Light trucks accounted for 54% of pedestrian fatalities where a vehicle type was known in 2023, compared to 37% for passenger cars.[(GHSA, 2024)](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data)')
st.markdown(' - More than three-quarters of pedestrian fatalities occur after dark. The share of nighttime deaths has skyrocketed recently. Fatal pedestrian crashes at night rose 84% between 2010 and 2023, compared to a 28% increase in daytime fatalities. [(GHSA, 2024)](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data)')
st.markdown(' - Nearly two-thirds (65%) of pedestrian deaths occurred in locations without a sidewalk in 2023. Sidewalks can help protect people walking by providing a physical separation between them and motor vehicle traffic, but they are missing or in poor condition in many parts of the country.[(GHSA, 2024)](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data)')
#st.markdown(' - [Pedestrian death peaked in 2022 ](https://www.npr.org/2023/06/26/1184034017/us-pedestrian-deaths-high-traffic-car) in the US.\
#         Massachussetts reported a [35% increase in pedestrian death in 2022.](https://storymaps.arcgis.com/stories/5ef0c0ec60764c85a7e6ace69b752fd4)')

st.image('figures/GHSA_2023 Pedestrian Deaths by the Numbers.jpg')
st.markdown(
    '<span style="font-size: 0.85rem;">'
    'Pedestrian deaths in 2023, figure from the GHSA \
    [Pedestrian Traffic Fatalities by State: 2024 Preliminary Data](https://www.ghsa.org/resource-hub/pedestrian-traffic-fatalities-2024-data)</span><br>',
    unsafe_allow_html=True)

st.markdown('**Massachussets stats**')
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
st.sidebar.write("This is the count of nearby car crashes since 2015. These points of interest have high Walk Scores, \
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



