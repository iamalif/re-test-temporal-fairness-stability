"""Recover plotted values from the vector graphics of Ding et al. (2021), arXiv v3.

Figures 4 (demographic parity, page 11) and 13 (equality of opportunity, page 47) are drawn as vector paths.
Each series is a 5-point polyline (2014-2018). For each panel, the y-axis ticks are short black horizontal
segments; their numeric labels are the text immediately to their left. A least-squares line through
(tick position, label) maps PDF coordinates to data values. Series colours are matched to the legend's
coloured handles, read left to right in the legend's text order.

Usage: python scripts/digitise_figure4.py docs/sources/ding2021_arxiv_v3.pdf
Output: results/reconstruction/figure4_digitised.json and figure13_digitised.json
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
FIGURES = {
    "figure4": dict(caption="Figure 4:", metric="dp",
                    legend=["GBM", "GBM w/ ExpGrad (DP)", "GBM w/ Postprocessing (DP)", "GBM w/ LFR"]),
    "figure13": dict(caption="Figure 13:", metric="eo",
                     legend=["GBM", "GBM w/ ExpGrad (EO)", "GBM w/ Postprocessing (EO)"]),
}
NUM = re.compile(r"^[−-]?\d*\.?\d+$")


def colour(o, key):
    c = o.get(key)
    return tuple(round(v, 6) for v in c[:3]) if isinstance(c, (tuple, list)) and len(c) >= 3 else None


def digitise(pdf, spec):
    first, second = spec["caption"].split()
    for page in pdf.pages:
        ws = page.extract_words()
        caps = [w for w in ws if w["text"] == first
                and any(v["text"] == second and abs(v["top"] - w["top"]) < 2 and 0 < v["x0"] - w["x1"] < 8
                        for v in ws)]
        if caps:
            cap_top = caps[0]["top"]
            break
    # series: stroked, unfilled coloured polylines with 5 points above the caption
    series = [o for o in page.curves if colour(o, "stroking_color") and not colour(o, "non_stroking_color")
              and len(o["pts"]) == 5 and o["bottom"] < cap_top and cap_top - o["top"] < 200]
    xs = sorted({round(o["pts"][0][0], 1) for o in series})            # left edge of each panel
    ticks_all = [o for o in page.lines if str(o.get("stroking_color")) in ("0.0", "0")
                 and abs(o["top"] - o["bottom"]) < 0.01 and 1.0 < o["x1"] - o["x0"] < 4.5]
    words = [w for w in page.extract_words() if NUM.match(w["text"])]
    maps = {}
    for x in xs:
        pairs = []
        for t in (t for t in ticks_all if abs(t["x1"] - x) < 0.6):
            cands = [w for w in words if w["x1"] < t["x0"] + 0.5 and t["x0"] - w["x1"] < 12
                     and abs((w["top"] + w["bottom"]) / 2 - t["top"]) < 3]
            if cands:
                w = max(cands, key=lambda w: w["x1"])
                pairs.append((t["top"], float(w["text"].replace("−", "-"))))
        ys, vals = np.array(sorted(pairs)).T   # top to bottom: values decrease
        v = vals.copy()
        zero = np.where(v == 0)[0]
        if len(zero):                          # minus signs are not extracted; restore them below zero
            v[zero[0] + 1:] = -np.abs(v[zero[0] + 1:])
        slope, icpt = np.polyfit(ys, v, 1)
        resid = float(np.max(np.abs(np.polyval([slope, icpt], ys) - v)))
        maps[x] = (slope, icpt, resid, len(pairs))
    lowest = max(s["bottom"] for s in series)
    handles = sorted({(round(o["x0"], 0), colour(o, "stroking_color"))
                      for o in page.lines + page.curves
                      if colour(o, "stroking_color") and lowest + 5 < o["top"] < cap_top})
    seen = []
    for _, c in handles:
        if c not in seen:
            seen.append(c)
    name_of = dict(zip(seen, spec["legend"]))
    out = {"source": f"arXiv:2108.04884v3, page {page.page_number}, {spec['caption'][:-1]}",
           "years": [2014, 2015, 2016, 2017, 2018],
           "axis_fit": {str(k): {"ticks": v[3], "max_residual": round(v[2], 6)} for k, v in maps.items()},
           "series": {}}
    left_x = min(xs)
    for o in series:
        x0 = round(o["pts"][0][0], 1)
        slope, icpt, _, _ = maps[x0]
        key = "accuracy" if x0 == left_x else spec["metric"]
        vals = [round(float(slope * y + icpt), 4) for _, y in o["pts"]]
        out["series"].setdefault(name_of[colour(o, "stroking_color")], {})[key] = vals
    return out


def main(pdf_path):
    pdf = pdfplumber.open(pdf_path)
    dest = ROOT / "results" / "reconstruction"
    dest.mkdir(parents=True, exist_ok=True)
    for name, spec in FIGURES.items():
        res = digitise(pdf, spec)
        (dest / f"{name}_digitised.json").write_text(json.dumps(res, indent=1))
        print(name, res["axis_fit"])
        for k, v in res["series"].items():
            print("  ", k, v)


if __name__ == "__main__":
    main(sys.argv[1])
