# Disposition of independent QA 1 (report: `docs/qa_independent_1_report.md`)

Date: 2026-11-19. Status: all findings accepted or under evidence-gathering; archiving blocked until every row is closed.
No finding requires refitting ExpGrad or any existing frozen model. One new cheap model family is added before archiving (#12).
No 2019+ data has been opened; all validation below uses synthetic data or 2014–2018.

| # | Severity | Disposition | Exact change | Models / estimands change? | Validation | Blocker until |
|---|---|---|---|---|---|---|
| 1 | critical | **Accepted** | C8 removed from the confirmatory family; reported descriptively (count of states, ties reported, per-state intervals). Family = C1–C7, Bonferroni α = 0.05/7. | Estimand family changes (pre-archive, allowed). No models. | None needed for a descriptive output. | prereg + runner edited |
| 2 | major | **Accepted** | G (yardsticks) declared fixed historical calibration constants (conditional target, stated mathematically). Monte Carlo percentile interval replaced by a conservative projection bound: a simultaneous (1−α) Bonferroni box for the two changes, D bounded by its min/max over the box (exact for |·|). G floor 0.005 pre-specified. | Inference method changes. No models. | Synthetic coverage simulation incl. zero-change and equal-stability boundary (`scripts/validate_inference.py`). | simulation passes |
| 3 | major | **Accepted** | C3/C4 renamed "retention of the historical disparity envelope"; estimand stated as the seed-average signed gap of the five frozen post-processed models; per-seed gaps reported as diagnostics; no certification claim. | Wording/estimand definition only. | — | prereg + paper edited |
| 4 | major | **Accepted** | Macro changed to the paired contrast (per-year − common)/published = 29.5%; 35% kept only as "share not recovered by the common-scaler reconstruction"; "only" → "among the variants examined"; no causal attribution to the original code. | No. | Recomputed from saved aggregates. | macros regenerated |
| 5 | major | **Accepted** | Predictions carry a sidecar JSON (model sha256, data-file sha256, n, code fingerprint); loads verify it; models verified against the manifest hash on load; atomic writes; exact inventory check before Stage A analysis and Stage B. | No. Existing predictions re-derived (cheap). | Synthetic tamper tests (altered bytes, reordered rows, truncated file). | tests pass |
| 6 | major | **Accepted** | Workers collect errors and exit non-zero; exact inventory asserted (73+ models, 20 states, 380 ordered pairs per metric/weighting); completion record JSON. | No. | Deliberately failing synthetic worker. | tests pass |
| 7 | major | **Accepted** | All directories created; downloads to temp path, zip integrity test, atomic rename; CPI fallback separated from other failures; README no longer claims a verified one-command rebuild until checked. | No. | Stubbed fresh-checkout dry run. | dry run passes |
| 8 | major | **Accepted** | Missing `csv_ppr.zip` or wrong geography set is a hard error. | No. | Unit check. | — |
| 9 | major | **Accepted** | Claim-to-estimand table in prereg and paper; endpoint wording; raw changes reported beside normalised C7; race/sex horizon caveat. | Wording only. | — | prereg + paper |
| 10 | major | **Accepted** | Nulls and conditioning written mathematically (bands and reference conditional on the observed 2014–2018 data); decision-probability simulation over within-band / boundary / outside-band effects using the actual Stage A SEs; anticipated inconclusive rates reported in the prereg. | No. | `scripts/validate_inference.py` power section. | simulation done |
| 11 | major | **Accepted** | Household-grouped folds; overlap, weight-tail, ESS and group-specific balance diagnostics; clipping sensitivity (99%, 99.9%, none); residual renamed "conditional change plus approximation error"; P2 suppressed when reliability fails. | Secondary analysis only. | Re-run of the 2014→2018 check with diagnostics. | check re-run |
| 12 | major | **Accepted** | Fit and freeze, before archiving, a dedicated per-year-scaling model (harmonised features, scaler for each year fitted on that year's full eligible population, 2014 model trained on 2014 scaled by the 2014 full-year scaler), 5 seeds. Old §8.6 variant relabelled as a preprocessing perturbation. | New model family (GBM only, ≈10–20 min on the Mac). | Its 2014–2018 trajectory compared with the reconstruction. | models frozen |
| 13 | major | **Accepted** | "Bound" language removed; mapping provenance table (documented vs analyst assumption, incl. Cyprus); race/sex-specific occupation-share diagnostics; raw-vs-harmonised labelled a sensitivity contrast. | No. | Diagnostics on 2014–2018 documentation/data. | table written |
| 14 | question | **Needs evidence** | Weighted analysis stays a sensitivity analysis. Check on 2014–2018: spread of the weighted estimate across 50 random re-splits vs the replicate SE on one split; if the split adds variance, add it (pre-specified). Unweighted SEs described as household-cluster model-based, not full ACS design. | Possibly the SE formula for baseline years (pre-archive). | Re-split simulation on allowed years. | evidence in |
| 15 | question | **Accepted** | Target = expected performance of the randomised policy. Post-processed and ExpGrad predictions stored as positive-class probabilities; metrics computed from expected predictions (all metrics are linear in the prediction, so influence functions carry over). | Prediction convention changes; no refits. | Compare expected vs realised on 2014–2018. | predictions re-derived |
| 16 | major | **Accepted** | Prereg-to-output checklist (`prereg/OUTPUT_CHECKLIST.md`) enforced by a script; margin curves 0.005–0.03 implemented; §8.9 changes output; model bytes (135 MB) archived on Zenodo with the code; machine-readable archive receipt; `ARCHIVED` created only after the receipt verifies. | No. | Checklist script. | archive |
| 17 | major | **Accepted** | Novelty claims scoped to "we did not identify … in the search described"; no "first" claims; "most-cited" removed unless supported; citations verified. | Paper only. | — | before submission |
| 18 | minor | **Accepted** | "Recovered from vector graphics to about four decimal places"; legend mapping described as a manual assignment with visual verification; required-series assertion before macros. | No. | — | — |
| 19 | minor | **Accepted** | Pooling fallback, unseen categories, zero-denominator/non-finite policy, ties, base-rate grid bounds ($20k–$150k, boundary hit reported, lowest threshold on ties) written into the prereg; finiteness asserted before decisions. | No. | — | prereg |
| 20 | minor | **Accepted** | Manuscript, prereg header, docstrings and universe definition reconciled (2018-trained models; filters stated explicitly; loader as an enabling artifact). | No. | — | before archive |

## Status after implementation (20 Nov 2026, before the Stage A rerun)

All code changes above are implemented and were rehearsed end to end (decision log D024): full production code
paths on real 2014–2018 subsamples and synthetic stand-ins for later years, including integrity tests (all
tampering cases detected) and the output checklist. Additional changes found during the rehearsal are in D024
(balance threshold 0.05, P1 without place of birth, not-computable handling, inventory records).
Simulation results already available: the earlier C7 interval had minimum coverage 0.93 (target 0.992); the new
one ≥ 0.995, max P(wrong direction) 0.004. C5's P(holds | θ = 0) is 0.31 unweighted and 0.00 weighted.
Waiting for the Stage A rerun (Mac, 6–7 h): the refitted models, split-variance multipliers (#14), Stage A
calibration constants, the real-data decomposition check (#11), and the final operating characteristics (#10).
The plan's ⟨A⟩ values are filled from those files afterwards.
