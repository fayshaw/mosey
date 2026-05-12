"""
Crash hotspot visualization functions.

Run from the project root (the folder that contains app.py):

    python -m src.plot_hotspots

This produces:
  output/vuln_heatmap.html        — Folium heatmap of ped + cyclist crashes
  output/before_after_<name>.png  — side-by-side maps for each intersection

To add a new intersection, copy one of the plot_before_after() calls at the
bottom of this file and change lat, lon, title, and optionally radius_ft and
the before/after year tuples.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import folium
from folium.plugins import HeatMap, MarkerCluster

# ── Vulnerable-user hotspot functions ────────────────────────────────────────
# These use DB schema column names (lowercase: latitude, longitude, crash_year,
# crash_severity, first_harmful_event, vuln_user_type).

# Feet → decimal degrees (approximate, valid near 42 °N)
_FT_PER_DEG_LAT = 364_000
_FT_PER_DEG_LON = 288_200


def plot_vuln_heatmap(df, zoom=14, radius=15, blur=10):
    """
    Folium heatmap of pedestrian and cyclist crashes citywide.

    Tweak `zoom`, `radius`, and `blur` to adjust appearance.
    Returns a folium.Map — call display(m) in a notebook or m.save('out.html').

    Parameters
    ----------
    df     : crash DataFrame (DB schema, lowercase columns)
    zoom   : initial map zoom
    radius : HeatMap pixel radius
    blur   : HeatMap pixel blur
    """
    from src.crash_utils import is_ped_crash, is_cycle_crash

    vuln = df[is_ped_crash(df) | is_cycle_crash(df)].dropna(
        subset=['latitude', 'longitude']
    )
    center_lat = vuln['latitude'].mean()
    center_lon = vuln['longitude'].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom,
                   tiles='OpenStreetMap')
    HeatMap(
        vuln[['latitude', 'longitude']].values.tolist(),
        radius=radius,
        blur=blur,
        min_opacity=0.4,
        gradient={0.4: 'blue', 0.6: 'cyan', 0.7: 'lime', 0.8: 'yellow', 1.0: 'red'},
    ).add_to(m)
    return m


def plot_before_after(df, lat, lon, radius_ft=500,
                      before=(2018, 2020), after=(2021, 2023),
                      title='Before / After', figsize=(16, 8)):
    """
    Side-by-side scatter maps of crashes near one intersection for two periods.

    Useful for before/after analysis of a signal installation, road change, etc.
    A black + marks the intersection center; the gray dashed box shows the search area.

    Marker colors match the app:
      blue   = car crash
      red    = pedestrian crash
      orange triangle = cyclist crash
      maroon x = fatal pedestrian

    Parameters
    ----------
    df        : crash DataFrame (DB schema, lowercase columns)
    lat, lon  : intersection center (decimal degrees)
    radius_ft : search radius in feet around the intersection
    before    : (start_year, end_year) inclusive for the "before" panel
    after     : (start_year, end_year) inclusive for the "after" panel
    title     : figure suptitle
    figsize   : matplotlib figure size

    Example
    -------
    # Highland Ave & Fellsway — traffic signal installed ~2021
    fig, axes = plot_before_after(
        crash_df, lat=42.428, lon=-71.090,
        before=(2018, 2020), after=(2021, 2023),
        title='Highland Ave & Fellsway W'
    )

    # Malden City Hall / Pleasant St & Commercial St
    fig, axes = plot_before_after(
        crash_df, lat=42.426, lon=-71.074,
        before=(2018, 2020), after=(2021, 2023),
        title='Pleasant St & Commercial St (City Hall)'
    )
    """
    from src.crash_utils import is_ped_crash, is_cycle_crash, is_fatal_ped_crash

    d_lat = radius_ft / _FT_PER_DEG_LAT
    d_lon = radius_ft / _FT_PER_DEG_LON

    nearby = df[
        df['latitude'].between(lat - d_lat, lat + d_lat) &
        df['longitude'].between(lon - d_lon, lon + d_lon)
    ]
    before_df = nearby[nearby['crash_year'].between(*before)]
    after_df  = nearby[nearby['crash_year'].between(*after)]

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    for ax, period_df, label in [
        (axes[0], before_df, f'{before[0]}–{before[1]}'),
        (axes[1], after_df,  f'{after[0]}–{after[1]}'),
    ]:
        ped_mask       = is_ped_crash(period_df)
        fatal_ped_mask = is_fatal_ped_crash(period_df)
        cycle_mask     = is_cycle_crash(period_df) & ~ped_mask
        car_mask       = ~ped_mask & ~cycle_mask

        for mask, color, marker, size, lbl in [
            (car_mask,                   'blue',   'o', 35,  'Car crash'),
            (ped_mask & ~fatal_ped_mask, 'red',    'o', 45,  'Pedestrian'),
            (cycle_mask,                 'orange',  '^', 55,  'Cyclist'),
            (fatal_ped_mask,             'maroon',  'x', 130, 'Fatal pedestrian'),
        ]:
            sub = period_df[mask]
            if not sub.empty:
                ax.scatter(sub['longitude'], sub['latitude'],
                           color=color, marker=marker, s=size,
                           alpha=0.8, linewidths=2 if marker == 'x' else 0.5,
                           label=f'{lbl} ({len(sub)})', zorder=3)

        # Intersection centre and search boundary
        ax.scatter([lon], [lat], color='black', marker='+', s=250,
                   linewidths=2.5, zorder=5, label='Intersection')
        rect = plt.Rectangle(
            (lon - d_lon, lat - d_lat), 2 * d_lon, 2 * d_lat,
            linewidth=1, edgecolor='gray', linestyle='--', facecolor='none'
        )
        ax.add_patch(rect)

        pad = 0.1
        ax.set_xlim(lon - d_lon * (1 + pad), lon + d_lon * (1 + pad))
        ax.set_ylim(lat - d_lat * (1 + pad), lat + d_lat * (1 + pad))
        ax.set_title(f'{label}  (n={len(period_df)})', fontsize=13)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)

    fig.suptitle(title, fontsize=15, fontweight='bold')
    plt.tight_layout()
    return fig, axes

def plot_kde_density(df, x='Longitude', y='Latitude', cmap='magma', levels=10, alpha=0.6):
    """
    Creates a Seaborn KDE plot that avoids the 'fireball' effect by using
    lower density levels and transparency.
    """
    plt.figure(figsize=(12, 8))
    sns.kdeplot(
        data=df, x=x, y=y, 
        cmap=cmap, 
        levels=levels, 
        fill=True, 
        alpha=alpha, 
        thresh=0.05,
        legend=True
    )
    plt.title(f'Crash Density (KDE) - {levels} Levels')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True, alpha=0.3)
    return plt.gca()

def plot_folium_heatmap(df, lat_col='Latitude', lon_col='Longitude', radius=15, blur=10, min_opacity=0.4):
    """
    Creates a Folium HeatMap that avoids the 'smoke cloud' effect by 
    setting a higher min_opacity and adjusting radius/blur.
    """
    # Filter out nulls
    heat_df = df.dropna(subset=[lat_col, lon_col])
    heat_data = [[row[lat_col], row[lon_col]] for idx, row in heat_df.iterrows()]
    
    center_lat = heat_df[lat_col].mean()
    center_lon = heat_df[lon_col].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='OpenStreetMap')
    
    # Custom gradient to avoid off-road haze (starts later)
    gradient = {
        0.4: 'blue',
        0.6: 'cyan',
        0.7: 'lime',
        0.8: 'yellow',
        1.0: 'red'
    }
    
    HeatMap(
        heat_data,
        radius=radius,
        blur=blur,
        min_opacity=min_opacity,
        max_zoom=18,
        gradient=gradient
    ).add_to(m)
    
    return m

def plot_plotly_density(df, lat_col='Latitude', lon_col='Longitude', radius=15, zoom=13):
    """
    Creates a Plotly Density Map with a fixed radius to maintain 
    intuitive magnitude across zoom levels.
    """
    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()
    
    fig = px.density_map(
        df, 
        lat=lat_col, 
        lon=lon_col, 
        radius=radius,
        center=dict(lat=center_lat, lon=center_lon), 
        zoom=zoom,
        color_continuous_scale="Viridis",
        map_style="open-street-map",
        title='Crash Density Map (Fixed Radius)'
    )
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    return fig

def plot_marker_clusters(df, lat_col='Latitude', lon_col='Longitude', popup_col='Crash Date'):
    """
    Creates an interactive Folium Marker Cluster map.
    Best for showing exact counts that resolve upon zooming.
    """
    clean_df = df.dropna(subset=[lat_col, lon_col])
    center_lat = clean_df[lat_col].mean()
    center_lon = clean_df[lon_col].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
    marker_cluster = MarkerCluster().add_to(m)
    
    for idx, row in clean_df.iterrows():
        popup_text = f"{popup_col}: {row[popup_col]}" if popup_col in row else "Crash Location"
        folium.CircleMarker(
            location=[row[lat_col], row[lon_col]],
            radius=5,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.2,
            popup=popup_text
        ).add_to(marker_cluster)
        
    return m

def plot_hexbin_density(df, lon_col='Longitude', lat_col='Latitude', gridsize=40):
    """
    Creates a Matplotlib hexbin plot for a regularized spatial grid.
    Reduces visual bias of individual points.
    """
    plt.figure(figsize=(12, 8))
    hb = plt.hexbin(df[lon_col], df[lat_col], gridsize=gridsize, cmap='YlOrRd', mincnt=1)
    plt.colorbar(hb, label='Number of Crashes')
    plt.title(f'Crash Hotspots (Hexagonal Binning, Gridsize={gridsize})')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True, alpha=0.3)
    return plt.gca()

def plot_categorical_bubbles(df, lat_col='Latitude', lon_col='Longitude', size_max=30):
    """
    Creates a Plotly categorical bubble map.
    Magnitude is represented by both size and color for maximum intuitiveness.
    """
    # Aggregate counts per location
    hotspots = df.groupby([lat_col, lon_col]).size().reset_index(name='count')
    
    fig = px.scatter_map(
        hotspots, 
        lat=lat_col, 
        lon=lon_col, 
        size='count', 
        color='count',
        color_continuous_scale="YlOrRd",
        size_max=size_max, 
        zoom=13, 
        map_style="open-street-map",
        title='Crash Hotspots by Magnitude (Bubble Map)'
    )
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    return fig


if __name__ == '__main__':
    from pathlib import Path
    from src.load_data import load_crashes_from_db

    out = Path('output')
    out.mkdir(exist_ok=True)

    print("Loading crash data from database...")
    crash_df = load_crashes_from_db(malden_only=True)

    # ── Citywide heatmap ──────────────────────────────────────────────────────
    print("Generating vulnerable-user heatmap...")
    m = plot_vuln_heatmap(crash_df, zoom=14)
    path = out / 'vuln_heatmap.html'
    m.save(str(path))
    print(f"  Saved {path}")

    # ── Before / after intersections ─────────────────────────────────────────
    # Add or edit entries here to analyse different locations.
    # lat/lon: intersection centre (copy from Google Maps — right-click → "What's here?")
    # radius_ft: how wide to search around the centre (500 ft ≈ 1 city block)
    # before/after: year ranges to compare

    intersections = [
        dict(
            lat=42.428, lon=-71.090,
            title='Highland Ave & Fellsway W',
            radius_ft=500,
            before=(2018, 2020),
            after=(2021, 2023),
        ),
        dict(
            lat=42.426, lon=-71.074,
            title='Pleasant St & Commercial St (City Hall)',
            radius_ft=600,
            before=(2018, 2020),
            after=(2021, 2023),
        ),
        dict(
            lat=42.434, lon=-71.046,
            title='Lebanon St & Broadway',
            radius_ft=500,
            before=(2018, 2020),
            after=(2021, 2023),
        ),
    ]

    for spec in intersections:
        print(f"Generating before/after: {spec['title']}...")
        fig, _ = plot_before_after(crash_df, **spec)
        slug = spec['title'].replace(' ', '_').replace('/', '-').replace('&', 'and')
        path = out / f'before_after_{slug}.png'
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved {path}")

    print("Done.")
