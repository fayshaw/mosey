import os
import re
import time

import geopandas as gpd
import networkx as nx
import pandas as pd

from src.constants import (
    CRS_MASS_STATE_PLANE,
    CRS_WGS84,
    MALDEN_STREET_CORRECTIONS,
    RATING_COLOR,
    WALK_AUDIT_NAME_Q,
    WALK_AUDIT_OVERALL_Q,
    WALK_AUDIT_SECTION_Q,
    WALK_AUDIT_SECTION_VAL,
    WALK_AUDIT_STREET_Q,
)
from src.geo_filtering import filter_to_malden_geo
from src.spatial_utils import geocodio_geocode, route_along_roads


def clean_walk_audit(raw_df):
    """
    Drop PII, filter to walk-audit section, remove all-null rows and columns.
    Returns a cleaned DataFrame (typically 31 rows × 41 cols).
    """
    df = raw_df.drop(columns=WALK_AUDIT_NAME_Q, errors='ignore')
    df = df[df[WALK_AUDIT_SECTION_Q] == WALK_AUDIT_SECTION_VAL]
    df = df.dropna(axis=0, how='all')
    df = df.dropna(axis=1, how='all')
    return df.reset_index(drop=True)


def _correct_street_name(name):
    """
    Title-case a parsed street name and apply Malden-specific corrections.
    Fixes missing suffixes (Main → Main St) and wrong suffixes (Bell Rock Ave → Bell Rock St).
    Returns the corrected string, or the title-cased input if no correction is found.
    """
    if not name:
        return name
    key = name.strip().title()
    return MALDEN_STREET_CORRECTIONS.get(key, key)


def parse_street_segment(segment):
    """
    Parse a free-text street segment description into structured fields.

    Handles formats like:
      "Bell Rock Ave, Wyllis to Converse"
      "Pleasant St between Summer St and Highland Ave"
      "Main St (Highland Ave to Pearl St)"
      "Pierce Street, starting at Salem, ending at Forest"

    Returns a dict with keys:
      along       — the primary street being audited
      begin       — the cross street at the start of the segment
      end         — the cross street at the end of the segment
      normalized  — the cleaned/normalized input string
      is_complete — True when along, begin, and end were all parsed
      raw         — the original input string
    """
    result = {
        'along': None, 'begin': None, 'end': None,
        'normalized': None, 'is_complete': False, 'raw': segment,
    }
    normalized = segment.strip()

    # Convert "Main St (Highland Ave to Pearl St)" → "Main St, Highland Ave to Pearl St"
    normalized = re.sub(
        r'(St|Ave|Rd|Blvd|Dr|Ln|Pl|Way|Ct|Ter|Sq|Cir|Park|Circle|Place|Street)'
        r'\.?(?!\s*,)\s+(?=\S+\s+to)',
        r'\1, ', normalized, flags=re.IGNORECASE,
    )

    normalized = re.sub(r'Intersection of|\)', '', normalized)
    normalized = normalized.replace('ending at', ' to ').replace('starting at', ', ')
    normalized = re.sub(r'\s+(?:from|between|meets)\s+|\(', ', ', normalized)
    normalized = re.sub(r',{2,}|\.(?=,)|\s+,', ',', normalized)
    normalized = re.sub(r'\s*,+\s*', ',', normalized)

    # Normalize street suffixes to standard abbreviations
    suffix_map = {
        r'\b(street|str|st)\b': 'St',
        r'\b(avenue|ave|av)\b': 'Ave',
        r'\b(road|rd)\b': 'Rd',
        r'\b(boulevard|blvd|blv)\b': 'Blvd',
        r'\b(drive|dr)\b': 'Dr',
        r'\b(lane|ln)\b': 'Ln',
        r'\b(place|pl)\b': 'Pl',
        r'\b(way)\b': 'Way',
        r'\b(court|ct|crt)\b': 'Ct',
        r'\b(terrace|ter|terr)\b': 'Ter',
        r'\b(square|sq)\b': 'Sq',
        r'\b(circle|cir|circ)\b': 'Cir',
        r'\b(parkway|pkwy)\b': 'Pkwy',
        r'\b(trail|tr)\b': 'Trl',
    }
    for pattern, replacement in suffix_map.items():
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    # Treat "and" as a range separator only when it connects two cross streets
    normalized = normalized.replace(' and ', ' to ')
    result['normalized'] = normalized

    parts = normalized.split(',')
    result['along'] = _correct_street_name(parts[0].strip())

    if len(parts) < 2:
        return result

    intersections = ' '.join(parts[1:]).split(' to ')
    if len(intersections) == 2:
        begin, end = intersections[0].strip(), intersections[1].strip()
        # Reject if either cross street looks like a street address (contains digits)
        if not re.search(r'\d', begin) and not re.search(r'\d', end):
            result['begin'] = _correct_street_name(begin)
            result['end']   = _correct_street_name(end)
            result['is_complete'] = True

    return result


