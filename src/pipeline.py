"""Confirmatory pipeline: fit every model once on 2014, freeze it, and store its predictions per survey year.

Primary specification (decision log D015; pre-registration section 4):
- features: harmonised ACSIncome features (src/harmonise.py), missing values -> 0 as in folktables;
- preprocessing: one standardisation fitted on the 2014 training split, frozen (trees are invariant to it;
  it matters only for LFR);
- base model: GradientBoostingClassifier(loss="exponential", max_depth=5, n_estimators=100);
- training data: 2014, within-state 80/20 split with the model's seed; the 2014 test split is the 2014 evaluation set;
  every other year is evaluated on all of its rows.

Model families (all trained on 2014 only):
- gbm_s{0..4}: base model, five seeds.
- post_{dp,eo}_{race,sex}_s{0..4}: fairlearn ThresholdOptimizer on gbm_s (group thresholds, objective accuracy),
  race = RAC1P (all categories), sex = SEX; randomised predictions with a fixed seed.
- expgrad_dp_race_s0: fairlearn ExponentiatedGradient(DemographicParity), library defaults, RAC1P.
- lfr_race_s0: AIF360 LFR (k=10, Ax=0.1, Ay=1, Az=2), binary White indicator, base model on the representation.
- rawgbm_s0: base model on the raw (unharmonised) codes, for the recoding-artefact analysis on 2014-2018.
- state{ST}_gbm_s0, state{ST}_post_dp_race_s0: per-state models for the 20 largest states (by 2014 rows),
  trained on that state's 2014 training split.
- y2018_gbm_s{0..4}, y2018_post_dp_{race,sex}_s{0..4}: the same base model and DP post-processing trained on 2018
  instead (secondary analysis 8.9: is the pattern specific to a 2014 deployment?). Evaluated on the 2018 test split
  and on later years.

Fitted models are written to data/derived/models/ (not committed); their SHA-256 hashes go to
results/models_manifest.json (committed and cited in the pre-registration). Predictions are stored bit-packed in
data/derived/preds/<model>/<year>.npy, aligned with the rows of data/derived/acsincome_<year>.parquet.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from common import DERIVED, FEATURES, RESULTS, WHITE, folktables_matrix, label, load_year, state_split
from harmonise import HARMONISED_FEATURES, harmonise

MODELS = DERIVED / "models"
PREDS = DERIVED / "preds"
MANIFEST = RESULTS / "models_manifest.json"
TRAIN_YEAR = 2014
N_TREES = 100
SEEDS = (0, 1, 2, 3, 4)
GROUPS = {"race": "RAC1P", "sex": "SEX"}
N_STATES = 20

SMOKE = os.environ.get("RT_SMOKE_ROWS")   # smoke tests only: small subsample, separate output folders
if SMOKE:
    _tag = os.environ.get("RT_SMOKE_TAG", "0")
    MODELS, PREDS = DERIVED / f"smoke{_tag}_models", DERIVED / f"smoke{_tag}_preds"
    MANIFEST = DERIVED / f"smoke{_tag}_models_manifest.json"
    N_TREES, SEEDS, N_STATES = 5, (0, 1), 2


# ---------------- data ----------------

def year_frame(year: int) -> pd.DataFrame:
    """One survey year with raw and harmonised features, labels' income, state, sex, race and weight."""
    path = DERIVED / f"acsincome_{year}.parquet"
    names = set(pq.read_schema(path).names)
    want = FEATURES + ["PINCP", "ST", "PWGTP", "RELSHIPP", "SERIALNO"]
    df = load_year(year, columns=[c for c in want if c in names])
    if SMOKE:
        df = df.sample(n=int(SMOKE), random_state=0).reset_index(drop=True)
    return harmonise(df, year)


def design(df: pd.DataFrame, features: str) -> np.ndarray:
    return folktables_matrix(df, HARMONISED_FEATURES if features == "harmonised" else FEATURES)


def largest_states(n: int = N_STATES) -> list[int]:
    st = load_year(TRAIN_YEAR, columns=["ST"])["ST"]
    st = st[st != 72]                                       # Puerto Rico excluded from the state arm
    return [int(s) for s in st.value_counts().index[:n]]


class Scaler:
    def __init__(self, X):
        self.mu, sd = X.mean(0), X.std(0)
        self.sd = np.where(sd > 0, sd, 1.0)

    def __call__(self, X):
        return (X - self.mu) / self.sd


def base_model(seed: int):
    from sklearn.ensemble import GradientBoostingClassifier
    return GradientBoostingClassifier(loss="exponential", max_depth=5, n_estimators=N_TREES, random_state=seed)


# ---------------- fitted predictors ----------------

