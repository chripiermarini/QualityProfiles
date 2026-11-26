# Changelog

All notable changes to Quality Profiles are listed here. The project follows
[semantic versioning](https://semver.org).

## 1.1.0

### Plotting

* `plot_quality_profiles` and `plot_quality_profiles_interactive` accept `steps=False`
  to join the grid points with straight segments, as the reference MATLAB code does,
  instead of drawing step functions (the default, and the exact shape of a profile).

### Examples

* One notebook per group of figures of the paper (`notebooks/01_first_example.ipynb` to
  `04_derivative_free.ipynb`), with the same data, `r1` and `r2` as the reference MATLAB
  scripts. They replace `quality_profiles_example.ipynb`.
* Figure numbers now follow the paper accepted in Mathematical Programming Computation,
  in `examples/reproduce_paper_figures.py` and in the documentation of the data.
* `examples/data/two_solvers.csv` is back: it is the data of Figures 2 and 3, taken from
  the MATLAB script `*_Figures_2_3.m`.

## 1.0.0

First public release.

### Quality profiles

* `quality_profiles(f0, f_solvers, ...)` computes weak and strong quality profiles,
  with the scaling exponents `r1` and `r2`, solver-independent reference values
  (`f_ref`) and a configurable sampling grid. On the same grid the results are
  identical to the reference MATLAB implementation.
* `QualityProfile` holds the sampled profiles, with exact evaluation at any precision
  level (`evaluate`), the area under each profile (`area`) and the ranking of the
  solvers by area (`ranking`).
* `split_matrix` reads results stored like the `TT` matrix of the MATLAB code.

### Plots

* `plot_quality_profiles` draws step plots with matplotlib, with colors and line styles
  that follow each solver and stay distinguishable without color. It also supports any
  matplotlib style, including the SciencePlots ones (`quality-profiles[science]`), and
  legends outside the axes.
* `plot_quality_profiles_interactive` draws interactive Plotly figures with zoom, hover
  values and legend toggling (`quality-profiles[interactive]`).

### Examples and documentation

* The results published with the paper, with problem names and dimensions, in
  `examples/data`, and scripts that reproduce the paper's figures.
* An example notebook, an API reference, a description of what is computed, and
  contributing guidelines.
