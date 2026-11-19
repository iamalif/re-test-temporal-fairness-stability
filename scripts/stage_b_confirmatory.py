"""Stage B, confirmatory analysis (pre-registration sections 5-7). Runs only after the plan is archived:
loading any year after 2018 requires prereg/ARCHIVED (src/data.py).

Confirmatory family (Bonferroni, alpha = 0.05/6 per test): C1, C2, C3, C4, C6, C7.
Reported with the same machinery but outside the family: C5 (EO race; secondary because the anticipated SE makes
"holds" nearly unreachable, results/validation/inference_validation.json) and C8 (per-state counts; descriptive,
because the 20 state comparisons share observations and no valid joint null was pre-specified; QA 1, #1).

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

from analysis import (METRICS, REP, Estimate, NotComputable, change, compare_stability, household_ids, inflate,
                      noise_corrected_abs, sign_count, split_multiplier, three_way, unweighted, weighted)
from common import label, load_year, state_split
from pipeline import MANIFEST, SEEDS, SMOKE, load_pred, train_year_of, verify_inventory

FAMILY = ("C1", "C2", "C3", "C4", "C6", "C7")
ALPHA = 0.05 / len(FAMILY)
ALPHA_SECONDARY = 0.05
ALL_YEARS = (2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
BASE_YEARS = (2014, 2015, 2016, 2017, 2018)
Y_RACE, Y_SEX = 2019, 2024
OUT = ROOT / "results" / "stage_b"
MARGINS = ROOT / "results" / "stage_a" / "margins.json"
WT = ("unweighted", "weighted")
if SMOKE:   # code test on original-cohort years only: 2017 and 2018 stand in for 2019 and 2024
    Y_RACE, Y_SEX, ALL_YEARS = 2017, 2018, (2014, 2015, 2016, 2017, 2018)
    OUT = ROOT / "data" / "derived" / "smoke_stage_b"
    MARGINS = ROOT / "data" / "derived" / "smoke_stage_a" / "margins.json"


def frame(year):
    df = load_year(year, columns=["PINCP", "RAC1P", "SEX", "ST", "SERIALNO", "PWGTP"] + REP)
    if SMOKE:
        df = df.sample(n=int(SMOKE), random_state=0).reset_index(drop=True)
    return df


def estimate(name, year, df, seed=0, rows=None, rule=">", train_year=2014):
    """(unweighted, weighted) Estimate of a frozen model on one year (its training year: test split of its seed,
    with the pre-specified split-variance multipliers applied)."""
    pred = load_pred(name, year, df)
    keep = state_split(df, seed) if year == train_year else np.ones(len(df), bool)
    if rows is not None:
        keep &= rows
    y = label(df, rule=rule)
    sub = df[keep].reset_index(drop=True)
    eu = Estimate.from_unweighted(unweighted(pred[keep], y[keep], sub), household_ids(sub))
    ew = Estimate.from_weighted(weighted(pred[keep], y[keep], sub), int(keep.sum()))
    if year == train_year and not SMOKE:
        eu, ew = inflate(eu, split_multiplier("unweighted")), inflate(ew, split_multiplier("weighted"))
    return eu, ew


_STORE = {}


def stored(name, year, wt):
    """Stage A estimate (values, covariance) of a US model in an original-cohort year."""
    if not _STORE:
        _STORE.update(json.loads((MARGINS.parent / "estimates_2014_2018.json").read_text()))
    e = _STORE[f"{name}|{year}|{wt}"]
    return Estimate(e["values"], np.array(e["cov"]), e["n"])     # split multipliers already applied in Stage A


def seed_mean_dev_from_baseline(family, year, frames, metric, wi):
    """Seed-mean deviation of m(year) from the model's 2014-2018 baseline mean B (equal weight per year), and the
    mean per-seed SE (a valid upper bound for the SE of the seed mean). Var(B) = sum_t Var(m_t) / 25
    (independent years); Var(m(year) - B) = Var(m_year) + Var(B). Per-seed values are kept as diagnostics."""
    wt, k = WT[wi], METRICS.index(metric)
    ds, ses = [], []
    for s in SEEDS:
        base = [stored(f"{family}_s{s}", y, wt) for y in BASE_YEARS]
        b = np.mean([e.values[metric] for e in base])
        var_b = sum(e.cov[k, k] for e in base) / 25.0
        e_t = estimate(f"{family}_s{s}", year, frames[year], s)[wi]
        ds.append(e_t.values[metric] - b)
        ses.append(np.sqrt(e_t.cov[k, k] + var_b))
    return float(np.mean(ds)), float(np.mean(ses)), {"per_seed_deviation": ds, "per_seed_se": ses}


def seed_mean_level(family, year, frames, metric, wi):
    vals, ses = [], []
    for s in SEEDS:
        e = estimate(f"{family}_s{s}", year, frames[year], s)[wi]
        vals.append(e.values[metric]); ses.append(e.se(metric))
    return float(np.mean(vals)), float(np.mean(ses)), {"per_seed_level": vals, "per_seed_se": ses}


def guarded(fn):
    """Failure policy (prereg 7.5): a claim that cannot be computed is reported as such, never dropped."""
    try:
        return fn()
    except NotComputable as e:
        return {"decision": "not computable", "reason": str(e)}


def main():
    verify_inventory(years=sorted({2014, Y_RACE, Y_SEX}))
    OUT.mkdir(parents=True, exist_ok=True)
    margins = json.loads(MARGINS.read_text())
    manifest = json.loads(MANIFEST.read_text())
    frames = {y: frame(y) for y in (2014, Y_RACE, Y_SEX)}
    res = {"family": list(FAMILY), "alpha_per_test": ALPHA, "alpha_secondary": ALPHA_SECONDARY}
    for wi, wt in enumerate(WT):
        mg, r = margins[wt], {}

        def dev(metric, year, margin, alpha):
            d, se, diag = seed_mean_dev_from_baseline("gbm", year, frames, metric, wi)
            return three_way(d, se, margin, alpha) | diag

        def lev(family, metric, year, margin):
            v, se, diag = seed_mean_level(family, year, frames, metric, wi)
            return three_way(v, se, margin, ALPHA) | diag

        r["C1"] = guarded(lambda: dev("dp_race", Y_RACE, mg["delta"]["dp_race"], ALPHA))
        r["C2"] = guarded(lambda: dev("dp_sex", Y_SEX, mg["delta"]["dp_sex"], ALPHA))
        r["C3"] = guarded(lambda: lev("post_dp_race", "dp_race", Y_RACE, mg["epsilon"]["race"]))
        r["C4"] = guarded(lambda: lev("post_dp_sex", "dp_sex", Y_SEX, mg["epsilon"]["sex"]))
        r["C5"] = guarded(lambda: dev("eo_race", Y_RACE, mg["delta"]["eo_race"], ALPHA_SECONDARY)
                          | {"status": "secondary (outside the family)"})
        r["C6"] = guarded(lambda: dev("eo_sex", Y_SEX, mg["delta"]["eo_sex"], ALPHA))

        def c7():
            # joint seed-mean changes from 2014 of DP_race and accuracy; covariance = mean of per-seed covariances
            # (upper bound of the seed-mean covariance in PSD order)
            i_dp, i_acc = METRICS.index("dp_race"), METRICS.index("accuracy")
            dd, covs = [], []
            for s in SEEDS:
                dlt, cov = change(estimate(f"gbm_s{s}", Y_RACE, frames[Y_RACE], s)[wi],
                                  estimate(f"gbm_s{s}", 2014, frames[2014], s)[wi])
                dd.append([dlt["dp_race"], dlt["accuracy"]])
                covs.append(cov[np.ix_([i_dp, i_acc], [i_dp, i_acc])])
            m, cov2 = np.mean(dd, axis=0), np.mean(covs, axis=0)
            return compare_stability(m[0], m[1], cov2, mg["G"]["dp_race"], mg["G"]["accuracy"], ALPHA) | {
                "per_seed_changes": dd}
        r["C7"] = guarded(c7)

        def c8():
            temporal, geographic, detail = [], [], {}
            k = METRICS.index("dp_race")
            for st in margins["states"]:
                name = f"state{st}_gbm_s0"
                e0 = estimate(name, 2014, frames[2014], 0, rows=(frames[2014]["ST"] == st).to_numpy())[wi]
                e1 = estimate(name, Y_RACE, frames[Y_RACE], 0, rows=(frames[Y_RACE]["ST"] == st).to_numpy())[wi]
                dlt, cov = change(e1, e0)
                se = float(np.sqrt(cov[k, k]))
                t, g = noise_corrected_abs(dlt["dp_race"], se), mg["G_by_source_state"]["dp_race"][str(st)]
                temporal.append(t); geographic.append(g)
                detail[str(st)] = {"change": dlt["dp_race"], "se": se, "ci95": [dlt["dp_race"] - 1.96 * se,
                                   dlt["dp_race"] + 1.96 * se], "temporal_corrected": t, "geographic": g}
            return sign_count(temporal, geographic) | {"states": detail}
        r["C8"] = guarded(c8)
        # sensitivity of each decision to the margin (prereg 6): decisions over margins 0.005-0.03
        grid = [round(0.005 + 0.0025 * i, 4) for i in range(11)]
        for c in ("C1", "C2", "C3", "C4", "C5", "C6"):
            if "se" in r[c]:
                a = r[c]["alpha"]
                r[c]["margin_curve"] = {str(m): three_way(r[c]["estimate"], r[c]["se"], m, a)["decision"] for m in grid}
        res[wt] = r
    res["weighting_sensitive"] = [c for c in FAMILY
                                  if res["unweighted"][c]["decision"] != res["weighted"][c]["decision"]]
    (OUT / "confirmatory.json").write_text(json.dumps(res, indent=1, default=float))
    for c in ("C1", "C2", "C3", "C4", "C5", "C6", "C7"):
        print(c, "unweighted:", res["unweighted"][c]["decision"], "| weighted:", res["weighted"][c]["decision"])
    print("C8 (descriptive):", {wt: {k: res[wt]["C8"].get(k) for k in ("smaller", "ties", "larger")} for wt in WT})

    # trajectories of every US model, all years, nominal label (">" and ">=")
    rows = []
    for y in ALL_YEARS:
        df = frame(y)
        for name, meta in manifest.items():
            ty = train_year_of(name, manifest)
            if name.startswith("state") or (name.startswith("rawgbm") and y > 2018) or y < ty:
                continue
            for rule in (">", ">="):
                for wt, e in zip(WT, estimate(name, y, df, meta["seed"], rule=rule, train_year=ty)):
                    for m in METRICS:
                        rows.append(dict(model=name, year=y, rule=rule, weighting=wt, metric=m,
                                         value=e.values[m], se=e.se(m)))
    pd.DataFrame(rows).to_csv(OUT / "trajectories.csv", index=False)


if __name__ == "__main__":
    main()
