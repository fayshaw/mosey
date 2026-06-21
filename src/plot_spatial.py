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
                         title='Malden Crashes', save_path=None, figsize=(20, 16)):
    """
    Spatial crash map: Malden boundary + optional road network (gray) +
    all crashes (blue) + pedestrian crashes (red) + cyclist crashes (orange triangle).

    Automatically filters crash_df into ped/bike subsets.
    Requires crash_df to have latitude/longitude (converts to GeoDataFrame internally).
    malden_roads is optional; pass the output of load_malden_roads() to include it.
    """
    from src.crash_utils import is_ped_crash, is_cycle_crash
    from src.geo_filtering import crashes_to_geodataframe

    # Convert to GeoDataFrame
    crash_gdf = crashes_to_geodataframe(crash_df)
    crash_gdf = crash_gdf.to_crs(malden_gdf.crs)

    # Filter into subsets
    ped_df    = crash_df[is_ped_crash(crash_df)]
    ped_fatal = ped_df[ped_df['crash_severity'] == 'Fatal injury']
    cycle_df  = crash_df[is_cycle_crash(crash_df)]

    ped_gdf = crashes_to_geodataframe(ped_df).to_crs(malden_gdf.crs)
    ped_fatal_gdf = crashes_to_geodataframe(ped_fatal).to_crs(malden_gdf.crs)
    cycle_gdf = crashes_to_geodataframe(cycle_df).to_crs(malden_gdf.crs)

    # Plot
    fig, ax = plot_malden_boundary(malden_gdf, figsize=figsize)
    if malden_roads is not None:
        malden_roads.plot(ax=ax, color='gray', linewidth=0.5, alpha=0.7)
    crash_gdf.plot(ax=ax, color='blue', markersize=10, alpha=0.5, label='All crashes')
    ped_gdf.plot(ax=ax, color='red', markersize=20, label='Pedestrian')
    if not ped_fatal_gdf.empty:
        ped_fatal_gdf.plot(ax=ax, color='maroon', markersize=90, label='Fatal pedestrian', marker='x')
    cycle_gdf.plot(ax=ax, color='orange', markersize=20, label='Cyclist', marker='^')
    ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=13)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=300)
        print(f"Saved {save_path}")
    return fig, ax

def plot_malden_wards(wards_gdf, save_path=None, figsize=(14, 12), dpi=200):
    """
    Choropleth of Malden's 8 wards. Precincts in wards_gdf are dissolved to ward
    boundaries, each ward colored by WARD_COLORS, ward number labeled at centroid.
    """
    import matplotlib.patches as mpatches
    from src.constants import WARD_COLORS

    wards = wards_gdf.dissolve(by='WARD').reset_index()
    wards['WARD'] = wards['WARD'].astype(int)
    wards = wards.sort_values('WARD').reset_index(drop=True).to_crs('EPSG:26986')

    colors = [WARD_COLORS[w] for w in wards['WARD']]

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    wards.plot(ax=ax, color=colors, edgecolor='black', linewidth=1.5)

    for _, row in wards.iterrows():
        c = row.geometry.centroid
        ax.text(c.x, c.y, str(row['WARD']),
                fontsize=18, ha='center', va='center', fontweight='bold')

    patches = [mpatches.Patch(color=WARD_COLORS[w], label=f"Ward {w}")
               for w in wards['WARD']]
    ax.legend(handles=patches, title='Ward', fontsize=20, loc='lower right')
    ax.set_title('City of Malden \n Ward map', fontsize=24, fontweight='bold')
    ax.set_axis_off()
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"Saved {save_path}")
    return fig, ax


def plot_malden_wards_roads(wards_gdf, roads_gdf, save_path=None, figsize=(14, 12), dpi=200,
                             gdf_all=None, gdf_lines=None):
    """
    Ward boundaries (40% alpha) over the road network. Roads drawn first so they
    show through the semi-transparent ward fill. Ward numbers labeled at centroids.

    Optionally overlay walk audit data by passing gdf_all (points) and/or
    gdf_lines (route segments), both output of build_route_geodataframes().
    Audit lines and points are colored by walkability rating (RATING_COLOR).
    """
    import matplotlib.patches as mpatches
    from src.constants import WARD_COLORS, RATING_COLOR, AUDIT_OVERALL_Q

    wards = wards_gdf.dissolve(by='WARD').reset_index()
    wards['WARD'] = wards['WARD'].astype(int)
    wards = wards.sort_values('WARD').reset_index(drop=True).to_crs('EPSG:26986')
    roads = roads_gdf.to_crs('EPSG:26986')

    colors = [WARD_COLORS[w] for w in wards['WARD']]

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    roads.plot(ax=ax, color='gray', linewidth=0.6, alpha=0.8)
    wards.plot(ax=ax, color=colors, edgecolor='black', linewidth=1.5, alpha=0.4)

    pad = 500
    minx, miny, maxx, maxy = wards.total_bounds
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)

    if gdf_lines is not None:
        audit_lines = gdf_lines.to_crs('EPSG:26986')
        for rating, color in RATING_COLOR.items():
            subset = audit_lines[audit_lines[AUDIT_OVERALL_Q] == rating]
            if not subset.empty:
                subset.plot(ax=ax, color=color, linewidth=5, alpha=0.85)

    if gdf_all is not None:
        audit_pts = gdf_all.to_crs('EPSG:26986')
        for rating, color in RATING_COLOR.items():
            subset = audit_pts[audit_pts[AUDIT_OVERALL_Q] == rating]
            if not subset.empty:
                subset.plot(ax=ax, color=color, markersize=35, alpha=0.9)

    for _, row in wards.iterrows():
        c = row.geometry.centroid
        ax.text(c.x, c.y, str(row['WARD']),
                fontsize=18, ha='center', va='center', fontweight='bold')

    ward_patches = [mpatches.Patch(color=WARD_COLORS[w], label=f"Ward {w}")
                    for w in wards['WARD']]
    #legend_handles = ward_patches
    if gdf_lines is not None or gdf_all is not None:
        audit_patches = [mpatches.Patch(color=c, label=r) for r, c in RATING_COLOR.items()]
        legend_handles = audit_patches

    ax.legend(handles=legend_handles, title='Ward / Rating', fontsize=11, loc='lower right')
    title = 'City of Malden \n Ward Walk Audits' if (gdf_lines is not None or gdf_all is not None) else 'City of Malden'
    ax.set_title(title, fontsize=24, fontweight='bold')
    ax.set_axis_off()
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"Saved {save_path}")
    return fig, ax


