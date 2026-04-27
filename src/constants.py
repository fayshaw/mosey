from pathlib import Path

# Project root (src/config.py → src/ → project root)
ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / 'output'
DATA_DIR = ROOT / 'data_sources'

# File paths
CRASH_FILE         = DATA_DIR / "Malden_crashesJan2015-1Dec2025.csv"
WALK_AUDIT_FILE    = DATA_DIR / "Walk Audit Responses.xlsx"
TOWN_SURVEY_SHP    = ROOT / "GIS/townssurvey_shp/TOWNSSURVEY_POLY.shp"
ROADS_SHP          = ROOT / "GIS/statewide_viewer_SHP/gisdata/men1/infrastructure/EOTROADS_ARC.shp"
ROAD_NETWORK_CACHE = ROOT / "GIS/malden_road_network.graphml"
DB_PATH            = ROOT / "db/crashes.db"
CRS = "EPSG:4326"

# MassDOT CSV column names → database column names
COLUMN_MAP = {
    'Crash Number':                                         'crash_number',
    'Crash Date':                                           'crash_date',
    'Crash Year':                                           'crash_year',
    'Crash Time':                                           'crash_time',
    'Crash Hour':                                           'crash_hour',
    'Crash Severity':                                       'crash_severity',
    'First Harmful Event':                                  'first_harmful_event',
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

# Coordinate reference systems
CRS_WGS84            = "EPSG:4326"
CRS_MASS_STATE_PLANE = "EPSG:26986"

# Walk audit rating scales
RATING_VALUE = {'Great': 4, 'Acceptable': 3, 'Mixed': 2, 'Poor': 1}
RATING_COLOR = {'Great': 'darkgreen', 'Acceptable': 'lightgreen', 'Mixed': 'gold', 'Poor': 'red'}

# Walk audit column question strings (must match the spreadsheet headers exactly)
WALK_AUDIT_NAME_Q      = "If you would like to be contacted for follow ups, please share your name. If in a group, share everyone's name separated by commas."
WALK_AUDIT_WARD_Q      = "What Ward are you Walking in? (Optional)"
WALK_AUDIT_SECTION_Q   = "Which Section of the Walk Audit are you Completing?"
WALK_AUDIT_SECTION_VAL = "Sidewalks, Streets and Crossings (WALKING AUDIT)"
WALK_AUDIT_STREET_Q    = "Which street are you auditing? Please indicate starting and ending locations."
WALK_AUDIT_OVERALL_Q   = "Walkability of the area, based on the findings above:  "
