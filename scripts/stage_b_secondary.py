"""Stage B, secondary analyses (pre-registration section 8). Runs only after archiving (src/data.py guard).
Secondary analyses are outside the family-wise error control; intervals are 95% unless stated.

  8.2 other interventions (ExpGrad DP, LFR, EO post-processing): within their own 2014-2018 envelope (rule C3)
  8.3 label definitions: nominal '>', '>=', inflation-anchored, base-rate-anchored (accuracy and EO)
  8.4 DiNardo-Fortin-Lemieux reweighting: change split into a composition part and a residual
      ("conditional change plus approximation error"), with reliability diagnostics that govern interpretation
  8.5 theory predictions P1-P3 (P1 uses per-state domain-classifier AUCs; slow: about 400 classifiers)
  8.6 per-year-scaling pipeline: the frozen peryear_gbm models (each year standardised with its own scaler)
  8.8 per-state DP-post-processed models: |DP| in the own state later vs in other states in 2014
  8.9 models deployed in 2018 instead of 2014: change from 2018 to each later year, with SEs
  8.10 sensitivity without race as a feature: the C2, C4 and C6 rules on the frozen no-race models
Writes results/stage_b/secondary.json and secondary_labels.csv.  Usage: python scripts/stage_b_secondary.py [--skip-p1]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import openpyxl
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

from analysis import METRICS, NotComputable, change, estimates, household_ids, point, three_way
from common import BLACK, WHITE, load_year, state_split
from pipeline import SEEDS, SMOKE, design, load_pred, provenance, verify_inventory, year_frame

ALPHA = 0.05                       # secondary: per-analysis level, no family-wise claim
Y_RACE, Y_SEX = 2019, 2024
YEARS = (2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
OUT = ROOT / "results" / "stage_b"
STAGE_A = ROOT / "results" / "stage_a"
if SMOKE:
    Y_RACE, Y_SEX, YEARS = 2017, 2018, (2014, 2015, 2016, 2017, 2018)
    OUT, STAGE_A = ROOT / "data" / "derived" / "smoke_stage_b", ROOT / "data" / "derived" / "smoke_stage_a"
CHECK_TOL = 0.005                  # DP falsification check of the decomposition
BAL_BASE, BAL_K = 0.02, 3.0        # balance after reweighting, per group (D026): the largest SMD over quantitative
                                   # features and indicators of categories with pooled share >= 1% must not exceed
                                   # BAL_BASE + BAL_K * sqrt(1/ESS_group + 1/n_target_group) (sampling-noise allowance)
CAT_MIN_SHARE = 0.01
QUANT_FEATURES = ("AGEP", "WKHP")  # every other harmonised feature is a nominal or ordinal category code
CLIP_TOL = 0.005                   # clipping sensitivity: |residual(no clip) - residual(99.9%)|, P2 metrics
P2_METRICS = ("accuracy", "eo_race", "eo_sex")
CLIPS = {"q999": 0.999, "q99": 0.99, "none": None}
BASE_RATE_GRID = (20000, 150000, 1000)   # base-rate anchoring: search grid (inclusive), $1000 steps


# ---------------- data and labels ----------------

def frame(year):
    df = year_frame(year)                                  # harmonised features + PINCP, ST, SERIALNO, PWGTP ...
    adj = load_year(year, columns=["ADJINC"])["ADJINC"]
    if SMOKE:
        adj = adj.sample(n=int(SMOKE), random_state=0).reset_index(drop=True)
    df["ADJINC"] = adj.to_numpy()
    return df


def cpi_annual() -> dict[int, float]:
    wb = openpyxl.load_workbook(ROOT / "data/raw/cpi/r-cpi-u-rs-allitems.xlsx", read_only=True, data_only=True)
    rows = list(wb.worksheets[0].iter_rows(values_only=True))
    hdr = next(i for i, r in enumerate(rows) if r and r[0] == "YEAR")
    col = list(rows[hdr]).index("AVG")
    return {int(r[0]): float(r[col]) for r in rows[hdr + 1:] if r and isinstance(r[0], (int, float)) and r[col]}


def thresholds(frames: dict) -> dict:
    """Inflation-anchored and base-rate-anchored thresholds per year (section 8.3).
    Base-rate anchoring: the threshold on the $1000 grid [20000, 150000] whose share above it (strict >) is closest
    to the 2014 nominal share; ties go to the lowest threshold; a grid-boundary solution is flagged."""
    cpi = cpi_annual()
    for y, f in frames.items():
        assert f["ADJINC"].nunique() == 1, f"ADJINC not constant in {y}"
    adj = {y: float(f["ADJINC"].iloc[0]) for y, f in frames.items()}
    out = {"cpi": {y: cpi[y] for y in frames}, "adjinc": adj, "inflation": {}, "base_rate": {},
           "base_rate_at_grid_boundary": {}}
    p14 = float((frames[2014]["PINCP"] > 50000).mean())
    lo, hi, step = BASE_RATE_GRID
    grid = np.arange(lo, hi + 1, step)
    for y, f in frames.items():
        out["inflation"][y] = float(round(50000 * adj[2014] / adj[y] * cpi[y] / cpi[2014], -3))
        inc = f["PINCP"].to_numpy()
        rates = np.array([(inc > t).mean() for t in grid])
        t = float(grid[np.argmin(np.abs(rates - p14))])          # argmin returns the first (lowest) on ties
        out["base_rate"][y] = t
        out["base_rate_at_grid_boundary"][y] = t in (lo, hi)
    out["base_rate_2014_nominal"] = p14
    return out


def labels_for(df, year, thr):
    inc = df["PINCP"].to_numpy()
    return {"nominal": inc > 50000, "geq": inc >= 50000,
            "inflation": inc > thr["inflation"][year], "base_rate": inc > thr["base_rate"][year]}


def rows_for(year, seed, df, train_year=2014):
    return state_split(df, seed) if year == train_year else np.ones(len(df), bool)


def dp_race_of(pred, df):
    """White - Black positive rate only (NaN if a group is empty: reported as not computable, prereg 7.5)."""
    r = df["RAC1P"].to_numpy()
    w, b = r == WHITE, r == BLACK
    return float(pred[w].mean() - pred[b].mean()) if w.any() and b.any() else float("nan")


def est_u(pred, y, df, split=False):
    """Unweighted estimate from the central builder (split multipliers on training-year test splits)."""
    return estimates(pred, y, df, split=split, apply_split_multiplier=not SMOKE, with_weighted=False)[0]


def three_way_or_nc(*args, **kw):
    try:
        return three_way(*args, **kw)
    except NotComputable as e:
        return {"decision": "not computable", "reason": str(e)}


# ---------------- 8.4 decomposition ----------------

def domain_probs(X0, X1, g0, g1, seed=0):
    """Cross-fitted P(sample = 1 | x) for the pooled rows. Folds keep households together (a household is never
    split between fitting and prediction), stratified by sample."""
    X = np.vstack([X0, X1]); d = np.r_[np.zeros(len(X0)), np.ones(len(X1))]
    groups = np.r_[np.char.add("a", np.asarray(g0, str)), np.char.add("b", np.asarray(g1, str))]
    p = np.zeros(len(X))
    for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(X, d, groups):
        clf = HistGradientBoostingClassifier(random_state=seed).fit(X[tr], d[tr])
        p[te] = clf.predict_proba(X[te])[:, 1]
    return p, d


def odds_weights(p, n0, n1, clip_q):
    p0 = np.clip(p[:n0], 1e-6, 1 - 1e-6)
    w = p0 / (1 - p0) * n0 / n1
    clipped = 0.0
    if clip_q is not None:
        cap = np.quantile(w, clip_q)
        clipped = float((w > cap).mean())
        w = np.minimum(w, cap)
    return w, clipped


def dfl_weights(X0, X1, g0, g1, seed=0):
    """Primary weights (99.9% clipping) and the cross-fitted domain AUC (household-grouped folds)."""
    p, d = domain_probs(X0, X1, g0, g1, seed)
    return odds_weights(p, len(X0), len(X1), 0.999)[0], float(roc_auc_score(d, p))


def balance(X0, w, X1, mask0, mask1) -> dict:
    """Balance between reweighted sample 0 and sample 1 within a group (QA 2, A4). Category codes are not treated as
    numbers: for each categorical feature, every category with pooled share >= 1% gets the standardised difference
    of its share, |p0 - p1| / sqrt(p(1 - p)); quantitative features (age, hours) get the usual SMD. Also reports the
    total-variation distance of each categorical feature (all categories). Features constant in both samples within
    the group (e.g. race within a race group) are skipped."""
    from harmonise import HARMONISED_FEATURES
    a, b = X0[mask0], X1[mask1]
    wa = w[mask0] / w[mask0].sum()
    worst, where, tvd = 0.0, None, {}
    for j, f in enumerate(HARMONISED_FEATURES):
        x0, x1 = a[:, j], b[:, j]
        if f in QUANT_FEATURES:
            sd = np.sqrt((x0.var() + x1.var()) / 2)
            if sd > 0:
                v = abs(float(np.dot(wa, x0) - x1.mean())) / sd
                if v > worst:
                    worst, where = v, f
            continue
        cats = np.union1d(np.unique(x0), np.unique(x1))
        p0 = np.array([wa[x0 == c].sum() for c in cats])
        p1 = np.array([(x1 == c).mean() for c in cats])
        tvd[f] = float(np.abs(p0 - p1).sum() / 2)
        pp = (p0 + p1) / 2
        ok = (pp >= CAT_MIN_SHARE) & (pp * (1 - pp) > 0)
        if ok.any():
            v = np.abs(p0 - p1)[ok] / np.sqrt(pp[ok] * (1 - pp[ok]))
            i = int(np.argmax(v))
            if v[i] > worst:
                worst, where = float(v[i]), f"{f}={cats[ok][i]:g}"
    ess = float(w[mask0].sum() ** 2 / (w[mask0] ** 2).sum())
    limit = BAL_BASE + BAL_K * np.sqrt(1 / ess + 1 / max(int(mask1.sum()), 1))
    return {"max_smd": float(worst), "worst": where, "tvd": tvd, "ess": ess, "n_target": int(mask1.sum()),
            "limit": float(limit), "passes": bool(worst <= limit)}


_DOMAIN_CACHE: dict = {}


def decompose(name, seed, year, frames, thr, label_key="nominal"):
    f0, f1 = frames[2014], frames[year]
    r0 = rows_for(2014, seed, f0)
    s0 = f0[r0].reset_index(drop=True)
    X0, X1 = design(s0, "harmonised"), design(f1, "harmonised")
    y0 = labels_for(s0, 2014, thr)[label_key]
    y1 = labels_for(f1, year, thr)[label_key]
    p0 = load_pred(name, 2014, f0)[r0]
    p1 = load_pred(name, year, f1)
    key = (seed, year)                      # the domain model does not depend on the label definition
    if key not in _DOMAIN_CACHE:
        _DOMAIN_CACHE[key] = domain_probs(X0, X1, household_ids(s0), household_ids(f1), seed)
    p, d = _DOMAIN_CACHE[key]
    auc = float(roc_auc_score(d, p))
    m0, m1 = point(p0, y0, s0), point(p1, y1, f1)
    by_clip, diag = {}, {}
    for tag, q in CLIPS.items():
        w, clipped = odds_weights(p, len(X0), len(X1), q)
        mcf = point(p0, y0, s0, w)
        by_clip[tag] = {"counterfactual": mcf, "composition": {m: mcf[m] - m0[m] for m in METRICS},
                        "residual": {m: m1[m] - mcf[m] for m in METRICS}, "share_clipped": clipped}
        if tag == "q999":
            race0, race1 = s0["RAC1P"].to_numpy(), f1["RAC1P"].to_numpy()
            sex0, sex1 = s0["SEX"].to_numpy(), f1["SEX"].to_numpy()
            groups = {"white": (race0 == WHITE, race1 == WHITE), "black": (race0 == BLACK, race1 == BLACK),
                      "male": (sex0 == 1, sex1 == 1), "female": (sex0 == 2, sex1 == 2)}
            diag = {"ess_fraction": float(w.sum() ** 2 / (w ** 2).sum() / len(w)),
                    "max_weight_over_mean": float(w.max() / w.mean()),
                    "share_2014_p_below_0.01": float((p[:len(X0)] < 0.01).mean()),
                    "share_target_p_above_0.99": float((p[len(X0):] > 0.99).mean()),
                    "balance_by_group": {g: balance(X0, w, X1, a, b) for g, (a, b) in groups.items()},
                    "balance_by_group_before_reweighting": {g: balance(X0, np.ones(len(X0)), X1, a, b)
                                                            for g, (a, b) in groups.items()},
                    "balance_all": balance(X0, w, X1, np.ones(len(X0), bool), np.ones(len(X1), bool))}
    prim = by_clip["q999"]
    dp_check = {g: {"residual": prim["residual"][f"dp_{g}"], "passes": abs(prim["residual"][f"dp_{g}"]) <= CHECK_TOL}
                for g in ("race", "sex")}
    clip_shift = {m: abs(by_clip["none"]["residual"][m] - prim["residual"][m]) for m in P2_METRICS}
    reliable = (all(v["passes"] for v in dp_check.values())
                and all(v["passes"] for v in diag["balance_by_group"].values())
                and all(np.isfinite(v) and v <= CLIP_TOL for v in clip_shift.values()))
    return {"model": name, "year": year, "label": label_key, "auc_2014_vs_year": auc, "m2014": m0, "m_year": m1,
            "counterfactual": prim["counterfactual"], "composition": prim["composition"],
            "residual": prim["residual"], "by_clipping": by_clip, "diagnostics": diag,
            "dp_check": dp_check, "clip_sensitivity": clip_shift, "reliable": bool(reliable),
            "interpretation": ("residual = conditional change plus approximation error" if reliable else
                               "unreliable: composition/residual split not interpreted; P2 suppressed")}


# ---------------- 8.5 theory predictions ----------------

def p3_prior_shift(m0, m1, g):
    """DP change predicted by group-conditional prior shift alone (Asiaee and Aryan), with 2014 TPR/FPR.
    The ratio predicted/observed is unstable when the observed change is small and is not a variance share."""
    pred = sum(sign * (m0[f"tpr_{g}{k}"] - m0[f"fpr_{g}{k}"]) * (m1[f"base_rate_{g}{k}"] - m0[f"base_rate_{g}{k}"])
               for sign, k in ((1, "1"), (-1, "2")))
    obs = m1[f"dp_{g}"] - m0[f"dp_{g}"]
    return {"observed_dp_change": obs, "predicted_by_prior_shift": pred,
            "ratio_predicted_to_observed": (pred / obs) if abs(obs) >= CHECK_TOL else None,
            "abs_eo_change": abs(m1[f"eo_{g}"] - m0[f"eo_{g}"]), "abs_dp_change": abs(obs)}


def domain_auc(Xa, Xb, ga, gb, seed=0):
    return dfl_weights(Xa, Xb, ga, gb, seed)[1]


def p1_auc(frames, states, year, drop=()):
    """drop: harmonised features left out of the domain classifier (sensitivity: place of birth separates states
    almost by construction, because most people live in the state where they were born)."""
    from harmonise import HARMONISED_FEATURES
    keep = [i for i, f in enumerate(HARMONISED_FEATURES) if f not in drop]
    f0, f1 = frames[2014], frames[year]
    st0, st1 = f0["ST"].to_numpy(), f1["ST"].to_numpy()
    X0, X1 = design(f0, "harmonised")[:, keep], design(f1, "harmonised")[:, keep]
    h0, h1 = household_ids(f0), household_ids(f1)
    res = {}
    for s in states:
        a = st0 == s
        temporal = domain_auc(X0[a], X1[st1 == s], h0[a], h1[st1 == s])
        geo = [domain_auc(X0[a], X0[st0 == t], h0[a], h0[st0 == t]) for t in states if t != s]
        res[str(s)] = {"temporal_auc": temporal, "geographic_auc_median": float(np.median(geo))}
    k = sum(v["temporal_auc"] < v["geographic_auc_median"] for v in res.values())
    return {"by_state": res, "states_with_smaller_temporal_shift": k, "n_states": len(states)}


# ---------------- main ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-p1", action="store_true")
    a = ap.parse_args()
    verify_inventory(YEARS)                 # preflight: models, hashes, prediction provenance
    OUT.mkdir(parents=True, exist_ok=True)
    margins = json.loads((STAGE_A / "margins.json").read_text())
    frames = {y: frame(y) for y in YEARS}
    thr = thresholds(frames)
    res = {"alpha": ALPHA, "thresholds": thr, "provenance": provenance()}

    # 8.2 other interventions: envelope rule as C3, each with its own 2014-2018 envelope
    band = {}
    for name in ("expgrad_dp_race_s0", "lfr_race_s0"):
        vals = []
        for y in (2014, 2015, 2016, 2017, 2018):
            f = frames[y]; r = rows_for(y, 0, f)
            vals.append(point(load_pred(name, y, f)[r], labels_for(f[r], y, thr)["nominal"],
                              f[r].reset_index(drop=True))["dp_race"])
        eps = max(max(abs(v) for v in vals), margins["floor"])
        f = frames[Y_RACE]
        e = est_u(load_pred(name, Y_RACE, f), labels_for(f, Y_RACE, thr)["nominal"], f)
        band[name] = three_way_or_nc(e.values["dp_race"], e.se("dp_race"), eps, ALPHA) | {"dp_2014_2018": vals}
    for g, yr in (("race", Y_RACE), ("sex", Y_SEX)):
        f = frames[yr]; yy = labels_for(f, yr, thr)["nominal"]; vals, ses = [], []
        for sd in SEEDS:
            e = est_u(load_pred(f"post_eo_{g}_s{sd}", yr, f), yy, f)
            vals.append(e.values[f"eo_{g}"]); ses.append(e.se(f"eo_{g}"))
        band[f"post_eo_{g}"] = three_way_or_nc(float(np.mean(vals)), float(np.mean(ses)),
                                         margins["unweighted"]["epsilon_eo"][g], ALPHA) | {
                                             "year": yr, "per_seed": vals}
    res["8.2_other_interventions"] = band

    # 8.3 label definitions: every metric of every seed-0 model, every year
    rows = []
    for y in YEARS:
        f = frames[y]
        for name in ("gbm_s0", "post_dp_race_s0", "post_eo_race_s0", "post_dp_sex_s0", "post_eo_sex_s0",
                     "expgrad_dp_race_s0", "lfr_race_s0"):
            r = rows_for(y, 0, f); sub = f[r].reset_index(drop=True); pred = load_pred(name, y, f)[r]
            for lk, yy in labels_for(sub, y, thr).items():
                e = est_u(pred, yy, sub, split=(y == 2014))
                for m in METRICS:
                    rows.append(dict(model=name, year=y, label=lk, metric=m, value=e.values[m], se=e.se(m)))
    pd.DataFrame(rows).to_csv(OUT / "secondary_labels.csv", index=False)

    # 8.4 decomposition and 8.5 P2/P3 (P2 only when the decomposition passes its reliability rule)
    dec = []
    for name, year in (("gbm_s0", Y_RACE), ("gbm_s0", Y_SEX)):
        for lk in ("nominal", "inflation", "base_rate"):
            d = decompose(name, 0, year, frames, thr, lk)
            d["P2_residual_larger"] = ({m: abs(d["residual"][m]) > abs(d["composition"][m])
                                        for m in ("accuracy", "eo_race", "eo_sex")} if d["reliable"]
                                       else "suppressed (decomposition unreliable)")
            d["P3"] = {g: p3_prior_shift(d["m2014"], d["m_year"], g) for g in ("race", "sex")}
            dec.append(d)
    res["8.4_decomposition"] = dec

    # 8.6 per-year-scaling pipeline: frozen peryear_gbm models vs the primary frozen-scaler gbm (seed means)
    view = {}
    for y in YEARS:
        f = frames[y]
        per = {}
        for fam in ("peryear_gbm", "gbm"):
            ests = []
            for sd in SEEDS:
                r = rows_for(y, sd, f)
                ests.append(est_u(load_pred(f"{fam}_s{sd}", y, f)[r], labels_for(f[r], y, thr)["nominal"],
                                  f[r].reset_index(drop=True), split=(y == 2014)))
            per[fam] = {m: {"value": float(np.mean([e.values[m] for e in ests])),
                            "se": float(np.mean([e.se(m) for e in ests]))} for m in METRICS}
        view[str(y)] = per
    res["8.6_per_year_scaling"] = view

    # 8.8 per-state DP-post-processed models (descriptive; unweighted point estimates)
    f14, ft = frames[2014], frames[Y_RACE]
    st14, stt = f14["ST"].to_numpy(), ft["ST"].to_numpy()
    test14 = state_split(f14, 0)
    y14, yt = labels_for(f14, 2014, thr)["nominal"], labels_for(ft, Y_RACE, thr)["nominal"]
    per_state = {}
    for st in margins["states"]:
        name = f"state{st}_post_dp_race_s0"
        p14, pt = load_pred(name, 2014, f14), load_pred(name, Y_RACE, ft)
        own = (st14 == st) & test14
        dp_own14 = dp_race_of(p14[own], f14[own])
        m_t = stt == st
        dp_own_t = dp_race_of(pt[m_t], ft[m_t])
        geo = [dp_race_of(p14[st14 == o], f14[st14 == o]) for o in margins["states"] if o != st]
        per_state[str(st)] = {"dp_own_2014": dp_own14, "dp_own_later": dp_own_t,
                              "median_abs_dp_other_states_2014": float(np.nanmedian(np.abs(geo)))}
    ok = {k_: v for k_, v in per_state.items() if np.isfinite(v["dp_own_later"])
          and np.isfinite(v["median_abs_dp_other_states_2014"])}
    k = sum(abs(v["dp_own_later"]) < v["median_abs_dp_other_states_2014"] for v in ok.values())
    res["8.8_state_post_processing"] = {"by_state": per_state, "states_where_temporal_transfer_is_better": k,
                                        "n_states": len(per_state), "n_states_computable": len(ok)}

    # 8.9 deployment in 2018: seed-mean levels, and changes from the 2018 test split with mean per-seed SEs
    later = [y for y in YEARS if y > 2018]
    dep = {}
    f18 = frames[2018]
    for fam in ("y2018_gbm", "y2018_post_dp_race", "y2018_post_dp_sex"):
        e18 = []
        for sd in SEEDS:
            r18 = state_split(f18, sd)
            e18.append(est_u(load_pred(f"{fam}_s{sd}", 2018, f18)[r18], labels_for(f18[r18], 2018, thr)["nominal"],
                             f18[r18].reset_index(drop=True), split=True))
        dep[fam] = {"2018": {m: float(np.mean([e.values[m] for e in e18])) for m in METRICS}}
        for y in later:
            f = frames[y]
            ey = [est_u(load_pred(f"{fam}_s{sd}", y, f), labels_for(f, y, thr)["nominal"], f) for sd in SEEDS]
            ch = [change(a_, b_) for a_, b_ in zip(ey, e18)]
            dep[fam][str(y)] = {m: {"level": float(np.mean([e.values[m] for e in ey])),
                                    "change_from_2018": float(np.mean([c[0][m] for c in ch])),
                                    "se": float(np.mean([np.sqrt(c[1][k, k]) for c in ch]))}
                                for k, m in enumerate(METRICS)}
    res["8.9_deployment_2018"] = dep

    # 8.10 sensitivity without race as a feature (sex endpoints; race coding changed in 2020): the C2, C4 and C6
    # rules applied to the frozen no-race models, with calibration constants from their own 2014-2018 estimates
    stored = json.loads((STAGE_A / "estimates_2014_2018.json").read_text())
    base_years = (2014, 2015, 2016, 2017, 2018)
    f = frames[Y_SEX]
    ysex = labels_for(f, Y_SEX, thr)["nominal"]
    nr = {}
    for key, fam, metric, kind in (("C2_norace", "norace_gbm", "dp_sex", "dev"),
                                   ("C4_norace", "norace_post_dp_sex", "dp_sex", "env"),
                                   ("C6_norace", "norace_gbm", "eo_sex", "dev")):
        k = METRICS.index(metric)
        hist = np.array([[stored[f"{fam}_s{sd}|{y}|unweighted"]["values"][metric] for y in base_years] for sd in SEEDS])
        hvar = np.array([[stored[f"{fam}_s{sd}|{y}|unweighted"]["cov"][k][k] for y in base_years] for sd in SEEDS])
        traj = hist.mean(0)
        ests = [est_u(load_pred(f"{fam}_s{sd}", Y_SEX, f), ysex, f) for sd in SEEDS]
        if kind == "dev":
            margin = max(float(np.max(np.abs(traj - traj.mean()))), margins["floor"])
            vals = [e.values[metric] - hist[i].mean() for i, e in enumerate(ests)]
            ses = [np.sqrt(e.cov[k, k] + hvar[i].sum() / 25) for i, e in enumerate(ests)]
        else:
            margin = max(float(np.max(np.abs(traj))), margins["floor"])
            vals = [e.values[metric] for e in ests]
            ses = [e.se(metric) for e in ests]
        nr[key] = three_way_or_nc(float(np.mean(vals)), float(np.mean(ses)), margin, ALPHA) | {
            "per_seed": vals, "calibration_constant": margin}
    res["8.10_without_race"] = nr

    if not a.skip_p1:
        res["8.5_P1"] = p1_auc(frames, margins["states"], Y_RACE)
        res["8.5_P1_without_birthplace"] = p1_auc(frames, margins["states"], Y_RACE, drop=("POBP_H",))
    (OUT / "secondary.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({"thresholds": thr["inflation"], "base_rate_thr": thr["base_rate"],
                      "8.2": {k: v["decision"] for k, v in band.items()},
                      "decomposition": [(d["model"], d["year"], d["label"], d["reliable"], d["dp_check"])
                                        for d in dec]}, indent=1, default=float))


if __name__ == "__main__":
    main()
