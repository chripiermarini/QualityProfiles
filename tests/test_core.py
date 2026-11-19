from __future__ import annotations

import numpy as np
import pytest

from conftest import load_csv, reference_loop
from quality_profiles import (
    QualityProfile,
    default_n_intervals,
    quality_profiles,
    split_matrix,
)

# ---------------------------------------------------------------------------
# Agreement with the reference (MATLAB) algorithm
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("r1", "r2", "strong"),
    [(1, 1, False), (5, 1, False), (0.5, 2, False), (1, 1, True), (3, 0.5, True)],
)
def test_matches_reference_loop_on_random_data(random_problem, r1, r2, strong):
    f0, fs = random_problem
    fs = fs.copy()
    fs[::7, 1] = np.nan  # some failures
    qp = quality_profiles(f0, fs, r1=r1, r2=r2, strong=strong, n_intervals=200)
    # The grid follows the MATLAB formula up to rounding: vectorized and scalar
    # power functions may differ in the last bit, depending on the CPU.
    tau_ref, _ = reference_loop(f0, fs, r1=r1, r2=r2, strong=strong, n_intervals=200)
    np.testing.assert_allclose(qp.precision, tau_ref, rtol=1e-15, atol=0)
    # On the same grid, every counting decision is identical, bit for bit.
    _, q_ref = reference_loop(
        f0, fs, r1=r1, r2=r2, strong=strong, n_intervals=200, precision=qp.precision
    )
    np.testing.assert_array_equal(qp.values, q_ref)


@pytest.mark.parametrize(
    ("name", "r1", "r2"),
    [
        ("two_solvers", 4, 1),
        ("cutest_smooth", 1, 1),
        ("cutest_smooth", 5, 1),
        ("negative_curvature", 2, 1),
        ("dfo_budget_250n", 0.5, 1),
    ],
)
def test_matches_reference_loop_on_paper_data(name, r1, r2):
    f0, fs, names = load_csv(name)
    n = 300
    qp = quality_profiles(f0, fs, solver_names=names, r1=r1, r2=r2, n_intervals=n)
    _, q_ref = reference_loop(f0, fs, r1=r1, r2=r2, n_intervals=n, precision=qp.precision)
    np.testing.assert_array_equal(qp.values, q_ref)
    assert qp.solver_names == tuple(names)


def test_boundary_values_are_decided_exactly():
    # Ratios land exactly on (or within rounding of) grid points.
    n = 10
    f0 = np.full(n + 1, 3.0)
    fs = np.column_stack([np.arange(n + 1) * 0.3, np.zeros(n + 1)])
    qp = quality_profiles(f0, fs, n_intervals=n)
    _, q_ref = reference_loop(f0, fs, n_intervals=n, precision=qp.precision)
    np.testing.assert_array_equal(qp.values, q_ref)


# ---------------------------------------------------------------------------
# Basic semantics
# ---------------------------------------------------------------------------


def test_hand_computed_example():
    f0 = np.array([10.0, 10.0, 10.0])
    fs = np.array([[0.0, 1.0], [5.0, 0.0], [np.nan, 0.0]])
    qp = quality_profiles(f0, fs, solver_names=["A", "B"], n_intervals=10)
    np.testing.assert_allclose(qp["A"], [1 / 3] * 5 + [2 / 3] * 6)
    np.testing.assert_allclose(qp["B"], [2 / 3] + [1.0] * 10)
    np.testing.assert_allclose(
        qp.evaluate([0.0, 0.05, 0.1, 1.0]), [[1 / 3, 2 / 3], [1 / 3, 2 / 3], [1 / 3, 1], [2 / 3, 1]]
    )


def test_grid_and_shapes(random_problem):
    f0, fs = random_problem
    qp = quality_profiles(f0, fs)
    assert isinstance(qp, QualityProfile)
    assert qp.tau.shape == qp.precision.shape == (1001,)
    assert qp.values.shape == (1001, 3)
    assert qp.tau[0] == 0.0 and qp.tau[-1] == 1.0
    assert qp.n_problems == 100 and qp.n_solvers == 3
    assert qp.solver_names == ("Solver-1", "Solver-2", "Solver-3")


@pytest.mark.parametrize(("r1", "expected"), [(1, 1000), (5, 5000), (0.25, 4000), (2.5, 2500)])
def test_default_n_intervals(r1, expected):
    assert default_n_intervals(r1) == expected
    f0, fs = np.ones(2), np.zeros((2, 2))
    assert quality_profiles(f0, fs, r1=r1).tau.size == expected + 1


