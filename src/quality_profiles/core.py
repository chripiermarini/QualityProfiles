r"""Computation of quality profiles.

Given a set of test problems :math:`P` and a set of solvers :math:`S`, the
(weak) quality profile of solver :math:`s` is

.. math::

    Q_s(\tau) = \frac{1}{|P|}\,
    \mathrm{size}\left\{ p \in P :
    f_s^{(p)} - f_L^{(p)} \le \tau \left( f^{(p)}(x_0^{(p)}) - f_L^{(p)} \right)
    \right\},
    \qquad \tau \in [0, 1],

where :math:`f_s^{(p)}` is the best objective value found by solver :math:`s`
on problem :math:`p`, :math:`f^{(p)}(x_0^{(p)})` is the objective value at the
common starting point and :math:`f_L^{(p)}` is a reference value (by default
the best value found by any solver). *Strong* quality profiles replace
:math:`f^{(p)}(x_0^{(p)})` with the worst value found by any solver.

The scaled version plotted in practice is :math:`[Q_s(\tau^{r_1})]^{r_2}`,
where ``r1`` zooms the abscissa and ``r2`` zooms the ordinate.

Reference: G. Fasano, C. Piermarini, M. Roma, "Benchmarking Optimization
Algorithms with Quality Profiles and Test Set Profiles", arXiv:2607.16798.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import ArrayLike, NDArray

__all__ = [
    "QualityProfile",
    "default_n_intervals",
    "quality_profiles",
    "split_matrix",
]

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.intp]

_BASE_INTERVALS = 1000


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
    """
    r1 = _check_exponent(r1, "r1")
    return math.floor(max(_BASE_INTERVALS, _BASE_INTERVALS * r1, _BASE_INTERVALS / r1))


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


@dataclass(frozen=True, eq=False)
class QualityProfile:
    r"""Quality profiles of a set of solvers on a set of test problems.

    Instances are created by :func:`quality_profiles`. They are immutable: the
    attributes cannot be reassigned and the arrays are read-only (use
    ``.copy()`` to get a modifiable array). Two instances compare equal only if
    they are the same object.

    Attributes
    ----------
    tau : ndarray, shape (T,)
        Equally spaced samples of the parameter :math:`\tau \in [0, 1]`.
    precision : ndarray, shape (T,)
        Precision levels :math:`\tau^{r_1}` actually tested, i.e. the abscissa
        of the plot.
    values : ndarray, shape (T, S)
        Scaled profiles :math:`[Q_s(\tau^{r_1})]^{r_2}`; column ``s`` belongs to
        ``solver_names[s]``.
    solver_names : tuple of str
        Names of the solvers, in column order.
    n_problems : int
        Number of test problems :math:`|P|` (failures included).
    r1, r2 : float
        Abscissa and ordinate scaling exponents.
    strong : bool
        ``True`` for strong quality profiles, ``False`` for weak ones.
    """

    tau: FloatArray
    precision: FloatArray
    values: FloatArray
    solver_names: tuple[str, ...]
    n_problems: int
    r1: float
    r2: float
    strong: bool
    # Normalization data kept to evaluate the profiles exactly at arbitrary points.
    _gap_solvers: FloatArray = field(repr=False, compare=False)
    _gap_start: FloatArray = field(repr=False, compare=False)

    @property
    def n_solvers(self) -> int:
        """Number of solvers :math:`|S|`."""
        return len(self.solver_names)

    def __getitem__(self, solver: str | int) -> FloatArray:
        """Return the profile values of one solver, selected by name or column index."""
        return self.values[:, self._column(solver)]

    def evaluate(self, precision: ArrayLike) -> FloatArray:
        r"""Evaluate the scaled profiles exactly at the given precision levels.

        This does not interpolate on the sampling grid: the counts are recomputed
        from the data, so e.g. ``evaluate([1e-1, 1e-2, 1e-3])`` gives the
        fraction of problems (raised to ``r2``) on which each solver reduced
        :math:`f(x_0) - f_L` by at least 1, 2 and 3 orders of magnitude.

        Parameters
        ----------
        precision : array_like
            Precision levels :math:`\tau^{r_1}`; values are not restricted to
            :math:`[0, 1]` but are meaningful there.

        Returns
        -------
        ndarray, shape (len(precision), S)
            :math:`[Q_s(\cdot)]^{r_2}` at each requested level.
        """
        levels = np.atleast_1d(np.asarray(precision, dtype=np.float64))
        if levels.ndim != 1:
            raise ValueError("precision must be a scalar or a 1-D array")
        if np.any(np.isnan(levels)):
            raise ValueError("precision must not contain NaN")
        order = np.argsort(levels, kind="stable")
        counts = _count_successes(levels[order], self._gap_solvers, self._gap_start)
        out = np.empty_like(counts, dtype=np.float64)
        out[order] = (counts / self.n_problems) ** self.r2
        return out

    def area(self) -> FloatArray:
        r"""Area under each profile, as a scalar summary for ranking solvers.

        The area is computed with the trapezoidal rule with respect to the
        equally spaced parameter :math:`\tau \in [0, 1]`, i.e. it approximates
        :math:`\int_0^1 [Q_s(\tau^{r_1})]^{r_2}\, d\tau`. Choosing ``r1 > 1``
        therefore weighs high-accuracy levels more (see Observation 2.9 of the
        paper). The larger the area, the better the solver.

        Returns
        -------
        ndarray, shape (S,)
            One value in :math:`[0, 1]` per solver.
        """
        y = self.values
        dx = np.diff(self.tau)
        return np.asarray(((y[1:] + y[:-1]) * 0.5 * dx[:, None]).sum(axis=0), dtype=np.float64)

    def ranking(self) -> list[tuple[str, float]]:
        """Solvers sorted by decreasing :meth:`area`.

        Returns
        -------
        list of (str, float)
            Pairs ``(solver_name, area)``, best solver first. Ties keep the
            original column order.
        """
        areas = self.area()
        order = np.argsort(-areas, kind="stable")
        return [(self.solver_names[i], float(areas[i])) for i in order]

    def _column(self, solver: str | int) -> int:
        if isinstance(solver, str):
            try:
                return self.solver_names.index(solver)
            except ValueError:
                raise KeyError(f"unknown solver {solver!r}") from None
        index = int(solver)
        if not -self.n_solvers <= index < self.n_solvers:
            raise IndexError(f"solver index {solver} out of range for {self.n_solvers} solvers")
        return index % self.n_solvers


