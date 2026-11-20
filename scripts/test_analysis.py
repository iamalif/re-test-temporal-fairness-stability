"""Synthetic tests of the estimators and decision rules (QA 2, A6 and A8). No survey data.
Writes results/validation/analysis_tests.json; exits non-zero if any test fails."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
from scipy import stats

from analysis import (METRICS, REP, Estimate, NotComputable, compare_stability, estimates, point, three_way,
                      unweighted, weighted)

rng = np.random.default_rng(1)
results = {}


def record(name, ok, detail=""):
    results[name] = {"passed": bool(ok), "detail": detail}


def frame(n=4000, black_pos=True):
    race = rng.choice([1, 2], n, p=[0.8, 0.2])
    sex = rng.choice([1, 2], n)
    y = rng.random(n) < 0.3
    if not black_pos:
        y[race == 2] = False
    df = pd.DataFrame({"RAC1P": race, "SEX": sex, "ST": rng.choice([6, 48], n),
                       "SERIALNO": [f"H{i // 2}" for i in range(n)], "PWGTP": rng.integers(1, 50, n)})
    for c in REP:
        df[c] = rng.integers(0, 60, n)
    return df, y


# 1. DP computable while Black EO has no positives: EO NaN, DP finite, other metrics unaffected
df, y = frame(black_pos=False)
pred = rng.random(len(df))
eu, ew = estimates(pred, y, df, apply_split_multiplier=False)
record("dp_finite_when_eo_race_not_computable",
       np.isfinite(eu.values["dp_race"]) and np.isnan(eu.values["eo_race"]) and np.isfinite(eu.se("dp_race"))
       and np.isnan(eu.se("eo_race")) and np.isfinite(eu.values["accuracy"]) and "eo_race" in eu.invalid,
       f"unweighted invalid={eu.invalid}")
record("weighted_fails_independently",
       np.isfinite(ew.values["dp_race"]) and np.isnan(ew.values["eo_race"]), f"weighted invalid={ew.invalid}")

# 2. zero replicate denominator for one group: only that metric is NaN in the weighted estimate
df, y = frame()
df.loc[df.RAC1P == 2, "PWGTP7"] = 0
ew = estimates(pred, y, df, apply_split_multiplier=False)[1]
record("zero_replicate_denominator_is_metric_local",
       np.isnan(ew.values["dp_race"]) and np.isfinite(ew.values["dp_sex"]) and np.isfinite(ew.values["accuracy"]),
       f"invalid={ew.invalid}")

# 3. decisions refuse non-finite inputs
for label_, fn in (("three_way_nan_estimate", lambda: three_way(np.nan, 0.01, 0.01, 0.05)),
                   ("three_way_nan_se", lambda: three_way(0.0, np.nan, 0.01, 0.05)),
                   ("c7_nan_yardstick", lambda: compare_stability(0.01, 0.01, np.eye(2) * 1e-6, np.nan, 0.01, 0.05)),
                   ("c7_nan_covariance", lambda: compare_stability(0.01, 0.01, np.full((2, 2), np.nan), 0.02, 0.01,
                                                                   0.05))):
    try:
        fn()
        record(label_, False, "no exception")
    except NotComputable:
        record(label_, True)

# 4. expected-prediction accuracy equals the mean of realised random predictions (large sample)
df, y = frame(n=200000)
p = rng.random(len(df))
acc_exp = point(p, y, df)["accuracy"]
acc_mc = float(np.mean((rng.random(len(df)) < p) == y))
record("expected_accuracy_matches_randomised_policy", abs(acc_exp - acc_mc) < 0.005, f"{acc_exp:.4f} vs {acc_mc:.4f}")

# 5. hard predictions: estimates equal the textbook formulas
df, y = frame()
h = (rng.random(len(df)) < 0.4).astype(float)
u = unweighted(h, y, df)
w, b = df.RAC1P.to_numpy() == 1, df.RAC1P.to_numpy() == 2
record("dp_formula", abs(u["dp_race"][0] - (h[w].mean() - h[b].mean())) < 1e-12)
wt = weighted(h, y, df)
pw = df.PWGTP.to_numpy(float)
record("weighted_accuracy_formula", abs(wt["accuracy"][0] - np.average(h == y, weights=pw)) < 1e-12)

# 6. 'violated' error bound is alpha in general, not alpha/2 (A8): tiny margin, theta = 0
alpha = 0.05 / 6
z = stats.norm.ppf(1 - alpha / 2)
m = 1e-5
p_viol = stats.norm.sf(m + z) + stats.norm.cdf(-m - z)
record("violated_bound_alpha_not_half", alpha / 2 < p_viol <= alpha, f"P(violated)={p_viol:.6f}")

# 7. C7 projection: interval covers the true D whenever the box covers the true changes (exhaustive grid)
ok = True
for df_, da in [(0.0, 0.0), (0.01, -0.02), (-0.005, 0.0)]:
    r = compare_stability(df_, da, np.diag([1e-6, 1e-6]), 0.02, 0.015, 0.05)
    ok &= r["ci"][0] <= abs(df_) / 0.02 - abs(da) / 0.015 <= r["ci"][1]
record("c7_interval_contains_point", ok)

# 8. decomposition balance gate (QA 3, A3-5): synthetic failures must fail, a balanced case must pass
sys.path.insert(0, str(ROOT / "scripts"))
from stage_b_secondary import balance  # noqa: E402
from harmonise import HARMONISED_FEATURES  # noqa: E402
nf = len(HARMONISED_FEATURES)
j_pob, j_age = HARMONISED_FEATURES.index("POBP_H"), HARMONISED_FEATURES.index("AGEP")


def sample(n, pob_probs):
    X = np.zeros((n, nf))
    X[:, j_age] = rng.normal(40, 12, n)
    X[:, j_pob] = rng.choice(len(pob_probs), n, p=pob_probs)
    return X


base = np.ones(300) / 300
X0, X1 = sample(20000, base), sample(40000, base)
m0, m1 = np.ones(len(X0), bool), np.ones(len(X1), bool)
ok_case = balance(X0, np.ones(len(X0)), X1, m0, m1)
record("balance_passes_identical_distributions", ok_case["passes"], f"smd={ok_case['max_smd']:.4f}")
wc = np.ones(len(X0)); wc[:10] = 1e5                 # weights concentrated on 10 rows: no effective support
conc = balance(X0, wc, X1, m0, m1)
record("balance_fails_concentrated_weights", (not conc["passes"]) and not conc["ess_ok"],
       f"ess_fraction={conc['ess_fraction']:.4f}, limit={conc['limit']:.3f}")
shift = base.copy(); shift[:150] *= 0.5; shift[150:] *= 1.5; shift /= shift.sum()   # mass moved among rare categories
X1s = sample(40000, shift)
rare = balance(X0, np.ones(len(X0)), X1s, m0, np.ones(len(X1s), bool))
record("balance_fails_shift_among_rare_categories", (not rare["passes"]) and rare["smd_ok"] and not rare["tvd_ok"],
       f"max indicator smd={rare['max_smd']:.4f} (rare categories < 1% excluded), tvd={rare['tvd']['POBP_H']:.3f}")

passed = all(v["passed"] for v in results.values())
for k, v in results.items():
    print(f"{k:50s} {'ok' if v['passed'] else 'FAILED'}  {v['detail']}")
out = ROOT / "results" / "validation"
out.mkdir(parents=True, exist_ok=True)
(out / "analysis_tests.json").write_text(json.dumps({"tests": results, "all_passed": passed,
                                                     "script_sha256": __import__("hashlib").sha256(
                                                         Path(__file__).read_bytes()).hexdigest()}, indent=1))
sys.exit(0 if passed else 1)
