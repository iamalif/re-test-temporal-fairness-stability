"""Confirmatory pipeline: fit every model once on 2014, freeze it, and store its predictions per survey year.

Primary specification (decision log D015; pre-registration section 4):
- features: harmonised ACSIncome features (src/harmonise.py), missing values -> 0 as in folktables;
- preprocessing: one standardisation fitted on the 2014 training split, frozen (trees are invariant to it;
  it matters only for LFR);
- base model: GradientBoostingClassifier(loss="exponential", max_depth=5, n_estimators=100);
- training data: 2014, within-state 80/20 split with the model's seed; the 2014 test split is the 2014 evaluation set;
  every other year is evaluated on all of its rows.

Model families (trained on 2014 unless prefixed y2018_):
- gbm_s{0..4}: base model, five seeds.
- post_{dp,eo}_{race,sex}_s{0..4}: fairlearn ThresholdOptimizer on gbm_s (group thresholds, objective accuracy),
  race = RAC1P (all categories), sex = SEX; randomised; evaluated through expected predictions.
- expgrad_dp_race_s0: fairlearn ExponentiatedGradient(DemographicParity), library defaults, RAC1P.
- lfr_race_s0: AIF360 LFR (k=10, Ax=0.1, Ay=1, Az=2), binary White indicator, base model on the representation.
- rawgbm_s0: base model on the raw (unharmonised) codes, for the recoding-artefact analysis on 2014-2018.
- state{ST}_gbm_s0, state{ST}_post_dp_race_s0: per-state models for the 20 largest states (by 2014 rows),
  trained on that state's 2014 training split.
- y2018_gbm_s{0..4}, y2018_post_dp_{race,sex}_s{0..4}: the same base model and DP post-processing trained on 2018
  instead (secondary analysis 8.9: is the pattern specific to a 2014 deployment?). Evaluated on the 2018 test split
  and on later years.
- peryear_gbm_s{0..4}: base model with per-year standardisation (scaler of each evaluated year fitted on that year's
  full eligible population; secondary analysis 8.6). Trees are invariant to the scaler of their own training data,
  so this differs from gbm_s only through the year-specific standardisation of later years.

Fitted models are written to data/derived/models/ (not committed); their SHA-256 hashes go to
results/models_manifest.json (committed and cited in the pre-registration); every load checks the hash.
Predictions are expected predictions P(output = 1) (float32) in data/derived/preds/<model>/<year>.npy, aligned with
the rows of data/derived/acsincome_<year>.parquet, each with a provenance record <year>.json (model hash, data-file
hash, row identity, convention, code fingerprint) that is verified before use.
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

FEATURE_SETS = {"raw": FEATURES, "harmonised": HARMONISED_FEATURES,
                "harmonised_norace": [f for f in HARMONISED_FEATURES if f != "RAC1P"]}

MODELS = DERIVED / "models"
PREDS = DERIVED / "preds"
MANIFEST = RESULTS / "models_manifest.json"
TRAIN_YEAR = 2014
N_TREES = 100
SEEDS = (0, 1, 2, 3, 4)
GROUPS = {"race": "RAC1P", "sex": "SEX"}
GBM_PARAMS = {"loss": "exponential", "max_depth": 5}          # plus n_estimators = N_TREES
POST_OBJECTIVE = "accuracy_score"
POST_CONSTRAINTS = {"dp": "demographic_parity", "eo": "true_positive_rate_parity"}
LFR_PARAMS = {"k": 10, "Ax": 0.1, "Ay": 1.0, "Az": 2.0}
LFR_FIT = {"maxiter": 5000, "maxfun": 5000}
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
    want = FEATURES + ["PINCP", "ST", "PWGTP", "RELSHIPP", "SERIALNO", "SPORDER"]
    df = load_year(year, columns=[c for c in want if c in names])
    if SMOKE:
        df = df.sample(n=int(SMOKE), random_state=0).reset_index(drop=True)
    return harmonise(df, year)


def design(df: pd.DataFrame, features: str) -> np.ndarray:
    return folktables_matrix(df, FEATURE_SETS[features])


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
    return GradientBoostingClassifier(**GBM_PARAMS, n_estimators=N_TREES, random_state=seed)


# ---------------- fitted predictors ----------------

class Frozen:
    """A fitted predictor with its frozen preprocessing. predict(df) -> expected predictions for all rows of df."""

    def __init__(self, name, features, scaler, kind, model, group=None, seed=0, lfr=None, keep=None):
        self.name, self.features, self.scaler, self.kind = name, features, scaler, kind
        self.model, self.group, self.seed, self.lfr = model, group, seed, lfr
        self.keep = keep          # sensitive-feature categories kept separate; all others pooled (POOLED)

    def sensitive(self, df: pd.DataFrame) -> np.ndarray:
        return pool_categories(df[GROUPS[self.group]].to_numpy().astype(int), self.keep)

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        X = design(df, self.features)
        if getattr(self, "scaling", "frozen") == "per_year":
            return Scaler(X)(X)             # standardised with the evaluated year's own full-population scaler
        return self.scaler(X)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Expected prediction P(output = 1) for every row of df. Deterministic models give 0/1; the randomised
        predictors (ThresholdOptimizer, ExponentiatedGradient) give the probability of a positive output, so
        metrics computed from it are the expected metrics of the randomised policy (pre-registration 4.4)."""
        X = self.transform(df)
        if self.kind == "gbm":
            return self.model.predict(X).astype(float)
        if self.kind == "post":
            return np.asarray(self.model._pmf_predict(X, sensitive_features=self.sensitive(df)))[:, 1].astype(float)
        if self.kind == "expgrad":
            return np.asarray(self.model._pmf_predict(X))[:, 1].astype(float)
        if self.kind == "lfr":
            Z = self.lfr.transform(_aif_dataset(X, np.zeros(len(X)), df["RAC1P"].to_numpy())).features
            return self.model.predict(Z).astype(float)
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
    t = ThresholdOptimizer(estimator=gbm, prefit=True, predict_method="predict_proba", objective=POST_OBJECTIVE,
                           constraints=POST_CONSTRAINTS[constraint])
    return t.fit(X, y, sensitive_features=sens)


