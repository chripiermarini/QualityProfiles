# API reference

Everything listed here is importable from the top-level package:

```python
from quality_profiles import quality_profiles, plot_quality_profiles
```

For the definitions behind these functions, see [What is computed](what-is-computed.md).

| Name | Kind | Summary |
| --- | --- | --- |
| [`quality_profiles`](#quality_profiles) | function | Compute the profiles; returns a `QualityProfile`. |
| [`QualityProfile`](#qualityprofile) | class | The sampled profiles, with exact evaluation, area and ranking. |
| [`plot_quality_profiles`](#plot_quality_profiles) | function | Matplotlib step plot, optionally with a matplotlib or SciencePlots style. |
| [`plot_quality_profiles_interactive`](#plot_quality_profiles_interactive) | function | Interactive Plotly figure (`[interactive]` extra). |
| [`split_matrix`](#split_matrix) | function | Split a MATLAB-style `P x (1+S)` results matrix. |
| [`default_n_intervals`](#default_n_intervals) | function | Default number of sampling intervals for a given `r1`. |
| [`default_colors`, `paper_colors`, `PALETTE`](#colors) | functions, constant | Default and paper color schemes. |

## Computing profiles

### `quality_profiles`

```python
quality_profiles(
    f0, f_solvers, *,
    solver_names=None, r1=1.0, r2=1.0, strong=False, f_ref=None, n_intervals=None,
) -> QualityProfile
```

Compute the quality profiles $[Q_s(\tau^{r_1})]^{r_2}$ of a set of solvers.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `f0` | array, shape `(P,)` | | Objective value at the common starting point of each problem. Ignored when `strong=True`. A `NaN` marks a problem on which no solver is credited. |
| `f_solvers` | array, shape `(P, S)` | | Best value found by each solver (columns) on each problem (rows). `NaN` or any non-finite value marks a failure. A 1-D array is read as a single solver. |
| `solver_names` | sequence of str | `"Solver-1"`, `"Solver-2"`, ... | Names of the solvers. They must be unique. |
| `r1` | float > 0 | `1.0` | Abscissa scaling. `r1 > 1` zooms in on high accuracy, `r1 < 1` zooms in near precision 1. |
| `r2` | float > 0 | `1.0` | Ordinate scaling. `r2 > 1` stretches the ordinate near 0, `r2 < 1` near 1. |
| `strong` | bool | `False` | Compute strong profiles: `f0` is replaced by the worst value found by any solver. |
| `f_ref` | array, shape `(P,)` | best value of any solver | Reference values $f_L^{(p)}$. Values that do not depend on the solvers make each profile independent of the others. |
| `n_intervals` | int > 0 | [`default_n_intervals(r1)`](#default_n_intervals) | Number of equal intervals sampling $\tau \in [0, 1]$; the grid has `n_intervals + 1` points. |

**Returns** a [`QualityProfile`](#qualityprofile).

**Raises**

* `ValueError` if the shapes are inconsistent, `r1` or `r2` is not a positive finite
  number, `n_intervals` is not a positive integer, the solver names are not unique or do
  not match the number of solvers, or $f_L^{(p)} > f^{(p)}(x_0^{(p)})$ on some problem. In
  the last case the message lists the offending rows.
* `TypeError` if `r1` or `r2` is not a number, or `solver_names` is a single string.

The inputs are never modified.

```python
>>> import numpy as np
>>> f0 = np.array([10.0, 10.0, 10.0])
>>> fs = np.array([[0.0, 1.0], [5.0, 0.0], [np.nan, 0.0]])
>>> qp = quality_profiles(f0, fs, solver_names=["A", "B"], n_intervals=10)
>>> qp.evaluate([0.0, 0.5, 1.0]).round(3).tolist()
[[0.333, 0.667], [0.667, 1.0], [0.667, 1.0]]
```

### `QualityProfile`

Immutable result of [`quality_profiles`](#quality_profiles): the attributes cannot be
reassigned and the arrays are read-only (call `.copy()` on an array to modify it). Two
profiles compare equal only if they are the same object, and profiles can be used in sets
and as dictionary keys.

| Attribute | Type | Description |
| --- | --- | --- |
| `tau` | array, shape `(T,)` | Equally spaced samples of $\tau \in [0, 1]$. |
| `precision` | array, shape `(T,)` | Precision levels $\tau^{r_1}$: the abscissa of the plot. |
| `values` | array, shape `(T, S)` | Scaled profiles $[Q_s(\tau^{r_1})]^{r_2}$; column `s` belongs to `solver_names[s]`. |
| `solver_names` | tuple of str | Names of the solvers, in column order. |
| `n_solvers` | int | Number of solvers $\lvert S \rvert$. |
| `n_problems` | int | Number of test problems $\lvert P \rvert$, failures included. |
| `r1`, `r2` | float | Scaling exponents used. |
| `strong` | bool | Whether the profiles are strong. |

| Method | Returns | Description |
| --- | --- | --- |
| `evaluate(precision)` | array, shape `(len(precision), S)` | Exact values $[Q_s(\cdot)]^{r_2}$ at any precision levels, recomputed from the data rather than interpolated. At $10^{-k}$ it gives the fraction of problems on which each solver gained at least $k$ orders of magnitude. Raises `ValueError` for `NaN` levels. |
| `area()` | array, shape `(S,)` | Area under each profile, with respect to $\tau$ (trapezoidal rule). Larger is better; `r1 > 1` weighs high accuracy more. |
| `ranking()` | list of `(name, area)` | Solvers sorted by decreasing area; ties keep the column order. |
| `profile[name]` or `profile[index]` | array, shape `(T,)` | Values of one solver, by name or column index. Raises `KeyError` or `IndexError`. |

```python
qp["TRON"]                      # values of one solver
qp.evaluate([1e-1, 1e-3, 1e-6]) # fractions at 1, 3 and 6 orders of magnitude
qp.ranking()                    # [("TRON", 0.976), ("CG+", 0.948), ...]
```

## Plotting

### `plot_quality_profiles`

```python
plot_quality_profiles(
    profile, ax=None, *,
    logscale=True, solvers=None, colors=None, linestyles=None, linewidth=None,
    reference_lines=None, legend=True, legend_loc="best", title=None, grid=None,
    style=None,
) -> matplotlib.axes.Axes
```

Draw the profiles as step functions against the precision $\tau^{r_1}$. Each solver
keeps the same color and line style, also when only some of the solvers are drawn.

| Parameter | Default | Description |
| --- | --- | --- |
| `profile` | | A [`QualityProfile`](#qualityprofile). |
| `ax` | new figure | Axes to draw on. Leave it out to create a figure, which is needed for `style` and for outside legends. |
| `logscale` | `True` | Logarithmic abscissa (recommended). The point $\tau = 0$ is left out. Axes shorter than about one decade show plain tick numbers. |
| `solvers` | all | Subset of solvers to draw, by name or column index. |
| `colors` | `default_colors`, or the style's colors | One color per solver of the profile, in column order. `"paper"` uses the red-to-blue colors of the paper. |
| `linestyles` | `DEFAULT_LINESTYLES` | Line styles, assigned in column order. With a style that defines at least one line style per solver, the style's are used. |
| `linewidth` | 2, or the style's | Width of the lines. |
| `reference_lines` | `(1e-3, 1e-2, 1e-1)` on a linear axis, none on a log axis | Abscissae of dashed vertical guides. `()` disables them. |
| `legend` | `True` | Draw a legend with the solver names. |
| `legend_loc` | `"best"` | Legend position. Values starting with `"outside"`, such as `"outside right center"`, put the legend next to the axes. |
| `title` | none | Axes title. |
| `grid` | light grid, or the style's choice | Draw a grid. |
| `style` | none | A matplotlib style or list of styles, used instead of the package's look: for example `"ggplot"`, `"science"` or `["science", "ieee"]`. The SciencePlots styles need the `[science]` extra. If `"science"` is used and LaTeX is not installed, `"no-latex"` is added automatically. The style applies to this figure only. |

**Returns** the matplotlib axes. Save the figure with `ax.figure.savefig(...)`: the
format follows the extension (`.pdf`, `.svg`, `.png`, ...). For a paper, prefer PDF.

**Raises** `ValueError` for too few colors or an unknown color scheme, and for an outside
legend on axes without a layout engine. Raises `ImportError`, with the install command,
if a SciencePlots style is requested without the package.

```python
ax = plot_quality_profiles(qp, title="r1 = 5")
ax = plot_quality_profiles(qp, solvers=["TRON", "CG+"], logscale=False)
ax = plot_quality_profiles(qp, style=["science", "ieee"], legend_loc="outside right center")
ax.figure.savefig("profiles.pdf")
```

### `plot_quality_profiles_interactive`

```python
plot_quality_profiles_interactive(
    profile, *,
    logscale=True, solvers=None, colors=None, linewidth=2.0, reference_lines=None,
    title=None, height=420, width=None,
) -> plotly.graph_objects.Figure
```

Interactive version of the plot: drag to zoom, double-click to reset, click a legend
entry to hide a solver, and hover to read the value of every solver at a precision
level. Requires the `[interactive]` extra (Plotly).

The parameters `logscale`, `solvers`, `colors`, `linewidth`, `reference_lines` and
`title` mean the same as for [`plot_quality_profiles`](#plot_quality_profiles); colors
must be CSS colors. `height` and `width` are in pixels; by default the width follows the
container.

Each step curve is reduced to its jump points before drawing, so the figure is identical
to the full curve but much smaller.

**Returns** a Plotly figure. Show it with `fig.show()`, or save it with
`fig.write_html("profiles.html")`. With `include_plotlyjs="cdn"` the file is small but
needs a network connection to open. Static images (`fig.write_image`) need the
additional `kaleido` package.

**Raises** `ImportError`, with the install command, if Plotly is missing; `ValueError`
for too few colors or an unknown color scheme.

## Helpers

### `split_matrix`

```python
split_matrix(matrix) -> tuple[ndarray, ndarray]
```

Split a `P x (1 + S)` results matrix into `(f0, f_solvers)`. This is the layout of the
`TT` matrix of the reference MATLAB code: the first column holds the starting values,
the other columns hold one solver each. Raises `ValueError` if the matrix is not 2-D
with at least two columns.

### `default_n_intervals`

```python
default_n_intervals(r1) -> int
```

Default number of sampling intervals, `floor(max(1000, 1000 * r1, 1000 / r1))`. See
[Sampling](what-is-computed.md#sampling).

### Colors

| Name | Description |
| --- | --- |
| `PALETTE` | The eight default colors, in a fixed order chosen so that neighbouring colors stay distinguishable with color-vision deficiencies. |
| `default_colors(n)` | The first `n` colors of `PALETTE`; beyond eight they repeat. |
| `paper_colors(n)` | `n` colors fading from red to blue, as in the paper's figures. |

The default line styles are distinct for up to eight solvers, so the curves can be told
apart without color, for example in print.

## Optional extras

| Extra | Installs | Enables |
| --- | --- | --- |
| `quality-profiles[science]` | SciencePlots | `plot_quality_profiles(..., style="science")` and the other SciencePlots styles |
| `quality-profiles[interactive]` | Plotly | `plot_quality_profiles_interactive` |
| `quality-profiles[all]` | both | everything |
