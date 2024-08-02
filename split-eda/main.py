from datetime import datetime
from eda import Eda, TIMEZONE
import matplotlib.pyplot as plt
from pathlib import Path

def to_micros(dt: datetime) -> float:
    return dt.timestamp() * 1_000_000

out = Eda.from_dir(
    Path('./split-eda/Data/EDA/Experiment2/2023-09-15/eda.csv'),
    Path('./split-eda/Data-Post-Processing/Experiment2/2023-09-15/baseline'),
    2,
)

print(out.get_raw_min_max_timestamps())

# draw visualization type 1

def type_1(title: str):
    continuous_chunk = out.chunk(('continuous', '*'))
    discrete_chunk = out.chunk(('discrete', '*'))
    mv1_chunk = out.chunk(('mv1', '*'))
    mv2_chunk = out.chunk(('mv2', '*'))
    none_chunk = out.chunk(('none', '*'))

    continuous_bounds = continuous_chunk.get_min_max_timestamps()
    discrete_bounds = discrete_chunk.get_min_max_timestamps()
    mv1_bounds = mv1_chunk.get_min_max_timestamps()
    mv2_bounds = mv2_chunk.get_min_max_timestamps()
    none_bounds = none_chunk.get_min_max_timestamps()

    # convert datetime.timestamp() to microseconds
    intervals = [
        (to_micros(continuous_bounds[0]), to_micros(continuous_bounds[1]), 'Continuous'),
        (to_micros(discrete_bounds[0]), to_micros(discrete_bounds[1]), 'Discrete'),
        (to_micros(mv1_bounds[0]), to_micros(mv1_bounds[1]), 'mv1'),
        (to_micros(mv2_bounds[0]), to_micros(mv2_bounds[1]), 'mv2'),
        (to_micros(none_bounds[0]), to_micros(none_bounds[1]), 'None'),
    ]

    out.plot(title, intervals)

    return continuous_chunk, discrete_chunk, mv1_chunk, mv2_chunk, none_chunk

continuous_part, discrete_part, mv1_part, mv2_part, none_part = type_1('Electrodermal Activity (EDA), 2023-09-15, Type 1')
