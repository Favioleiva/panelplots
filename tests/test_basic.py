from __future__ import annotations

import numpy as np
import pandas as pd

from panelplots import compute_quantile_fan, plot_fanchart, plot_spaghetti
from panelplots.utils import infer_time_frequency, normalize_time_column


def make_sample_panel(freq: str = "D") -> pd.DataFrame:
    rng = np.random.default_rng(123)
    if freq == "D":
        dates = pd.date_range("2020-01-01", periods=30, freq="D")
    elif freq == "MS":
        dates = pd.date_range("2020-01-01", periods=12, freq="MS").strftime("%Y-%m")
    elif freq == "YS":
        dates = np.arange(2010, 2020)
    else:
        raise ValueError(freq)

    units = [f"u{i:03d}" for i in range(20)]
    rows = []
    for i, unit in enumerate(units):
        base = i / 10
        for t, date in enumerate(dates):
            rows.append({"unit": unit, "date": date, "mean": base + 0.01 * t + rng.random() * 0.1})
    return pd.DataFrame(rows)


def test_compute_quantile_fan_deciles_daily():
    df = make_sample_panel("D")
    fan = compute_quantile_fan(
        df,
        y="mean",
        time="date",
        unit="unit",
        transform="blackmarble_log_mean",
    )
    assert len(fan) == 30
    assert fan.attrs["time_frequency"] == "D"
    assert "q00" in fan.columns
    assert "q50" in fan.columns
    assert "q100" in fan.columns


def test_month_year_strings_are_supported():
    df = make_sample_panel("MS")
    fan = compute_quantile_fan(
        df,
        y="mean",
        time="date",
        unit="unit",
        transform="blackmarble_log_mean",
    )
    assert len(fan) == 12
    assert fan.attrs["time_frequency"] == "MS"
    assert fan["date"].dt.day.eq(1).all()


def test_numeric_years_are_supported():
    df = make_sample_panel("YS")
    fan = compute_quantile_fan(
        df,
        y="mean",
        time="date",
        unit="unit",
        transform="blackmarble_log_mean",
    )
    assert len(fan) == 10
    assert fan.attrs["time_frequency"] == "YS"
    assert fan["date"].dt.month.eq(1).all()
    assert fan["date"].dt.day.eq(1).all()
    assert fan["date"].dt.year.min() == 2010


def test_time_normalization_helpers():
    years = normalize_time_column(pd.Series([2020, 2021]))
    months = normalize_time_column(pd.Series(["2020-05", "2020/06"]))
    days = normalize_time_column(pd.Series(["2020-05-03", "2020-05-04"]))

    assert years.dt.strftime("%Y-%m-%d").tolist() == ["2020-01-01", "2021-01-01"]
    assert months.dt.strftime("%Y-%m-%d").tolist() == ["2020-05-01", "2020-06-01"]
    assert infer_time_frequency(years) == "YS"
    assert infer_time_frequency(months) == "MS"
    assert infer_time_frequency(days) == "D"


def test_plot_functions_return_fig_ax_for_daily_monthly_and_annual():
    for freq in ["D", "MS", "YS"]:
        df = make_sample_panel(freq)
        fig1, ax1 = plot_spaghetti(
            df,
            y="mean",
            time="date",
            unit="unit",
            transform="blackmarble_log_mean",
            y_limits=(0, 10),
            y_tick_step=2,
        )
        fig2, ax2 = plot_fanchart(
            df,
            y="mean",
            time="date",
            unit="unit",
            transform="blackmarble_log_mean",
            y_limits=(0, 10),
            y_tick_step=2,
        )
        assert fig1 is ax1.figure
        assert fig2 is ax2.figure
