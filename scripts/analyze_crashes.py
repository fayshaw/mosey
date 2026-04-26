import pandas as pd
import os
import matplotlib.pyplot as plt
# from matplotlib.ticker import FormatStrFormatter

DATA_DIR  = '../data_sources/'
OUT_DIR  = '../output/'
RAW_CRASH_FILE = 'Malden_crashes_2015-2025.csv'
CRASH_FILE_PATH = os.path.join(DATA_DIR, RAW_CRASH_FILE)

CRASH_TYPES = {
    'crash_counts': {},  # All crashes (no filter)
    'ped_counts': {'First Harmful Event': 'Collision with pedestrian'},
    'ped_fatal_counts': {'First Harmful Event': 'Collision with pedestrian', 'Crash Severity': 'Fatal injury'},
    'cycle_counts': {'First Harmful Event': 'Collision with cyclist'},
    'cycle_fatal_counts': {'First Harmful Event': 'Collision with cyclist', 'Crash Severity': 'Fatal injury'},
}

def load_data(file_path):
    raw_df = pd.read_csv(file_path, dtype={'Crash Year': 'Int32', 'Speed Limit': 'Int32'}, low_memory=False)

#  Warning: Could not infer format, so each element will be parsed individually, falling back to `dateutil`. To ensure parsing is consistent and as-expected, please specify a format.
#    raw_df = pd.read_csv(file_path, dtype={'Crash Year': 'Int32', 'Speed Limit': 'Int32'},
#                     parse_dates=['Crash Date'], low_memory=False) # add date format
    # raw_df['Crash Date'] = pd.to_datetime(raw_df['Crash Date'], format='%m/%d/%y', errors='coerce')
    return raw_df

def filter_crashes(df, **criteria):
    """Filter raw data based on criteria"""
    result = df
    for column, value in criteria.items():
        result = result[result[column] == value]
    return result

# TODO: clean the data and THEN split
def split_data_years(df):
    """Split raw data into years based on min and max years"""

    min_year = df['Crash Year'].min()
    max_year = df['Crash Year'].max()

    for year in range(int(min_year), int(max_year)+1):
        year_df = df[df['Crash Year'] == year]
        year_df.to_csv(os.path.join(OUT_DIR, 'raw_crash_data_{}.csv'.format(year)))

def get_counts(df, name='crash_counts'):
    counts = df['Crash Year'].value_counts().sort_index()
    return counts.rename(name)



def plot_crashes_over_time_annotate(all_stats_df, include_crashes=True, include_ped=True, include_cycle=True,
                           include_ped_fatal=False, include_cycle_fatal=False):
    """Plot crash trends with flexible category inclusion"""
    fig, ax = plt.subplots(figsize=(10, 5))

    columns = {
        'crash_counts': {'include': include_crashes, 'color': 'tab:blue', 'label': 'Total Car Crashes'},
        'ped_counts': {'include': include_ped, 'color': 'red', 'label': 'Crashes with Pedestrians'},
        'ped_fatal_counts': {'include': include_ped_fatal, 'color': 'darkred', 'label': 'Fatal Pedestrian Crashes',
                             'marker': 'x'},
        'cycle_counts': {'include': include_cycle, 'color': 'orange', 'label': 'Crashes with Cyclists'},
        'cycle_fatal_counts': {'include': include_cycle_fatal, 'color': 'darkorange', 'label': 'Fatal Cyclist Crashes',
                               'marker': 'x'},
    }

    for col, style in columns.items():
        if style['include'] and col in all_stats_df.columns:
            marker = style.get('marker', 'o')
            ax.plot(all_stats_df[col], f'{marker}-', color=style['color'], label=style['label'], linewidth=2)

    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Crashes')
    ax.set_title('Car Crashes in Malden')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'crash_trends_annotate.png'))


def plot_crashes_subplots(all_counts_df, include_ped=True, include_cycle=True):
    fig, axes = plt.subplots(2, 1, figsize=(8, 6))
    axes[0].set_title('Total Car Crashes')
    axes[0].plot(all_counts_df['crash_counts'], 'o-', label='Total Crashes', linewidth=2)
    axes[0].set_ylabel('Number of Crashes')
    axes[0].grid(True)
    axes[0].legend(loc='upper left')

    axes[1].set_title('Crashes with Pedestrians and Cyclists')
    axes[1].plot(all_counts_df['ped_counts'], 'o-', color='red', label='Crashes with pedestrians', linewidth=2)
    axes[1].plot(all_counts_df['cycle_counts'], '^-', color='orange', label='Crashes with cylcists', linewidth=2)
    axes[1].plot(all_counts_df['ped_fatal_counts'], 'x-', color='darkred', label='Fatal pedestrian crashes', linewidth=2)
    axes[1].plot(all_counts_df['cycle_fatal_counts'], 's-', color='darkorange', label='Fatal cyclist crashes', linewidth=2)
    axes[1].grid(True)
    axes[1].legend(loc='upper left')

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'crash_trends_subplots.png'))


