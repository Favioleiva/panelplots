"""Input/output helpers for panelplots."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt


def save_figure(
    fig: plt.Figure,
    output_path: str | Path,
    *,
    dpi: int = 300,
    formats: Iterable[str] | None = None,
    facecolor: str = "white",
) -> list[Path]:
    """Save a matplotlib figure in one or several publication formats.

    Parameters
    ----------
    fig:
        Matplotlib figure to save.
    output_path:
        File path. If ``formats`` is provided, the suffix of ``output_path`` is
        replaced by each requested format.
    dpi:
        Resolution for raster outputs such as PNG.
    formats:
        Optional list such as ``["png", "pdf", "svg"]``.
    facecolor:
        Figure background color.
    """

    base = Path(output_path)
    base.parent.mkdir(parents=True, exist_ok=True)

    if formats is None:
        paths = [base]
    else:
        paths = [base.with_suffix("." + fmt.lower().lstrip(".")) for fmt in formats]

    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=dpi, facecolor=facecolor)

    return paths
