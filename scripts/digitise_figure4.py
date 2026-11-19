"""Recover the plotted values of Ding et al. (2021) Figure 4 from the vector graphics of arXiv v3 (page 11).

The figure is drawn as vector paths (no raster image). Each series is a 5-point polyline; axis ticks are
short line segments whose positions map pixel coordinates to data values. Series colours are matched to
legend entries by the legend's own coloured handles. Output: results/reconstruction/figure4_digitised.json
Precision is about 1e-4 in data units (PDF coordinates are given to 1e-2 points).
Usage: python scripts/digitise_figure4.py docs/sources/ding2021_arxiv_v3.pdf
"""
import json
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]


def main(pdf_path: str):
    pg = pdfplumber.open(pdf_path).pages[10]
    in_fig = lambda o: 125 < o["top"] < 245
    blk = [o for o in pg.lines if in_fig(o) and str(o.get("stroking_color")) == "0.0"]
    # y-ticks: horizontal ticks 1.53 pt long at the left edge of each panel
    left_ticks = sorted({round(o["top"], 2) for o in blk if abs(o["x1"] - 94.41) < 0.01 and o["x0"] < 94})
    right_ticks = sorted({round(o["top"], 2) for o in blk if abs(o["x1"] - 333.81) < 0.01 and o["x0"] < 333.8})
    acc_labels = [0.86, 0.84, 0.82, 0.80, 0.78, 0.76]          # top to bottom, from the tick labels
    dp_labels = [0.175, 0.150, 0.125, 0.100, 0.075, 0.050, 0.025, 0.000]
    assert len(left_ticks) == len(acc_labels) and len(right_ticks) == len(dp_labels)
    a_top, a_bot = left_ticks[0], left_ticks[-1]
    d_top, d_bot = right_ticks[0], right_ticks[-1]
    acc = lambda y: acc_labels[-1] + (a_bot - y) / (a_bot - a_top) * (acc_labels[0] - acc_labels[-1])
    dp = lambda y: dp_labels[-1] + (d_bot - y) / (d_bot - d_top) * (dp_labels[0] - dp_labels[-1])
    # legend: handles below the axes, left to right, in the legend's text order
    legend_names = ["GBM", "GBM w/ ExpGrad (DP)", "GBM w/ Postprocessing (DP)", "GBM w/ LFR"]
    handles = sorted({(round(o["x0"], 0), tuple(o["stroking_color"][:3]))
                      for o in pg.lines + pg.curves
                      if 255 < o["top"] < 270 and isinstance(o.get("stroking_color"), tuple)})
    colours = []
    for _, c in handles:
        if c not in colours:
            colours.append(c)
    colour_to_name = dict(zip(colours, legend_names))
    out = {"source": "arXiv:2108.04884v3, page 11, Figure 4", "years": [2014, 2015, 2016, 2017, 2018],
           "series": {}}
    for o in pg.curves:
        if not (in_fig(o) and isinstance(o.get("stroking_color"), tuple)):
            continue
        if isinstance(o.get("non_stroking_color"), tuple):
            continue  # filled confidence band; the 5-point polyline is the estimate
        name = colour_to_name[tuple(o["stroking_color"][:3])]
        left = o["pts"][0][0] < 300
        vals = [round((acc if left else dp)(y), 4) for _, y in o["pts"]]
        out["series"].setdefault(name, {})["accuracy" if left else "dp"] = vals
    dest = ROOT / "results" / "reconstruction"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "figure4_digitised.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
