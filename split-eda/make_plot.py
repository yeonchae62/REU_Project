# -*- coding: utf-8 -*-
from warnings import warn

from datetime import datetime, timedelta
import matplotlib.collections
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# from ..misc import NeuroKitWarning

def _eda_plot_ignored(ax, x_axis, labeled_regions):
    first = 0
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
    if first < x_axis[-1]:
        ax.axvspan(first, x_axis[-1], color='black', alpha=0.65, zorder=2)

def eda_plot(title, start_datetime, eda_signals, info, labeled_regions):
    '''**Visualize electrodermal activity (EDA) data**

    Must be followed by ``plt.show()`` to display the figure.

    Parameters
    ----------
    eda_signals : DataFrame
        DataFrame obtained from :func:`eda_process()`.
    info : dict
        The information Dict returned by ``eda_process()``. Defaults to ``None``.
    static : bool
        If True, a static plot will be generated with matplotlib.
        If False, an interactive plot will be generated with plotly.
        Defaults to True.

    Returns
    -------
    See :func:`.ecg_plot` for details on how to access the figure, modify the size and save it.

    Examples
    --------
    .. ipython:: python

      import neurokit2 as nk

      eda_signal = nk.eda_simulate(duration=30, scr_number=5, drift=0.1, noise=0, sampling_rate=250)
      eda_signals, info = nk.eda_process(eda_signal, sampling_rate=250)

      @savefig p_eda_plot1.png scale=100%
      nk.eda_plot(eda_signals, info)
      @suppress
      plt.close()

    See Also
    --------
    eda_process

    '''
    if info is None:
        warn(
            f'{info} dict not provided. Some information might be missing.'
            + ' Sampling rate will be set to 1000 Hz.',
            category=NeuroKitWarning,
        )

        info = {
            'sampling_rate': 1000,
        }

    # Determine peaks, onsets, and half recovery.
    peaks = np.where(eda_signals['SCR_Peaks'] == 1)[0]
    onsets = np.where(eda_signals['SCR_Onsets'] == 1)[0]
    half_recovery = np.where(eda_signals['SCR_Recovery'] == 1)[0]

    # clean peaks that do not have onsets
    if len(peaks) > len(onsets):
        peaks = peaks[1:]

    # Determine unit of x-axis.
    x_label = 'Time (seconds)'
    x_axis = np.linspace(0, len(eda_signals) / info['sampling_rate'], len(eda_signals))

    fig, axes = plt.subplots(nrows=3, ncols=1, sharex=True)
    ax0, ax1, ax2 = axes
    for ax in axes:
        # mdates.DateFormatter bizzarely interprets an input x-axis value as *days* since Unix epoch, instead of requiring the input to be datetime??
        # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        # this manual approach is a workaround
        def format_func(seconds, _):
            return (start_datetime + timedelta(seconds=seconds)).strftime('%Y-%m-%d %H:%M:%S')
        ax.xaxis.set_major_formatter(format_func)
        ax.tick_params(axis='x', rotation=25)

    fig.suptitle(title, fontweight='bold', x=0.5)
    last_ax = fig.get_axes()[-1]
    last_ax.set_xlabel(x_label)

    # Plot cleaned and raw electrodermal activity.
    ax0.set_title('Raw and Cleaned Signal')

    ax0.plot(x_axis, eda_signals['EDA_Raw'], color='#B0BEC5', label='Raw', zorder=1)
    ax0.plot(
        x_axis,
        eda_signals['EDA_Clean'],
        color='#9C27B0',
        label='Cleaned',
        linewidth=1.5,
        zorder=1,
    )
    ax0.legend(loc='upper right')

    if labeled_regions:
        _eda_plot_ignored(ax0, x_axis, labeled_regions)

    # Plot skin conductance response.
    ax1.set_title('Skin Conductance Response (SCR)')

    # Plot Phasic.
    ax1.plot(
        x_axis,
        eda_signals['EDA_Phasic'],
        color='#E91E63',
        label='Phasic Component',
        linewidth=1.5,
        zorder=1,
    )

    # Mark segments.
    risetime_coord, amplitude_coord, halfr_coord = _eda_plot_dashedsegments(
        eda_signals, ax1, x_axis, onsets, peaks, half_recovery
    )

    risetime = matplotlib.collections.LineCollection(
        risetime_coord, colors='#FFA726', linewidths=1, linestyle='dashed'
    )
    ax1.add_collection(risetime)

    amplitude = matplotlib.collections.LineCollection(
        amplitude_coord, colors='#1976D2', linewidths=1, linestyle='solid'
    )
    ax1.add_collection(amplitude)

    halfr = matplotlib.collections.LineCollection(
        halfr_coord, colors='#FDD835', linewidths=1, linestyle='dashed'
    )
    ax1.add_collection(halfr)
    ax1.legend(loc='upper right')

    if labeled_regions:
        _eda_plot_ignored(ax1, x_axis, labeled_regions)

    # Plot Tonic.
    ax2.set_title('Skin Conductance Level (SCL)')
    ax2.plot(
        x_axis,
        eda_signals['EDA_Tonic'],
        color='#673AB7',
        label='Tonic Component',
        linewidth=1.5,
    )
    ax2.legend(loc='upper right')

    if labeled_regions:
        _eda_plot_ignored(ax2, x_axis, labeled_regions)

