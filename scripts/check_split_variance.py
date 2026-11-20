"""Empirical calibration of variance estimates on a 20% test split (pre-registration 7.1; QA 1 #14, QA 2 A2).

The training year is evaluated on a random 20% within-state test split, later years on all rows. For a split
estimate, total variance = variance of the full-sample estimate + variance added by the random split. On 2018, where
models trained on 2014 are evaluated on all rows, any random 20% within-state split is a valid stand-in. For each
configuration c (model, label rule, population) and each metric and weighting:
  V_full = variance estimate on all rows of the population (replicate weights, or household-clustered influence)
  S      = variance of the split estimates over K random within-state splits (the split's own contribution)
  V_split= mean of the variance estimates computed on the splits
  ratio  = (V_full + S_upper) / V_split, with S_upper the one-sided 95% upper confidence bound of S
           (chi-square with (valid splits - 1) degrees of freedom; approximate, assuming roughly normal split
           estimates), which makes Monte Carlo error more likely to enlarge than to shrink the adjustment.
Pre-specified multiplier for every training-year test-split estimate of a metric and weighting: the largest ratio
over the configurations, floored at 1. Configurations span the model families (base, DP and EO post-processing,
ExpGrad, per-year scaling), both label rules, and three per-state populations (largest, middle and smallest of the
20 states). This is an empirical calibration over representative settings, not a theorem; the per-configuration
ratios are reported. Writes results/validation/split_variance.json.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
from scipy import stats

from analysis import METRICS, REP, Estimate, unweighted, weighted
from common import label, load_year, state_split
from pipeline import MANIFEST, SMOKE, data_files, load_pred, provenance, verify_inventory

K = 400
SEEDS = range(1000, 1000 + K)
US_MODELS = ("gbm_s0", "post_dp_race_s0", "post_dp_sex_s0", "post_eo_race_s0", "expgrad_dp_race_s0",
             "peryear_gbm_s0")
WT = ("unweighted", "weighted")


def est(pred, y, df, hh):
    return (Estimate.from_unweighted(unweighted(pred, y, df), hh),
            Estimate.from_weighted(weighted(pred, y, df), len(df)))


def main():
    verify_inventory([2018])
    df = load_year(2018, columns=["PINCP", "RAC1P", "SEX", "ST", "SERIALNO", "SPORDER", "PWGTP"] + REP)
    if SMOKE:
        df = df.sample(n=int(SMOKE), random_state=0).reset_index(drop=True)
    hh = pd.factorize(df["ST"].astype(int).astype(str) + "_" + df["SERIALNO"].astype(str))[0]
    states = sorted({int(n[5:].split("_")[0]) for n in json.loads(MANIFEST.read_text()) if n.startswith("state")})
    counts = df[df.ST.isin(states)].groupby("ST").size().sort_values(ascending=False)
    pick = [int(counts.index[0]), int(counts.index[len(counts) // 2]), int(counts.index[-1])]
    configs = [(m, rule, None) for m in US_MODELS for rule in (">", ">=")]
    configs += [(f"state{s}_gbm_s0", ">", s) for s in pick]
    preds = {m: load_pred(m, 2018, df) for m in {c[0] for c in configs}}
    labels = {r: label(df, rule=r) for r in (">", ">=")}
    st = df["ST"].to_numpy()
    pops = {c: (np.ones(len(df), bool) if c[2] is None else st == c[2]) for c in configs}

    full = {c: est(preds[c[0]][pops[c]], labels[c[1]][pops[c]], df[pops[c]].reset_index(drop=True), hh[pops[c]])
            for c in configs}
    split_vals = {c: {wt: [] for wt in WT} for c in configs}
    split_vars = {c: {wt: [] for wt in WT} for c in configs}
    for s in SEEDS:
        m = state_split(df, s)
        sub = df[m].reset_index(drop=True)
        for c in configs:
            pm = pops[c][m]
            e = est(preds[c[0]][m][pm], labels[c[1]][m][pm], sub[pm].reset_index(drop=True), hh[m][pm])
            for wi, wt in enumerate(WT):
                split_vals[c][wt].append([e[wi].values[k] for k in METRICS])
                split_vars[c][wt].append(np.diag(e[wi].cov))
    out = {"K": K, "year": 2018, "states_used": pick, "configurations": {}, "multipliers": {wt: {} for wt in WT},
           "rule": "max over configurations of (V_full + S_upper95) / V_split, floored at 1",
           "provenance": provenance(inputs=data_files([2018]))}
    for c in configs:
        key = f"{c[0]}|{c[1]}|{'US' if c[2] is None else c[2]}"
        out["configurations"][key] = {}
        for wi, wt in enumerate(WT):
            vals, vars_ = np.array(split_vals[c][wt]), np.array(split_vars[c][wt])
            res = {}
            for k, metric in enumerate(METRICS):
                v_full = float(full[c][wi].cov[k, k])
                n_ok = int(np.isfinite(vals[:, k]).sum())
                s_b = float(np.nanvar(vals[:, k], ddof=1)) if n_ok > 1 else float("nan")
                s_up = s_b * (n_ok - 1) / stats.chi2.ppf(0.05, n_ok - 1) if n_ok > 1 else float("nan")
                v_split = float(np.nanmean(vars_[:, k])) if np.isfinite(vars_[:, k]).any() else float("nan")
                ok = bool(np.isfinite([v_full, s_b, v_split]).all() and v_split > 0)
                res[metric] = {"valid_splits": n_ok, "V_full": v_full, "S": s_b, "S_upper95": s_up, "V_split": v_split,
                               "ratio_point": (v_full + s_b) / v_split if ok else None,
                               "ratio_upper": (v_full + s_up) / v_split if ok else None}
            out["configurations"][key][wt] = res
    failures = []
    for wt in WT:
        for metric in METRICS:
            cells = {k: out["configurations"][k][wt][metric] for k in out["configurations"]}
            bad = [k for k, c in cells.items() if c["ratio_upper"] is None or c["valid_splits"] < 0.95 * K]
            if bad:                     # calibration must cover every registered configuration (no silent 1.0)
                failures.append(f"{wt}/{metric}: insufficient evidence in {bad}")
            r = [c["ratio_upper"] for c in cells.values() if c["ratio_upper"] is not None]
            out["multipliers"][wt][metric] = max([1.0] + r)
        print(wt, {m: round(v, 3) for m, v in out["multipliers"][wt].items()})
    path = ROOT / "results" / "validation"
    path.mkdir(parents=True, exist_ok=True)
    out["calibration_failures"] = failures
    (path / ("split_variance.json" if not SMOKE else "smoke_split_variance.json")).write_text(json.dumps(out, indent=1))
    if failures:
        raise SystemExit("split-variance calibration failed:\n  " + "\n  ".join(failures))


if __name__ == "__main__":
    main()
