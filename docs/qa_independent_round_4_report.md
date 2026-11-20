# Independent critical QA — round 4

Date: 20 November 2026  
Project: `/Users/alif/Base/Projects/re-test-temporal-fairness-stability/`  
HEAD observed: `ea20cb167b577a7c97c4de18f4da884e1c4bb207`  
Scope: current source and documentation, round-3 dispositions, and isolated synthetic checks. References below are relative to the project root. The working files, rather than the commit identifier alone, were reviewed.

## Refit-relevant — decision first

**No new confirmed blocking defect in the fitted models or their predictions was identified. Proceed with the planned 2014–2018 rebuild and model refit.** This is a bounded review conclusion, not certification that the forthcoming run will succeed. The required derived-data provenance must be produced by the rebuild before training; the updated workflow already puts that step first.

The remaining confirmed implementation blocker is **A4-1, archive verification**, which can be fixed independently of the expensive fits. It does not call for a different statistical model, feature mapping, training split, or prediction convention.

**R4-1 — non-blocking; refit-relevant operational improvement:** semantic settings still invalidate more model families than necessary. This is safe over-invalidation, not a reason to delay or repeat the planned refit. Details follow below.

**Archive recommendation: archive after the listed fix and successful final validation.** Do not archive the currently stale Stage A outputs. The supplied rehearsal is not a substitute for the final run, especially because its split calibration failed. That failure was correctly detected; it is not evidence of a new defect in the failure policy.

## Findings, ordered by consequence

### A4-1 — major; blocking before archive: source presence is checked, but source identity and shell-script completeness are not

**Location:** `scripts/verify_archive.py`, `verify()` (approximately lines 109–130), `REQUIRED`, and `scripts/test_archive.py`; `prereg/PREREGISTRATION.md`, Section 10.

**Evidence:** the verifier now opens the ZIP, computes member hashes, checks required reference files against local bytes, and checks packaged models against the archived model manifest. These are substantial improvements. However, its separate `src/` and `scripts/` loop only enumerates local `*.py` paths and checks whether those paths occur in the archive. It never compares their contents. Shell scripts such as `scripts/run_all.sh` and the download helpers are outside that inventory check.

I reproduced both gaps using the project's synthetic archive fixture in an isolated temporary tree with a mocked Zenodo record:

1. Build a complete package and receipt, then change the local `src/a.py`. `verify()` returns `[]`, meaning success.
2. Include `scripts/run_all.sh` in the fixture, build the package, remove that member, and update the receipt and mocked remote checksums to match the incomplete package. `verify()` again returns `[]`.

The project's existing six archive tests all pass. The current “local file changed” test changes `margins.json`, which is in `REQUIRED`; it therefore does not cover this source-code branch.

**Why it matters:** the archive can contain different executable code from the working copy that will process the unopened years, while verification still permits creating `ARCHIVED`. An incomplete package can also omit the orchestration/download code. This contradicts the plan's explicit promise of the same local bytes and complete code inventory. It is not a claim that an actual published archive is defective; no real archive or remote record was verified in this review.

**Suggested fix:** derive an explicit inventory of executable source and required support files, including `.sh` scripts, and compare both membership and SHA-256 against the local files. Reuse a consistent inventory policy between packaging and verification, with explicit exclusions for generated receipt/flag files. Preserve the existing reference-file and model checks. Add regression tests for changed Python bytes and omitted shell code; ideally also changed shell bytes. Both demonstrated cases must fail while a complete unchanged package still passes.

**Refit impact:** none. A verifier/test change should not require fitting models again. Rebuild the archive after the fix and after final outputs are ready.

### G4-1 — major; blocking before archive: final empirical validation remains outstanding

**Location:** `docs/progress_update_for_reviewer_round4.md`, `scripts/run_all.sh`, `scripts/check_outputs.py::stage_a`, and the plan's Stage A placeholders.