# ---------------- jobs ----------------

def _ast_hash(*objs) -> str:
    """Hash of the code of functions/classes, ignoring comments, docstrings and formatting."""
    import ast
    import inspect
    import textwrap
    h = hashlib.sha256()
    for o in objs:
        tree = ast.parse(textwrap.dedent(inspect.getsource(o)))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and node.body and \
                    isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), ast.Constant) \
                    and isinstance(node.body[0].value.value, str):
                node.body = node.body[1:] or [ast.Pass()]
        h.update(ast.dump(tree, annotate_fields=False).encode())
    return h.hexdigest()


def _versions() -> dict:
    import aif360
    import fairlearn
    import scipy
    import sklearn
    return {"numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__,
            "sklearn": sklearn.__version__, "fairlearn": fairlearn.__version__, "aif360": aif360.__version__}


def semantic_config() -> dict:
    """Every configuration value that changes what a model learns or predicts, serialised by value (QA 3, R3-1):
    feature sets, group columns, label threshold and rule, race codes, pooling rule, estimator and intervention
    settings (including the library defaults of ExpGrad and its constraint)."""
    import common
    from fairlearn.reductions import DemographicParity, ExponentiatedGradient
    eg = {k: v for k, v in ExponentiatedGradient(base_model(0), constraints=DemographicParity()).get_params().items()
          if k not in ("estimator", "constraints")}
    dp = {k: v for k, v in DemographicParity().get_params().items()} if hasattr(DemographicParity(), "get_params") \
        else {}
    return {"FEATURE_SETS": FEATURE_SETS, "GROUPS": GROUPS, "THRESHOLD": common.THRESHOLD, "LABEL_RULE": ">",
            "WHITE": common.WHITE, "BLACK": common.BLACK, "TRAIN_YEAR": TRAIN_YEAR, "N_TREES": N_TREES,
            "GBM_PARAMS": GBM_PARAMS, "POOLING": {"POOLED": POOLED, "MIN_ROWS": MIN_ROWS,
                                                  "MIN_EACH_LABEL": MIN_EACH_LABEL},
            "POST": {"objective": POST_OBJECTIVE, "constraints": POST_CONSTRAINTS},
            "LFR": {"params": LFR_PARAMS, "fit": LFR_FIT}, "EXPGRAD": eg, "DEMOGRAPHIC_PARITY": dp,
            "MAPPING_SHA256": mapping_fingerprint()}


