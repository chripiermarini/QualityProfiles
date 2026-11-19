"""Draw the plot-style gallery shown in the README.

The static images need the dev environment (``uv sync``). The Plotly screenshot and
the animated GIFs also need Playwright and a local Google Chrome::

    uv run --with playwright python examples/make_readme_gallery.py

Use ``--static-only`` to skip everything that needs a browser.

Files written to ``docs/assets``:

* ``style_default.png``, ``style_science.png``, ``style_science_ieee.png``: the smooth
  CUTEst experiment of the paper (Figure 5, ``r1 = 5``) in the matplotlib styles;
* ``style_plotly.png``: the same profiles in the interactive Plotly figure;
* ``plotly_hover.gif``: the cursor moving along the curves, with the hover values;
* ``plotly_legend_zoom.gif``: hiding solvers from the legend and zooming, on the
  derivative-free experiment (Figure 12, seven solvers).
"""

from __future__ import annotations

import argparse
import io
import tempfile
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
OUT = HERE.parent / "docs" / "assets"

WIDTH, HEIGHT = 860, 420  # size of the Plotly figures, in pixels

# A small arrow that follows the mouse: headless Chrome does not draw the cursor.
CURSOR_JS = """
() => {
  const c = document.createElement('div');
  c.id = 'fake-cursor';
  c.style.cssText = 'position:fixed;left:-50px;top:-50px;width:18px;height:24px;z-index:99999;'
    + 'pointer-events:none;transform:translate(-2px,-1px)';
  c.innerHTML = '<svg width="18" height="24" viewBox="0 0 18 24">'
    + '<path d="M1 1 L1 19 L6 14.5 L9.5 22 L12.5 20.7 L9 13.3 L15.5 13.3 Z" '
    + 'fill="#1f1f1e" stroke="white" stroke-width="1.4" stroke-linejoin="round"/></svg>';
  document.body.appendChild(c);
}
"""


def load(name: str):
    path = DATA / f"{name}.csv"
    names = path.read_text(encoding="utf-8").splitlines()[0].split(",")[1:]
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    return data[:, 0], data[:, 1:], names


def profiles(name: str, r1: float):
    f0, f_solvers, names = load(name)
    return quality_profiles(f0, f_solvers, solver_names=names, r1=r1)


def static_images() -> None:
    qp = profiles("cutest_smooth", r1=5)
    title = "L-BFGS, CG+, TRON, CG_DESCENT, r1 = 5"

    ax = plot_quality_profiles(qp, title=title, legend_loc="lower right")
    ax.figure.savefig(OUT / "style_default.png", dpi=150)
    plt.close(ax.figure)

    for fname, style in [
        ("style_science.png", "science"),
        ("style_science_ieee.png", ["science", "ieee"]),
    ]:
        ax = plot_quality_profiles(qp, style=style, legend_loc="lower right")
        ax.figure.savefig(OUT / fname, dpi=300)
        plt.close(ax.figure)
    print("written the matplotlib styles")


class Recorder:
    """Drive a Plotly figure in Chrome and collect frames for a GIF."""

    def __init__(self, page, chart):
        self.page = page
        self.chart = chart
        self.frames: list = []
        self.x, self.y = 0.0, 0.0

    def snap(self, repeat: int = 1) -> None:
        from PIL import Image

        self.page.wait_for_timeout(45)
        png = self.page.screenshot(clip=self.chart)
        frame = Image.open(io.BytesIO(png)).convert("RGB")
        self.frames.extend([frame] * repeat)

    def move(self, x: float, y: float, steps: int, snap: bool = True) -> None:
        for k in range(1, steps + 1):
            t = k / steps
            t = t * t * (3 - 2 * t)  # ease in and out
            cx, cy = self.x + (x - self.x) * t, self.y + (y - self.y) * t
            self.page.mouse.move(cx, cy)
            self.page.evaluate(
                "([x, y]) => { const c = document.getElementById('fake-cursor');"
                " c.style.left = x + 'px'; c.style.top = y + 'px'; }",
                [cx, cy],
            )
            if snap:
                self.snap()
        self.x, self.y = x, y

    def click(self, double: bool = False) -> None:
        if double:
            self.page.mouse.dblclick(self.x, self.y)
        else:
            self.page.mouse.click(self.x, self.y)
        self.page.wait_for_timeout(350)
        self.snap(repeat=4)

    def save(self, path: Path, ms: int = 70) -> None:
        palette = self.frames[0].quantize(colors=128, method=2)
        frames = [f.quantize(palette=palette, dither=0) for f in self.frames]
        frames[0].save(
            path, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=True
        )
        print(f"written {path.name}: {len(frames)} frames, {path.stat().st_size // 1024} KB")


