"""Compare the plot styles on one figure: package default, SciencePlots and Plotly.

Needs the optional extras (already in the dev environment created by ``uv sync``):
``pip install "quality-profiles[all]"``.

Usage::

    uv run python examples/compare_plot_styles.py                          # paper Fig. 5
    uv run python examples/compare_plot_styles.py negative_curvature --r1 4 --r2 2

It writes ``examples/figures/style_comparison.html`` and opens it in the browser.
The page shows the same quality profiles drawn four ways:

A. the package's default style (``plot_quality_profiles``);
B. SciencePlots "science", sized for one journal column;
C. SciencePlots "science" + "ieee", which also works in black and white;
D. the interactive Plotly figure (``plot_quality_profiles_interactive``).
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import webbrowser
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from quality_profiles import (
    plot_quality_profiles,
    plot_quality_profiles_interactive,
    quality_profiles,
)

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "figures"


def load(name: str):
    """Return (f0, f_solvers, solver_names) for one of the paper's experiments."""
    path = DATA / f"{name}.csv"
    names = path.read_text(encoding="utf-8").splitlines()[0].split(",")[1:]
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    return data[:, 0], data[:, 1:], names


def png(fig, dpi: int) -> str:
    """Encode a matplotlib figure as an <img> tag."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi)
    plt.close(fig)
    return f'<img src="data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}">'


def main() -> None:
    available = sorted(p.stem for p in DATA.glob("*.csv"))
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("dataset", nargs="?", default="cutest_smooth", choices=available)
    parser.add_argument("--r1", type=float, default=5.0, help="abscissa scaling (default 5)")
    parser.add_argument("--r2", type=float, default=1.0, help="ordinate scaling (default 1)")
    parser.add_argument("--no-open", action="store_true", help="do not open the browser")
    args = parser.parse_args()

    f0, f_solvers, names = load(args.dataset)
    qp = quality_profiles(f0, f_solvers, solver_names=names, r1=args.r1, r2=args.r2)
    title = f"{args.dataset}: r1 = {args.r1:g}, r2 = {args.r2:g}"
    loc = "outside right center" if len(names) > 4 else "best"

    default = png(plot_quality_profiles(qp, title=title, legend_loc=loc).figure, dpi=130)
    science = png(plot_quality_profiles(qp, style="science", legend_loc=loc).figure, dpi=220)
    ieee = png(plot_quality_profiles(qp, style=["science", "ieee"], legend_loc=loc).figure, dpi=220)
    interactive = plot_quality_profiles_interactive(qp, title=title).to_html(
        full_html=False, include_plotlyjs=True
    )

    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Plot styles</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1000px;margin:24px auto;padding:0 16px;color:#1f1f1e;background:#fff}}
h2{{margin-top:32px;font-size:18px}} p{{color:#52514e;margin:4px 0 12px}} img{{max-width:100%}}
.row{{display:flex;gap:24px;flex-wrap:wrap}} .row>div{{flex:1;min-width:280px}}</style></head><body>
<h1 style="font-size:22px">Same quality profiles, four looks</h1><p>{html.escape(title)}</p>
<h2>A. Package default</h2><p><code>plot_quality_profiles(qp)</code></p>{default}
<h2>B and C. SciencePlots</h2>
<p>Sized for one journal column (3.5 inches). With LaTeX installed the fonts match the paper's text.</p>
<div class="row"><div><b>style="science"</b><br>{science}</div>
<div><b>style=["science", "ieee"]</b> (black and white friendly)<br>{ieee}</div></div>
<h2>D. Plotly</h2>
<p>Drag to zoom, double-click to reset, click a solver in the legend to hide it.
Hovering shows every solver's value at that precision.</p>{interactive}
</body></html>"""
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "style_comparison.html"
    out.write_text(page, encoding="utf-8")
    print(f"written {out}")
    if not args.no_open:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
