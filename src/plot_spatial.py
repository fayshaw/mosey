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

    street_labels = {}
    for _, row in gdf_lines.iterrows():
        street = row.get('along')
        if pd.notnull(street) and street not in street_labels:
            midpoint = row['geometry'].interpolate(0.5, normalized=True)
            street_labels[street] = midpoint

    from adjustText import adjust_text
    texts = []
    for street, point in street_labels.items():
        if point.is_empty:
            continue
        texts.append(ax.text(
            point.x, point.y, street.title(),
            fontsize=9, ha='center', va='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                      edgecolor='black', alpha=0.85, linewidth=1)))

    adjust_text(texts, ax=ax, force_text=(0.5, 0.5), force_points=(0.3, 0.3),
                expand=(1.4, 1.4), ensure_inside_axes=True)

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
            street_labels[street] = midpoint

    from adjustText import adjust_text
    texts = []
    for street, point in street_labels.items():
        if point.is_empty:
            continue
        texts.append(ax.text(
            point.x, point.y, street.title(),
            fontsize=9, ha='center', va='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow',
                      edgecolor='black', alpha=0.85, linewidth=1)))

    adjust_text(texts, ax=ax, force_text=(0.5, 0.5), force_points=(0.3, 0.3),
                expand=(1.4, 1.4), ensure_inside_axes=True)

    source = tile_source or ctx.providers.CartoDB.Positron
    ctx.add_basemap(ax, source=source)

    ax.set_axis_off()
    ax.set_title('Walk Audit Ratings in Malden', fontsize=16, pad=12)
    ax.legend(title='Rating', fontsize=16, loc='upper right')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
        print(f"Saved {save_path}")
    return fig, ax


def plot_walk_audit_map_html(gdf_all, gdf_lines, malden_gdf=None, save_path=None):
    """
    Interactive Folium/Leaflet HTML map of walk audit ratings.

    Route segments are drawn as colored polylines. Street name labels are
    rendered as draggable markers so the user can reposition them in the
    browser before screenshotting.

    Parameters
    ----------
    gdf_all    : GeoDataFrame of intersection points (output of build_route_geodataframes)
    gdf_lines  : GeoDataFrame of route LineStrings  (output of build_route_geodataframes)
    malden_gdf : optional GeoDataFrame of Malden boundary
    save_path  : optional path to write the HTML file
    """
    import folium
    import pandas as pd
    from src.constants import RATING_COLOR, AUDIT_OVERALL_Q

    gdf_lines_wgs = gdf_lines.to_crs("EPSG:4326")

    center = [42.4259, -71.0662]
    m = folium.Map(location=center, zoom_start=14, tiles="CartoDB positron")

    if malden_gdf is not None:
        folium.GeoJson(
            malden_gdf.to_crs("EPSG:4326").__geo_interface__,
            style_function=lambda _: {
                "fillColor": "none",
                "color": "black",
                "weight": 2,
            },
        ).add_to(m)

    def _polyline_coords(geom):
        """Return list-of-lists of (lat, lon) for LineString or MultiLineString."""
        from shapely.geometry import MultiLineString
        parts = geom.geoms if isinstance(geom, MultiLineString) else [geom]
        return [[(y, x) for x, y in part.coords] for part in parts]

    # Colored route segments
    for _, row in gdf_lines_wgs.iterrows():
        if row["geometry"] is None or row["geometry"].is_empty:
            continue
        rating = row.get(AUDIT_OVERALL_Q)
        color  = RATING_COLOR.get(rating, "gray")
        tooltip = f"{row.get('along', '')} — {rating}"
        for coords in _polyline_coords(row["geometry"]):
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=6,
                opacity=0.85,
                tooltip=tooltip,
            ).add_to(m)

    # Draggable street name labels at segment midpoints
    street_labels = {}
    for _, row in gdf_lines_wgs.iterrows():
        street = row.get("along")
        if pd.notnull(street) and street not in street_labels:
            midpoint = row["geometry"].interpolate(0.5, normalized=True)
            rating   = row.get(AUDIT_OVERALL_Q)
            street_labels[street] = (midpoint, RATING_COLOR.get(rating, "gray"))

    for street, (point, color) in street_labels.items():
        if point.is_empty:
            continue
        label = street.title()
        width = len(label) * 7 + 16
        folium.Marker(
            location=[point.y, point.x],
            icon=folium.DivIcon(
                html=(
                    f'<div class="audit-label" style="background:lightyellow;'
                    f'border:1.5px solid black;border-radius:4px;padding:2px 6px;'
                    f'font-size:11px;font-weight:bold;white-space:nowrap;'
                    f'cursor:move;transform-origin:center center;">'
                    f"{label}</div>"
                ),
                icon_size=(width, 22),
                icon_anchor=(width // 2, 11),
            ),
            draggable=True,
            tooltip=label,
        ).add_to(m)

    map_var = m.get_name()
    base_zoom = 14
    zoom_scale_js = f"""
    <script>
    {map_var}.on('zoomend', function() {{
        var scale = Math.pow(2, {map_var}.getZoom() - {base_zoom});
        scale = Math.max(0.3, Math.min(scale, 1.0));
        document.querySelectorAll('.audit-label').forEach(function(el) {{
            el.style.transform = 'scale(' + scale + ')';
        }});
    }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(zoom_scale_js))

    # Legend
    legend_items = "".join(
        f'<span style="background:{c};display:inline-block;width:14px;height:14px;'
        f'margin-right:6px;border-radius:2px;vertical-align:middle;"></span>{r}<br>'
        for r, c in RATING_COLOR.items()
    )
    legend_html = (
        '<div style="position:fixed;bottom:30px;right:30px;z-index:1000;'
        'background:white;padding:10px 14px;border:2px solid gray;'
        'border-radius:6px;font-size:13px;font-family:sans-serif;">'
        f"<b>Walk Audit Rating</b><br>{legend_items}</div>"
    )
    m.get_root().html.add_child(folium.Element(legend_html))

    if save_path:
        m.save(str(save_path))
        print(f"Saved {save_path}")
    return m


def plot_walk_audit_folium(geocoded_df, malden_gdf=None, gdf_lines=None,
                           wards_gdf=None, ward=None, save_path=None):
    """
    Interactive Folium map of walk audit data with per-audit popups.

    When gdf_lines is provided, routes follow real roads (road-snapped MultiLineStrings
    from build_route_geodataframes). Without it, routes are straight lines between
    begin/end geocoded points.

    Parameters
    ----------
    geocoded_df : DataFrame from walk_audit_database.csv or audit_geocoded.csv
    malden_gdf  : optional GeoDataFrame of Malden boundary
    gdf_lines   : optional GeoDataFrame from build_route_geodataframes (road-snapped routes)
    wards_gdf   : optional GeoDataFrame of ward/precinct boundaries (from load_malden_wards)
    ward        : optional int ward number to filter to (e.g. 5 shows only Ward 5)
    save_path   : optional path to write the HTML file
    """
    import folium
    import pandas as pd
    from src.constants import RATING_COLOR, AUDIT_OVERALL_Q, AUDIT_WARD_Q

    df = geocoded_df.copy()
    if ward is not None:
        df = df[df[AUDIT_WARD_Q].str.contains(f"Ward {ward}", na=False)]

    SIDEWALK_COLS = [
        ("Buffer/curb",        '1. Is separated from the street by a barrier or buffer (a curb, grass, landscaping)  '),
        ("Smooth surface",     '2. Is surfaced with a material that is smooth and consistent (e.g., concrete or asphalt rather than bricks)   '),
        ("Good condition",     '3. Is in good condition, without cracks or raised sections '),
        ("Free of obstacles",  '4. Is free of obstacles (hydrants, utility poles, overgrown landscaping, trash receptacles) '),
        ("Free of driveways",  '5. Is free of interruptions from driveways (such as to/from homes, parking lots, etc.) '),
        ("Continuous",         "6. Is continuous (no segments are missing) and complete (it doesn't randomly end) "),
        ("Wide enough (≥5ft)", '7. Is wide enough (at least 5 feet) for two people to walk side by side or pass one another '),
        ("Tactile indicators", '8. Has tactile ground surface indicators so pedestrians with vision impairment will know when the path is ending '),
        ("Curb cut ramps",     '9. Has a curb cut ramp (for use by wheelchairs, baby strollers, etc.) wherever it is interrupted by a street '),
    ]
    CROSSING_COLS = [
        ("Traffic lights",     '1. Has traffic lights and/or stop signs at intersections and crossings '),
        ("Controls visible",   '2. The traffic lights and/or stop signs are clearly visible to drivers and pedestrians '),
        ("Has crosswalks",     '3. Has crosswalks '),
        ("Crosswalks marked",  '4. The crosswalks are well marked and clearly visible to drivers and pedestrians '),
        ("Ped signage",        '5. Has signage alerting drivers to the presence of pedestrians '),
        ("Bike lane",          '6. Has a designated bicycle lane '),
    ]

    def _score_cell(val):
        try:
            v = float(val)
            bg = '#c8e6c9' if v >= 4 else '#fff9c4' if v >= 3 else '#ffcdd2'
            return f'<td style="background:{bg};text-align:center;padding:1px 6px">{v:.0f}</td>'
        except (TypeError, ValueError):
            return '<td style="text-align:center;padding:1px 6px">—</td>'

    def _popup_html(row):
        street = str(row.get('along', ''))
        ward_  = str(row.get(AUDIT_WARD_Q, ''))
        rating = str(row.get(AUDIT_OVERALL_Q, ''))
        rcolor = RATING_COLOR.get(rating, 'gray')
        sw_rows = ''.join(
            f'<tr><td style="padding:1px 4px">{lbl}</td>{_score_cell(row.get(col))}</tr>'
            for lbl, col in SIDEWALK_COLS
        )
        cr_rows = ''.join(
            f'<tr><td style="padding:1px 4px">{lbl}</td>{_score_cell(row.get(col))}</tr>'
            for lbl, col in CROSSING_COLS
        )
        return (
            '<div style="font-family:sans-serif;font-size:12px;min-width:240px;'
            'max-height:400px;overflow-y:auto">'
            f'<b style="font-size:14px">{street}</b><br>'
            f'<span style="color:gray;font-size:11px">{ward_}</span><br>'
            f'<span style="background:{rcolor};padding:2px 8px;border-radius:3px;'
            f'font-weight:bold;color:white;display:inline-block;margin:3px 0">{rating}</span>'
            '<table style="border-collapse:collapse;width:100%;margin-top:4px">'
            '<tr><th colspan="2" style="text-align:left;padding:2px 4px;background:#eee">'
            'Sidewalk (1–5)</th></tr>'
            f'{sw_rows}'
            '<tr><th colspan="2" style="text-align:left;padding:2px 4px;background:#eee">'
            'Crossing (1–5)</th></tr>'
            f'{cr_rows}'
            '</table></div>'
        )

    begin_df = df[df['endpoint'] == 'begin'].dropna(subset=['lat', 'lon'])
    end_df   = df[df['endpoint'] == 'end']

    # Build a Timestamp → survey-row lookup for popup data
    survey_by_ts = begin_df.set_index('Timestamp')

    if ward is not None and len(begin_df) > 0:
        center = [begin_df['lat'].mean(), begin_df['lon'].mean()]
        zoom   = 15
    else:
        center = [42.4259, -71.0662]
        zoom   = 14

    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")

    if malden_gdf is not None:
        folium.GeoJson(
            malden_gdf.to_crs("EPSG:4326").__geo_interface__,
            style_function=lambda _: {"fillColor": "none", "color": "black", "weight": 2},
        ).add_to(m)

    if wards_gdf is not None and ward is not None:
        ward_boundary = (
            wards_gdf[wards_gdf['WARD'] == str(ward)]
            .dissolve()
            .to_crs("EPSG:4326")
        )
        folium.GeoJson(
            ward_boundary.__geo_interface__,
            style_function=lambda _: {
                "fillColor": "#1a73e8",
                "fillOpacity": 0.06,
                "color": "#1a73e8",
                "weight": 2.5,
                "dashArray": "6, 4",
            },
            tooltip=f"Ward {ward}",
        ).add_to(m)

    rating_groups = {r: folium.FeatureGroup(name=r, show=True) for r in RATING_COLOR}
    rating_groups['Unknown'] = folium.FeatureGroup(name='Unknown', show=True)
    for g in rating_groups.values():
        g.add_to(m)

    def _polyline_coords(geom):
        from shapely.geometry import MultiLineString
        parts = geom.geoms if isinstance(geom, MultiLineString) else [geom]
        return [[(y, x) for x, y in part.coords] for part in parts]

    if gdf_lines is not None:
        # Road-snapped routes: join gdf_lines to survey data via Timestamp
        lines_wgs = gdf_lines.to_crs("EPSG:4326")
        for _, line_row in lines_wgs.iterrows():
            ts     = line_row.get('Timestamp')
            rating = str(line_row.get(AUDIT_OVERALL_Q, ''))
            color  = RATING_COLOR.get(rating, 'gray')
            group  = rating_groups.get(rating, rating_groups['Unknown'])

            # Skip routes not in the current ward filter
            if ts not in survey_by_ts.index:
                continue

            survey_row = survey_by_ts.loc[ts]
            # loc returns a DataFrame when there are duplicate Timestamps; take first
            if isinstance(survey_row, pd.DataFrame):
                survey_row = survey_row.iloc[0]

            geom = line_row.get('geometry')
            if geom is None or geom.is_empty:
                continue
            tooltip = f"{line_row.get('along', '')} — {rating}"
            for coords in _polyline_coords(geom):
                folium.PolyLine(
                    locations=coords,
                    color=color,
                    weight=5,
                    opacity=0.8,
                    tooltip=tooltip,
                ).add_to(group)

            # CircleMarker at the start of the routed line
            start_coord = _polyline_coords(geom)[0][0]
            folium.CircleMarker(
                location=start_coord,
                radius=8,
                color='black',
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                popup=folium.Popup(_popup_html(survey_row), max_width=300),
                tooltip=tooltip,
            ).add_to(group)

    else:
        # Fallback: straight lines between geocoded begin/end points
        for _, b_row in begin_df.iterrows():
            ts     = b_row.get('Timestamp')
            rating = str(b_row.get(AUDIT_OVERALL_Q, ''))
            color  = RATING_COLOR.get(rating, 'gray')
            group  = rating_groups.get(rating, rating_groups['Unknown'])
            b_lat, b_lon = float(b_row['lat']), float(b_row['lon'])

            e_match = end_df[end_df['Timestamp'] == ts]
            if len(e_match) > 0:
                e_row = e_match.iloc[0]
                e_lat, e_lon = e_row.get('lat'), e_row.get('lon')
                if pd.notna(e_lat) and pd.notna(e_lon):
                    folium.PolyLine(
                        locations=[(b_lat, b_lon), (float(e_lat), float(e_lon))],
                        color=color,
                        weight=5,
                        opacity=0.8,
                        tooltip=f"{b_row.get('along', '')} — {rating}",
                    ).add_to(group)

            folium.CircleMarker(
                location=[b_lat, b_lon],
                radius=8,
                color='black',
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                popup=folium.Popup(_popup_html(b_row), max_width=300),
                tooltip=f"{b_row.get('along', '')} — {rating}",
            ).add_to(group)

    folium.LayerControl(collapsed=False).add_to(m)

    legend_items = ''.join(
        f'<span style="background:{c};display:inline-block;width:14px;height:14px;'
        f'margin-right:6px;border-radius:2px;vertical-align:middle;"></span>{r}<br>'
        for r, c in RATING_COLOR.items()
    )
    m.get_root().html.add_child(folium.Element(
        '<div style="position:fixed;bottom:30px;right:30px;z-index:1000;'
        'background:white;padding:10px 14px;border:2px solid gray;'
        'border-radius:6px;font-size:13px;font-family:sans-serif;">'
        f'<b>Walk Audit Rating</b><br>{legend_items}</div>'
    ))

    if save_path:
        m.save(str(save_path))
        print(f"Saved {save_path}")
    return m
