"""Reproduce the quality-profile figures of the paper from the bundled result files.

Usage::

    uv run python examples/reproduce_paper_figures.py [output_dir]

The result files in ``examples/data`` hold, for every test problem, the
objective value at the starting point (column ``f0``) followed by the best value
found by each solver. Figures are written as PNG files to ``output_dir``
(default: ``examples/figures``).

Figure numbers follow arXiv:2607.16798.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from quality_profiles import plot_quality_profiles, quality_profiles

DATA_DIR = Path(__file__).resolve().parent / "data"

# (figure id, dataset, r1, r2, logscale)
FIGURES = [
    ("fig02", "two_solvers", 10, 3, True),
    ("fig03", "two_solvers", 4, 1, True),
    ("fig04", "cutest_smooth", 1, 1, True),
    ("fig05", "cutest_smooth", 5, 1, True),
    ("fig08", "cutest_smooth", 1, 1, False),
    ("fig09", "negative_curvature", 1, 1, True),
]

# Figures 12-15: derivative-free solvers, one figure per budget, three values of r1.
DFO_FIGURES = [
    ("fig12", "dfo_budget_1000n"),
    ("fig13", "dfo_budget_750n"),
    ("fig14", "dfo_budget_500n"),
    ("fig15", "dfo_budget_250n"),
]


def load(name: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Load a result file as ``(f0, f_solvers, solver_names)``."""
    path = DATA_DIR / f"{name}.csv"
    names = path.read_text(encoding="utf-8").splitlines()[0].split(",")[1:]
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    return data[:, 0], data[:, 1:], names


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    for fig_id, dataset, r1, r2, logscale in FIGURES:
        f0, fs, names = load(dataset)
        qp = quality_profiles(f0, fs, solver_names=names, r1=r1, r2=r2)
        ax = plot_quality_profiles(qp, logscale=logscale, title=f"{dataset}: r1={r1}, r2={r2}")
        ax.figure.savefig(out_dir / f"{fig_id}_{dataset}.png", dpi=150)
        plt.close(ax.figure)
        print(f"{fig_id}: ranking by area ->", ", ".join(n for n, _ in qp.ranking()))

    for fig_id, dataset in DFO_FIGURES:
        f0, fs, names = load(dataset)
        fig, axes = plt.subplots(3, 1, figsize=(8, 13), layout="constrained")
        for ax, r1 in zip(axes, (5, 1, 0.2), strict=True):
            qp = quality_profiles(f0, fs, solver_names=names, r1=r1)
            plot_quality_profiles(qp, ax, title=f"{dataset}: r1={r1}, r2=1")
        fig.savefig(out_dir / f"{fig_id}_{dataset}.png", dpi=150)
        plt.close(fig)
        print(f"{fig_id}: written")


if __name__ == "__main__":
    default = Path(__file__).resolve().parent / "figures"
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else default)
