"""The :class:`QualityProfile` result class."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import ArrayLike

from .helpers import FloatArray, _count_successes

__all__ = ["QualityProfile"]


@dataclass(frozen=True, eq=False)
class QualityProfile:
    r"""Quality profiles of a set of solvers on a set of test problems.

    Instances are created by :func:`~quality_profiles.quality_profiles`. They are
    immutable: the attributes cannot be reassigned and the arrays are read-only
    (use ``.copy()`` to get a modifiable array). Two instances compare equal only
    if they are the same object.

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