def _shared_code() -> list:
    """Functions on the path from a data file to a design matrix, used by fitting and by prediction."""
    import common
    import harmonise as H
    return [year_frame, design, common.folktables_matrix, common.load_year, H.harmonise, H.occp_group_map,
            H.group_codes, H.dictionary, H.dictionary_file, Scaler, pool_categories]


def fit_spec(job: dict) -> dict:
    """Everything that determines a fitted model (QA 2 R1, QA 3 R3-1/R3-7): job, semantic configuration by value,
    training-data hash, split code, the shared data-to-design code, and the code of this job's model family only
    (so a change to one family's fitting code does not invalidate the others), library versions."""
    import common
    fam = FIT_FAMILY[job["kind"]]
    family_code = [globals()[fam]] + [globals()[h] for h in FAMILY_HELPERS[fam]]
    return {"job": {k: job[k] for k in sorted(job)}, "features": FEATURE_SETS[job_features(job)],
            "config": semantic_config(), "gbm_params": base_model(job["seed"]).get_params(),
            "train_data_sha256": data_sha(job.get("train_year", TRAIN_YEAR)), "smoke": SMOKE,
            "split_code": _ast_hash(common.state_split),
            "shared_code": _ast_hash(_prepare, kept_categories, base_model, common.label, job_features,
                                     *_shared_code()),
            "family_code": _ast_hash(*family_code), "versions": _versions()}


def fit_spec_sha(job: dict) -> str:
    return hashlib.sha256(json.dumps(fit_spec(job), sort_keys=True, default=str).encode()).hexdigest()


def expected_specs() -> dict:
    """{model name: fit-spec hash} for the registered inventory."""
    return {n: fit_spec_sha(j) for j in stage_a_jobs() for n in job_names(j)}


def pred_spec_sha() -> str:
    """Prediction convention, semantic configuration by value, and the code that turns a frozen model and a data
    frame into predictions (including the per-year scaler and the sensitive-feature pooling)."""
    spec = {"convention": PRED_CONVENTION, "config": semantic_config(),
            "code": _ast_hash(Frozen, _aif_dataset, row_key, *_shared_code()), "versions": _versions()}
    return hashlib.sha256(json.dumps(spec, sort_keys=True, default=str).encode()).hexdigest()


def mapping_fingerprint() -> str:
    """Hash of the harmonisation mappings' content (not of the source file, so comments do not invalidate models)."""
    import harmonise as H
    spec = {"features": H.HARMONISED_FEATURES, "destination": H.DESTINATION_GROUP, "prefix": H.PREFIX_FIXES,
            "relshipp": H.RELSHIPP_TO_RELP, "relp": H.RELP_MERGE, "pobp": H.POBP_MERGE,
            "occp_2017": H.occp_group_map(2017), "occp_2018": H.occp_group_map(2018), "groups": H.group_codes()}
    return hashlib.sha256(json.dumps(spec, sort_keys=True, default=str).encode()).hexdigest()


def model_current(name: str, entry: dict, specs: dict) -> bool:
    """A frozen model is current if its fit specification equals the registered one and its file matches its hash."""
    path = MODELS / f"{name}.joblib"
    return (name in specs and entry.get("fit_spec_sha256") == specs[name] and path.exists()
            and sha256_file(path) == entry.get("sha256"))


# Training-only state that holds row-level training data. Fairlearn's ExponentiatedGradient keeps the training matrix,
# labels and group tags in constraints_ (a loaded copy of the constraint object); prediction (_pmf_predict) uses only
# the fitted predictors, their weights and the unloaded constraint object (freeze review FZ-1, D033).
TRAINING_CACHES = {"expgrad": ("constraints_",)}
ROW_LEVEL_MIN = 5000   # any array this long inside a model is treated as row-level data (largest legitimate array:
                       # ThresholdOptimizer's 1,001-point grids; smallest training set: 24,478 rows)


def inference_only(fz: Frozen) -> Frozen:
    """Remove the training-only caches of TRAINING_CACHES from a fitted model, in place; predictions are unchanged."""
    for attr in TRAINING_CACHES.get(fz.kind, ()):
        if hasattr(fz.model, attr):
            delattr(fz.model, attr)
    return fz