**Evidence:** the progress update explicitly says the full rerun has not started and that Stage A and nonsynthetic validation outputs are stale. The rehearsal failed split calibration on its small sample. The current gate correctly rejects nonempty `calibration_failures`; a reassuring count of eligible people in each full-data state does not itself establish that all metrics/configurations will pass calibration.

**Why it matters:** implementation acceptance and empirical acceptance are different. There is not yet current evidence that the registered calibration and inference criteria pass on the intended full run.

**Required completion:** run the prescribed allowed-year rebuild, fitting, prediction, calibration, analysis, decomposition and inference-validation sequence; require the final Stage A gate to pass on current inputs. Fill the plan's Stage A values from those outputs before packaging. If full-data calibration or validation fails, investigate and document the resolution before archive or later-year access; do not silently waive a case, default its multiplier, or loosen a criterion because the result is inconvenient.

This is an existing readiness condition, **not a newly discovered code bug or a request for an extra model run**. A failure in analysis validation does not automatically justify refitting otherwise unchanged models.

### A4-2 — minor; non-blocking: the joint simulation is a proxy for the runner, not an exact reproduction of its seed aggregation

**Location:** `scripts/validate_inference.py::part3` (approximately lines 153–189), `scripts/stage_b_confirmatory.py::seed_mean_dev_from_baseline`, and plan Section 7.6.

**Evidence:** the runner first combines each seed's new-year and baseline variances, takes a square root, then averages over seeds. For deviation claims its reported SE is

`mean_s sqrt(v_new,s + sum_t v_t,s / 25)`.

The joint simulation averages each year's per-seed SEs first, then combines those averages:

`sqrt((mean_s sqrt(v_new,s))² + sum_t (mean_s sqrt(v_t,s))² / 25)`.

These are generally unequal. The latter is no larger than the former by the triangle inequality; equality needs special alignment of the per-seed variance profiles. The simulation also uses those averaged annual SEs as the noise of the seed-mean estimate, rather than reproducing cross-seed sampling covariance.

**Why this is not a refit or archive blocker:** the revised claim is about anticipated, unconditional operating characteristics under specified simulation assumptions. It is not a uniform or conditional error-control theorem. For the same simulated point estimates and margins, narrower intervals make both decisive outcomes easier to reach, so this interval-width difference alone does not establish anti-conservative acceptance relative to the runner. I found no evidence here that the actual confirmatory runner computes its SE incorrectly.

**Suggested improvement:** describe this as an annual-SE proxy/stress model and distinguish it from the exact runner calculation. Avoid reading “overstates noise” as a general proof of conservatism when that noise also determines the margin. An optional sensitivity analysis can use the runner's exact aggregate SE for interval construction while retaining the stated annual noise model. Report any materially different conclusions. This requires analysis work only, not new fitted models.

The plan's removal of conditional guarantees is the important substantive correction and should be retained. The manuscript's design section is still a placeholder; when completing it, carry over this qualification rather than replacing it with an unqualified claim of validated error control.

### A4-3 — minor; non-blocking: validation-grid completeness is checked by counts, not by unique coordinates

**Location:** `scripts/check_outputs.py::check_validation` (approximately lines 67–103).

**Evidence:** the gate requires nine three-way rows, 33 joint rows, and at least 30 C7 rows per setting. It checks claim keys and recomputes acceptance from detailed rows, but it does not require the exact set of unique history/theta coordinates or C7 setting/grid coordinates. A same-length collection with duplicated cells can therefore satisfy the count checks while omitting a registered case.

**Why non-blocking:** the current generator explicitly loops over the intended grids, and the new complete-run restriction fixes the original stale-section merging problem. I did not find an actual omitted grid cell in that generator. This is a remaining defense against future regressions or malformed artifacts, not evidence that the pending run will skip cases.

**Suggested improvement:** compare coordinate sets and require uniqueness, in addition to row counts and acceptance criteria. Add a small fixture replacing one cell with a duplicate and require rejection. No model refit is implicated.

### R4-1 — minor; non-blocking; refit-relevant: family-specific function hashes coexist with global semantic invalidation