# =============================================================================
# Internals
# =============================================================================
def _eda_plot_dashedsegments(
    eda_signals, ax, x_axis, onsets, peaks, half_recovery,
):
    # Mark onsets, peaks, and half-recovery.
    onset_x_values = x_axis[onsets]
    onset_y_values = eda_signals['EDA_Phasic'][onsets].values
    peak_x_values = x_axis[peaks]
    peak_y_values = eda_signals['EDA_Phasic'][peaks].values
    halfr_x_values = x_axis[half_recovery]
    halfr_y_values = eda_signals['EDA_Phasic'][half_recovery].values

    end_onset = pd.Series(
        eda_signals['EDA_Phasic'][onsets].values, eda_signals['EDA_Phasic'][peaks].index
    )

    risetime_coord = []
    amplitude_coord = []
    halfr_coord = []

    for i in range(len(onsets)):
        # Rise time.
        start = (onset_x_values[i], onset_y_values[i])
        end = (peak_x_values[i], onset_y_values[i])
        risetime_coord.append((start, end))

    for i in range(len(peaks)):
        # SCR Amplitude.
        start = (peak_x_values[i], onset_y_values[i])
        end = (peak_x_values[i], peak_y_values[i])
        amplitude_coord.append((start, end))

    for i in range(len(half_recovery)):
        # Half recovery.
        end = (halfr_x_values[i], halfr_y_values[i])
        peak_x_idx = np.where(peak_x_values < halfr_x_values[i])[0][-1]
        start = (peak_x_values[peak_x_idx], halfr_y_values[i])
        halfr_coord.append((start, end))

    # Plot with matplotlib.
    # Mark onsets, peaks, and half-recovery.
    ax.scatter(
        x_axis[onsets],
        eda_signals['EDA_Phasic'][onsets],
        color='#FFA726',
        label='SCR - Onsets',
        zorder=2,
    )
    ax.scatter(
        x_axis[peaks],
        eda_signals['EDA_Phasic'][peaks],
        color='#1976D2',
        label='SCR - Peaks',
        zorder=2,
    )
    ax.scatter(
        x_axis[half_recovery],
        eda_signals['EDA_Phasic'][half_recovery],
        color='#FDD835',
        label='SCR - Half recovery',
        zorder=2,
    )

    ax.scatter(x_axis[end_onset.index], end_onset.values, alpha=0)

    return risetime_coord, amplitude_coord, halfr_coord
