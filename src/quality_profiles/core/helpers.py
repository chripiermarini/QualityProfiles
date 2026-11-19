"""Helpers: sampling grid, input handling and the counting algorithm."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray

__all__ = [
    "MAX_DEFAULT_INTERVALS",
    "FloatArray",
    "default_n_intervals",
    "split_matrix",
]

FloatArray = NDArray[np.float64]

_BASE_INTERVALS = 1000

MAX_DEFAULT_INTERVALS = 1_000_000
"""Largest grid chosen automatically, reached for ``r1 = 1000`` or ``r1 = 0.001``.

Beyond it :func:`~quality_profiles.quality_profiles` asks for an explicit
``n_intervals`` instead of silently allocating a huge grid (``r1 = 10**6`` would
need a billion points).
"""


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def default_n_intervals(r1: float) -> int:
    r"""Return the default number of sampling intervals of ``tau`` for a given ``r1``.

    With ``r1 = 1`` the interval :math:`[0, 1]` is split into 1000 equal parts.
    For ``r1 != 1`` the samples :math:`\tau^{r_1}` are no longer equally spaced,
    so the number of intervals is increased to ``1000 * r1`` (``r1 > 1``) or
    ``1000 / r1`` (``r1 < 1``) to partially compensate for the uneven density.

    Parameters
    ----------
    r1 : float
        Positive abscissa scaling exponent.

    Returns
    -------
    int
        ``floor(max(1000, 1000 * r1, 1000 / r1))``.

    Raises
    ------
    ValueError
        If ``r1`` is so extreme that the formula overflows.
    """
    r1 = _check_exponent(r1, "r1")
    n = max(_BASE_INTERVALS, _BASE_INTERVALS * r1, _BASE_INTERVALS / r1)
    if not math.isfinite(n):
        raise ValueError(f"r1 = {r1!r} is too extreme to choose a sampling grid")
    return math.floor(n)


def split_matrix(matrix: ArrayLike) -> tuple[FloatArray, FloatArray]:
    """Split a ``P x (1 + S)`` results matrix into ``(f0, f_solvers)``.

    This matches the layout of the ``TT`` matrix used by the reference MATLAB
    code: the first column holds the objective value at the starting point,
    the remaining ``S`` columns hold the best value found by each solver.

    Parameters
    ----------
    matrix : array_like, shape (P, 1 + S)
        Results matrix.

    Returns
    -------
    f0 : ndarray, shape (P,)
        Objective values at the starting points.
    f_solvers : ndarray, shape (P, S)
        Best objective values found by the solvers.
    """
    tt = np.asarray(matrix, dtype=np.float64)
    if tt.ndim != 2 or tt.shape[1] < 2:
        raise ValueError(
            "expected a 2-D matrix with at least 2 columns (f0 and one solver), "
            f"got shape {tt.shape}"
        )
    return tt[:, 0].copy(), tt[:, 1:].copy()


# ---------------------------------------------------------------------------
# Counting algorithm (used by quality_profiles and QualityProfile.evaluate)
# ---------------------------------------------------------------------------


def _count_successes(
    levels: FloatArray, gap_solvers: FloatArray, gap_start: FloatArray
) -> FloatArray:
    """Count the problems solved by each solver at each (sorted) level.

    Problem ``p`` is solved by solver ``s`` at level ``t`` when
    ``gap_solvers[p, s] <= t * gap_start[p]``.

    The test is monotone in ``t`` (``gap_start >= 0``), so for each problem and
    solver it suffices to find the first level at which it holds. The search is
    done on the ratio and then corrected so that the decision is exactly the
    floating-point inequality above.
    """
    n_levels = levels.size
    n_problems, n_solvers = gap_solvers.shape
    first = np.full((n_problems, n_solvers), n_levels, dtype=np.intp)

    start = np.broadcast_to(gap_start[:, None], gap_solvers.shape)
    valid = np.isfinite(gap_solvers) & np.isfinite(start)

    # Degenerate problems with f0 == f_ref: solved at every level iff f_s == f_ref.
    flat = valid & (start == 0)
    first[flat & (gap_solvers <= 0)] = 0

    regular = valid & (start > 0)
    if np.any(regular) and n_levels:
        g = gap_solvers[regular]
        d = start[regular]
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            k = np.searchsorted(levels, g / d, side="left").astype(np.intp)
        # Fix off-by-rounding decisions so the result matches `g <= level * d` exactly.
        while True:
            down = (k > 0) & (g <= levels[np.maximum(k - 1, 0)] * d)
            if not down.any():
                break
            k[down] -= 1
        while True:
            up = (k < n_levels) & ~(g <= levels[np.minimum(k, n_levels - 1)] * d)
            if not up.any():
                break
            k[up] += 1
        first[regular] = k

    counts = np.empty((n_levels, n_solvers), dtype=np.float64)
    for s in range(n_solvers):
        hist = np.bincount(first[:, s], minlength=n_levels + 1)[:n_levels]
        counts[:, s] = np.cumsum(hist)
    return counts


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def _as_arrays(f0: ArrayLike, f_solvers: ArrayLike) -> tuple[FloatArray, FloatArray]:
    start = np.asarray(f0, dtype=np.float64)
    solvers = np.asarray(f_solvers, dtype=np.float64)
    if solvers.ndim == 1:
        solvers = solvers[:, None]
    if solvers.ndim != 2:
        raise ValueError(
            f"f_solvers must be a 2-D array of shape (P, S), got shape {solvers.shape}"
        )
    if start.ndim != 1:
        start = start.reshape(-1) if start.ndim == 2 and 1 in start.shape else start
    if start.ndim != 1:
        raise ValueError(f"f0 must be a 1-D array of shape (P,), got shape {np.shape(f0)}")
    if start.shape[0] != solvers.shape[0]:
        raise ValueError(
            f"f0 has {start.shape[0]} entries but f_solvers has {solvers.shape[0]} rows (problems)"
        )
    if solvers.shape[0] == 0 or solvers.shape[1] == 0:
        raise ValueError("at least one problem and one solver are required")
    solvers = np.where(np.isfinite(solvers), solvers, np.nan)
    start = np.where(np.isfinite(start), start, np.nan)
    return start, solvers


def _as_reference(f_ref: ArrayLike, n_problems: int) -> FloatArray:
    reference = np.asarray(f_ref, dtype=np.float64).reshape(-1)
    if reference.shape != (n_problems,):
        raise ValueError(f"f_ref must have shape ({n_problems},), got shape {np.shape(f_ref)}")
    return np.where(np.isfinite(reference), reference, np.nan)


def _nan_reduce(reducer: object, solvers: FloatArray) -> FloatArray:
    """Row-wise min/max ignoring NaN (all-NaN rows give NaN), without warnings."""
    return np.asarray(reducer(solvers, axis=1), dtype=np.float64)  # type: ignore[operator]


def _solver_names(names: Sequence[str] | None, n_solvers: int) -> tuple[str, ...]:
    if names is None:
        return tuple(f"Solver-{i + 1}" for i in range(n_solvers))
    if isinstance(names, str):
        raise TypeError("solver_names must be a sequence of strings, not a single string")
    result = tuple(str(n) for n in names)
    if len(result) != n_solvers:
        raise ValueError(f"got {len(result)} solver names for {n_solvers} solvers")
    if len(set(result)) != len(result):
        raise ValueError("solver names must be unique")
    return result


def _check_intervals(n_intervals: int | None, r1: float) -> int:
    if n_intervals is None:
        n = default_n_intervals(r1)
        if n > MAX_DEFAULT_INTERVALS:
            raise ValueError(
                f"r1 = {r1:g} would need a grid of {n:,} intervals (the default grows "
                f"with r1 and 1/r1, up to {MAX_DEFAULT_INTERVALS:,}); pass n_intervals "
                "explicitly, e.g. n_intervals=100_000"
            )
        return n
    try:
        valid = not isinstance(n_intervals, bool) and int(n_intervals) == n_intervals >= 1
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        raise ValueError(f"n_intervals must be a positive integer, got {n_intervals!r}")
    return int(n_intervals)


def _check_exponent(value: float, name: str) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise TypeError(f"{name} must be a real number, got {value!r}") from None
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f"{name} must be a positive finite number, got {value!r}")
    return x
