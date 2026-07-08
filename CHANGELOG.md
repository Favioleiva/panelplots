# Changelog

## 0.1.1

- Added automatic time parsing for daily, monthly, and annual panel datasets.
- Numeric year columns such as `2020` are now interpreted as `2020-01-01`, not as nanoseconds after 1970.
- Month-year strings such as `"2020-05"` and `"2020/05"` are now normalized to month-start dates.
- `plot_fanchart()` now uses `freq="auto"` by default and completes daily, monthly, or annual grids automatically.
- Added tests for daily, monthly, and annual panels.

## 0.1.0

- Initial package scaffold.
- Added `plot_spaghetti()`.
- Added `plot_fanchart()`.
- Added `compute_quantile_fan()`.
- Added Black Marble transformation helper.
- Added Peru Black Marble example script and Colab template.
