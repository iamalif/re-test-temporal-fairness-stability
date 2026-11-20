# Independent critical QA — round 3

**Date:** 20 November 2026. **Archive recommendation: archive after the fixes and final-run verification listed below; do not archive the current artifacts.**

**Refit recommendation:** I found no demonstrated need to change the planned estimators, hyperparameters, occupation overrides, expected-policy prediction convention, or the 98-model design. Resolve the narrow specification and legacy-data provenance issues below before starting the long fit. Most remaining issues are analysis/validation/archive issues and do not require refitting ExpGrad.

Project: `/Users/alif/Base/Projects/re-test-temporal-fairness-stability/`. HEAD observed: `188ae0e108f3057a9d983ec5ff9838b60e7db116`. Findings concern inspected working files; this is not a claim that the working tree is identical to HEAD. Locations below are project-relative with function names.

## Scope and evidence

I began with the round-3 progress update and round-2 disposition, then followed the round-2 review brief with the requested substitution of dispositions. I inspected the revised model/prediction specifications, data-build checks, estimators, variance calibration, joint simulation, balance diagnostics, no-race analysis, freshness gate and archive verifier. I ran the current 12 estimator tests and download fixture tests in a separate copy. I also performed small synthetic checks of person identity, inventory and specification hashing.

No project file was modified. No person records of any year, derived-data contents, later-year results or outcome-revealing external sources were opened. No model fitting or production analysis was run. All test writes occurred in the separate review workspace. Final Stage A artifacts are explicitly stale pending the refit, so I do not treat rehearsal reports or old validation files as validation of the final experiment. This is a code/design review with targeted execution, not a full independent raw-data reconstruction.

## Refit-relevant findings

### R3-1. Major — refit-relevant: specification hashes omit some prediction/fitting dependencies

**Where:** `src/pipeline.py::{fit_spec,pred_spec_sha,_ast_hash,design,Frozen.sensitive}` and global configuration.

**Evidence:** the new specification hashes include much more than before, but an AST hash of a function records global-variable names, not the values or implementations of every dependency. For example, `Frozen.sensitive` uses `GROUPS`, which is absent from `pred_spec_sha`'s configuration. In a copied module, with documentation/library fingerprints held fixed, I changed `GROUPS['sex']` from `SEX` to `RAC1P`: `pred_spec_sha()` remained identical. That changes the sensitive values supplied to sex post-processing. Prediction feature selection also depends on `FEATURE_SETS`, which is not explicitly serialised into the prediction specification. The fit specification records the selected feature list, but its all-dependencies claim still needs an explicit inventory of referenced global constants and helper functions.

**Why it matters:** current values appear appropriate; this is not evidence that existing predictions used the wrong group. It is evidence that the promised invalidation guarantee is incomplete and could silently reuse predictions after a meaningful configuration edit.

**Fix before refit:** serialise the prediction feature sets, group-column mapping, relevant label/group constants and other semantic configuration directly. Audit the fit and prediction dependency lists, including helper implementations called by hashed functions. Add targeted tests that change one semantic constant at a time and verify the correct artifact class becomes stale. Keep this bounded: an explicit versioned specification is preferable to trying to invent a universal dependency tracker.

**Refit impact:** correcting metadata now should not require changing estimator settings. Establish the final specification before the planned fit so there is no later ambiguity about whether old models need migration or refitting.

### R3-2. Major — refit-relevant: legacy derived-data acceptance still lacks build provenance

**Where:** `src/data.py::{build_year,_logged_raw_hashes,build_spec_sha}`; `scripts/download_stage1.sh` raw-hash log generation.

**Evidence:** new-format metadata checks raw hashes and build-specification hash. The legacy branch instead verifies existing parquet against its own saved hash and compares currently present raw inputs with `logs/raw_sha256.txt`. It does not establish which build specification produced that parquet. The Stage A download script rewrites the raw-hash log, so agreement with that log need not establish agreement with the inputs used to produce an older parquet. The legacy loop also does not require both raw files before accepting the cached dataset. Finally, `build_spec_sha` hashes the reading/filtering functions but omits the `build_year` conversion/column-selection implementation that also affects the resulting table.

**Why it matters:** the pending fit would faithfully hash whichever training parquet it receives, but that does not prove the parquet implements today's registered build. This is the right moment to establish that chain once rather than discover it after a long fit.

**Fix before refit:** either rebuild the allowed 2014–2018 tables with the current builder, or make a documented one-time migration based on an independently established legacy build/input identity. Do not simply stamp current provenance onto old outputs. Preserve the old raw manifest rather than overwrite the sole historical evidence. Include the conversion/schema portion of the builder in its specification and require both registered raw inputs in the cache-validation path.