def row_level_arrays(obj, n_min: int = ROW_LEVEL_MIN) -> list:
    """Paths and shapes of arrays, frames, series and sequences with at least n_min rows anywhere in an object graph
    (attributes, containers, object arrays); a deposited model must have none (FZ-1)."""
    import pandas as pd_
    out, seen, stack = [], set(), [("model", obj)]
    while stack:
        path, o = stack.pop()
        if id(o) in seen or isinstance(o, (str, bytes, int, float, bool, type(None), np.number)):
            continue
        seen.add(id(o))
        if isinstance(o, np.ndarray):
            if o.ndim and o.shape[0] >= n_min:
                out.append((path, list(o.shape)))
            if o.dtype == object:
                stack += [(f"{path}[{i}]", v) for i, v in enumerate(o.ravel())]
        elif isinstance(o, (pd_.DataFrame, pd_.Series, pd_.Index)):
            if len(o) >= n_min:
                out.append((path, list(o.shape)))
            vals = o.to_numpy()
            if vals.dtype == object:
                stack += [(f"{path}.values[{i}]", v) for i, v in enumerate(vals.ravel())]
        elif isinstance(o, dict):
            stack += [(f"{path}[{k!r}]", v) for k, v in o.items()]
        elif isinstance(o, (list, tuple, set, frozenset)):
            if len(o) >= n_min:
                out.append((path, [len(o)]))
            stack += [(f"{path}[{i}]", v) for i, v in enumerate(o)]
        elif hasattr(o, "__dict__"):
            stack += [(f"{path}.{k}", v) for k, v in vars(o).items()]
        elif hasattr(o, "__slots__"):
            stack += [(f"{path}.{k}", getattr(o, k)) for k in o.__slots__ if hasattr(o, k)]
    return out


def dump_model(fz: Frozen) -> Path:
    """Write an inference-only model file atomically; refuses a model that still holds row-level arrays."""
    inference_only(fz)
    left = row_level_arrays(fz)
    if left:
        raise RuntimeError(f"model {fz.name} still holds row-level arrays: {left[:5]}")
    MODELS.mkdir(parents=True, exist_ok=True)
    path = MODELS / f"{fz.name}.joblib"
    tmp = path.with_suffix(".joblib.tmp")
    joblib.dump(fz, tmp, compress=3)
    os.replace(tmp, path)
    return path


def _save(fz: Frozen, fit_seconds: float, n_train: int, train_year: int, spec_sha: str) -> dict:
    path = dump_model(fz)
    return {"name": fz.name, "file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "fit_seconds": round(fit_seconds, 1), "n_train": int(n_train), "kind": fz.kind,
            "features": fz.features, "group": fz.group, "seed": fz.seed,
            "kept_categories": fz.keep, "train_year": int(train_year),
            "mapping_sha256": mapping_fingerprint() if fz.features.startswith("harmonised") else None,
            "scaling": getattr(fz, "scaling", "frozen"), "fit_spec_sha256": spec_sha, "versions": _versions()}


def model_prefix(job: dict) -> str:
    ty = job.get("train_year", TRAIN_YEAR)
    p = f"y{ty}_" if ty != TRAIN_YEAR else ""
    p += "norace_" if job.get("features") == "harmonised_norace" else ""
    return p + (f"state{job['state']}_" if job.get("state") is not None else "")


def job_features(job: dict) -> str:
    return "raw" if job["kind"] == "rawgbm" else job.get("features", "harmonised")


def _prepare(job: dict) -> dict:
    """Training data of a job: its training year (default 2014), within-state split of its seed, optional state."""
    seed = job["seed"]
    train_year = job.get("train_year", TRAIN_YEAR)
    df = year_frame(train_year)
    test = state_split(df, seed)
    if job.get("state") is not None:
        keep = (df["ST"] == job["state"]).to_numpy()
        df, test = df[keep].reset_index(drop=True), test[keep]
    tr = ~test
    feats = job_features(job)
    X = design(df, feats)
    scaler = Scaler(X[tr])
    return {"seed": seed, "train_year": train_year, "df": df, "tr": tr, "y": label(df), "feats": feats, "X": X,
            "scaler": scaler, "Xs": scaler(X), "prefix": model_prefix(job)}


