from datetime import datetime
from eda import Eda, TIMEZONE
import matplotlib.pyplot as plt
from pathlib import Path

def to_micros(dt: datetime) -> float:
    return dt.timestamp() * 1_000_000

out = Eda.from_dir(
    Path('./split-eda/Data/EDA/Experiment1/2023-09-22/eda.csv'),
    Path('./split-eda/Data-Post-Processing/2023-09-22/Hao/'),
)

print(out.get_raw_min_max_timestamps())

# draw visualization type 1

def type_1(title: str):
    slope_chunk = out.chunk(('*', 's*', '*'))
    flat_chunk = out.chunk(('*', 'f*', '*'))

    slope_bounds = slope_chunk.get_min_max_timestamps()
    flat_bounds = flat_chunk.get_min_max_timestamps()

    # convert datetime.timestamp() to microseconds
    intervals = [
        (to_micros(slope_bounds[0]), to_micros(slope_bounds[1]), 'Slope'),
        (to_micros(flat_bounds[0]), to_micros(flat_bounds[1]), 'Flat'),
    ]

    out.plot(title, intervals)

    return slope_chunk, flat_chunk

slope_part, flat_part = type_1('Electrodermal Activity (EDA), 2023-09-22 Hao, Type 1')

# draw visualization type 2

def type_2(chunk, title: str):
    bounds = chunk.get_raw_min_max_timestamps()

    single_chunk = chunk.chunk(('single-view', '*', '*'))
    multi_chunk = chunk.chunk(('multiple-view', '*', '*'))
    hmd_chunk = chunk.chunk(('HMD', '*', '*'))

    single_bounds = single_chunk.get_min_max_timestamps()
    multi_bounds = multi_chunk.get_min_max_timestamps()
    hmd_bounds = hmd_chunk.get_min_max_timestamps()

    intervals = [
        (to_micros(single_bounds[0]), to_micros(single_bounds[1]), 'Single View'),
        (to_micros(multi_bounds[0]), to_micros(multi_bounds[1]), 'Multi View'),
        (to_micros(hmd_bounds[0]), to_micros(hmd_bounds[1]), 'HMD'),
    ]

    chunk.plot(title, intervals)

# TODO: still need to filter raw data by timestamp bounds
type_2(slope_part, 'Electrodermal Activity (EDA), 2023-09-22 Hao, Type 2 - Slope')
type_2(flat_part, 'Electrodermal Activity (EDA), 2023-09-22 Hao, Type 2 - Flat')
