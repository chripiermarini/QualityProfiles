"""Reproduce the quality-profile figures of the paper from the bundled result files.

Usage::

    uv run python examples/reproduce_paper_figures.py [output_dir]

The result files in ``examples/data`` hold, for every test problem, the objective
value at the starting point followed by the best value found by each solver (see
``paper_data.py``). Figures are written as PNG files to ``output_dir`` (default:
``examples/figures``).

Figure numbers follow arXiv:2607.16798 (v1). The last figures restrict the test sets
to the largest smooth problems (n = 10000) and to the derivative-free problems with
n = 100, as in the scripts ``*_Figures_8_9_n_10000.m``, ``*_Figure_10_n_10000.m`` and
``*_Figure_11a..d_n_100.m`` of the reference MATLAB repository.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from paper_data import load

from quality_profiles import plot_quality_profiles, quality_profiles

# (output name, dataset, problem dimension or None for all, r1, r2, logscale)
FIGURES = [
    ("fig04", "cutest_smooth", None, 1, 1, True),
    ("fig05", "cutest_smooth", None, 5, 1, True),
    ("fig08", "cutest_smooth", None, 1, 1, False),
    ("fig09", "negative_curvature", None, 1, 1, True),
    # Subsets of the smooth test set: only the n = 10000 instances (45 problems).
    ("smooth_n10000_r1", "cutest_smooth", 10000, 1, 1, True),
    ("smooth_n10000_r5", "cutest_smooth", 10000, 5, 1, True),
    ("negative_curvature_n10000", "negative_curvature", 10000, 1, 1, True),
]

# Figures 12-15: derivative-free solvers, one figure per budget, three values of r1.
DFO_FIGURES = [
    ("fig12", "dfo_budget_1000n"),
    ("fig13", "dfo_budget_750n"),
    ("fig14", "dfo_budget_500n"),
    ("fig15", "dfo_budget_250n"),
]

DFO_BUDGETS = ["1000n", "750n", "500n", "250n"]


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for fig_id, dataset, n, r1, r2, logscale in FIGURES:
        f0, fs, names = load(dataset, n=n)
        qp = quality_profiles(f0, fs, solver_names=names, r1=r1, r2=r2)
        subset = "" if n is None else f", n = {n} ({len(f0)} problems)"
        ax = plot_quality_profiles(
            qp, logscale=logscale, title=f"{dataset}{subset}: r1={r1}, r2={r2}"
        )
        ax.figure.savefig(out_dir / f"{fig_id}_{dataset}.png", dpi=150)
        plt.close(ax.figure)
        print(f"{fig_id}: ranking by area ->", ", ".join(s for s, _ in qp.ranking()))

    for fig_id, dataset in DFO_FIGURES:
        f0, fs, names = load(dataset)
        fig, axes = plt.subplots(3, 1, figsize=(9, 13), layout="constrained")
        for k, (ax, r1) in enumerate(zip(axes, (5, 1, 0.2), strict=True)):
            qp = quality_profiles(f0, fs, solver_names=names, r1=r1)
            # one legend for the three panels, next to them: with seven solvers a
            # legend inside the axes covers the curves
            plot_quality_profiles(
                qp,
                ax,
                title=f"{dataset}: r1={r1}, r2=1",
                legend=k == 0,
                legend_loc="outside right center",
            )
        fig.savefig(out_dir / f"{fig_id}_{dataset}.png", dpi=150)
        plt.close(fig)
        print(f"{fig_id}: written")

    # Derivative-free solvers on the n = 100 problems (22 problems), one panel per budget.
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout="constrained", sharex=True, sharey=True)
    for k, (ax, budget) in enumerate(zip(axes.flat, DFO_BUDGETS, strict=True)):
        f0, fs, names = load(f"dfo_budget_{budget}", n=100)
        qp = quality_profiles(f0, fs, solver_names=names, r1=1)
        plot_quality_profiles(
            qp,
            ax,
            title=f"budget {budget}, n = 100 ({len(f0)} problems): r1=1, r2=1",
            legend=k == 0,
            legend_loc="outside right center",
        )
    fig.savefig(out_dir / "dfo_n100_all_budgets.png", dpi=150)
    plt.close(fig)
    print("dfo_n100: written")


if __name__ == "__main__":
    default = Path(__file__).resolve().parent / "figures"
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else default)