def parse_all_segments(walk_df):
    """
    Apply parse_street_segment to every row and append parsed columns to walk_df.
    Returns the combined DataFrame.
    """
    parsed = walk_df[WALK_AUDIT_STREET_Q].apply(parse_street_segment)
    parsed_df = pd.DataFrame(parsed.tolist())
    return pd.concat([walk_df.reset_index(drop=True), parsed_df], axis=1)


def build_intersection_strings(parsed_df):
    """
    For complete rows (is_complete == True), produce two geocodable intersection
    strings per audit row — one at the begin cross street and one at the end.

    Returns a single DataFrame (begin rows first, end rows second) with an
    'intersection' column and an 'endpoint' column ('begin' or 'end').
    """
    complete = parsed_df[parsed_df['is_complete']].copy()

    begin = complete.copy()
    begin['intersection'] = begin['along'] + " & " + begin['begin'] + ", Malden, MA"
    begin['endpoint'] = 'begin'

    end = complete.copy()
    end['intersection'] = end['along'] + " & " + end['end'] + ", Malden, MA"
    end['endpoint'] = 'end'

    return pd.concat([begin, end], axis=0).reset_index(drop=True)


def geocode_intersections(intersections_df, api_key=None):
    """
    Geocode every row's 'intersection' string using the Geocodio API.
    Reads GEOCODIO_API_KEY from the environment if api_key is not supplied.
    Returns intersections_df with lat, lon, geocoding_status columns appended.
    """
    from dotenv import load_dotenv
    from geocodio import Geocodio

    load_dotenv()
    key = api_key or os.getenv('GEOCODIO_API_KEY')
    client = Geocodio(key)

    print(f"Geocoding {len(intersections_df)} intersections via Geocodio...")
    results = []
    for _, row in intersections_df.iterrows():
        results.append(geocodio_geocode(row['intersection'], client))
        time.sleep(0.2)  # stay within Geocodio's rate limit

    geocoded = pd.DataFrame(results)
    return pd.concat([intersections_df.reset_index(drop=True), geocoded], axis=1)


def add_rating_colors(walk_df, rating_col=None):
    """
    Add a 'color' column mapped from the overall walkability rating string.
    Defaults to WALK_AUDIT_OVERALL_Q from constants if rating_col is not given.
    """
    col = rating_col or WALK_AUDIT_OVERALL_Q
    df = walk_df.copy()
    df['color'] = df[col].map(RATING_COLOR)
    return df


def build_route_geodataframes(geocoded_df, G, malden_boundary=None,
                              target_crs=CRS_MASS_STATE_PLANE):
    """
    Build two GeoDataFrames from geocoded walk audit data.

    Returns:
      gdf_all   — one point per intersection endpoint (begin + end)
      gdf_lines — one road-network route LineString per audit segment

    geocoded_df must be structured with begin-endpoint rows first and
    end-endpoint rows second (as produced by geocode_intersections called on
    the output of build_intersection_strings).

    G is the OSMnx road network graph in EPSG:4326.
    Both returned GeoDataFrames are projected to target_crs.

    If malden_boundary is provided, intersection points and route lines that
    fall outside the Malden boundary (plus a 100 m buffer) are dropped.
    """
    plot_df = geocoded_df.dropna(subset=['lat', 'lon'])
    gdf_all = gpd.GeoDataFrame(
        plot_df,
        geometry=gpd.points_from_xy(plot_df['lon'], plot_df['lat']),
        crs=CRS_WGS84,
    ).to_crs(target_crs)

    if malden_boundary is not None:
        gdf_all = filter_to_malden_geo(gdf_all, malden_boundary, keep_geometry=True)
        print(f"After filtering: {len(gdf_all)} intersection points in Malden")

    num_audits = len(geocoded_df) // 2
    begin_pts = geocoded_df.iloc[:num_audits].reset_index(drop=True)
    end_pts   = geocoded_df.iloc[num_audits:].reset_index(drop=True)

    lines = []
    for i in range(num_audits):
        start = begin_pts.iloc[i]
        end   = end_pts.iloc[i]

        if pd.isnull(start['lat']) or pd.isnull(start['lon']) or \
           pd.isnull(end['lat'])   or pd.isnull(end['lon']):
            continue

        try:
            geom = route_along_roads(G, start['lon'], start['lat'],
                                      end['lon'],   end['lat'])
            lines.append({
                'geometry':          geom,
                WALK_AUDIT_OVERALL_Q: start[WALK_AUDIT_OVERALL_Q],
                'color':             start['color'],
                'along':             start.get('along'),
                'audit_id':          i,
            })
        except nx.NetworkXNoPath:
            print(f"No road path for audit {i} ({start.get('along', '?')}); skipping.")
        except Exception as e:
            print(f"Error on audit {i}: {e}")

    gdf_lines = gpd.GeoDataFrame(lines, crs=CRS_WGS84).to_crs(target_crs)

    if malden_boundary is not None:
        gdf_lines = filter_to_malden_geo(gdf_lines, malden_boundary, keep_geometry=True)
        print(f"After filtering: {len(gdf_lines)} route segments in Malden")

    return gdf_all, gdf_lines
