# Contributing to Quality Profiles

Thank you for your interest in Quality Profiles! Questions, bug reports, ideas and code
are all very welcome, whether you are benchmarking your own solvers, teaching
optimization, or working on the method itself.

## Asking a question or reporting a problem

Open an [issue](https://github.com/chripiermarini/QualityProfiles/issues). There is no
need to be sure that something is a bug: questions about the method, the results or the
API are welcome too.

For a bug, it helps to include:

* what you ran, ideally a short script that reproduces the problem (small arrays for
  `f0` and `f_solvers` are usually enough);
* what you expected and what happened, with the full error message if there is one;
* your versions of Python, `quality-profiles`, NumPy and Matplotlib, and your operating
  system.

## Proposing a change

Small fixes (typos, documentation, a clearer error message) can go straight to a pull
request. For larger changes, such as a new feature or a change in behaviour, please open
an issue first, so that we can agree on the approach before you invest time in it.

## Setting up the development environment

The project uses [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/chripiermarini/QualityProfiles
cd QualityProfiles
uv sync          # .venv with the package, Plotly, SciencePlots and the dev tools
```

## Checks

Before opening a pull request, run:

```bash
uv run pytest                      # unit tests and doctests
uv run pytest --nbmake notebooks   # the notebooks of the paper's figures
uv run ruff check .                # lint
uv run ruff format .               # format (the style is the same as Black)
uv run mypy                        # strict type checking
```

The same checks run on GitHub Actions, on Linux, macOS and Windows, for Python 3.10,
3.12 and 3.14.

## Guidelines

* **Tests.** Every change in behaviour comes with a test, and every bug fix with a test
  that fails without the fix.
* **Faithfulness to the method.** The results must stay exactly those of the reference
  MATLAB implementation; the tests compare them with a line-by-line port of the MATLAB
  loops (`tests/conftest.py`). If a change is meant to alter the results, explain why
  in the pull request.
* **Style.** Code is formatted with `ruff format` and fully type-annotated. Public
  functions have docstrings in the [NumPy style](https://numpydoc.readthedocs.io/en/latest/format.html),
  with a short example when useful.
* **Dependencies.** The core package depends only on NumPy and Matplotlib. Anything else
  goes into an optional extra (as Plotly and SciencePlots do), imported only when used,
  with a clear message if it is missing.
* **Documentation.** Update [`api.md`](api.md) or [`what-is-computed.md`](what-is-computed.md)
  when you change the public API or the behaviour, and the notebooks when they are
  affected.
* **Data.** The files in `examples/data` hold the results published with the paper:
  please do not change their values. See [`examples/data/README.md`](../examples/data/README.md).
* **Figures.** The images in `docs/assets` are drawn by the scripts in
  `examples/utils/`; regenerate them with those scripts rather than editing them by hand.

## Pull requests

* Keep each pull request focused on one change, with a description of what it does and
  why.
* Write commit messages in the imperative mood, with a short first line (for example
  "Fix the legend position with seven solvers").
* Make sure the checks above pass.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](../LICENSE) of the project.