def _fit_peryear(job: dict, c: dict, spec: str) -> list[dict]:
    # per-year-scaling pipeline (secondary 8.6): scaler fitted on all eligible rows of the training year;
    # at prediction time every year is standardised with its own full-population scaler
    t0 = time.time()
    full = Scaler(c["X"])
    gbm = base_model(c["seed"]).fit(full(c["X"])[c["tr"]], c["y"][c["tr"]])
    fz = Frozen(f"peryear_gbm_s{c['seed']}", c["feats"], full, "gbm", gbm, seed=c["seed"])
    fz.scaling = "per_year"
    return [_save(fz, time.time() - t0, c["tr"].sum(), c["train_year"], spec)]


def _fit_gbm(job: dict, c: dict, spec: str) -> list[dict]:
    t0, tr, y, seed = time.time(), c["tr"], c["y"], c["seed"]
    gbm = base_model(seed).fit(c["Xs"][tr], y[tr])
    name = f"{c['prefix']}{'rawgbm' if c['feats'] == 'raw' else 'gbm'}_s{seed}"
    out = [_save(Frozen(name, c["feats"], c["scaler"], "gbm", gbm, seed=seed), time.time() - t0, tr.sum(),
                 c["train_year"], spec)]
    for group, constraint in job.get("post", []):
        t1 = time.time()
        raw_sens = c["df"][GROUPS[group]].to_numpy().astype(int)
        keep = kept_categories(raw_sens[tr], y[tr])
        sens = pool_categories(raw_sens, keep)
        post = _post(gbm, c["Xs"][tr], y[tr], sens[tr], constraint)
        fz = Frozen(f"{c['prefix']}post_{constraint}_{group}_s{seed}", c["feats"], c["scaler"], "post", post, group,
                    seed, keep=keep)
        out.append(_save(fz, time.time() - t1, tr.sum(), c["train_year"], spec))
    return out


def _fit_expgrad(job: dict, c: dict, spec: str) -> list[dict]:
    from fairlearn.reductions import DemographicParity, ExponentiatedGradient
    t0, tr, y, seed = time.time(), c["tr"], c["y"], c["seed"]
    raw_sens = c["df"][GROUPS["race"]].to_numpy().astype(int)
    keep = kept_categories(raw_sens[tr], y[tr])
    eg = ExponentiatedGradient(base_model(seed), constraints=DemographicParity())
    eg.fit(c["Xs"][tr], y[tr], sensitive_features=pool_categories(raw_sens, keep)[tr])
    return [_save(Frozen(f"expgrad_dp_race_s{seed}", c["feats"], c["scaler"], "expgrad", eg, "race", seed, keep=keep),
                  time.time() - t0, tr.sum(), c["train_year"], spec)]


def _fit_lfr(job: dict, c: dict, spec: str) -> list[dict]:
    from aif360.algorithms.preprocessing import LFR
    t0, tr, y, seed = time.time(), c["tr"], c["y"], c["seed"]
    race = c["df"][GROUPS["race"]].to_numpy()
    ds = _aif_dataset(c["Xs"][tr], y[tr], race[tr])
    lfr = LFR(unprivileged_groups=[{"white": 0.0}], privileged_groups=[{"white": 1.0}], **LFR_PARAMS, seed=seed,
              verbose=0)
    lfr.fit(ds, **LFR_FIT)
    gbm = base_model(seed).fit(lfr.transform(ds).features, y[tr])
    return [_save(Frozen(f"lfr_race_s{seed}", c["feats"], c["scaler"], "lfr", gbm, "race", seed, lfr=lfr),
                  time.time() - t0, tr.sum(), c["train_year"], spec)]


FIT_FAMILY = {"gbm": "_fit_gbm", "rawgbm": "_fit_gbm", "peryear": "_fit_peryear", "expgrad": "_fit_expgrad",
              "lfr": "_fit_lfr"}
FAMILY_HELPERS = {"_fit_gbm": ("_post",), "_fit_lfr": ("_aif_dataset",), "_fit_peryear": (), "_fit_expgrad": ()}


