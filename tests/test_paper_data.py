"""The paper datasets in examples/data and the loader used by the example scripts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture(scope="module")
def paper_data():
    spec = importlib.util.spec_from_file_location(
        "paper_data", EXAMPLES / "utils" / "paper_data.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SMOOTH = ["cutest_smooth", "negative_curvature"]
DFO = ["dfo_budget_1000n", "dfo_budget_750n", "dfo_budget_500n", "dfo_budget_250n"]


def test_datasets(paper_data):
    assert paper_data.dataset_names() == sorted(["two_solvers", *SMOOTH, *DFO])


@pytest.mark.parametrize(
    ("name", "rows", "solvers"),
    [
        ("two_solvers", 166, ["Solver-1", "Solver-2"]),
        ("cutest_smooth", 166, ["L-BFGS", "CG+", "TRON", "CG_DESCENT"]),
        ("negative_curvature", 166, ["TN-NONegCurv", "TN-NC1", "TN-NC2", "TN-NC3"]),
        ("dfo_budget_250n", 145, ["NEWUOA", "ALG1", "ALG2", "ALG4", "ALG6", "ALG7", "ALG8"]),
    ],
)
def test_shapes_and_solver_names(paper_data, name, rows, solvers):
    f0, f_solvers, names = paper_data.load(name)
    assert f0.shape == (rows,)
    assert f_solvers.shape == (rows, len(solvers))
    assert names == solvers


def test_smooth_problems_are_the_cutest_test_set(paper_data):
    problems, dims = paper_data.problems("cutest_smooth")
    assert len(problems) == 166 and len(set(problems)) == 60  # Table 1: 60 problems
    assert problems[:3] == ["ARWHEAD"] * 3 and dims[:3].tolist() == [1000, 5000, 10000]
    # both smooth experiments use the same problems, in the same order
    same_problems, same_dims = paper_data.problems("negative_curvature")
    assert same_problems == problems
    np.testing.assert_array_equal(same_dims, dims)


def test_dfo_problems_are_the_same_for_every_budget(paper_data):
    problems, dims = paper_data.problems(DFO[0])
    assert len(problems) == 145
    for name in DFO[1:]:
        other, other_dims = paper_data.problems(name)
        assert other == problems
        np.testing.assert_array_equal(other_dims, dims)
    # Table 2 of the paper: CRAGGLVY with n = 4, 10, 50, 100
    assert dims[[i for i, p in enumerate(problems) if p == "CRAGGLVY"]].tolist() == [4, 10, 50, 100]


def test_large_scale_subset(paper_data):
    # The reference scripts *_Figures_8_9_n_10000.m and *_Figure_10_n_10000.m use the
    # 45 instances with n = 10000 (the last instance of most problems in Table 1).
    full, full_solvers, _ = paper_data.load("cutest_smooth")
    _, dims = paper_data.problems("cutest_smooth")
    f0, f_solvers, names = paper_data.load("cutest_smooth", n=10000)
    assert f0.shape == (45,)
    assert names == ["L-BFGS", "CG+", "TRON", "CG_DESCENT"]
    rows = np.flatnonzero(dims == 10000)
    assert (rows[:6] + 1).tolist() == [3, 6, 9, 12, 15, 18]
    assert (rows[-3:] + 1).tolist() == [160, 163, 166]
    np.testing.assert_array_equal(f0, full[rows])
    np.testing.assert_array_equal(f_solvers, full_solvers[rows])


def test_dfo_n100_subset(paper_data):
    # The reference scripts *_Figure_11a..d_n_100.m use the 22 problems with n = 100.
    expected = [3, 5, 13, 20, 66, 75, 78, 80, 84, 87, 96, 100, 107, 108, 114, 120, 124, 128,
                131, 135, 140, 144]  # fmt: skip
    for name in DFO:
        full, full_solvers, _ = paper_data.load(name)
        f0, f_solvers, _ = paper_data.load(name, n=100)
        np.testing.assert_array_equal(f0, full[np.array(expected) - 1])
        np.testing.assert_array_equal(f_solvers, full_solvers[np.array(expected) - 1])


def test_several_dimensions(paper_data):
    f0, _, _ = paper_data.load("cutest_smooth", n=[1000, 10000])
    assert f0.shape == (44 + 45,)


def test_loader_errors(paper_data):
    with pytest.raises(FileNotFoundError, match="unknown dataset"):
        paper_data.load("nope")
    with pytest.raises(ValueError, match="no problem with n = 7"):
        paper_data.load("cutest_smooth", n=7)


def test_dataset_without_problem_columns(paper_data, tmp_path, monkeypatch):
    # Files with only f0 and the solvers (e.g. a user's own results) are supported.
    (tmp_path / "mine.csv").write_text("f0,A,B\n10,1,2\n5,0,0.5\n", encoding="utf-8")
    monkeypatch.setattr(paper_data, "DATA", tmp_path)
    f0, f_solvers, names = paper_data.load("mine")
    np.testing.assert_array_equal(f0, [10, 5])
    np.testing.assert_array_equal(f_solvers, [[1, 2], [0, 0.5]])
    assert names == ["A", "B"]
    assert paper_data.problems("mine") == (None, None)
    with pytest.raises(ValueError, match="does not record the problem dimension"):
        paper_data.load("mine", n=100)


def _run_script(path: Path, monkeypatch, argv=()):
    """Run a script as `python path` would: its own folder first on sys.path."""
    import runpy

    monkeypatch.syspath_prepend(str(path.parent))
    monkeypatch.setattr(sys, "argv", [str(path), *argv])
    return runpy.run_path(str(path), run_name="__main__")


def test_reproduce_paper_figures_runs(tmp_path, monkeypatch):
    _run_script(EXAMPLES / "reproduce_paper_figures.py", monkeypatch, [str(tmp_path)])
    assert len(list(tmp_path.glob("*.png"))) == 10


def test_readme_figure_script_runs(tmp_path, monkeypatch):
    import runpy

    script = EXAMPLES / "utils" / "make_readme_figure.py"
    monkeypatch.syspath_prepend(str(script.parent))
    module = runpy.run_path(str(script))  # not as __main__: redirect the output first
    out = tmp_path / "figure.png"
    module["main"].__globals__["OUT"] = out
    module["main"]()
    assert out.is_file()
