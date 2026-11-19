from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest

from quality_profiles import default_colors, plot_quality_profiles, quality_profiles


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
    assert ax.get_title() == "QP"


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


def test_default_colors():
    colors = default_colors(3)
    assert colors[0] == (1.0, 0.0, 0.0) and colors[-1] == (0.0, 0.0, 1.0)
    assert np.allclose(colors[1], (0.5, 0.0, 0.5))
    with pytest.raises(ValueError):
        default_colors(0)