def fit_job(job: dict) -> list[dict]:
    """Fit the models of one job on its training year (default 2014) and save them. Returns manifest entries."""
    if job["kind"] not in FIT_FAMILY:
        raise ValueError(job)
    spec = fit_spec_sha(job)
    return globals()[FIT_FAMILY[job["kind"]]](job, _prepare(job), spec)


def stage_a_jobs() -> list[dict]:
    post = [("race", "dp"), ("race", "eo"), ("sex", "dp"), ("sex", "eo")]
    jobs = [dict(kind="expgrad", seed=0), dict(kind="lfr", seed=0)]
    jobs += [dict(kind="gbm", seed=s, post=post) for s in SEEDS]
    jobs += [dict(kind="rawgbm", seed=0)]
    jobs += [dict(kind="gbm", seed=0, state=st, post=[("race", "dp")]) for st in largest_states()]
    jobs += [dict(kind="gbm", seed=s, train_year=2018, post=[("race", "dp"), ("sex", "dp")]) for s in SEEDS]
    jobs += [dict(kind="peryear", seed=s) for s in SEEDS]
    # sensitivity (secondary 8.10): without race as a feature, for the sex endpoints (race coding changed in 2020)
    jobs += [dict(kind="gbm", seed=s, features="harmonised_norace", post=[("sex", "dp")]) for s in SEEDS]
    return jobs


def job_names(job: dict) -> list[str]:
    """Names of the models a job produces (used for resuming and for the exact inventory check)."""
    p = model_prefix(job)
    if job["kind"] in ("gbm", "rawgbm"):
        return [f"{p}{job['kind']}_s{job['seed']}"] + [f"{p}post_{c}_{g}_s{job['seed']}"
                                                         for g, c in job.get("post", [])]
    return [{"expgrad": f"expgrad_dp_race_s{job['seed']}", "lfr": f"lfr_race_s{job['seed']}",
             "peryear": f"peryear_gbm_s{job['seed']}"}[job["kind"]]]


def expected_models() -> list[str]:
    return sorted(n for j in stage_a_jobs() for n in job_names(j))


def train_year_of(name: str, manifest: dict) -> int:
    """Training year recorded in the manifest (entries written before 8.9 was added are 2014 models)."""
    return int(manifest[name].get("train_year", TRAIN_YEAR))


PRED_CONVENTION = "expected-v2"     # float32 P(output = 1) per row; person-level row key (pre-registration 4.4)
_DATA_SHA: dict = {}
_CACHE: dict = {}


def _pred_spec() -> str:
    if "pred_spec" not in _CACHE:
        _CACHE["pred_spec"] = pred_spec_sha()
    return _CACHE["pred_spec"]


def _manifest() -> dict:
    """The frozen-model manifest, read once per process (a run uses one immutable model inventory)."""
    if "manifest" not in _CACHE:
        _CACHE["manifest"] = json.loads(MANIFEST.read_text())
    return _CACHE["manifest"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def data_sha(year: int) -> str:
    if year not in _DATA_SHA:
        _DATA_SHA[year] = sha256_file(DERIVED / f"acsincome_{year}.parquet")
    return _DATA_SHA[year]


ROW_ID = ["ST", "SERIALNO", "SPORDER"]      # person identity: household (state, serial number) + person number


def row_key(df: pd.DataFrame) -> str:
    """Identity and order of the evaluated rows: hash of (ST, SERIALNO, SPORDER) in row order, plus the row count."""
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(df["ST"].to_numpy().astype(np.int64)).tobytes())
    h.update("\x1f".join(df["SERIALNO"].astype(str)).encode())
    h.update(np.ascontiguousarray(df["SPORDER"].to_numpy().astype(np.int64)).tobytes())
    return f"{len(df)}:{h.hexdigest()}"


def assert_unique_persons(df: pd.DataFrame) -> None:
    if df.duplicated(ROW_ID).any():
        raise RuntimeError("person identity (ST, SERIALNO, SPORDER) is not unique")


def load_model(name: str, manifest: dict | None = None) -> "Frozen":
    """Load a frozen model after checking its bytes against the SHA-256 recorded in the manifest."""
    manifest = manifest or json.loads(MANIFEST.read_text())
    path = MODELS / f"{name}.joblib"
    got = sha256_file(path)
    if got != manifest[name]["sha256"]:
        raise RuntimeError(f"model {name}: file hash {got[:12]} differs from manifest {manifest[name]['sha256'][:12]}")
    return joblib.load(path)


