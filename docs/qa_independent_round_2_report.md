# Independent critical QA — round 2

**Date:** 20 November 2026. **Recommendation: do not archive the current version.**

**Refit decision:** the corrected occupation mapping and expected-policy prediction convention are coherent on inspection. I found no demonstrated new error requiring a different ExpGrad estimator or hyperparameter choice. Before starting the long refit, close the provenance/preflight issues below and explicitly decide whether a race-feature sensitivity model is wanted. Most other findings are analysis-only and need not delay model fitting. Do not interpret this report as certification of the existing fitted artifacts.

Project: `/Users/alif/Base/Projects/re-test-temporal-fairness-stability/`. Inspected HEAD: `74e8f77db98477ce594e9ca9c5cf6e6d9fe82a28`; observations concern the files present during this review, not a guarantee that the working tree equals that commit. File references below are project-relative, with functions/sections as stable locations.

## Scope and restrictions

I started with `docs/progress_update_for_reviewer_2026-11-20.md`, followed the round-2 brief, and checked the earlier report and disposition. I inspected the revised plan, source, runners, validation scripts, output checks, mapping provenance and manuscript passages. I executed small synthetic checks using copied source outside the project and re-derived the occupation destination mapping from the local Census crosswalk/dictionaries. I inspected the explicitly historical/synthetic inference-validation output.

No project files were modified. No person records of any year were opened, no `data/derived/` contents were inspected, no later-year result artifacts were opened, and no models were fitted. I did not run the project's destructive tamper tests against its live artifacts. The plan's exposure paragraph again contains an already-recorded external result of unspecified years; I encountered that record, do not repeat it, and did not open its source. No new outcome-revealing literature was sought.

The progress note correctly warns that current Stage A results are stale relative to the planned refit. In this checkout, `results/validation/integrity_tests.json` and `results/validation/split_variance.json` were absent. Their claimed rehearsal success therefore cannot be independently confirmed from those requested files. `inference_validation.json` exists; its reported minima are discussed below. This review is not a fresh raw-data rebuild or a full replication of the validation simulation.

## Refit-relevant findings — read before the long run

### R1. Major — refit-relevant: model/prediction provenance still does not enforce the complete experiment

**Where:** `src/pipeline.py::{model_current,_save,_pred_valid,load_pred,code_fingerprint,verify_inventory}`; `scripts/stage_a.py::main`; `src/data.py::build_year`.

**Evidence:** `model_current` returns true for all raw-feature entries, or for harmonised entries whose mapping hash matches. It does not compare training-data bytes, row split, estimator settings, fitting implementation or library versions. A change to `N_TREES`, splitting logic, fitting data, or LFR settings can leave a model considered current. The fit runner skips such entries without first checking their model files. `code_fingerprint` is explicitly “recorded, not enforced”; `_pred_valid` omits it. Thus a prediction implementation change can leave old predictions reusable when model/data hashes are unchanged. Derived-data reuse verifies the parquet against its own metadata but does not bind it to the current raw inputs/build specification.

**Additional execution gap:** `load_pred` does not compare its sidecar's model hash with the current manifest. The main confirmatory runner has an inventory preflight, but `stage_b_secondary.py::main` and `check_decomposition_2018.py` do not perform equivalent preflight themselves. A standalone secondary run can consume a correctly checksummed prediction produced by a superseded model. The statement “before every analysis” is therefore too strong.

**Why it matters:** the new checks detect byte corruption substantially better than before, but do not fully prevent stale scientific artifacts. That distinction matters particularly when the pending run is intended to replace old harmonised models.

**Fix before refit:** define a fitting-specification fingerprint including training-data identity, split algorithm/seed, feature/mapping specification, hyperparameters and relevant implementation/environment identity. Record it with every fit and compare it on resume. Define and enforce a prediction implementation/convention version. Validate model bytes before treating a fit as complete; use the current manifest inside `load_pred`, or require an immutable verified run context. Add standalone preflight to every entry point that consumes predictions. Bind derived-data metadata to raw inputs and build specification.

**Refit impact:** these checks do not inherently require another expensive fit after the already-planned run. Adding them now makes the upcoming run auditable. If implementation changes are needed later, the fingerprints should identify exactly which fits/predictions need regeneration rather than forcing everything to rerun.

