"""Optional backends: SciencePlots styles and Plotly interactive figures."""

from __future__ import annotations

import builtins

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_hex

from quality_profiles import (
    PALETTE,
    paper_colors,
    plot_quality_profiles,
    plot_quality_profiles_interactive,
    quality_profiles,
)
from quality_profiles.interactive import step_points


@pytest.fixture
def profile(random_problem):
    return quality_profiles(*random_problem, n_intervals=100)


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _block_import(monkeypatch, module):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == module or name.startswith(module + "."):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


# ---------------------------------------------------------------------------
# Matplotlib styles
# ---------------------------------------------------------------------------


def test_plain_matplotlib_style_is_respected(profile):
    with plt.style.context("default"):
        expected = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    ax = plot_quality_profiles(profile, style="ggplot")
    colors = [to_hex(line.get_color()) for line in ax.get_lines()]
    with plt.style.context("ggplot"):
        ggplot_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    assert colors == [to_hex(c) for c in ggplot_colors[:3]]
    assert colors != [to_hex(c) for c in expected[:3]]
    assert all(line.get_drawstyle() == "steps-post" for line in ax.get_lines())
    # the package look is not applied: spines stay as the style wants them
    assert ax.spines["top"].get_visible()


def test_science_style(profile):
    pytest.importorskip("scienceplots")
    ax = plot_quality_profiles(profile, style="science")
    fig = ax.figure
    np.testing.assert_allclose(fig.get_size_inches(), (3.5, 2.625))
    # science defines colors only: line styles are added so curves differ without color
    patterns = {str(line._unscaled_dash_pattern) for line in ax.get_lines()}
    assert len(patterns) == 3


def test_loading_scienceplots_shows_no_deprecation_warnings(profile, monkeypatch):
    pytest.importorskip("scienceplots")
    import sys

    # force a fresh import, as in a new session; warnings are errors in this test suite
    for name in [m for m in sys.modules if m == "scienceplots" or m.startswith("scienceplots.")]:
        monkeypatch.delitem(sys.modules, name)
    plot_quality_profiles(profile, style="science")


def test_ieee_style_uses_its_own_line_styles(profile):
    pytest.importorskip("scienceplots")
    ax = plot_quality_profiles(profile, style=["science", "ieee"])
    assert [line.get_linestyle() for line in ax.get_lines()] == ["-", "--", ":"]


def test_short_style_cycle_never_draws_two_solvers_alike(rng):
    pytest.importorskip("scienceplots")
    f0 = rng.random(30)
    many = quality_profiles(f0, f0[:, None] - rng.random((30, 7)), n_intervals=50)
    ax = plot_quality_profiles(many, style=["science", "ieee"])  # ieee cycles 4 colors/styles
    looks = {
        (to_hex(line.get_color()), str(line._unscaled_dash_pattern)) for line in ax.get_lines()
    }
    assert len(looks) == 7


def test_style_keeps_colors_per_solver(profile):
    pytest.importorskip("scienceplots")
    full = plot_quality_profiles(profile, style="science")
    subset = plot_quality_profiles(profile, style="science", solvers=["Solver-3"])
    assert to_hex(subset.get_lines()[0].get_color()) == to_hex(full.get_lines()[2].get_color())


def test_style_with_paper_colors(profile):
    pytest.importorskip("scienceplots")
    ax = plot_quality_profiles(profile, style="science", colors="paper")
    assert [line.get_color() for line in ax.get_lines()] == paper_colors(3)


def test_style_does_not_leak(profile):
    pytest.importorskip("scienceplots")
    before = dict(plt.rcParams)
    plot_quality_profiles(profile, style=["science", "ieee"])
    assert plt.rcParams["figure.dpi"] == before["figure.dpi"]
    assert plt.rcParams["font.family"] == before["font.family"]


def test_missing_scienceplots_gives_install_hint(profile, monkeypatch):
    _block_import(monkeypatch, "scienceplots")
    with pytest.raises(ImportError, match=r"quality-profiles\[science\]"):
        plot_quality_profiles(profile, style="science")


def test_unknown_style_raises(profile):
    with pytest.raises(OSError):
        plot_quality_profiles(profile, style="no-such-style")


# ---------------------------------------------------------------------------
# Plotly
# ---------------------------------------------------------------------------