def _pred_paths(name: str, year: int) -> tuple[Path, Path]:
    d = PREDS / name
    return d / f"{year}.npy", d / f"{year}.json"


def _pred_valid(name: str, year: int, manifest: dict, df: pd.DataFrame | None = None) -> bool:
    arr, meta = _pred_paths(name, year)
    if not (arr.exists() and meta.exists()):
        return False
    m = json.loads(meta.read_text())
    ok = (m.get("convention") == PRED_CONVENTION and m.get("pred_spec_sha256") == _pred_spec()
          and m.get("model_sha256") == manifest[name]["sha256"]
          and m.get("data_sha256") == data_sha(year) and m.get("pred_sha256") == sha256_file(arr))
    if ok and df is not None:
        ok = m.get("row_key") == row_key(df)
    return ok


def predict_year(model_names: list[str], year: int) -> None:
    """Store expected predictions of the named frozen models for all rows of one year, with a provenance record.
    Existing predictions are reused only if model hash, data hash, row identity and convention all match."""
    manifest = json.loads(MANIFEST.read_text())
    df = year_frame(year)
    assert_unique_persons(df)
    key = row_key(df)
    for name in model_names:
        if _pred_valid(name, year, manifest, df):
            continue
        fz = load_model(name, manifest)
        pred = np.asarray(fz.predict(df), dtype=np.float32)
        if len(pred) != len(df) or not np.all(np.isfinite(pred)):
            raise RuntimeError(f"{name} {year}: bad prediction vector")
        arr, meta = _pred_paths(name, year)
        arr.parent.mkdir(parents=True, exist_ok=True)
        tmp = arr.with_suffix(".tmp.npy")
        np.save(tmp, pred)
        os.replace(tmp, arr)
        rec = {"model": name, "year": year, "convention": PRED_CONVENTION, "n": len(pred), "row_key": key,
               "model_sha256": manifest[name]["sha256"], "data_sha256": data_sha(year),
               "pred_sha256": sha256_file(arr), "pred_spec_sha256": _pred_spec(),
               "code_sha256": code_fingerprint()}
        tmpj = meta.with_suffix(".tmp.json")
        tmpj.write_text(json.dumps(rec, indent=1))
        os.replace(tmpj, meta)


