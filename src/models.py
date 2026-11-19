"""Models and fairness interventions of Ding et al. (2021, App. C), with the choices they leave open made explicit.

Base model: sklearn GradientBoostingClassifier with exponential loss and max_depth 5. The number of trees is a
parameter because the value stated in the paper (5) does not reproduce its results (decision log D012).

Interventions (each fitted on the training year only):
- postprocessing: fairlearn ThresholdOptimizer on the fitted GBM's scores (group-specific thresholds,
  Hardt et al. 2016), objective accuracy, randomised predictions with a fixed seed.
- expgrad: fairlearn ExponentiatedGradient around the same GBM specification, library defaults.
- lfr: AIF360 LFR with the App. C hyperparameters (k=10, Ax=0.1, Ay=1.0, Az=2.0, maxiter=maxfun=5000),
  protected attribute White vs non-White as in AIF360's Adult tutorial; a GBM is trained on the representation.
Open choices fixed here (to be pre-specified): the sensitive feature for postprocessing and expgrad is RAC1P
with all its categories; LFR uses the binary White indicator because AIF360's LFR needs a binary attribute.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from common import FEATURES, WHITE, folktables_matrix, label, load_year, state_split


# ---------------- data preparation ----------------

def year_arrays(year: int, seed: int):
    df = load_year(year, columns=FEATURES + ["PINCP", "ST"])
    smoke = os.environ.get("RT_SMOKE_ROWS")          # smoke tests only: a small fixed subsample
    if smoke:
        df = df.sample(n=int(smoke), random_state=0).reset_index(drop=True)
    X = folktables_matrix(df)
    return X, label(df), df["RAC1P"].to_numpy().astype(int), state_split(df, seed)


class Scaling:
    """'common': one scaler fitted on the training split of the training year, used for every year.
    'per_year': a scaler fitted on all rows of each year, used for that year (hypothesis H-scale, D012)."""

    def __init__(self, kind: str, X_train: np.ndarray):
        assert kind in ("common", "per_year")
        self.kind = kind
        self.mu, self.sd = X_train.mean(0), X_train.std(0)

    def apply(self, X_year: np.ndarray) -> np.ndarray:
        if self.kind == "common":
            mu, sd = self.mu, self.sd
        else:
            mu, sd = X_year.mean(0), X_year.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        return (X_year - mu) / sd


def gbm(n_trees: int, seed: int) -> GradientBoostingClassifier:
    return GradientBoostingClassifier(loss="exponential", n_estimators=n_trees, max_depth=5, random_state=seed)


# ---------------- methods ----------------

class Method:
    """fit(X, y, race) on the training year; predict(X, race) on any year."""
    name = "gbm"

    def __init__(self, n_trees: int, seed: int, constraint: str | None = None):
        self.n_trees, self.seed, self.constraint = n_trees, seed, constraint

    def fit(self, X, y, race):
        self.model = gbm(self.n_trees, self.seed).fit(X, y)
        return self

    def predict(self, X, race):
        return self.model.predict(X).astype(bool)


class PostProcessing(Method):
    name = "postprocessing"

    def fit(self, X, y, race):
        from fairlearn.postprocessing import ThresholdOptimizer
        base = gbm(self.n_trees, self.seed).fit(X, y)
        cons = {"dp": "demographic_parity", "eo": "true_positive_rate_parity"}[self.constraint]
        self.model = ThresholdOptimizer(estimator=base, constraints=cons, objective="accuracy_score",
                                        prefit=True, predict_method="predict_proba")
        self.model.fit(X, y, sensitive_features=race)
        return self

    def predict(self, X, race):
        return np.asarray(self.model.predict(X, sensitive_features=race, random_state=self.seed)).astype(bool)


class ExpGrad(Method):
    name = "expgrad"

    def fit(self, X, y, race):
        from fairlearn.reductions import DemographicParity, ExponentiatedGradient, TruePositiveRateParity
        cons = {"dp": DemographicParity, "eo": TruePositiveRateParity}[self.constraint]()
        self.model = ExponentiatedGradient(gbm(self.n_trees, self.seed), constraints=cons)
        self.model.fit(X, y, sensitive_features=race)
        return self

    def predict(self, X, race):
        return np.asarray(self.model.predict(X, random_state=self.seed)).astype(bool)


class LFRMethod(Method):
    name = "lfr"

    def _dataset(self, X, y, race):
        from aif360.datasets import BinaryLabelDataset
        df = pd.DataFrame(X, columns=FEATURES)
        df["white"] = (race == WHITE).astype(float)
        df["y"] = y.astype(float)
        return BinaryLabelDataset(df=df, label_names=["y"], protected_attribute_names=["white"],
                                  favorable_label=1.0, unfavorable_label=0.0)

    def fit(self, X, y, race):
        from aif360.algorithms.preprocessing import LFR
        ds = self._dataset(X, y, race)
        self.lfr = LFR(unprivileged_groups=[{"white": 0.0}], privileged_groups=[{"white": 1.0}],
                       k=10, Ax=0.1, Ay=1.0, Az=2.0, seed=self.seed, verbose=0)
        self.lfr.fit(ds, maxiter=5000, maxfun=5000)
        Z = self.lfr.transform(ds).features
        self.model = gbm(self.n_trees, self.seed).fit(Z, y)
        return self

    def predict(self, X, race):
        dummy_y = np.zeros(len(X), dtype=bool)
        Z = self.lfr.transform(self._dataset(X, dummy_y, race)).features
        return self.model.predict(Z).astype(bool)


METHODS = {"gbm": Method, "postprocessing": PostProcessing, "expgrad": ExpGrad, "lfr": LFRMethod}
