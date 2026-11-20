# Additional deep QA before the long refit

**Date:** 20 November 2026  
**Project:** `/Users/alif/Base/Projects/re-test-temporal-fairness-stability/`  
**Current commit reviewed:** `2e65809cd51ff182f6ad0fadaecb6e52d94c61ac`

## Refit-relevant conclusion

**Proceed with the planned allowed-year rebuild and refit. This additional pass found no confirmed blocking defect requiring a change to fitted models or predictions.** The evidence is stronger than in round 4: this pass executed all 43 fitting jobs and all 98 model variants on synthetic data, exercised the actual command-line workflow, and checked raw-data ingestion and artifact corruption cases.

This is not a guarantee of error-freeness. Small synthetic fits establish that the exercised paths work together; they do not establish full-data convergence, adequate resources, or passing final statistical calibration. The long run is still needed to establish those facts.

**The archive defect reported in round 4 is fixed in the current commit.** My early progress message carrying it forward was outdated. I inspected the newer changes and independently reran the updated nine-case archive suite; all cases passed, including the previously demonstrated failures.

No production fit was started. No project files were edited. No ACS person records for 2019 or later, or later-year empirical results, were accessed. All new person-shaped inputs were synthetic; no real person records were needed for this pass.

## Current findings and readiness conditions

### P5-1 — blocking before archive, not before refit: complete the real run and its validation

**Location:** `scripts/run_all.sh`, `scripts/check_outputs.py::stage_a`, `scripts/check_split_variance.py`, `scripts/validate_inference.py`, and the pre-registration's Stage A placeholders.

The full-data outputs remain to be generated and accepted. This is an outstanding execution requirement, not a new implementation defect. The synthetic results in this report must not be substituted for scientific outputs, final model files, split multipliers, or validation results.

**Action:** use the prescribed sequence: rebuild 2014–2018 with provenance, fit, predict, calibrate split variance, regenerate analysis and validation, then pass the current Stage A gate. Fill the plan's Stage A values from the accepted run before packaging. A failed calibration or validation criterion requires investigation; it must not be silently waived. There is no basis in this review to repeat an otherwise valid model fit just because a downstream analysis or archive check needs correction.

### P5-2 — non-blocking: C7 grid checking is still less exact than the other validation grids

**Location:** `scripts/check_outputs.py::check_validation`, C7 branch; `scripts/validate_inference.py::part2`.

The new gate now checks the exact three-way theta list and exact joint history/theta list, including multiplicity. I independently verified that replacing a registered cell with a duplicate is rejected for each of those two branches.

For C7, the gate requires the expected number of settings and at least 30 unique `(a, b)` pairs in each setting. It does not require the exact setting identities or reconstruct the complete registered coordinate set from that setting's covariance and geographic yardsticks. Consequently, “exact validation grids” is fully supported for the three-way/joint branches, but remains an overstatement for C7.

**Why non-blocking:** the current C7 generator constructs its grid directly from the stated quantities. I found no actual omission in that generator. This remains optional regression protection, not a reason to delay the refit or evidence that current scientific results are wrong.

**Optional action:** validate C7 setting labels and compare the coordinate set with the generator's expected grid. Keep this separate from model-fitting code.

### P5-3 — non-blocking; refit-relevant operational limitation: configuration invalidation remains broad

**Location:** `src/pipeline.py::semantic_config`, `fit_spec`, and `scripts/test_specs.py`.

The round-4 observation remains: a family-local semantic setting can invalidate unrelated model families because they share the configuration fingerprint. This safely favors recomputation; it does not accept stale models. Family-specific function hashing is implemented.

**Action:** leave this optimization for later. Do not change the fitting specification merely to avoid harmless over-invalidation immediately before the planned run.

No other new finding is promoted to blocking status by this pass.

## What was actually executed

The checks ran in an isolated copy under the review workspace, using the project's installed Python environment. The copied `src/*.py` files were compared with the current project source. They matched except for two deliberate fixture-only reductions: three boosting trees, and LFR optimization limits of eight iterations/fifteen function evaluations. These reductions were never applied to the project.

The synthetic model fixture contained 8,160 rows per year, all 51 registered geographies, household/person identifiers, raw feature codes, multiple sensitive groups and labels, and data for 2014–2018 only. Official occupation dictionaries were used to choose valid codes and exercise the real harmonization path. Synthetic derived files had their own build metadata and hashes.

### 1. All model families, saving, loading and prediction

**Result: passed.** All **43 jobs produced the expected 98 distinct model names**, covering:

- Five primary GBMs and their race/sex DP and EO post-processors.
- ExpGrad and LFR.
- The raw-code model.
- Twenty state-specific GBMs and their race-DP post-processors.
- Models trained on 2018.
- Per-year-scaling models.
- No-race models and their sex-DP post-processors.

Checks established that:

- Each job saved exactly the names declared by `job_names()`.
- Every saved model satisfied its expected fit specification and file hash.
- Predictions were finite and within `[0, 1]`.
- Stored float32 predictions agreed with direct predictions from reloaded models within `3e-8` absolute tolerance for the directly checked 2014/2018 predictions.
- Repeated predictions were identical for GBM, race-DP post-processing, ExpGrad and LFR.
- A never-seen race category was handled without failure by race-DP and race-EO post-processing through the specified pooling path.
- National, state-specific and 2018-training scalers used the correct training rows.
- The strict income-label boundary behaved as specified: 49,999 and 50,000 were negative; 50,001 was positive.

