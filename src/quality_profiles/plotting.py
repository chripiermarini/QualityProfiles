"""Plotting of quality profiles with matplotlib."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np

from .core import QualityProfile

if TYPE_CHECKING:
    from matplotlib.axes import Axes

__all__ = ["PALETTE", "default_colors", "paper_colors", "plot_quality_profiles"]

PALETTE: tuple[str, ...] = (
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#6250d6",  # violet
    "#e34948",  # red
)
"""Categorical colors, in a fixed order that keeps neighbours distinguishable
with color-vision deficiencies."""

DEFAULT_LINESTYLES: tuple[Any, ...] = (
    "-",
    (0, (5, 2)),
    (0, (5, 1.5, 1, 1.5)),
    (0, (1, 1.2)),
    (0, (8, 2, 1, 2, 1, 2)),
    (0, (2.5, 1.5)),
    (0, (10, 2)),
    (0, (5, 1.5, 1, 1.5, 1, 1.5)),
)
"""Line styles, one per solver, so that curves stay distinguishable without color."""

DEFAULT_LINEAR_REFERENCE_LINES: tuple[float, ...] = (1e-3, 1e-2, 1e-1)
"""Vertical guides drawn on linear abscissae (1, 2 and 3 orders of magnitude)."""

_INK = "#1f1f1e"
_INK_SECONDARY = "#52514e"
_GRID = "#e4e3df"
_AXIS = "#b5b4ae"


def default_colors(n_solvers: int) -> list[str]:
    """Return the first ``n_solvers`` colors of :data:`PALETTE`.

    Beyond eight solvers the palette repeats; line styles still tell the
    curves apart, but consider plotting fewer solvers per figure.

    Parameters
    ----------
    n_solvers : int
        Number of colors.

    Returns
    -------
    list of str
        Hex colors.
    """
    if n_solvers < 1:
        raise ValueError("n_solvers must be at least 1")
    return [PALETTE[i % len(PALETTE)] for i in range(n_solvers)]


def paper_colors(n_solvers: int) -> list[tuple[float, float, float]]:
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
    colors: Sequence[Any] | Literal["paper"] | None = None,
    linestyles: Sequence[Any] | None = None,
    linewidth: float = 2.0,
    reference_lines: Sequence[float] | None = None,
    legend: bool = True,
    legend_loc: str = "best",
    title: str | None = None,
    grid: bool = True,
) -> Axes:
    r"""Plot quality profiles :math:`[Q_s(\tau^{r_1})]^{r_2}` against :math:`\tau^{r_1}`.

    Profiles are drawn as step functions. Each solver keeps the same color and
    line style when only a subset of solvers is drawn.

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
    colors : sequence or "paper", optional
        One matplotlib color per solver of the profile, in column order.
        Defaults to :func:`default_colors`; ``"paper"`` uses the red-to-blue
        colors of the paper (:func:`paper_colors`).
    linestyles : sequence, optional
        Line styles, assigned to the solvers in column order and cycled.
        Defaults to :data:`DEFAULT_LINESTYLES`.
    linewidth : float, default 2.0
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
        Draw a light grid.

    Returns
    -------
    matplotlib.axes.Axes
        The axes containing the plot.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(6.4, 4.0), layout="constrained")

    n = profile.n_solvers
    columns = list(range(n)) if solvers is None else [profile._column(s) for s in solvers]
    if colors is None:
        palette: Sequence[Any] = default_colors(n)
    elif isinstance(colors, str):
        if colors != "paper":
            raise ValueError(f"unknown color scheme {colors!r}; use 'paper' or a sequence")
        palette = paper_colors(n)
    elif len(colors) < n:
        raise ValueError(f"got {len(colors)} colors for {n} solvers")
    else:
        palette = colors
    styles = tuple(linestyles) if linestyles else DEFAULT_LINESTYLES

    x = profile.precision
    rows = slice(1, None) if logscale else slice(None)
    for col in columns:
        ax.plot(
            x[rows],
            profile.values[rows, col],
            color=palette[col],
            linestyle=styles[col % len(styles)],
            linewidth=linewidth,
            drawstyle="steps-post",
            solid_capstyle="round",
            dash_capstyle="round",
            label=profile.solver_names[col],
            zorder=3,
        )

    if reference_lines is None:
        reference_lines = () if logscale else DEFAULT_LINEAR_REFERENCE_LINES
    for xv in reference_lines:
        ax.axvline(xv, color=_INK_SECONDARY, linewidth=0.8, linestyle=(0, (2, 2)), zorder=2)

    if logscale:
        ax.set_xscale("log")
        if x[rows][0] >= 0.05:
            # Less than about one decade: plain numbers read better than powers of ten.
            from matplotlib.ticker import FuncFormatter

            plain = FuncFormatter(lambda v, _: f"{v:g}")
            ax.xaxis.set_major_formatter(plain)
            ax.xaxis.set_minor_formatter(plain)
    ax.set_xlim(x[rows][0], 1.0)
    ax.set_xlabel(r"precision  $\tau^{r_1}$", color=_INK, fontsize=11)
    ax.set_ylabel(r"$[\,Q_s(\tau)\,]^{r_2}$", color=_INK, fontsize=11)
    if title is not None:
        ax.set_title(title, color=_INK, fontsize=12, loc="left")

    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(_AXIS)
    ax.tick_params(colors=_INK_SECONDARY, labelsize=9.5, which="both")
    ax.tick_params(which="minor", length=0)
    if grid:
        ax.grid(True, which="major", color=_GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
    if legend:
        leg = ax.legend(
            loc=cast(Any, legend_loc),
            fontsize=9.5,
            handlelength=3.2,
            frameon=True,
            facecolor="white",
            edgecolor="none",
            framealpha=0.85,
        )
        for text in leg.get_texts():
            text.set_color(_INK)
    return ax
