"""Reproduce the quality-profile figures of the paper from the bundled result files.

Usage::

    uv run python examples/reproduce_paper_figures.py [output_dir]

The result files in ``examples/data`` hold, for every test problem, the objective
value at the starting point followed by the best value found by each solver (see
``utils/paper_data.py``). One PNG file per figure is written to ``output_dir`` (default:
``examples/figures``).

Figure numbers follow the paper accepted in Mathematical Programming Computation, as
do the names of the MATLAB scripts of the reference repository
(``Profiles_N_codes_v3_github_revised_Figure*.m``). The notebooks in ``notebooks/``
show the same figures one by one.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from utils.paper_data import load

from quality_profiles import plot_quality_profiles, quality_profiles

# (figure, dataset, problem dimension or None for all, r1, r2)
SINGLE_PANEL = [
    ("fig02", "two_solvers", None, 10, 3),
    ("fig03", "two_solvers", None, 4, 1),
    ("fig04", "cutest_smooth", None, 1, 1),
    ("fig05", "cutest_smooth", None, 5, 1),
    ("fig06", "negative_curvature", None, 1, 1),
    # The same experiments restricted to the 45 smooth problems with n = 10000.
    ("fig08", "cutest_smooth", 10000, 1, 1),
    ("fig09", "cutest_smooth", 10000, 5, 1),
    ("fig10", "negative_curvature", 10000, 1, 1),
]

# Derivative-free solvers, one panel per budget: (a) 1000n, (b) 750n, (c) 500n, (d) 250n.
# (figure, problem dimension or None for all)
DFO_FIGURES = [("fig07", None), ("fig11", 100)]
DFO_BUDGETS = ["1000n", "750n", "500n", "250n"]


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for fig_id, dataset, n, r1, r2 in SINGLE_PANEL:
        f0, fs, names = load(dataset, n=n)
        qp = quality_profiles(f0, fs, solver_names=names, r1=r1, r2=r2)
        title = f"{dataset}, {len(f0)} problems: r1 = {r1}, r2 = {r2}"
        ax = plot_quality_profiles(qp, colors="paper", title=title, legend_loc="lower right")
        ax.figure.savefig(out_dir / f"{fig_id}_{dataset}.png", dpi=150)
        plt.close(ax.figure)
        print(f"{fig_id}: ranking by area ->", ", ".join(s for s, _ in qp.ranking()))

    for fig_id, n in DFO_FIGURES:
        fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained")
        for k, (ax, budget) in enumerate(zip(axes.flat, DFO_BUDGETS, strict=True)):
            f0, fs, names = load(f"dfo_budget_{budget}", n=n)
            qp = quality_profiles(f0, fs, solver_names=names)
            plot_quality_profiles(
                qp,
                ax,
                colors="paper",
                title=f"({'abcd'[k]}) budget {budget}, {len(f0)} problems: r1 = 1, r2 = 1",
                legend=k == 0,
                legend_loc="outside right center",
            )
        fig.savefig(out_dir / f"{fig_id}_derivative_free.png", dpi=150)
        plt.close(fig)
        print(f"{fig_id}: written")


if __name__ == "__main__":
    default = Path(__file__).resolve().parent / "figures"
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else default)
