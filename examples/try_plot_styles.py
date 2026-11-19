"""Try the SciencePlots and Plotly options on the paper datasets.

Needs the optional extras (already in the dev environment created by ``uv sync``):
``pip install "quality-profiles[all]"``.

Usage::

    uv run python examples/try_plot_styles.py                        # all datasets, r1 = 5
    uv run python examples/try_plot_styles.py cutest_smooth --r1 1   # one dataset, other r1
    uv run python examples/try_plot_styles.py negative_curvature --r1 5 --r2 3
    uv run python examples/try_plot_styles.py --strong --linear      # strong profiles, linear axis
    uv run python examples/try_plot_styles.py --list                 # show the datasets

For each dataset it writes, in ``examples/figures/styles``:

* ``<name>_science.png``: SciencePlots "science" style;
* ``<name>_science_ieee.png``: SciencePlots "science" + "ieee" (works in black and white);
* ``<name>_interactive.html``: Plotly interactive figure;

and an ``index.html`` page with everything, which opens in the browser.
"""

from __future__ import annotations

import argparse
import base64
import html
import webbrowser
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from utils.paper_data import DATA, dataset_names, load

from quality_profiles import (
    plot_quality_profiles,
    plot_quality_profiles_interactive,
    quality_profiles,
)

OUT = Path(__file__).resolve().parent / "figures" / "styles"


def main() -> None:
    available = dataset_names()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("datasets", nargs="*", help="dataset names (default: all)")
    parser.add_argument("--r1", type=float, default=5.0, help="abscissa scaling (default 5)")
    parser.add_argument("--r2", type=float, default=1.0, help="ordinate scaling (default 1)")
    parser.add_argument("--strong", action="store_true", help="strong instead of weak profiles")
    parser.add_argument("--linear", action="store_true", help="linear instead of log abscissa")
    parser.add_argument("--list", action="store_true", help="list the datasets and exit")
    parser.add_argument("--no-open", action="store_true", help="do not open the browser")
    args = parser.parse_args()

    if not DATA.is_dir():
        raise SystemExit(f"data folder not found: {DATA}")
    if args.list:
        print("\n".join(available))
        return
    datasets = args.datasets or available
    unknown = sorted(set(datasets) - set(available))
    if unknown:
        raise SystemExit(
            f"unknown dataset(s): {', '.join(unknown)}; available: {', '.join(available)}"
        )

    OUT.mkdir(parents=True, exist_ok=True)
    settings = f"r1 = {args.r1:g}, r2 = {args.r2:g}, {'strong' if args.strong else 'weak'}"
    sections = []
    for name in datasets:
        f0, f_solvers, names = load(name)
        qp = quality_profiles(
            f0, f_solvers, solver_names=names, r1=args.r1, r2=args.r2, strong=args.strong
        )
        logscale = not args.linear

        pngs = []
        for suffix, style in [("science", "science"), ("science_ieee", ["science", "ieee"])]:
            # SciencePlots figures are one journal column wide: keep the legend outside
            ax = plot_quality_profiles(
                qp, style=style, logscale=logscale, legend_loc="outside right center"
            )
            # widen the figure for the legend, so that the axes keep about a column's width
            ax.figure.set_size_inches(5.4, ax.figure.get_figheight())
            file = OUT / f"{name}_{suffix}.png"
            ax.figure.savefig(file, dpi=200)
            plt.close(ax.figure)
            pngs.append((suffix, file))

        fig = plot_quality_profiles_interactive(qp, logscale=logscale, title=f"{name}: {settings}")
        html_file = OUT / f"{name}_interactive.html"
        fig.write_html(html_file, include_plotlyjs="cdn")

        ranking = ", ".join(f"{n} ({a:.3f})" for n, a in qp.ranking())
        images = "".join(
            f'<figure><img src="data:image/png;base64,{base64.b64encode(f.read_bytes()).decode()}">'
            f"<figcaption>{html.escape(s.replace('_', ' + '))}</figcaption></figure>"
            for s, f in pngs
        )
        # plotly.js is embedded once, with the first figure, so the page works offline
        plotly_div = fig.to_html(full_html=False, include_plotlyjs=not sections)
        sections.append(
            f"<section><h2>{html.escape(name)}</h2><p>{len(f0)} problems, "
            f"{len(names)} solvers. Ranking by area: {html.escape(ranking)}</p>"
            f'<div class="row">{images}</div>{plotly_div}</section>'
        )
        print(f"{name}: written {pngs[0][1].name}, {pngs[1][1].name}, {html_file.name}")

    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Style trial</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1050px;margin:24px auto;padding:0 16px;color:#1f1f1e;background:#fff}}
section{{border-top:1px solid #e4e3df;margin-top:28px;padding-top:8px}} p{{color:#52514e}}
.row{{display:flex;gap:16px;flex-wrap:wrap}} figure{{margin:0;flex:1;min-width:280px}} img{{width:100%;max-width:500px}}
figcaption{{color:#52514e;font-size:13px}}</style></head><body>
<h1 style="font-size:22px">SciencePlots and Plotly on the paper datasets</h1><p>{html.escape(settings)}</p>
{"".join(sections)}</body></html>"""
    index = OUT / "index.html"
    index.write_text(page, encoding="utf-8")
    print(f"\nOpen: {index}")
    if not args.no_open:
        webbrowser.open(index.as_uri())


if __name__ == "__main__":
    main()
