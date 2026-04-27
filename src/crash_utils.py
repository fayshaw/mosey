import re
import pandas as pd
from pathlib import Path
from src.constants import OUT_DIR

def parse_crash_dates(df, col='crash_date'):
    """Parse crash_date strings (YYYY-MM-DD) to datetime. Returns df with new column."""
    df = df.copy()
    df[col] = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
    return df


def get_counts(df, name='crash_counts'):
    """Return crash counts per year as a named Series, sorted by year."""
    return df['crash_year'].value_counts().sort_index().rename(name)


_ABBREV = {'STREET': 'ST', 'AVENUE': 'AVE', 'ROAD': 'RD', 'DRIVE': 'DR',
           'BOULEVARD': 'BLVD', 'PLACE': 'PL', 'COURT': 'CT', 'LANE': 'LN'}

def _clean_street(s):
    """Strip route numbers and directional suffixes from a MassDOT street name string."""
    if not s or not isinstance(s, str):
        return ''
    s = re.split(r'\s+Rte\b', s.strip())[0]
    s = re.sub(r'\s+[NSEW]\s*$', '', s).strip()
    return s.title()


def _norm(s):
    """Normalize a street name for comparison: uppercase, expand/collapse abbreviations."""
    if not s:
        return ''
    s = s.upper().strip()
    for full, abbr in _ABBREV.items():
        s = re.sub(r'\b' + abbr + r'\b', full, s)
    return re.sub(r'\s+', '', s)  # remove spaces for fuzzy match


def top_intersections(df, n=5, event_types=None):
    """
    Find the top N intersections by crash count for vulnerable road users.

    Clusters crashes by rounding lat/lon to 3 decimal places (~100m radius),
    which collapses the many name variants MassDOT uses for the same intersection.

    Parameters
    ----------
    df           : crash DataFrame loaded from the database (must include
                   latitude, longitude, first_harmful_event, street_name_linked_rd,
                   near_intersection, crash_year columns)
    n            : number of top intersections to return (default 5)
    event_types  : list of first_harmful_event values to include
                   (default: pedestrian + cyclist)

    Returns
    -------
    DataFrame with columns: rank, intersection, crashes, ped_crashes,
                             bike_crashes, lat, lon, years_active
    """
    if event_types is None:
        event_types = ['Collision with pedestrian', 'Collision with cyclist']

    vuln = df[
        df['first_harmful_event'].isin(event_types) &
        df['latitude'].notna() &
        df['longitude'].notna()
    ].copy()

    # Round to 3 decimal places (~100m) to cluster nearby crashes at the same intersection
    vuln['lat_r'] = vuln['latitude'].round(3)
    vuln['lon_r'] = vuln['longitude'].round(3)

    # Label each cluster with the most common clean street name pair
    def best_label(cluster):
        main  = cluster['street_name_linked_rd'].dropna()
        cross = cluster['near_intersection'].dropna()
        main_name  = _clean_street(main.mode().iloc[0])  if len(main)  > 0 else ''
        cross_name = _clean_street(cross.mode().iloc[0]) if len(cross) > 0 else ''

        # If near_intersection is empty or matches main, try parsing the roadway column.
        # Many roadway values are formatted "STREET A / STREET B" — restrict to those
        # entries that contain a "/" so we don't pick single-street values as the mode.
        if not cross_name or _norm(cross_name) == _norm(main_name):
            roadway_vals = cluster['roadway'].dropna()
            intersection_roadways = roadway_vals[roadway_vals.str.contains('/')]
            if len(intersection_roadways) > 0:
                most_common = intersection_roadways.mode().iloc[0]
                parts = [_clean_street(p) for p in most_common.split('/')]
                parts = [p for p in parts if p and _norm(p) != _norm(main_name)]
                if parts:
                    cross_name = parts[0]

        if main_name and cross_name and main_name != cross_name:
            return f"{main_name} & {cross_name}"
        return main_name or cross_name or 'Unknown'

    # Count all crashes, pedestrian crashes, and cyclist crashes per cluster
    rows = []
    for (lat_r, lon_r), cluster in vuln.groupby(['lat_r', 'lon_r']):
        rows.append({
            'lat_r':        lat_r,
            'lon_r':        lon_r,
            'intersection': best_label(cluster),
            'crashes':      len(cluster),
            'ped_crashes':  (cluster['first_harmful_event'] == 'Collision with pedestrian').sum(),
            'bike_crashes': (cluster['first_harmful_event'] == 'Collision with cyclist').sum(),
            'lat':          cluster['latitude'].mean(),
            'lon':          cluster['longitude'].mean(),
            'years_active': f"{int(cluster['crash_year'].min())}–{int(cluster['crash_year'].max())}",
        })

    counts = (
        pd.DataFrame(rows)
        .sort_values('crashes', ascending=False)
        .head(n)
        .reset_index(drop=True)
    )
    counts.insert(0, 'rank', range(1, len(counts) + 1))

    return counts[['rank', 'intersection', 'crashes', 'ped_crashes',
                   'bike_crashes', 'lat', 'lon', 'years_active']]


def split_data_years(df, out_dir):
    """Write one CSV per year to out_dir/raw_crash_data_YYYY.csv."""
    out_dir = Path(out_dir)
    for year in range(int(df['crash_year'].min()), int(df['crash_year'].max()) + 1):
        df[df['crash_year'] == year].to_csv(
            OUT_DIR / f'raw_crash_data_{year}.csv', index=False
        )

