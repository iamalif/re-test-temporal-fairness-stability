# Final independent pre-archive review

**Date:** 20 November 2026  
**Project:** `/Users/alif/Base/Projects/re-test-temporal-fairness-stability/`  
**Reviewed HEAD:** `e61295201422ffa8ac953c2f43feb8e8909e8665`  
**Stage A run commit:** `7d16f23`  
**Brief:** `docs/review_brief_pre_archive.md`

## Decision summary

The full Stage A evidence is now present, and **I independently reran `scripts/check_outputs.py stage_a` successfully** in an isolated project copy. The numerical calibration values, manifest hash, split-calibration results and decomposition summaries agree with the plan. The logged production fitting sequence contains 43 successful jobs producing all 98 distinct models, followed by successful predictions for all five allowed years. There are no source/script changes between the run commit and the reviewed HEAD.

**One correction is blocking before archive:** Section 7.6 conflates the maximum error rate for an individual error category with the probability of making either type of error. The latter maximum is **0.0094**, not **0.0055**. Correct the interpretation; this does **not** require refitting models, changing decisions or rerunning Stage A.

The remaining observations below are non-blocking. I found no additional confirmed defect requiring a change to the frozen models or their predictions.

## Findings

### PA-1 — major; blocking before archive: correct the combined-error interpretation in Section 7.6

**Location:** `prereg/PREREGISTRATION.md`, final paragraph of Section 7.6; `results/validation/inference_validation.json`, unweighted joint C1, observed-shape history, theta = −0.01; `scripts/validate_inference.py::part3`.

**Evidence:** the plan concludes:

> The largest per-test error of either kind, 0.0055, is below the per-test α of 0.0083.

The saved row has:

| Quantity | Value |
|---|---:|
| Unconditional false “holds” | 0.0055 |
| Unconditional false “violated” | 0.0039 |
| Null-outside denominator | 20,000 |
| Null-inside denominator | 20,000 |
| Mean realized margin | 0.01 |

At this boundary both null conditions apply: `abs(theta) >= margin` and `abs(theta) <= margin`. “Holds” and “violated” are mutually exclusive decisions, but both count as erroneous under the stated boundary conventions. Therefore the probability of **either error** in this cell is the sum, **0.0094**. Recomputing this sum across all stored joint-simulation cells gives the same maximum, with Monte Carlo SE approximately **0.0006823**.

The 0.0055 figure is correct as the largest *individual error-category rate*. It is not the largest combined per-test error probability. The maximum of two categories cannot be substituted for their union when describing overall error or invoking Bonferroni.

**What this does and does not establish:**

- The registered gate really did pass. For false “holds”, its nominal-bound three-SE threshold is approximately **0.0055331**, and 0.0055 is below it.
- The estimated 0.0094 combined rate is only about 1.6 Monte Carlo SE above 0.05/6. It is not, by itself, persuasive evidence that the procedure violates its nominal combined rate.
- Conversely, neither the largest single-category estimate nor the average over 60 boundary cells proves a per-cell error bound or family-wise control.
- The existing qualifications about unconditional operating characteristics, the annual-SE proxy and finite simulation settings are appropriate and should remain.

**Required correction:** replace the final reassurance with an accurate description of the category-specific and combined rates. For example:

> All prespecified validation criteria passed, including their Monte Carlo tolerances. The largest false-“holds” rate was 0.0055 (Monte Carlo SE 0.000523), above the nominal α/2 target but within its registered tolerance. The largest false-“violated” rate was 0.0050. Because both boundary null conditions include equality, the largest probability of either error was 0.0094 (Monte Carlo SE 0.000682). These finite-grid results are compatible with sampling variation around the targets; they do not establish a uniform or conditional error-control guarantee.

The boundary-cell mean of 0.0038225 may remain as a descriptive statistic, but should not be offered as validation of the worst cell. Also replace “Beyond the margin the largest rate is 0.0004” with the precise description of the calculation: **“Among grid points with |theta| > 0.01, the largest unconditional false-‘holds’ rate was 0.00035.”** The simulation has random margins and differing envelopes; “beyond the margin” is not interchangeable with “beyond the 0.01 floor.”

No new acceptance criterion or extra simulation is required to make this correction. Do not tune criteria or refit models in response to this wording issue.

### PA-2 — minor; non-blocking: the archive is not self-contained for non-person reference inputs

**Location:** `scripts/verify_archive.py::inventory`, `scripts/download_docs.sh`, `scripts/stage_b_secondary.py::cpi_annual`, `src/harmonise.py::dictionary_file`.

The shared package inventory includes source, plan, results, documentation, logs, paper files, lock/project files and all manifest-listed models. It does not include the actual `data/raw/dictionaries/` files or `data/raw/cpi/r-cpi-u-rs-allitems.xlsx`. The archive retains download instructions and the raw-input hash log, so these inputs are identified; their bytes must nevertheless be recovered separately on another machine. In particular, the plan identifies a dated CPI workbook used for inflation-anchored thresholds.

