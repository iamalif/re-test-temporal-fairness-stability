"""Shared helpers: splits, features, metrics and confidence intervals as in Ding et al. (2021, App. C)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
RESULTS = ROOT / "results"

FEATURES = ["AGEP", "COW", "SCHL", "MAR", "OCCP", "POBP", "RELP", "WKHP", "SEX", "RAC1P"]
WHITE, BLACK = 1, 2
THRESHOLD = 50_000


def load_year(year: int, columns: list[str] | None = None) -> pd.DataFrame:
    from data import check_year_allowed  # same guard as the loader
    check_year_allowed(year)
    return pd.read_parquet(DERIVED / f"acsincome_{year}.parquet", columns=columns)


def label(df: pd.DataFrame, threshold: float = THRESHOLD, rule: str = ">") -> np.ndarray:
    if rule == ">":
        return (df["PINCP"] > threshold).to_numpy()
    if rule == ">=":
        return (df["PINCP"] >= threshold).to_numpy()
    raise ValueError(rule)


def folktables_matrix(df: pd.DataFrame, features: list[str] = FEATURES) -> np.ndarray:
    """Features as folktables builds them: raw codes, column-stacked, NaN -> 0.

    folktables calls np.nan_to_num(x, -1); the second positional argument of nan_to_num is `copy`,
    so missing values become 0, not -1 (folktables issue #39). We reproduce that behaviour.
    """
    return np.nan_to_num(df[features].to_numpy(dtype=float), copy=True, nan=0.0)


def state_split(df: pd.DataFrame, seed: int, test_frac: float = 0.2) -> np.ndarray:
    """Boolean test mask: an independent 80/20 random split within each state (App. C)."""
    rng = np.random.default_rng(seed)
    is_test = np.zeros(len(df), dtype=bool)
    for _, idx in df.groupby("ST").indices.items():
        idx = np.asarray(idx)
        n_test = int(round(test_frac * len(idx)))
        chosen = rng.choice(idx, size=n_test, replace=False)
        is_test[chosen] = True
    return is_test


# ---------- metrics ----------

def rate(pred: np.ndarray, mask: np.ndarray, w: np.ndarray | None = None) -> float:
    if w is None:
        return float(pred[mask].mean())
    return float(np.average(pred[mask], weights=w[mask]))


def dp_gap(pred, race, w=None) -> float:
    """P(Yhat=1 | White) - P(Yhat=1 | Black)."""
    return rate(pred, race == WHITE, w) - rate(pred, race == BLACK, w)


def eo_gap(pred, y, race, w=None) -> float:
    """P(Yhat=1 | White, Y=1) - P(Yhat=1 | Black, Y=1)."""
    return rate(pred, (race == WHITE) & y, w) - rate(pred, (race == BLACK) & y, w)


def accuracy(pred, y, w=None) -> float:
    return rate(pred == y, np.ones(len(y), dtype=bool), w)


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    lo = stats.beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = stats.beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return float(lo), float(hi)


def wilson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    z = stats.norm.ppf(1 - alpha / 2)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return float(centre - half), float(centre + half)


def newcombe(k1: int, n1: int, k2: int, n2: int, alpha: float = 0.05) -> tuple[float, float]:
    """Newcombe (1998) hybrid score interval (method 10) for p1 - p2."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, alpha)
    l2, u2 = wilson(k2, n2, alpha)
    d = p1 - p2
    lo = d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return float(lo), float(hi)


def evaluate(pred: np.ndarray, y: np.ndarray, race: np.ndarray) -> dict:
    """Unweighted point estimates and the intervals used in the original paper."""
    pred = pred.astype(bool)
    y = y.astype(bool)
    n = len(y)
    k_acc = int((pred == y).sum())
    w_, b_ = race == WHITE, race == BLACK
    wy, by = w_ & y, b_ & y
    out = {
        "n": n,
        "accuracy": k_acc / n,
        "accuracy_ci": clopper_pearson(k_acc, n),
        "dp": dp_gap(pred, race),
        "dp_ci": newcombe(int(pred[w_].sum()), int(w_.sum()), int(pred[b_].sum()), int(b_.sum())),
        "eo": eo_gap(pred, y, race),
        "eo_ci": newcombe(int(pred[wy].sum()), int(wy.sum()), int(pred[by].sum()), int(by.sum())),
        "pos_rate": float(pred.mean()),
        "base_rate": float(y.mean()),
        "n_white": int(w_.sum()), "n_black": int(b_.sum()),
    }
    return out