def open_figure(browser, fig, tmp: Path, scale: float = 1):
    html = tmp / "figure.html"
    # showTips=False: no "double-click to ..." pop-ups covering the figure
    fig.write_html(html, include_plotlyjs=True, config={"displaylogo": False, "showTips": False})
    width, height = fig.layout.width or WIDTH, fig.layout.height or HEIGHT
    page = browser.new_page(
        viewport={"width": width + 20, "height": height + 20}, device_scale_factor=scale
    )
    page.goto(html.as_uri())
    page.wait_for_selector(".main-svg")
    page.wait_for_timeout(400)
    page.evaluate(CURSOR_JS)
    chart = page.locator(".js-plotly-plot").bounding_box()
    plot = page.locator(".nsewdrag").first.bounding_box()
    return page, chart, plot


def browser_images() -> None:
    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory() as tmpdir, sync_playwright() as p:
        tmp = Path(tmpdir)
        browser = p.chromium.launch(channel="chrome", headless=True)

        # Static screenshot: narrower and at twice the resolution, so that it matches the
        # proportions of the matplotlib images next to it in the README.
        qp = profiles("cutest_smooth", r1=5)
        title = "L-BFGS, CG+, TRON, CG_DESCENT, r1 = 5"
        fig = plot_quality_profiles_interactive(qp, title=title, width=640, height=420)
        page, chart, _ = open_figure(browser, fig, tmp, scale=2)
        page.screenshot(path=OUT / "style_plotly.png", clip=chart)
        page.close()
        print("written style_plotly.png")

        # Hover animation, on the same experiment.
        fig = plot_quality_profiles_interactive(qp, title=title, width=WIDTH, height=HEIGHT)
        page, chart, plot = open_figure(browser, fig, tmp)
        rec = Recorder(page, chart)
        left, right = plot["x"] + 8, plot["x"] + plot["width"] - 8
        mid_y = plot["y"] + plot["height"] * 0.45
        rec.move(left - 40, mid_y + 60, steps=1, snap=False)
        rec.snap(repeat=6)
        rec.move(left, mid_y, steps=8)
        rec.move(right, mid_y, steps=60)
        rec.snap(repeat=10)
        rec.move(plot["x"] + plot["width"] * 0.55, mid_y - 30, steps=25)
        rec.snap(repeat=14)
        rec.save(OUT / "plotly_hover.gif")
        page.close()

        # Legend toggling and zoom, on the derivative-free experiment.
        qp = profiles("dfo_budget_1000n", r1=5)
        fig = plot_quality_profiles_interactive(
            qp, title="Derivative-free solvers, budget 1000n, r1 = 5", width=WIDTH, height=HEIGHT
        )
        page, chart, plot = open_figure(browser, fig, tmp)
        rec = Recorder(page, chart)
        entries = page.locator(".legend .traces")
        rec.move(plot["x"] + plot["width"] * 0.5, plot["y"] + plot["height"] * 0.6, 1, False)
        rec.snap(repeat=8)
        for index in (5, 4, 2):  # hide ALG7, ALG6 and ALG2
            box = entries.nth(index).bounding_box()
            rec.move(box["x"] + 18, box["y"] + box["height"] / 2, steps=14)
            rec.click()
        rec.snap(repeat=6)
        # Zoom on the high-accuracy range by dragging a box.
        x0, y0 = plot["x"] + plot["width"] * 0.04, plot["y"] + plot["height"] * 0.08
        x1, y1 = plot["x"] + plot["width"] * 0.62, plot["y"] + plot["height"] * 0.55
        rec.move(x0, y0, steps=16)
        page.mouse.down()
        rec.move(x1, y1, steps=24)
        page.mouse.up()
        page.wait_for_timeout(500)
        rec.snap(repeat=16)
        # Back to the full view.
        rec.move(plot["x"] + plot["width"] * 0.3, plot["y"] + plot["height"] * 0.3, steps=10)
        rec.click(double=True)
        rec.snap(repeat=12)
        rec.save(OUT / "plotly_legend_zoom.gif")
        page.close()

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--static-only", action="store_true", help="skip the browser images")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    static_images()
    if not args.static_only:
        browser_images()


if __name__ == "__main__":
    main()
