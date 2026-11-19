"""Plotting of quality profiles with matplotlib."""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np

from .core import QualityProfile

if TYPE_CHECKING:
    from matplotlib.axes import Axes

__all__ = [
    "PALETTE",
    "SCIENCEPLOTS_STYLES",
    "default_colors",
    "paper_colors",
    "plot_quality_profiles",
]

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

SCIENCEPLOTS_STYLES: frozenset[str] = frozenset(
    {
        "science",
        "ieee",
        "nature",
        "notebook",
        "grid",
        "scatter",
        "no-latex",
        "latex-sans",
        "sans",
        "pgf",
        "bright",
        "vibrant",
        "muted",
        "retro",
        "high-contrast",
        "high-vis",
        "light",
        "std-colors",
    }
)
"""Style names provided by the optional SciencePlots package (loaded on demand)."""

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
    linewidth: float | None = None,
    reference_lines: Sequence[float] | None = None,
    legend: bool = True,
    legend_loc: str = "best",
    title: str | None = None,
    grid: bool | None = None,
    style: str | Sequence[str] | None = None,
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
        Defaults to :func:`default_colors`, or to the colors of ``style``.
        ``"paper"`` uses the red-to-blue colors of the paper (:func:`paper_colors`).
    linestyles : sequence, optional
        Line styles, assigned to the solvers in column order and cycled.
        Defaults to :data:`DEFAULT_LINESTYLES`, or to the line styles of
        ``style`` if it defines any.
    linewidth : float, optional
        Width of the profile lines. Defaults to 2, or to the width set by ``style``.
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
    grid : bool, optional
        Draw a grid. Defaults to a light grid, or to the choice of ``style``.
    style : str or sequence of str, optional
        A matplotlib style, or a list of styles, used instead of the package's
        look: for example ``"science"`` or ``["science", "ieee"]`` from
        SciencePlots (``pip install quality-profiles[science]``). Fonts, sizes,
        ticks and colors then come from the style. If ``"science"`` is
        requested and no LaTeX installation is found, ``"no-latex"`` is added.
        Leave ``ax=None`` so that the figure itself is created with the style.

    Returns
    -------
    matplotlib.axes.Axes
        The axes containing the plot.
    """
    import matplotlib.pyplot as plt

    options: dict[str, Any] = {
        "logscale": logscale,
        "solvers": solvers,
        "colors": colors,
        "linestyles": linestyles,
        "linewidth": linewidth,
        "reference_lines": reference_lines,
        "legend": legend,
        "legend_loc": legend_loc,
        "title": title,
        "grid": grid,
    }
    styles = _resolve_style(style)
    if styles is None:
        return _draw(profile, ax, themed=True, **options)
    with plt.style.context(styles):
        return _draw(profile, ax, themed=False, **options)


def _resolve_style(style: str | Sequence[str] | None) -> list[str] | None:
    if style is None:
        return None
    names = [style] if isinstance(style, str) else [str(n) for n in style]
    if any(n in SCIENCEPLOTS_STYLES for n in names):
        try:
            import scienceplots  # noqa: F401  (registers the styles with matplotlib)
        except ImportError:
            raise ImportError(
                "the SciencePlots styles need the 'SciencePlots' package: "
                "pip install quality-profiles[science]"
            ) from None
        if "science" in names and "no-latex" not in names and shutil.which("latex") is None:
            names.append("no-latex")
    return names


def _draw(
    profile: QualityProfile,
    ax: Axes | None,
    *,
    themed: bool,
    logscale: bool,
    solvers: Sequence[str | int] | None,
    colors: Sequence[Any] | Literal["paper"] | None,
    linestyles: Sequence[Any] | None,
    linewidth: float | None,
    reference_lines: Sequence[float] | None,
    legend: bool,
    legend_loc: str,
    title: str | None,
    grid: bool | None,
) -> Axes:
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(6.4, 4.0) if themed else None, layout="constrained")

    n = profile.n_solvers
    columns = list(range(n)) if solvers is None else [profile._column(s) for s in solvers]
    cycle = plt.rcParams["axes.prop_cycle"].by_key()
    palette: Sequence[Any]
    if colors is None:
        if themed or "color" not in cycle:
            palette = default_colors(n)
        else:
            palette = [cycle["color"][i % len(cycle["color"])] for i in range(n)]
    elif isinstance(colors, str):
        if colors != "paper":
            raise ValueError(f"unknown color scheme {colors!r}; use 'paper' or a sequence")
        palette = paper_colors(n)
    elif len(colors) < n:
        raise ValueError(f"got {len(colors)} colors for {n} solvers")
    else:
        palette = colors
    if linestyles:
        styles = tuple(linestyles)
    elif not themed and "linestyle" in cycle:
        styles = tuple(cycle["linestyle"])
    else:
        styles = DEFAULT_LINESTYLES
    if linewidth is None:
        linewidth = 2.0 if themed else float(plt.rcParams["lines.linewidth"])

    x = profile.precision
    rows = slice(1, None) if logscale else slice(None)
    profile_lines = []
    for col in columns:
        (line,) = ax.plot(
            x[rows],
            profile.values[rows, col],
            color=palette[col],
            linestyle=styles[col % len(styles)],
            linewidth=linewidth,
            drawstyle="steps-post",
            label=profile.solver_names[col],
            zorder=3,
        )
        profile_lines.append(line)

    if reference_lines is None:
        reference_lines = () if logscale else DEFAULT_LINEAR_REFERENCE_LINES
    guide_color = _INK_SECONDARY if themed else plt.rcParams["axes.edgecolor"]
    for xv in reference_lines:
        ax.axvline(xv, color=guide_color, linewidth=0.8, linestyle=(0, (2, 2)), zorder=2)

    if logscale:
        ax.set_xscale("log")
        if x[rows][0] >= 0.05:
            # Less than about one decade: plain numbers read better than powers of ten.
            from matplotlib.ticker import FuncFormatter

            plain = FuncFormatter(lambda v, _: f"{v:g}")
            ax.xaxis.set_major_formatter(plain)
            ax.xaxis.set_minor_formatter(plain)
    ax.set_xlim(x[rows][0], 1.0)

    xlabel, ylabel = r"precision  $\tau^{r_1}$", r"$[\,Q_s(\tau)\,]^{r_2}$"
    if not themed:
        # Leave every visual choice to the active style.
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title is not None:
            ax.set_title(title)
        if grid is not None:
            ax.grid(grid)
        if legend:
            ax.legend(loc=cast(Any, legend_loc))
        return ax

    for line in profile_lines:
        line.set_solid_capstyle("round")
        line.set_dash_capstyle("round")
    ax.set_xlabel(xlabel, color=_INK, fontsize=11)
    ax.set_ylabel(ylabel, color=_INK, fontsize=11)
    if title is not None:
        ax.set_title(title, color=_INK, fontsize=12, loc="left")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(_AXIS)
    ax.tick_params(colors=_INK_SECONDARY, labelsize=9.5, which="both")
    ax.tick_params(which="minor", length=0)
    if grid is None or grid:
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
