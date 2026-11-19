# quality-profiles

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

Let $f_s^{(p)}$ be the best value found by solver $s$ on problem $p$,
$f^{(p)}(x_0^{(p)})$ the value at the starting point, and $f_L^{(p)}$ a reference value
(by default $\min_s f_s^{(p)}$). The **(weak) quality profile** of solver $s$ is

$$
Q_s(\tau) = \frac{1}{|P|}\,\mathrm{size}\Big\{p \in P :
f_s^{(p)} - f_L^{(p)} \le \tau\,\big(f^{(p)}(x_0^{(p)}) - f_L^{(p)}\big)\Big\},
\qquad \tau \in [0, 1].
$$

The **strong** quality profile (`strong=True`) replaces $f^{(p)}(x_0^{(p)})$ with
$\max_s f_s^{(p)}$. The package samples $[Q_s(\tau^{r_1})]^{r_2}$ for $\tau$ on a uniform
grid, where

* `r1 > 1` zooms in on high accuracy (precision levels close to 0), and `r1 < 1` zooms in
  near 1;
* `r2 > 1` stretches the ordinate near 0, and `r2 < 1` stretches it near 1.

The relative ranking of the solvers does not depend on `r1` or `r2`. The defaults are
`r1 = r2 = 1`.

How to read a profile:

* $Q_s(0)$ is the fraction of problems on which $s$ found the best value;
* $Q_s(1) < 1$ means $s$ failed, or ended above $f(x_0)$, on some problems;
* on a semilog plot, the value at $\tau = 10^{-k}$ is the fraction of problems on which
  $s$ reduced $f(x_0) - f_L$ by at least $k$ orders of magnitude;
* the higher the curve, the better the solver.

## API

| Function / class | Description |
| --- | --- |
| `quality_profiles(f0, f_solvers, *, solver_names, r1, r2, strong, f_ref, n_intervals)` | Compute the profiles; returns a `QualityProfile`. |
| `QualityProfile.tau`, `.precision`, `.values` | Uniform grid $\tau$, abscissa $\tau^{r_1}$ and values $[Q_s(\tau^{r_1})]^{r_2}$ (one column per solver). |
| `QualityProfile.evaluate(levels)` | Exact profile values at arbitrary precision levels. |
| `QualityProfile.area()` / `.ranking()` | Area under each profile, and solvers sorted by area. |
| `QualityProfile["name"]` | Values of one solver. |
| `plot_quality_profiles(profile, ax=None, *, logscale=True, style=None, ...)` | Matplotlib step plot. Colors and line styles follow the solver; `colors="paper"` uses the paper's red-to-blue colors. `style=` applies a matplotlib or SciencePlots style. |
| `plot_quality_profiles_interactive(profile, *, logscale=True, ...)` | Interactive Plotly figure with zoom, hover values and legend toggling (`[interactive]` extra). |
| `split_matrix(tt)` | Split a `P x (1+S)` matrix (`f0` column, then one column per solver), the layout of the MATLAB code. |
| `default_n_intervals(r1)` | Default grid size, `floor(max(1000, 1000*r1, 1000/r1))`. |

Notes on the inputs:

* A non-finite value in `f_solvers` is a failure. A solver that ends above `f0` is never
  credited on that problem.
* Failures count in the denominator $|P|$, so they keep the profile below 1.
* `f_ref` can hold reference values that do not depend on the solvers, for instance known
  optimal values. Each profile is then independent of the other solvers (Lemma 2.7 of the
  paper).
* A `ValueError` is raised if $f_L^{(p)} > f^{(p)}(x_0^{(p)})$ on some problem. On such a
  problem the profiles are not defined.

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
