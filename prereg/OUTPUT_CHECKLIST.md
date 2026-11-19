# Pre-registration → output checklist

Enforced by `scripts/check_outputs.py stage_a|stage_b` (exits non-zero on any missing item).

## Stage A (before archiving; 2014–2018 only)

| Plan section | Output | File |
|---|---|---|
| 3 | Harmonisation report; destination set equals the crosswalk-derived set; group-wise 2018 deviations | `results/harmonisation/report_2014_2018.json`, `occp_group_shares.csv`, `occp_group_jumps_by_group.csv` |
| 3 | Mapping provenance | `docs/harmonisation_provenance.md` |
| 4 | Exact model inventory (88 models) with hashes and mapping fingerprints | `results/models_manifest.json` |
| 4, 10 | Inventory check passed for 2014–2018 | `results/inventory_check.json` |
| 6 | δ, ε, ε_EO, G, G by source state, baseline means, per-seed post-processed DP, 20 states | `results/stage_a/margins.json` |
| 6 | 380 ordered state pairs per metric and weighting | `results/stage_a/geographic_pairs_2014.csv` |
| 5, 7 | Stored 2014–2018 estimates with covariances (all US models) | `results/stage_a/estimates_2014_2018.json` |
| 7.1 | Split-variance multipliers | `results/validation/split_variance.json` |
| 7.6 | Operating characteristics of C1–C6 and C7 coverage | `results/validation/inference_validation.json` |
| 8.4 | Decomposition check 2014 → 2018 with diagnostics and reliability | `results/stage_a/decomposition_2018_check.json` |
| 8.7 | Raw versus harmonised, 2014–2018 | `results/stage_a/recoding_check.json` |
| 10 | Integrity tests (tampering, stale artifacts, failing workers) | `results/validation/integrity_tests.json` |
| Reconstruction | 56-run inventory, comparison, figure, macros | `results/reconstruction/runs.jsonl`, `comparison.csv`, `paper/figures/reconstruction.pdf`, `paper/numbers_reconstruction.tex` |

## Archive (between the stages)

| Item | File |
|---|---|
| Zenodo DOI, Software Heritage ID, SHA-256 of every deposited file | `prereg/ARCHIVE_RECEIPT.json` |
| Guard flag, created only after the receipt is verified | `prereg/ARCHIVED` |

## Stage B (after archiving)

| Plan section | Output | File |
|---|---|---|
| 5, 7 | C1–C8, unweighted and weighted: estimates, intervals, decisions; per-seed diagnostics; margin curves (C1–C6); C7 raw changes; C8 per-state detail; weighting-sensitive list | `results/stage_b/confirmatory.json` |
| 8.1 | Trajectories, all US models, all years, `>` and `>=` | `results/stage_b/trajectories.csv` |
| 8.2, 8.4–8.6, 8.8, 8.9 | Secondary analyses | `results/stage_b/secondary.json` |
| 8.3 | Label definitions | `results/stage_b/secondary_labels.csv` |