**Location:** `src/pipeline.py::semantic_config`, fit/prediction specifications, and `scripts/test_specs.py`.

**Evidence:** fitting-function changes are now isolated by family, as requested. However, all family fits include the common semantic-configuration object. The sensitivity test explicitly expects changing an LFR hyperparameter to change the GBM, ExpGrad, per-year and no-race fit specifications too. The isolated test confirmed that behavior.

**Why it matters:** a future family-local setting change can schedule unnecessary expensive fits. It does not allow stale models to be accepted and does not make current predictions incorrect.

**Suggested improvement:** optional future separation into shared and family-relevant semantic settings, with dependency tests. Do not make this optimization a prerequisite to the imminent run. The disposition's family-specific *code* isolation claim is supported; a broader claim of completely family-local cache invalidation would not be.

## Part 1 — round-3 disposition verification

“Resolved” below concerns the implementation or narrowed claim. It does not imply that the outstanding full-data run has already supplied current validation evidence.

| Round-3 item | Verdict | Independent basis and residual status |
|---|---|---|
| R3-1 — semantic specification coverage | **Resolved for the reported omission** | `pipeline.semantic_config()` serializes the feature/group/label/race, pooling, estimator and mitigation settings; fit/prediction code coverage includes the data-to-design and preprocessing helpers. Nine semantic mutations changed the expected fingerprints in isolated tests. This verifies fingerprint sensitivity, not equivalence of every possible training implementation. Residual over-invalidation is non-blocking R4-1. |
| R3-2 — derived-data build provenance | **Resolved in code; execution evidence pending** | `data.assert_derived_current`, `build_spec_sha`, `build_year`, and `common.load_year` reject legacy/stale tables and bind the current table to build metadata; rebuilding requires the raw inputs. The workflow explicitly rebuilds 2014–2018 before training. I did not independently repeat the claimed five-year byte-identical rebuild. Retain its evidence and the final run's build records. This is covered by blocking readiness condition G4-1, not a new refit defect. |
| A3-1 — archive contents | **Partly resolved** | ZIP contents, required reference bytes, model hashes, remote checksum/size/DOI and recorded manual SWH check are now checked. Source-byte equality and shell completeness remain unverified; independently reproduced in blocking A4-1. |
| A3-2 — upstream input lineage | **Resolved for the identified analysis paths** | `pipeline.provenance(inputs=...)`, `stale_inputs`, the analysis/validation callers and `check_outputs.fresh` now connect upstream data/calibration/results to downstream freshness. The isolated lineage test detects an upstream-only change. This is explicit caller-supplied lineage, not automatic discovery of every dependency. |
| A3-3 — conditional versus unconditional claims | **Resolved by narrowing, with a non-blocking approximation caveat** | Plan Sections 6/7.6 and `validate_inference.part3` explicitly describe unconditional rates and disclaim conditional guarantees. Both signs, trend history, null-conditioned rates and denominators are implemented. The manuscript needs these qualifications when its unfinished methods section is written. See A4-2 for the residual SE-proxy distinction. |
| A3-4 — partial validation freshness | **Resolved for the original stale-section defect** | Partial runs cannot replace the registered complete result, and the gate requires `complete_run` and recomputes acceptance from rows. Exact grid identity remains optional hardening, A4-3. |
| A3-5 — ESS/balance failure policy | **Resolved as an operational diagnostic** | `stage_b_secondary.balance` adds an ESS-fraction floor of 0.5, caps the marginal tolerance at 0.05 and checks categorical total variation with a noise allowance. Synthetic identical-distribution, concentrated-weight and rare-category cases pass their expected tests. This remains a calibrated balance heuristic, not proof of joint overlap or causal identification. The reported real-data before/after success was not independently recomputed. |
| A3-6 — invalid splits and degrees of freedom | **Resolved in code; full-data acceptance pending** | `check_split_variance.py` uses each cell's valid count in the variance bound, requires at least 95% of the K splits, records failures and fails the run. `check_outputs.stage_a` also rejects those failures. The plan calls this calibration approximate. The small-sample rehearsal failure is consistent with that policy. |
| A3-7 — fitting code per family | **Resolved for code dependencies** | Separate fit functions and family-specific helper hashing are implemented. All four isolated family-function replacement tests pass. Broad configuration invalidation remains non-blocking R4-1. |

