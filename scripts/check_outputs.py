"""Pre-registration-to-output checklist and freshness gate (QA 1 #16, QA 2 A7).
The human-readable list is prereg/OUTPUT_CHECKLIST.md; this script enforces it.

  python scripts/check_outputs.py stage_a     # before archiving
  python scripts/check_outputs.py stage_b     # after the confirmatory and secondary runs

Beyond existence it checks that (i) the model inventory, hashes and prediction provenance are current now (the
inventory check is re-run, not read from a file); (ii) every result file was produced from the current model
manifest, prediction specification and analysis code (its embedded provenance block); (iii) the registered
acceptance criteria of the validation results hold and their alpha equals the family alpha; (iv) the output
inventories are complete. Exits non-zero and lists every problem.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np
import pandas as pd

METRICS = ("accuracy", "dp_race", "eo_race", "dp_sex", "eo_sex")
WT = ("unweighted", "weighted")
FAMILY = ["C1", "C2", "C3", "C4", "C6", "C7"]
ALPHA = 0.05 / len(FAMILY)
problems = []


def need(cond, msg):
    if not cond:
        problems.append(msg)


def load(rel):
    p = ROOT / rel
    if not p.exists():
        problems.append(f"missing file {rel}")
        return None
    return json.loads(p.read_text()) if p.suffix == ".json" else pd.read_csv(p)


def fresh(rel, prov, current):
    """The result file's provenance must match the current manifest and prediction specification, and the current
    code of src/ and of the script(s) that produced it."""
    from pipeline import code_sha
    if not isinstance(prov, dict):
        problems.append(f"{rel}: no provenance block")
        return
    for k in ("models_manifest_sha256", "pred_spec_sha256"):
        if prov.get(k) != current.get(k):
            problems.append(f"{rel}: produced with a different {k.replace('_sha256', '')} (stale; rerun that step)")
    if prov.get("code_sha256") != code_sha(prov.get("script", "")):
        problems.append(f"{rel}: code of {prov.get('script')} or src/ changed since it was produced (rerun that step)")
    from pipeline import stale_inputs
    for inp in stale_inputs(prov):
        problems.append(f"{rel}: input {inp} changed since it was produced (rerun that step)")
    if prov.get("smoke"):
        problems.append(f"{rel}: produced in smoke mode")


def check_validation(val):
    """Recompute the acceptance criteria from the detailed validation results and require complete case grids
    (QA 3, A3-4); the summary booleans in the file are not trusted."""
    acc = val.get("acceptance", {})
    for wt in WT:
        r = val.get(wt, {})
        tw = r.get("three_way", {})
        need(set(tw) == {"C1", "C2", "C3", "C4", "C5", "C6", "C5_secondary"}, f"validation[{wt}]: three-way claims")
        for c, v in tw.items():
            need(sorted(r_["theta_over_margin"] for r_ in v.get("rows", [])) == [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0],
                 f"validation[{wt}] {c}: the 9 registered theta values, each once")
            if not c.endswith("secondary"):
                need(all(row["p_holds"] <= ALPHA / 2 + 1e-9 for row in v.get("rows", [])
                         if row["theta_over_margin"] >= 1), f"validation[{wt}] {c}: false holds above alpha/2")
        from validate_inference import C7_SETTINGS, c7_grid
        c7 = r.get("C7", [])
        need([x.get("label") for x in c7] == C7_SETTINGS[wt], f"validation[{wt}]: C7 settings {C7_SETTINGS[wt]}")
        for x in c7:
            rows = x.get("rows", [])
            want = sorted(c7_grid(x["cov"], x["G_fair"], x["G_acc"]))
            got = sorted((rw["a"], rw["b"]) for rw in rows)
            need(got == want, f"validation[{wt}] C7 {x.get('label')}: grid differs from the registered grid")
            need(rows and min(rw["coverage"] for rw in rows) >= 1 - ALPHA, f"validation[{wt}] C7 {x.get('label')}: coverage")
        jt = r.get("joint", {})
        need(set(jt) == {"C1", "C2", "C3", "C4", "C6"}, f"validation[{wt}]: joint simulation claims")
        for c, v in jt.items():
            rows, n = v.get("rows", []), v.get("reps", 0)
            coords = sorted((rw["history"], rw["theta"]) for rw in rows)
            want = sorted((h, t) for h in ("flat", "observed shape", "trend")
                          for t in (-0.02, -0.01, -0.005, 0.0, 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.02, 0.03))
            need(coords == want and n >= 20000, f"validation[{wt}] joint {c}: the 33 registered cells, each once, "
                                                f">= 20000 replicates")
            for rw in rows:
                need(rw["p_false_holds"] <= ALPHA / 2 + 3 * np.sqrt(ALPHA / 2 * (1 - ALPHA / 2) / max(n, 1)),
                     f"validation[{wt}] joint {c} {rw['history']} theta={rw['theta']}: false holds")
                need(rw["p_false_violated"] <= ALPHA + 3 * np.sqrt(ALPHA * (1 - ALPHA) / max(n, 1)),
                     f"validation[{wt}] joint {c} {rw['history']} theta={rw['theta']}: false violated")
    need(abs(acc.get("three_way_false_holds_max", 0) - ALPHA / 2) < 1e-12, "validation: registered acceptance values")


def check_models_inference_only(man):
    """No deposited model may hold row-level data (freeze review FZ-1, D033): every model file is loaded (hash-checked)
    and its object graph scanned; the inference-only export record must match the manifest and show identical
    predictions for every evaluated year."""
    from pipeline import TRAINING_CACHES, load_model, row_level_arrays
    for name in sorted(man):
        try:
            fz = load_model(name, man)
        except Exception as e:                             # noqa: BLE001
            problems.append(f"model {name}: {str(e)[:200]}")
            continue
        found = row_level_arrays(fz)
        need(not found, f"model {name}: holds row-level arrays {found[:3]}")
        need(not any(hasattr(fz.model, a) for a in TRAINING_CACHES.get(fz.kind, ())), f"model {name}: training cache")
    rec = load("results/validation/inference_only_export.json")
    need(rec is not None, "inference-only export record missing (scripts/export_inference_only.py)")
    if rec:
        for name, e in rec.get("exports", {}).items():
            need(man.get(name, {}).get("sha256") == e.get("new_sha256"), f"export record {name}: manifest hash differs")
            need(man.get(name, {}).get("inference_only", {}).get("exported_from_sha256") == e.get("old_sha256"),
                 f"export record {name}: original hash differs")
            preds = e.get("predictions", {})
            need(sorted(preds) == [str(y) for y in range(2014, 2019)] and
                 all(v.get("identical") is True and v["old_pred_sha256"] == v["new_pred_sha256"] for v in preds.values()),
                 f"export record {name}: predictions not identical for every year 2014-2018")
        need(rec.get("audit_after", {}).get("with_row_level_arrays") == 0, "export record: audit after export")


def stage_a(current):
    from pipeline import N_STATES, expected_specs, verify_inventory
    from reconstruct import load_runs
    try:
        verify_inventory([2014, 2015, 2016, 2017, 2018], write_record=False)
    except Exception as e:                                 # noqa: BLE001
        problems.append(f"inventory check now: {str(e)[:300]}")
    try:
        load_runs("all")
    except Exception as e:                                 # noqa: BLE001
        problems.append(f"reconstruction inventory: {e}")
    tex = ROOT / "paper" / "numbers_reconstruction.tex"
    need(tex.exists() and "PreprocContrastShare" in tex.read_text(), "reconstruction macros (PreprocContrastShare)")
    for f in ("results/reconstruction/comparison.csv", "results/reconstruction/figure4_digitised.json",
              "results/reconstruction/figure13_digitised.json", "results/harmonisation/occp_group_shares.csv",
              "results/harmonisation/occp_group_jumps_by_group.csv", "docs/harmonisation_provenance.md",
              "prereg/OUTPUT_CHECKLIST.md", *[f"results/data_provenance/acsincome_{y}.json" for y in range(2014, 2019)]):
        need((ROOT / f).exists(), f"missing file {f}")
    import data as D
    for y in range(2014, 2019):              # derived tables: build provenance current (QA 3, R3-2)
        try:
            D.assert_derived_current(y)
        except Exception as e:                             # noqa: BLE001
            problems.append(f"derived table {y}: {e}")
        dp = ROOT / "results" / "data_provenance" / f"acsincome_{y}.json"
        if dp.exists():
            m = json.loads(dp.read_text())
            need(m.get("build_spec_sha256") == D.build_spec_sha(), f"data provenance {y}: other build specification")
            need(m.get("sha256_parquet") == D._sha256(ROOT / "data" / "derived" / f"acsincome_{y}.parquet"),
                 f"data provenance {y}: table differs from its build record")
    h = load("results/harmonisation/report_2014_2018.json")
    if h:
        need(h["occp_crosswalk"].get("destination_group_matches_crosswalk") is True, "harmonisation: destination check")
    man = load("results/models_manifest.json")
    if man is not None:
        need(set(man) == set(expected_specs()), "manifest: exact model inventory")
        check_models_inference_only(man)
    mg = load("results/stage_a/margins.json")
    if mg:
        fresh("margins.json", mg.get("provenance"), current)
        need(len(mg.get("states", [])) == N_STATES, "margins: 20 source states")
        for wt in WT:
            for k in ("delta", "epsilon", "epsilon_eo", "G", "G_by_source_state", "baseline_mean",
                      "post_dp_per_seed_by_year"):
                need(k in mg.get(wt, {}), f"margins[{wt}].{k}")
            need(all(np.isfinite(mg.get(wt, {}).get("delta", {}).get(m, np.nan)) for m in METRICS),
                 f"margins[{wt}].delta: finite for all metrics")
            need(all(np.isfinite(mg.get(wt, {}).get("G", {}).get(m, np.nan)) for m in ("dp_race", "accuracy")),
                 f"margins[{wt}].G: finite for the C7 yardsticks")
    est = load("results/stage_a/estimates_2014_2018.json")
    if est:
        fresh("estimates_2014_2018.json", est.get("_provenance"), current)
        for s in range(5):
            for y in range(2014, 2019):
                for wt in WT:
                    for fam in ("gbm", "post_dp_race", "post_dp_sex", "peryear_gbm", "norace_gbm", "norace_post_dp_sex"):
                        need(f"{fam}_s{s}|{y}|{wt}" in est, f"stored estimate {fam}_s{s}|{y}|{wt}")
    geo = load("results/stage_a/geographic_pairs_2014.csv")
    if geo is not None:
        c = geo.groupby(["weighting", "metric"]).size()
        need(len(c) == 10 and (c == N_STATES * (N_STATES - 1)).all(), "geographic pairs: 380 per metric/weighting")
    rc = load("results/stage_a/recoding_check.json")
    if rc:
        fresh("recoding_check.json", rc.get("_provenance"), current)
    dec = load("results/stage_a/decomposition_2018_check.json")
    if dec:
        fresh("decomposition_2018_check.json", dec.get("provenance"), current)
        need(all("diagnostics" in d and "reliable" in d and "balance_by_group" in d["diagnostics"]
                 for d in dec["results"]), "decomposition check diagnostics")
    val = load("results/validation/inference_validation.json")
    if val:
        fresh("inference_validation.json", val.get("provenance"), current)
        need(val.get("complete_run") is True, "inference validation: must come from one complete run")
        need(abs(val.get("alpha_per_test", 0) - ALPHA) < 1e-12, "inference validation: alpha equals family alpha")
        check_validation(val)
    sv = load("results/validation/split_variance.json")
    if sv:
        fresh("split_variance.json", sv.get("provenance"), current)
        need(sv.get("calibration_failures") == [], f"split-variance calibration failures: {sv.get('calibration_failures')}")
        need(len(sv.get("configurations", {})) == 15, "split-variance calibration: 15 configurations")
        need(all(np.isfinite(sv.get("multipliers", {}).get(wt, {}).get(m, np.nan)) for wt in WT for m in METRICS),
             "split-variance multipliers")
    from pipeline import sha256_file
    it = load("results/validation/integrity_tests.json")
    if it:
        need(all("NOT " not in str(v) for k, v in it.items() if not k.startswith("_")), "integrity tests all detected")
        need(it.get("_script_sha256") == sha256_file(ROOT / "scripts" / "test_integrity.py"),
             "integrity tests: produced by another version of the test script")
    for f, script in (("fetch_tests.json", "test_fetch.sh"), ("analysis_tests.json", "test_analysis.py"),
                      ("spec_tests.json", "test_specs.py"), ("archive_tests.json", "test_archive.py")):
        r = load(f"results/validation/{f}")
        if r:
            need(r.get("all_passed") is True, f"{f}: not all passed")
            need(r.get("script_sha256") == sha256_file(ROOT / "scripts" / script),
                 f"{f}: produced by another version of {script}")


def stage_b(current):
    from pipeline import expected_specs, prediction_years, verify_inventory
    try:
        verify_inventory([2014, 2018, 2019, 2021, 2022, 2023, 2024], write_record=False)
    except Exception as e:                                 # noqa: BLE001
        problems.append(f"inventory check now: {str(e)[:300]}")
    c = load("results/stage_b/confirmatory.json")
    if c:
        fresh("confirmatory.json", c.get("provenance"), current)
        need(c.get("family") == FAMILY, "confirmatory family")
        for wt in WT:
            r = c.get(wt, {})
            for k in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"):
                need(k in r and ("decision" in r[k] or "smaller" in r[k]), f"{wt}: {k} reported")
            for k in ("C1", "C2", "C3", "C4", "C5", "C6"):
                nc = r.get(k, {}).get("decision") == "not computable"
                need(nc or "margin_curve" in r.get(k, {}), f"{wt}: {k} margin curve")
            for k in ("C3", "C4"):
                nc = r.get(k, {}).get("decision") == "not computable"
                need(nc or "per_seed_level" in r.get(k, {}), f"{wt}: per-seed {k}")
        need("weighting_sensitive" in c, "weighting sensitivity list")
    t = load("results/stage_b/trajectories.csv")
    man = json.loads((ROOT / "results" / "models_manifest.json").read_text())
    years = (2014, 2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
    if t is not None:
        expect = sum(len(prediction_years(n, man, years)) for n in man if not n.startswith("state")) * 2 * 2 * 5
        need(len(t) == expect, f"trajectories: {len(t)} rows, expected {expect}")
    s = load("results/stage_b/secondary.json")
    if s:
        fresh("secondary.json", s.get("provenance"), current)
        for k in ("thresholds", "8.2_other_interventions", "8.4_decomposition", "8.6_per_year_scaling",
                  "8.8_state_post_processing", "8.9_deployment_2018", "8.10_without_race", "8.5_P1",
                  "8.5_P1_without_birthplace"):
            need(k in s, f"secondary: {k}")
        need(all("reliable" in d for d in s.get("8.4_decomposition", [])), "secondary 8.4: reliability")
        dep = s.get("8.9_deployment_2018", {})
        need(all("change_from_2018" in dep.get(f, {}).get("2024", {}).get("accuracy", {})
                 for f in ("y2018_gbm", "y2018_post_dp_race", "y2018_post_dp_sex")), "secondary 8.9: changes")
    lab = load("results/stage_b/secondary_labels.csv")
    if t is not None and lab is not None:          # the same estimate must agree across output tables (A3)
        a = t[(t.model == "gbm_s0") & (t.year == 2014) & (t.rule == ">") & (t.weighting == "unweighted")]
        b = lab[(lab.model == "gbm_s0") & (lab.year == 2014) & (lab.label == "nominal")]
        mm = a.merge(b, on="metric", suffixes=("_t", "_s"))
        need(len(mm) == 5 and np.allclose(mm.value_t, mm.value_s, equal_nan=True)
             and np.allclose(mm.se_t, mm.se_s, equal_nan=True), "gbm_s0 2014 estimate differs between output tables")


if __name__ == "__main__":
    from pipeline import provenance
    current = provenance("check_outputs.py")
    which = sys.argv[1] if len(sys.argv) > 1 else "stage_a"
    {"stage_a": stage_a, "stage_b": stage_b}[which](current)
    if problems:
        print(f"{which}: {len(problems)} problems:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print(f"{which}: all promised outputs present, current and passing their acceptance criteria")