### R2. Major — refit-relevant: row identity identifies households, not people

**Where:** `src/pipeline.py::row_key`, `year_frame`; data-frame column selections used by prediction consumers.

**Evidence:** the key hashes `ST`, `SERIALNO` and row count. Members of a household share those fields. A synthetic two-person household with SPORDER 1 and 2 gives the same key after reversing the people. Full-file hashing does not detect reordering an evaluation frame in memory while the underlying file remains unchanged.

**Why it matters:** the advertised row-alignment check misses a realistic class of prediction/label misalignment. The existing reversed-frame tamper test generally reverses households too and therefore misses this case.

**Fix:** include SPORDER or another verified unique person key, retain it in all evaluation frames, assert uniqueness and test a permutation restricted to one household. Keep the full-data hash as an additional check.

**Refit impact:** no estimator refit should be needed for a pure identity-check correction. Prediction sidecars will need migration or regeneration. Make the convention final before the planned prediction phase.

### R3. Question — refit-relevant: later sex analyses still use a feature with an acknowledged race-measurement break

**Where:** `src/harmonise.py::HARMONISED_FEATURES`; preregistration §§3–5.

**Evidence:** RAC1P remains a predictor in all primary harmonised models. The protocol ends confirmatory race outcomes in 2019 because race measurement changes, but extends sex outcomes to 2024. A change in how a predictor is measured can change predictions and therefore sex disparities even when sex coding itself is comparable.

**Interpretation:** this is not proof that the sex estimand is invalid. A deployment study can intentionally measure the consequences of changing input measurement. It does mean the race caveat is not confined to race metrics, and a sex result cannot automatically be interpreted as change in substantive population fairness under unchanged measurement.

**Decision before refit:** either state explicitly that sex endpoint results include the effect of race-input measurement changes, or pre-specify a sensitivity using models fitted without RAC1P. If the latter, fit/freeze the chosen families before archive. A cheap base-model/sex-postprocessing sensitivity may suffice; there is no evidence here requiring an additional ExpGrad fit. Avoid dropping race from the primary pipeline solely on this reviewer's suggestion without considering fidelity and the estimand.

### R4. Minor/question — refit-relevant: crosswalk verification reproduces the fix but silently discards unresolved destinations

**Where:** `scripts/harmonisation_report.py::derive_destinations`; `src/harmonise.py::DESTINATION_GROUP`; `docs/harmonisation_provenance.md`.

**Verified:** executing the crosswalk parser on documentation reproduced exactly `{4610: HLS, 5620: TRN, 5800: CMM}`. This supports the correction of the five previously misassigned split codes.

**Remaining issue:** the parser records destinations without a PUMS prefix and then discards `None` before deciding whether a move is whole. In this run unresolved destinations were recorded for source codes 430, 3060, 3730 and 9520. This does not demonstrate that any of the three current whole moves is wrong, but the procedure is not a general proof of a whole-code mapping when destinations are unresolved.

**Fix:** reject a whole-move classification whenever any destination remains unresolved, unless an explicit full-code-to-PUMS crosswalk resolves it. Preserve an auditable exception list. The current three mappings need no change based on the evidence found here. Correct the provenance table's past-tense “all affected models were refitted” while the refit is pending.

## Analysis and reporting findings — no refit inherently required

### A1. Major — the blanket conditional error-control claim is still not established

**Where:** preregistration §§5–7; `stage_b_confirmatory.py::seed_mean_dev_from_baseline`; `scripts/validate_inference.py`.

The plan now defines B as a mean of population metrics, estimates B from historical samples, includes its sampling variance, and simultaneously conditions on margins/yardsticks selected from those same historical observations. Declaring calibration constants fixed does not by itself prove that an interval using the unconditional historical-baseline variance has the advertised coverage conditional on the selected constants. Historical model/setting selection adds another conditioning issue. The validation script treats fixed margins and covariance as known and simulates normal changes; it does not regenerate historical samples, calibration and baseline estimation jointly or evaluate conditional coverage after calibration.

