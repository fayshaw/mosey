"""
Run the full walk audit pipeline:
  load → clean → parse → geocode → route → save

Outputs:
  data_sources/walk_audit_geocoded.csv  — geocoded intersection data
  GIS/malden_road_network.graphml       — cached road network (on first run)
"""
from dotenv import load_dotenv

from src.constants import OUT_DIR, WALK_AUDIT_FILE, WALK_AUDIT_OVERALL_Q
from src.load_data import load_walk_audit_excel
from src.spatial_utils import get_malden_road_network
from src.walk_audit import (
    add_rating_colors,
    build_intersection_strings,
    build_route_geodataframes,
    clean_walk_audit,
    geocode_intersections,
    parse_all_segments,
)


load_dotenv()

raw_df      = load_walk_audit_excel(WALK_AUDIT_FILE)
print(f"Loaded raw data: {raw_df.shape}")

clean_df    = clean_walk_audit(raw_df)
print(f"Cleaned data:    {clean_df.shape}")

parsed_df   = parse_all_segments(clean_df)
complete    = parsed_df['is_complete'].sum()
print(f"Parsed segments: {len(parsed_df)} rows, {complete} complete")

intersect_df = build_intersection_strings(parsed_df)
print(f"Intersection strings: {len(intersect_df)}")

geocoded_df = geocode_intersections(intersect_df)
success     = (geocoded_df['geocoding_status'] == 'success').sum()
print(f"Geocoded: {success}/{len(geocoded_df)} successful")

geocoded_df = add_rating_colors(geocoded_df, rating_col=WALK_AUDIT_OVERALL_Q)

out_path = OUT_DIR / "walk_audit_geocoded.csv"
geocoded_df.to_csv(out_path, index=False)
print(f"Saved {out_path} ({len(geocoded_df)} rows)")

G = get_malden_road_network()
gdf_all, gdf_lines = build_route_geodataframes(geocoded_df, G)
print(f"Route GeoDataFrames: {len(gdf_all)} points, {len(gdf_lines)} segments")

