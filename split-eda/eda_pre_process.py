import math

class PreProcessedEda:
    '''
    A pre-processed invidiual EDA data chunk. This includes the data itself, as well as the determined sampling rate, found using the average time between data points.
    '''
    def __init__(self, data: list[tuple[float, float]], sampling_rate_hz: float):
        self.data = data
        self.sampling_rate = sampling_rate_hz

    @staticmethod
    def from_raw(raw: list[tuple[float, float]]) -> 'PreProcessedEda':
        '''
        Creates a PreProcessedEda object from raw data, determining the sampling rate by averaging the time between data points.
        '''
        gap_sizes = [raw[i + 1][0] - raw[i][0] for i in range(len(raw) - 1)]
        average_time_in_micros = sum(gap_sizes) / len(gap_sizes)
        return PreProcessedEda(raw, 1_000_000 / average_time_in_micros)

    def __copy__(self) -> 'PreProcessedEda':
        return PreProcessedEda(self.data[:], self.sampling_rate)

    def __repr__(self) -> str:
        return f'PreProcessedEda(data={self.data}, sampling_rate={self.sampling_rate})'

    def __str__(self) -> str:
        return f'PreProcessedEda(data=(len={len(self.data)}), sampling_rate={self.sampling_rate} Hz)'

def pre_process_raw_eda(raw: list[tuple[float, float]]) -> list[PreProcessedEda]:
    '''
    Breaks the given raw data into chunks based on the presence of "large" gaps in the timestamps.

    A gap between two data points is "large" if the time between them is greater than 3 standard deviations above the average time between data points.
    '''
    # compute the gap sizes for each data point
    # gap_sizes[i] = raw[i + 1][0] - raw[i][0]
    gap_sizes = [raw[i + 1][0] - raw[i][0] for i in range(len(raw) - 1)]
    average_time_in_micros = sum(gap_sizes) / len(gap_sizes)
    sum_of_squared_diffs = sum((x - average_time_in_micros) ** 2 for x in gap_sizes)
    stddev = math.sqrt(sum_of_squared_diffs / len(gap_sizes))

    def is_large_gap(diff: float) -> bool:
        return diff > average_time_in_micros + 3 * stddev

    # locate the indices of the large gaps
    # note that found indices point at the data point that immediately precedes the large gap
    large_gaps = [i for i, diff in enumerate(gap_sizes) if is_large_gap(diff)]

    # break the data into chunks based on the large gaps
    chunks = []
    start = 0

    for gap in large_gaps:
        chunks.append(PreProcessedEda.from_raw(raw[start:gap + 1]))
        start = gap + 1

    chunks.append(PreProcessedEda.from_raw(raw[start:]))
    return chunks
