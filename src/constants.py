from pathlib import Path

# Project root (src/config.py → src/ → project root)
ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / 'output'
DATA_DIR = ROOT / 'data_sources'

# Crashes
CRASH_FILE       = DATA_DIR / "Malden_crashesJan2015-1Dec2025.csv"
CRASH_DB         = ROOT / "db/crashes.db"

# GIS
TOWN_SURVEY_SHP    = ROOT / "GIS/townssurvey_shp/TOWNSSURVEY_POLY.shp"
ROADS_SHP          = ROOT / "GIS/statewide_viewer_SHP/gisdata/men1/infrastructure/EOTROADS_ARC.shp"
ROAD_NETWORK       = ROOT / "GIS/malden_road_network.graphml"
WARDSPRECINCTS_SHP = ROOT / "GIS/statewide_viewer_SHP/gisdata/men1/Political_Boundaries/WARDSPRECINCTS2022_POLY.shp"

# Coordinate reference systems
CRS                  = "EPSG:4326"
CRS_WGS84            = "EPSG:4326"
CRS_MASS_STATE_PLANE = "EPSG:26986"

# Crash output file paths
CRASH_COUNTS_CSV       = OUT_DIR  / 'crash_counts_by_year.csv'
CRASH_TRENDS           = 'crashes_{start_year}-{end_year}.png'
CRASH_TRENDS_SUBPLOTS  = 'crashes_subplots_{min_year}-{max_year}.png'
CRASH_TRENDS_BAR       = 'crashes_bar_{min_year}-{max_year}.png'
CRASH_TRENDS_COMBINED  = 'crashes_subplots_bar_{min_year}-{max_year}'
CRASH_SPATIAL_RANGE    = 'crashes_spatial_{start_year}-{end_year}.png'
CRASH_SPATIAL_YEAR     = 'crashes_spatial_{year}.png'
CRASH_RAW              = 'raw_crash_data_{year}.csv'

# Walk audit file paths
AUDIT_RAW         = DATA_DIR / "Walk_Audit_Responses_2026-06-19_edited.xlsx"
AUDIT_RAW_FIX     = DATA_DIR / "Walk_Audit_Responses_2026-06-19_edited.xlsx"
AUDIT_GEO         = OUT_DIR  / "audit_geocoded.csv"
AUDIT_GEO_FIX     = OUT_DIR  / "audit_geocoded_fixed.csv"
AUDIT_WARD_COUNTS = OUT_DIR  / "ward_counts.png"
AUDIT_MAP         = OUT_DIR  / "walk_audit_map.png"
AUDIT_MAP_OSM     = OUT_DIR  / "walk_audit_map_osm.png"
WARD_MAP            = OUT_DIR  / "malden_wards.png"
WARD_ROADS_MAP      = OUT_DIR  / "malden_wards_roads.png"
WARD_ROADS_AUDIT_MAP = OUT_DIR / "malden_wards_roads_audit.png"


# MassDOT CSV column names → database column names
COLUMN_MAP = {
    'Crash Number':                                         'crash_number',
    'Crash Date':                                           'crash_date',
    'Crash Year':                                           'crash_year',
    'Crash Time':                                           'crash_time',
    'Crash Hour':                                           'crash_hour',
    'Crash Severity':                                       'crash_severity',
    'First Harmful Event':                                  'first_harmful_event',
    'First Harmful Event Location':                         'first_harmful_event_location',
    'Latitude':                                             'latitude',
    'Longitude':                                            'longitude',
    'Max Injury Severity Reported':                         'max_injury_severity',
    'Total Fatalities':                                     'total_fatalities',
    'Total Non-Fatal Injuries':                             'total_nonfatal_injuries',
    'Most Harmful Event (All Vehicles)':                    'most_harmful_event_all',
    'Number of Vehicles':                                   'num_vehicles',
    'Age of Driver - Youngest Known':                       'age_driver_young',
    'Age of Driver - Oldest Known':                         'age_driver_old',
    'Age of Vulnerable User - Youngest Known':              'age_vuln_user_young',
    'Age of Vulnerable User - Oldest Known':                'age_vuln_user_old',
    'Driver Contributing Circumstances (All Drivers)':      'driver_contrib_circumst',
    'Manner of Collision':                                  'manner_of_collision',
    'Vehicle Actions Prior to Crash (All Vehicles)':        'vehicle_action_pre_crash',
    'Vehicle Configuration (All Vehicles)':                 'vehicle_configurations',
    'Vehicle Towed From Scene (All Vehicles)':              'vehicle_towed_from_scene',
    'Vehicle Travel Directions (All Vehicles)':             'vehicle_travel_directions',
    'Vulnerable User Action (All Persons)':                 'vuln_user_action',
    'Vulnerable User Location (All Persons)':               'vuln_user_location',
    'Vulnerable User Type (All Persons)':                   'vuln_user_type',
    'Vehicle Sequence of Events (All Vehicles)':            'vehicle_sequence_events',
    'Vulnerable User Sequence of Events (All Persons)':     'vuln_user_sequence_events',
    'Vulnerable User Contributing Circumstances (All Persons)': 'vuln_user_contrib_circumst',
    'Speed Limit':                                          'speed_limit',
    'Roadway':                                              'roadway',
    'Street Name-linked RD':                                'street_name_linked_rd',
    'From Street Name-linked RD':                           'from_street_name_linked_rd',
    'To Street Name-linked RD':                             'to_street_name_linked_rd',
    'Near Intersection Roadway':                            'near_intersection',
    'Light Conditions':                                     'light_conditions',
    'Weather Conditions':                                   'weather_conditions',
    'Road Surface Condition':                               'road_surface',
    'Hit and Run':                                          'hit_and_run',
    'Roadway Junction Type':                                'roadway_junction_type',
    'Traffic Control Device Type':                          'traffic_ctrl_device_type',
    'Trafficway Description':                               'trafficway_description',
    'Geocoding Method':                                     'geocoding_method',
    'Crash Report IDs':                                     'crash_report_ids',
}

