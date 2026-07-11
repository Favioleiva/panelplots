"""Descriptive fan charts for large panel datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from .io import save_figure
from .style import set_academic_style
from .transforms import apply_transform
from .utils import apply_time_axis, apply_y_axis, complete_time_grid, maybe_make_parent, normalize_time_column, resolve_time_frequency, validate_columns

DEFAULT_DECILE_COLORS = [
    "#313695",  # p00-p10 deep blue
    "#4575B4",  # p10-p20 blue
    "#74ADD1",  # p20-p30 light blue
    "#ABD9E9",  # p30-p40 pale blue
    "#FFFFBF",  # p40-p50 yellow midpoint
    "#FEE090",  # p50-p60 warm yellow
    "#FDAE61",  # p60-p70 orange
    "#F46D43",  # p70-p80 warm orange/red
    "#D73027",  # p80-p90 red
    "#A50026",  # p90-p100 deep red
]


def _quantile_name(q: float) -> str:
    return f"q{int(round(q * 100)):02d}"


def compute_quantile_fan(
    df: pd.DataFrame,
    *,
    y: str,
    time: str,
    unit: str | None = None,
    transform: str | Callable[[pd.Series], pd.Series] | None = None,
    transform_scale: float = 1000.0,
    quantiles: Sequence[float] | None = None,
    complete_time_index: bool = True,
    freq: str | None = "auto",
) -> pd.DataFrame:
    """Compute cross-sectional quantiles by time period for a panel dataset."""

    if quantiles is None:
        quantiles = [i / 10 for i in range(0, 11)]

    quantiles = list(quantiles)
    if min(quantiles) < 0 or max(quantiles) > 1:
        raise ValueError("Quantiles must be expressed between 0 and 1.")

    required = [time, y]
    if unit is not None:
        required.append(unit)
    validate_columns(df, required)

    work = df[required].copy()
    work[time] = normalize_time_column(work[time], time_frequency=freq)
    work[y] = pd.to_numeric(work[y], errors="coerce")
    work["_panelplots_y"] = apply_transform(work[y], transform, scale=transform_scale)

    q_stats = work.groupby(time)["_panelplots_y"].quantile(quantiles).unstack()
    q_stats.columns = [_quantile_name(q) for q in quantiles]
    q_stats = q_stats.reset_index()

    if unit is None:
        daily_summary = (
            work.groupby(time, as_index=False)
            .agg(n_valid_observations=("_panelplots_y", lambda x: int(x.notna().sum())))
        )
    else:
        daily_summary = (
            work.groupby(time, as_index=False)
            .agg(n_valid_units=("_panelplots_y", lambda x: int(x.notna().sum())))
        )

    fan = q_stats.merge(daily_summary, on=time, how="outer").sort_values(time)

    if complete_time_index and not fan.empty:
        fan = complete_time_grid(fan, time_col=time, freq=freq)
    else:
        fan.attrs["time_frequency"] = resolve_time_frequency(fan[time], freq)

    return fan


def plot_fanchart(
    df: pd.DataFrame,
    *,
    y: str,
    time: str,
    unit: str | None = None,
    transform: str | Callable[[pd.Series], pd.Series] | None = None,
    transform_scale: float = 1000.0,
    quantiles: Sequence[float] | None = None,
    band_colors: Sequence[str] | None = None,
    band_alpha: float = 0.66,
    reference_quantiles: Sequence[tuple[float, str, float]] | None = None,
    complete_time_index: bool = True,
    freq: str | None = "auto",
    expected_units: int | None = None,
    figsize: tuple[float, float] = (16, 9),
    y_label: str = "Log\nNTL",
    x_label: str = "Year",
    title: str | None = None,
    y_limits: tuple[float, float] | None = None,
    y_tick_step: float | None = None,
    year_tick_base: int = 2,
    grid: bool = True,
    legend: bool = True,
    output_path: str | Path | None = None,
    output_formats: list[str] | None = None,
    stats_output_path: str | Path | None = None,
    dpi: int = 300,
    ax: plt.Axes | None = None,
    apply_style: bool = True,
    return_data: bool = False,
):
    """Create a descriptive fan chart from cross-sectional quantile bands.

    The default configuration creates adjacent decile bands, matching the Peru
    Black Marble example: p00-p10, p10-p20, ..., p90-p100.
    """

    if quantiles is None:
        quantiles = [i / 10 for i in range(0, 11)]

    quantiles = list(quantiles)
    q_names = [_quantile_name(q) for q in quantiles]
    bands = list(zip(q_names[:-1], q_names[1:]))

    if band_colors is None:
        if len(bands) == 10:
            band_colors = DEFAULT_DECILE_COLORS
        else:
            cmap = plt.get_cmap("RdYlBu_r")
            band_colors = [cmap(v) for v in np.linspace(0.05, 0.95, len(bands))]

    if len(band_colors) < len(bands):
        raise ValueError("band_colors must contain at least one color per quantile band.")

    if apply_style:
        set_academic_style()

    validate_columns(df, [time, y] + ([unit] if unit is not None else []))

    if expected_units is not None and unit is not None:
        n_units = df[unit].astype(str).nunique()
        if n_units != expected_units:
            print(
                f"WARNING: expected {expected_units:,} unique units but found {n_units:,}."
            )

    fan = compute_quantile_fan(
        df,
        y=y,
        time=time,
        unit=unit,
        transform=transform,
        transform_scale=transform_scale,
        quantiles=quantiles,
        complete_time_index=complete_time_index,
        freq=freq,
    )

    stats_path = maybe_make_parent(stats_output_path)
    if stats_path is not None:
        fan.to_csv(stats_path, index=False)

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    x = pd.to_datetime(fan[time])

    for i, ((lower_col, upper_col), color) in enumerate(zip(bands, band_colors)):
        mask = fan[[lower_col, upper_col]].notna().all(axis=1).to_numpy()
        ax.fill_between(
            x,
            fan[lower_col].to_numpy(dtype=float),
            fan[upper_col].to_numpy(dtype=float),
            where=mask,
            color=color,
            alpha=band_alpha,
            linewidth=0,
            zorder=1 + i,
        )

    if reference_quantiles is None and all(q in quantiles for q in [0.10, 0.50, 0.90]):
        reference_quantiles = [
            (0.10, "#313695", 0.30),
            (0.50, "#8C6D1F", 0.28),
            (0.90, "#A50026", 0.30),
        ]

    if reference_quantiles:
        for q, color, alpha in reference_quantiles:
            q_col = _quantile_name(q)
            if q_col in fan.columns:
                ax.plot(
                    x,
                    fan[q_col],
                    color=color,
                    linewidth=0.65,
                    alpha=alpha,
                    zorder=20,
                )

    if title:
        ax.set_title(title, fontsize=20, pad=14)

    ax.set_ylabel(y_label, fontsize=19, rotation=0, labelpad=58, va="center")
    ax.set_xlabel(x_label, fontsize=19, labelpad=12)

    if not fan.empty:
        ax.set_xlim(pd.to_datetime(fan[time]).min(), pd.to_datetime(fan[time]).max())

    apply_y_axis(ax, y_limits=y_limits, y_tick_step=y_tick_step)
    apply_time_axis(ax, freq=fan.attrs.get("time_frequency", resolve_time_frequency(fan[time], freq)), year_tick_base=year_tick_base)

    ax.tick_params(axis="x", labelsize=15, pad=8)
    ax.tick_params(axis="y", labelsize=15, pad=8)

    if grid:
        ax.grid(axis="y", alpha=0.22, linewidth=0.8)
        ax.grid(axis="x", which="major", alpha=0.10, linewidth=0.6)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.9)
        spine.set_color("#222222")

    if legend:
        legend_handles = []

        for i, ((lower_col, upper_col), color) in enumerate(
            zip(bands, band_colors),
            start=1,
        ):
            lower_q = int(round(quantiles[i - 1] * 100))
            upper_q = int(round(quantiles[i] * 100))

            legend_handles.append(
                Patch(
                    facecolor=color,
                    edgecolor="none",
                    alpha=band_alpha,
                    label=f"D{i}: p{lower_q:02d}–p{upper_q:02d}",
                )
            )

        ax.legend(
            handles=legend_handles,
            loc="upper left",
            frameon=False,
            fontsize=12,
            ncol=5,
            columnspacing=1.2,
            handlelength=1.5,
            handletextpad=0.5,
        )

    fig.tight_layout()

    saved_paths = []
    path = maybe_make_parent(output_path)
    if path is not None:
        saved_paths = save_figure(fig, path, dpi=dpi, formats=output_formats)

    if return_data:
        return fig, ax, fan, saved_paths

    return fig, ax
