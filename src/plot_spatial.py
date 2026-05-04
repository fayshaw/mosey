"""
Plotting functions for crash and walk audit data.

Two groups of functions:
  - Time-series charts (crash counts by year) — called by analyze_crashes.py
  - Spatial maps (crash locations, walk audit routes) — require geopandas

All functions accept an out_dir argument so they can be called from any script
without assuming a fixed output path.
"""
import matplotlib.pyplot as plt


# ── Spatial map plots ────────────────────────────────────────────────────────
# These functions require geopandas. They are imported lazily so that
# the time-series functions above work without geopandas installed.

def plot_malden_boundary(malden_gdf, ax=None, figsize=(12, 10)):
    """
    Plot the Malden town boundary. Returns (fig, ax) for composing with other layers.
    If ax is provided, draws onto it instead of creating a new figure.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure
    malden_gdf.plot(ax=ax, color='whitesmoke', edgecolor='black', linewidth=1)
    return fig, ax


def plot_crashes_spatial(crash_df, malden_gdf, malden_roads=None,
                         title='Malden Crashes', save_path=None, figsize=(14, 10)):
    """
    Spatial crash map: Malden boundary + optional road network (gray) +
    all crashes (blue) + pedestrian crashes (red) + cyclist crashes (orange triangle).

    Automatically filters crash_df into ped/bike subsets.
    Requires crash_df to have latitude/longitude (converts to GeoDataFrame internally).
    malden_roads is optional; pass the output of load_malden_roads() to include it.
    """
    from src.filter_crashes import crashes_to_geodataframe
    from src.crash_utils import is_ped_crash, is_cyclist_crash

    # Convert to GeoDataFrame
    crash_gdf = crashes_to_geodataframe(crash_df)
    crash_gdf = crash_gdf.to_crs(malden_gdf.crs)

    # Filter into subsets
    ped_df    = crash_df[is_ped_crash(crash_df)]
    ped_fatal = ped_df[ped_df['crash_severity'] == 'Fatal injury']
    cycle_df  = crash_df[is_cyclist_crash(crash_df)]

    ped_gdf = crashes_to_geodataframe(ped_df).to_crs(malden_gdf.crs)
    ped_fatal_gdf = crashes_to_geodataframe(ped_fatal).to_crs(malden_gdf.crs)
    cycle_gdf = crashes_to_geodataframe(cycle_df).to_crs(malden_gdf.crs)

    # Plot
    fig, ax = plot_malden_boundary(malden_gdf, figsize=figsize)
    if malden_roads is not None:
        malden_roads.plot(ax=ax, color='gray', linewidth=0.5, alpha=0.7)
    crash_gdf.plot(ax=ax, color='blue', markersize=10, alpha=0.5, label='All crashes')
    ped_gdf.plot(ax=ax, color='red', markersize=30, label='Pedestrian')
    if not ped_fatal_gdf.empty:
        ped_fatal_gdf.plot(ax=ax, color='darkred', markersize=80, label='Fatal pedestrian', marker='x')
    cycle_gdf.plot(ax=ax, color='orange', markersize=30, label='Cyclist', marker='^')
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=13)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved {save_path}")
    return fig, ax

def plot_walk_audit_map(gdf_all, gdf_lines, malden_gdf, malden_roads,
                        save_path=None, figsize=(16, 12), dpi=300):
    """
    Walk audit map: road network (gray) + audit route lines colored by rating +
    intersection points colored by rating + direction-aware street labels.

    Parameters
    ----------
    gdf_all     : GeoDataFrame of intersection points (output of build_route_geodataframes)
    gdf_lines   : GeoDataFrame of road-network route lines (output of build_route_geodataframes)
    malden_gdf  : GeoDataFrame of Malden boundary
    malden_roads: GeoDataFrame of Malden roads
    save_path   : optional path to save the figure (PNG)
    figsize     : figure size tuple
    dpi         : resolution for both rendering and saving
    """
    import math
    import pandas as pd
    from src.constants import RATING_COLOR, WALK_AUDIT_OVERALL_Q

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    malden_gdf.plot(ax=ax,   color='whitesmoke', edgecolor='black', linewidth=1)
    malden_roads.plot(ax=ax, color='gray',       linewidth=0.75)

    # Lines first so they appear under the intersection points
    for rating, color in RATING_COLOR.items():
        subset = gdf_lines[gdf_lines[WALK_AUDIT_OVERALL_Q] == rating]
        if not subset.empty:
            subset.plot(ax=ax, color=color, linewidth=5, alpha=0.7)

    for rating, color in RATING_COLOR.items():
        subset = gdf_all[gdf_all[WALK_AUDIT_OVERALL_Q] == rating]
        if not subset.empty:
            subset.plot(ax=ax, color=color, markersize=35, alpha=0.8, label=rating)

    # Direction-aware street labels: one per street name, placed at segment midpoint.
    # Labels on roughly horizontal segments are nudged slightly downward to clear the line.
    street_labels = {}
    for _, row in gdf_lines.iterrows():
        street = row.get('along')
        if pd.notnull(street) and street not in street_labels:
            midpoint = row['geometry'].interpolate(0.5, normalized=True)
            street_labels[street] = (midpoint, row['geometry'])

    offset_pct = 0.02
    for street, (point, geom) in street_labels.items():
        p1 = geom.interpolate(0.49, normalized=True)
        p2 = geom.interpolate(0.51, normalized=True)
        angle      = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
        angle_norm = angle % 180

        if 45 < angle_norm < 135:
            # Roughly vertical street — label at midpoint, no offset needed
            label_x, label_y = point.x, point.y
        else:
            # Roughly horizontal street — nudge label slightly below the line
            v_offset = -((ax.get_ylim()[1] - ax.get_ylim()[0]) * offset_pct)
            label_x  = point.x
            label_y  = point.y + v_offset

        ax.text(label_x, label_y, street.title(),
                fontsize=9, ha='center', va='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                          edgecolor='black', alpha=0.85, linewidth=1))

    ax.set_title('Walk Audit Ratings in Malden', fontsize=16)
    ax.legend(title='Rating', fontsize=12, loc='upper right')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"Saved {save_path}")
    return fig, ax