# Walk audit rating scales
RATING_VALUE = {'Great': 4, 'Acceptable': 3, 'Mixed': 2, 'Poor': 1}
RATING_COLOR = {'Great': 'darkgreen', 'Acceptable': 'lightgreen', 'Mixed': 'gold', 'Poor': 'red'}

# Ward fill colors (keys are int ward numbers 1–8)
WARD_COLORS = {
    1: 'saddlebrown',
    2: 'purple',
    3: 'red',
    4: 'orange',
    5: 'yellow',
    6: 'green',
    7: 'gray',
    8: 'blue',
}

# Malden-specific street name corrections applied after parsing.
# Keys are title-cased names; values are the canonical form.
# Add entries here whenever a survey response uses the wrong or missing suffix.
MALDEN_STREET_CORRECTIONS = {
    # Missing suffixes
    'Main':          'Main St',
    'Summer':        'Summer St',
    'Salem':         'Salem St',
    'Lebanon':       'Lebanon St',
    'Canal':         'Canal St',
    'Medford':       'Medford St',
    'Highland':      'Highland Ave',
    'Eastern':       'Eastern Ave',
    'Willow':        'Willow St',
    'Bryant':        'Bryant St',
    'Earl':          'Earl St',
    'Ferry':         'Ferry St',
    'Glenwood':      'Glenwood St',
    'Wyllis':        'Wyllis Ave',
    'Charles':       'Charles St',
    'Commercial':    'Commercial St',
    'Forest':        'Forest St',
    'Forrest':       'Forrest St',
    'Cross':         'Cross St',
    'Center':        'Center St',
    'Converse':      'Converse Ave',
    'Pearl':         'Pearl St',
    'Maple':         'Maple St',
    'Essex':         'Essex St',
    # Wrong suffix in survey responses
    'Bell Rock Ave': 'Bell Rock St',
}

# Walk audit column question strings (must match the spreadsheet headers exactly)
AUDIT_NAME_Q      = "If you would like to be contacted for follow ups, please share your name. If in a group, share everyone's name separated by commas."
AUDIT_WARD_Q      = "What Ward are you Walking in? (Optional)"
AUDIT_SECTION_Q   = "Which Section of the Walk Audit are you Completing?"
AUDIT_SECTION_VAL = "Sidewalks, Streets and Crossings (WALKING AUDIT)"
AUDIT_STREET_Q    = "Which street are you auditing? Please indicate starting and ending locations. \nEx. Pleasant St. from Commercial to Main"
AUDIT_OVERALL_Q   = "Walkability of the area, based on the findings above:  "

SEARCH_RADIUS = 150  # feet radius for nearby-crash queries
SCHOOL_RADIUS = 300  # feet — wider search area around school buildings to take into account multiple intersections

malden_places = {
    'Immigrant Learning Center'    : '442 Main Street Malden MA 02148',
    'Malden Public Library'        : '36 Salem St., Malden, MA 02148',
    'Malden High School'           : '77 Salem St, Malden, MA 02148',
    'Malden City Hall'             : '215 Pleasant St, Malden, MA 02148',
    'Ferryway School'              : '150 Cross St, Malden, MA 02148',
    'Salemwood School'             : '529 Salem St, Malden, MA 02148',
    'Beebe School'                 : '401 Pleasant St, Malden, MA 02148',
    'Linden STEAM Academy'         : '29 Wescott St, Malden, MA 02148',
    'Early Learning Center'        : '257 Mountain Ave, Malden, MA 02148',
    'Forestdale School'            : '74 Sylvan Street, Malden, MA 02148',
    'Oak Grove Station'            : '287 Washington St, Malden, MA 02148',
    'MA 99 at Broadway Plaza '     : '62 Broadway, Malden, MA 02148',
    'Fellsway & Salem'             : '104 Fellsway W, Medford, MA 02155'
}