**Refit impact:** no new fitting method is required. If verification changes training-table content/order, the planned refit must use the corrected tables. I did not inspect the tables and therefore do not assert that their current contents are wrong.

## Analysis, validation and archive findings

### A3-1. Major — the archive verifier does not verify package contents

**Where:** `scripts/verify_archive.py::main`, `REQUIRED_IN_PACKAGE`.

**Evidence:** the verifier checks local archive-file hashes against the receipt and checks the remote Zenodo file listing/checksums. It then trusts `package_contents_sha256` from the receipt and compares those strings with current local files. It never opens the deposited archive to establish that the listed members actually occur inside it or have those hashes. A package missing the preregistration or containing different internal files can therefore pass if the receipt lists the intended local hashes. Required members also do not explicitly include the actual model bytes, source tree, all promised diagnostics and mapping resources. Missing local required files are not rejected in the `elif (ROOT / rel).exists()` branch. The Software Heritage identifier is copied to the flag without verification.

**Why it matters:** this script is the transition from blinded preparation to allowed later-year access. Its “archive verified” claim is stronger than what it checks.

**Fix:** inspect each local package member safely without extracting untrusted paths; verify actual member hashes and the complete required inventory, including every model file against the model manifest. Because the outer package hash matches the public record, checking those actual local package bytes establishes the content link. Require all expected local reference files or explicitly verify them solely from package bytes. Check archive publication/DOI identity and Software Heritage receipt as promised, or distinguish those as documented manual checks. Add an offline mocked-record test with an archive that deliberately omits a required member; it must fail even when the receipt claims that member exists.

**Refit impact:** none.

### A3-2. Major — result freshness does not cover upstream analysis inputs

**Where:** `src/pipeline.py::{provenance,code_sha}`; `scripts/check_outputs.py::fresh`; consumers of `split_variance.json`, `margins.json`, stored estimates, CPI/documentation inputs.

**Evidence:** result provenance binds the model manifest, prediction specification, producing source and selected script code. It does not generally include the hashes of consumed result files or external analytical inputs. For example, regenerate the split-variance calibration with a changed calibration script: the model manifest and prediction spec remain unchanged, and `stage_a_analysis.py` plus `src/*.py` may be unchanged. Old stored estimates/margins can still pass their own freshness comparison although they used old multipliers. The new calibration can pass its own current-code check at the same time. Similarly, validation consumes stored estimates and margins but does not fingerprint their bytes. CSV outputs do not all have equivalent independently checked provenance. Synthetic-test success files are checked for success flags without linking them to the current test implementation.

**Fix:** provenance needs a direct-input map, not just the producing code: path/artifact ID and hash for each consumed upstream output, calibration file, price-index file and relevant mapping resource. Validate the dependency graph recursively or freeze a complete run manifest with those identities. Include test-script identities in test evidence. Add a regression test that changes only an upstream multiplier file and verifies that dependent Stage A estimates and inference validation become stale.

**Refit impact:** none; rerun the affected analysis stages in dependency order.

### A3-3. Major — joint simulation supports an unconditional diagnostic, not the remaining conditional guarantee

**Where:** `scripts/validate_inference.py::part3`; preregistration §§5–7; `src/analysis.py` inference description.

**Evidence:** `part3` redraws historical estimates, recalibrates the margin and redraws the new estimate. It computes `mean(holds & true_outside_realised_band)` and the analogous false-violation frequency. These are joint, unconditional frequencies across random historical calibrations. They are not conditional error rates given the realised historical constants, nor rates conditional on the random null being true. The plan still says the tests/estimands are conditional on calibration constants. The simulation uses seed-0 per-year SEs as a stand-in for the implemented seed-mean procedure, only flat/observed histories and a positive theta grid. It is useful evidence, but does not validate every aspect of the final procedure or establish a uniform guarantee.

**Fix:** choose and state the claim precisely. If the target is a population-history comparison with empirical operating-characteristic checks, describe the joint simulation as such and remove unsupported conditional guarantees. If conditional control is essential, justify or validate that stronger property explicitly. Report null-conditioned rates as an additional diagnostic with denominators/Monte Carlo uncertainty; do not confuse them with the unconditional intersection rates currently tested. Simulate the actual seed-mean covariance/SE convention or explain why the stand-in is conservative for the tested claim. Add negative deviations and stress histories where useful. Do not redesign the frozen models to fix this inference issue.

**Qualification of this review:** a random-band, unconditional procedure can be defensible. I am not claiming that the present procedure necessarily exceeds its unconditional error budget. The problem is the mismatch between the scope of the evidence and the remaining conditional language.

