# Results used in the paper

Each CSV file holds one experiment of arXiv:2607.16798. There is one row per test
problem, with the columns:

* `problem`, `n`: the CUTEst problem and its dimension;
* `f0`: the objective value at the common starting point;
* one column per solver, with the best objective value it found; the header gives the
  solver name.

These files are not part of the installed package. They are read with
[`examples/paper_data.py`](../paper_data.py), which is used by the example scripts and
the test suite:

```python
from paper_data import load

f0, f_solvers, names = load("cutest_smooth")            # all 166 problems
f0, f_solvers, names = load("cutest_smooth", n=10000)   # the 45 instances with n = 10000
```

| File | Problems | Solvers | Paper figures |
| --- | --- | --- | --- |
| `cutest_smooth.csv` | 166 | L-BFGS, CG+, TRON, CG_DESCENT | 4 (`r1=1`), 5 (`r1=5`), 6–8 |
| `negative_curvature.csv` | 166 | TN-NONegCurv, TN-NC1, TN-NC2, TN-NC3 | 9–11 |
| `dfo_budget_1000n.csv` | 145 | NEWUOA, ALG1, ALG2, ALG4, ALG6, ALG7, ALG8 | 12 (budget 1000·n) |
| `dfo_budget_750n.csv` | 145 | same | 13 (budget 750·n) |
| `dfo_budget_500n.csv` | 145 | same | 14 (budget 500·n) |
| `dfo_budget_250n.csv` | 145 | same | 15 (budget 250·n) |

Figure numbers refer to version 1 of the arXiv preprint.

The smooth experiments use large-scale unconstrained CUTEst problems (Table 1 of the
paper). The derivative-free ones use the CUTEst selection of Table 2. In the DFO files,
ALG1, ALG2, ALG4, ALG6, ALG7 and ALG8 are COORD, COMPASS, H&J, SH&H, NM and SMD from
the Direct Search suite.

## Subsets of the test sets

The reference MATLAB repository also compares the solvers on part of the test sets:
`*_Figures_8_9_n_10000.m` and `*_Figure_10_n_10000.m` use the 45 smooth instances with
`n = 10000`, and `*_Figure_11a..d_n_100.m` the 22 derivative-free problems with
`n = 100`. Their data are rows of the files above, so they are not stored separately:
`load(name, n=10000)` and `load(name, n=100)` give exactly the same matrices (checked by
the test suite).

## Where the data come from

The objective values come from the `TT` matrices of the MATLAB scripts in the reference
repository ([fasano-g/Quality-Profiles](https://github.com/fasano-g/Quality-Profiles),
`Profiles_N_codes_v3_github_revised_*.m`). The problem names and dimensions come from the
raw result files of the same repository (`Section2-SmoothOptimization/` and
`Section3-DerivativeFreeOptimization/`); rows were matched by their starting values and,
where available, by the solvers' results.

One correction was made: three entries of the CG_DESCENT column of `cutest_smooth.csv`
(problem VARDIM with n = 1000, 5000 and 10000, rows 158–160) are written in Fortran
overflow notation without the exponent letter (`0.2974667+125`,
`0.1559314+170`, `0.2864373+189`). MATLAB evaluates them as sums, giving about 125.3,
170.2 and 189.3. Here they are stored as the intended values `2.974667e124`,
`1.559314e169` and `2.864373e188`. These values are above `f0`, so they count as
failures of CG_DESCENT.

## Known issues in the original data

* **Rounded values in the smooth experiment.** In the `TT` matrix of
  `*_Figures_4_5.m`, and therefore in `cutest_smooth.csv`, the solvers' final values are
  rounded to three significant digits (e.g. `3.98E+03`), while the raw solver outputs
  in `Section2-SmoothOptimization/Section2.2.1/` give seven digits (`0.3983818E+04`). The
  files here keep the values used in the paper.
* **Starting value of CRAGGLVY with n = 50 (derivative-free files).** In
  `MatricePuntiIniziali.txt` the row of CRAGGLVY with `n = 50` repeats the row with
  `n = 10`, including its starting value `3303.567`. All the solver tables, and Table 2
  of the paper, have `n = 50` for that problem, which is the dimension stored here; its
  `f0` is still the one of the `n = 10` problem, as in the paper.