**Fix:** distinguish the following targets explicitly: (a) comparison with the observed historical reference, treated as fixed, versus (b) comparison with the unknown population-history reference. For (a), inference can be based on future-year sampling conditional on the fully frozen history, with an appropriately redefined target. For (b), justify the joint calibration/reference procedure and limit conditional guarantees accordingly. The same distinction affects C7's estimated 2014 reference. Do not claim exact finite-sample coverage from normal approximations with estimated SEs. The projection argument is sound if its marginal intervals are valid; it cannot establish those premises.

This is an unresolved inferential justification, not a demonstrated numerical failure of the actual final estimates.

### A2. Major — one model/year's split-variance ratio is extrapolated to every model, state and label without validation

**Where:** `scripts/check_split_variance.py`; `src/analysis.py::{split_multiplier,inflate}`; preregistration §7.1.

The check uses only `gbm_s0` evaluated on the full 2018 cohort. Its five metric-specific multipliers are then applied to all fitted-model families, all source-state test splits, 2014 and 2018 deployment years, and alternative-label analyses where used. The ratio of full-survey variance plus split variance to the average split estimator is not known to be universal across those settings. Ratios also have Monte Carlo error; flooring their point estimates at one does not establish a conservative bound. The original question about survey-plus-split variance has therefore received a useful diagnostic, not a general validation theorem.

**Fix:** either derive the needed two-stage variance procedure for the actual estimators, or validate transport of the chosen adjustment across representative models, state samples, years and label definitions, and describe it as empirical calibration. Store source model/data/specification hashes in the calibration result. Consider an analytic split-variance component instead of many expensive repeated weighted calculations if a valid derivation is available. Do not refit models merely to compute these diagnostics.

### A3. Major — the split multiplier is omitted from promised secondary estimates

**Where:** `scripts/stage_b_secondary.py::main`, §8.3 label loop and §8.6 per-year-scaling loop; `est_u`.

Those loops compute 2014 test-split SEs through `est_u` without `inflate`, whereas the main trajectory runner and §8.9 do apply it. Thus the same primary model/2014/nominal metric can have different reported SEs across outputs, contrary to the plan's “every training-year test-split estimate” rule.

**Fix:** centralise estimate construction with explicit training-year/split status and reuse it everywhere. Test that duplicate nominal estimates agree in value and SE across trajectory and secondary tables. Any deliberate exception must be stated before archive.

### A4. Major — decomposition balance diagnostics treat nominal category codes as meaningful numbers

**Where:** `scripts/stage_b_secondary.py::{max_smd,decompose}`; preregistration §8.4.

The SMD check operates on the numeric design matrix, including occupation-group indices, place-of-birth codes, marital status and other nominal categories. Matching means of arbitrary category numbers does not establish category balance. A synthetic example with source categories {1,3} and target {2,2} produces SMD zero despite disjoint categorical support. Tightening the threshold from 0.10 to 0.05 cannot fix this defect. Numeric mean checks can also miss important continuous distribution changes.

**Fix:** evaluate nominal balance with category indicators or distribution distances, retaining SMDs for genuinely quantitative features. Report per-group category imbalance and overlap/ESS; specify how poor overlap affects interpretation. Add label/EO-relevant diagnostics and clipping sensitivity if P2 is interpreted for EO, since the present clipping gate is accuracy-only. Reassess the historical reliability result after the diagnostic change and disclose that recalibration used allowed historical data. No frozen prediction-model refit is necessary.

### A5. Major — temporary downloads bypass the claimed integrity test

**Where:** `scripts/_fetch.sh::{valid_file,fetch}`.

`fetch` tests `dest.part`, but `valid_file` chooses format from the final filename suffix. A `.zip.part`, `.xlsx.part` or `.pdf.part` falls into the generic nonempty-file branch. I confirmed that a text file containing “not an archive” named `corrupt.zip.part` is accepted. It can be renamed to the final path and consumed before a subsequent invocation checks it. In addition, genuine legacy `.xls` files are tested with unzip, which is not a valid test for the binary XLS format.

**Fix:** pass the intended format/destination name separately, or remove `.part` before choosing the check; distinguish XLS from XLSX. Add synthetic corrupt ZIP/PDF/XLSX fixtures tested on the actual temporary path. This fix does not require downloading any person data.

### A6. Major — failure handling is neither metric-local nor consistently enforced