def _descent_data(rng):
    """Every solver ends below its starting value."""
    f0 = rng.random(100)
    return f0, f0[:, None] - rng.random((100, 3))


def test_profiles_reach_one_without_failures(rng):
    qp = quality_profiles(*_descent_data(rng))
    np.testing.assert_array_equal(qp.values[-1], 1.0)


def test_values_above_start_never_count(random_problem):
    f0, fs = random_problem
    qp = quality_profiles(f0, fs)
    np.testing.assert_allclose(qp.values[-1], (fs <= f0[:, None]).mean(axis=0))


def test_failures_keep_profile_below_one(rng):
    f0, fs = _descent_data(rng)
    fs[:10, 0] = np.nan
    fs[:5, 1] = np.inf
    qp = quality_profiles(f0, fs)
    assert qp.values[-1, 0] == pytest.approx(0.9)
    assert qp.values[-1, 1] == pytest.approx(0.95)
    assert qp.values[-1, 2] == 1.0


def test_value_at_zero_is_fraction_of_best_values():
    f0 = np.full(4, 5.0)
    fs = np.array([[1.0, 2.0], [1.0, 1.0], [3.0, 2.0], [0.0, 4.0]])
    qp = quality_profiles(f0, fs)
    np.testing.assert_allclose(qp.values[0], [3 / 4, 2 / 4])


def test_nan_start_value_never_counts():
    f0 = np.array([np.nan, 1.0])
    fs = np.zeros((2, 2))
    qp = quality_profiles(f0, fs)
    np.testing.assert_array_equal(qp.values[-1], [0.5, 0.5])


def test_flat_problem_counts_only_best_solver():
    # f0 == f_ref: only solvers reaching f_ref are credited, at every level.
    f0 = np.array([1.0])
    fs = np.array([[1.0, 1.0]])
    np.testing.assert_array_equal(quality_profiles(f0, fs).values, 1.0)


def test_one_dimensional_solver_array_is_one_solver():
    qp = quality_profiles([2.0, 2.0], [0.0, 1.0])
    assert qp.n_solvers == 1


def test_split_matrix():
    tt = np.array([[3.0, 1.0, 2.0], [4.0, 0.0, 0.5]])
    f0, fs = split_matrix(tt)
    np.testing.assert_array_equal(f0, [3.0, 4.0])
    np.testing.assert_array_equal(fs, [[1.0, 2.0], [0.0, 0.5]])
    with pytest.raises(ValueError, match="at least 2 columns"):
        split_matrix(np.ones((3, 1)))


# ---------------------------------------------------------------------------
# Properties proved in the paper
# ---------------------------------------------------------------------------


def test_nondecreasing_in_tau(random_problem):  # Lemma 2.3
    qp = quality_profiles(*random_problem, r1=3, r2=2)
    assert np.all(np.diff(qp.values, axis=0) >= 0)
    assert np.all((qp.values >= 0) & (qp.values <= 1))


@pytest.mark.parametrize("strong", [False, True])
def test_affine_invariance(rng, strong):  # Lemma 2.2
    # Integer data with a power-of-two scale keeps the transformation exact in floating point.
    fs = rng.integers(-50, 20, size=(60, 3)).astype(float)
    f0 = fs.max(axis=1) + rng.integers(0, 30, size=60)
    a, b = 4.0, -8.0
    q1 = quality_profiles(f0, fs, strong=strong, n_intervals=128)
    q2 = quality_profiles(a * f0 + b, a * fs + b, strong=strong, n_intervals=128)
    np.testing.assert_array_equal(q1.values, q2.values)


def test_ranking_invariant_to_r1_r2(random_problem):  # Lemma 2.6
    f0, fs = random_problem
    base = quality_profiles(f0, fs, n_intervals=64)
    for r1, r2 in [(1, 3), (1, 0.3)]:
        other = quality_profiles(f0, fs, r1=r1, r2=r2, n_intervals=64)
        np.testing.assert_array_equal(
            np.sign(base.values[:, :, None] - base.values[:, None, :]),
            np.sign(other.values[:, :, None] - other.values[:, None, :]),
        )
    # r1 only changes where tau is sampled: evaluating at the same precision gives the same Q.
    zoomed = quality_profiles(f0, fs, r1=4)
    levels = [1e-4, 1e-2, 0.3, 1.0]
    np.testing.assert_array_equal(zoomed.evaluate(levels), base.evaluate(levels))