A precision point on R3-2: provenance validation is cached within a process; “checked on every load” should be understood as validation of the process's frozen input, not continuous monitoring for external file replacement. Avoid modifying input tables during a run. This does not warrant changing the fitting method.

## Part 2 — checks and limits

### Checks independently executed

All executable checks were run from copies under the review workspace or in temporary synthetic trees, using the project's Python environment with bytecode writing disabled. No project files were modified.

| Check | Result | Scope |
|---|---|---|
| Analysis synthetic suite | **15/15 passed** | Estimator/decision-rule cases plus the new balance cases. |
| Download-integrity fixture suite | **10/10 passed** | Synthetic/local fixtures; no ACS download. |
| Existing archive fixture suite | **6/6 passed** | Mocked remote record and synthetic package. |
| Additional archive probes | **2 defects reproduced** | Changed local Python bytes and omitted packaged shell script both incorrectly accepted. |
| Specification and lineage suite | **14/14 passed** | Nine setting changes, four family changes, one upstream-lineage change. In the isolated copy, data-file hashes were replaced with deterministic synthetic values; official dictionary files supplied the mapping. No person data were loaded. |

The specification test is intentionally qualified: it exercises fingerprint dependencies with fixed synthetic data identity. It does not verify the actual table hashes, train models, or certify stored model artifacts.

### Areas found sound or appropriately limited

- The rebuild precedes the fit, and stage orchestration stops on failed commands. There is no reason to repeat a successful fit merely to correct the archive verifier.
- Fit and prediction identity now cover the previously identified configuration and preprocessing omissions. Family-function isolation works.
- Result freshness includes the newly explicit upstream analysis inputs; it is no longer solely a code/model fingerprint comparison.
- Partial inference runs cannot stamp a mixture of old and new sections as a complete registered validation run.
- Split-calibration failures are explicit and are rejected both by the calibration script and the final output gate.
- The new support and total-variation checks address the particular low-ESS and distributed rare-category loopholes raised previously.
- The narrowed unconditional simulation claim is materially more defensible than the earlier implication of conditional error control. Finite simulation grids still describe the chosen settings, not all possible future populations.
- No new confirmed reason to change the frozen-model family, expected-randomization prediction convention, or harmonized feature construction emerged from this review.

### Boundaries of this review

I started with the round-4 progress update, followed the round-2 brief with the requested round-3 substitution, and used the round-3 report/disposition as claims to verify rather than as proof. The review focused most deeply on changed model/data specifications, lineage, inference validation, balance/split failure policy and archive enforcement.

No ACS person records for 2019 or later were accessed, downloaded or computed on. No later-year empirical results or external publications reporting them were consulted. Stage B source was reviewed as code only. I did not run Stage B, build a real archive, query the actual deposit, or create an archive flag.

I did not rerun the expensive models, independently reconstruct the five full allowed-year tables, reproduce the full harmonization/reconstruction outputs, or certify stale result files. The rehearsal and byte-identity statements remain supplied evidence, not newly reproduced results. This report therefore supports proceeding to the full run; it does not replace the full run or a final check of its artifacts.

## Handoff to the implementing AI

1. Proceed with the planned allowed-year rebuild and refit. Preserve build records; stop if the derived-data checks fail.
2. Fix **A4-1** and add the two demonstrated regression cases before creating the archive. Keep this fix separate from model-fitting semantics.
3. Complete **G4-1**: regenerate the required outputs, pass the registered full-data gates, fill the plan's Stage A values, then build and verify the actual deposit.
4. Record **A4-2, A4-3 and R4-1** as non-blocking limitations/improvements. Do not restart the expensive fits to satisfy them.
5. Keep later-year data unopened until the finalized plan and required artifacts have been archived under the corrected verification procedure.