**Where:** `src/analysis.py::{unweighted,weighted,point,compare_stability}`; confirmatory `guarded` and trajectory loop; secondary runner; `check_outputs.py`.

All-metric constructors throw when any group-specific metric fails. I confirmed a dataset with a well-defined DP gap of 0.15 fails `unweighted` because Black EO has no positives. Calling `estimate` for C1 therefore can report C1 not computable because an unrelated EO metric fails. The unweighted and weighted estimates are constructed together, so weighted failure can suppress an otherwise computable unweighted estimate. The later trajectory and secondary loops do not uniformly catch `NotComputable`, so the process can still abort rather than produce the promised per-claim record.

Separately, C7 accepts non-finite yardsticks: with G_fair=NaN it returns D/CI=NaN and decision “inconclusive”, which is not an honest inconclusive statistical result. The checklist unconditionally requires C3/C4 per-seed fields even when a legitimate not-computable record exists.

**Fix:** carry metric-specific validity and reasons, isolate weighting failures, validate all C7 inputs, and represent failure consistently in every output. Test missing positives with computable DP, a zero replicate denominator, NaN G, and a valid not-computable C3/C4 record. The normal large-sample run may not encounter these cases, but the protocol explicitly promises this behavior.

### A7. Major — output validation can accept stale or incomplete evidence

**Where:** `scripts/check_outputs.py::{stage_a,stage_b}`; validation writers; `results/validation/`.

The checklist checks existence and selected keys, not that analysis/validation outputs were produced from the current model manifest, mappings, calibration constants and analysis code. It accepts any saved successful inventory record with the relevant years rather than re-verifying current files. Inference-validation alpha is not checked against the current family. Presence of C7 fields is checked, not a pre-specified validation acceptance criterion. Trajectories are checked for years/label rules but not the complete model×year×metric×weighting inventory. Several checklist promises, such as provenance documents and some harmonisation outputs, have no corresponding explicit existence check.

**Evidence availability:** this checkout contains inference-validation results but no `integrity_tests.json` or `split_variance.json`. The progress note says some evidence comes from a rehearsal elsewhere; that is not equivalent to evidence for the final production run. Current stored C7 minima are 0.99675 and 0.9975 for anticipated unweighted/weighted settings, and 0.99725/0.99525 for unweighted stress settings, at alpha=0.05/6. These are recorded Monte Carlo results under the simulation assumptions, not a validation of final refitted models.

**Fix:** every analysis/validation artifact should reference an immutable run manifest containing input hashes, code/specification version, family/alpha, and status. Have the archive gate recompute identity checks and validate full output inventories, finite values or explicit failures, and registered statistical acceptance criteria. Preserve rehearsal evidence separately. Do not reuse stale Stage A validation merely because its fields exist.

### A8. Minor — the stated alpha/2 bound for “violated” is false in general

**Where:** `src/analysis.py::three_way` docstring; preregistration §§6 and 7.2.

For a two-sided 1−alpha normal interval entirely outside a positive band, false violation can occur in either tail. At theta=0 with the band very small relative to SE, its probability approaches alpha, not alpha/2. A synthetic calculation with alpha=0.05/6, margin=0.00001 and SE=1 gives P(violated)≈0.00833309, greater than alpha/2≈0.00416667. Even at theta=margin, the opposite tail contributes a positive amount beyond alpha/2.

**Fix:** state the general bound as alpha (under valid interval assumptions). The “holds” one-sided-boundary argument can retain its appropriate conservative bound. The existing family allocation alpha=0.05/6 need not change merely because this stronger subclaim was wrong. Add this edge case to the validation, rather than claiming the implementation itself must be replaced.

### A9. Minor — validation and status wording still overstates what has been demonstrated

**Where:** `docs/qa_independent_1_disposition.md`; `docs/harmonisation_provenance.md`; preregistration §§2, 7.6, 10; manuscript introduction/design placeholder.

