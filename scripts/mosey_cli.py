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
Loaded from db/crashes.db (SQLite, 2015–present).

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
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.constants import DB_PATH, OUT_DIR
from src.load_data import load_crashes_from_db, load_malden_boundary, load_malden_roads
from src.plot_counts import plot_crashes_over_time, plot_crashes_subplots_bar
from src.filter_crashes import filter_crashes
from src.crash_utils import get_counts, split_data_years, top_intersections
from src.plot_spatial import plot_crashes_spatial

CRASH_TYPES = {
    'crash_counts':       {},
    'ped_counts':         {'first_harmful_event': 'Collision with pedestrian'},
    'ped_fatal_counts':   {'first_harmful_event': 'Collision with pedestrian',
                           'crash_severity': 'Fatal injury'},
    'cycle_counts':       {'first_harmful_event': 'Collision with cyclist'},
    'cycle_fatal_counts': {'first_harmful_event': 'Collision with cyclist',
                           'crash_severity': 'Fatal injury'},
}

if __name__ == '__main__':
    malden_gdf = load_malden_boundary()

    # ── Time-series counts (all Malden crashes, full date range) ──────────────
    print("Loading crash data from database...")
    crash_df = load_crashes_from_db(DB_PATH, start_year=2015, malden_only=True)
    print(f"Loaded {len(crash_df):,} Malden crashes "
          f"({crash_df['crash_year'].min()}–{crash_df['crash_year'].max()})")

    all_counts_df = pd.DataFrame()
    for crash_type, criteria in CRASH_TYPES.items():
        filtered = filter_crashes(crash_df, **criteria) if criteria else crash_df
        all_counts_df = pd.concat([all_counts_df, get_counts(filtered, crash_type)], axis=1)

    all_counts_df = all_counts_df.fillna(0).astype(int)
    all_counts_df.to_csv(OUT_DIR / 'crash_counts_by_year.csv')
    print("Saved crash_counts_by_year.csv")
    

    plot_crashes_subplots_bar(all_counts_df, OUT_DIR)


    # ── Spatial map (recent years, Malden boundary only) ─────────────────────

    """
    malden_roads = load_malden_roads()

    years = [2021, 2022, 2023, 2024, 2025]
    map_df = load_crashes_from_db(DB_PATH, start_year=min(years), end_year=max(years), malden_only=True)
    plot_crashes_spatial(
        map_df, malden_gdf, malden_roads,
        title=f'Malden Car Crashes 2021-2025',
        save_path=OUT_DIR / f'crashes_spatial_2021-2025.png')

    for year in years:
        map_df = load_crashes_from_db(DB_PATH, start_year=year, end_year=year, malden_only=True)
        print(f"\nPlotting {len(map_df):,} crashes on the map for: {year}.")

        plot_crashes_spatial(
            map_df, malden_gdf, malden_roads,
            title=f'Malden Car Crashes {year}',
            save_path=OUT_DIR / f'crashes_spatial_{year}.png'
        )
        """

    # TODO: walk audit map — add when walk_audit.py pipeline is complete
    # plot_walk_audit_map(gdf_points, gdf_lines, malden_gdf, malden_roads, RATING_COLOR)
