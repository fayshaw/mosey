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


def split_data_years(df, out_dir):
    """Write one CSV per year to out_dir/raw_crash_data_YYYY.csv."""
    out_dir = Path(out_dir)
    for year in range(int(df['crash_year'].min()), int(df['crash_year'].max()) + 1):
        df[df['crash_year'] == year].to_csv(
            OUT_DIR / f'raw_crash_data_{year}.csv', index=False
        )

