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

The package is split into:

* :mod:`.compute`: :func:`quality_profiles`, the main entry point;
* :mod:`.profile`: the :class:`QualityProfile` result class;
* :mod:`.helpers`: the sampling grid, :func:`split_matrix`, input validation and
  the counting algorithm.

Reference: G. Fasano, C. Piermarini, M. Roma, "Benchmarking Optimization
Algorithms with Quality Profiles and Test Set Profiles", arXiv:2607.16798.
"""

from .compute import quality_profiles
from .helpers import MAX_DEFAULT_INTERVALS, default_n_intervals, split_matrix
from .profile import QualityProfile

__all__ = [
    "MAX_DEFAULT_INTERVALS",
    "QualityProfile",
    "default_n_intervals",
    "quality_profiles",
    "split_matrix",
]
