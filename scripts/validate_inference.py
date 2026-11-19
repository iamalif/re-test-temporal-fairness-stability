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

ALPHA = 0.05 / 6          # confirmatory family C1, C2, C3, C4, C6, C7 (C5 secondary: power, C8 descriptive)
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
    for c in ("C1", "C2", "C3", "C4", "C5", "C6"):
        se, m = se_by_claim[c], margin_of[c]
        rows = []
        for r in (0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0):
            theta = r * m
            ph, pi, pv = three_way_probs(theta, se, m, ALPHA)
            sims = theta + se * rng.standard_normal(20000)
            dec = [three_way(x, se, m, ALPHA)["decision"] for x in sims[:4000]]
            mc = {d: dec.count(d) / len(dec) for d in ("holds", "inconclusive", "violated")}
            rows.append(dict(theta_over_margin=r, theta=theta, p_holds=ph, p_inconclusive=pi, p_violated=pv,
                             mc_holds=mc["holds"], mc_violated=mc["violated"]))
        z = stats.norm.ppf(1 - ALPHA / 2)
        res[c] = {"se": se, "margin": m, "min_margin_for_holds_possible": z * se,
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261119)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    path = OUT / "inference_validation.json"
    res = json.loads(path.read_text()) if path.exists() else {}
    res["alpha_per_test"] = ALPHA
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
    path.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
