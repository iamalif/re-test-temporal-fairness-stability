"""Stage B, secondary analyses (pre-registration section 8). Runs only after archiving (src/data.py guard).

  8.2 other interventions (ExpGrad DP, LFR): |DP(2019)| within their own 2014-2018 band (rule C3)
  8.3 label definitions: nominal '>', '>=', inflation-anchored, base-rate-anchored (accuracy and EO)
  8.4 DiNardo-Fortin-Lemieux decomposition of change into composition and conditional components,
      with the built-in DP check (|DP conditional component| <= 0.005)
  8.5 theory predictions P1-P3 (P1 uses per-state domain-classifier AUCs; slow: about 400 classifiers)
  8.6 original-pipeline view: the seed-0 GBM with each year standardised separately
Writes results/stage_b/secondary_*.json / .csv.  Usage: uv run python scripts/stage_b_secondary.py [--skip-p1]
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import joblib
import numpy as np
import openpyxl
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from analysis import METRICS, Estimate, point, three_way, unweighted
from common import load_year, state_split
from harmonise import HARMONISED_FEATURES
from pipeline import MODELS, SMOKE, Scaler, design, load_pred, year_frame

ALPHA = 0.05 / 8
Y_RACE, Y_SEX = 2019, 2024
YEARS = (2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
OUT = ROOT / "results" / "stage_b"
STAGE_A = ROOT / "results" / "stage_a"
if SMOKE:
    Y_RACE, Y_SEX, YEARS = 2017, 2018, (2014, 2015, 2016, 2017, 2018)
    OUT, STAGE_A = ROOT / "data" / "derived" / "smoke_stage_b", ROOT / "data" / "derived" / "smoke_stage_a"
CHECK_TOL = 0.005


# ---------------- data and labels ----------------

def frame(year):
    df = year_frame(year)                                  # harmonised features + PINCP, ST, PWGTP ...
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
    """Inflation-anchored (c) and base-rate-anchored (d) thresholds per year (section 8.3)."""
    cpi = cpi_annual()
    adj = {y: float(f["ADJINC"].iloc[0]) for y, f in frames.items()}
    for y, f in frames.items():
        assert f["ADJINC"].nunique() == 1, f"ADJINC not constant in {y}"
    out = {"cpi": {y: cpi[y] for y in frames}, "adjinc": adj, "inflation": {}, "base_rate": {}}
    p14 = float((frames[2014]["PINCP"] > 50000).mean())
    grid = np.arange(20000, 150001, 1000)
    for y, f in frames.items():
        out["inflation"][y] = float(round(50000 * adj[2014] / adj[y] * cpi[y] / cpi[2014], -3))
        inc = f["PINCP"].to_numpy()
        rates = np.array([(inc > t).mean() for t in grid])
        out["base_rate"][y] = float(grid[np.argmin(np.abs(rates - p14))])
    out["base_rate_2014_nominal"] = p14
    return out


def labels_for(df, year, thr):
    inc = df["PINCP"].to_numpy()
    return {"nominal": inc > 50000, "geq": inc >= 50000,
            "inflation": inc > thr["inflation"][year], "base_rate": inc > thr["base_rate"][year]}


def rows_for(year, seed, df):
    return state_split(df, seed) if year == 2014 else np.ones(len(df), bool)


# ---------------- 8.4 decomposition ----------------

def dfl_weights(X0, X1, seed=0):
    """Cross-fitted odds weights that reweight sample 0 to the feature distribution of sample 1."""
    X = np.vstack([X0, X1]); d = np.r_[np.zeros(len(X0)), np.ones(len(X1))]
    p = np.zeros(len(X))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(X, d):
        clf = HistGradientBoostingClassifier(random_state=seed).fit(X[tr], d[tr])
        p[te] = clf.predict_proba(X[te])[:, 1]
    p0 = np.clip(p[: len(X0)], 1e-6, 1 - 1e-6)
    w = p0 / (1 - p0) * len(X0) / len(X1)
    w = np.minimum(w, np.quantile(w, 0.999))
    return w, float(roc_auc_score(d, p))


def decompose(name, seed, year, frames, thr, label_key="nominal"):
    f0, f1 = frames[2014], frames[year]
    r0 = rows_for(2014, seed, f0)
    s0 = f0[r0].reset_index(drop=True)
    X0, X1 = design(s0, "harmonised"), design(f1, "harmonised")
    y0 = labels_for(s0, 2014, thr)[label_key]
    y1 = labels_for(f1, year, thr)[label_key]
    p0 = load_pred(name, 2014, len(f0))[r0]
    p1 = load_pred(name, year, len(f1))
    w, auc = dfl_weights(X0, X1, seed)
    m0, m1, mcf = point(p0, y0, s0), point(p1, y1, f1), point(p0, y0, s0, w)
    comp = {m: mcf[m] - m0[m] for m in METRICS}
    cond = {m: m1[m] - mcf[m] for m in METRICS}
    return {"model": name, "year": year, "label": label_key, "auc_2014_vs_year": auc,
            "m2014": m0, "m_year": m1, "counterfactual": mcf, "composition": comp, "conditional": cond,
            "dp_check": {g: {"conditional": cond[f"dp_{g}"], "passes": abs(cond[f"dp_{g}"]) <= CHECK_TOL}
                         for g in ("race", "sex")}}


# ---------------- 8.5 theory predictions ----------------

def p3_prior_shift(m0, m1, g):
    """DP change predicted by group-conditional prior shift alone (Asiaee and Aryan), with 2014 TPR/FPR."""
    pred = sum(sign * (m0[f"tpr_{g}{k}"] - m0[f"fpr_{g}{k}"]) * (m1[f"base_rate_{g}{k}"] - m0[f"base_rate_{g}{k}"])
               for sign, k in ((1, "1"), (-1, "2")))
    obs = m1[f"dp_{g}"] - m0[f"dp_{g}"]
    return {"observed_dp_change": obs, "predicted_by_prior_shift": pred,
            "share_explained": pred / obs if obs else None,
            "abs_eo_change": abs(m1[f"eo_{g}"] - m0[f"eo_{g}"]), "abs_dp_change": abs(obs)}


def domain_auc(Xa, Xb, seed=0):
    return dfl_weights(Xa, Xb, seed)[1]


def p1_auc(frames, states, year):
    f0, f1 = frames[2014], frames[year]
    st0, st1 = f0["ST"].to_numpy(), f1["ST"].to_numpy()
    X0, X1 = design(f0, "harmonised"), design(f1, "harmonised")
    res = {}
    for s in states:
        temporal = domain_auc(X0[st0 == s], X1[st1 == s])
        geo = [domain_auc(X0[st0 == s], X0[st0 == t]) for t in states if t != s]
        res[str(s)] = {"temporal_auc": temporal, "geographic_auc_median": float(np.median(geo))}
    k = sum(v["temporal_auc"] < v["geographic_auc_median"] for v in res.values())
    return {"by_state": res, "states_with_smaller_temporal_shift": k, "n_states": len(states)}


# ---------------- main ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-p1", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    margins = json.loads((STAGE_A / "margins.json").read_text())
    frames = {y: frame(y) for y in YEARS}
    thr = thresholds(frames)
    res = {"thresholds": thr}

    # 8.2 other interventions
    band = {}
    for name in ("expgrad_dp_race_s0", "lfr_race_s0"):
        vals = []
        for y in (2014, 2015, 2016, 2017, 2018):
            f = frames[y]; r = rows_for(y, 0, f)
            vals.append(point(load_pred(name, y, len(f))[r], labels_for(f[r], y, thr)["nominal"],
                              f[r].reset_index(drop=True))["dp_race"])
        eps = max(max(abs(v) for v in vals), margins["floor"])
        f = frames[Y_RACE]
        u = unweighted(load_pred(name, Y_RACE, len(f)), labels_for(f, Y_RACE, thr)["nominal"], f)
        e = Estimate.from_unweighted(u)
        # LFR does not remove DP; its band is [-eps, eps] around 0 as for the other models, per section 8.2
        band[name] = three_way(e.values["dp_race"], e.se("dp_race"), eps, ALPHA) | {"dp_2014_2018": vals}
    res["8.2_other_interventions"] = band

    # 8.3 label definitions: accuracy and EO of every seed-0 model, every year
    rows = []
    for y in YEARS:
        f = frames[y]
        for name in ("gbm_s0", "post_dp_race_s0", "post_eo_race_s0", "post_dp_sex_s0", "post_eo_sex_s0",
                     "expgrad_dp_race_s0", "lfr_race_s0"):
            r = rows_for(y, 0, f); sub = f[r].reset_index(drop=True); pred = load_pred(name, y, len(f))[r]
            for lk, yy in labels_for(sub, y, thr).items():
                e = Estimate.from_unweighted(unweighted(pred, yy, sub))
                for m in METRICS:
                    rows.append(dict(model=name, year=y, label=lk, metric=m, value=e.values[m], se=e.se(m)))
    pd.DataFrame(rows).to_csv(OUT / "secondary_labels.csv", index=False)

    # 8.4 decomposition and 8.5 P2/P3
    dec = []
    for name, year in (("gbm_s0", Y_RACE), ("gbm_s0", Y_SEX)):
        for lk in ("nominal", "inflation", "base_rate"):
            d = decompose(name, 0, year, frames, thr, lk)
            d["P2_conditional_larger"] = {m: abs(d["conditional"][m]) > abs(d["composition"][m])
                                          for m in ("accuracy", "eo_race", "eo_sex")}
            d["P3"] = {g: p3_prior_shift(d["m2014"], d["m_year"], g) for g in ("race", "sex")}
            dec.append(d)
    res["8.4_decomposition"] = dec

    # 8.6 original-pipeline view (per-year standardisation), seed-0 GBM
    fz = joblib.load(MODELS / "gbm_s0.joblib")
    view = {}
    for y in YEARS:
        f = frames[y]; r = rows_for(y, 0, f)
        X = design(f, "harmonised")
        per_year = Scaler(X)
        Xs = per_year(X)                                    # year-specific standardisation
        pred = fz.model.predict(Xs[r]).astype(bool)
        view[y] = point(pred, labels_for(f[r], y, thr)["nominal"], f[r].reset_index(drop=True))
    res["8.6_per_year_scaling"] = view

    if not a.skip_p1:
        res["8.5_P1"] = p1_auc(frames, margins["states"], Y_RACE)
    (OUT / "secondary.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps({"thresholds": thr["inflation"], "base_rate_thr": thr["base_rate"],
                      "8.2": {k: v["decision"] for k, v in band.items()},
                      "dp_checks": [(d["model"], d["year"], d["label"], d["dp_check"]) for d in dec]},
                     indent=1, default=float))


if __name__ == "__main__":
    main()
