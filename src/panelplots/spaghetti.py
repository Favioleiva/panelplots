"""Spaghetti plots for large panel datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects

from .io import save_figure
from .style import set_academic_style
from .transforms import apply_transform
from .utils import apply_time_axis, apply_y_axis, maybe_make_parent, normalize_time_column, resolve_time_frequency, validate_columns

def _per_unit(value, unit_id, name):
    """Resolve a scalar-or-dict styling parameter for a single unit."""
    if isinstance(value, dict):
        try:
            return value[unit_id]
        except KeyError:
            raise KeyError(
                f"unit {unit_id!r} missing from {name}. "
                f"Provide a value for every unit, or pass a scalar."
            ) from None
    return value

def _coerce(d):
    """Coerce mapping keys to str, matching the plotted unit ids."""
    return {str(k): v for k, v in d.items()} if isinstance(d, dict) else d

def plot_spaghetti(
    df: pd.DataFrame,
    *,
    y: str,
    time: str,
    unit: str,
    transform: str | Callable[[pd.Series], pd.Series] | None = None,
    transform_scale: float = 1000.0,
    time_frequency: str | None = "auto",
    y_plot_name: str | None = None,
    expected_units: int | None = None,
    max_units: int | None = None,
    random_state: int = 2026,
    color_by_mean: bool = True,
    unit_cmap: str = "plasma",
    unit_colors: dict | None = None,
    unit_alpha: float | dict = 0.10,
    unit_linewidth: float | dict = 0.55,
    mean_line: bool = True,
    mean_label: str | None = None,
    mean_color: str = "#C2185B",
    mean_linewidth: float = 3.6,
    mean_outline: bool = True,
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
    dpi: int = 300,
    ax: plt.Axes | None = None,
    apply_style: bool = True,
    return_data: bool = False,
):
    """Create a publication-ready spaghetti plot from a panel dataset.

    Parameters
    ----------
    df:
        Panel dataset in long format.
    y, time, unit:
        Column names for outcome, time, and unit identifier.
    transform:
        Optional transformation. Use ``"blackmarble_log_mean"`` or
        ``"log1p_scaled"`` for ``log(1 + transform_scale × y)``.
    expected_units:
        Optional validation warning if the panel does not contain this number of
        unique units.
    max_units:
        Optional random subsample of units. Use ``None`` to plot all units.
    unit_colors:
        Optional mapping ``{unit_id: color}``. When provided it overrides
        ``color_by_mean`` and ``unit_cmap``. Keys are coerced to ``str``.
        Raises ``KeyError`` if a plotted unit is absent from the mapping.
    unit_alpha, unit_linewidth:
        Scalar applied to all units, or a mapping ``{unit_id: value}``
        following the same rules as ``unit_colors``.
    output_path:
        Optional path to save the figure.
    return_data:
        If ``True``, return ``(fig, ax, plot_data, mean_series)``.
    """

    validate_columns(df, [unit, time, y])

    if apply_style:
        set_academic_style()

    y_plot = y_plot_name or (
        f"{y}_plot" if transform is None else f"{y}_{str(transform).replace(' ', '_')}"
    )

    plot_df = df[[unit, time, y]].copy()
    plot_df[unit] = plot_df[unit].astype(str)
    plot_df[time] = normalize_time_column(plot_df[time], time_frequency=time_frequency)
    plot_df[y] = pd.to_numeric(plot_df[y], errors="coerce")
    plot_df[y_plot] = apply_transform(plot_df[y], transform, scale=transform_scale)
    plot_df = plot_df.sort_values([unit, time]).reset_index(drop=True)

    n_units = plot_df[unit].nunique()
    if expected_units is not None and n_units != expected_units:
        print(
            f"WARNING: expected {expected_units:,} unique units but found {n_units:,}."
        )

    unit_ids = np.array(sorted(plot_df[unit].dropna().unique()))
    if max_units is not None and len(unit_ids) > max_units:
        rng = np.random.default_rng(random_state)
        selected_ids = rng.choice(unit_ids, size=max_units, replace=False)
        plot_df = plot_df[plot_df[unit].isin(selected_ids)].copy()
        unit_ids = np.array(sorted(plot_df[unit].dropna().unique()))

    mean_series = (
        plot_df.groupby(time, as_index=False)
        .agg(
            panel_mean=(y_plot, "mean"),
            n_valid_units=(y_plot, lambda x: int(x.notna().sum())),
        )
        .sort_values(time)
    )

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    unit_colors = _coerce(unit_colors)
    unit_alpha = _coerce(unit_alpha)
    unit_linewidth = _coerce(unit_linewidth)

    cmap = plt.get_cmap(unit_cmap)
    if color_by_mean:
        unit_order = (
            plot_df.groupby(unit)[y_plot]
            .mean()
            .sort_values()
            .index
            .tolist()
        )
    else:
        unit_order = sorted(unit_ids)

    palette_values = np.linspace(0.12, 0.92, max(len(unit_order), 1))
    color_map = {
        unit_id: cmap(value) for unit_id, value in zip(unit_order, palette_values)
    }

    for unit_id, group in plot_df.groupby(unit, sort=False):
        group = group.sort_values(time)
        if unit_colors is not None:
            color = _per_unit(unit_colors, unit_id, "unit_colors")
        else:
            color = color_map.get(unit_id, cmap(0.55))
        ax.plot(
            group[time],
            group[y_plot],
            color=color,
            linewidth=_per_unit(unit_linewidth, unit_id, "unit_linewidth"),
            alpha=_per_unit(unit_alpha, unit_id, "unit_alpha"),
            zorder=1,
            label=f"_unit_{unit_id}",
        )

    if mean_line:
        label = mean_label or f"Mean across {len(unit_ids):,} units"
        line, = ax.plot(
            mean_series[time],
            mean_series["panel_mean"],
            color=mean_color,
            linewidth=mean_linewidth,
            label=label,
            zorder=4,
        )
        if mean_outline:
            line.set_path_effects(
                [
                    path_effects.Stroke(linewidth=mean_linewidth + 1.8, foreground="white"),
                    path_effects.Normal(),
                ]
            )

    if title:
        ax.set_title(title, fontsize=20, pad=14)

    ax.set_ylabel(y_label, fontsize=19, rotation=0, labelpad=58, va="center")
    ax.set_xlabel(x_label, fontsize=19, labelpad=12)
    ax.set_xlim(plot_df[time].min(), plot_df[time].max())

    apply_y_axis(ax, y_limits=y_limits, y_tick_step=y_tick_step)
    apply_time_axis(ax, freq=resolve_time_frequency(plot_df[time], time_frequency), year_tick_base=year_tick_base)

    ax.tick_params(axis="x", labelsize=15, pad=8)
    ax.tick_params(axis="y", labelsize=15, pad=8)

    if grid:
        ax.grid(axis="y", alpha=0.25, linewidth=0.8)
        ax.grid(axis="x", which="major", alpha=0.12, linewidth=0.6)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if legend and mean_line:
        ax.legend(loc="upper left", frameon=False, fontsize=17)

    fig.tight_layout()

    saved_paths = []
    path = maybe_make_parent(output_path)
    if path is not None:
        saved_paths = save_figure(fig, path, dpi=dpi, formats=output_formats)

    if return_data:
        return fig, ax, plot_df, mean_series, saved_paths

    return fig, ax
