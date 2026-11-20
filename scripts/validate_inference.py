"""Validation of the confirmatory decision procedures (QA 1, #2 and #10). Uses only synthetic draws and the
2014-2018 Stage A estimates (results/stage_a/estimates_2014_2018.json); no later-year data.

Part 1  Operating characteristics of the three-way rule (C1-C6) at the anticipated standard errors:
        P(holds), P(inconclusive), P(violated) as a function of the true deviation, analytic and Monte Carlo.
Part 2  Coverage and error rates of the C7 interval (Bonferroni-box projection) over a grid of true changes,
        including zero changes and the equal-stability boundary D = 0, at the anticipated covariance and under
        stress settings (larger SEs, strong correlation). The earlier Monte Carlo percentile interval is
        evaluated alongside for comparison.

Anticipated SEs: the later-year estimate is computed on a full year (as in 2015-2018), so its SE is approximated by
the model's 2018 full-year SE; the 2014-2018 baseline variance is sum_t Var_t / 25 (as in the confirmatory runner).
Writes results/validation/inference_validation.json and prints summaries.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
from scipy import stats

from analysis import G_FLOOR, METRICS, compare_stability, three_way
from pipeline import provenance

ALPHA = 0.05 / 6          # confirmatory family C1, C2, C3, C4, C6, C7 (C5 secondary: power, C8 descriptive)
ALPHA_SECONDARY = 0.05
ACCEPT = {"three_way_false_holds_max": ALPHA / 2, "three_way_false_violated_max": ALPHA,
          "C7_min_coverage": 1 - ALPHA, "joint_false_holds_max": ALPHA / 2, "joint_false_violated_max": ALPHA}
SEEDS = range(5)
YEARS = (2014, 2015, 2016, 2017, 2018)
OUT = ROOT / "results" / "validation"
EST = json.loads((ROOT / "results" / "stage_a" / "estimates_2014_2018.json").read_text())
MARG = json.loads((ROOT / "results" / "stage_a" / "margins.json").read_text())


def cov(name, year, wt):
    return np.array(EST[f"{name}|{year}|{wt}"]["cov"])


def anticipated(wt):
    """Anticipated SEs of the confirmatory statistics (mean over seeds of per-seed SE, as in the runner)."""
    out = {}
    for c, fam, m in (("C1", "gbm", "dp_race"), ("C2", "gbm", "dp_sex"),
                      ("C5", "gbm", "eo_race"), ("C6", "gbm", "eo_sex")):
        k = METRICS.index(m)
        ses = [np.sqrt(cov(f"{fam}_s{s}", 2018, wt)[k, k] + sum(cov(f"{fam}_s{s}", y, wt)[k, k] for y in YEARS) / 25)
               for s in SEEDS]
        out[c] = float(np.mean(ses))
    for c, fam, m in (("C3", "post_dp_race", "dp_race"), ("C4", "post_dp_sex", "dp_sex")):
        k = METRICS.index(m)
        out[c] = float(np.mean([np.sqrt(cov(f"{fam}_s{s}", 2018, wt)[k, k]) for s in SEEDS]))
    ix = [METRICS.index("dp_race"), METRICS.index("accuracy")]
    c7 = np.mean([(cov(f"gbm_s{s}", 2018, wt) + cov(f"gbm_s{s}", 2014, wt))[np.ix_(ix, ix)] for s in SEEDS], axis=0)
    out["C7_cov"] = c7.tolist()
    return out


def three_way_probs(theta, se, m, alpha):
    z = stats.norm.ppf(1 - alpha / 2)
    p_hold = max(stats.norm.cdf((m - z * se - theta) / se) - stats.norm.cdf((-m + z * se - theta) / se), 0.0) \
        if m > z * se else 0.0
    p_viol = stats.norm.sf((m + z * se - theta) / se) + stats.norm.cdf((-m - z * se - theta) / se)
    return p_hold, max(1 - p_hold - p_viol, 0.0), p_viol


def part1(wt, se_by_claim, rng):
    margins = MARG[wt]
    margin_of = {"C1": margins["delta"]["dp_race"], "C2": margins["delta"]["dp_sex"],
                 "C5": margins["delta"]["eo_race"], "C6": margins["delta"]["eo_sex"],
                 "C3": margins["epsilon"]["race"], "C4": margins["epsilon"]["sex"]}
    res = {}
    runs = [(c, c, ALPHA) for c in ("C1", "C2", "C3", "C4", "C5", "C6")] + [("C5_secondary", "C5", ALPHA_SECONDARY)]
    for key, c, alpha in runs:
        se, m = se_by_claim[c], margin_of[c]
        rows = []
        for r in (0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0):
            theta = r * m
            ph, pi, pv = three_way_probs(theta, se, m, alpha)
            sims = theta + se * rng.standard_normal(20000)
            dec = [three_way(x, se, m, alpha)["decision"] for x in sims[:4000]]
            mc = {d: dec.count(d) / len(dec) for d in ("holds", "inconclusive", "violated")}
            rows.append(dict(theta_over_margin=r, theta=theta, p_holds=ph, p_inconclusive=pi, p_violated=pv,
                             mc_holds=mc["holds"], mc_violated=mc["violated"]))
        z = stats.norm.ppf(1 - alpha / 2)
        res[key] = {"alpha": alpha, "se": se, "margin": m, "min_margin_for_holds_possible": z * se,
                  "max_abs_estimate_for_holds": m - z * se, "rows": rows}
    return res


def old_mc(d_f, d_a, cov2, gf, ga, alpha, rng, draws=4000):
    sims = rng.multivariate_normal([d_f, d_a], cov2, size=draws)
    D = np.abs(sims[:, 0]) / gf - np.abs(sims[:, 1]) / ga
    return np.quantile(D, [alpha / 2, 1 - alpha / 2])


def part2(cov2, gf, ga, rng, reps=20000, old_reps=1000, label=""):
    L = np.linalg.cholesky(cov2)
    grid = []
    sf, sa = np.sqrt(cov2[0, 0]), np.sqrt(cov2[1, 1])
    a_vals = sorted({0.0, sf, 2 * sf, 0.5 * gf, gf, 2 * gf})
    for a in a_vals:
        for b in sorted({0.0, sa, 2 * sa, 0.5 * ga, ga, 2 * ga} | {a * ga / gf}):   # last value: D = 0
            grid.append((a, b))
    rows, worst = [], 0.0
    for a, b in grid:
        true_d = abs(a) / gf - abs(b) / ga
        x = np.array([a, b]) + rng.standard_normal((reps, 2)) @ L.T
        cover, fair, accm = 0, 0, 0
        for xf, xa in x:
            r = compare_stability(xf, xa, cov2, gf, ga, ALPHA)
            lo, hi = r["ci"]
            cover += lo <= true_d <= hi
            fair += r["decision"] == "fairness more stable"
            accm += r["decision"] == "accuracy more stable"
        wrong = (fair if true_d >= 0 else 0) + (accm if true_d <= 0 else 0)
        row = dict(a=a, b=b, true_D=true_d, coverage=cover / reps, p_fair_more_stable=fair / reps,
                   p_acc_more_stable=accm / reps, p_wrong_direction=wrong / reps)
        if old_reps and (a == 0.0 or abs(true_d) < 1e-12):
            oc = 0
            for xf, xa in x[:old_reps]:
                lo, hi = old_mc(xf, xa, cov2, gf, ga, ALPHA, rng)
                oc += lo <= true_d <= hi
            row["old_mc_percentile_coverage"] = oc / old_reps
        worst = max(worst, row["p_wrong_direction"])
        rows.append(row)
    return {"label": label, "cov": cov2.tolist(), "G_fair": gf, "G_acc": ga, "reps": reps,
            "min_coverage": min(r["coverage"] for r in rows), "max_p_wrong_direction": worst,
            "old_mc_min_coverage": min((r["old_mc_percentile_coverage"] for r in rows
                                        if "old_mc_percentile_coverage" in r), default=None),
            "rows": rows}


def violated_edge_case():
    """P(false 'violated') can approach alpha (not alpha/2) when the margin is tiny relative to the SE (QA 2, A8)."""
    out = []
    for m_over_se in (1e-5, 0.5, 1.0, 2.0, 3.0):
        for theta_over_m in (0.0, 1.0):
            se, m = 1.0, m_over_se
            _, _, pv = three_way_probs(theta_over_m * m, se, m, ALPHA)
            out.append({"margin_over_se": m_over_se, "theta_over_margin": theta_over_m, "p_violated": pv,
                        "within_alpha": bool(pv <= ALPHA + 1e-12), "within_alpha_over_2": bool(pv <= ALPHA / 2 + 1e-12)})
    return out


def part3(wt, rng, reps=20000):
    """Joint simulation of the whole procedure for C1, C2, C6 (deviation from the baseline) and C3, C4 (envelope):
    the five historical estimates, the calibration rule (delta or epsilon from those estimates, floor 0.01), the
    baseline estimate and the later-year estimate are all redrawn in every replicate (QA 2, A1). True histories:
    flat, and the observed seed-mean shape of 2014-2018. Errors are judged against the realised calibration
    constant: a false 'holds' is |theta| >= margin with decision 'holds'; a false 'violated' is |theta| <= margin
    with decision 'violated'. Uses the per-year SEs of seed 0 (a stand-in for the seed-mean SE)."""
    m = MARG[wt]
    specs = {"C1": ("gbm_s0", "dp_race", "dev"), "C2": ("gbm_s0", "dp_sex", "dev"), "C6": ("gbm_s0", "eo_sex", "dev"),
             "C3": ("post_dp_race_s0", "dp_race", "env"), "C4": ("post_dp_sex_s0", "dp_sex", "env")}
    z = stats.norm.ppf(1 - ALPHA / 2)
    res = {}
    for c, (name, metric, kind) in specs.items():
        k = METRICS.index(metric)
        s_t = np.array([np.sqrt(cov(name, y, wt)[k, k]) for y in YEARS])
        s_new = float(s_t[-1])                           # later year approximated by 2018 on all rows
        shape = (np.array([m["deviation_from_baseline_by_year"][metric][str(y)] for y in YEARS]) if kind == "dev"
                 else np.array([np.mean(m["post_dp_per_seed_by_year"][metric[3:]][str(y)]) for y in YEARS]))
        rows = []
        for hist_label, mu_hist in (("flat", np.zeros(5)), ("observed shape", shape)):
            B = mu_hist.mean()
            for theta in (0.0, 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.02, 0.03):
                hist = mu_hist + s_t * rng.standard_normal((reps, 5))
                newv = (B if kind == "dev" else 0.0) + theta + s_new * rng.standard_normal(reps)
                if kind == "dev":
                    bhat = hist.mean(1)
                    margin = np.maximum(np.abs(hist - bhat[:, None]).max(1), 0.01)
                    est, se = newv - bhat, np.sqrt(s_new ** 2 + (s_t ** 2).sum() / 25)
                    true = theta                                  # population later value minus population baseline
                else:
                    margin = np.maximum(np.abs(hist).max(1), 0.01)
                    est, se, true = newv, s_new, theta
                lo, hi = est - z * se, est + z * se
                holds = (lo >= -margin) & (hi <= margin)
                viol = (lo > margin) | (hi < -margin)
                fh = float(np.mean(holds & (abs(true) >= margin)))
                fv = float(np.mean(viol & (abs(true) <= margin)))
                rows.append({"history": hist_label, "theta": theta, "p_holds": float(holds.mean()),
                             "p_violated": float(viol.mean()), "p_false_holds": fh, "p_false_violated": fv,
                             "mean_margin": float(margin.mean())})
        res[c] = {"rows": rows, "max_p_false_holds": max(r["p_false_holds"] for r in rows),
                  "max_p_false_violated": max(r["p_false_violated"] for r in rows), "reps": reps}
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261119)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    path = OUT / "inference_validation.json"
    res = json.loads(path.read_text()) if path.exists() else {}
    res["alpha_per_test"] = ALPHA
    res["acceptance"] = ACCEPT
    res["violated_edge_case"] = violated_edge_case()
    for wt in ("unweighted", "weighted"):
        se = anticipated(wt)
        res.setdefault(wt, {})["anticipated_se"] = se
        if which in ("all", "part1"):
            res[wt]["three_way"] = part1(wt, se, rng)
            for c, v in res[wt]["three_way"].items():
                r0 = v["rows"][0]
                print(f"[{wt}] {c}: se={v['se']:.4f} margin={v['margin']:.4f}  at theta=0: P(holds)={r0['p_holds']:.3f}"
                      f"  P(inconcl)={r0['p_inconclusive']:.3f};  holds needs |est| <= {v['max_abs_estimate_for_holds']:.4f}")
        if which in ("all", "part2"):
            c2 = np.array(se["C7_cov"])
            gf, ga = max(MARG[wt]["G"]["dp_race"], G_FLOOR), max(MARG[wt]["G"]["accuracy"], G_FLOOR)
            settings = [("anticipated", c2)]
            if wt == "unweighted":
                s = np.sqrt(np.diag(c2))
                settings += [("SE x3, rho=+0.9", np.outer(3 * s, 3 * s) * np.array([[1, .9], [.9, 1]])),
                             ("SE x3, rho=-0.9", np.outer(3 * s, 3 * s) * np.array([[1, -.9], [-.9, 1]]))]
            res[wt]["C7"] = []
            for lab, cv in settings:
                r = part2(cv, gf, ga, rng, reps=4000 if lab != "anticipated" else 8000,
                          old_reps=400 if lab == "anticipated" else 0, label=lab)
                res[wt]["C7"].append(r)
                print(f"[{wt}] C7 {lab}: min coverage {r['min_coverage']:.4f} (target >= {1 - ALPHA:.4f}); "
                      f"max P(wrong direction) {r['max_p_wrong_direction']:.4f} (<= {ALPHA:.4f}); "
                      f"old MC percentile min coverage {r['old_mc_min_coverage']}")
        if which in ("all", "part3"):
            res[wt]["joint"] = part3(wt, rng)
            for c, v in res[wt]["joint"].items():
                print(f"[{wt}] joint {c}: max P(false holds) {v['max_p_false_holds']:.4f} (<= {ALPHA / 2:.4f}); "
                      f"max P(false violated) {v['max_p_false_violated']:.4f} (<= {ALPHA:.4f})")
    # acceptance summary (checked by check_outputs.py)
    ok = {}
    for wt in ("unweighted", "weighted"):
        r = res.get(wt, {})
        tw = r.get("three_way", {})
        ok[f"{wt}|three_way"] = all(
            row["p_holds"] <= ACCEPT["three_way_false_holds_max"] + 1e-9
            for c, v in tw.items() if not c.endswith("secondary") for row in v["rows"] if row["theta_over_margin"] >= 1)
        ok[f"{wt}|C7"] = all(x["min_coverage"] >= ACCEPT["C7_min_coverage"] for x in r.get("C7", []))
        jt = r.get("joint", {})
        tol = lambda b, n: b + 3 * np.sqrt(b * (1 - b) / n)       # Monte Carlo tolerance (3 standard errors)
        ok[f"{wt}|joint"] = bool(jt) and all(
            v["max_p_false_holds"] <= tol(ACCEPT["joint_false_holds_max"], v["reps"])
            and v["max_p_false_violated"] <= tol(ACCEPT["joint_false_violated_max"], v["reps"]) for v in jt.values())
    res["acceptance_passed"] = ok
    res["provenance"] = provenance()
    print("acceptance:", ok)
    path.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))


if __name__ == "__main__":
    main()
