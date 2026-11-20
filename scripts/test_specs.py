"""Specification-sensitivity tests (QA 3, R3-1 and R3-7): changing one semantic setting at a time must change the
fit and/or prediction specification of the affected models, and changing one model family's fitting code must not
change the other families' fit specifications. Reads only the hash of the 2014/2018 data files (no records).
Writes results/validation/spec_tests.json; exits non-zero on any failure."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import common
import harmonise as H
import pipeline as P

JOBS = {"gbm": dict(kind="gbm", seed=0, post=[("race", "dp"), ("sex", "dp")]), "expgrad": dict(kind="expgrad", seed=0),
        "lfr": dict(kind="lfr", seed=0), "peryear": dict(kind="peryear", seed=0),
        "norace": dict(kind="gbm", seed=0, features="harmonised_norace", post=[("sex", "dp")])}
results = {}


def snapshot():
    P._CACHE.clear()
    H.occp_group_map.cache_clear(); H.group_codes.cache_clear() if hasattr(H.group_codes, "cache_clear") else None
    return {k: P.fit_spec_sha(j) for k, j in JOBS.items()}, P.pred_spec_sha()


BASE_FIT, BASE_PRED = snapshot()


def check(name, mutate, restore, fit_changes, pred_changes):
    mutate()
    try:
        fit, pred = snapshot()
    finally:
        restore()
    changed = {k for k in JOBS if fit[k] != BASE_FIT[k]}
    ok = changed == set(fit_changes) and ((pred != BASE_PRED) == pred_changes)
    results[name] = {"passed": ok, "fit_specs_changed": sorted(changed), "expected": sorted(fit_changes),
                     "pred_spec_changed": pred != BASE_PRED, "expected_pred_change": pred_changes}


def setattr_case(name, obj, attr, value, fit_changes, pred_changes):
    old = copy.deepcopy(getattr(obj, attr))
    check(name, lambda: setattr(obj, attr, value), lambda: setattr(obj, attr, old), fit_changes, pred_changes)


ALL = list(JOBS)
setattr_case("GROUPS sex column", P, "GROUPS", {"race": "RAC1P", "sex": "RAC1P"}, ALL, True)
setattr_case("feature set", P, "FEATURE_SETS", {**P.FEATURE_SETS, "harmonised": P.FEATURE_SETS["harmonised"][:-1]},
             ALL, True)
setattr_case("label threshold", common, "THRESHOLD", 60000, ALL, True)
setattr_case("race code WHITE", common, "WHITE", 9, ALL, True)
setattr_case("number of trees", P, "N_TREES", 50, ALL, True)
setattr_case("pooling rule", P, "MIN_ROWS", 50, ALL, True)
setattr_case("LFR hyperparameter", P, "LFR_PARAMS", {**P.LFR_PARAMS, "k": 5}, ALL, True)
setattr_case("post-processing constraint", P, "POST_CONSTRAINTS", {"dp": "x", "eo": "y"}, ALL, True)
setattr_case("occupation mapping", H, "DESTINATION_GROUP", {**H.DESTINATION_GROUP, 4320: "TRN"}, ALL, True)


# family isolation: replacing one family's fitting function changes only that family's fit specification
def dummy(job, c, spec):
    return [c, spec, "different"]


for fam_fn, affected in (("_fit_lfr", ["lfr"]), ("_fit_expgrad", ["expgrad"]), ("_fit_peryear", ["peryear"]),
                         ("_fit_gbm", ["gbm", "norace"])):
    old = getattr(P, fam_fn)
    check(f"family isolation {fam_fn}", lambda f=fam_fn: setattr(P, f, dummy), lambda f=fam_fn, o=old: setattr(P, f, o),
          affected, False)

# lineage (QA 3, A3-2): a result whose upstream input file changes must be reported stale
up = ROOT / "results" / "validation" / "_lineage_test_upstream.json"
up.parent.mkdir(parents=True, exist_ok=True)
up.write_text(json.dumps({"multipliers": [1.1]}))
prov = P.provenance("stage_a_analysis.py", inputs=[str(up.relative_to(ROOT))])
before = P.stale_inputs(prov)
up.write_text(json.dumps({"multipliers": [1.2]}))      # only the upstream file changes
after = P.stale_inputs(prov)
results["lineage: changed upstream file makes dependants stale"] = {
    "passed": before == [] and after == [str(up.relative_to(ROOT))], "fit_specs_changed": [], "expected": [],
    "pred_spec_changed": False, "expected_pred_change": False}
up.write_text("{}")                                     # left in place (deleting files may be disallowed)

passed = all(v["passed"] for v in results.values())
for k, v in results.items():
    print(f"{k:40s} {'ok' if v['passed'] else 'FAILED'}  changed={v['fit_specs_changed']} pred={v['pred_spec_changed']}")
out = ROOT / "results" / "validation"
out.mkdir(parents=True, exist_ok=True)
(out / "spec_tests.json").write_text(json.dumps({"tests": results, "all_passed": passed,
                                                 "script_sha256": P.sha256_file(Path(__file__))}, indent=1))
sys.exit(0 if passed else 1)
