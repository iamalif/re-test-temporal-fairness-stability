"""Stage A analysis (original cohort 2014-2018 only): metrics of the frozen models, the pre-registered
margins and yardsticks, and the recoding-artefact check. Writes results/stage_a/.

Margins (pre-registration section 6), all computed here from 2014-2018 data and then frozen:
- delta[m]   temporal margin for the unconstrained model: max over t in 2014-2018 of |m(t) - B|, where m is the
             seed-mean trajectory and B its 2014-2018 mean (the baseline), floored at FLOOR. It is the year-to-year
             variation that the original paper called "essentially constant".
- epsilon[g] constraint tolerance for the post-processed DP model of group g: max over 2014-2018 of
             |mean over seeds of DP(t)|, floored at FLOOR.
- G[m]       geographic yardstick: median over ordered pairs of the 20 largest states (s -> s', 2014) of the
             noise-corrected |m(s -> s') - m(s -> s)| for the per-state unconstrained models.
Both unweighted (primary) and weighted versions are written.
"""
import json
import sys
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd

from analysis import (METRICS, REP, Estimate, change, household_ids, inflate, noise_corrected_abs, split_multiplier,
                      unweighted, weighted)
from common import label, load_year, state_split
from pipeline import MANIFEST, N_STATES, SEEDS, SMOKE, load_pred, train_year_of, verify_inventory

YEARS = (2014, 2015, 2016, 2017, 2018)
FLOOR = 0.01
OUT = ROOT / "results" / "stage_a"
if __import__("os").environ.get("RT_SMOKE_ROWS"):
    OUT = ROOT / "data" / "derived" / "smoke_stage_a"


def frame(year):
    df = load_year(year, columns=["PINCP", "RAC1P", "SEX", "ST", "SERIALNO", "PWGTP"] + REP)
    if SMOKE:                       # same fixed subsample as the pipeline's smoke mode
        df = df.sample(n=int(SMOKE), random_state=0).reset_index(drop=True)
    return df


def estimates(pred, y, df, split=False):
    """(unweighted, weighted) estimates; split=True for estimates on a 20% test split, whose variances get the
    pre-specified multipliers of results/validation/split_variance.json (pre-registration 7.3)."""
    eu = Estimate.from_unweighted(unweighted(pred, y, df), household_ids(df))
    ew = Estimate.from_weighted(weighted(pred, y, df), len(y))
    if split and not SMOKE:
        eu, ew = inflate(eu, split_multiplier("unweighted")), inflate(ew, split_multiplier("weighted"))
    return eu, ew


