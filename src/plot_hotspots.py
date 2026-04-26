import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import folium
from folium.plugins import HeatMap, MarkerCluster

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
