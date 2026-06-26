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
    AUDIT_NAME_Q,
    AUDIT_OVERALL_Q,
    AUDIT_SECTION_Q,
    AUDIT_SECTION_VAL,
    AUDIT_STREET_Q,
    AUDIT_WARD_Q,
)
from src.geo_filtering import filter_to_malden_geo
from src.spatial_utils import geocodio_geocode, route_along_roads


def clean_walk_audit(raw_df):
    """
    Drop PII, filter to walk-audit section, remove all-null rows and columns.
    Returns a cleaned DataFrame (typically 31 rows × 41 cols).
    """
    df = raw_df.drop(columns=AUDIT_NAME_Q, errors='ignore')
    n_rows_raw = len(df)
    print(f"Number of rows: {n_rows_raw}")
    df = df[df[AUDIT_SECTION_Q] == AUDIT_SECTION_VAL]
    walk_rows = len(df)
    print(f"Walk audit rows: {walk_rows}")

    non_walk_rows = n_rows_raw - walk_rows
    print(f"Non walk audit rows: {non_walk_rows}")

    df = df.dropna(axis=0, how='all')
    df = df.dropna(axis=1, how='all')
    print(f"Null rows dropped: {len(df) - walk_rows}")

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
    elif len(parts) >= 3:
        # "Highland Ave, Devir St, Pearl St" — three comma-separated streets, no "to"
        begin, end = parts[1].strip(), parts[2].strip()
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
    parsed = walk_df[AUDIT_STREET_Q].apply(parse_street_segment)
    parsed_df = pd.DataFrame(parsed.tolist())
    return pd.concat([walk_df.reset_index(drop=True), parsed_df], axis=1)


def build_intersection_strings(parsed_df):
    """
    Produce two rows per audit row — one for the begin cross street and one for
    the end — with a geocodable 'intersection' string.  Rows that could not be
    fully parsed (is_complete == False) are included with intersection=None so
    they appear in the output CSV for manual lat/lon entry.

    Returns a single DataFrame (begin rows first, end rows second) with an
    'intersection' column and an 'endpoint' column ('begin' or 'end').
    """
    complete   = parsed_df[parsed_df['is_complete']].copy()
    incomplete = parsed_df[~parsed_df['is_complete']].copy()

    begin = complete.copy()
    begin['intersection'] = begin['along'] + " & " + begin['begin'] + ", Malden, MA"
    begin['endpoint'] = 'begin'

    end = complete.copy()
    end['intersection'] = end['along'] + " & " + end['end'] + ", Malden, MA"
    end['endpoint'] = 'end'

    inc_begin = incomplete.copy()
    inc_begin['intersection'] = None
    inc_begin['endpoint'] = 'begin'

    inc_end = incomplete.copy()
    inc_end['intersection'] = None
    inc_end['endpoint'] = 'end'

    return pd.concat([begin, inc_begin, end, inc_end], axis=0).reset_index(drop=True)


def flag_outside_malden(df):
    """
    Check geocoded points against the Malden boundary (+ 100m buffer).
    Any 'success' rows outside Malden get status changed to 'outside_malden'
    and lat/lon set to None.
    """
    from src.load_data import load_malden_boundary

    has_coords = df['geocoding_status'] == 'success'
    success = df[has_coords].copy()
    if success.empty:
        return df

    malden_gdf = load_malden_boundary()
    pts = gpd.GeoDataFrame(
        success,
        geometry=gpd.points_from_xy(success['lon'], success['lat']),
        crs=CRS_WGS84,
    ).to_crs(malden_gdf.crs)
    malden_buffered = malden_gdf.copy()
    malden_buffered['geometry'] = malden_gdf.buffer(100)
    inside = gpd.sjoin(pts, malden_buffered[['geometry']], predicate='within')
    outside_idx = success.index.difference(inside.index)
    for idx in outside_idx:
        row = df.loc[idx]
        print(f"  WARNING: {row['intersection']} geocoded outside Malden "
              f"({row['lat']:.4f}, {row['lon']:.4f}) — marking outside_malden")
        df.loc[idx, 'geocoding_status'] = 'outside_malden'
        df.loc[idx, ['lat', 'lon']] = None

    return df


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
        if pd.isnull(row['intersection']):
            results.append(pd.Series({'lat': None, 'lon': None, 'geocoding_status': 'needs_manual'}))
        else:
            results.append(geocodio_geocode(row['intersection'], client))
            time.sleep(0.2)  # stay within Geocodio's rate limit

    geocoded = pd.DataFrame(results)
    combined = pd.concat([intersections_df.reset_index(drop=True), geocoded], axis=1)

    return flag_outside_malden(combined)


def add_rating_colors(walk_df, rating_col=None):
    """
    Add a 'color' column mapped from the overall walkability rating string.
    Defaults to AUDIT_OVERALL_Q from constants if rating_col is not given.
    """
    col = rating_col or AUDIT_OVERALL_Q
    df = walk_df.copy()
    df['color'] = df[col].map(RATING_COLOR)
    return df


