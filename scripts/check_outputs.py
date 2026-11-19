"""Pre-registration-to-output checklist (QA 1, #16): every promised output exists and is complete.
The human-readable list is prereg/OUTPUT_CHECKLIST.md; this script enforces it.

  python scripts/check_outputs.py stage_a     # before archiving
  python scripts/check_outputs.py stage_b     # after the confirmatory and secondary runs
Exits non-zero and lists every missing item.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd

METRICS = ("accuracy", "dp_race", "eo_race", "dp_sex", "eo_sex")
WT = ("unweighted", "weighted")
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


def stage_a():
    from pipeline import N_STATES, expected_models
    from reconstruct import load_runs
    try:
        load_runs("all")
    except Exception as e:                                 # noqa: BLE001
        problems.append(f"reconstruction inventory: {e}")
    tex = (ROOT / "paper" / "numbers_reconstruction.tex")
    need(tex.exists() and "PreprocContrastShare" in tex.read_text(), "reconstruction macros (PreprocContrastShare)")
    load("results/reconstruction/comparison.csv")
    for f in ("figure4_digitised.json", "figure13_digitised.json"):
        load(f"results/reconstruction/{f}")
    h = load("results/harmonisation/report_2014_2018.json")
    if h:
        need(h["occp_crosswalk"].get("destination_group_matches_crosswalk") is True, "harmonisation: destination check")
    man = load("results/models_manifest.json")
    if man is not None:
        need(set(man) == set(expected_models()), "manifest: exact model inventory")
    inv = load("results/inventory_check.json")
    if inv:
        need(inv["problems"] == [] and set(inv["checked_years"]) >= {2014, 2015, 2016, 2017, 2018},
             "inventory check passed for 2014-2018")
    mg = load("results/stage_a/margins.json")
    if mg:
        need(len(mg.get("states", [])) == N_STATES, "margins: 20 source states")
        for wt in WT:
            for k in ("delta", "epsilon", "epsilon_eo", "G", "G_by_source_state", "baseline_mean",
                      "post_dp_per_seed_by_year"):
                need(k in mg.get(wt, {}), f"margins[{wt}].{k}")
            need(all(m in mg.get(wt, {}).get("delta", {}) for m in METRICS), f"margins[{wt}].delta: all metrics")
    est = load("results/stage_a/estimates_2014_2018.json")
    if est:
        for s in range(5):
            for y in range(2014, 2019):
                for wt in WT:
                    for fam in ("gbm", "post_dp_race", "post_dp_sex", "peryear_gbm"):
                        need(f"{fam}_s{s}|{y}|{wt}" in est, f"stored estimate {fam}_s{s}|{y}|{wt}")
    geo = load("results/stage_a/geographic_pairs_2014.csv")
    if geo is not None:
        c = geo.groupby(["weighting", "metric"]).size()
        need(len(c) == 10 and (c == N_STATES * (N_STATES - 1)).all(), "geographic pairs: 380 per metric/weighting")
    load("results/stage_a/recoding_check.json")
    dec = load("results/stage_a/decomposition_2018_check.json")
    if dec:
        need(all("diagnostics" in d and "reliable" in d for d in dec["results"]), "decomposition check diagnostics")
    val = load("results/validation/inference_validation.json")
    if val:
        for wt in WT:
            need("three_way" in val.get(wt, {}) and "C7" in val.get(wt, {}), f"inference validation [{wt}]")
    sv = load("results/validation/split_variance.json")
    if sv:
        need(all(m in sv.get(wt, {}) for wt in WT for m in METRICS), "split-variance multipliers")
    it = load("results/validation/integrity_tests.json")
    if it:
        need(not any("NOT DETECTED" in v for v in it.values()), "integrity tests all detected")


def stage_b():
    c = load("results/stage_b/confirmatory.json")
    if c:
        need(c.get("family") == ["C1", "C2", "C3", "C4", "C6", "C7"], "confirmatory family")
        for wt in WT:
            r = c.get(wt, {})
            for k in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"):
                need(k in r and ("decision" in r[k] or "smaller" in r[k]), f"{wt}: {k} reported")
            for k in ("C1", "C2", "C3", "C4", "C5", "C6"):
                need("margin_curve" in r.get(k, {}) or r.get(k, {}).get("decision") == "not computable",
                     f"{wt}: {k} margin curve")
            need("per_seed_level" in r.get("C3", {}) and "per_seed_level" in r.get("C4", {}), f"{wt}: per-seed C3/C4")
        need("weighting_sensitive" in c, "weighting sensitivity list")
    t = load("results/stage_b/trajectories.csv")
    if t is not None:
        need({2019, 2021, 2022, 2023, 2024} <= set(t["year"]), "trajectories: all later years")
        need(set(t["rule"]) == {">", ">="}, "trajectories: both label rules")
    s = load("results/stage_b/secondary.json")
    if s:
        for k in ("thresholds", "8.2_other_interventions", "8.4_decomposition", "8.6_per_year_scaling",
                  "8.8_state_post_processing", "8.9_deployment_2018", "8.5_P1"):
            need(k in s, f"secondary: {k}")
        need(all("reliable" in d for d in s.get("8.4_decomposition", [])), "secondary 8.4: reliability")
        dep = s.get("8.9_deployment_2018", {})
        need(all("change_from_2018" in dep.get(f, {}).get("2024", {}).get("accuracy", {})
                 for f in ("y2018_gbm", "y2018_post_dp_race", "y2018_post_dp_sex")), "secondary 8.9: changes")
    load("results/stage_b/secondary_labels.csv")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "stage_a"
    {"stage_a": stage_a, "stage_b": stage_b}[which]()
    if problems:
        print(f"{which}: {len(problems)} missing or incomplete outputs:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print(f"{which}: all promised outputs present")
