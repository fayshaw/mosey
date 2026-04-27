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


def plot_crashes_spatial(crash_df, malden_gdf, title='Malden Crashes', save_path=None, figsize=(14, 10)):
    """
    Spatial crash map: Malden boundary + all crashes (blue) +
    pedestrian crashes (red) + cyclist crashes (orange triangle).

    Automatically filters crash_df into ped/bike subsets.
    Requires crash_df to have latitude/longitude (converts to GeoDataFrame internally).
    """
    from src.filter_crashes import filter_crashes, crashes_to_geodataframe
    from src.constants import CRS

    # Convert to GeoDataFrame
    crash_gdf = crashes_to_geodataframe(crash_df)
    crash_gdf = crash_gdf.to_crs(malden_gdf.crs)

    # Filter into subsets
    ped_df = filter_crashes(crash_df, first_harmful_event='Collision with pedestrian')
    ped_fatal = ped_df[ped_df['crash_severity'] == 'Fatal injury']
    cycle_df = filter_crashes(crash_df, first_harmful_event='Collision with cyclist')

    ped_gdf = crashes_to_geodataframe(ped_df).to_crs(malden_gdf.crs)
    ped_fatal_gdf = crashes_to_geodataframe(ped_fatal).to_crs(malden_gdf.crs)
    cycle_gdf = crashes_to_geodataframe(cycle_df).to_crs(malden_gdf.crs)

    # Plot
    fig, ax = plot_malden_boundary(malden_gdf, figsize=figsize)
    crash_gdf.plot(ax=ax, color='blue', markersize=10, alpha=0.5, label='All crashes')
    ped_gdf.plot(ax=ax, color='red', markersize=30, label='Pedestrian')
    if not ped_fatal_gdf.empty:
        ped_fatal_gdf.plot(ax=ax, color='darkred', markersize=80, label='Fatal pedestrian', marker='x') #, edgecolor='yellow', linewidth=1)
    cycle_gdf.plot(ax=ax, color='orange', markersize=30, label='Cyclist', marker='^')
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=13)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved {save_path}")
    return fig, ax

def plot_walk_audit_map(gdf_points, gdf_lines, malden_gdf, malden_roads,
                        rating_color, save_path=None):
    """
    Walk audit map: road network (gray) + audit route lines colored by rating +
    intersection points colored by rating + grouped street labels.

    Parameters
    ----------
    gdf_points  : GeoDataFrame with walk audit intersection points and an 'overall_rating' column
    gdf_lines   : GeoDataFrame with road-network routing lines and an 'overall_rating' column
    malden_gdf  : GeoDataFrame of Malden boundary
    malden_roads: GeoDataFrame of Malden road network
    rating_color: dict mapping rating strings to color strings (from src.config.RATING_COLOR)
    save_path   : optional Path to save the figure
    """
    import math

    fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
    malden_gdf.plot(ax=ax,   color='whitesmoke', edgecolor='black', linewidth=1)
    malden_roads.plot(ax=ax, color='gray',       linewidth=0.75)

    for rating, color in rating_color.items():
        line_subset  = gdf_lines[gdf_lines['overall_rating']  == rating]
        point_subset = gdf_points[gdf_points['overall_rating'] == rating]
        if not line_subset.empty:
            line_subset.plot(ax=ax,  color=color, linewidth=2.5, label=rating, alpha=0.8)
        if not point_subset.empty:
            point_subset.plot(ax=ax, color=color, markersize=6)

    # Group labels by street name to avoid overlapping text
    if 'street_label' in gdf_points.columns:
        labeled = set()
        for _, row in gdf_points.iterrows():
            label = row.get('street_label', '')
            if label and label not in labeled:
                ax.annotate(label, xy=(row.geometry.x, row.geometry.y),
                            fontsize=7, ha='center',
                            xytext=(0, 6), textcoords='offset points')
                labeled.add(label)

    ax.legend(title='Overall Rating', loc='upper right')
    ax.set_title('Malden Walk Audit Results')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300)
        print(f"Saved {save_path}")
    return fig, ax
