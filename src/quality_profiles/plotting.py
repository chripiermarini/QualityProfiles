"""Plotting of quality profiles with matplotlib."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

import numpy as np

from .core import QualityProfile

if TYPE_CHECKING:
    from matplotlib.axes import Axes

__all__ = ["default_colors", "plot_quality_profiles"]

DEFAULT_LINESTYLES: tuple[str, ...] = ("-", "--", "-.", ":")
"""Line styles cycled over the solvers, as in the figures of the paper."""

DEFAULT_LINEAR_REFERENCE_LINES: tuple[float, ...] = (1e-3, 1e-2, 1e-1)
"""Vertical guides drawn on linear abscissae (1, 2 and 3 orders of magnitude)."""


def default_colors(n_solvers: int) -> list[tuple[float, float, float]]:
    """Return ``n_solvers`` colors fading from red to blue, as in the paper's figures.

    Parameters
    ----------
    n_solvers : int
        Number of colors.

    Returns
    -------
    list of (float, float, float)
        RGB triples.
    """
    if n_solvers < 1:
        raise ValueError("n_solvers must be at least 1")
    red = np.linspace(1.0, 0.0, n_solvers)
    return [(float(r), 0.0, float(1.0 - r)) for r in red]


def plot_quality_profiles(
    profile: QualityProfile,
    ax: Axes | None = None,
    *,
    logscale: bool = True,
    solvers: Sequence[str | int] | None = None,
    colors: Sequence[Any] | None = None,
    linestyles: Sequence[str] | None = None,
    linewidth: float = 2.5,
    reference_lines: Sequence[float] | None = None,
    legend: bool = True,
    legend_loc: str = "best",
    title: str | None = None,
    grid: bool = True,
) -> Axes:
    r"""Plot quality profiles :math:`[Q_s(\tau^{r_1})]^{r_2}` against :math:`\tau^{r_1}`.

    Parameters
    ----------
    profile : QualityProfile
        Profiles returned by :func:`quality_profiles`.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on. A new figure is created if omitted.
    logscale : bool, default True
        Use a logarithmic abscissa (recommended: equally spaced ticks then
        correspond to orders of magnitude of accuracy). The point
        :math:`\tau = 0` is omitted in this case.
    solvers : sequence of str or int, optional
        Subset of solvers to draw (names or column indices). All by default.
    colors : sequence, optional
        One matplotlib color per drawn solver. Defaults to :func:`default_colors`.
    linestyles : sequence of str, optional
        Line styles, cycled over the solvers. Defaults to ``("-", "--", "-.", ":")``.
    linewidth : float, default 2.5
        Width of the profile lines.
    reference_lines : sequence of float, optional
        Abscissae of thin vertical guide lines. Defaults to
        ``(1e-3, 1e-2, 1e-1)`` on a linear abscissa and to none on a
        logarithmic one. Pass ``()`` to disable.
    legend : bool, default True
        Draw a legend with the solver names.
    legend_loc : str, default "best"
        Legend location, forwarded to :meth:`matplotlib.axes.Axes.legend`.
    title : str, optional
        Axes title.
    grid : bool, default True
        Draw a grid.

    Returns
    -------
    matplotlib.axes.Axes
        The axes containing the plot.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(8, 5.5), layout="constrained")

    columns = (
        list(range(profile.n_solvers)) if solvers is None else [profile._column(s) for s in solvers]
    )
    if colors is None:
        colors = default_colors(len(columns))
    elif len(colors) < len(columns):
        raise ValueError(f"got {len(colors)} colors for {len(columns)} solvers")
    styles = tuple(linestyles) if linestyles else DEFAULT_LINESTYLES

    x = profile.precision
    rows = slice(1, None) if logscale else slice(None)
    for i, col in enumerate(columns):
        ax.plot(
            x[rows],
            profile.values[rows, col],
            color=colors[i],
            linestyle=styles[i % len(styles)],
            linewidth=linewidth,
            label=profile.solver_names[col],
        )

    if reference_lines is None:
        reference_lines = () if logscale else DEFAULT_LINEAR_REFERENCE_LINES
    for xv in reference_lines:
        ax.axvline(xv, color="k", linewidth=0.5)

    if logscale:
        ax.set_xscale("log")
    ax.set_xlabel(r"$0 \leq \tau^{r_1} \leq 1$")
    ax.set_ylabel(r"$[\,Q_s(\tau)\,]^{r_2}$")
    if title is not None:
        ax.set_title(title)
    if grid:
        ax.grid(True, which="major", alpha=0.4)
    if legend:
        ax.legend(loc=cast(Any, legend_loc))
    return ax
