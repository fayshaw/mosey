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

from src.constants import (DB_PATH, OUT_DIR, CRASH_COUNTS_CSV,
                           CRASH_SPATIAL_RANGE_PNG, CRASH_SPATIAL_YEAR_PNG)
from src.load_data import load_crashes_from_db, load_malden_boundary, load_malden_roads
from src.plot_counts import plot_crashes_over_time, plot_crashes_subplots_bar, plot_combined_crashes_subplots_bar
from src.crash_utils import get_counts, filter_crashes, split_data_years, top_intersections, is_ped_crash, is_cycle_crash
from src.plot_spatial import plot_crashes_spatial

if __name__ == '__main__':
    malden_gdf = load_malden_boundary()

    # ── Time-series counts (all Malden crashes, full date range) ──────────────
    print("Loading crash data from database...")

    start_year = 2015
    end_year = 2025

    crash_df = load_crashes_from_db(DB_PATH, start_year=start_year, end_year=end_year, malden_only=True)
    print(f"Loaded {len(crash_df):,} Malden crashes "
          f"({crash_df['crash_year'].min()}–{crash_df['crash_year'].max()})")

    ped_df   = crash_df[is_ped_crash(crash_df)]
    cycle_df = crash_df[is_cycle_crash(crash_df)]

    crash_subsets = {
        'crash_counts':       crash_df,
        'ped_counts':         ped_df,
        'ped_fatal_counts':   ped_df[ped_df['crash_severity'] == 'Fatal injury'],
        'cycle_counts':       cycle_df,
        'cycle_fatal_counts': cycle_df[cycle_df['crash_severity'] == 'Fatal injury'],
    }

    all_counts_df = pd.DataFrame()
    # Save individual years to CSV
    for crash_type, subset in crash_subsets.items():
        all_counts_df = pd.concat([all_counts_df, get_counts(subset, crash_type)], axis=1)

    all_counts_df = all_counts_df.fillna(0).astype(int)
    all_counts_df.to_csv(CRASH_COUNTS_CSV)
    print("Saved crash_counts_by_year.csv")

    plot_crashes_subplots_bar(all_counts_df, OUT_DIR)
    plot_crashes_over_time(all_counts_df, OUT_DIR)
    plot_combined_crashes_subplots_bar(all_counts_df, OUT_DIR)

    # ── Spatial map (recent years, Malden boundary only) ─────────────────────


    malden_roads = load_malden_roads()

    years = list(range(start_year, end_year))
#    years = [2021, 2022, 2023, 2024, 2025]
#    years = [2015, 2016, 2017, 2018, 2019]
    #min_year, max_year = min(years), max(years)
    map_df = load_crashes_from_db(DB_PATH, start_year=start_year, end_year=end_year, malden_only=True)

    plot_crashes_spatial(
        map_df, malden_gdf, malden_roads,
        title=f'Malden Car Crashes {start_year}-{end_year}',
        save_path=OUT_DIR / CRASH_SPATIAL_RANGE_PNG.format(start_year=start_year, end_year=end_year))

    for year in years:
        map_df = load_crashes_from_db(DB_PATH, start_year=year, end_year=year, malden_only=True)
        print(f"\nPlotting {len(map_df):,} crashes on the map for: {year}.")

        plot_crashes_spatial(
            map_df, malden_gdf, malden_roads,
            title=f'Malden Car Crashes {year}',
            save_path=OUT_DIR / CRASH_SPATIAL_YEAR_PNG.format(year=year)
        )


    # TODO: walk audit map — add when walk_audit.py pipeline is complete
    # plot_walk_audit_map(gdf_points, gdf_lines, malden_gdf, malden_roads, RATING_COLOR)