def load_pred(name: str, year: int, df: pd.DataFrame) -> np.ndarray:
    """Expected predictions of a frozen model for the rows of df (all eligible rows of that year, in file order).
    Refuses predictions whose provenance record does not match the current model, data file and rows."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("load_pred needs the evaluated data frame (row identity is verified)")
    arr, meta = _pred_paths(name, year)
    m = json.loads(meta.read_text())
    if m.get("row_key") != row_key(df) or m.get("convention") != PRED_CONVENTION:
        raise RuntimeError(f"predictions {name}/{year}: rows or convention differ from the evaluated frame")
    if m.get("data_sha256") != data_sha(year):
        raise RuntimeError(f"predictions {name}/{year}: data file changed since prediction")
    if m.get("pred_sha256") != sha256_file(arr):
        raise RuntimeError(f"predictions {name}/{year}: file differs from its provenance record")
    if m.get("pred_spec_sha256") != _pred_spec():
        raise RuntimeError(f"predictions {name}/{year}: made with another prediction specification")
    if m.get("model_sha256") != _manifest()[name]["sha256"]:
        raise RuntimeError(f"predictions {name}/{year}: made by a model that is not the current frozen model")
    p = np.load(arr)
    if len(p) != len(df):
        raise RuntimeError(f"predictions {name}/{year}: length {len(p)} != {len(df)}")
    return p.astype(float)


def code_fingerprint() -> str:
    """Hash of the source files that define features, preprocessing and prediction (recorded, not enforced)."""
    h = hashlib.sha256()
    src = Path(__file__).resolve().parent
    for f in ("common.py", "harmonise.py", "pipeline.py", "data.py"):
        h.update((src / f).read_bytes())
    return h.hexdigest()


def provenance(script: str | None = None, inputs: list | None = None) -> dict:
    """Identity of the inputs of a result file: model manifest, prediction specification, git commit and the code
    that produced it (src/*.py plus the producing script), and the SHA-256 of every consumed input file (upstream
    result files, calibration files, data files, price index), so that a change upstream makes it stale (QA 3,
    A3-2). check_outputs.py compares all of these with the current state."""
    import inspect
    import subprocess
    root = Path(__file__).resolve().parents[1]
    if script is None:                  # the calling script
        script = Path(inspect.stack()[1].filename).name
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "src", "scripts"], cwd=root,
                                    capture_output=True, text=True).stdout.strip())
    except OSError:
        commit, dirty = "", None
    return {"models_manifest_sha256": sha256_file(MANIFEST) if MANIFEST.exists() else None,
            "pred_spec_sha256": _pred_spec(), "git_commit": commit, "git_dirty_code": dirty,
            "script": script, "code_sha256": code_sha(script), "smoke": bool(SMOKE),
            "inputs": {rel: sha256_file(root / rel) for rel in (inputs or [])},
            "time": time.strftime("%Y-%m-%dT%H:%M:%S")}


def stale_inputs(prov: dict) -> list:
    """Inputs recorded in a provenance block whose current bytes differ (or that no longer exist)."""
    root = Path(__file__).resolve().parents[1]
    out = []
    for rel, h in (prov.get("inputs") or {}).items():
        p = root / rel
        if not p.exists() or sha256_file(p) != h:
            out.append(rel)
    return out


def data_files(years) -> list:
    return [f"data/derived/acsincome_{y}.parquet" for y in years]


def code_sha(script: str) -> str:
    """Hash of src/*.py and the producing script(s) ("a.py+b.py" for a script that uses another one's code)."""
    root = Path(__file__).resolve().parents[1]
    code = hashlib.sha256()
    for f in sorted((root / "src").glob("*.py")) + [root / "scripts" / x for x in script.split("+")]:
        if f.exists():
            code.update(f.name.encode()); code.update(f.read_bytes())
    return code.hexdigest()


def prediction_years(name: str, manifest: dict, years) -> list[int]:
    """Years a model is evaluated on: from its training year on; raw-code models only on 2014-2018."""
    ty = train_year_of(name, manifest)
    return [y for y in years if y >= ty and not (name.startswith("rawgbm") and y > 2018)]


def verify_inventory(years, write_record: bool = True) -> dict:
    """Exact inventory check before any analysis: the manifest holds exactly the expected models, every model file
    matches its hash, and every required prediction exists with a matching provenance record. Raises otherwise."""
    manifest = json.loads(MANIFEST.read_text())
    specs = expected_specs()
    expected = set(specs)
    problems = []
    if set(manifest) != expected:
        problems.append(f"manifest differs: missing {sorted(expected - set(manifest))[:8]}, "
                        f"unexpected {sorted(set(manifest) - expected)[:8]}")
    for name in sorted(expected & set(manifest)):
        if not model_current(name, manifest[name], specs):
            problems.append(f"model missing, altered or fitted under another specification: {name}")
            continue
        for y in prediction_years(name, manifest, years):
            if not _pred_valid(name, y, manifest):
                problems.append(f"prediction missing or stale: {name}/{y}")
    states = sorted({n.split("_")[0] for n in manifest if n.startswith("state")})
    if not SMOKE and len(states) != N_STATES:
        problems.append(f"{len(states)} source states, expected {N_STATES}")
    rec = {"checked_years": list(years), "n_models": len(manifest), "problems": problems,
           "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "provenance": provenance()}
    if write_record:                    # one record per set of checked years (Stage A and Stage B keep theirs)
        out = (MANIFEST.parent / ("inventory_check.json" if not SMOKE else "smoke_inventory_check.json"))
        allrec = json.loads(out.read_text()) if out.exists() else {}
        if "checked_years" in allrec:   # older single-record format
            allrec = {}
        allrec["-".join(map(str, sorted(years)))] = rec
        out.write_text(json.dumps(allrec, indent=1))
    if problems:
        raise RuntimeError("inventory check failed:\n  " + "\n  ".join(problems[:30]))
    return rec


def manifest_update(entries: list[dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    cur = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    for e in entries:
        cur[e["name"]] = e
    tmp = MANIFEST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(dict(sorted(cur.items())), indent=1))
    os.replace(tmp, MANIFEST)
