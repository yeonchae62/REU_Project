import csv
from datetime import datetime
import matplotlib.pyplot as plt
import os
from pathlib import Path
import pytz

def plot_eda(date: str, data, labeled_regions=None):
    plt.figure(figsize=(15, 3))
    for d in data:
        to_plot, color, label = d
        plt.plot(to_plot, color=color, label=label, zorder=1)

    plt.title(f'Electrodermal Activity (EDA), {date}', fontsize=14, fontweight='bold')
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Signal strength', fontsize=12)
    plt.legend()

    if labeled_regions:
        first = 0
        for region in labeled_regions:
            start, end, label = region
            if start > first:
                # draw ignored rectangle
                plt.axvspan(first, start, color='black', alpha=0.65, zorder=2)
                first = end

            # draw labeled rectangle
            plt.text((start + end) / 2, plt.ylim()[0], label, ha='center', va='bottom', color='black', fontsize=10, fontweight='bold', zorder=3)
            plt.text(start, plt.ylim()[0], f'{start}', ha='center', va='top', color='black', fontsize=8, zorder=3)
            plt.text(end, plt.ylim()[0], f'{end}', ha='center', va='top', color='black', fontsize=8, zorder=3)

        # ignore the rest of the data
        if first < len(data[0][0]):
            plt.axvspan(first, len(data[0][0]), color='black', alpha=0.65, zorder=2)

    plt.show()

# # Example usage with arbitrary data
# x = np.linspace(0, 100, 500)
# raw_data_1 = 1 + 0.5 * np.sin(0.1 * x) + 0.2 * np.random.randn(500)
# cleaned_data_1 = 1 + 0.5 * np.sin(0.1 * x)
#
# x = np.linspace(0, 120, 300)
# raw_data_2 = 1 + 0.5 * np.sin(0.1 * x) + 0.2 * np.random.randn(300)
# cleaned_data_2 = 1 + 0.5 * np.sin(0.1 * x)
#
# plot_eda([
#     (raw_data_1, '#735a8f', 'Flat - raw'),
#     (cleaned_data_1, '#7b00ff', 'Flat - cleaned'),
#     (raw_data_2, '#877f56', 'Slope - raw'),
#     (cleaned_data_2, '#e3bd00', 'Slope - cleaned')
# ], [
#     (20, 70, 'Flat'),
#     (90, 110, 'Slope'),
# ])

TIMEZONE = pytz.timezone('America/Chicago')

def get_boundaries(dir: Path):
    '''
    Find the start and end times of the experiments that occurred in the given date / directory.
    '''

    def get_csvs(start_dir: Path) -> list[Path]:
        '''
        Find all eda.csv files in the given directories.
        '''
        csvs = []
        for root, _, files in os.walk(start_dir):
            for file in files:
                if file == 'eda.csv':
                    csvs.append(Path(os.path.join(root, file)))
        return csvs

    def process_path(path: Path) -> tuple[str, str, str]:
        '''
        Given a path in the form '??/Data-Post-Processing/2023-09-06/HMD/fdump/1/eda.csv', extract the test type, environment, and trial number into a tuple.
        '''
        parts = path.parts
        return parts[-4], parts[-3], parts[-2]

    def get_timestamps(csvs: list[Path]) -> list[tuple[tuple[str, str, str], datetime, datetime]]:
        '''
        Extract the start and end times of the slope and flat experiments from the given csv files, by iterating over all csv files, extracting the first and last timestamps, and choosing the earliest and latest timestamps as the start and end times.
        '''
        out = []
        for path in csvs:
            first_timestamps = []
            last_timestamps = []

            with open(path, 'r') as file:
                reader = csv.reader(file)
                data = list(reader)

                first_timestamp_micros = float(data[1][0]) # skip the header row
                last_timestamp_micros = float(data[-1][0])

                first_timestamps.append(first_timestamp_micros)
                last_timestamps.append(last_timestamp_micros)

            first_timestamp = min(first_timestamps)
            last_timestamp = max(last_timestamps)

            first_datetime = datetime.fromtimestamp(first_timestamp / 1_000_000, TIMEZONE)
            last_datetime = datetime.fromtimestamp(last_timestamp / 1_000_000, TIMEZONE)

            out.append((process_path(path), first_datetime, last_datetime))

        return out

    return get_timestamps(get_csvs(dir))

def slope_flat_bounds(boundaries: list[tuple[tuple[str, str, str], datetime, datetime]]) -> dict[str, tuple[datetime, datetime]]:
    '''
    Given a list of boundaries in the form [(('HMD', 'fdump', '1'), datetime, datetime), ...], return the earliest slope start time and the latest flat end time.
    '''
    slope_start = None
    slope_end = None
    flat_start = None
    flat_end = None

    for boundary in boundaries:
        _, environment, _ = boundary[0]
        start, end = boundary[1], boundary[2]

        if environment.startswith('s'):
            if slope_start is None or start < slope_start:
                slope_start = start
            if slope_end is None or end > slope_end:
                slope_end = end
        elif environment.startswith('f'):
            if flat_start is None or start < flat_start:
                flat_start = start
            if flat_end is None or end > flat_end:
                flat_end = end

    return {
        'slope': (slope_start, slope_end),
        'flat': (flat_start, flat_end),
    }

# Example usage with real data
# NOTE: requires EDA and Data-Post-Processing directories to be present in the current working directory
with open('./EDA/2023-09-22/eda.csv', 'r') as file:
    reader = csv.reader(file)
    data = list(reader)

    print(len(data))

    first_timestamp_micros = int(data[1][0])
    first_datetime = datetime.fromtimestamp(first_timestamp_micros / 1_000_000, TIMEZONE)
    print(first_timestamp_micros)
    print(first_datetime)

    last_timestamp_micros = int(data[-1][0])
    last_datetime = datetime.fromtimestamp(last_timestamp_micros / 1_000_000, TIMEZONE)
    print(last_timestamp_micros)
    print(last_datetime)

    def get_secs(dt: datetime) -> float:
        return (dt - first_datetime).total_seconds()

    # this value must match len(data)
    print(get_secs(last_datetime))

    bounds = get_boundaries(Path('./Data-Post-Processing/2023-09-22/Hao/'))
    slope_flat = slope_flat_bounds(bounds)
    intervals = [
        (get_secs(slope_flat['slope'][0]), get_secs(slope_flat['slope'][1]), 'Slope'),
        (get_secs(slope_flat['flat'][0]), get_secs(slope_flat['flat'][1]), 'Flat'),
    ]
    print(intervals)

    # only extract the eda values, we know the sampling rate is 64 Hz
    eda_values = [float(row[1]) for row in data[1:]]
    plot_eda('2023-09-22', [(eda_values, '#735a8f', 'EDA')], intervals)
