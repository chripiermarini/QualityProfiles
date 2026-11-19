"""Interactive plots of quality profiles with Plotly (optional dependency)."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from .core import QualityProfile
from .plotting import DEFAULT_LINEAR_REFERENCE_LINES, default_colors, paper_colors

__all__ = ["plot_quality_profiles_interactive", "step_points"]

PLOTLY_DASHES: tuple[str, ...] = ("solid", "dash", "dashdot", "dot", "longdash", "longdashdot")
"""Plotly dash patterns, one per solver, so that curves stay distinguishable without color."""

_GRID = "#e4e3df"
_INK = "#1f1f1e"
_INK_SECONDARY = "#52514e"


def step_points(
    x: NDArray[np.float64], y: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Reduce a sampled step function to the points needed to draw it exactly.

    For every jump, the last sample of the old level and the first sample of
    the new one are kept, together with the end points. Drawn with a
    horizontal-then-vertical line shape, the result is identical to the full
    curve, with far fewer points.

    Parameters
    ----------
    x, y : ndarray, shape (T,)
        Sorted abscissae and the step function sampled on them.

    Returns
    -------
    x, y : ndarray
        The retained samples, in order.
    """
    if y.size <= 2:
        return x, y
    jumps = np.flatnonzero(y[1:] != y[:-1]) + 1
    keep = np.zeros(y.size, dtype=bool)
    keep[[0, -1]] = True
    keep[jumps] = True
    keep[jumps - 1] = True
    return x[keep], y[keep]


def plot_quality_profiles_interactive(
    profile: QualityProfile,
    *,
    logscale: bool = True,
    solvers: Sequence[str | int] | None = None,
    colors: Sequence[str] | Literal["paper"] | None = None,
    linewidth: float = 2.0,
    reference_lines: Sequence[float] | None = None,
    title: str | None = None,
    height: int = 420,
    width: int | None = None,
) -> Any:
    r"""Interactive Plotly figure of the quality profiles :math:`[Q_s(\tau^{r_1})]^{r_2}`.

    The figure supports zooming, hiding solvers by clicking on the legend,
    and shows the values of all solvers at the hovered precision level.
    Requires Plotly: ``pip install quality-profiles[interactive]``.

    Parameters
    ----------
    profile : QualityProfile
        Profiles returned by :func:`quality_profiles`.
    logscale : bool, default True
        Use a logarithmic abscissa. The point :math:`\tau = 0` is omitted in this case.
    solvers : sequence of str or int, optional
        Subset of solvers to draw (names or column indices). All by default.
    colors : sequence of str or "paper", optional
        One CSS color per solver of the profile, in column order. Defaults to
        :func:`default_colors`; ``"paper"`` uses the paper's red-to-blue colors.
    linewidth : float, default 2.0
        Width of the profile lines, in pixels.
    reference_lines : sequence of float, optional
        Abscissae of vertical guide lines. Defaults to ``(1e-3, 1e-2, 1e-1)``
        on a linear abscissa and to none on a logarithmic one.
    title : str, optional
        Figure title.
    height, width : int, optional
        Size of the figure in pixels. The width follows the container by default.

    Returns
    -------
    plotly.graph_objects.Figure
        Show it with ``fig.show()`` or save it with ``fig.write_html(...)``.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError(
            "interactive plots need the 'plotly' package: pip install quality-profiles[interactive]"
        ) from None

    n = profile.n_solvers
    columns = list(range(n)) if solvers is None else [profile._column(s) for s in solvers]
    if colors is None:
        palette = default_colors(n)
    elif isinstance(colors, str):
        if colors != "paper":
            raise ValueError(f"unknown color scheme {colors!r}; use 'paper' or a sequence")
        palette = [f"rgb({r * 255:.0f},{g * 255:.0f},{b * 255:.0f})" for r, g, b in paper_colors(n)]
    elif len(colors) < n:
        raise ValueError(f"got {len(colors)} colors for {n} solvers")
    else:
        palette = list(colors)

    x = profile.precision
    rows = slice(1, None) if logscale else slice(None)
    fig = go.Figure()
    for col in columns:
        name = profile.solver_names[col]
        xs, ys = step_points(x[rows], profile.values[rows, col])
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                name=name,
                mode="lines",
                line={
                    "shape": "hv",
                    "width": linewidth,
                    "color": palette[col],
                    "dash": PLOTLY_DASHES[col % len(PLOTLY_DASHES)],
                },
                hovertemplate=f"{name}: %{{y:.3f}}<extra></extra>",
            )
        )

    if reference_lines is None:
        reference_lines = () if logscale else DEFAULT_LINEAR_REFERENCE_LINES
    for xv in reference_lines:
        fig.add_vline(x=xv, line={"color": _INK_SECONDARY, "width": 1, "dash": "dot"})

    xaxis: dict[str, Any] = {
        "title": {"text": "precision τ<sup>r1</sup>"},
        "showgrid": True,
        "gridcolor": _GRID,
        "zeroline": False,
        "hoverformat": ".2e",
    }
    if logscale:
        x_min = float(x[rows][0])
        decades = -math.log10(x_min)
        xaxis.update(type="log", range=[math.log10(x_min), 0.0])
        if decades > 1:
            xaxis.update(exponentformat="power", dtick=max(1, math.ceil(decades / 9)))
    else:
        xaxis.update(range=[0.0, 1.0])

    fig.update_layout(
        template="simple_white",
        height=height,
        width=width,
        title={"text": title, "x": 0.01, "font": {"size": 15, "color": _INK}} if title else None,
        margin={"l": 60, "r": 20, "t": 50 if title else 20, "b": 50},
        hovermode="x unified",
        # Each curve keeps only its jump points, so a long flat step can be far from the
        # cursor: always take the nearest point of every curve. Both ends of a flat step
        # carry the same value, so the hovered value is the value of the step.
        hoverdistance=-1,
        font={"color": _INK},
        legend={"x": 1.02, "y": 1.0, "xanchor": "left", "yanchor": "top"},
        xaxis=xaxis,
        yaxis={
            "title": {"text": "[Q<sub>s</sub>(τ)]<sup>r2</sup>"},
            "showgrid": True,
            "gridcolor": _GRID,
            "zeroline": False,
        },
    )
    return fig
