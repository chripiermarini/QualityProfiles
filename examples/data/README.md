# Results used in the paper

Each CSV file holds one experiment of arXiv:2607.16798. There is one row per test
problem. The first column, `f0`, is the objective value at the common starting point.
Each remaining column holds the best objective value found by one solver; the header
gives the solver name.

These files are not part of the installed package. They are used by
`examples/reproduce_paper_figures.py` and by the test suite.

| File | Problems | Solvers | Paper figures |
| --- | --- | --- | --- |
| `two_solvers.csv` | 166 | Solver-1, Solver-2 | 2 (`r1=10, r2=3`), 3 (`r1=4, r2=1`) |
| `cutest_smooth.csv` | 166 | L-BFGS, CG+, TRON, CG_DESCENT | 4 (`r1=1`), 5 (`r1=5`), 6–8 |
| `negative_curvature.csv` | 166 | TN-NONegCurv, TN-NC1, TN-NC2, TN-NC3 | 9–11 |
| `dfo_budget_1000n.csv` | 145 | NEWUOA, ALG1, ALG2, ALG4, ALG6, ALG7, ALG8 | 12 (budget 1000·n) |
| `dfo_budget_750n.csv` | 145 | same | 13 (budget 750·n) |
| `dfo_budget_500n.csv` | 145 | same | 14 (budget 500·n) |
| `dfo_budget_250n.csv` | 145 | same | 15 (budget 250·n) |

The smooth experiments use large-scale unconstrained CUTEst problems (Table 1 of the
paper). The derivative-free ones use the CUTEst selection of Table 2. In the DFO files,
ALG1, ALG2, ALG4, ALG6, ALG7 and ALG8 are COORD, COMPASS, H&J, SH&H, NM and SMD from
the Direct Search suite.

The values were extracted from the `TT` matrices of the MATLAB scripts that accompany
the paper (`Profiles_N_codes_v3_github_revised_*.m`). One correction was made: three
entries of the CG_DESCENT column of `cutest_smooth.csv` (rows 158–160, 1-based) are
written in Fortran overflow notation without the exponent letter (`0.2974667+125`,
`0.1559314+170`, `0.2864373+189`). MATLAB evaluates them as sums, giving about 125.3,
170.2 and 189.3. Here they are stored as the intended values `2.974667e124`,
`1.559314e169` and `2.864373e188`. These values are above `f0`, so they count as
failures of CG_DESCENT.
