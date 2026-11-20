"""Estimands, standard errors and decision rules (pre-registration sections 5-7).

Every metric is a smooth function of group means, so its sampling variance is computed from influence values:
for an unweighted estimate theta with influence values phi_i, Var = sum(phi_i^2). Weighted estimates use the
person weight PWGTP and the 80 replicate weights (Census successive-difference replication):
Var = 4/80 * sum_r (theta_r - theta)^2, with covariances computed the same way.
Unweighted variances are clustered by household (influence values summed within household before squaring);
they are model-based (households treated as independent draws), not a reconstruction of the full ACS design.
Estimates for different survey years come from independent samples, so variances of differences add.
All intervals are large-sample normal approximations, conditional on the frozen models. The margins (delta,
epsilon) and yardsticks (G) are numbers set from the 2014-2018 estimates and frozen before any later year is
opened; the error rates of the decisions, with the constants set this way, are operating characteristics averaged
over the historical sampling (scripts/validate_inference.py, joint simulation), not guarantees conditional on the
realised constants.

Predictions may be hard (0/1) or expected (the probability that a randomised predictor outputs 1). Every metric
is linear in the prediction, so the same formulas give the expected metric of a randomised policy (prereg 4.4).

Failure policy (pre-registration 7.5) is metric-local: a metric whose group or denominator is empty is NaN (its
variance row and column too), with the reason in Estimate.invalid; other metrics of the same estimate are
unaffected, and unweighted and weighted estimates fail independently. A decision on a non-finite input raises
NotComputable, which the runners record as "not computable" for that claim only.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from common import BLACK, WHITE

MALE, FEMALE = 1, 2
METRICS = ("accuracy", "dp_race", "eo_race", "dp_sex", "eo_sex")
REP = [f"PWGTP{i}" for i in range(1, 81)]
G_FLOOR = 0.005          # pre-specified lower bound for the geographic yardsticks used in C7
SPLIT_FILE = Path(__file__).resolve().parents[1] / "results" / "validation" / "split_variance.json"


class NotComputable(ValueError):
    pass


def _masks(df: pd.DataFrame, y: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    race, sex = df["RAC1P"].to_numpy(), df["SEX"].to_numpy()
    w, b, m, f = race == WHITE, race == BLACK, sex == MALE, sex == FEMALE
    return {"dp_race": (w, b), "eo_race": (w & y, b & y), "dp_sex": (m, f), "eo_sex": (m & y, f & y)}


def _prepare(pred, y):
    pred, y = np.asarray(pred, float), np.asarray(y, bool)
    if len(pred) != len(y) or len(y) == 0:
        raise NotComputable("empty or misaligned prediction/label vectors")
    if not np.all(np.isfinite(pred)) or pred.min() < 0 or pred.max() > 1:
        raise NotComputable("predictions must be finite and in [0, 1]")
    return pred, y


def _correct(pred, y):
    """Expected correctness: P(prediction equals label) (equals (pred == y) for hard predictions)."""
    return np.where(y, pred, 1.0 - pred)


def unweighted(pred: np.ndarray, y: np.ndarray, df: pd.DataFrame) -> dict:
    """Point estimates and influence values (unweighted): {metric: (theta, phi)}; theta NaN if not computable,
    with the reason under the key "_invalid"."""
    pred, y = _prepare(pred, y)
    n = len(y)
    out, invalid = {}, {}
    correct = _correct(pred, y)
    acc = correct.mean()
    out["accuracy"] = (acc, (correct - acc) / n)
    for name, (g1, g2) in _masks(df, y).items():
        n1, n2 = g1.sum(), g2.sum()
        if n1 == 0 or n2 == 0:
            out[name] = (np.nan, np.zeros(n))
            invalid[name] = "empty group"
            continue
        p1, p2 = pred[g1].mean(), pred[g2].mean()
        phi = np.zeros(n)
        phi[g1] = (pred[g1] - p1) / n1
        phi[g2] = -(pred[g2] - p2) / n2
        out[name] = (p1 - p2, phi)
    out["_invalid"] = invalid
    return out


def point(pred: np.ndarray, y: np.ndarray, df: pd.DataFrame, w: np.ndarray | None = None) -> dict:
    """Point estimates of all metrics with arbitrary non-negative row weights (None = unweighted); NaN where a
    group is empty. Used for reweighted (counterfactual) estimates in the decomposition."""
    pred, y = _prepare(pred, y)
    w = np.ones(len(y)) if w is None else np.asarray(w, float)

    def avg(v, m):
        s = w[m].sum()
        return float(np.dot(v[m], w[m]) / s) if s > 0 else float("nan")

    allr = np.ones(len(y), bool)
    out = {"accuracy": avg(_correct(pred, y), allr)}
    masks = _masks(df, y)
    for name, (g1, g2) in masks.items():
        out[name] = avg(pred, g1) - avg(pred, g2)
    for g, (m1, m2) in {"race": masks["dp_race"], "sex": masks["dp_sex"]}.items():
        for tag, m in (("1", m1), ("2", m2)):
            out[f"base_rate_{g}{tag}"] = avg(y.astype(float), m)
            out[f"tpr_{g}{tag}"] = avg(pred, m & y)
            out[f"fpr_{g}{tag}"] = avg(pred, m & ~y)
    return out


def weighted(pred: np.ndarray, y: np.ndarray, df: pd.DataFrame) -> dict:
    """Weighted point estimates and their 80 replicate estimates, as {metric: (theta, theta_r[80])}; NaN for a
    metric whose denominator is zero under the full or any replicate weight. Ratios computed as w @ A / w @ G."""
    pred, y = _prepare(pred, y)
    cols_num, cols_den, layout = [], [], []
    correct = _correct(pred, y)
    cols_num.append(correct); cols_den.append(np.ones_like(correct)); layout.append(("accuracy", None))
    for name, (g1, g2) in _masks(df, y).items():
        for sign, g in ((1, g1), (-1, g2)):
            cols_num.append(pred * g); cols_den.append(g.astype(float)); layout.append((name, sign))
    A, G = np.column_stack(cols_num), np.column_stack(cols_den)
    cols = ["PWGTP"] + REP
    num, den = np.empty((len(cols), A.shape[1])), np.empty((len(cols), A.shape[1]))
    for j, c in enumerate(cols):                         # one weight vector at a time (memory)
        w = df[c].to_numpy(float)
        num[j], den[j] = w @ A, w @ G
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(den > 0, num / np.where(den > 0, den, 1.0), np.nan)
    vals = {}
    for j, (name, sign) in enumerate(layout):
        col = r[:, j] * (1 if sign is None else sign)
        vals[name] = col if name not in vals else vals[name] + col
    out = {}
    for m in METRICS:
        v = vals[m]
        out[m] = (float(v[0]), v[1:]) if np.all(np.isfinite(v)) else (float("nan"), np.full(80, np.nan))
    return out


class Estimate:
    """A vector of metric estimates for one (model, year, label, weighting) with its covariance matrix.
    Metrics that are not computable are NaN, with NaN variance row and column; `invalid` gives the reasons."""

    def __init__(self, values: dict, cov: np.ndarray, n: int, invalid: dict | None = None):
        self.values, self.cov, self.n = dict(values), np.asarray(cov, float), n
        self.invalid = dict(invalid or {})
        for m in METRICS:
            if not np.isfinite(self.values[m]):
                self.invalid.setdefault(m, "not computable")
        bad = [METRICS.index(m) for m in self.invalid]
        if bad:
            self.values.update({m: float("nan") for m in self.invalid})
            self.cov[bad, :] = np.nan
            self.cov[:, bad] = np.nan

    @classmethod
    def from_unweighted(cls, u: dict, cluster=None):
        """Covariance from influence values. With `cluster` (household ids), influence values are summed within
        clusters first, so that correlation between members of the same household is accounted for."""
        names = list(METRICS)
        Phi = np.vstack([u[m][1] for m in names])
        n = Phi.shape[1]
        if cluster is not None:
            codes, uniq = pd.factorize(np.asarray(cluster))
            Phi = np.vstack([np.bincount(codes, weights=row, minlength=len(uniq)) for row in Phi])
        return cls({m: float(u[m][0]) for m in names}, Phi @ Phi.T, n, u.get("_invalid"))

    @classmethod
    def from_weighted(cls, wt: dict, n: int):
        names = list(METRICS)
        D = np.vstack([np.nan_to_num(wt[m][1] - wt[m][0]) for m in names])
        return cls({m: float(wt[m][0]) for m in names}, 4.0 / 80.0 * D @ D.T, n)

    def se(self, m: str) -> float:
        return float(np.sqrt(self.cov[METRICS.index(m), METRICS.index(m)]))


def split_multiplier(weighting: str, path: Path | None = None) -> np.ndarray:
    """Pre-specified variance multipliers for estimates on a 20% test split (pre-registration 7.1), one per metric,
    from results/validation/split_variance.json (scripts/check_split_variance.py)."""
    d = json.loads(Path(path or SPLIT_FILE).read_text())["multipliers"][weighting]
    return np.array([d[m] for m in METRICS])


def inflate(e: Estimate, mult: np.ndarray) -> Estimate:
    """Covariance scaled by sqrt(m_i m_j): each variance multiplied by m_i (correlations unchanged)."""
    r = np.sqrt(np.asarray(mult, float))
    return Estimate(dict(e.values), e.cov * np.outer(r, r), e.n, e.invalid)


def household_ids(df: pd.DataFrame) -> np.ndarray:
    """Household identifier for clustering: state code and SERIALNO (Puerto Rico has its own file)."""
    return (df["ST"].astype(int).astype(str) + "_" + df["SERIALNO"].astype(str)).to_numpy()


def estimates(pred, y, df: pd.DataFrame, split: bool = False, apply_split_multiplier: bool = True,
              with_weighted: bool = True):
    """(unweighted, weighted) Estimates of one model on one evaluation set. The one place where estimates are built.
    split=True marks an evaluation on a 20% training-year test split: its variances get the pre-specified
    multipliers (pre-registration 7.1) unless apply_split_multiplier is False (smoke tests only).
    with_weighted=False returns (unweighted, None) for frames without replicate weights."""
    df = df.reset_index(drop=True)
    eu = Estimate.from_unweighted(unweighted(pred, y, df), household_ids(df))
    ew = Estimate.from_weighted(weighted(pred, y, df), len(df)) if with_weighted else None
    if split and apply_split_multiplier:
        eu = inflate(eu, split_multiplier("unweighted"))
        ew = inflate(ew, split_multiplier("weighted")) if ew is not None else None
    return eu, ew


def change(later: Estimate, base: Estimate) -> tuple[dict, np.ndarray]:
    """Differences later - base for every metric; independent samples, so covariances add."""
    return {m: later.values[m] - base.values[m] for m in METRICS}, later.cov + base.cov


def noise_corrected_abs(delta: float, se: float) -> float:
    """|delta| corrected for sampling noise: sqrt(max(delta^2 - se^2, 0)); NaN if an input is NaN. Descriptive."""
    if not (np.isfinite(delta) and np.isfinite(se)):
        return float("nan")
    return float(np.sqrt(max(delta ** 2 - se ** 2, 0.0)))


def three_way(est: float, se: float, margin: float, alpha: float) -> dict:
    """Pre-registered decision for 'within +/- margin': two-sided (1 - alpha) normal interval.
    holds: interval inside [-margin, margin]; violated: interval entirely outside it; else inconclusive.
    Error control (large-sample): if |theta| >= margin, P(holds) <= alpha/2; if |theta| <= margin,
    P(violated) <= alpha (either tail can produce a false "violated")."""
    if not (np.isfinite(est) and np.isfinite(se) and se >= 0 and np.isfinite(margin) and margin > 0):
        raise NotComputable("three_way: non-finite estimate, SE or margin")
    z = stats.norm.ppf(1 - alpha / 2)
    lo, hi = est - z * se, est + z * se
    if -margin <= lo and hi <= margin:
        decision = "holds"
    elif lo > margin or hi < -margin:
        decision = "violated"
    else:
        decision = "inconclusive"
    return {"estimate": est, "se": se, "ci": [lo, hi], "margin": margin, "alpha": alpha, "decision": decision}


def _abs_range(lo: float, hi: float) -> tuple[float, float]:
    """Range of |x| for x in [lo, hi]."""
    if lo <= 0 <= hi:
        return 0.0, max(-lo, hi)
    return min(abs(lo), abs(hi)), max(abs(lo), abs(hi))


def compare_stability(d_fair: float, d_acc: float, cov2: np.ndarray, g_fair: float, g_acc: float,
                      alpha: float) -> dict:
    """C7: D = |Delta_fair|/G_fair - |Delta_acc|/G_acc, with G fixed calibration constants (floored at G_FLOOR).
    Conservative projection interval: a simultaneous (1 - alpha) Bonferroni box for (Delta_fair, Delta_acc)
    (each side a two-sided 1 - alpha/2 normal interval, valid for any correlation), and the exact range of D
    over that box. If the box covers the true changes, the interval covers the true D, so the probability of a
    wrong directional decision is at most alpha (given valid marginal intervals). D < 0: the fairness metric
    changed less, relative to its yardstick."""
    cov2 = np.asarray(cov2, float)
    if not (np.all(np.isfinite([d_fair, d_acc, g_fair, g_acc])) and np.all(np.isfinite(cov2))
            and g_fair >= 0 and g_acc >= 0 and cov2[0, 0] >= 0 and cov2[1, 1] >= 0):
        raise NotComputable("compare_stability: non-finite or negative input")
    g_fair, g_acc = max(g_fair, G_FLOOR), max(g_acc, G_FLOOR)
    z = stats.norm.ppf(1 - alpha / 4)
    s_f, s_a = np.sqrt(cov2[0, 0]), np.sqrt(cov2[1, 1])
    f_lo, f_hi = _abs_range(d_fair - z * s_f, d_fair + z * s_f)
    a_lo, a_hi = _abs_range(d_acc - z * s_a, d_acc + z * s_a)
    lo, hi = f_lo / g_fair - a_hi / g_acc, f_hi / g_fair - a_lo / g_acc
    pt = abs(d_fair) / g_fair - abs(d_acc) / g_acc
    decision = "fairness more stable" if hi < 0 else ("accuracy more stable" if lo > 0 else "inconclusive")
    return {"D": float(pt), "ci": [float(lo), float(hi)], "alpha": alpha, "decision": decision,
            "delta_fair": float(d_fair), "delta_acc": float(d_acc), "se_fair": float(s_f), "se_acc": float(s_a),
            "G_fair": float(g_fair), "G_acc": float(g_acc), "method": "bonferroni-box projection"}


def sign_count(temporal: list[float], geographic: list[float]) -> dict:
    """Descriptive (not confirmatory; QA 1, #1): number of states whose noise-corrected temporal change is
    smaller than, equal to, or larger than their geographic reference; non-finite comparisons counted apart."""
    t, g = np.asarray(temporal, float), np.asarray(geographic, float)
    ok = np.isfinite(t) & np.isfinite(g)
    return {"n": int(len(t)), "n_computable": int(ok.sum()), "smaller": int((t[ok] < g[ok]).sum()),
            "ties": int((t[ok] == g[ok]).sum()), "larger": int((t[ok] > g[ok]).sum()), "status": "descriptive"}
