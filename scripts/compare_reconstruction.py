"""Compare reconstruction runs (results/reconstruction/runs.jsonl) with the digitised Figures 4 and 13.

For every method x scaling x trees (seed 0 unless averaged), prints accuracy and the fairness metric per year,
the published values, and the mean absolute and maximum deviation over 2014-2018. Also reports seed spread
for the plain GBM. Writes results/reconstruction/comparison.csv.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
YEARS = [2014, 2015, 2016, 2017, 2018]
NAME = {("gbm", "none"): "GBM", ("expgrad", "dp"): "GBM w/ ExpGrad (DP)",
        ("postprocessing", "dp"): "GBM w/ Postprocessing (DP)", ("lfr", "dp"): "GBM w/ LFR",
        ("expgrad", "eo"): "GBM w/ ExpGrad (EO)", ("postprocessing", "eo"): "GBM w/ Postprocessing (EO)"}


def main():
    rec = ROOT / "results" / "reconstruction"
    f4 = json.loads((rec / "figure4_digitised.json").read_text())["series"]
    f13 = json.loads((rec / "figure13_digitised.json").read_text())["series"]
    runs = [json.loads(l) for l in (rec / "runs.jsonl").read_text().splitlines() if l.strip()]
    runs = [r for r in runs if r["status"] == "ok"]
    rows = []
    for r in runs:
        j = r["job"]
        name = NAME[(j["method"], j["constraint"])]
        for fig, ref, metric in (("fig4", f4, "dp"), ("fig13", f13, "eo")):
            if name not in ref or (j["method"] != "gbm" and j["constraint"] != metric):
                continue
            for m in ("accuracy", metric):
                ours = np.array([r["eval"][str(y)][m] for y in YEARS])
                pub = np.array(ref[name][m])
                rows.append(dict(figure=fig, series=name, method=j["method"], constraint=j["constraint"],
                                 scaling=j["scaling"], n_trees=j["n_trees"], seed=j["seed"], metric=m,
                                 **{f"ours_{y}": o for y, o in zip(YEARS, ours)},
                                 **{f"pub_{y}": p for y, p in zip(YEARS, pub)},
                                 mean_abs_dev=float(np.mean(np.abs(ours - pub))),
                                 max_abs_dev=float(np.max(np.abs(ours - pub))),
                                 change_ours=float(ours[-1] - ours[0]), change_pub=float(pub[-1] - pub[0])))
    df = pd.DataFrame(rows)
    df.to_csv(rec / "comparison.csv", index=False)
    pd.set_option("display.width", 250)
    s0 = df[df.seed == 0]
    print(s0.sort_values(["figure", "series", "metric", "n_trees", "scaling"])[
        ["figure", "series", "metric", "n_trees", "scaling", "mean_abs_dev", "max_abs_dev", "change_ours",
         "change_pub"]].round(4).to_string(index=False))
    g = df[(df.method == "gbm")].groupby(["figure", "metric", "n_trees", "scaling"])[
        ["mean_abs_dev", "change_ours"]].agg(["mean", "std"]).round(4)
    print("\nGBM across 5 seeds:\n", g.to_string())


if __name__ == "__main__":
    main()
