# Pre-registration → output checklist

Enforced by `scripts/check_outputs.py stage_a|stage_b` (exits non-zero on any missing item).

## Stage A (before archiving; 2014–2018 only)

| Plan section | Output | File |
|---|---|---|
| 3 | Harmonisation report; destination set equals the crosswalk-derived set; group-wise 2018 deviations | `results/harmonisation/report_2014_2018.json`, `occp_group_shares.csv`, `occp_group_jumps_by_group.csv` |
| 3 | Mapping provenance | `docs/harmonisation_provenance.md` |
| 4 | Exact model inventory (98 models) with hashes and fit-specification hashes | `results/models_manifest.json` |
| 4, 10 | Inventory check passes now (re-run by the checker) and its record | `results/inventory_check.json` |
| 10 | Every result file below carries a provenance block matching the current manifest, prediction specification and code | (checked by `scripts/check_outputs.py`) |
| 6 | δ, ε, ε_EO, G, G by source state, baseline means, per-seed post-processed DP, 20 states | `results/stage_a/margins.json` |
| 6 | 380 ordered state pairs per metric and weighting | `results/stage_a/geographic_pairs_2014.csv` |
| 5, 7 | Stored 2014–2018 estimates with covariances (all US models) | `results/stage_a/estimates_2014_2018.json` |
| 7.1 | Split-variance calibration: 15 configurations, multipliers | `results/validation/split_variance.json` |
| 7.6 | Operating characteristics of C1–C6, C7 coverage, joint simulation, acceptance criteria passed | `results/validation/inference_validation.json` |
| 8.4 | Decomposition check 2014 → 2018 with diagnostics and reliability | `results/stage_a/decomposition_2018_check.json` |
| 8.7 | Raw versus harmonised, 2014–2018 | `results/stage_a/recoding_check.json` |
| 10 | Integrity tests (tampering, stale artifacts, person swap within a household, failing workers) | `results/validation/integrity_tests.json` |
| 10 | Estimator and decision-rule tests (synthetic) | `results/validation/analysis_tests.json` |
| 10 | Download integrity tests (synthetic) | `results/validation/fetch_tests.json` |
| 4, 10 | Specification-sensitivity and lineage tests | `results/validation/spec_tests.json` |
| 10 | Archive-verifier tests (synthetic git repositories, mocked Zenodo record; 24 cases) | `results/validation/archive_tests.json` |
| 4 | Inference-only model files: audit of every model for row-level arrays; export record with byte-identical 2014–2018 predictions (D033) | `results/validation/inference_only_export.json` |
| 10 | Frozen list of non-person reference inputs with SHA-256 | `results/reference_inputs.json` |
| 3 | Derived tables 2014–2018 with build provenance (raw-file hashes, build-code hash; byte-identical rebuild) | `results/data_provenance/acsincome_<year>.json` (committed and archived; the copy in `data/derived/` is checked on every load) |
| Reconstruction | 56-run inventory, comparison, figure, macros | `results/reconstruction/runs.jsonl`, `comparison.csv`, `paper/figures/reconstruction.pdf`, `paper/numbers_reconstruction.tex` |

## Archive (between the stages)

| Item | File |
|---|---|
| Archive package (the files of the archived commit: code, plan, results, docs, logs, paper; all frozen model files; non-person reference inputs) | `archive/package.zip` (`scripts/verify_archive.py build`) |
| Zenodo record and DOI, archived git commit, Software Heritage revision ID of that commit and date of its manual check, SHA-256, MD5 and size of the package | `prereg/ARCHIVE_RECEIPT.json` |
| Guard flag, created by `scripts/verify_archive.py verify --create-flag` only after the package members, local copies, Zenodo record and Software Heritage check are verified | `prereg/ARCHIVED` |

## Stage B (after archiving)

| Plan section | Output | File |
|---|---|---|
| 5, 7 | C1–C8, unweighted and weighted: estimates, intervals, decisions; per-seed diagnostics; margin curves (C1–C6); C7 raw changes; C8 per-state detail; weighting-sensitive list | `results/stage_b/confirmatory.json` |
| 8.1 | Trajectories, all US models, all years, `>` and `>=` | `results/stage_b/trajectories.csv` |
| 8.2, 8.4–8.6, 8.8–8.10 | Secondary analyses (P1 with and without place of birth) | `results/stage_b/secondary.json` |
| 7.1 | The same estimate agrees across output tables (gbm_s0, 2014) | (checked by `scripts/check_outputs.py`) |
| 8.3 | Label definitions | `results/stage_b/secondary_labels.csv` |