def walk_audit_summary(raw_df, geocoded_df):
    """
    Print and return a summary dict of walk audit statistics.

    Parameters
    ----------
    raw_df      : output of load_walk_audit_excel() — needed for auditor names
                  before clean_walk_audit() strips PII
    geocoded_df : output of geocode_intersections() — has begin/end rows,
                  geocoding_status, intersection, along, and rating columns
    """
    walk_rows = raw_df[raw_df[AUDIT_SECTION_Q] == AUDIT_SECTION_VAL]

    # Unique auditors: split comma-separated and "and"-joined name strings
    all_names = []
    for entry in walk_rows[AUDIT_NAME_Q].dropna():
        parts = re.split(r',|\band\b', str(entry), flags=re.IGNORECASE)
        all_names.extend(p.strip().title() for p in parts if p.strip())
    unique_auditors = sorted(set(all_names))

    # Wards: strip emoji and trailing parenthetical, keep "Ward N"
    ward_raw = walk_rows[AUDIT_WARD_Q].dropna()
    ward_labels = (ward_raw
                   .str.encode('ascii', 'ignore').str.decode('ascii')
                   .str.strip()
                   .str.extract(r'(Ward \d+)')[0]
                   .dropna())
    unique_wards = sorted(ward_labels.unique())

    # Begin-only rows avoid double-counting (each audit has a begin + end row)
    begin = geocoded_df[geocoded_df['endpoint'] == 'begin']

    unique_streets     = sorted(begin['along'].dropna().unique())
    unique_intersect   = geocoded_df['intersection'].dropna().nunique()
    geo_status         = geocoded_df['geocoding_status'].value_counts().to_dict()
    ratings            = begin[AUDIT_OVERALL_Q].value_counts().to_dict()

    summary = {
        'audits_completed':      len(walk_rows),
        'unique_auditors':       len(unique_auditors),
        'auditors':              unique_auditors,
        'wards_represented':     unique_wards,
        'unique_streets':        unique_streets,
        'unique_intersections':  unique_intersect,
        'geocoding_status':      geo_status,
        'ratings':               ratings,
    }

    # Print
    print("=== Walk Audit Summary ===")
    print(f"  Audits completed    : {summary['audits_completed']}")
    print(f"  Unique auditors     : {summary['unique_auditors']}  ({', '.join(unique_auditors)})")
    print(f"  Wards represented   : {len(unique_wards)}  ({', '.join(unique_wards)})")
    print(f"  Unique streets      : {len(unique_streets)}  ({', '.join(unique_streets)})")
    print(f"  Unique intersections: {unique_intersect}")
    print()
    print("  Ratings (begin endpoints):")
    for rating, n in sorted(ratings.items(), key=lambda x: -x[1]):
        print(f"    {rating:<12} {n}")
    print()
    print("  Geocoding status:")
    for status, n in sorted(geo_status.items(), key=lambda x: -x[1]):
        print(f"    {status:<20} {n}")

    return summary


def build_route_geodataframes(geocoded_df, G, malden_boundary=None,
                              target_crs=CRS_MASS_STATE_PLANE):
    """
    Build two GeoDataFrames from geocoded walk audit data.

    Returns:
      gdf_all   — one point per intersection endpoint (begin + end)
      gdf_lines — one road-network route LineString per audit segment

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

    sort_cols = ['along', 'begin', 'end']
    begin_pts = (geocoded_df[geocoded_df['endpoint'] == 'begin']
                 .sort_values(sort_cols).reset_index(drop=True))
    end_pts   = (geocoded_df[geocoded_df['endpoint'] == 'end']
                 .sort_values(sort_cols).reset_index(drop=True))
    num_audits = len(begin_pts)

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
                AUDIT_OVERALL_Q: start[AUDIT_OVERALL_Q],
                'color':             start['color'],
                'along':             start.get('along'),
                'audit_id':          i,
                'Timestamp':         start.get('Timestamp'),
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


def _normalize_timestamp(ts_series):
    """Parse timestamps and truncate to second precision for matching."""
    return pd.to_datetime(ts_series).dt.floor('s')


def merge_into_database(new_df, db_path):
    """
    Merge new geocoded rows into the walk audit database CSV.

    If db_path does not exist, writes new_df as the initial database.
    If it exists, appends only rows whose (Timestamp, endpoint) pair is
    not already in the database. Existing rows are never overwritten,
    so manual lat/lon fixes persist.

    Returns the merged DataFrame.
    """
    from pathlib import Path
    db_path = Path(db_path)

    if new_df.empty and db_path.exists():
        return pd.read_csv(db_path)

    if not db_path.exists():
        new_df.to_csv(db_path, index=False)
        print(f"Created {db_path} ({len(new_df)} rows)")
        return new_df

    existing = pd.read_csv(db_path)

    existing_keys = set(zip(
        _normalize_timestamp(existing['Timestamp']),
        existing['endpoint'],
    ))

    new_ts = _normalize_timestamp(new_df['Timestamp'])
    is_new = [
        (ts, ep) not in existing_keys
        for ts, ep in zip(new_ts, new_df['endpoint'])
    ]
    to_add = new_df[is_new]

    if to_add.empty:
        print("No new rows to add")
        return existing

    merged = pd.concat([existing, to_add], ignore_index=True)
    merged.to_csv(db_path, index=False)
    print(f"Added {len(to_add)} new rows to {db_path} ({len(merged)} total)")
    return merged
