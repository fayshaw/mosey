"""
Walk audit pipeline: geocode → review/fix → merge into database → map.

Usage:
  python walk_audit_cli.py                                       # map from walk_audit_database.csv (default)
  python walk_audit_cli.py --geocode                             # geocode from default Excel → staging CSV, then map
  python walk_audit_cli.py --geocode --input path/to/file.xlsx   # geocode from specific Excel → staging CSV, then map
  python walk_audit_cli.py --input path/to/file.csv              # map from a specific geocoded CSV
  python walk_audit_cli.py --html                                # also output interactive HTML map

Workflow for new data:
  0. Before running anything, check to see that raw Excel file has complete along, begin, and end streets.
     Check the comments to see what those streets might be.
  1. python walk_audit_cli.py --geocode --input walk_audit_20260623.xlsx
     → writes output/audit_geocoded.csv (staging file, review and fix lat/lon here)
  2. Manually fix any rows with geocoding_status=needs_manual in the staging CSV
  3. python walk_audit_cli.py --merge
     → merges new rows from staging into output/walk_audit_database.csv
  4. python walk_audit_cli.py
     → maps from the database

Outputs:
  output/audit_geocoded.csv        — staging file from geocoding (may need manual fixes)
  output/walk_audit_database.csv   — single source of truth (manual fixes persist across updates)
  output/walk_audit_map.png        — walk audit ratings map (road-network style)
  output/walk_audit_map_osm.png    — walk audit ratings map (OSM tile basemap)
  output/walk_audit_map.html       — interactive map with draggable labels (--html only)
  output/walk_audit_folium.html    — simple interactive Folium map with popups (--folium only)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from dotenv import load_dotenv

from src.constants import (AUDIT_RAW, AUDIT_CLEAN,
                           AUDIT_OVERALL_Q, AUDIT_WARD_Q,
                           AUDIT_GEO, AUDIT_DB, AUDIT_WARD_COUNTS,
                           AUDIT_MAP, AUDIT_MAP_OSM, AUDIT_MAP_HTML, AUDIT_MAP_FOLIUM)
from src.load_data import load_malden_boundary, load_malden_roads, load_walk_audit_excel
from src.plot_spatial import (plot_walk_audit_map, plot_walk_audit_map_osm,
                               plot_walk_audit_map_html, plot_walk_audit_folium)
from src.spatial_utils import get_malden_road_network
from src.walk_utils import (
    add_rating_colors,
    build_intersection_strings,
    build_route_geodataframes,
    clean_walk_audit,
    flag_outside_malden,
    geocode_intersections,
    merge_into_database,
    parse_all_segments,
    walk_audit_summary,
)
from src.plot_counts import plot_audit_ward_counts

load_dotenv()

parser = argparse.ArgumentParser(description="Walk audit map pipeline")
parser.add_argument('--geocode', action='store_true',
                    help='Geocode from Excel → staging CSV. Without --merge, stops after geocoding so you can review.')
parser.add_argument('--merge', action='store_true',
                    help='Merge staging CSV into the database. Can combine with --geocode to geocode and merge in one step.')
parser.add_argument('--input', metavar='FILE',
                    help='With --geocode: Excel file to geocode. With --merge: CSV to merge. Without either: CSV to map from.')
parser.add_argument('--html', action='store_true',
                    help='Also output an interactive HTML map with draggable street labels.')
parser.add_argument('--folium', action='store_true',
                    help='Output a simple Folium HTML map with per-audit popups (no road network needed).')
parser.add_argument('--ward', type=int, metavar='N',
                    help='With --folium: filter to a single ward (e.g. --ward 5).')
args = parser.parse_args()


def run_geocode_pipeline(clean_path, geocode_path):
    raw_df = load_walk_audit_excel(geocode_path)
    print(f"Loaded raw data: {raw_df.shape}")

    clean_df = clean_walk_audit(raw_df)
    # clean_df.to_csv('walk_audit_clean.csv', index=False)
    clean_df.sort_values(by=['Timestamp']).to_csv(clean_path, index=False)
    print(f"Cleaned data:    {clean_df.shape}")

    parsed_df = parse_all_segments(clean_df)
    complete  = parsed_df['is_complete'].sum()
    print(f"Parsed segments: {len(parsed_df)} rows, {complete} complete")

    intersect_df = build_intersection_strings(parsed_df)
    print(f"Intersection strings: {len(intersect_df)}")

    geocoded_df = geocode_intersections(intersect_df)
    success = (geocoded_df['geocoding_status'] == 'success').sum()
    print(f"Geocoded: {success}/{len(geocoded_df)} successful")

    geocoded_df = add_rating_colors(geocoded_df, rating_col=AUDIT_OVERALL_Q)
    geocoded_df.sort_values(by=['Timestamp'])
    geocoded_df.to_csv(AUDIT_GEO, index=False)
    print(f"Saved staging file {AUDIT_GEO} ({len(geocoded_df)} rows)")
    return geocoded_df


input_path = Path(args.input) if args.input else None

# --- Geocode step ---
if args.geocode:
    clean_path = AUDIT_CLEAN
    excel_source = input_path if input_path else AUDIT_RAW
    run_geocode_pipeline(clean_path, excel_source)
    if not args.merge:
        print(f"\nReview {AUDIT_GEO} and fix any rows, then run --merge to update the database.")
        sys.exit(0)

# --- Merge step ---
if args.merge:
    staging_path = input_path if (input_path and not args.geocode) else AUDIT_GEO
    if not Path(staging_path).exists():
        print(f"Error: staging file {staging_path} not found. Run --geocode first.")
        sys.exit(1)
    staging_df = pd.read_csv(staging_path)
    merge_into_database(staging_df, AUDIT_DB)

# --- Determine mapping source ---
if input_path and not args.geocode and not args.merge:
    map_input = input_path
elif AUDIT_DB.exists():
    map_input = AUDIT_DB
else:
    map_input = AUDIT_GEO

print(f"Using {map_input} for mapping")
geocoded_df = flag_outside_malden(pd.read_csv(map_input))

excel_source = input_path if (args.geocode and input_path) else AUDIT_RAW
raw_df = load_walk_audit_excel(excel_source)
walk_audit_summary(raw_df, geocoded_df)

ward_counts = geocoded_df[AUDIT_WARD_Q].value_counts()
plot_audit_ward_counts(ward_counts, plt_path=AUDIT_WARD_COUNTS)

malden_gdf   = load_malden_boundary()
malden_roads = load_malden_roads()

G = get_malden_road_network()
gdf_all, gdf_lines = build_route_geodataframes(geocoded_df, G)
print(f"Route GeoDataFrames: {len(gdf_all)} points, {len(gdf_lines)} segments")
plot_walk_audit_map(gdf_all, gdf_lines, malden_gdf, malden_roads, save_path=AUDIT_MAP)
plot_walk_audit_map_osm(gdf_all, gdf_lines, malden_gdf, save_path=AUDIT_MAP_OSM)
if args.html:
    plot_walk_audit_map_html(gdf_all, gdf_lines, malden_gdf=malden_gdf, save_path=AUDIT_MAP_HTML)
if args.folium:
    plot_walk_audit_folium(geocoded_df, malden_gdf=malden_gdf, gdf_lines=gdf_lines,
                           ward=args.ward, save_path=AUDIT_MAP_FOLIUM)
