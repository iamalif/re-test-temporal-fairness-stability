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
    if prov.get("smoke"):
        problems.append(f"{rel}: produced in smoke mode")


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
              "prereg/OUTPUT_CHECKLIST.md"):
        need((ROOT / f).exists(), f"missing file {f}")
    h = load("results/harmonisation/report_2014_2018.json")
    if h:
        need(h["occp_crosswalk"].get("destination_group_matches_crosswalk") is True, "harmonisation: destination check")
    man = load("results/models_manifest.json")
    if man is not None:
        need(set(man) == set(expected_specs()), "manifest: exact model inventory")
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
        need(abs(val.get("alpha_per_test", 0) - ALPHA) < 1e-12, "inference validation: alpha equals family alpha")
        acc = val.get("acceptance_passed", {})
        need(len(acc) == 6 and all(acc.values()), f"inference validation acceptance: {acc}")
    sv = load("results/validation/split_variance.json")
    if sv:
        fresh("split_variance.json", sv.get("provenance"), current)
        need(all(np.isfinite(sv.get("multipliers", {}).get(wt, {}).get(m, np.nan)) for wt in WT for m in METRICS),
             "split-variance multipliers")
    it = load("results/validation/integrity_tests.json")
    if it:
        need(all("NOT " not in str(v) for k, v in it.items() if not k.startswith("_")), "integrity tests all detected")
    ft = load("results/validation/fetch_tests.json")
    if ft:
        need(ft.get("all_passed") is True, "download integrity tests")
    at = load("results/validation/analysis_tests.json")
    if at:
        need(at.get("all_passed") is True, "estimator and decision-rule tests")


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