def quality_profiles(
    f0: ArrayLike,
    f_solvers: ArrayLike,
    *,
    solver_names: Sequence[str] | None = None,
    r1: float = 1.0,
    r2: float = 1.0,
    strong: bool = False,
    f_ref: ArrayLike | None = None,
    n_intervals: int | None = None,
) -> QualityProfile:
    r"""Compute the quality profiles :math:`[Q_s(\tau^{r_1})]^{r_2}` of a set of solvers.

    Parameters
    ----------
    f0 : array_like, shape (P,)
        Objective value at the common starting point :math:`x_0^{(p)}` of each
        test problem. Ignored when ``strong=True``. A NaN marks a problem that
        no solver is credited with.
    f_solvers : array_like, shape (P, S)
        Best objective value found by each solver (columns) on each problem
        (rows). Use NaN (or any non-finite value) to mark a failure: the
        problem then never counts as solved by that solver, so its profile
        stays below 1.
    solver_names : sequence of str, optional
        Names of the ``S`` solvers. Defaults to ``"Solver-1"``, ``"Solver-2"``, ...
    r1 : float, default 1.0
        Positive abscissa scaling exponent. ``r1 > 1`` zooms in near precision
        0 (high accuracy), ``r1 < 1`` zooms in near precision 1.
    r2 : float, default 1.0
        Positive ordinate scaling exponent. ``r2 > 1`` zooms in near 0,
        ``r2 < 1`` zooms in near 1. The relative ranking of the solvers does
        not depend on ``r1`` and ``r2``.
    strong : bool, default False
        If ``True`` compute strong quality profiles, replacing ``f0`` with the
        worst value found by any solver on each problem.
    f_ref : array_like, shape (P,), optional
        Reference values :math:`f_L^{(p)}`. Defaults to the best value found by
        any solver on each problem. Providing values that do not depend on the
        solvers makes each profile independent of the other solvers.
    n_intervals : int, optional
        Number of equal intervals used to sample :math:`\tau \in [0, 1]`
        (the grid has ``n_intervals + 1`` points). Defaults to
        :func:`default_n_intervals` of ``r1``.

    Returns
    -------
    QualityProfile
        The sampled profiles together with the parameters used.

    Raises
    ------
    ValueError
        If the inputs have inconsistent shapes, the exponents are not positive,
        or :math:`f_L^{(p)} > f^{(p)}(x_0^{(p)})` on some problem (e.g. every
        solver ended above the starting value), in which case the profiles are
        not defined.

    Examples
    --------
    >>> import numpy as np
    >>> f0 = np.array([10.0, 10.0, 10.0])
    >>> fs = np.array([[0.0, 1.0], [5.0, 0.0], [np.nan, 0.0]])
    >>> qp = quality_profiles(f0, fs, solver_names=["A", "B"], n_intervals=10)
    >>> qp.evaluate([0.0, 0.5, 1.0]).round(3).tolist()
    [[0.333, 0.667], [0.667, 1.0], [0.667, 1.0]]
    """
    r1 = _check_exponent(r1, "r1")
    r2 = _check_exponent(r2, "r2")
    start, solvers = _as_arrays(f0, f_solvers)
    n_problems, n_solvers = solvers.shape
    names = _solver_names(solver_names, n_solvers)

    if strong:
        start = _nan_reduce(np.fmax.reduce, solvers)
    reference = (
        _nan_reduce(np.fmin.reduce, solvers) if f_ref is None else _as_reference(f_ref, n_problems)
    )

    bad = np.flatnonzero(reference > start)  # NaN comparisons are False
    if bad.size:
        shown = ", ".join(str(i) for i in bad[:10]) + (", ..." if bad.size > 10 else "")
        raise ValueError(
            "the reference value f_ref exceeds the starting value f0 on "
            f"{bad.size} problem(s) (row indices: {shown}); quality profiles are not defined"
        )

    n_intervals = _check_intervals(n_intervals, r1)

    tau = np.arange(n_intervals + 1, dtype=np.float64) * (1.0 / n_intervals)
    precision = tau**r1

    gap_solvers = solvers - reference[:, None]
    gap_start = start - reference
    counts = _count_successes(precision, gap_solvers, gap_start)
    values = (counts / n_problems) ** r2
    for array in (tau, precision, values, gap_solvers, gap_start):
        array.flags.writeable = False

    return QualityProfile(
        tau=tau,
        precision=precision,
        values=values,
        solver_names=names,
        n_problems=n_problems,
        r1=r1,
        r2=r2,
        strong=bool(strong),
        _gap_solvers=gap_solvers,
        _gap_start=gap_start,
    )


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
        return default_n_intervals(r1)
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