**Why non-blocking:** the inputs already exist locally, the current input-lineage checks pass, and the frozen hashes identify the intended versions. I found no current mismatch or ambiguity about the intended CPI series. This is a preservation/recovery limitation, not a demonstrated error in the pending analysis.

**Suggested improvement:** include these small, non-person reference inputs in the deposit, or explicitly document their external retrieval and checksum verification. Do not confuse this suggestion with a request to package or access later-year person data. If the inventory is extended, rerun the archive tests and build the final package afterward; no model refit is indicated.

### PA-3 — minor; non-blocking: P1 has a production-scale execution risk, not an unresolved scientific choice

**Location:** `scripts/stage_b_secondary.py::p1_auc`, `domain_probs`, and `main`; plan Section 8.5.

P1 runs 20 temporal and 380 ordered geographic comparisons, both with and without birthplace. Each comparison uses five domain-classifier folds: approximately **4,000 HistGradientBoosting fits**. The complete secondary JSON is written only after these calculations finish. The prior full-chain rehearsal skipped this expensive section; the decision log records a smaller P1 test.

I independently exercised both P1 variants on synthetic 2014/2018 stand-ins with three states. Each returned all three states and finite temporal/geographic AUCs. The code uses the specified household grouping and feature omission. This does not establish runtime or peak memory on the full production workload.

**Why non-blocking:** the scientific computation and comparison rule are specified, and a failure/retry does not require choosing a new estimator or seeing results before defining the analysis. The final gate requires both P1 outputs, so `--skip-p1` is not a valid completed deliverable.

**Suggested improvement:** preserve progress logs and consider deterministic checkpointing if operationally necessary. Keep the states, folds, seeds and comparisons fixed. A runtime problem should not become a reason to omit P1 after later-year results are seen.

### PA-4 — minor; non-blocking: update two stale descriptive details in the plan

**Location:** pre-registration Sections 2 and 4.

- The exposure record still says “three rounds” of independent review, while the introduction records five reviews and this is the final pre-archive review. It also says the reviewer opened no person records. In this final pass I used permitted 2014 columns to independently verify the minimum subgroup count, and the isolated output gate reads permitted training-year columns. No later-year person records were accessed. Update the historical wording to distinguish earlier reviews from this final pass.
- The model files total **126,749,100 bytes**, approximately **126.7 MB / 120.9 MiB**, rather than the plan's approximate 135 MB. The manifest and inventory, not that approximate size, determine what is frozen.

These are editorial corrections and do not change the design or execution.

## Plan-to-results audit

The following values were independently extracted or recalculated from the named allowed-year artifacts. Rounding in the plan is consistent unless explicitly discussed in PA-1 or PA-4.

| Item | Independent check |
|---|---|
| Model manifest | Exactly 98 entries; SHA-256 `e1c51845bbd43d67c6851ba8137a8c018bfd281903737d182366f2476450baac`, matching Section 4. |
| Derived populations | 2014: 1,587,856; 2015: 1,603,542; 2016: 1,618,060; 2017: 1,642,973; 2018: 1,664,500. Every build record reports content identity and matching previous/current parquet hashes. The gate independently validates current parquet hashes. |
| Temporal margins | All four disparity margins are 0.01 in both weightings. Raw deviations match the plan's rounded values: unweighted 0.0024/0.0044/0.0014/0.0034 and weighted 0.0034/0.0050/0.0042/0.0051, in DP-race/DP-sex/EO-race/EO-sex order. |
| DP envelopes | Race 0.01 in both weightings; sex 0.01175765 unweighted and 0.01855187 weighted. Race raw maxima 0.00386697 and 0.00454455. |
| Geographic yardsticks | DP-race/accuracy: 0.02876205/0.01539919 unweighted and 0.02637883/0.01212245 weighted. All 380 pairs are computable for every metric/weighting. |
| Split multipliers | In accuracy/DP-race/EO-race/DP-sex/EO-sex order: unweighted 1.176336/1.163110/1.245642/1.260349/1.214077; weighted 1.188972/1.307866/1.305512/1.203833/1.202876. All round as stated. |
| Split-calibration coverage | Fifteen configurations; **400 valid splits in every metric/weighting cell**, not merely the required 95%; no calibration failures. State codes 6/34/29 correspond to California/New Jersey/Missouri. |
| Minimum source-state subgroup | Independently recomputed on the allowed 2014 seed-0 test split: minimum Black, income-over-$50,000 count among the 20 source states is **20**, matching Section 7.5. |
| Anticipated SEs | All six rounded unweighted/weighted values in Section 7.6 match `anticipated_se`. |
| Probability of “holds” at zero | C5: 0.266283/0 at family alpha and 0.691550/0.277654 at 0.05. Weighted C6: 0.994681. Other listed values round as stated. |
| C7 coverage | Anticipated minimum 0.997375 in both weightings; stress minima 0.99675 and 0.99375. Old percentile minima 0.9425 and 0.9325. |
| Joint simulation | Maximum false holds 0.0055; maximum false violated 0.0050; mean over 60 ±0.01 boundary cells 0.0038225; maximum false holds at grid points with absolute theta above 0.01 is 0.00035. Combined-error interpretation requires PA-1. |
| Decomposition | All three label definitions reliable. AUC 0.549138; DP residuals −0.00197509 and −0.00230049. Accuracy composition −0.004147996; residuals −0.01365643 nominal, −0.00815748 inflation, −0.00108869 base-rate. |
| Decomposition diagnostics | Before-reweighting group balance 0.039256–0.045677; after 0.009810–0.023078; limits approximately 0.0266–0.0392. Group ESS fractions 0.974672–0.977725. Largest categorical TVD 0.027778, corresponding limit 0.070329. Maximum recorded clipping sensitivity 0.000018204, below 0.0001. |
| Harmonization diagnostics | Report/log support rounded maximum jump 0.0051 overall and 0.0056 across groups. |
| Numerical placeholders | No `⟨A⟩` placeholders remain in the plan. |
| Software versions | Manifest versions agree with the listed NumPy, pandas, SciPy, scikit-learn, Fairlearn and AIF360 versions. |

