# Notebooks: the figures of the paper

Each notebook draws a group of quality-profile figures of

> G. Fasano, C. Piermarini, M. Roma. *Benchmarking Optimization Algorithms with Quality
> Profiles.* Mathematical Programming Computation (accepted),
> [arXiv:2607.16798](https://arxiv.org/abs/2607.16798).

The data and the parameters `r1` and `r2` are those of the MATLAB scripts of the
reference repository [fasano-g/Quality-Profiles](https://github.com/fasano-g/Quality-Profiles),
so the output of the two implementations can be compared figure by figure.

| Notebook | Figures | Experiment | MATLAB scripts |
| --- | --- | --- | --- |
| [`01_first_example.ipynb`](01_first_example.ipynb) | 2, 3 | two solvers, `r1 = 10, r2 = 3` and `r1 = 4, r2 = 1`; also with SciencePlots and Plotly | `*_Figures_2_3.m` |
| [`02_smooth_solvers.ipynb`](02_smooth_solvers.ipynb) | 4, 5, 8, 9 | L-BFGS, CG+, TRON, CG_DESCENT | `*_Figures_4_5.m`, `*_Figures_8_9_n_10000.m` |
| [`03_negative_curvature.ipynb`](03_negative_curvature.ipynb) | 6, 10 | truncated Newton with negative curvature | `*_Figure_6.m`, `*_Figure_10_n_10000.m` |
| [`04_derivative_free.ipynb`](04_derivative_free.ipynb) | 7, 11 | derivative-free solvers, four budgets | `*_Figure_7a..d.m`, `*_Figure_11a..d_n_100.m` |

Open them in Jupyter or VS Code from inside the repository (they read `examples/data`).
To execute them all, as the CI does:

```bash
uv run pytest --nbmake notebooks
```
