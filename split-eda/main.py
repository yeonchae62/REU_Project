from datetime import datetime
from make_plot import eda_plot
from eda import Eda, TIMEZONE
import matplotlib.pyplot as plt
from pathlib import Path

out = Eda.from_dir(
    Path('./split-eda/Data/EDA/Experiment1/2023-09-22/eda.csv'),
    Path('./split-eda/Data-Post-Processing/2023-09-22/Hao/'),
)

bounds = out.get_raw_min_max_timestamps()
print(bounds)

# draw visualization type 1

slope_chunk = out.chunk(('*', 's*', '*'))
flat_chunk = out.chunk(('*', 'f*', '*'))

slope_bounds = slope_chunk.get_min_max_timestamps()
flat_bounds = flat_chunk.get_min_max_timestamps()

# convert datetime.timestamp() to microseconds
intervals = [
    (slope_bounds[0].timestamp() * 1_000_000, slope_bounds[1].timestamp() * 1_000_000, 'Slope'),
    (flat_bounds[0].timestamp() * 1_000_000, flat_bounds[1].timestamp() * 1_000_000, 'Flat'),
]

out.plot('Electrodermal Activity (EDA), 2023-09-22 Hao, Type 1', intervals)
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
