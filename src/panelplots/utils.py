"""Internal utilities for panel visualizations."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


TimeFrequency = str | None


def validate_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    """Raise a clear error if a required column is missing."""

    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _is_integer_like_numeric(series: pd.Series) -> bool:
    values = pd.to_numeric(series.dropna(), errors="coerce")
    if values.empty or values.isna().any():
        return False
    return bool(np.all(np.isclose(values, np.round(values))))


def _looks_like_year_numeric(series: pd.Series) -> bool:
    values = pd.to_numeric(series.dropna(), errors="coerce")
    if values.empty or values.isna().any():
        return False
    return bool(
        _is_integer_like_numeric(series)
        and values.between(1000, 3000).all()
    )


def _parse_year_numeric(series: pd.Series) -> pd.Series:
    out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    mask = series.notna()
    years = pd.to_numeric(series.loc[mask], errors="coerce").round().astype("Int64").astype(str)
    out.loc[mask] = pd.to_datetime(years + "-01-01", format="%Y-%m-%d", errors="coerce")
    return out


def _parse_year_strings(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    mask = text.notna() & text.str.fullmatch(r"\d{4}")
    out.loc[mask] = pd.to_datetime(text.loc[mask] + "-01-01", format="%Y-%m-%d", errors="coerce")
    return out


def _parse_month_strings(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip().str.replace("/", "-", regex=False)
    out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    mask = text.notna() & text.str.fullmatch(r"\d{4}-\d{1,2}")
    fixed = text.loc[mask].str.replace(r"^(\d{4})-(\d)$", r"\1-0\2", regex=True)
    out.loc[mask] = pd.to_datetime(fixed + "-01", format="%Y-%m-%d", errors="coerce")
    return out


def normalize_time_column(values: pd.Series, *, time_frequency: TimeFrequency = "auto") -> pd.Series:
    """Normalize common panel time encodings into pandas datetimes.

    The function is intentionally friendly to empirical panel data. It handles:

    - true datetime columns;
    - pandas Period columns, including monthly and annual periods;
    - numeric or string years such as ``2020`` or ``"2020"``;
    - month-year strings such as ``"2020-05"`` or ``"2020/05"``;
    - ordinary date strings such as ``"2020-05-17"``.

    Numeric values between 1000 and 3000 that are integer-like are treated as
    years, because ``pd.to_datetime(2020)`` would otherwise interpret the value
    as nanoseconds after 1970 instead of as the year 2020.
    """

    series = pd.Series(values).copy()

    if isinstance(series.dtype, pd.PeriodDtype):
        return series.dt.to_timestamp()

    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    requested = (time_frequency or "").upper()

    if requested in {"Y", "YS", "A", "AS", "YEAR", "ANNUAL", "YEARLY"}:
        if pd.api.types.is_numeric_dtype(series):
            return _parse_year_numeric(series)
        parsed = _parse_year_strings(series)
        fallback = pd.to_datetime(series, errors="coerce")
        return parsed.where(parsed.notna(), fallback)

    if requested in {"M", "MS", "MONTH", "MONTHLY"}:
        parsed = _parse_month_strings(series)
        fallback = pd.to_datetime(series, errors="coerce")
        return parsed.where(parsed.notna(), fallback)

    if pd.api.types.is_numeric_dtype(series) and _looks_like_year_numeric(series):
        return _parse_year_numeric(series)

    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        text = series.astype("string").str.strip()
        all_non_null = text.dropna()
        if not all_non_null.empty and all_non_null.str.fullmatch(r"\d{4}").all():
            return _parse_year_strings(series)
        if not all_non_null.empty and all_non_null.str.replace("/", "-", regex=False).str.fullmatch(r"\d{4}-\d{1,2}").all():
            return _parse_month_strings(series)

    return pd.to_datetime(series, errors="coerce")


def infer_time_frequency(times: pd.Series) -> str | None:
    """Infer a plotting/reindexing frequency from normalized datetimes.

    Returns a pandas offset alias such as ``"D"``, ``"MS"`` or ``"YS"``.
    The inference is deliberately conservative and optimized for long panels.
    """

    dt = pd.Series(pd.to_datetime(times, errors="coerce")).dropna().drop_duplicates().sort_values()
    if dt.empty:
        return None
    if len(dt) == 1:
        value = dt.iloc[0]
        if value.month == 1 and value.day == 1:
            return "YS"
        if value.day == 1:
            return "MS"
        return "D"

    # Regular indexes are best handled by pandas first.
    try:
        inferred = pd.infer_freq(pd.DatetimeIndex(dt))
    except ValueError:
        inferred = None
    if inferred:
        if inferred.startswith(("YS", "AS", "A", "Y")):
            return "YS"
        if inferred.startswith(("MS", "M")):
            return "MS"
        if inferred.startswith("D"):
            return "D"
        return inferred

    # Missing years/months are common in empirical datasets. Infer from anchors.
    if (dt.dt.month.eq(1) & dt.dt.day.eq(1)).all():
        return "YS"
    if dt.dt.day.eq(1).all():
        return "MS"

    deltas = dt.diff().dropna().dt.days
    if not deltas.empty:
        median_days = float(deltas.median())
        if 0.5 <= median_days <= 1.5:
            return "D"
        if 27 <= median_days <= 32:
            return "MS"
        if 360 <= median_days <= 370:
            return "YS"

    return None


def resolve_time_frequency(times: pd.Series, freq: str | None = "auto") -> str | None:
    """Return the effective pandas frequency alias for a normalized time column."""

    if freq is None:
        return None
    if isinstance(freq, str) and freq.lower() == "auto":
        return infer_time_frequency(times)
    return freq


def complete_time_grid(df: pd.DataFrame, *, time_col: str, freq: str | None = "auto") -> pd.DataFrame:
    """Reindex a time-indexed summary to a complete daily/monthly/yearly grid."""

    if df.empty:
        return df
    effective_freq = resolve_time_frequency(df[time_col], freq)
    if effective_freq is None:
        return df.sort_values(time_col).reset_index(drop=True)

    full_dates = pd.date_range(
        start=pd.to_datetime(df[time_col]).min(),
        end=pd.to_datetime(df[time_col]).max(),
        freq=effective_freq,
    )
    if len(full_dates) == 0:
        return df.sort_values(time_col).reset_index(drop=True)

    out = (
        df.set_index(time_col)
        .reindex(full_dates)
        .rename_axis(time_col)
        .reset_index()
    )
    out.attrs["time_frequency"] = effective_freq
    return out


def prepare_panel_data(
    df: pd.DataFrame,
    *,
    unit_col: str | None,
    time_col: str,
    y_col: str,
    y_plot_col: str,
    time_frequency: str | None = "auto",
) -> pd.DataFrame:
    required = [time_col, y_col]
    if unit_col is not None:
        required.insert(0, unit_col)
    validate_columns(df, required)

    columns = required.copy()
    out = df[columns].copy()

    if unit_col is not None:
        out[unit_col] = out[unit_col].astype(str)

    out[time_col] = normalize_time_column(out[time_col], time_frequency=time_frequency)
    out[y_col] = pd.to_numeric(out[y_col], errors="coerce")
    out[y_plot_col] = out[y_col]

    sort_cols = [col for col in [unit_col, time_col] if col is not None]
    return out.sort_values(sort_cols).reset_index(drop=True)


def apply_time_axis(ax: plt.Axes, *, freq: str | None = "auto", year_tick_base: int = 2) -> None:
    """Apply a readable time axis for daily, monthly, or annual panels."""

    effective_freq = freq
    if isinstance(effective_freq, str):
        effective_freq = effective_freq.upper()

    # Keep the original thesis-friendly look: year labels on the main x-axis.
    if effective_freq in {"YS", "AS", "A", "Y", "YEAR", "ANNUAL", "YEARLY"}:
        ax.xaxis.set_major_locator(mdates.YearLocator(base=max(int(year_tick_base), 1), month=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_minor_locator(mdates.YearLocator(base=1, month=1))
        return

    if effective_freq in {"MS", "M", "MONTH", "MONTHLY"}:
        ax.xaxis.set_major_locator(mdates.YearLocator(base=max(int(year_tick_base), 1), month=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
        return

    ax.xaxis.set_major_locator(mdates.YearLocator(base=max(int(year_tick_base), 1), month=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_minor_locator(mdates.YearLocator(base=1, month=1))


def apply_year_axis(ax: plt.Axes, base: int = 2) -> None:
    """Backward-compatible alias for the original year-based axis helper."""

    apply_time_axis(ax, freq="YS", year_tick_base=base)


def apply_y_axis(
    ax: plt.Axes,
    *,
    y_limits: tuple[float, float] | None = None,
    y_tick_step: float | None = None,
) -> None:
    if y_limits is not None:
        ax.set_ylim(*y_limits)
        if y_tick_step is not None:
            ax.set_yticks(np.arange(y_limits[0], y_limits[1] + y_tick_step, y_tick_step))


def maybe_make_parent(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
