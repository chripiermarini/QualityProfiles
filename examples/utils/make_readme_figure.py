"""Draw the figure shown at the top of the README.

Usage::

    uv run python examples/utils/make_readme_figure.py

It writes ``docs/assets/readme_profiles.png``: the smooth CUTEst experiment of the
paper (L-BFGS, CG+, TRON, CG_DESCENT on 166 problems) with ``r1 = 1`` and ``r1 = 5``.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from paper_data import load

from quality_profiles import plot_quality_profiles, quality_profiles

OUT = Path(__file__).resolve().parents[2] / "docs" / "assets" / "readme_profiles.png"


def main() -> None:
    f0, f_solvers, names = load("cutest_smooth")

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), layout="constrained")
    for ax, r1, label in zip(axes, (1, 5), ("low accuracy", "high accuracy"), strict=True):
        qp = quality_profiles(f0, f_solvers, solver_names=names, r1=r1)
        plot_quality_profiles(qp, ax, title=f"r1 = {r1}: {label}", legend=False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside right center", frameon=False, handlelength=3.2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=160)
    print(f"written {OUT}")


if __name__ == "__main__":
    main()
