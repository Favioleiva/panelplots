"""Outcome transformations for panel visualizations."""

from __future__ import annotations

from typing import Callable, Literal

import numpy as np
import pandas as pd

TransformName = Literal["none", "log1p", "log1p_scaled", "blackmarble_log_mean"]


def blackmarble_log_mean_transform(values: pd.Series | np.ndarray, scale: float = 1000.0) -> pd.Series:
    """Return ``log(1 + scale * values)``.

    This is the harmonized transformation used in the Peru / Indonesia / Bolivia
    daily Black Marble examples: ``log(1 + 1000 × mean daily radiance)``.
    """

    numeric = pd.to_numeric(values, errors="coerce")
    return np.log1p(scale * numeric)


def apply_transform(
    values: pd.Series | np.ndarray,
    transform: TransformName | Callable[[pd.Series], pd.Series] | None = None,
    *,
    scale: float = 1000.0,
) -> pd.Series:
    """Apply a named or callable transformation to an outcome series.

    Parameters
    ----------
    values:
        Raw outcome values.
    transform:
        One of ``None``, ``"none"``, ``"log1p"``, ``"log1p_scaled"``,
        ``"blackmarble_log_mean"``, or a callable that accepts a pandas Series.
    scale:
        Scale factor used by ``"log1p_scaled"`` and ``"blackmarble_log_mean"``.
    """

    series = pd.to_numeric(values, errors="coerce")

    if transform is None or transform == "none":
        return series

    if callable(transform):
        return transform(series)

    if transform == "log1p":
        return np.log1p(series)

    if transform in {"log1p_scaled", "blackmarble_log_mean"}:
        return blackmarble_log_mean_transform(series, scale=scale)

    raise ValueError(
        "Unknown transform. Use None, 'none', 'log1p', 'log1p_scaled', "
        "'blackmarble_log_mean', or a callable."
    )