- The disposition header says no existing model needs refitting and its initial table retains the seven-test family, while the current progress update correctly says harmonised models will be refitted and the family has six tests. Preserve chronology but add an unmistakable current-status override.
- The provenance table says affected models “were refitted” while the run is pending.
- The manuscript's design section remains a TODO, so consistent narrowing of certificate/endpoint claims across the whole manuscript cannot yet be certified. Its introduction still centres on certificate validity; the final design must state clearly that C3/C4 do not certify fairness.
- The plan's exposure paragraph says the independent reviewer opened no later-year outcomes without acknowledging the already-recorded unknown-year statement encountered in the earlier review. Clarify that distinction without repeating the outcome.
- C5's “almost unreachable” rationale should distinguish weighted from unweighted operating characteristics and the family alpha from its new secondary alpha. The reported earlier unweighted zero-change hold probability of 0.31 is not literally near zero. `validate_inference.part1` still uses family alpha for C5; if intended as rationale for exclusion, label it as such and also report its actual secondary operating characteristics.
- The archive receipt is a written procedure; no receipt-verification implementation was identified in the inspected scripts. A documented human verification is acceptable if represented accurately; file existence alone is not proof of deposition.

**Fix:** reconcile these statements before archive, keep historical decisions dated, and distinguish mathematical justification, synthetic simulation, rehearsal, and final-run evidence.

## Disposition of every earlier finding

“Resolved” here means the specific methodological/code issue was addressed on inspection; it does not certify final post-refit outputs. Numbers refer to `docs/qa_independent_1_report.md`.

| Earlier # | Round-2 judgement | Evidence and remaining work |
|---|---|---|
| 1 — C8 binomial test | **Resolved** | `analysis.sign_count` and confirmatory C8 are descriptive; ties and state detail are retained. No binomial significance call remains in that path. |
| 2 — C7 percentile interval | **Partly resolved** | `compare_stability` correctly projects a Bonferroni box and floors G. Remaining conditional/normal coverage premises and non-finite input handling: A1/A6. |
| 3 — certification vs envelope | **Partly resolved** | Plan §5 and C3/C4 output correctly use seed-average historical envelopes and diagnostics. Manuscript design is unfinished and certificate framing persists: A9. |
| 4 — preprocessing attribution | **Resolved** | Manuscript now uses paired contrast and explicitly disclaims attribution to original code; corrected macros are referenced. No new reconstruction fit is needed for that arithmetic correction. |
| 5 — stale provenance | **Partly resolved** | Model/prediction byte hashes, sidecars and atomic writes improve integrity. Fitting/prediction spec enforcement and person identity remain incomplete: R1/R2. |
| 6 — worker failures/inventory | **Partly resolved** | `stage_a.main` accumulates worker failures and exits nonzero; `verify_inventory` checks expected model names. Standalone secondary preflight and final evidence freshness remain gaps: R1/A7. |
| 7 — clean rebuild/downloads | **Partly resolved** | Required directories and temporary writes added. Actual `.part` validation bypass and XLS handling remain: A5. Fresh rebuild not independently executed. |
| 8 — Puerto Rico optional | **Resolved** | `read_year_universe` now raises for either absent archive; `build_year` verifies exact registered geographies. |
| 9 — scope vs headline | **Partly resolved** | Plan gives explicit endpoint and reconstructed-extension scope and raw C7 changes. Manuscript design remains TODO; race-input caveat also affects sex interpretation: R3/A9. |
| 10 — calibration/power | **Partly resolved** | Targets, fixed-band language and operating-characteristic code added. Joint/conditional calibration validity is not established by fixed-normal simulation: A1. |
| 11 — decomposition | **Partly resolved** | Household-grouped folds, diagnostics, clipping sensitivity and P2 suppression are implemented. Nominal-code SMD can pass despite categorical imbalance: A4. |
| 12 — per-year-scaling mismatch | **Resolved in fitting/prediction code** | `fit_job(kind=peryear)` fits with full-year scaling; `Frozen.transform` applies full evaluation-year scaling. Dedicated families are included in the inventory. R1 still governs provenance; A3 concerns SEs, not these fits. |
| 13 — harmonisation bound | **Partly resolved** | Bound language removed, documented/analyst mappings separated, five-code bug corrected. Crosswalk reproduction supports current three moves; unresolved-destination logic remains: R4. |
| 14 — weighted split inference | **Partly resolved; evidence outstanding** | New diagnostic and inflation rule exist but no local output and no demonstrated universal transport: A2/A3. |
| 15 — randomised prediction target | **Resolved in metric/prediction algebra** | `_pmf_predict` supplies policy probabilities; `_correct` uses y*p+(1−y)*(1−p), and DP/EO use probability means. This addresses the original repeated-random-stream issue. Validate final probability artifacts after refit. |
| 16 — outputs/archive | **Partly resolved** | Margin curves and deployment changes implemented; written archive package expanded. Completeness/freshness gate and some SE/failure consistency remain: A3/A6/A7/A9. |
| 17 — novelty | **Partly resolved** | Manuscript narrows to “we did not identify” within a described search. Search appendix and other reading remain unfinished; no independent new literature certification in this round. |
| 18 — figure precision | **Resolved in wording** | Manuscript now says about four decimals and manual legend assignment. Earlier independent extraction agreement remains useful evidence. |
| 19 — numerical edge policy | **Partly resolved** | Grid boundary/tie and pooling behavior described; guards added. Metric-local failures, NaN C7, and consumer consistency remain: A6. |
| 20 — manuscript/protocol sync | **Partly resolved** | Most scope and universe corrections are present; stale disposition/refit statements and unfinished manuscript sections remain: A9. |