The reconstruction-specific historical claims were not newly reproduced by refitting or redigitizing figures in this review. The output gate successfully checked the reconstruction inventory and required outputs; this is narrower than a fresh reconstruction study.

## Run completeness and output freshness

I copied code and the relevant Stage A/result directories into the review workspace and linked only explicitly selected allowed-year data/model/prediction artifacts and non-person reference inputs. The command was run there using the project's Python environment, with bytecode writing disabled.

**Independent command outcome:**

`stage_a: all promised outputs present, current and passing their acceptance criteria`

This verifies current model/prediction inventory and hashes, current fit specifications, derived-table provenance, recorded upstream inputs, producing-code fingerprints, calibration acceptance and required output presence. It is stronger evidence than simply accepting the saved gate message in the log.

The production section of `logs/stage_a_rerun_D029.txt` contains:

- All 43 successful fitting jobs and 98 distinct model names.
- Successful prediction completion for 2014, 2015, 2016, 2017 and 2018.
- Split calibration, Stage A analysis and all three decomposition checks.
- Complete inference validation with all six acceptance summaries true.
- Smoke fitting/prediction and integrity tests detecting their deliberate corruptions.
- The final successful output gate and `=== ALL DONE ===`.

No uncaught failure or production interruption is visible in the log. Deliberate integrity-test failures and optional AIF360 dependency warnings are expected and do not indicate a failed run. The log supports completion; it is not an independently timestamped audit of every process or proof that an orchestration command was never restarted. Current artifacts passing the independent gate remove the practical ambiguity relevant to archiving.

`git diff 7d16f23 HEAD -- src scripts` was empty. Thus the reviewed execution code matches the run's code rather than a post-run implementation revision.

## Stage B readiness

Source review found the primary endpoint/family/alpha assignments consistent with the plan: race endpoints 2019, sex endpoints 2024, C5 outside the family at 0.05, and the six-test family at 0.05/6. Training-year evaluation uses held-out rows; later-year evaluation uses all eligible rows. The stored baseline estimates already include the training-year split adjustment. The no-race analysis derives its own historical margins. Household-grouped domain folds, clipping variants, reliability checks and suppression of P2 when unreliable are implemented.

The CPI and base-rate label rules, including strict inequality and lowest-threshold tie handling, are explicit. The 2018-deployment results use the appropriate training year and changes from its test split. Descriptive state comparisons report computability rather than silently counting non-finite cases as successes.

The updated C7 gate reconstructs expected grid coordinates and checks the registered settings; the earlier grid-completeness observation is closed. The remaining large-scale execution uncertainty is described in PA-3, not treated as proof of a bug.

I did not execute Stage B on actual later-year data. The new P1 check used synthetic frames labeled 2014 and 2018. It produced finite outputs in both feature specifications. A local core-count warning fell back to logical-core counting and did not prevent completion.

## Archive procedure

The corrected verifier uses one inventory policy for packaging and local-byte comparison, includes shell scripts and all 98 manifest-listed model files, checks packaged model hashes, and verifies the package checksum/size and DOI against the remote record. It also requires the recorded manual Software Heritage check.

I reran the current **nine synthetic archive tests** in the isolated copy. All passed, including changed Python bytes, changed shell bytes and omitted shell code. The earlier archive-source identity blocker remains resolved.

This review did not build or publish the real deposit, contact a real Zenodo record, verify a real Software Heritage snapshot, or create `ARCHIVED`. Those remain the actual archive procedure, not actions authorized by this review request. After correcting PA-1, finalize the plan and commit, build the package, publish and verify that exact package, record the manual Software Heritage check, and only then create the flag and begin later-year access. Do not edit inventoried files between package creation and verification without rebuilding.

No refit is required for the mandatory plan wording correction. No project files were modified during review. No ACS person records for 2019 or later, later-year empirical results, or external sources reporting such results were accessed.

## Archive recommendation

**ARCHIVE AFTER THE LISTED FIXES:** correct PA-1's error-rate interpretation before freezing the plan, then complete the normal deposit verification. The full-data Stage A readiness condition is satisfied; PA-2 through PA-4 are non-blocking. No additional model refit is indicated.
