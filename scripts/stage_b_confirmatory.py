"""Stage B, confirmatory analysis (pre-registration sections 5-7). Runs only after the plan is archived:
loading any year after 2018 requires prereg/ARCHIVED (src/data.py).

Order of work after archiving:
  1. download 2019 and 2021-2024 person files; build them with src/data.py
  2. uv run python scripts/stage_a.py predict --years 2019 2021 2022 2023 2024
  3. uv run python scripts/stage_b_confirmatory.py
Writes results/stage_b/confirmatory.json and results/stage_b/trajectories.csv.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from analysis import (METRICS, REP, Estimate, change, compare_stability, noise_corrected_abs, sign_test, three_way,
                      unweighted, weighted)
from common import label, load_year, state_split
from pipeline import MANIFEST, SEEDS, SMOKE, load_pred

ALPHA = 0.05 / 8
ALL_YEARS = (2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
Y_RACE, Y_SEX = 2019, 2024
OUT = ROOT / "results" / "stage_b"
MARGINS = ROOT / "results" / "stage_a" / "margins.json"
WT = ("unweighted", "weighted")
if SMOKE:   # code test on original-cohort years only: 2017 and 2018 stand in for 2019 and 2024
    Y_RACE, Y_SEX, ALL_YEARS = 2017, 2018, (2014, 2015, 2016, 2017, 2018)
    OUT = ROOT / "data" / "derived" / "smoke_stage_b"
    MARGINS = ROOT / "data" / "derived" / "smoke_stage_a" / "margins.json"


def frame(year):
    df = load_year(year, columns=["PINCP", "RAC1P", "SEX", "ST", "PWGTP"] + REP)
    if SMOKE:
        df = df.sample(n=int(SMOKE), random_state=0).reset_index(drop=True)
    return df


def estimate(name, year, df, seed=0, rows=None, rule=">"):
    """(unweighted, weighted) Estimate of a frozen US model on one year (2014: test split of its seed)."""
    pred = load_pred(name, year, len(df))
    keep = state_split(df, seed) if year == 2014 else np.ones(len(df), bool)
    if rows is not None:
        keep &= rows
    y = label(df, rule=rule)
    sub = df[keep].reset_index(drop=True)
    return (Estimate.from_unweighted(unweighted(pred[keep], y[keep], sub)),
            Estimate.from_weighted(weighted(pred[keep], y[keep], sub), int(keep.sum())))


def seed_mean_change(family, year, frames, metric, wi):
    """Seed-mean change from 2014 and the mean per-seed SE (upper bound under positive correlation)."""
    ds, ses = [], []
    for s in SEEDS:
        e_t = estimate(f"{family}_s{s}", year, frames[year], s)[wi]
        e_0 = estimate(f"{family}_s{s}", 2014, frames[2014], s)[wi]
        d, cov = change(e_t, e_0)
        k = METRICS.index(metric)
        ds.append(d[metric]); ses.append(np.sqrt(cov[k, k]))
    return float(np.mean(ds)), float(np.mean(ses))


def seed_mean_level(family, year, frames, metric, wi):
    vals, ses = [], []
    for s in SEEDS:
        e = estimate(f"{family}_s{s}", year, frames[year], s)[wi]
        vals.append(e.values[metric]); ses.append(e.se(metric))
    return float(np.mean(vals)), float(np.mean(ses))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    margins = json.loads(MARGINS.read_text())
    manifest = json.loads(MANIFEST.read_text())
    frames = {y: frame(y) for y in (2014, Y_RACE, Y_SEX)}
    res = {"alpha_per_test": ALPHA}
    for wi, wt in enumerate(WT):
        mg, r = margins[wt], {}
        d, se = seed_mean_change("gbm", Y_RACE, frames, "dp_race", wi)
        r["C1"] = three_way(d, se, mg["delta"]["dp_race"], ALPHA)
        d, se = seed_mean_change("gbm", Y_SEX, frames, "dp_sex", wi)
        r["C2"] = three_way(d, se, mg["delta"]["dp_sex"], ALPHA)
        v, se = seed_mean_level("post_dp_race", Y_RACE, frames, "dp_race", wi)
        r["C3"] = three_way(v, se, mg["epsilon"]["race"], ALPHA)
        v, se = seed_mean_level("post_dp_sex", Y_SEX, frames, "dp_sex", wi)
        r["C4"] = three_way(v, se, mg["epsilon"]["sex"], ALPHA)
        d, se = seed_mean_change("gbm", Y_RACE, frames, "eo_race", wi)
        r["C5"] = three_way(d, se, mg["delta"]["eo_race"], ALPHA)
        d, se = seed_mean_change("gbm", Y_SEX, frames, "eo_sex", wi)
        r["C6"] = three_way(d, se, mg["delta"]["eo_sex"], ALPHA)
        # C7: joint seed-mean changes of DP_race and accuracy; covariance = mean of per-seed covariances
        i_dp, i_acc = METRICS.index("dp_race"), METRICS.index("accuracy")
        dd, covs = [], []
        for s in SEEDS:
            dlt, cov = change(estimate(f"gbm_s{s}", Y_RACE, frames[Y_RACE], s)[wi],
                              estimate(f"gbm_s{s}", 2014, frames[2014], s)[wi])
            dd.append([dlt["dp_race"], dlt["accuracy"]])
            covs.append(cov[np.ix_([i_dp, i_acc], [i_dp, i_acc])])
        dd, cov2 = np.mean(dd, axis=0), np.mean(covs, axis=0)
        r["C7"] = compare_stability(dd[0], dd[1], cov2, mg["G"]["dp_race"], mg["G"]["accuracy"], ALPHA)
        r["C7"]["delta_dp_race"], r["C7"]["delta_accuracy"] = float(dd[0]), float(dd[1])
        # C8: per-state temporal change vs the state's geographic reference
        ind, detail = [], {}
        for st in margins["states"]:
            name = f"state{st}_gbm_s0"
            e0 = estimate(name, 2014, frames[2014], 0, rows=(frames[2014]["ST"] == st).to_numpy())[wi]
            e1 = estimate(name, Y_RACE, frames[Y_RACE], 0, rows=(frames[Y_RACE]["ST"] == st).to_numpy())[wi]
            dlt, cov = change(e1, e0)
            k = METRICS.index("dp_race")
            temporal = noise_corrected_abs(dlt["dp_race"], float(np.sqrt(cov[k, k])))
            geographic = mg["G_by_source_state"]["dp_race"][str(st)]
            ind.append(temporal < geographic)
            detail[str(st)] = {"temporal": temporal, "geographic": geographic}
        r["C8"] = sign_test(ind, ALPHA) | {"states": detail}
        res[wt] = r
    res["weighting_sensitive"] = [c for c in res["unweighted"]
                                  if res["unweighted"][c]["decision"] != res["weighted"][c]["decision"]]
    (OUT / "confirmatory.json").write_text(json.dumps(res, indent=1, default=float))
    for c in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"):
        print(c, "unweighted:", res["unweighted"][c]["decision"], "| weighted:", res["weighted"][c]["decision"])

    # trajectories of every US model, all years, nominal label (">" and ">=")
    rows = []
    for y in ALL_YEARS:
        df = frame(y)
        for name, meta in manifest.items():
            if name.startswith("state") or (name.startswith("rawgbm") and y > 2018):
                continue
            for rule in (">", ">="):
                for wt, e in zip(WT, estimate(name, y, df, meta["seed"], rule=rule)):
                    for m in METRICS:
                        rows.append(dict(model=name, year=y, rule=rule, weighting=wt, metric=m,
                                         value=e.values[m], se=e.se(m)))
    pd.DataFrame(rows).to_csv(OUT / "trajectories.csv", index=False)


if __name__ == "__main__":
    main()
