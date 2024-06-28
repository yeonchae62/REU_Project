from datetime import datetime
from make_plot import eda_plot
from eda import Eda, TIMEZONE
import matplotlib.pyplot as plt
from pathlib import Path

out = Eda.from_dir(
    Path('./split-eda/Data/EDA/Experiment1/2023-09-22/eda.csv'),
    Path('./split-eda/Data-Post-Processing/2023-09-22/Hao/'),
)

for i, (signals, info) in enumerate(out.analyzed_data):
    temp_date = datetime.fromtimestamp(out.raw_chunks[i].data[0][0] / 1_000_000, TIMEZONE)
    eda_plot('Electrodermal Activity (EDA), 2023-09-22 Hao, Type 1', temp_date, signals, info, [])
    plt.show()
exit()

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

# only extract the eda values, we know the sampling rate is 64 Hz
eda_values = [float(row[1]) for row in out.raw]
# signals, info = nk.eda_process(eda_values, sampling_rate=64/60)
signals, info = nk.eda_process(eda_values, sampling_rate=1/0.250026)
print(info.keys())
exit()
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