def plot_walk_audit_map(gdf_all, gdf_lines, malden_gdf, malden_roads,
                        save_path=None, figsize=(20, 16), dpi=300):
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
    from src.constants import RATING_COLOR, AUDIT_OVERALL_Q

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    malden_gdf.plot(ax=ax,   color='whitesmoke', edgecolor='black', linewidth=1)
    malden_roads.plot(ax=ax, color='gray',       linewidth=0.75)
    pad = 500
    minx, miny, maxx, maxy = malden_gdf.total_bounds
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)

    # Lines first so they appear under the intersection points
    for rating, color in RATING_COLOR.items():
        subset = gdf_lines[gdf_lines[AUDIT_OVERALL_Q] == rating]
        if not subset.empty:
            subset.plot(ax=ax, color=color, linewidth=5, alpha=0.7)

    for rating, color in RATING_COLOR.items():
        subset = gdf_all[gdf_all[AUDIT_OVERALL_Q] == rating]
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
        if point.is_empty:
            continue
        p1 = geom.interpolate(0.49, normalized=True)
        p2 = geom.interpolate(0.51, normalized=True)
        if p1.is_empty or p2.is_empty or (p1.x == p2.x and p1.y == p2.y):
            angle = 0.0
        else:
            angle = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
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


def plot_walk_audit_map_osm(gdf_all, gdf_lines, malden_gdf,
                             save_path=None, figsize=(20, 16), dpi=150,
                             tile_source=None):
    """
    Walk audit map with an OpenStreetMap tile basemap.

    Reprojects all layers to Web Mercator (EPSG:3857) for contextily, then
    overlays the Malden boundary outline, colored audit route lines, and
    intersection rating points.

    Parameters
    ----------
    gdf_all     : GeoDataFrame of intersection points
    gdf_lines   : GeoDataFrame of road-network route lines
    malden_gdf  : GeoDataFrame of Malden boundary
    save_path   : optional path to save the figure (PNG)
    figsize     : figure size tuple
    dpi         : resolution (lower than static map — tiles add their own detail)
    tile_source : contextily tile provider; defaults to CartoDB Positron
    """
    import math
    import contextily as ctx
    import pandas as pd
    from src.constants import RATING_COLOR, AUDIT_OVERALL_Q

    WEB_MERCATOR = "EPSG:3857"

    gdf_all_wm   = gdf_all.to_crs(WEB_MERCATOR)
    gdf_lines_wm = gdf_lines.to_crs(WEB_MERCATOR)
    malden_wm    = malden_gdf.to_crs(WEB_MERCATOR)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    malden_wm.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5)
    pad = 500
    minx, miny, maxx, maxy = malden_wm.total_bounds
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)

    for rating, color in RATING_COLOR.items():
        subset = gdf_lines_wm[gdf_lines_wm[AUDIT_OVERALL_Q] == rating]
        if not subset.empty:
            subset.plot(ax=ax, color=color, linewidth=5, alpha=0.8)

    for rating, color in RATING_COLOR.items():
        subset = gdf_all_wm[gdf_all_wm[AUDIT_OVERALL_Q] == rating]
        if not subset.empty:
            subset.plot(ax=ax, color=color, markersize=35, alpha=0.9, label=rating)

    street_labels = {}
    for _, row in gdf_lines_wm.iterrows():
        street = row.get('along')
        if pd.notnull(street) and street not in street_labels:
            midpoint = row['geometry'].interpolate(0.5, normalized=True)
            street_labels[street] = (midpoint, row['geometry'])

    offset_pct = 0.02
    for street, (point, geom) in street_labels.items():
        if point.is_empty:
            continue
        p1 = geom.interpolate(0.49, normalized=True)
        p2 = geom.interpolate(0.51, normalized=True)
        if p1.is_empty or p2.is_empty or (p1.x == p2.x and p1.y == p2.y):
            angle = 0.0
        else:
            angle = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
        angle_norm = angle % 180

        if 45 < angle_norm < 135:
            label_x, label_y = point.x, point.y
        else:
            v_offset = -((ax.get_ylim()[1] - ax.get_ylim()[0]) * offset_pct)
            label_x  = point.x
            label_y  = point.y + v_offset

        ax.text(label_x, label_y, street.title(),
                fontsize=9, ha='center', va='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                          edgecolor='black', alpha=0.85, linewidth=1))

    source = tile_source or ctx.providers.CartoDB.Positron
    ctx.add_basemap(ax, source=source)

    ax.set_axis_off()
    ax.set_title('Walk Audit Ratings in Malden', fontsize=16, pad=12)
    ax.legend(title='Rating', fontsize=12, loc='upper right')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"Saved {save_path}")
    return fig, ax
