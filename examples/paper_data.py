"""Load the results published with the paper (``examples/data/*.csv``).

Each file has one row per test problem: optionally the problem name (``problem``) and
its dimension (``n``), then the objective value at the starting point (``f0``), then one
column per solver. The example scripts import this module::

    from paper_data import load

    f0, f_solvers, names = load("cutest_smooth")            # all 166 problems
    f0, f_solvers, names = load("cutest_smooth", n=10000)   # only the n = 10000 instances
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent / "data"

__all__ = ["DATA", "dataset_names", "load", "problems"]


def dataset_names() -> list[str]:
    """Names of the available datasets, without the ``.csv`` extension."""
    return sorted(p.stem for p in DATA.glob("*.csv"))


def _read(name: str) -> tuple[list[str], list[list[str]]]:
    path = DATA / f"{name}.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"unknown dataset {name!r}; available: {', '.join(dataset_names())}"
        )
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    return rows[0], rows[1:]


def problems(name: str) -> tuple[list[str] | None, np.ndarray | None]:
    """Problem names and dimensions of a dataset, or ``(None, None)`` if not recorded."""
    header, rows = _read(name)
    names = [r[header.index("problem")] for r in rows] if "problem" in header else None
    dims = np.array([int(r[header.index("n")]) for r in rows]) if "n" in header else None
    return names, dims


def load(
    name: str, n: int | Iterable[int] | None = None
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Return ``(f0, f_solvers, solver_names)`` for one experiment of the paper.

    Parameters
    ----------
    name : str
        Dataset name, e.g. ``"cutest_smooth"`` (see :func:`dataset_names`).
    n : int or iterable of int, optional
        Keep only the problems with these dimensions, e.g. ``n=10000`` for the
        large-scale instances. Needs a dataset that records the dimension.
    """
    header, rows = _read(name)
    start = header.index("f0")
    values = np.array([[float(v) for v in r[start:]] for r in rows])
    f0, f_solvers, solver_names = values[:, 0], values[:, 1:], header[start + 1 :]
    if n is not None:
        _, dims = problems(name)
        if dims is None:
            raise ValueError(f"dataset {name!r} does not record the problem dimension")
        keep = np.isin(dims, [n] if isinstance(n, int) else list(n))
        if not keep.any():
            raise ValueError(
                f"no problem with n = {n} in {name!r}; dimensions: {sorted(set(dims))}"
            )
        f0, f_solvers = f0[keep], f_solvers[keep]
    return f0, f_solvers, solver_names
