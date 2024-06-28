import csv
from datetime import datetime
from make_plot import eda_plot
import matplotlib.pyplot as plt
import neurokit2 as nk
import os
from pathlib import Path
import pytz

TIMEZONE = pytz.timezone('America/Chicago')

def get_min_max_timestamps(data: list[tuple[float, float]]) -> tuple[datetime, datetime]:
    '''
    Returns the earliest and latest timestamps found in one list of data, where each data point consists of a tuple containing the timestamp and the EDA value at that time.
    '''
    first_timestamp_micros = data[0][0]
    last_timestamp_micros = data[-1][0]

    return (
        datetime.fromtimestamp(first_timestamp_micros / 1_000_000, TIMEZONE),
        datetime.fromtimestamp(last_timestamp_micros / 1_000_000, TIMEZONE),
    )

def filter_by_timestamp_bounds(data: list[tuple[float, float]], bounds: tuple[datetime, datetime]) -> list[tuple[float, float]]:
    '''
    Filters the given list of data to the data points that lie within the timestamps indicated by the given bounds.

    The original list will not be modified.
    '''
    new_data = []

    for timestamp_micros, eda_value in data:
        dt = datetime.fromtimestamp(timestamp_micros / 1_000_000, TIMEZONE)
        if bounds[0] <= dt <= bounds[1]:
            new_data.append((timestamp_micros, eda_value))

    return new_data

def get_min_max_timestamps_many(data: dict[tuple[str, str, str], list[tuple[float, float]]]) -> tuple[datetime, datetime]:
    '''
    Returns the earliest and latest timestamps found in a set containing multiple lists of data.
    '''
    earliest_micros = None
    latest_micros = None

    for data in data.values():
        first_timestamp_micros = data[0][0]
        last_timestamp_micros = data[-1][0]

        if earliest_micros is None or first_timestamp_micros < earliest_micros:
            earliest_micros = first_timestamp_micros
        if latest_micros is None or last_timestamp_micros > latest_micros:
            latest_micros = last_timestamp_micros

    assert earliest_micros is not None
    assert latest_micros is not None
    return (
        datetime.fromtimestamp(earliest_micros / 1_000_000, TIMEZONE),
        datetime.fromtimestamp(latest_micros / 1_000_000, TIMEZONE),
    )

class Eda:
    '''
    A wrapper around a set of `eda.csv` files and the paths to those files, providing tools to search and segment all given data at once.
    '''
    def __init__(self, raw: list[tuple[float, float]], data_set: dict[tuple[str, str, str], list[tuple[float, float]]]):
        self.raw = raw
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

        new_data_bounds = get_min_max_timestamps_many(result)
        return Eda(filter_by_timestamp_bounds(self.raw, new_data_bounds), result)

    def get_raw_min_max_timestamps(self) -> tuple[datetime, datetime]:
        '''
        Returns the earliest and latest timestamps found in the raw data. This will not account for any data segmentation.
        '''
        return get_min_max_timestamps(self.raw)

    def get_min_max_timestamps(self) -> tuple[datetime, datetime]:
        '''
        Returns the earliest and latest timestamps found in the data.
        '''
        return get_min_max_timestamps_many(self.data)

    @staticmethod
    def from_dir(raw_path: Path, start_dir: Path) -> 'Eda':
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
        return Eda(process_one(raw_path)[1], data)

out = Eda.from_dir(
    Path('./split-eda/Data/EDA/Experiment1/2023-09-22/eda.csv'),
    Path('./split-eda/Data-Post-Processing/2023-09-22/Hao/'),
)

def get_secs(dt: datetime) -> float:
    return (dt - bounds[0]).total_seconds()

bounds = out.get_raw_min_max_timestamps()
print(bounds)

# draw visualization type 1

slope_chunk = out.chunk(('*', 's*', '*'))
flat_chunk = out.chunk(('*', 'f*', '*'))

slope_bounds = slope_chunk.get_min_max_timestamps()
flat_bounds = flat_chunk.get_min_max_timestamps()

intervals = [
    (get_secs(slope_bounds[0]), get_secs(slope_bounds[1]), 'Slope'),
    (get_secs(flat_bounds[0]), get_secs(flat_bounds[1]), 'Flat'),
]

# compute average time between each data point
total_time = bounds[1] - bounds[0]
total_secs = total_time.total_seconds()
print(total_time, total_secs)
expected_time_per_point = total_secs / len(out.raw)
print(f'Expected time per point: {expected_time_per_point} seconds')

# compute the actual time between each data point
actual_times = []
min_diff = None
max_diff = None
for i in range(1, len(out.raw)):
    diff = out.raw[i][0] - out.raw[i - 1][0]
    if diff > 500_000:
        print(f'Large gap detected: {diff / 1_000_000} seconds')
        print(f'Index: {i}')
        print(f'surrounding times:')
        for j in range(max(0, i - 3), min(len(out.raw), i + 3)):
            print(f'   {j}: {out.raw[j][0]}')
    actual_times.append(diff)

    if min_diff is None or diff < min_diff:
        min_diff = diff
    if max_diff is None or diff > max_diff:
        max_diff = diff

average_time_in_micros = sum(actual_times) / len(actual_times)
print(f'Average time between points: {average_time_in_micros / 1_000_000} seconds')
print(f'Minimum time between points: {min_diff / 1_000_000} seconds')
print(f'Maximum time between points: {max_diff / 1_000_000} seconds')
import math
stddev = math.sqrt(sum((x - average_time_in_micros) ** 2 for x in actual_times) / len(actual_times))
print(f'Standard deviation of time between points: {stddev / 1_000_000} seconds')

# only extract the eda values, we know the sampling rate is 64 Hz
eda_values = [float(row[1]) for row in out.raw]
# signals, info = nk.eda_process(eda_values, sampling_rate=64/60)
signals, info = nk.eda_process(eda_values, sampling_rate=1/0.250026)
eda_plot('Electrodermal Activity (EDA), 2023-09-22 Hao, Type 1', bounds[0], signals, info, intervals)
plt.show()
exit()
# draw visualization type 2

# TODO: do for flat and slope
slope_bounds = slope_chunk.get_raw_min_max_timestamps()
print(slope_bounds)
print(len(slope_chunk.raw))

single_chunk = slope_chunk.chunk(('single-view', '*', '*'))
multi_chunk = slope_chunk.chunk(('multiple-view', '*', '*'))
hmd_chunk = slope_chunk.chunk(('HMD', '*', '*'))

single_bounds = single_chunk.get_min_max_timestamps()
multi_bounds = multi_chunk.get_min_max_timestamps()
hmd_bounds = hmd_chunk.get_min_max_timestamps()

intervals = [
    (get_secs(single_bounds[0]), get_secs(single_bounds[1]), 'Single View'),
    (get_secs(multi_bounds[0]), get_secs(multi_bounds[1]), 'Multi View'),
    (get_secs(hmd_bounds[0]), get_secs(hmd_bounds[1]), 'HMD'),
]

eda_values = [float(row[0]) for row in slope_chunk.raw]
signals, info = nk.eda_process(eda_values, sampling_rate=4)
eda_plot('Electrodermal Activity (EDA), 2023-09-22 Hao, Type 2', slope_bounds[0], signals, info, intervals)
plt.show()
