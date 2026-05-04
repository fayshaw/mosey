"""
Plotting functions for crash and walk audit data.

Two groups of functions:
  - Time-series charts (crash counts by year) — called by analyze_crashes.py
  - Spatial maps (crash locations, walk audit routes) — require geopandas

All functions accept an out_dir argument so they can be called from any script
without assuming a fixed output path.
"""
import matplotlib.pyplot as plt
from src.constants import OUT_DIR

# ── Time-series plots ────────────────────────────────────────────────────────

PLOT_STYLES = {
    'crash_counts':       {'color': 'tab:blue',   'label': 'Total Car Crashes'},
    'ped_counts':         {'color': 'red',         'label': 'Crashes with Pedestrians'},
    'ped_fatal_counts':   {'color': 'darkred',     'label': 'Fatal Pedestrian Crashes',  'marker': 'x'},
    'cycle_counts':       {'color': 'orange',      'label': 'Crashes with Cyclists'},
    'cycle_fatal_counts': {'color': 'darkorange',  'label': 'Fatal Cyclist Crashes',     'marker': 'x'},
}


def plot_crashes_over_time(counts_df, OUT_DIR,
                           include_crashes=True, include_ped=True, include_cycle=True,
                           include_ped_fatal=False, include_cycle_fatal=False):
    """Line chart of crash trends by year."""
    include = {
        'crash_counts': include_crashes, 'ped_counts': include_ped,
        'ped_fatal_counts': include_ped_fatal, 'cycle_counts': include_cycle,
        'cycle_fatal_counts': include_cycle_fatal,
    }
    fig, ax = plt.subplots(figsize=(10, 5))
    for col, style in PLOT_STYLES.items():
        if include.get(col) and col in counts_df.columns:
            marker = style.get('marker', 'o')
            ax.plot(counts_df[col], f'{marker}-', color=style['color'],
                    label=style['label'], linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Crashes')
    ax.set_title('Car Crashes in Malden')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = OUT_DIR / 'crash_trends.png'
    plt.savefig(path)
    plt.close()
    print(f"Saved {path.name}")




def plot_crashes_subplots(counts_df, out_dir):
    """Two-panel line chart: total crashes (top), ped/cycle crashes (bottom)."""
    fig, axes = plt.subplots(2, 1, figsize=(8, 6))

    axes[0].set_title('Total Car Crashes')
    axes[0].plot(counts_df['crash_counts'], 'o-', label='Total Crashes', linewidth=2)
    axes[0].set_ylabel('Number of Crashes')
    axes[0].grid(True)
    axes[0].legend(loc='upper left')

    axes[1].set_title('Crashes with Pedestrians and Cyclists')
    axes[1].plot(counts_df['ped_counts'],         'o-', color='red',        label='Crashes with pedestrians', linewidth=2)
    axes[1].plot(counts_df['cycle_counts'],       '^-', color='orange',     label='Crashes with cyclists',    linewidth=2)
    axes[1].plot(counts_df['ped_fatal_counts'],   'x-', color='darkred',    label='Fatal pedestrian crashes', linewidth=2)
    axes[1].plot(counts_df['cycle_fatal_counts'], 's-', color='darkorange', label='Fatal cyclist crashes',    linewidth=2)
    axes[1].grid(True)
    axes[1].legend(loc='upper left')

    plt.tight_layout()
    path = out_dir / 'crash_trends_subplots.png'
    plt.savefig(path)
    plt.close()
    print(f"Saved {path.name}")


def plot_crashes_subplots_bar(counts_df, out_dir):
    """Three-panel chart: total line, ped/cycle line, fatal bar chart."""
    fig, axes = plt.subplots(3, 1, figsize=(10, 10))
    xticks = counts_df.index

    axes[0].set_title('Total Car Crashes')
    axes[0].plot(counts_df['crash_counts'], 'o-', label='Total Crashes', linewidth=2)
    axes[0].set_xticks(xticks)
    axes[0].set_xticklabels(counts_df.index, rotation=45)
    min_y0 = max(min(counts_df['crash_counts']) - 100, 0)
    max_y0 = max(counts_df['crash_counts']) + 100
    axes[0].set_ylim(min_y0, max_y0)
    axes[0].set_ylabel('Number of Crashes')
    axes[0].grid(True)
    axes[0].legend(loc='upper left')

    # Plot pedestrians and cyclists
    axes[1].set_title('Crashes with Pedestrians and Cyclists')
    axes[1].plot(counts_df['ped_counts'],   'o-', color='red',    label='Pedestrian Crashes', linewidth=2)
    axes[1].plot(counts_df['cycle_counts'], '^-', color='orange', label='Cyclist Crashes',    linewidth=2)
    axes[1].set_xticks(xticks)
    axes[1].set_xticklabels(counts_df.index, rotation=45)
    # min_y1 = min(min(counts_df['ped_counts']) - 20, 0)
    max_y1 = max(counts_df['ped_counts'] + 10)
    axes[1].set_ylim(0, max_y1)
    axes[1].set_ylabel('Number of Crashes')
    axes[1].grid(True)
    axes[1].legend(loc='upper left')

    axes[2].set_title('Fatal Crashes with Pedestrians and Cyclists')
    x, width = counts_df.index, 0.35
    axes[2].bar(x - width/2, counts_df['ped_fatal_counts'],   width, label='Fatal Pedestrian', color='darkred')
    axes[2].bar(x + width/2, counts_df['cycle_fatal_counts'], width, label='Fatal Cyclist',    color='darkorange')
    axes[2].set_ylabel('Number of Fatal Crashes')
    axes[2].set_xlabel('Year')
    axes[2].set_xticks(xticks)
    axes[2].set_xticklabels(counts_df.index, rotation=45)
    axes[2].set_yticks([0, 1, 2])
    axes[2].grid(True)
    axes[2].legend(loc='upper left')

    plt.tight_layout()
    path = out_dir / 'crash_trends_subplots_bar.png'
    plt.savefig(path)
    plt.close()
    print(f"Saved {path.name}")

def plot_audit_ward_counts(ward_counts, plt_path=OUT_DIR / 'ward_counts.png'):
    plt.figure(figsize=(10, 6))
    plt.bar(ward_counts.index, ward_counts.values)
    plt.xlabel('Ward')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.title('Walk Audit Ward Counts')
    plt.tight_layout()
    plt.savefig(plt_path)
    plt.close()