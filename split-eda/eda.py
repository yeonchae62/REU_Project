import csv
from datetime import datetime
from eda_plot import eda_plot
import matplotlib.pyplot as plt
from eda_pre_process import PreProcessedEda, pre_process_raw_eda
import neurokit2 as nk
import os
from pathlib import Path
import pytz

TIMEZONE = pytz.timezone('America/Chicago')

def get_raw_min_max_timestamps(raw_chunks: list[PreProcessedEda]) -> tuple[datetime, datetime]:
    '''
    Returns the earliest and latest timestamps found in raw chunks of data, where each data point consists of a tuple containing the timestamp and the EDA value at that time.
    '''
    first_timestamp_micros = raw_chunks[0].data[0][0]
    last_timestamp_micros = raw_chunks[-1].data[-1][0]

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

def get_min_max_timestamps(data: dict[tuple[str, str, str], tuple[float, float]]) -> tuple[datetime, datetime]:
    '''
    Returns the earliest and latest timestamps found in a set containing multiple lists of data.
    '''
    earliest_micros = None
    latest_micros = None

    for data in data.values():
        first_timestamp_micros = data[0]
        last_timestamp_micros = data[-1]

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
    def __init__(
        self,
        raw_chunks: list[PreProcessedEda],
        analyzed_data: list[dict],
        group_times: dict[tuple[str, str, str], tuple[float, float]],
    ):
        self.raw_chunks = raw_chunks
        self.analyzed_data = analyzed_data
        self.group_times = group_times

    @staticmethod
    def process(
        raw: list[tuple[float, float]],
        group_times: dict[tuple[str, str, str], tuple[float, float]],
    ) -> 'Eda':
        '''
        Creates an Eda instance by processing the given raw data.
        '''
        raw_chunks = pre_process_raw_eda(raw)
        return Eda(
            raw_chunks,
            [(nk.eda_process([eda_value for _, eda_value in chunk.data], sampling_rate=chunk.sampling_rate)) for chunk in raw_chunks],
            group_times,
        )

    def chunk(self, group_pattern: tuple[str, str, str]) -> 'Eda':
        '''
        Returns a copy of this Eda instance's data, but with only thr groups that match the provided group pattern.

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

        for group, bounds in self.group_times.items():
            if pattern_match(group, group_pattern):
                result[group] = bounds

        return Eda(self.raw_chunks[:], self.analyzed_data[:], result)

    def get_raw_min_max_timestamps(self) -> tuple[datetime, datetime]:
        '''
        Returns the earliest and latest timestamps found in the raw data. This will not account for any data segmentation.
        '''
        return get_raw_min_max_timestamps(self.raw_chunks)

    def get_min_max_timestamps(self) -> tuple[datetime, datetime]:
        '''
        Returns the earliest and latest timestamps found in all groups of data.
        '''
        return get_min_max_timestamps(self.group_times)

    def plot(self, title: str, labeled_regions: list[tuple[float, float, str]] = []):
        '''
        Plots the chunks of analyzed data on one graph.
        '''
        eda_plot(title, self.raw_chunks, self.analyzed_data, labeled_regions)
        plt.show()

    @staticmethod
    def from_dir(raw_path: Path, start_dir: Path) -> 'Eda':
        '''
        Creates an Eda instance from `eda.csv` files found by walking the given starting directory.
        '''
        def process_raw(raw_path: Path) -> list[tuple[float, float]]:
            '''
            Returns a list contaning the data found in the given `eda.csv` file.
            '''
            with open(raw_path, 'r') as file:
                reader = csv.reader(file)

                # skip header
                next(reader)

                return [(
                    float(line[0]), # timestamp
                    float(line[1]), # eda
                ) for line in reader]

        def process_group_file(eda_path: Path) -> tuple[tuple[str, str, str], tuple[float, float]]:
            '''
            Determines the groups of this `eda.csv` file (e.g., HMD + fdump + trial 1) and the start and end time this group was recorded.
            '''
            parts = eda_path.parts
            groups = parts[-4], parts[-3], parts[-2]

            with open(eda_path, 'r') as file:
                reader = csv.reader(file)

                # skip header
                next(reader)

                data = list(reader)
                return (groups, (float(data[0][0]), float(data[-1][0])))

        group_times = {}
        for root, _, files in os.walk(start_dir):
            for file in files:
                if file == 'eda.csv':
                    (groups, result) = process_group_file(Path(os.path.join(root, file)))
                    group_times[groups] = result
        return Eda.process(process_raw(raw_path), group_times)
