"""Example: Peru daily Black Marble spaghetti plot and descriptive fan chart.

Usage
-----
python examples/peru_blackmarble_example.py /path/to/peru_daily_panel.parquet \
    --output-dir presentation_figures

The input file must contain at least:
    ID_ADMIN, date, mean

The time column may be daily dates, month-year strings such as 2020-05,
or numeric years such as 2020.

This example reproduces the package version of the Peru plotting logic from the
original research notebook.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from panelplots import plot_fanchart, plot_spaghetti


def read_panel(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError("Input must be a .parquet or .csv file.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", type=Path, help="Local Peru daily panel file.")
    parser.add_argument("--output-dir", type=Path, default=Path("presentation_figures"))
    parser.add_argument("--id-col", default="ID_ADMIN")
    parser.add_argument("--date-col", default="date")
    parser.add_argument("--y-col", default="mean")
    parser.add_argument(
        "--freq",
        default="auto",
        help="Time frequency for fan chart completion: auto, D, MS, YS, or None.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = read_panel(args.input_path)

    print("Loaded panel:")
    print("Rows:", f"{len(df):,}")
    print("Columns:", f"{df.shape[1]:,}")

    fig, ax = plot_spaghetti(
        df,
        y=args.y_col,
        time=args.date_col,
        unit=args.id_col,
        transform="blackmarble_log_mean",
        transform_scale=1000,
        time_frequency=args.freq if args.freq != "None" else None,
        expected_units=1793,
        y_label="Log\nNTL",
        x_label="Year",
        y_limits=(0, 16),
        y_tick_step=2,
        mean_label="Mean across 1,793 districts",
        output_path=args.output_dir / "peru_daily_spaghetti_log_mean_x1000_plus1_y0_16.png",
        output_formats=["png", "pdf", "svg"],
    )

    fig, ax, fan_stats, saved_paths = plot_fanchart(
        df,
        y=args.y_col,
        time=args.date_col,
        unit=args.id_col,
        transform="blackmarble_log_mean",
        transform_scale=1000,
        freq=args.freq if args.freq != "None" else None,
        expected_units=1793,
        y_label="Log\nNTL",
        x_label="Year",
        y_limits=(0, 16),
        y_tick_step=2,
        output_path=args.output_dir / "peru_daily_decile_fanchart_log_mean_x1000_plus1_y0_16.png",
        output_formats=["png", "pdf", "svg"],
        stats_output_path=args.output_dir / "peru_daily_decile_fanchart_quantiles_log_mean_x1000_plus1.csv",
        return_data=True,
    )

    print("Saved figures and quantile table in:", args.output_dir)


if __name__ == "__main__":
    main()
