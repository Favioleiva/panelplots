"""Panelplots: publication-ready spaghetti plots and descriptive fan charts."""

from .fanchart import compute_quantile_fan, plot_fanchart
from .io import save_figure
from .spaghetti import plot_spaghetti
from .style import set_academic_style
from .transforms import apply_transform, blackmarble_log_mean_transform

__all__ = [
    "apply_transform",
    "blackmarble_log_mean_transform",
    "compute_quantile_fan",
    "plot_fanchart",
    "plot_spaghetti",
    "save_figure",
    "set_academic_style",
]

__version__ = "0.1.1"
