from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_hex

from quality_profiles import (
    PALETTE,
    default_colors,
    paper_colors,
    plot_quality_profiles,
    quality_profiles,
)


@pytest.fixture
def profile(random_problem):
    return quality_profiles(*random_problem, n_intervals=100)


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def test_log_plot(profile):
    ax = plot_quality_profiles(profile, title="QP")
    assert ax.get_xscale() == "log"
    assert len(ax.get_lines()) == 3
    # tau = 0 is skipped on a log axis
    assert all(len(line.get_xdata()) == 100 for line in ax.get_lines())
    assert [t.get_text() for t in ax.get_legend().get_texts()] == list(profile.solver_names)
    assert ax.get_title(loc="left") == "QP"


def test_linear_plot_draws_reference_lines(profile):
    ax = plot_quality_profiles(profile, logscale=False)
    assert ax.get_xscale() == "linear"
    assert len(ax.get_lines()) == 3 + 3
    ax2 = plot_quality_profiles(profile, logscale=False, reference_lines=())
    assert len(ax2.get_lines()) == 3


def test_existing_axes_and_subset(profile):
    _, ax = plt.subplots()
    out = plot_quality_profiles(profile, ax, solvers=["Solver-3", 0], legend=False)
    assert out is ax
    labels = [line.get_label() for line in ax.get_lines()]
    assert labels == ["Solver-3", "Solver-1"]
    assert ax.get_legend() is None


def test_custom_styles(profile):
    ax = plot_quality_profiles(profile, colors=["k", "g", "m"], linestyles=["-"])
    assert {line.get_linestyle() for line in ax.get_lines()} == {"-"}
    with pytest.raises(ValueError, match="colors"):
        plot_quality_profiles(profile, colors=["k"])
    with pytest.raises(ValueError, match="color scheme"):
        plot_quality_profiles(profile, colors="rainbow")


def test_colors_follow_the_solver_not_its_position(profile):
    full = plot_quality_profiles(profile)
    _, ax = plt.subplots()
    subset = plot_quality_profiles(profile, ax, solvers=["Solver-3"])
    assert to_hex(subset.get_lines()[0].get_color()) == to_hex(full.get_lines()[2].get_color())
    assert subset.get_lines()[0].get_linestyle() == full.get_lines()[2].get_linestyle()


def test_paper_colors_option(profile):
    ax = plot_quality_profiles(profile, colors="paper")
    assert [line.get_color() for line in ax.get_lines()] == paper_colors(3)


def test_profiles_are_drawn_as_steps(profile):
    ax = plot_quality_profiles(profile)
    assert all(line.get_drawstyle() == "steps-post" for line in ax.get_lines())


def test_straight_segments_option(profile):
    # steps=False joins the grid points with straight segments, as the MATLAB code
    # does; the plotted points are the same.
    steps = plot_quality_profiles(profile)
    segments = plot_quality_profiles(profile, steps=False)
    assert all(line.get_drawstyle() == "default" for line in segments.get_lines())
    for a, b in zip(steps.get_lines(), segments.get_lines(), strict=True):
        np.testing.assert_array_equal(a.get_xydata(), b.get_xydata())


def test_underflowing_precision_levels_are_skipped_on_log_axes():
    # with r1 = 100 the first levels (1/n)**100 underflow to 0
    qp = quality_profiles([1.0, 1.0], [[1e-300, 0.5], [0.0, 0.0]], r1=100)
    assert (qp.precision[1:] == 0).any()
    ax = plot_quality_profiles(qp)
    ax.figure.canvas.draw()
    x = ax.get_lines()[0].get_xdata()
    assert np.all(x > 0)
    assert ax.get_xlim()[0] > 0


def test_outside_legend(profile):
    ax = plot_quality_profiles(profile, legend_loc="outside right center")
    assert ax.get_legend() is None
    (legend,) = ax.figure.legends
    assert [t.get_text() for t in legend.get_texts()] == list(profile.solver_names)


def test_outside_legend_needs_layout_engine(profile):
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match="layout engine"):
        plot_quality_profiles(profile, ax, legend_loc="outside right center")


def test_legend_lists_only_profiles(profile):
    ax = plot_quality_profiles(profile, logscale=False)  # adds reference lines
    assert len(ax.get_legend().get_texts()) == 3


def test_default_colors():
    assert default_colors(3) == list(PALETTE[:3])
    assert default_colors(9)[8] == PALETTE[0]
    with pytest.raises(ValueError):
        default_colors(0)


def test_paper_colors():
    colors = paper_colors(3)
    assert colors[0] == (1.0, 0.0, 0.0) and colors[-1] == (0.0, 0.0, 1.0)
    assert np.allclose(colors[1], (0.5, 0.0, 0.5))
    with pytest.raises(ValueError):
        paper_colors(0)