def test_strong_profiles_use_worst_solver_value():
    f0 = np.array([100.0, 100.0])
    fs = np.array([[0.0, 1.0], [0.0, 2.0]])
    weak = quality_profiles(f0, fs)
    strong = quality_profiles(f0, fs, strong=True)
    # Strong: the worst solver sits at tau = 1 exactly.
    assert strong.evaluate([0.999])[0, 1] == 0.0
    assert strong.evaluate([1.0])[0, 1] == 1.0
    assert weak.evaluate([0.03])[0, 1] == 1.0


def test_user_reference_makes_profiles_independent(random_problem):  # Lemma 2.7
    f0, fs = random_problem
    f_ref = np.full(f0.shape, -3.5)
    full = quality_profiles(f0, fs, f_ref=f_ref)
    alone = quality_profiles(f0, fs[:, [0]], f_ref=f_ref)
    np.testing.assert_array_equal(full.values[:, 0], alone.values[:, 0])


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------


def test_area_and_ranking():
    f0 = np.full(2, 10.0)
    fs = np.array([[0.0, 1.0], [0.5, 0.0]])
    qp = quality_profiles(f0, fs, solver_names=["A", "B"])
    np.testing.assert_allclose(qp.area(), [0.5 * 0.05 + 0.95, 0.5 * 0.1 + 0.9], atol=1e-3)
    assert [name for name, _ in qp.ranking()] == ["A", "B"]


def test_paper_third_solver_ranks_first(random_problem):
    qp = quality_profiles(*random_problem)
    assert qp.ranking()[0][0] == "Solver-3"


def test_getitem():
    qp = quality_profiles([1.0, 1.0], [[0.0, 0.5], [0.0, 0.0]], solver_names=["x", "y"])
    np.testing.assert_array_equal(qp["y"], qp.values[:, 1])
    np.testing.assert_array_equal(qp[-1], qp.values[:, 1])
    with pytest.raises(KeyError):
        qp["z"]
    with pytest.raises(IndexError):
        qp[2]


def test_evaluate_preserves_input_order(random_problem):
    qp = quality_profiles(*random_problem)
    levels = np.array([0.5, 1e-3, 1.0, 0.0])
    out = qp.evaluate(levels)
    for i, lv in enumerate(levels):
        np.testing.assert_array_equal(out[i], qp.evaluate(lv)[0])
    with pytest.raises(ValueError, match="NaN"):
        qp.evaluate([np.nan])


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_reference_above_start_raises():
    f0 = np.array([0.0, 0.0])
    fs = np.array([[1.0, 2.0], [-1.0, 0.0]])
    with pytest.raises(ValueError, match=r"1 problem\(s\) \(row indices: 0\)"):
        quality_profiles(f0, fs)


def test_individual_solver_above_start_is_allowed():
    f0 = np.array([0.0])
    fs = np.array([[-1.0, 5.0]])
    qp = quality_profiles(f0, fs)
    assert qp.values[-1, 1] == 0.0


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"r1": 0}, ValueError, "r1"),
        ({"r2": -1}, ValueError, "r2"),
        ({"r1": np.inf}, ValueError, "r1"),
        ({"r1": "a"}, TypeError, "r1"),
        ({"n_intervals": 0}, ValueError, "n_intervals"),
        ({"n_intervals": 2.5}, ValueError, "n_intervals"),
        ({"solver_names": ["a"]}, ValueError, "solver names"),
        ({"solver_names": ["a", "a"]}, ValueError, "unique"),
        ({"solver_names": "ab"}, TypeError, "sequence"),
        ({"f_ref": [0.0]}, ValueError, "f_ref"),
    ],
)
def test_invalid_arguments(kwargs, error, match):
    with pytest.raises(error, match=match):
        quality_profiles([1.0, 1.0], [[0.0, 0.0], [0.0, 0.0]], **kwargs)


def test_shape_mismatch():
    with pytest.raises(ValueError, match="3 entries"):
        quality_profiles([1.0, 1.0, 1.0], np.zeros((2, 2)))
    with pytest.raises(ValueError, match="2-D"):
        quality_profiles([1.0], np.zeros((1, 1, 1)))
    with pytest.raises(ValueError, match="at least one"):
        quality_profiles([], np.zeros((0, 2)))


def test_inputs_are_not_modified(random_problem):
    f0, fs = random_problem
    f0c, fsc = f0.copy(), fs.copy()
    quality_profiles(f0, fs, strong=True)
    np.testing.assert_array_equal(f0, f0c)
    np.testing.assert_array_equal(fs, fsc)


def test_profile_is_immutable(random_problem):
    qp = quality_profiles(*random_problem)
    with pytest.raises(AttributeError):
        qp.r1 = 2.0  # type: ignore[misc]
