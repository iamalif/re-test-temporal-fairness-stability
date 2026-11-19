"""Does the variance estimator of a test-split estimate include the extra 20% person subsampling? (QA 1, #14)

The training year (2014) is evaluated on a random 20% within-state test split, later years on all rows. For a split
estimate, total variance = design variance of the full-sample estimate + variance added by the random split.
Check on 2018, where the frozen 2014 model is evaluated on all rows (so any random 20% split is a valid stand-in):
  V_full  = variance estimate on all 2018 rows (replicate weights, or household-clustered influence values)
  S       = variance of the split estimates over K random within-state splits (the split's own contribution)
  V_split = mean of the variance estimates computed on each split
  ratio R = V_split / (V_full + S)          (R near 1: the estimator already covers the split)
Pre-specified use (pre-registration 7.3): the variance of every 2014 test-split estimate in Stage B is multiplied by
max(1, 1/R) for that metric and weighting. Writes results/validation/split_variance.json.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from analysis import METRICS, REP, Estimate, household_ids, unweighted, weighted
from common import label, load_year, state_split
from pipeline import load_pred

K = 200
SEEDS = range(1000, 1000 + K)


def est(pred, y, df):
    return (Estimate.from_unweighted(unweighted(pred, y, df), household_ids(df)),
            Estimate.from_weighted(weighted(pred, y, df), len(df)))


def main():
    df = load_year(2018, columns=["PINCP", "RAC1P", "SEX", "ST", "SERIALNO", "PWGTP"] + REP)
    y = label(df)
    pred = load_pred("gbm_s0", 2018, df)
    full = est(pred, y, df)
    splits = {"unweighted": [], "weighted": []}
    for s in SEEDS:
        m = state_split(df, s)
        sub = df[m].reset_index(drop=True)
        for wt, e in zip(("unweighted", "weighted"), est(pred[m], y[m], sub)):
            splits[wt].append(e)
    out = {"K": K, "model": "gbm_s0", "year": 2018}
    for wi, wt in enumerate(("unweighted", "weighted")):
        res = {}
        for k, m in enumerate(METRICS):
            theta = np.array([e.values[m] for e in splits[wt]])
            v_split = float(np.mean([e.cov[k, k] for e in splits[wt]]))
            v_full = float(full[wi].cov[k, k])
            s_between = float(theta.var(ddof=1))
            r = v_split / (v_full + s_between)
            res[m] = {"V_full": v_full, "S_between_splits": s_between, "V_split_mean": v_split, "ratio": r,
                      "variance_multiplier": max(1.0, 1.0 / r),
                      "mc_se_of_S": s_between * np.sqrt(2 / (K - 1))}
        out[wt] = res
        print(wt, {m: round(v["ratio"], 3) for m, v in res.items()})
    path = ROOT / "results" / "validation"
    path.mkdir(parents=True, exist_ok=True)
    (path / "split_variance.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
