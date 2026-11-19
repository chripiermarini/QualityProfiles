from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

DATA_DIR = Path(__file__).resolve().parents[1] / "examples" / "data"


def reference_loop(f0, fs, r1=1.0, r2=1.0, strong=False, n_intervals=None):
    """Line-by-line port of the reference MATLAB implementation (no vectorization)."""
    f0 = np.array(f0, dtype=float)
    fs = np.asarray(fs, dtype=float)
    n_problems, n_solvers = fs.shape
    if n_intervals is None:
        n_intervals = int(np.floor(max(1000, 1000 * r1, 1000 / r1)))
    stepsize = 1 / n_intervals
    if strong:
        for i in range(n_problems):
            row = fs[i][~np.isnan(fs[i])]
            f0[i] = row.max() if row.size else np.nan
    f_star = np.empty(n_problems)
    for p in range(n_problems):
        row = fs[p][~np.isnan(fs[p])]
        f_star[p] = row.min() if row.size else np.nan
    tau = np.empty(n_intervals + 1)
    q = np.empty((n_intervals + 1, n_solvers))
    for s in range(n_solvers):
        for t in range(n_intervals + 1):
            tau[t] = (t * stepsize) ** r1
            counter = 0
            for w in range(n_problems):
                if (
                    not np.isnan(f0[w])
                    and not np.isnan(fs[w, s])
                    and (fs[w, s] - f_star[w]) <= tau[t] * (f0[w] - f_star[w])
                ):
                    counter += 1
            q[t, s] = (counter / n_problems) ** r2
    return tau, q


def load_csv(name):
    path = DATA_DIR / f"{name}.csv"
    header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    return data[:, 0], data[:, 1:], header[1:]


@pytest.fixture
def rng():
    return np.random.default_rng(12345)


@pytest.fixture
def random_problem(rng):
    """Synthetic data used in Section 4 of the paper (100 problems, 3 solvers)."""
    n = 100
    f0 = -1 + 2 * rng.random(n)
    fs = np.column_stack(
        [-2 + 2 * rng.random(n), -2.01 + 2 * rng.random(n), -3.0 + 2 * rng.random(n)]
    )
    return f0, fs
