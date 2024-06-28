from eda_pre_process import PreProcessedEda

from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

def eda_plot(
    title: str,
    raw_chunks: list[PreProcessedEda],
    analyzed_data,
    labeled_regions: list[tuple[float, float, str]] = [],
):
    '''
    Visualize electrodermal activity, including the raw and cleaned signal, the skin conductance response (SCR), and the skin conductance level (SCL).

    Must be followed by `matplotlib.pyplot.show()` to display the figure.

    :param title: The title to display at the top of the figure.
    :param raw_chunks: Raw EDA chunks obtained from an `Eda` instance.
    :param analyzed_data: Tuple of analyzed EDA data; return value of `nk.eda_process()`.
    :param labeled_regions: List of tuples indicating labeled regions to be ignored. Each tuple contains the start and end timestamps of the region, as well as a label to display on the plot.
    '''
    def legend_deduplicated(ax, *args, **kwargs):
        '''
        Deduplicate legend entries that can occur when multiple chunks are plotted.
        '''
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), *args, **kwargs)

    def plot_ignored_region(
        ax,
        bounds: tuple[float, float],
        labeled_regions: list[tuple[float, float, str]],
    ):
        '''
        Mark the labeled regions with dark rectangles, indicating that they should be ignored.
        '''
        # sort the labeled regions by start time
        # if they aren't sorted, the rectangles will get drawn in a weird order
        labeled_regions = labeled_regions[:]
        labeled_regions.sort(key=lambda region: region[0])

        first = bounds[0]
        for region in labeled_regions:
            start, end, label = region
            if start > first:
                # draw ignored rectangle
                ax.axvspan(first, start, color='black', alpha=0.65, zorder=2)
                first = end

            # draw labeled rectangle
            ax.text((start + end) / 2, ax.get_ylim()[0], label, ha='center', va='bottom', color='black', fontsize=10, fontweight='bold', zorder=3)
            ax.text(start, ax.get_ylim()[0], f'{int(start)}', ha='center', va='top', color='black', fontsize=8, zorder=3)
            ax.text(end, ax.get_ylim()[0], f'{int(end)}', ha='center', va='top', color='black', fontsize=8, zorder=3)

        # ignore the rest of the data
        if first < bounds[-1]:
            ax.axvspan(first, bounds[-1], color='black', alpha=0.65, zorder=2)

    time_bounds = (
        raw_chunks[0].data[0][0],
        raw_chunks[-1].data[-1][0],
    )

    fig, axes = plt.subplots(nrows=3, ncols=1, sharex=True)
    ax0, ax1, ax2 = axes
    for ax in axes:
        # mdates.DateFormatter bizzarely interprets an input x-axis value as *days* since Unix epoch, instead of requiring the input to be datetime??
        # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        # this manual approach is a workaround
        def format_func(microseconds, _):
            return datetime.fromtimestamp(microseconds / 1_000_000).strftime('%Y-%m-%d %H:%M:%S')
        ax.xaxis.set_major_formatter(format_func)
        ax.tick_params(axis='x', rotation=25)

    fig.suptitle(title, fontweight='bold', x=0.5)
    last_ax = fig.get_axes()[-1]
    last_ax.set_xlabel('Time (seconds)')

    # plot both cleaned and raw electrodermal activity in top subplot
    ax0.set_title('Raw and Cleaned Signal')

    for i, analyzed_chunk in enumerate(analyzed_data):
        x_axis = [timestamp_micros for timestamp_micros, _ in raw_chunks[i].data]
        ax0.plot(x_axis, analyzed_chunk[0]['EDA_Raw'], color='#B0BEC5', label='Raw', zorder=1)
        ax0.plot(
            x_axis,
            analyzed_chunk[0]['EDA_Clean'],
            color='#9C27B0',
            label='Cleaned',
            linewidth=1.5,
            zorder=1,
        )

    # deduplicate legend entries that can occur when multiple chunks are plotted
    legend_deduplicated(ax0, loc='upper right')

    if labeled_regions:
        plot_ignored_region(ax0, time_bounds, labeled_regions)

    # plot skin conductance response on middle subplot
    ax1.set_title('Skin Conductance Response (SCR)')

    # plot phasic component
    for i, analyzed_chunk in enumerate(analyzed_data):
        x_axis = [timestamp_micros for timestamp_micros, _ in raw_chunks[i].data]
        ax1.plot(x_axis, analyzed_chunk[0]['EDA_Phasic'], color='#E91E63', label='Phasic Component', linewidth=1.5)

    # plot SCR features
    # rise time (onset to peak)
    # amplitude (peak)
    # half recovery (peak to half recovery)
    for i, analyzed_chunk in enumerate(analyzed_data):
        x_axis = np.array([timestamp_micros for timestamp_micros, _ in raw_chunks[i].data])

        # indices into the associated x-axis time where the SCR features occur
        onset_indices = analyzed_chunk[1]['SCR_Onsets']
        peak_indices = analyzed_chunk[1]['SCR_Peaks']

        # this chunk bizzarely holds floats??, which can't be used as indices
        # and it also has `nan` values that weren't filtered out??
        half_recovery_indices = analyzed_chunk[1]['SCR_Recovery']
        half_recovery_indices = half_recovery_indices[~np.isnan(half_recovery_indices)].astype(int)

        # mark onsets, peaks, and half-recovery
        ax1.scatter(
            x_axis[onset_indices],
            analyzed_chunk[0]['EDA_Phasic'][onset_indices],
            color='#FFA726',
            label='SCR - Onsets',
            zorder=2,
        )

        ax1.scatter(
            x_axis[peak_indices],
            analyzed_chunk[0]['EDA_Phasic'][peak_indices],
            color='#1976D2',
            label='SCR - Peaks',
            zorder=2,
        )

        ax1.scatter(
            x_axis[half_recovery_indices],
            analyzed_chunk[0]['EDA_Phasic'][half_recovery_indices],
            color='#FDD835',
            label='SCR - Half recovery',
            zorder=2,
        )

    legend_deduplicated(ax1, loc='upper right')

    if labeled_regions:
        plot_ignored_region(ax1, time_bounds, labeled_regions)

    # plot tonic component in bottom subplot
    ax2.set_title('Skin Conductance Level (SCL)')

    for i, analyzed_chunk in enumerate(analyzed_data):
        x_axis = [timestamp_micros for timestamp_micros, _ in raw_chunks[i].data]
        ax2.plot(x_axis, analyzed_chunk[0]['EDA_Tonic'], color='#673AB7', label='Tonic Component', linewidth=1.5)

    legend_deduplicated(ax2, loc='upper right')

    if labeled_regions:
        plot_ignored_region(ax2, time_bounds, labeled_regions)
