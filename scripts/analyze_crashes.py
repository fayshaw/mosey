"""
Analyze Malden car crash data and generate time-series plots.

USAGE
-----
Run from the project root (Data/mosey/):

    python scripts/analyze_crashes.py

OUTPUTS  (written to output/)
-------
    crash_counts_by_year.csv      — crash counts by year and type
    crash_trends_annotate.png     — line chart with fatal crash value labels
    crash_trends_subplots_bar.png — 3-panel chart: total, ped/cycle line, fatal bar

DATA SOURCE
-----------
Loaded from db/app.db (SQLite, 2015–present).

To rebuild the database from scratch (drops existing data):
    python src/init_db.py

To load a new MassDOT CSV export into the existing database:
    python -c "
    from src.data_loader import ingest_csv_to_db
    ingest_csv_to_db('data_sources/new_export.csv')
    "

To query the database directly:
    python -c "
    from src.data_loader import load_crashes_from_db
    df = load_crashes_from_db(start_year=2022)
    print(df.shape)
    "
"""
import sys
from pathlib import Path

# Allow 'from src.x import ...' when running from project root or scripts/
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt

from src.config import DB_PATH
from src.data_loader import load_crashes_from_db

OUT_DIR = Path(__file__).parent.parent / 'output'

# Column names match the database schema (snake_case)
CRASH_TYPES = {
    'crash_counts':       {},
    'ped_counts':         {'first_harmful_event': 'Collision with pedestrian'},
    'ped_fatal_counts':   {'first_harmful_event': 'Collision with pedestrian',
                           'crash_severity': 'Fatal injury'},
    'cycle_counts':       {'first_harmful_event': 'Collision with cyclist'},
    'cycle_fatal_counts': {'first_harmful_event': 'Collision with cyclist',
                           'crash_severity': 'Fatal injury'},
}


def filter_crashes(df, **criteria):
    """Filter DataFrame by column=value pairs. Column names are snake_case DB names."""
    result = df
    for column, value in criteria.items():
        result = result[result[column] == value]
    return result


def split_data_years(df):
    """Write one CSV per year to output/raw_crash_data_YYYY.csv."""
    for year in range(int(df['crash_year'].min()), int(df['crash_year'].max()) + 1):
        df[df['crash_year'] == year].to_csv(
            OUT_DIR / f'raw_crash_data_{year}.csv', index=False
        )


def get_counts(df, name='crash_counts'):
    """Return crash counts per year as a named Series."""
    return df['crash_year'].value_counts().sort_index().rename(name)


def plot_crashes_over_time_annotate(all_stats_df, include_crashes=True, include_ped=True,
                                    include_cycle=True, include_ped_fatal=False,
                                    include_cycle_fatal=False):
    """Line chart of crash trends; annotates fatal crash counts above each point."""
    fig, ax = plt.subplots(figsize=(10, 5))

    columns = {
        'crash_counts':       {'include': include_crashes,    'color': 'tab:blue', 'label': 'Total Car Crashes'},
        'ped_counts':         {'include': include_ped,        'color': 'red',      'label': 'Crashes with Pedestrians'},
        'ped_fatal_counts':   {'include': include_ped_fatal,  'color': 'darkred',  'label': 'Fatal Pedestrian Crashes',   'marker': 'x'},
        'cycle_counts':       {'include': include_cycle,      'color': 'orange',   'label': 'Crashes with Cyclists'},
        'cycle_fatal_counts': {'include': include_cycle_fatal,'color': 'darkorange','label': 'Fatal Cyclist Crashes',     'marker': 'x'},
    }

    for col, style in columns.items():
        if style['include'] and col in all_stats_df.columns:
            marker = style.get('marker', 'o')
            ax.plot(all_stats_df[col], f'{marker}-', color=style['color'],
                    label=style['label'], linewidth=2)
            if 'fatal' in col:
                for year, value in all_stats_df[col].items():
                    ax.text(year, value + 0.1, str(int(value)),
                            ha='center', va='bottom', fontsize=8)

    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Crashes')
    ax.set_title('Car Crashes in Malden')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(OUT_DIR / 'crash_trends_annotate.png')
    print("Saved crash_trends_annotate.png")


def plot_crashes_subplots(all_counts_df):
    """Two-panel line chart: total crashes (top), ped/cycle crashes (bottom)."""
    fig, axes = plt.subplots(2, 1, figsize=(8, 6))

    axes[0].set_title('Total Car Crashes')
    axes[0].plot(all_counts_df['crash_counts'], 'o-', label='Total Crashes', linewidth=2)
    axes[0].set_ylabel('Number of Crashes')
    axes[0].grid(True)
    axes[0].legend(loc='upper left')

    axes[1].set_title('Crashes with Pedestrians and Cyclists')
    axes[1].plot(all_counts_df['ped_counts'],         'o-', color='red',       label='Crashes with pedestrians', linewidth=2)
    axes[1].plot(all_counts_df['cycle_counts'],       '^-', color='orange',    label='Crashes with cyclists',    linewidth=2)
    axes[1].plot(all_counts_df['ped_fatal_counts'],   'x-', color='darkred',   label='Fatal pedestrian crashes', linewidth=2)
    axes[1].plot(all_counts_df['cycle_fatal_counts'], 's-', color='darkorange',label='Fatal cyclist crashes',    linewidth=2)
    axes[1].grid(True)
    axes[1].legend(loc='upper left')

    plt.tight_layout()
    plt.savefig(OUT_DIR / 'crash_trends_subplots.png')
    print("Saved crash_trends_subplots.png")


