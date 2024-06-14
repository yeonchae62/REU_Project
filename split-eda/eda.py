import csv
from datetime import datetime
from make_plot import eda_plot
import matplotlib.pyplot as plt
import neurokit2 as nk
import os
from pathlib import Path
import pytz

TIMEZONE = pytz.timezone('America/Chicago')

class Eda:
    '''
    A wrapper around a set of `eda.csv` files and the paths to those files, providing tools to search and segment all given data at once.
    '''
    def __init__(self, data_set: dict[tuple[str, str, str], list[tuple[float, float]]]):
        self.data = data_set;

    def chunk(self, group_pattern: tuple[str, str, str]) -> 'Eda':
        '''
        Returns a wrapper over a subset of this Eda instance's data. The subset will include all groups that match the provided group pattern.

        A group pattern in this context is a tuple of strings used to verify the structure of a group. Each string within the pattern indicates what strings are valid in a potential group-to-be-matched. An example of a pattern is:

        `('HMD', 'fdump', '*')`

        This pattern will match any group whose first two components are 'HMD', and 'fdump'. The final component of the group can be anything, indicated by the wildcard '*'.
        '''
        def str_match(test: str, pattern: str) -> bool:
            '''
            Returns true if the given string matches the pattern.

            The pattern can contain at most one wildcard '*', indicating zero or more characters at its location.
            '''
            wildcard_pos = pattern.find('*')

            # if no wildcard, pattern must match string exactly
            if wildcard_pos == -1:
                return test == pattern

            # match pattern
            prefix = pattern[:wildcard_pos]
            suffix = pattern[wildcard_pos + 1:]

            if test.startswith(prefix) and test.endswith(suffix):
                return len(test) >= len(prefix) + len(suffix)

            return False

        def pattern_match(group: tuple[str, str, str], pattern: tuple[str, str, str]):
            '''
            Returns true if the given group matches the pattern, as specified in the documentation for `chunk`.
            '''
            for test, pat in zip(group, pattern):
                if not str_match(test, pat):
                    return False
            return True

        result = {}

        for group, data in self.data.items():
            if pattern_match(group, group_pattern):
                result[group] = data[:]

        return Eda(result)

    @staticmethod
    def from_dir(start_dir: Path) -> 'Eda':
        '''
        Creates an Eda instance from `eda.csv` files found by walking the given starting directory.
        '''
        def process_one(eda_path: Path) -> tuple[tuple[str, str, str], list[tuple[float, float]]]:
            '''
            Determines the groups of this `eda.csv` file (e.g., HMD + fdump + trial 1) and the data contained inside it.
            '''
            parts = eda_path.parts
            groups = parts[-4], parts[-3], parts[-2]

            data = []

            with open(eda_path, 'r') as file:
                reader = csv.reader(file)

                # skip header
                next(reader)

                for line in reader:
                    data.append((
                        float(line[0]), # timestamp
                        float(line[1]), # eda
                    ))

            return (groups, data)

        data = {}
        for root, _, files in os.walk(start_dir):
            for file in files:
                if file == 'eda.csv':
                    (groups, result) = process_one(Path(os.path.join(root, file)))
                    data[groups] = result
        return Eda(data)

out = Eda.from_dir(Path('./split-eda/Data-Post-Processing/2023-09-22/Hao/'))
exit()

def get_boundaries(dir: Path):
    '''
    Find the start and end times of the experiments that occurred in the given date / directory.
    '''

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
    # plot_eda('2023-09-22', [(eda_values, '#735a8f', 'EDA')], intervals)
    signals, info = nk.eda_process(eda_values, sampling_rate=64/60)
    eda_plot('Electrodermal Activity (EDA), 2023-09-22', first_datetime, signals, info, intervals)
    plt.show()
