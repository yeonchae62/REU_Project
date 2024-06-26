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

        return Eda(self.raw[:], result)

    def get_raw_min_max_timestamps(self) -> tuple[datetime, datetime]:
        '''
        Returns the earliest and latest timestamps found in the raw data. This will not account for any data segmentation.

        The return value will remain the same on all copies of this instance made by calling `chunk`.
        '''
        first_timestamp_micros = self.raw[0][0]
        last_timestamp_micros = self.raw[-1][0]

        return (
            datetime.fromtimestamp(first_timestamp_micros / 1_000_000, TIMEZONE),
            datetime.fromtimestamp(last_timestamp_micros / 1_000_000, TIMEZONE),
        )

    def get_min_max_timestamps(self) -> tuple[datetime, datetime]:
        '''
        Returns the earliest and latest timestamps found in the data.
        '''
        earliest_micros = None
        latest_micros = None

        for _, data in self.data.items():
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

bounds = out.get_raw_min_max_timestamps()
print(bounds)

slope_chunk = out.chunk(('*', 's*', '*'))
flat_chunk = out.chunk(('*', 'f*', '*'))

slope_bounds = slope_chunk.get_min_max_timestamps()
flat_bounds = flat_chunk.get_min_max_timestamps()
print(slope_bounds)
print(flat_bounds)

def get_secs(dt: datetime) -> float:
    return (dt - bounds[0]).total_seconds()

intervals = [
    (get_secs(slope_bounds[0]), get_secs(slope_bounds[1]), 'Slope'),
    (get_secs(flat_bounds[0]), get_secs(flat_bounds[1]), 'Flat'),
]

# only extract the eda values, we know the sampling rate is 64 Hz
eda_values = [float(row[1]) for row in out.raw]
signals, info = nk.eda_process(eda_values, sampling_rate=64/60)
eda_plot('Electrodermal Activity (EDA), 2023-09-22 Hao', bounds[0], signals, info, intervals)
plt.show()
