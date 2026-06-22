"""
Run the full walk audit pipeline:
  load → clean → parse → geocode → route → visualize → save

Usage:
  python walk_audit_cli.py                      # map from existing geocoded CSV
  python walk_audit_cli.py --geocode            # re-geocode from Excel, then map
  python walk_audit_cli.py --input path/to/file # map from a specific CSV

Outputs:
  output/walk_audit_geocoded.csv   — geocoded intersection data
  output/walk_audit_map.png        — walk audit ratings map (road-network style)
  output/walk_audit_map_osm.png    — walk audit ratings map (OSM tile basemap)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from dotenv import load_dotenv

from src.constants import (AUDIT_RAW, AUDIT_OVERALL_Q, AUDIT_WARD_Q,
                           AUDIT_GEO, AUDIT_GEO_FIX, AUDIT_WARD_COUNTS,
                           AUDIT_MAP, AUDIT_MAP_OSM)
from src.load_data import load_malden_boundary, load_malden_roads, load_walk_audit_excel
from src.plot_spatial import plot_walk_audit_map, plot_walk_audit_map_osm
from src.spatial_utils import get_malden_road_network
from src.walk_utils import (
    add_rating_colors,
    build_intersection_strings,
    build_route_geodataframes,
    clean_walk_audit,
    geocode_intersections,
    parse_all_segments,
    walk_audit_summary,
)
from src.plot_counts import plot_audit_ward_counts

load_dotenv()

parser = argparse.ArgumentParser(description="Walk audit map pipeline")
parser.add_argument('--geocode', action='store_true',
                    help='Re-run geocoding from the Excel source before mapping')
parser.add_argument('--input', metavar='CSV',
                    help='Use a specific geocoded CSV instead of the default')
args = parser.parse_args()

if args.geocode:
    raw_df = load_walk_audit_excel(AUDIT_RAW)
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

if args.input:
    map_input = args.input
elif AUDIT_GEO_FIX.exists():
    map_input = AUDIT_GEO_FIX
else:
    map_input = AUDIT_GEO
print(f"Using {map_input} for mapping")
geocoded_df = pd.read_csv(map_input)

raw_df = load_walk_audit_excel(AUDIT_RAW)
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