def main():
    verify_inventory(YEARS)                 # exact model inventory, hashes and prediction provenance
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    us_models = [n for n in manifest if not n.startswith("state")]   # includes y2018_* (8.9)
    states = sorted({int(n[5:].split("_")[0]) for n in manifest if n.startswith("state")})
    assert len(states) == N_STATES, f"{len(states)} source states, expected {N_STATES}"
    frames = {y: frame(y) for y in YEARS}
    labels = {y: label(frames[y]) for y in YEARS}
    rows, est = [], {}
    # ---- US-wide frozen models ----
    for name in us_models:
        seed, ty = manifest[name]["seed"], train_year_of(name, manifest)
        test_ty = state_split(frames[ty], seed)
        for y in YEARS:
            if y < ty:                      # models trained on 2018 (8.9) are evaluated forward only
                continue
            df, yy = frames[y], labels[y]
            pred = load_pred(name, y, df)
            keep = test_ty if y == ty else np.ones(len(df), bool)
            eu, ew = estimates(pred[keep], yy[keep], df[keep].reset_index(drop=True), split=(y == ty))
            est[(name, y)] = (eu, ew)
            for wt, e in (("unweighted", eu), ("weighted", ew)):
                for m in METRICS:
                    rows.append(dict(model=name, year=y, weighting=wt, metric=m, value=e.values[m], se=e.se(m)))
    tab = pd.DataFrame(rows)
    tab.to_csv(OUT / "metrics_us_2014_2018.csv", index=False)

    margins = {"floor": FLOOR, "unweighted": {}, "weighted": {}}
    for wi, wt in enumerate(("unweighted", "weighted")):
        mg = margins[wt]
        # delta (primary, prereg 6): largest deviation of a year 2014-2018 from the 2014-2018 baseline mean
        # (seed-mean trajectories), floored. Kept for transparency: the largest change from 2014.
        traj = {m: np.mean([[est[(f"gbm_s{s}", y)][wi].values[m] for y in YEARS] for s in SEEDS], axis=0)
                for m in METRICS}
        mg["baseline_mean"] = {m: float(traj[m].mean()) for m in METRICS}
        mg["deviation_from_baseline_by_year"] = {m: dict(zip(map(str, YEARS), (traj[m] - traj[m].mean()).tolist()))
                                                 for m in METRICS}
        mg["delta_raw"] = {m: float(np.max(np.abs(traj[m] - traj[m].mean()))) for m in METRICS}
        mg["delta"] = {m: max(mg["delta_raw"][m], FLOOR) for m in METRICS}
        mean_change = {m: [np.mean([change(est[(f"gbm_s{s}", y)][wi], est[(f"gbm_s{s}", 2014)][wi])[0][m]
                                    for s in SEEDS]) for y in YEARS[1:]] for m in METRICS}
        mg["max_change_from_2014"] = {m: max(abs(v) for v in mean_change[m]) for m in METRICS}
        mg["mean_change_by_year"] = {m: dict(zip(map(str, YEARS[1:]), mean_change[m])) for m in METRICS}
        # epsilon: post-processed DP models
        mg["epsilon"], mg["epsilon_raw"] = {}, {}
        for g in ("race", "sex"):
            dp = [abs(np.mean([est[(f"post_dp_{g}_s{s}", y)][wi].values[f"dp_{g}"] for s in SEEDS])) for y in YEARS]
            mg["epsilon_raw"][g] = max(dp)
            mg.setdefault("post_dp_per_seed_by_year", {})[g] = {
                str(y): [est[(f"post_dp_{g}_s{s}", y)][wi].values[f"dp_{g}"] for s in SEEDS] for y in YEARS}
            mg["epsilon"][g] = max(max(dp), FLOOR)
        # same rule for the EO-post-processed models (secondary 8.2)
        mg["epsilon_eo"], mg["epsilon_eo_raw"] = {}, {}
        for g in ("race", "sex"):
            eo = [abs(np.mean([est[(f"post_eo_{g}_s{s}", y)][wi].values[f"eo_{g}"] for s in SEEDS])) for y in YEARS]
            mg["epsilon_eo_raw"][g] = max(eo)
            mg["epsilon_eo"][g] = max(max(eo), FLOOR)

    # ---- geographic yardstick (2014, per-state models) ----
    df14, y14 = frames[2014], labels[2014]
    st14 = df14["ST"].to_numpy()
    test14 = state_split(df14, 0)
    geo_rows, own = [], {}
    for s in states:
        pred = load_pred(f"state{s}_gbm_s0", 2014, df14)
        m_own = (st14 == s) & test14
        own[s] = estimates(pred[m_own], y14[m_own], df14[m_own].reset_index(drop=True), split=True)
        for t in states:
            if t == s:
                continue
            m_t = st14 == t
            e_t = estimates(pred[m_t], y14[m_t], df14[m_t].reset_index(drop=True))
            for wi, wt in enumerate(("unweighted", "weighted")):
                d, cov = change(e_t[wi], own[s][wi])
                for k, m in enumerate(METRICS):
                    se = float(np.sqrt(cov[k, k]))
                    geo_rows.append(dict(source=s, target=t, weighting=wt, metric=m, delta=d[m], se=se,
                                         abs_corrected=noise_corrected_abs(d[m], se)))
    geo = pd.DataFrame(geo_rows)
    counts = geo.groupby(["weighting", "metric"]).size()
    assert (counts == len(states) * (len(states) - 1)).all() and len(counts) == 2 * len(METRICS), counts
    geo.to_csv(OUT / "geographic_pairs_2014.csv", index=False)
    for wt in ("unweighted", "weighted"):
        g = geo[geo.weighting == wt].groupby("metric")["abs_corrected"].median()
        margins[wt]["G"] = {m: float(g[m]) for m in METRICS}
        # per-state reference for C8: median geographic change from each source state
        margins[wt]["G_by_source_state"] = {
            m: {str(s): float(v) for s, v in
                geo[(geo.weighting == wt) & (geo.metric == m)].groupby("source")["abs_corrected"].median().items()}
            for m in ("dp_race", "eo_race", "dp_sex", "accuracy")}
    margins["states"] = states

    # ---- recoding artefact at 2018 (raw codes vs harmonised), seed 0 ----
    rec = {}
    for y in YEARS:
        eu_raw, eu_h = est[("rawgbm_s0", y)][0], est[("gbm_s0", y)][0]
        rec[str(y)] = {m: {"raw": eu_raw.values[m], "harmonised": eu_h.values[m]} for m in METRICS}
    (OUT / "recoding_check.json").write_text(json.dumps(rec, indent=1))
    (OUT / "margins.json").write_text(json.dumps(margins, indent=1))
    # estimates of every US model-year (values and covariance), reused by Stage B for the baseline
    store = {f"{n}|{y}|{wt}": {"values": e.values, "cov": e.cov.tolist(), "n": e.n}
             for (n, y), pair in est.items() for wt, e in zip(("unweighted", "weighted"), pair)}
    (OUT / "estimates_2014_2018.json").write_text(json.dumps(store))

    # ---- console summary ----
    pd.set_option("display.width", 220)
    u = tab[(tab.weighting == "unweighted") & tab.model.isin(
        ["gbm_s0", "post_dp_race_s0", "post_dp_sex_s0", "expgrad_dp_race_s0", "lfr_race_s0", "rawgbm_s0"])]
    print(u.pivot_table(index=["model", "metric"], columns="year", values="value").round(4).to_string())
    for wt in ("unweighted", "weighted"):
        mg = margins[wt]
        print(f"\n[{wt}] delta:", {k: round(v, 4) for k, v in mg["delta"].items()},
              "\n  raw max deviation from baseline:", {k: round(v, 4) for k, v in mg["delta_raw"].items()},
              "\n  max change from 2014:", {k: round(v, 4) for k, v in mg["max_change_from_2014"].items()},
              "\n  epsilon:", {k: round(v, 4) for k, v in mg["epsilon_raw"].items()},
              "\n  G:", {k: round(v, 4) for k, v in mg["G"].items()})


if __name__ == "__main__":
    main()