class Frozen:
    """A fitted predictor with its frozen preprocessing. predict(df) -> bool array for all rows of df."""

    def __init__(self, name, features, scaler, kind, model, group=None, seed=0, lfr=None, keep=None):
        self.name, self.features, self.scaler, self.kind = name, features, scaler, kind
        self.model, self.group, self.seed, self.lfr = model, group, seed, lfr
        self.keep = keep          # sensitive-feature categories kept separate; all others pooled (POOLED)

    def sensitive(self, df: pd.DataFrame) -> np.ndarray:
        return pool_categories(df[GROUPS[self.group]].to_numpy().astype(int), self.keep)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        X = self.scaler(design(df, self.features))
        if self.kind == "gbm":
            return self.model.predict(X).astype(bool)
        if self.kind == "post":
            return np.asarray(self.model.predict(X, sensitive_features=self.sensitive(df),
                                                 random_state=self.seed)).astype(bool)
        if self.kind == "expgrad":
            return np.asarray(self.model.predict(X, random_state=self.seed)).astype(bool)
        if self.kind == "lfr":
            Z = self.lfr.transform(_aif_dataset(X, np.zeros(len(X)), df["RAC1P"].to_numpy())).features
            return self.model.predict(Z).astype(bool)
        raise ValueError(self.kind)


POOLED = 99
MIN_ROWS, MIN_EACH_LABEL = 100, 20


def kept_categories(sens: np.ndarray, y: np.ndarray) -> dict:
    """Pre-specified handling of small sensitive-feature categories (avoids degenerate groups):
    a category keeps its own threshold/constraint if it has >= MIN_ROWS training rows and >= MIN_EACH_LABEL rows
    of each label; the others are pooled into one category; if that pooled category itself fails the same test,
    its rows are assigned to the largest category instead. Returns {"keep": [...], "pooled_to": code}."""
    keep = []
    for c in np.unique(sens):
        m = sens == c
        if m.sum() >= MIN_ROWS and y[m].sum() >= MIN_EACH_LABEL and (~y[m]).sum() >= MIN_EACH_LABEL:
            keep.append(int(c))
    rest = ~np.isin(sens, keep)
    ok = rest.sum() >= MIN_ROWS and y[rest].sum() >= MIN_EACH_LABEL and (~y[rest]).sum() >= MIN_EACH_LABEL
    vals, counts = np.unique(sens, return_counts=True)
    return {"keep": keep, "pooled_to": POOLED if ok else int(vals[np.argmax(counts)])}


def pool_categories(sens: np.ndarray, spec: dict) -> np.ndarray:
    return np.where(np.isin(sens, spec["keep"]), sens, spec["pooled_to"])


def _aif_dataset(X, y, race):
    from aif360.datasets import BinaryLabelDataset
    d = pd.DataFrame(X, columns=[f"x{i}" for i in range(X.shape[1])])
    d["white"] = (race == WHITE).astype(float)
    d["y"] = np.asarray(y, dtype=float)
    return BinaryLabelDataset(df=d, label_names=["y"], protected_attribute_names=["white"],
                              favorable_label=1.0, unfavorable_label=0.0)


def _post(gbm, X, y, sens, constraint):
    from fairlearn.postprocessing import ThresholdOptimizer
    t = ThresholdOptimizer(estimator=gbm, prefit=True, predict_method="predict_proba", objective="accuracy_score",
                           constraints={"dp": "demographic_parity", "eo": "true_positive_rate_parity"}[constraint])
    return t.fit(X, y, sensitive_features=sens)


# ---------------- jobs ----------------

def _save(fz: Frozen, fit_seconds: float, n_train: int, train_year: int) -> dict:
    MODELS.mkdir(parents=True, exist_ok=True)
    path = MODELS / f"{fz.name}.joblib"
    joblib.dump(fz, path, compress=3)
    return {"name": fz.name, "file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "fit_seconds": round(fit_seconds, 1), "n_train": int(n_train), "kind": fz.kind,
            "features": fz.features, "group": fz.group, "seed": fz.seed,
            "kept_categories": fz.keep, "train_year": int(train_year)}


def model_prefix(job: dict) -> str:
    ty = job.get("train_year", TRAIN_YEAR)
    p = f"y{ty}_" if ty != TRAIN_YEAR else ""
    return p + (f"state{job['state']}_" if job.get("state") is not None else "")