## Checks found sound

1. The expected-policy correctness formula is appropriate. Merely replacing boolean predictions with probabilities without changing accuracy would have been wrong; the implementation does change accuracy correctly.
2. C7's `z = norm.ppf(1−alpha/4)` gives two marginal two-sided intervals each with error alpha/2; their joint box has coverage at least 1−alpha if the marginal normal intervals are valid. `_abs_range` and the extremal D arithmetic correctly project the box. Correlation is not required for this union-bound construction.
3. The six-member family is consistent between the current plan, confirmatory runner and inference-validation alpha. C5 is separately evaluated at 0.05 in the confirmatory runner; C8 is descriptive.
4. The occupation correction mechanically matches the supplied Census crosswalk/dictionary interpretation for the three specified whole moves. I found no evidence warranting reversal of that correction.
5. New per-year models are trained and evaluated with a consistent scaling convention. Predictions are made on the full frame before selecting training-year test rows, which is necessary for their stated scaling rule.
6. Household-grouped cross-fitting is implemented in the domain classifier. Domain/sample prefixes prevent accidental household-ID collisions between years.
7. The decomposition residual is now explicitly labelled as conditional change plus approximation error, and P2 booleans are suppressed when its implemented reliability rule fails. The remaining issue is adequacy of that rule, not absence of suppression.
8. Required geography checks, explicit worker-error exits, model-byte validation in `load_model`, prediction-byte validation, and atomic model/prediction writes are real improvements. Their narrower guarantees should be retained while closing R1/R2.
9. The output now contains per-seed C3/C4 diagnostics, margin-decision grids, C7 raw changes, and §8.9 changes with SEs. No need to discard these additions because their validation gate is incomplete.
10. The revised manuscript separates the measured reconstruction preprocessing contrast from unexplained difference to the published curve. This resolves a material reporting error from round 1.

## Recommended sequence

**Before the long fit:** freeze and record the exact fit/prediction specifications; add the missing provenance enforcement and person-level row key; verify the three occupation overrides including unresolved-destination exclusions; decide R3's scope/sensitivity. Run cheap synthetic preflight checks. There is no confirmed reason in this review to alter ExpGrad hyperparameters or repeat the original reconstruction fitting campaign.

**After fitting, before archive:** resolve A1/A2's inferential justification; apply SE conventions consistently; replace categorical-code balance diagnostics; fix download checks and numerical failure paths; regenerate all Stage A analyses and validation against the final immutable manifest. Confirm all 88 intended models and all required predictions are present and current. Treat old validation outputs as historical evidence only.

**Archive gate:** a complete, internally consistent plan with numeric placeholders filled; current model/data/prediction/analysis identities; independently checkable validation results; complete output inventories; explicit remaining limitations; actual deposited model bytes and verified receipt. The manuscript need not contain future results before archive, but its methodological claims and the archive's protocol must agree.

**Overall:** substantial progress, but the first review is not fully closed. The highest-value remaining work is enforcing artifact identity and making the inferential and diagnostic claims match what the code actually guarantees. Proceed toward the planned refit after the specific preflight decisions above; do not archive this version as-is.
