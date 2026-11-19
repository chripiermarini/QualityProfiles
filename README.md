# quality-profiles

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/chripiermarini/QualityProfiles?style=flat&logo=github)](https://github.com/chripiermarini/QualityProfiles/stargazers)
[![Tests](https://github.com/chripiermarini/QualityProfiles/actions/workflows/ci.yml/badge.svg)](https://github.com/chripiermarini/QualityProfiles/actions/workflows/ci.yml)
[![Lint](https://github.com/chripiermarini/QualityProfiles/actions/workflows/lint.yml/badge.svg)](https://github.com/chripiermarini/QualityProfiles/actions/workflows/lint.yml)
[![Coverage](https://codecov.io/gh/chripiermarini/QualityProfiles/branch/main/graph/badge.svg)](https://codecov.io/gh/chripiermarini/QualityProfiles)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python&logoColor=white)](pyproject.toml)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](.github/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/quality-profiles?logo=pypi&logoColor=white)](https://pypi.org/project/quality-profiles/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/quality-profiles?label=PyPI%20downloads)](https://pypi.org/project/quality-profiles/)
[![Conda version](https://img.shields.io/conda/vn/conda-forge/quality-profiles?logo=anaconda&logoColor=white)](https://anaconda.org/conda-forge/quality-profiles)
[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/quality-profiles?label=conda%20downloads)](https://anaconda.org/conda-forge/quality-profiles)
[![Docs](https://img.shields.io/badge/docs-markdown-informational)](docs/)
[![Paper](https://img.shields.io/badge/arXiv-2607.16798-b31b1b.svg)](https://arxiv.org/abs/2607.16798)

**Quality profiles** for benchmarking optimization algorithms by the *quality* of the
solutions they return, in Python.

Performance and data profiles measure how much effort a solver needs. Quality
profiles measure something else: how good the final objective values are,
relative to a common starting point and a reference value, over the whole range
of precision levels. They need no a priori thresholds. They handle failures, and
solvers converging to different local minimizers, so no test problem has to be
excluded.

This package implements the method introduced in

> G. Fasano, C. Piermarini, M. Roma.
> *Benchmarking Optimization Algorithms with Quality Profiles and Test Set Profiles.*
> Mathematical Programming Computation (accepted). [arXiv:2607.16798](https://arxiv.org/abs/2607.16798)

It is a Python port of the authors' reference MATLAB code
([fasano-g/Quality-Profiles](https://github.com/fasano-g/Quality-Profiles)). On the same
grid it gives exactly the same values, and it runs much faster.

## Installation

```bash
pip install quality-profiles
# or, in a uv project
uv add quality-profiles
```

Requirements: Python ≥ 3.10, NumPy and Matplotlib.

Two optional extras add other ways to draw the profiles:

```bash
pip install "quality-profiles[science]"      # SciencePlots styles, for figures in papers
pip install "quality-profiles[interactive]"  # Plotly, for interactive exploration
pip install "quality-profiles[all]"          # both
```

## Quick start

For every test problem `p` you need the objective value at the common starting
point, `f0[p]`, and the best value found by each solver, `f_solvers[p, s]`.
Use `NaN` to mark a failure.

```python
import numpy as np
import matplotlib.pyplot as plt
from quality_profiles import quality_profiles, plot_quality_profiles

f0 = np.array([10.0, 3.0, 50.0, 7.0])           # f(x0) on 4 problems
f_solvers = np.array([                           # 3 solvers
    [1e-8,  2e-3,  0.5],
    [0.0,   1e-6,  1e-12],
    [12.0,  1e-4,  np.nan],                      # nan = failure
    [1e-3,  1e-3,  1e-9],
])

qp = quality_profiles(f0, f_solvers, solver_names=["A", "B", "C"], r1=4)

plot_quality_profiles(qp)      # semilog plot of [Q_s(tau^r1)]^r2
plt.show()

qp.evaluate([1e-1, 1e-3, 1e-6])  # fraction solved to 1, 3 and 6 orders of magnitude
qp.ranking()                     # solvers sorted by area under the profile
```

For a figure in a paper, or for interactive exploration:

```python
ax = plot_quality_profiles(qp, style=["science", "ieee"])  # needs the [science] extra
ax.figure.savefig("profiles.pdf")

from quality_profiles import plot_quality_profiles_interactive
fig = plot_quality_profiles_interactive(qp)            # needs the [interactive] extra
fig.show()                                             # zoom, hover, hide solvers
fig.write_html("profiles.html")
```

See [`notebooks/quality_profiles_example.ipynb`](notebooks/quality_profiles_example.ipynb)
for a walk-through of the paper's examples on the published results.

## What is computed

For every solver $s$ and precision level $\tau \in [0, 1]$, the quality profile
$Q_s(\tau)$ is the fraction of test problems on which $s$ reduced the gap between the
starting value $f(x_0)$ and a reference value $f_L$ (by default the best value found by
any solver) by at least a factor $\tau$. The package computes the scaled profiles
$[Q_s(\tau^{r_1})]^{r_2}$: `r1` zooms the abscissa, `r2` the ordinate, and neither changes
the ranking of the solvers.

On a semilog plot, the value at precision $10^{-k}$ is the fraction of problems on which
a solver gained at least $k$ orders of magnitude; the higher the curve, the better.

The definitions, weak and strong profiles, the choice of reference value, the scaling,
the properties proved in the paper and the handling of failures are described in
[**docs/what-is-computed.md**](docs/what-is-computed.md).

## API

| Function / class | Description |
| --- | --- |
| `quality_profiles(f0, f_solvers, ...)` | Compute the profiles; returns a `QualityProfile`. |
| `QualityProfile` | Sampled profiles, with `evaluate(levels)`, `area()` and `ranking()`. |
| `plot_quality_profiles(profile, ...)` | Matplotlib step plot, optionally with a matplotlib or SciencePlots `style`. |
| `plot_quality_profiles_interactive(profile, ...)` | Interactive Plotly figure (`[interactive]` extra). |
| `split_matrix(tt)` | Split a MATLAB-style `P x (1+S)` results matrix into `f0` and `f_solvers`. |

Every parameter, return value and error is documented in [**docs/api.md**](docs/api.md).

## Reproducing the paper's figures

`examples/data` contains the results used in the paper, one CSV file per experiment.
To redraw the quality-profile figures from them:

```bash
uv run python examples/reproduce_paper_figures.py
```

See [`examples/data/README.md`](examples/data/README.md) for a description of each file.

Two more scripts show the optional plot styles on the same data (they need the `[all]`
extra, which the development environment already includes):

```bash
uv run python examples/compare_plot_styles.py               # one figure, four looks
uv run python examples/try_plot_styles.py --r1 5             # every dataset, SciencePlots and Plotly
uv run python examples/try_plot_styles.py --help             # all options
```

## Development

The project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync                          # create the environment with the dev tools
uv run pytest                    # unit tests and doctests
uv run pytest --nbmake notebooks # execute the example notebook
uv run ruff check . && uv run ruff format --check .
uv run mypy                      # strict type checking
uv build                         # build the sdist and the wheel into dist/
```

## Citing

If you use this package, please cite the paper (see [`CITATION.cff`](CITATION.cff)):

```bibtex
@article{FasanoPiermariniRoma2026QualityProfiles,
  title   = {Benchmarking Optimization Algorithms with Quality Profiles and Test Set Profiles},
  author  = {Fasano, Giovanni and Piermarini, Christian and Roma, Massimo},
  journal = {Mathematical Programming Computation},
  note    = {Accepted. arXiv:2607.16798},
  year    = {2026}
}
```

## License

MIT. See [LICENSE](LICENSE).
