"""
Run the full walk audit pipeline:
  load → clean → parse → geocode → route → visualize → save

Usage:
  python walk_audit_cli.py                                      # map from existing geocoded CSV
  python walk_audit_cli.py --geocode                            # re-geocode from default Excel, then map
  python walk_audit_cli.py --geocode --input path/to/file.xlsx # re-geocode from specific Excel, then map
  python walk_audit_cli.py --input path/to/file.csv            # map from a specific geocoded CSV

Outputs:
  output/audit_geocoded.csv     — geocoded intersection data
  output/walk_audit_map.png     — walk audit ratings map (road-network style)
  output/walk_audit_map_osm.png — walk audit ratings map (OSM tile basemap)
  output/walk_audit_map.html    — interactive map with draggable labels (--html only)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from dotenv import load_dotenv

from src.constants import (AUDIT_RAW, AUDIT_OVERALL_Q, AUDIT_WARD_Q,
                           AUDIT_GEO, AUDIT_GEO_FIX, AUDIT_WARD_COUNTS,
                           AUDIT_MAP, AUDIT_MAP_OSM, AUDIT_MAP_HTML)
from src.load_data import load_malden_boundary, load_malden_roads, load_walk_audit_excel
from src.plot_spatial import plot_walk_audit_map, plot_walk_audit_map_osm, plot_walk_audit_map_html
from src.spatial_utils import get_malden_road_network
from src.walk_utils import (
    add_rating_colors,
    build_intersection_strings,
    build_route_geodataframes,
    clean_walk_audit,
    flag_outside_malden,
    geocode_intersections,
    parse_all_segments,
    walk_audit_summary,
)
from src.plot_counts import plot_audit_ward_counts

load_dotenv()

parser = argparse.ArgumentParser(description="Walk audit map pipeline")
parser.add_argument('--geocode', action='store_true',
                    help='Re-geocode from Excel before mapping. Use --input to specify a non-default Excel file.')
parser.add_argument('--input', metavar='FILE',
                    help='With --geocode: Excel file to geocode. Without: geocoded CSV to map from.')
parser.add_argument('--html', action='store_true',
                    help='Also output an interactive HTML map with draggable street labels.')
args = parser.parse_args()

def run_geocode_pipeline(excel_path):
    raw_df = load_walk_audit_excel(excel_path)
    print(f"Loaded raw data: {raw_df.shape}")

    clean_df = clean_walk_audit(raw_df)
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
    geocoded_df.to_csv(AUDIT_GEO, index=False)
    print(f"Saved {AUDIT_GEO} ({len(geocoded_df)} rows)")

input_path = Path(args.input) if args.input else None

if args.geocode:
    excel_source = input_path if input_path else AUDIT_RAW
    run_geocode_pipeline(excel_source)
    map_input = AUDIT_GEO
elif input_path:
    map_input = input_path
elif AUDIT_GEO_FIX.exists():
    map_input = AUDIT_GEO_FIX
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