### A3-4. Major — partial validation reruns can relabel old sections as current

**Where:** `scripts/validate_inference.py::main`; `scripts/check_outputs.py` validation acceptance checks.

**Evidence:** the validation script loads an existing JSON, updates selected parts according to `which`, and writes one fresh provenance block over the combined result. A `part3` run after changed inputs/code can retain old C7 and part1 results while making the whole file appear current. Some acceptance expressions also use `all(...)` on potentially empty collections, which is true; the checker tests the six acceptance flags rather than independently establishing complete expected case inventories.

**Fix:** either require a complete clean validation run for archive or attach and enforce per-part input/code identities. Reject missing/empty case grids. Recompute acceptance from the detailed current results in the gate rather than trusting only summary booleans. Partial reruns are useful during development but must not certify stale sections.

**Refit impact:** none.

### A3-5. Major — low overlap can make the decomposition balance gate easier to pass

**Where:** `scripts/stage_b_secondary.py::balance/decompose`; preregistration §8.4.

**Evidence:** category-share indicators fix the earlier arbitrary-code-mean problem. However, the acceptance limit grows as `0.02 + 3*sqrt(1/ESS + 1/n_target)`. With ESS near one the allowance is approximately three, accepting very large imbalance. ESS/overlap are reported but have no independent rejection criterion in the reliability gate. Total variation is reported but not gated, and categories with pooled share below 1% do not enter the maximum-indicator criterion; many rare categories can collectively carry substantial shifted mass.

**Why it matters:** an imprecise, poorly supported counterfactual can receive a more permissive balance threshold and still be labelled reliable. Accuracy/EO clipping checks and two DP residual checks do not establish adequate support in all relevant regions. Tuning the gate so historical before/after examples fail/pass is not independent validation.

**Fix:** add explicit minimum group-specific ESS/support criteria or an upper bound on the allowed balance tolerance. State how substantial total-variation or aggregate rare-category imbalance affects interpretation. Test the gate on synthetic overlap failure, concentrated weights and shifts among rare categories, not only the observed historical success case. Retain the revised “conditional change plus approximation error” wording and P2 suppression.

**Refit impact:** none for the frozen prediction models; domain-classifier/diagnostic analyses may be rerun.

### A3-6. Minor — the split-variance upper bound is only approximate and missing cases can disappear

**Where:** `scripts/check_split_variance.py`, ratio construction and final multiplier aggregation.

The expanded 15 configurations and K=400 are meaningful improvements, and the protocol now appropriately calls this empirical calibration. But the chi-square upper bound assumes approximately normal split estimates. When some split values are missing, `nanvar` uses fewer observations while the bound still uses K−1 degrees of freedom. Configurations with no valid ratio are dropped; if none remain for a metric, `max([1.0] + [])` produces one. The gate checks that the resulting multipliers are finite, not whether there was adequate evidence to calibrate them. The phrase that Monte Carlo error makes the adjustment larger “not smaller” is too absolute: an upper confidence bound can miss, and the denominator/full variance are also estimated.

**Fix:** report valid split counts and use their degrees of freedom; require the pre-specified coverage of configurations or record a calibration failure. Do not silently substitute one for absent evidence. Describe the bound as approximate and conditional on the distributional assumptions. Keep the conservative empirical maximum but do not claim it proves universal variance coverage.

**Refit impact:** none.

### A3-7. Minor — specification changes can unnecessarily invalidate every expensive model

**Where:** `src/pipeline.py::fit_spec`, hashing the full `fit_job` dispatcher for every job.

Hashing the entire dispatcher means an implementation change confined to a cheap no-race or per-year branch can invalidate the ExpGrad fit specification as well. This is fail-safe, not a validity defect, but it conflicts with the practical goal of avoiding unnecessary six-hour reruns.

**Suggestion:** split job-specific fit implementations or version each fitting family separately, while retaining shared dependencies where scientifically necessary. This is optional engineering work; do not delay a correct run merely to optimise invalidation. Freeze current fitting code before the run if leaving the broad hash in place.

## Verification of round-2 dispositions

“Resolved” means the specific inspected defect is addressed in code/design; final-run evidence remains pending. The identifiers below match `qa_independent_round_2_report.md`.