def test_interactive_figure(profile):
    pytest.importorskip("plotly")
    fig = plot_quality_profiles_interactive(profile, title="QP")
    assert [t.name for t in fig.data] == list(profile.solver_names)
    assert all(t.line.shape == "hv" for t in fig.data)
    assert [t.line.color for t in fig.data] == list(PALETTE[:3])
    assert fig.layout.xaxis.type == "log"
    assert fig.layout.title.text == "QP"
    # tau = 0 is skipped on a log axis; the drawn step function equals the profile
    for s, trace in enumerate(fig.data):
        x_full, y_full = profile.precision[1:], profile.values[1:, s]
        assert trace.x[0] == x_full[0] and trace.x[-1] == x_full[-1]
        np.testing.assert_array_equal(_as_step(trace.x, trace.y, x_full), y_full)


def _as_step(xs, ys, x_full):
    """Evaluate a horizontal-then-vertical polyline at the grid points."""
    return np.asarray(ys)[np.searchsorted(np.asarray(xs), x_full, side="right") - 1]


def test_step_points_is_exact_and_small(rng):
    x = np.linspace(0, 1, 5001)
    y = np.floor(np.cumsum(rng.random(5001) < 0.01)) / 60
    xs, ys = step_points(x, y)
    np.testing.assert_array_equal(_as_step(xs, ys, x), y)
    assert xs.size <= 2 * (np.count_nonzero(np.diff(y)) + 1)
    flat_x, flat_y = step_points(x, np.zeros_like(x))
    assert flat_x.tolist() == [0.0, 1.0] and flat_y.tolist() == [0.0, 0.0]
    short = step_points(x[:2], y[:2])
    assert short[0].size == 2


def test_interactive_hover_shows_every_solver(profile):
    pytest.importorskip("plotly")
    fig = plot_quality_profiles_interactive(profile)
    # the curves are thinned, so hover must not depend on a point being nearby
    assert fig.layout.hovermode == "x unified"
    assert fig.layout.hoverdistance == -1


def test_nearest_point_of_a_thinned_curve_has_the_step_value(profile):
    # What hoverdistance=-1 relies on: for any grid abscissa, the retained point
    # nearest to it (in plot coordinates) carries the profile value there, up to
    # one grid cell around each jump.
    x = np.log10(profile.precision[1:])
    for s in range(profile.n_solvers):
        y = profile.values[1:, s]
        xs, ys = step_points(x, y)
        nearest = ys[np.abs(xs[None, :] - x[:, None]).argmin(axis=1)]
        jump = np.flatnonzero(np.diff(y)) + 1
        near_jump = np.zeros(x.size, dtype=bool)
        near_jump[np.clip(np.concatenate([jump - 1, jump]), 0, x.size - 1)] = True
        np.testing.assert_array_equal(nearest[~near_jump], y[~near_jump])


def test_interactive_linear_with_reference_lines(profile):
    pytest.importorskip("plotly")
    fig = plot_quality_profiles_interactive(profile, logscale=False)
    assert fig.layout.xaxis.type != "log"
    assert len(fig.layout.shapes) == 3
    assert fig.data[0].x[0] == 0.0
    np.testing.assert_array_equal(
        _as_step(fig.data[0].x, fig.data[0].y, profile.precision), profile.values[:, 0]
    )


def test_interactive_subset_and_colors(profile):
    pytest.importorskip("plotly")
    fig = plot_quality_profiles_interactive(profile, solvers=["Solver-2"], colors="paper")
    assert [t.name for t in fig.data] == ["Solver-2"]
    assert fig.data[0].line.color == "rgb(128,0,128)"
    with pytest.raises(ValueError, match="colors"):
        plot_quality_profiles_interactive(profile, colors=["red"])
    with pytest.raises(ValueError, match="color scheme"):
        plot_quality_profiles_interactive(profile, colors="rainbow")


def test_interactive_with_underflowing_precision_levels():
    pytest.importorskip("plotly")
    qp = quality_profiles([1.0, 1.0], [[1e-300, 0.5], [0.0, 0.0]], r1=100)
    fig = plot_quality_profiles_interactive(qp)  # used to fail with "math domain error"
    assert all(np.all(np.asarray(t.x) > 0) for t in fig.data)
    assert np.isfinite(fig.layout.xaxis.range).all()


def test_interactive_html_export(profile, tmp_path):
    pytest.importorskip("plotly")
    out = tmp_path / "qp.html"
    plot_quality_profiles_interactive(profile).write_html(out, include_plotlyjs="cdn")
    assert "Solver-3" in out.read_text(encoding="utf-8")


def test_missing_plotly_gives_install_hint(profile, monkeypatch):
    _block_import(monkeypatch, "plotly")
    with pytest.raises(ImportError, match=r"quality-profiles\[interactive\]"):
        plot_quality_profiles_interactive(profile)