def plot_crashes_over_time(all_stats_df, include_crashes=True, include_ped=True,
                           include_cycle=True, include_ped_fatal=False,
                           include_cycle_fatal=False):
    """Line chart of crash trends (no annotations)."""
    fig, ax = plt.subplots(figsize=(10, 5))

    columns = {
        'crash_counts':       {'include': include_crashes,    'color': 'blue',      'label': 'Total Car Crashes'},
        'ped_counts':         {'include': include_ped,        'color': 'red',       'label': 'Crashes with Pedestrians'},
        'ped_fatal_counts':   {'include': include_ped_fatal,  'color': 'darkred',   'label': 'Fatal Pedestrian Crashes',  'marker': 'x'},
        'cycle_counts':       {'include': include_cycle,      'color': 'orange',    'label': 'Crashes with Cyclists'},
        'cycle_fatal_counts': {'include': include_cycle_fatal,'color': 'darkorange','label': 'Fatal Cyclist Crashes',     'marker': 'x'},
    }

    for col, style in columns.items():
        if style['include'] and col in all_stats_df.columns:
            marker = style.get('marker', 'o')
            ax.plot(all_stats_df[col], f'{marker}-', color=style['color'],
                    label=style['label'], linewidth=2)

    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Crashes')
    ax.set_title('Car Crashes in Malden')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / 'crash_trends.png')
    print("Saved crash_trends.png")


def plot_crashes_subplots_bar(all_counts_df):
    """Three-panel chart: total line, ped/cycle line, fatal bar chart."""
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    xticks = all_counts_df.index

    axes[0].set_title('Total Car Crashes')
    axes[0].plot(all_counts_df['crash_counts'], 'o-', label='Total Crashes', linewidth=2)
    axes[0].set_xticks(xticks)
    axes[0].set_ylim(600, 1100)
    axes[0].set_ylabel('Number of Crashes')
    axes[0].grid(True)
    axes[0].legend(loc='upper left')

    axes[1].set_title('Crashes with Pedestrians and Cyclists')
    axes[1].plot(all_counts_df['ped_counts'],   'o-', color='red',    label='Pedestrian Crashes', linewidth=2)
    axes[1].plot(all_counts_df['cycle_counts'], '^-', color='orange', label='Cyclist Crashes',    linewidth=2)
    axes[1].set_xticks(xticks)
    axes[1].set_ylabel('Number of Crashes')
    axes[1].grid(True)
    axes[1].legend(loc='upper left')

    axes[2].set_title('Fatal Crashes with Pedestrians and Cyclists')
    x, width = all_counts_df.index, 0.35
    axes[2].bar(x - width/2, all_counts_df['ped_fatal_counts'],   width, label='Fatal Pedestrian', color='darkred')
    axes[2].bar(x + width/2, all_counts_df['cycle_fatal_counts'], width, label='Fatal Cyclist',    color='darkorange')
    axes[2].set_ylabel('Number of Fatal Crashes')
    axes[2].set_xlabel('Year')
    axes[2].set_xticks(xticks)
    axes[2].set_yticks([0, 1, 2])
    axes[2].grid(True)
    axes[2].legend(loc='upper left')

    plt.tight_layout()
    plt.savefig(OUT_DIR / 'crash_trends_subplots_bar.png')
    print("Saved crash_trends_subplots_bar.png")


if __name__ == '__main__':
    print("Loading crash data from database...")
    crash_df = load_crashes_from_db(DB_PATH, start_year=2015)
    print(f"Loaded {len(crash_df):,} rows ({crash_df['crash_year'].min()}–{crash_df['crash_year'].max()})")

    split_data_years(crash_df)
    print("Saved per-year CSVs to output/")

    all_counts_df = pd.DataFrame()
    for crash_type, criteria in CRASH_TYPES.items():
        filtered = filter_crashes(crash_df, **criteria) if criteria else crash_df
        all_counts_df = pd.concat([all_counts_df, get_counts(filtered, crash_type)], axis=1)

    all_counts_df = all_counts_df.fillna(0).astype(int)
    all_counts_df.to_csv(OUT_DIR / 'crash_counts_by_year.csv')
    print("Saved crash_counts_by_year.csv")

    plot_crashes_subplots_bar(all_counts_df)
    plot_crashes_over_time_annotate(all_counts_df)
