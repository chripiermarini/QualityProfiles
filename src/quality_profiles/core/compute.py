"""The main entry point: :func:`quality_profiles`."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import ArrayLike

from .helpers import (
    _as_arrays,
    _as_reference,
    _check_exponent,
    _check_intervals,
    _count_successes,
    _nan_reduce,
    _solver_names,
)
from .profile import QualityProfile

__all__ = ["quality_profiles"]


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
        :func:`default_n_intervals` of ``r1``; for ``r1 > 1000`` or
        ``r1 < 0.001`` that would exceed :data:`MAX_DEFAULT_INTERVALS`, and an
        explicit value is required. An explicit value is never capped.

    Returns
    -------
    QualityProfile
        The sampled profiles together with the parameters used.

    Raises
    ------
    ValueError
        If the inputs have inconsistent shapes, the exponents are not positive,
        the default grid would be too large (see ``n_intervals``), or
        :math:`f_L^{(p)} > f^{(p)}(x_0^{(p)})` on some problem (e.g. every
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