def fit_job(job: dict) -> list[dict]:
    """Fit the models of one job on its training year (default 2014) and save them. Returns manifest entries."""
    seed = job["seed"]
    train_year = job.get("train_year", TRAIN_YEAR)
    df = year_frame(train_year)
    test = state_split(df, seed)
    if job.get("state") is not None:
        keep = (df["ST"] == job["state"]).to_numpy()
        df, test = df[keep].reset_index(drop=True), test[keep]
    tr = ~test
    y = label(df)
    feats = "raw" if job["kind"] == "rawgbm" else "harmonised"
    X = design(df, feats)
    scaler = Scaler(X[tr])
    Xs = scaler(X)
    out, t0 = [], time.time()
    prefix = model_prefix(job)
    if job["kind"] in ("gbm", "rawgbm"):
        gbm = base_model(seed).fit(Xs[tr], y[tr])
        name = f"{prefix}{'rawgbm' if feats == 'raw' else 'gbm'}_s{seed}"
        out.append(_save(Frozen(name, feats, scaler, "gbm", gbm, seed=seed), time.time() - t0, tr.sum(), train_year))
        for group, constraint in job.get("post", []):
            t1 = time.time()
            raw_sens = df[GROUPS[group]].to_numpy().astype(int)
            keep = kept_categories(raw_sens[tr], y[tr])
            sens = pool_categories(raw_sens, keep)
            post = _post(gbm, Xs[tr], y[tr], sens[tr], constraint)
            fz = Frozen(f"{prefix}post_{constraint}_{group}_s{seed}", feats, scaler, "post", post, group, seed,
                        keep=keep)
            out.append(_save(fz, time.time() - t1, tr.sum(), train_year))
    elif job["kind"] == "expgrad":
        from fairlearn.reductions import DemographicParity, ExponentiatedGradient
        raw_sens = df["RAC1P"].to_numpy().astype(int)
        keep = kept_categories(raw_sens[tr], y[tr])
        eg = ExponentiatedGradient(base_model(seed), constraints=DemographicParity())
        eg.fit(Xs[tr], y[tr], sensitive_features=pool_categories(raw_sens, keep)[tr])
        out.append(_save(Frozen(f"expgrad_dp_race_s{seed}", feats, scaler, "expgrad", eg, "race", seed,
                                keep=keep), time.time() - t0, tr.sum(), train_year))
    elif job["kind"] == "lfr":
        from aif360.algorithms.preprocessing import LFR
        race = df["RAC1P"].to_numpy()
        ds = _aif_dataset(Xs[tr], y[tr], race[tr])
        lfr = LFR(unprivileged_groups=[{"white": 0.0}], privileged_groups=[{"white": 1.0}],
                  k=10, Ax=0.1, Ay=1.0, Az=2.0, seed=seed, verbose=0)
        lfr.fit(ds, maxiter=5000, maxfun=5000)
        gbm = base_model(seed).fit(lfr.transform(ds).features, y[tr])
        out.append(_save(Frozen(f"lfr_race_s{seed}", feats, scaler, "lfr", gbm, "race", seed, lfr=lfr),
                         time.time() - t0, tr.sum(), train_year))
    else:
        raise ValueError(job)
    return out


def stage_a_jobs() -> list[dict]:
    post = [("race", "dp"), ("race", "eo"), ("sex", "dp"), ("sex", "eo")]
    jobs = [dict(kind="expgrad", seed=0), dict(kind="lfr", seed=0)]
    jobs += [dict(kind="gbm", seed=s, post=post) for s in SEEDS]
    jobs += [dict(kind="rawgbm", seed=0)]
    jobs += [dict(kind="gbm", seed=0, state=st, post=[("race", "dp")]) for st in largest_states()]
    jobs += [dict(kind="gbm", seed=s, train_year=2018, post=[("race", "dp"), ("sex", "dp")]) for s in SEEDS]
    return jobs


def train_year_of(name: str, manifest: dict) -> int:
    """Training year recorded in the manifest (entries written before 8.9 was added are 2014 models)."""
    return int(manifest[name].get("train_year", TRAIN_YEAR))


def predict_year(model_names: list[str], year: int) -> None:
    """Store predictions of the named frozen models for all rows of one year (bit-packed)."""
    df = year_frame(year)
    for name in model_names:
        out = PREDS / name / f"{year}.npy"
        if out.exists():
            continue
        fz = joblib.load(MODELS / f"{name}.joblib")
        pred = fz.predict(df)
        out.parent.mkdir(parents=True, exist_ok=True)
        np.save(out, np.packbits(pred))


def load_pred(name: str, year: int, n: int) -> np.ndarray:
    return np.unpackbits(np.load(PREDS / name / f"{year}.npy"))[:n].astype(bool)


def manifest_update(entries: list[dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    cur = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    for e in entries:
        cur[e["name"]] = e
    MANIFEST.write_text(json.dumps(dict(sorted(cur.items())), indent=1))