GBM, ExpGrad and LFR were also refitted with the same synthetic inputs/settings; their predictions were exactly equal to the corresponding earlier predictions. This is an observed reproducibility result for this fixture, not a claim of universal bitwise reproducibility across machines or library versions.

### 2. Actual command-line orchestration and resumption

**Result: passed.** The copied `scripts/stage_a.py` was executed as a command, rather than only invoking its helpers:

- `fit --jobs 2` recognized the complete current synthetic inventory and reported **zero fitting jobs**.
- `predict --jobs 2` produced/reused the required predictions for all five allowed years and passed the final inventory check.
- Two fit specifications were deliberately marked stale in the synthetic manifest. Parallel fitting reran the two corresponding jobs and successfully saved their three models: a state GBM/post-processing pair and a per-year GBM.
- An unsupported-year prediction job exited with status **1**, demonstrating worker failure propagation rather than a successful exit after an error.
- After deliberate repeat fits, verification rejected predictions whose recorded model hashes no longer matched the newly serialized artifacts. Running the prediction command again refreshed those artifacts and passed the full inventory check.

That last rejection is correct behavior: equality of predictions does not imply equality of serialized model bytes. The workflow correctly binds stored predictions to the actual frozen file.

### 3. Tampering, alignment and invalid artifacts

**Result: all 11 checks passed.** The isolated fixture covered:

- Altered model bytes rejected by model loading and inventory verification.
- Truncated prediction arrays rejected by prediction loading and inventory verification.
- A stale model hash in prediction metadata rejected.
- Swapping two people within the same household rejected.
- Duplicate person identities rejected.
- Restored artifacts passing the complete five-year inventory.
- The three repeat-fit prediction comparisons described above.

The initial model fixture additionally rejected reversed row order and verified that valid prediction files were reused without rewriting them.

### 4. Raw-data builder, boundaries and provenance

**Result: all 12 checks passed.** A separate synthetic ZIP/CSV fixture exercised the real builder. It supplied lower-case column names, all required replicate weights, both US and Puerto Rico archives, and deliberately included records on the filter boundaries.

Verified behavior:

- DC was excluded; the 50 states and Puerto Rico were retained.
- The age, income, hours and person-weight filter boundaries selected exactly the expected rows.
- Household serial numbers retained their leading zeroes.
- Lower-case replicate-weight names normalized correctly and their derived values used the intended integer type.
- Fresh build metadata was accepted.
- An unchanged rebuild was content-identical and byte-identical in this fixture.
- Removing build provenance caused rejection.
- Removing the required Puerto Rico archive caused rejection.
- Guard-only calls refused each supported later year without an archive flag. These calls did not create, inspect or open any later-year person file.

The small builder fixture proves these exercised boundary cases. It does not independently establish the claimed byte identity of all five full production tables; the real rebuild records must supply that evidence.

### 5. Current round-4 fixes

**Archive verification: nine tests passed.** The updated verifier shares an inventory policy between building and verifying the package and compares every inventoried local file's bytes, including shell scripts. Independent execution confirmed rejection of changed local Python source, changed shell source and an omitted packaged shell script, in addition to the six earlier cases. A complete unchanged fixture passed.

**Validation grid checks: three tests passed.** A complete synthetic coordinate fixture passed; duplicate-substitution fixtures failed in the three-way and joint branches. The remaining C7 qualification is P5-2 above.

**Simulation wording: corrected.** The current plan and `validate_inference.part3` describe the annual-SE construction as a proxy, distinguish it from the runner's per-seed combined SE, and explicitly avoid claiming a proof of conservatism. This resolves the round-4 wording concern without requiring a different fit.

## Scientific and operational review notes

The source review followed the path from allowed-year reading through harmonization, design matrices, training splits, scalers, family fitting, category pooling, serialization, expected predictions, row identity and cache validation. It also traced the training-year test masks into Stage A evaluation and checked the ordering of calibration and analysis steps.

No additional confirmed train/test mixing, misnamed model artifact, prediction-row misalignment, randomized prediction draw, or model-inventory omission emerged from that review and the fixtures. Per-year scaling deliberately uses each year's full feature population, as specified in the secondary analysis; this was not mistaken for leakage in the primary frozen-scaler specification.

The test data are intentionally small and artificial. Full optimization convergence, rare real-world distributions, numerical behavior with 100 trees, memory pressure with six concurrent production workers, and final inferential acceptance are outside what these tests establish. No expensive production run was initiated to investigate those properties. Optional-package warnings concerned unused AIF360 methods; the required LFR path itself executed successfully.

The final checked project source/documentation paths were clean in Git. The review wrote only to its own workspace.

## Recommendation to the implementing AI

**Start the planned refit workflow; no additional fitting-method change is justified by this pass.** Keep the current registered settings fixed and let the existing failure checks stop the run if a real issue appears. Preserve the rebuild metadata, model manifest and run logs.

After fitting, regenerate predictions and complete all registered calibration/validation steps. **Archive only after those current full-data checks pass and the plan is finalized.** The corrected archive verifier is now supported by independent synthetic tests. Keep later-year person data unopened until the archive requirement is satisfied.

This report supersedes the round-4 report's open archive-code blocker for commit `2e65809`. It does not supersede the requirement for successful final empirical validation.
