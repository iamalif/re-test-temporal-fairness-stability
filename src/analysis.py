"""Estimands, standard errors and decision rules (pre-registration sections 5-7).

Every metric is a smooth function of group means, so its sampling variance is computed from influence values:
for an unweighted estimate theta with influence values phi_i, Var = sum(phi_i^2). Weighted estimates use the
person weight PWGTP and the 80 replicate weights (Census successive-difference replication):
Var = 4/80 * sum_r (theta_r - theta)^2, with covariances computed the same way.
Estimates for different survey years come from independent samples, so variances of differences add.
All inference is conditional on the fitted (frozen) model.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from common import BLACK, WHITE

MALE, FEMALE = 1, 2
METRICS = ("accuracy", "dp_race", "eo_race", "dp_sex", "eo_sex")
REP = [f"PWGTP{i}" for i in range(1, 81)]


def _masks(df: pd.DataFrame, y: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    race, sex = df["RAC1P"].to_numpy(), df["SEX"].to_numpy()
    w, b, m, f = race == WHITE, race == BLACK, sex == MALE, sex == FEMALE
    return {"dp_race": (w, b), "eo_race": (w & y, b & y), "dp_sex": (m, f), "eo_sex": (m & y, f & y)}


def unweighted(pred: np.ndarray, y: np.ndarray, df: pd.DataFrame) -> dict:
    """Point estimates and influence values (unweighted)."""
    pred, y = pred.astype(float), y.astype(bool)
    n = len(y)
    out = {}
    correct = (pred == y).astype(float)
    acc = correct.mean()
    out["accuracy"] = (acc, (correct - acc) / n)
    for name, (g1, g2) in _masks(df, y).items():
        n1, n2 = g1.sum(), g2.sum()
        p1, p2 = pred[g1].mean(), pred[g2].mean()
        phi = np.zeros(n)
        phi[g1] = (pred[g1] - p1) / n1
        phi[g2] = -(pred[g2] - p2) / n2
        out[name] = (p1 - p2, phi)
    return out


def weighted(pred: np.ndarray, y: np.ndarray, df: pd.DataFrame) -> dict:
    """Weighted point estimates and their 80 replicate estimates, as {metric: (theta, theta_r[80])}.
    Each metric is a ratio of weighted sums (or a difference of two ratios), computed as w @ A / w @ G."""
    pred, y = pred.astype(float), y.astype(bool)
    cols_num, cols_den, layout = [], [], []
    correct = (pred == y).astype(float)
    cols_num.append(correct); cols_den.append(np.ones_like(correct)); layout.append(("accuracy", None))
    for name, (g1, g2) in _masks(df, y).items():
        for sign, g in ((1, g1), (-1, g2)):
            cols_num.append(pred * g); cols_den.append(g.astype(float)); layout.append((name, sign))
    A, G = np.column_stack(cols_num), np.column_stack(cols_den)

    def ratios(w):
        r = (w @ A) / (w @ G)
        out = {"accuracy": r[0]}
        for (name, sign), v in zip(layout[1:], r[1:]):
            out[name] = out.get(name, 0.0) + sign * v
        return out

    base = ratios(df["PWGTP"].to_numpy(float))
    reps = [ratios(df[c].to_numpy(float)) for c in REP]
    return {m: (base[m], np.array([r[m] for r in reps])) for m in METRICS}


class Estimate:
    """A vector of metric estimates for one (model, year, label, weighting) with its covariance matrix."""

    def __init__(self, values: dict, cov: np.ndarray, n: int):
        self.values, self.cov, self.n = values, cov, n

    @classmethod
    def from_unweighted(cls, u: dict):
        names = list(METRICS)
        Phi = np.vstack([u[m][1] for m in names])
        return cls({m: float(u[m][0]) for m in names}, Phi @ Phi.T, Phi.shape[1])

    @classmethod
    def from_weighted(cls, wt: dict, n: int):
        names = list(METRICS)
        D = np.vstack([wt[m][1] - wt[m][0] for m in names])
        return cls({m: float(wt[m][0]) for m in names}, 4.0 / 80.0 * D @ D.T, n)

    def se(self, m: str) -> float:
        return float(np.sqrt(self.cov[METRICS.index(m), METRICS.index(m)]))


def change(later: Estimate, base: Estimate) -> tuple[dict, np.ndarray]:
    """Differences later - base for every metric; independent samples, so covariances add."""
    return {m: later.values[m] - base.values[m] for m in METRICS}, later.cov + base.cov


def noise_corrected_abs(delta: float, se: float) -> float:
    """|delta| corrected for sampling noise: sqrt(max(delta^2 - se^2, 0))."""
    return float(np.sqrt(max(delta ** 2 - se ** 2, 0.0)))


def three_way(est: float, se: float, margin: float, alpha: float) -> dict:
    """Pre-registered decision for 'within +/- margin': two-sided (1 - alpha) normal interval.
    holds: interval inside [-margin, margin]; violated: interval entirely outside it; else inconclusive."""
    z = stats.norm.ppf(1 - alpha / 2)
    lo, hi = est - z * se, est + z * se
    if -margin <= lo and hi <= margin:
        decision = "holds"
    elif lo > margin or hi < -margin:
        decision = "violated"
    else:
        decision = "inconclusive"
    return {"estimate": est, "se": se, "ci": [lo, hi], "margin": margin, "alpha": alpha, "decision": decision}


def compare_stability(d_fair: float, d_acc: float, cov2: np.ndarray, g_fair: float, g_acc: float,
                      alpha: float, draws: int = 200_000, seed: int = 0) -> dict:
    """C7: D = |d_fair|/g_fair - |d_acc|/g_acc. Interval from the normal sampling distribution of
    (d_fair, d_acc) with covariance cov2 (Monte Carlo, fixed seed). D < 0: fairness more stable."""
    rng = np.random.default_rng(seed)
    sims = rng.multivariate_normal([d_fair, d_acc], cov2, size=draws)
    D = np.abs(sims[:, 0]) / g_fair - np.abs(sims[:, 1]) / g_acc
    lo, hi = np.quantile(D, [alpha / 2, 1 - alpha / 2])
    point = abs(d_fair) / g_fair - abs(d_acc) / g_acc
    decision = "fairness more stable" if hi < 0 else ("accuracy more stable" if lo > 0 else "inconclusive")
    return {"D": float(point), "ci": [float(lo), float(hi)], "alpha": alpha, "decision": decision}


def sign_test(indicators: list[bool], alpha: float) -> dict:
    """C8: exact two-sided binomial test of P(temporal change < geographic change) = 1/2 across states."""
    n, k = len(indicators), int(sum(indicators))
    p = float(stats.binomtest(k, n, 0.5, alternative="two-sided").pvalue)
    decision = ("temporal more stable" if (p <= alpha and k > n / 2)
                else "geographic more stable" if (p <= alpha and k < n / 2) else "inconclusive")
    return {"k": k, "n": n, "p_two_sided": p, "alpha": alpha, "decision": decision}