| Round-2 ID | Verdict | Evidence / remaining qualification |
|---|---|---|
| R1 — full provenance | **Partly resolved** | Fit/prediction specs are enforced, model files checked on resume, standalone analysis preflights added. Remaining semantic globals, legacy-build evidence and upstream analysis inputs: R3-1/R3-2/A3-2. |
| R2 — person row identity | **Resolved** | ST+SERIALNO+SPORDER key; uniqueness check. Independently confirmed within-household reversal changes the key. |
| R3 — race input affects sex | **Resolved as scoped sensitivity** | Primary race feature retained with caveat; five no-race GBMs plus five sex-DP postprocessors in inventory; §8.10 uses their own historical calibration and secondary level. Removing race is sensitivity, not proof that all measurement effects disappear. |
| R4 — unresolved crosswalk destinations | **Resolved on code inspection** | Unresolved destinations excluded from whole-move classification; current three registered moves unchanged. No evidence here warrants different occupation features. |
| A1 — inference target | **Partly resolved** | Population baseline and approximate intervals are explicit; joint simulation added. Conditional language is stronger than the simulated unconditional diagnostic: A3-3. |
| A2 — split calibration transport | **Partly resolved** | More representative configurations, more splits, conservative empirical aggregation, explicit non-theorem language. Missing-case and bound qualifications remain: A3-6; final calibration not yet available. |
| A3 — estimate consistency | **Resolved in implementation** | Central `analysis.estimates` and secondary `est_u(split=...)` route split estimates through the same multiplier convention. Final cross-table agreement should be checked after rerun. |
| A4 — categorical balance | **Partly resolved** | Indicator shares and TVD replace numeric category means; clipping check covers accuracy and EO. Low-ESS/rare-category acceptance remains: A3-5. |
| A5 — temporary downloads | **Resolved for reported bug** | Intended destination format supplied for `.part` validation. Copied fixture suite passed. PDF header/EOF and XLS signature tests are lightweight format checks, not full parser validation. |
| A6 — metric-local failure | **Resolved for tested defects** | Missing EO positives no longer invalidate DP; weighted failures remain metric-local; C7 rejects NaNs. All 12 supplied estimator tests passed independently in the copied workspace. This does not certify every edge path. |
| A7 — freshness gate | **Partly resolved** | Current inventory is rechecked; source/spec identities compared; more output inventories checked. Direct input lineage and per-validation-part identity remain: A3-2/A3-4. |
| A8 — false-violation bound | **Resolved** | Bound changed to alpha and edge case passes synthetic test. Normal-approximation assumptions still apply. |
| A9 — wording/status/archive | **Partly resolved** | Current progress explicitly acknowledges stale artifacts and pending refit; target and exposure language improved. New archive verifier does not inspect package contents: A3-1. Final manuscript/receipt still require reconciliation after the run. |

## Checks found sound

- The copied estimator suite completed with all 12 tests passing, including expected-policy accuracy, DP formula, weighted accuracy, metric-local missingness, C7 non-finite refusal and the alpha-bound edge case.
- The copied download fixture suite rejected corrupt/truncated temporary archives and accepted its intended fixtures. This directly closes the `.part` suffix-dispatch error.
- A synthetic household-person permutation now changes the row key.
- With a synthetic 20-state list substituted for the data-dependent selection, the registered inventory produces **98 distinct names**, including **10 no-race names**. No records were loaded for this check.
- The no-race job uses the separate feature set and sex-sensitive postprocessing; its new §8.10 analysis derives margins from that model family's own history rather than borrowing primary-model margins.
- Probability-based predictions and expected-correctness algebra remain coherent. The earlier change to expected-policy evaluation has not reverted to boolean accuracy comparisons.
- The C7 box-projection construction and finite-input checks remain appropriate subject to valid marginal interval assumptions. No new C7 algorithm replacement is recommended.
- C8 remains descriptive. There is no reason to restore the rejected independent-binomial significance test.
- The category-indicator balance implementation is a genuine improvement; the remaining objection concerns the acceptance policy, not a return to arbitrary category-code means.
- The progress update correctly distinguishes current synthetic tests from stale empirical/production artifacts. Preserve that distinction in the archive gate and manuscript.

## Decisions before and after fitting

**Before fitting:** settle R3-1's semantic specification and R3-2's legacy training-table provenance. Confirm the exact 98 jobs and final code/environment identities. No new expensive model family is requested by this review. Broad fit-code hashing makes last-minute dispatcher edits costly, so freeze that implementation deliberately.

**After fitting, before archive:** regenerate calibration and analysis in dependency order; close direct-input freshness and partial-validation relabelling gaps; clarify unconditional versus conditional inference; strengthen the overlap failure rule; inspect actual archive members. Run the complete final validation, not a mixture of old sections bearing a new provenance stamp. Fill numerical placeholders only from that verified run.

**Final recommendation:** the work is materially closer to a defensible archive. Proceed with the planned refit once the two specific preflight issues are settled. Archive only after the remaining analysis and packaging checks are complete. The outstanding issues do not justify repeatedly changing the scientific model specification merely to satisfy a growing infrastructure checklist.
