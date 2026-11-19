r"""Quality profiles for benchmarking optimization algorithms.

Quality profiles compare solvers by the *quality* (objective value) of the
solutions they return, relative to a common starting point and a reference
value, over the whole range of precision levels :math:`\tau \in [0, 1]`.

Reference: G. Fasano, C. Piermarini, M. Roma, "Benchmarking Optimization
Algorithms with Quality Profiles and Test Set Profiles", arXiv:2607.16798.

Examples
--------
>>> import numpy as np
>>> from quality_profiles import quality_profiles
>>> f0 = np.array([10.0, 10.0])
>>> fs = np.array([[0.0, 1.0], [0.5, 0.0]])
>>> qp = quality_profiles(f0, fs, solver_names=["A", "B"])
>>> [name for name, _ in qp.ranking()]
['A', 'B']
"""

from importlib.metadata import PackageNotFoundError, version

from .core import QualityProfile, default_n_intervals, quality_profiles, split_matrix
from .interactive import plot_quality_profiles_interactive
from .plotting import PALETTE, default_colors, paper_colors, plot_quality_profiles

try:
    __version__ = version("quality-profiles")
except PackageNotFoundError:  # pragma: no cover - running from a source tree
    __version__ = "0.0.0"

__all__ = [
    "PALETTE",
    "QualityProfile",
    "__version__",
    "default_colors",
    "default_n_intervals",
    "paper_colors",
    "plot_quality_profiles",
    "plot_quality_profiles_interactive",
    "quality_profiles",
    "split_matrix",
]
