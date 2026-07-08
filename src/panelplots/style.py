"""Shared plotting style for academic panel figures."""

from __future__ import annotations

from typing import Mapping, Any

import matplotlib.pyplot as plt


def set_academic_style(extra_rc: Mapping[str, Any] | None = None) -> None:
    """Apply a clean, publication-oriented matplotlib style.

    The function intentionally relies only on matplotlib so that the package
    stays lightweight and easy to install in notebooks, Colab, and research
    servers.
    """

    rc = {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.labelsize": 18,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.frameon": False,
        "font.size": 14,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    }

    if extra_rc:
        rc.update(dict(extra_rc))

    plt.rcParams.update(rc)
