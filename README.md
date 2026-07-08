# panelplots

`panelplots` is a lightweight Python package for producing standardized, publication-ready visual summaries of large panel datasets. It focuses on two complementary tools:

1. **Spaghetti plots**: show many unit-level trajectories over time.
2. **Descriptive fan charts**: summarize the cross-sectional distribution over time using quantile bands.

The package is motivated by daily nighttime lights panels, but it works with any long-format panel dataset: districts over days, firms over months, individuals over years, countries over decades, pixels over time, and similar structures.

## Why this package?

Large panel datasets are hard to visualize well. Plotting every unit can reveal the envelope, outliers, breaks, and shared trends, but it can also create visual clutter. Aggregating everything into one mean line is cleaner, but it hides heterogeneity and distributional change. `panelplots` standardizes both approaches so a thesis, paper, presentation, or dataset documentation can use the same visual grammar everywhere.

## Installation from GitHub

After creating a public GitHub repository, users can install the package directly with:

```bash
pip install git+https://github.com/YOUR_USERNAME/panelplots.git
```

For local development:

```bash
git clone https://github.com/YOUR_USERNAME/panelplots.git
cd panelplots
pip install -e .
```

## Minimal example

```python
from panelplots import plot_spaghetti, plot_fanchart

# df must be a long-format panel with one row per unit-time observation.
# Required columns in this example:
#   ID_ADMIN: district identifier
#   date: daily date
#   mean: raw daily mean nighttime lights radiance

fig, ax = plot_spaghetti(
    df,
    y="mean",
    time="date",
    unit="ID_ADMIN",
    transform="blackmarble_log_mean",
    transform_scale=1000,
    expected_units=1793,
    y_label="Log\nNTL",
    x_label="Year",
    y_limits=(0, 16),
    y_tick_step=2,
    mean_label="Mean across 1,793 districts",
    output_path="figures/peru_daily_spaghetti.png",
)

fig, ax, fan_stats, saved_paths = plot_fanchart(
    df,
    y="mean",
    time="date",
    unit="ID_ADMIN",
    transform="blackmarble_log_mean",
    transform_scale=1000,
    expected_units=1793,
    y_label="Log\nNTL",
    x_label="Year",
    y_limits=(0, 16),
    y_tick_step=2,
    output_path="figures/peru_daily_decile_fanchart.png",
    stats_output_path="figures/peru_daily_decile_fanchart_quantiles.csv",
    return_data=True,
)
```

## Time variables: daily, monthly, and annual panels

`panelplots` now accepts the most common time encodings automatically:

```python
# Daily dates
df["date"] = "2020-05-17"

# Month-year strings
df["month"] = "2020-05"

# Numeric years
df["year"] = 2020
```

You can normally leave the default `freq="auto"`. The package will infer whether the panel is daily, monthly, or annual and will use the correct complete time grid for fan charts.

```python
# Monthly panel: one row per unit-month
plot_fanchart(
    df_monthly,
    y="mean",
    time="month",      # values like "2020-05"
    unit="ID_ADMIN",
    transform="blackmarble_log_mean",
)

# Annual panel: one row per unit-year
plot_spaghetti(
    df_annual,
    y="mean",
    time="year",       # values like 2020, 2021, 2022
    unit="ID_ADMIN",
    transform="blackmarble_log_mean",
)
```

If you prefer to be explicit, use `freq="D"` for daily data, `freq="MS"` for month-start monthly data, or `freq="YS"` for year-start annual data in `plot_fanchart()`. For annual spaghetti plots, use `time_frequency="YS"`.

## Peru Black Marble example

The folder `examples/` includes `peru_blackmarble_example.py`, which reproduces the Peru-style figures from a local Parquet/CSV file. The folder `notebooks/` includes a Colab-ready template for loading the private Hugging Face Black Marble repository and then calling the package functions.

The Peru example uses the harmonized transformation:

```python
log(1 + 1000 × mean daily radiance)
```

and fixes the y-axis to `0–16`, which makes figures directly comparable across Peru, Indonesia, and Bolivia when the same transformation is used.

## Main functions

### `plot_spaghetti()`

Creates a spaghetti plot from a long-format panel dataset. It can:

- plot all units or a reproducible random subset;
- color unit trajectories by long-run average outcome;
- add a thick mean line across units;
- apply the Black Marble transformation `log(1 + 1000 × y)`;
- save figures as PNG, PDF, SVG, or any matplotlib-supported format;
- accept daily dates, month-year strings, or numeric years as the time variable.

### `plot_fanchart()`

Creates a descriptive fan chart from cross-sectional quantiles by time. It can:

- compute deciles, quintiles, or custom quantiles;
- draw adjacent quantile bands;
- preserve missing dates, months, or years as blank vertical gaps;
- save the quantile table used for the figure;
- use a cold-to-warm palette for lower-to-upper distribution bands;
- infer daily, monthly, or annual frequency automatically with `freq="auto"`.

### `set_academic_style()`

Applies a clean matplotlib style for academic figures.

### `save_figure()`

Exports a matplotlib figure to one or multiple formats.

## Design principles

- Keep the API simple.
- Depend only on `pandas`, `numpy`, and `matplotlib` for the core package.
- Make figures reproducible and thesis-ready.
- Make the style consistent across notebooks and projects.
- Keep the package general enough for non-remote-sensing panel data.

## Suggested repository structure

```text
panelplots/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── panelplots/
│       ├── __init__.py
│       ├── spaghetti.py
│       ├── fanchart.py
│       ├── transforms.py
│       ├── style.py
│       ├── io.py
│       └── utils.py
├── examples/
│   └── peru_blackmarble_example.py
├── notebooks/
│   └── peru_blackmarble_colab_template.ipynb
└── tests/
    └── test_basic.py
```

## Status

Initial research prototype. The current API is intentionally small and focused on producing consistent figures for large panel datasets.