def plot_crashes_over_time(all_stats_df, include_crashes=True, include_ped=True, include_cycle=True,
                           include_ped_fatal=False, include_cycle_fatal=False):
    """Plot crash trends with flexible category inclusion"""
    fig, ax = plt.subplots(figsize=(10, 5))

    columns = {
        'crash_counts': {'include': include_crashes, 'color': 'blue', 'label': 'Total Car Crashes'},
        'ped_counts': {'include': include_ped, 'color': 'red', 'label': 'Crashes with Pedestrians'},
        'ped_fatal_counts': {'include': include_ped_fatal, 'color': 'darkred', 'label': 'Fatal Pedestrian Crashes',
                             'marker': 'x'},
        'cycle_counts': {'include': include_cycle, 'color': 'orange', 'label': 'Crashes with Cyclists'},
        'cycle_fatal_counts': {'include': include_cycle_fatal, 'color': 'darkorange', 'label': 'Fatal Cyclist Crashes',
                               'marker': 'x'},
    }

    for col, style in columns.items():
        if style['include'] and col in all_stats_df.columns:
            marker = style.get('marker', 'o')
            ax.plot(all_stats_df[col], f'{marker}-', color=style['color'], label=style['label'], linewidth=2)

            # Add text annotations for fatal crashes (small values)
            if 'fatal' in col:
                for year, value in all_stats_df[col].items():
                    ax.text(year, value + 0.1, str(int(value)), ha='center', va='bottom', fontsize=8)

    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Crashes')
    ax.set_title('Car Crashes in Malden')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'crash_trends.png'))


def plot_crashes_subplots_bar(all_counts_df, include_ped=True, include_cycle=True):
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    xticks = all_counts_df.index

    # Total crashes
    axes[0].set_title('Total Car Crashes')
    axes[0].plot(all_counts_df['crash_counts'], 'o-', label='Total Crashes', linewidth=2)
    axes[0].set_xticks(xticks)

    axes[0].set_ylim(600, 1100)
    axes[0].set_ylabel('Number of Crashes')
    axes[0].grid(True)
    axes[0].legend(loc='upper left')

    # Pedestrian and cyclist crashes
    axes[1].set_title('Crashes with Pedestrians and Cyclists')
    axes[1].plot(all_counts_df['ped_counts'], 'o-', color='red', label='Pedestrian Crashes', linewidth=2)
    axes[1].plot(all_counts_df['cycle_counts'], '^-', color='orange', label='Cyclist Crashes', linewidth=2)
    axes[1].set_xticks(xticks)
    axes[1].set_ylabel('Number of Crashes')
    axes[1].grid(True)
    axes[1].legend(loc='upper left')

    # Fatal crashes (as bar chart for clarity)
    axes[2].set_title('Fatal Crashes with Pedestrians and Cyclists')
    x = all_counts_df.index
    width = 0.35
    axes[2].bar(x - width / 2, all_counts_df['ped_fatal_counts'], width, label='Fatal Pedestrian', color='darkred')
    axes[2].bar(x + width / 2, all_counts_df['cycle_fatal_counts'], width, label='Fatal Cyclist', color='darkorange')
    axes[2].set_ylabel('Number of Fatal Crashes')
    axes[2].set_xlabel('Year')
    axes[2].grid(True, axis='y')
    axes[2].set_xticks(xticks)
    axes[2].set_yticks([0, 1, 2])
    axes[2].grid(True)
    axes[2].legend(loc='upper left')

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'crash_trends_subplots_bar.png'))



if __name__ == '__main__':
    raw_df = load_data(CRASH_FILE_PATH)
    split_data_years(raw_df)

    all_counts_df = pd.DataFrame()
    for crash_type, criteria in CRASH_TYPES.items():
        filtered_df = filter_crashes(raw_df, **criteria) if criteria else raw_df
        crash_counts_df = get_counts(filtered_df, crash_type)
        all_counts_df = pd.concat([all_counts_df, crash_counts_df], axis=1)

    all_counts_df= all_counts_df.fillna(0)
    all_counts_df.to_csv(os.path.join(OUT_DIR, 'crash_counts_by_year.csv'))
    # plot_crashes_over_time(all_counts_df)
    # plot_crashes_subplots(all_counts_df)
    plot_crashes_subplots_bar(all_counts_df)
    plot_crashes_over_time_annotate(all_counts_df)
