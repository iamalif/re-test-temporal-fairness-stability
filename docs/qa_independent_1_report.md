# Consolidated independent QA: temporal fairness stability re-test

**Review date:** 19 November 2026. **Decision:** do not archive the present plan yet.

This document supersedes the earlier chat review. It combines a second source/code inspection with targeted checks of saved **2014–2018 aggregate results** and synthetic calculations. It distinguishes confirmed defects, methodological objections, and questions requiring further evidence. It is feedback for the researcher and implementing AI, not authorization to modify the research protocol or access held-out outcomes.

## Scope, restrictions, and evidence

Project reviewed: `/Users/alif/Base/Projects/re-test-temporal-fairness-stability/`. Project-relative file references below are intentional so this document remains usable on another computer. Functions and section names identify locations where line numbers may change.

No project files were changed. No person-level data were opened, including original-cohort records. No `data/derived/` contents were read or computed on. No fitting jobs were started. Executed checks used copied code in a separate review workspace, installed library code, synthetic values, documentation, and original-cohort aggregate reconstruction files. Consequently, this is **not an independent recomputation from raw records**, and it does not certify every reported empirical result.

The earlier pass encountered an already-recorded external outcome of unspecified survey years in the project's exposure record. It is not repeated here. No additional later-year outcome sources were intentionally opened in this pass. New literature searches likely to expose held-out results were avoided; novelty remains qualified accordingly.

Primary sources inspected include:

- [Ding et al., arXiv v3](https://arxiv.org/html/2108.04884v3), especially §4.1, Appendix C, and D.3; the local PDF was also used to re-run figure extraction.
- [Census, 2018 PUMS Accuracy of the Data](https://www2.census.gov/programs-surveys/acs/tech_docs/pums/accuracy/2018AccuracyPUMS.pdf): sampling design, replication, and dollar adjustments. This historical document does not validate every subsequent survey change.
- Local Census CSV data dictionaries for 2018, 2019, and 2021–2024, documentation only.
- Local folktables source: `folktables-main/folktables/acs.py` and `load_acs.py`.
- Installed Fairlearn source: `postprocessing/_interpolated_thresholder.py` and `reductions/_exponentiated_gradient/exponentiated_gradient.py`.
- Installed AIF360 source: `algorithms/preprocessing/lfr.py`.

The review inspected the plan, manuscript, decision/prior-work records, core source modules, reconstruction and paper-output scripts, Stage A/B runners and analyses, download scripts, and environment specification. It did not verify every bibliography entry, independently repeat all Census crosswalk decisions, run a fresh installation, compile the manuscript, or fit models.

## Overall judgement

The project has a worthwhile question and several strong design choices: genuinely withheld future outcomes, explicit historical calibration, saved models, a weighted sensitivity analysis, and candid reconstruction discrepancies. The current weaknesses are concentrated in inference, interpretation, and reproducibility enforcement. They are fixable without opening held-out data.

The contribution should be framed as a **pre-registered extension using a reconstructed and harmonised pipeline**, accompanied by an original-cohort reconstruction study. It cannot yet be described as an exact replication of the original deployed classifier. The strongest potential contribution is the combination of careful reconstruction, measurement comparability, and a clearly delimited temporal extension—not an unqualified novelty claim about fairness drift or decomposition.

Severity meanings: **critical** undermines a stated confirmatory validity claim; **major** requires correction or an explicit defensible resolution before archiving; **minor** is a narrower reporting/robustness defect; **question** is unresolved and must not be presented as a proven error.

## Findings, ordered by severity

### 1. Critical — C8 is not justified as an exact binomial test

**Where:** preregistration §§5 and 7.2; `src/analysis.py::sign_test`; geographic-reference construction in `scripts/stage_a_analysis.py`; C8 in `scripts/stage_b_confirmatory.py`.

**Evidence/problem:** the 20 indicators reuse state-year observations through the geographic references, and each temporal/geographic comparison shares its own 2014 reference estimate. A null about the probability of temporal change being smaller does not establish independent Bernoulli(1/2) indicators. Deliberate selection of the largest states also requires a clear target: these 20 states, or a hypothetical population of states? Fixed selection alone is not proof that a sign test is invalid; the missing independence/null justification is the decisive issue.

**Why it matters:** a binomial p-value need not have the claimed level. Bonferroni cannot repair an invalid constituent test. A synthetic counterexample makes the logical gap clear: let all 20 indicators equal one fair coin. Each marginal probability is 1/2, but the test rejects every time because the count is always 0 or 20. This is a counterexample to the justification, not an estimate of the actual project's false-positive rate. The implemented threshold of 17/20 is numerically correct under the independent-binomial model (two-sided p≈0.002577).

**Fix:** preferably make C8 descriptive for this study, preserving its scientific comparison. Alternatively define a finite-state estimand and develop joint inference that respects shared observations, estimated references, and uncertainty in the comparisons. Validate the proposed test under relevant nulls before restoring a family-wise claim. Do not simply bootstrap the 20 indicator values independently.

### 2. Major — C7's transformed-normal interval lacks a demonstrated coverage guarantee

**Where:** preregistration §7.2; `src/analysis.py::compare_stability`; C7 in the confirmatory runner.

**Evidence/problem:** the code draws a normal vector centred at the estimated changes, transforms draws through absolute values, and uses percentile endpoints. This is not automatically a frequentist confidence interval for the difference of absolute changes, particularly near zero. Geographic denominators are estimated from historical observations and reused as fixed constants without an explicit conditional target. The denominator can in principle be zero after the noise correction.

**Why it matters:** the asserted family-wise error control is unsupported until the constituent decision has suitable calibration. This review has not demonstrated numerical undercoverage for the project's actual parameter configuration.

**Fix:** explicitly decide whether the yardsticks are fixed historical calibration constants or estimated population quantities. A conservative route is to construct a justified joint confidence region for the underlying changes and bound the transformed statistic over that region, treating yardstick uncertainty consistently. Validate near-zero changes and the equal-stability boundary using synthetic simulations. Pre-specify behavior for zero/small yardsticks. Increasing Monte Carlo draws alone does not resolve coverage.

### 3. Major — C3/C4 test historical-envelope retention, not initial certification and retention

**Where:** preregistration §§5–6; `scripts/stage_a_analysis.py` epsilon calculation; manuscript certificate language.

**Evidence/problem:** epsilon is the maximum absolute seed-mean post-processed gap in 2014–2018, floored at 0.01. There is no independent substantive tolerance plus held-out 2014 certification gate. Large historical drift enlarges the later acceptance band. An average signed gap can also cancel opposite gaps across seeds; it does not certify each fitted model.

**Fix:** either rename the question consistently as retention of the historical disparity envelope, or specify a deployment-time tolerance, certification rule, and outcome for models that fail initial certification. Define whether the estimand is the average signed gap over five frozen models, a randomised mixture, or a claim about each deployed model. Report per-seed disparities as diagnostics. Do not silently replace the registered seed-average estimand after outcomes are seen.

### 4. Major — The headline preprocessing percentage is both miscomputed for its interpretation and over-attributed

**Where:** `scripts/make_reconstruction_outputs.py:94`, `ShareDeclinePerYearOnly`; manuscript abstract and Reconstruction → Preprocessing; log D015.

**Confirmed arithmetic:** the saved original-cohort aggregates give published decline 0.0254000, common-scaler decline 0.0164936, and per-year-scaler decline 0.0239763. The current formula is `(published − common)/published = 35.06%`. The paired preprocessing contrast is `(per_year − common)/published = 29.46%`. The difference between these percentages is unexplained reconstruction mismatch, not measured preprocessing effect.

**Additional interpretation problem:** agreement with a figure does not identify the original implementation. The paper itself admits the original scaler was not confirmed. The anchor establishes the experiment, not this retrospective explanation.

**Fix:** report the paired contrast and its denominator explicitly: changing preprocessing in this reconstruction adds approximately 0.007483 accuracy decline, about 29.5% of the published decline. Do not claim it caused that share of the original paper's decline without original code or author confirmation. Replace “only” with “among the variants examined.” The existing 35% figure may be described as the share of published decline not recovered by the common-scaler reconstruction, if useful, but not as a preprocessing attribution.

### 5. Major — Cached artifacts can silently become inconsistent with the frozen experiment

**Where:** `src/pipeline.py::predict_year`, `load_pred`, `manifest_update`; `scripts/stage_a.py::main`; `src/data.py::build_year`.

**Evidence/problem:** predictions are skipped solely by filename existence; loading unpacks bits and truncates to requested n. Model loading does not enforce the recorded SHA-256. Fit jobs are skipped based on names in a manifest. Derived datasets are reused based on file/metadata existence rather than verified provenance. Changed model bytes, preprocessing, row order, raw inputs or code can therefore coexist with stale predictions. A stored hash is evidence only if something checks it.

**Fix:** bind predictions to model hash, exact input hash/row identity, preprocessing/code version and original prediction count. Verify exact required model inventory and hashes before Stage A analysis and Stage B. Make writes atomic; reject corrupt/incomplete files. Include configuration and source fingerprints in reconstruction resume keys. Test altered model bytes, reordered rows, changed configuration, and interrupted writes using synthetic fixtures. Do not invalidate or regenerate an active run blindly; first inventory provenance and decide which artifacts are actually affected.

### 6. Major — Worker failures can masquerade as successful stages and incomplete experiments

**Where:** `scripts/stage_a.py`, error branches in fit/predict; `scripts/reconstruct.py::run_job/main`; `scripts/run_all.sh`; `scripts/stage_a_analysis.py` state discovery.

**Evidence/problem:** worker exceptions are printed/logged but the parent runners can return success. `set -e` cannot detect those failures. Stage A analysis derives its state list from whatever models are present, so an absent per-state job can reduce the geographic arm instead of enforcing exactly 20 sources. Reconstruction comparison and macros consume successful rows without enforcing the complete intended design or unique runs.

**Fix:** collect errors, exit nonzero on any required failure, and assert exact expected model/job/seed/year inventories before calculating results. Distinguish intentional optional omissions from errors in a machine-readable completion record. Require 20 source states and 380 ordered geographic pairs per metric/weighting. Add a deliberately failing synthetic worker check.

### 7. Major — The advertised clean rebuild lacks required directory setup and robust downloads

**Where:** `scripts/download_stage1.sh`; `scripts/download_stage2.sh`; `scripts/run_all.sh`; `.gitignore`.

**Evidence/problem:** Stage 1 creates year folders but assumes `data/raw/dictionaries/`, `data/raw/crosswalk/`, and `docs/sources/` already exist. Raw subfolders and sources are ignored, so a fresh checkout need not contain them. Output redirection into the dictionary folder can fail before reconstruction. Downloads use nonzero file size as completion evidence; an interrupted nonempty transfer can be reused. `download_docs.sh || echo ...` labels any documentation failure as a possible CPI issue and continues.

**Fix:** create every required directory, download to temporary paths, verify archive/document integrity, and atomically rename. Separate the expected CPI fallback from unrelated failures. Verify a fresh-checkout preparation workflow with stubbed downloads first, then an allowed-cohort rebuild when convenient. Do not claim the one-command rebuild is verified yet.

### 8. Major — Missing Puerto Rico silently changes the registered population

**Where:** `src/data.py::read_year_universe`; preregistration §3.

**Evidence/problem:** the loader continues when `csv_ppr.zip` is absent, although the study specifies the 50 states plus Puerto Rico. Recording `has_puerto_rico` does not prevent use of the altered population.

**Fix:** require both archives and the exact geography set for every registered year. Fail before generating accepted results when either is missing. Make any alternative geography an explicitly named analysis, not an implicit fallback.

### 9. Major — The primary estimands answer narrower questions than the headline implies

**Where:** preregistration §§4–6; manuscript title, abstract and contributions.

**Evidence/problem:** the main model changes raw occupations into coarse harmonised groups, uses reconstruction-selected tree count and frozen scaling, and evaluates complete later-year cohorts instead of the anchor's held-out test subsets. C1/C2/C5/C6 compare one endpoint with the five-year average. C3/C4 assess one later endpoint. These do not establish that fairness “stays” stable throughout the full extension, nor do they directly test the original unknown fitted model. Race's confirmatory extension is only one year beyond 2018; the longer confirmatory horizon concerns sex. C7 divides different metrics by different geographic references, changing the meaning of “more stable” relative to the original percentage-point comparison.

**Fix:** provide a claim-to-estimand table marking reconstruction, confirmatory extension, and descriptive analyses. Describe endpoint conclusions as endpoint conclusions. Retain trajectories to reveal interim deviations, without assigning them the endpoint family's error control. Report raw changes alongside normalised C7. State that different race/sex outcomes cannot identify a pure group effect because horizons differ. These design choices can be reasonable; their scope must be explicit.

### 10. Major — Historical calibration and power claims need a more explicit inferential target

**Where:** preregistration §§5–7; log D019.

**Evidence/problem:** the reference mean and margins are computed from the same historical observations. If the target is a population-history comparison, margin uncertainty and its dependence on the reference mean need treatment. If the target is a policy band defined by the actually observed historical data, that conditioning should be explicit. Using old data to set a band before opening new data is not inherently invalid; ambiguity about what is covered is the problem. A rough standard error and the statement that stability could “almost never” be concluded do not constitute a power analysis, particularly for EO and post-processed gaps.

**Fix:** write the nulls and conditioning mathematically, then align uncertainty calculations. Simulate decision probabilities across within-band, boundary and outside-band effects using synthetic data or allowed historical summaries, including the historical calibration rule when appropriate. Report anticipated inconclusive rates, not only interval width. Freeze numeric bands, reference estimates, yardsticks and acceptance criteria before release of new outcomes.

### 11. Major — Passing the DP check does not validate the decomposition's interpretation

**Where:** preregistration §8.4; `scripts/stage_b_secondary.py::dfl_weights/decompose`.

**Evidence/problem:** the residual contains true conditional-label change plus density-ratio estimation error, clipping bias and overlap failure. Matching two DP contrasts within 0.005 cannot establish balance in all feature regions relevant to EO and accuracy. Cross-fitting is by person rather than household, allowing related people in training and validation folds. The code records failure flags but still generates the theory-comparison booleans.

**Fix:** add overlap, weight-tail, effective-sample-size and group-specific balance diagnostics; pre-specify clipping sensitivity and uncertainty. Prefer household-respecting folds where dependence matters. Make reliability status govern the reported interpretation and suppress categorical P2 claims when validation fails. The historical check should be a falsification diagnostic, not proof of identification. Refer to the residual as conditional change plus approximation error until stronger evidence supports a narrower explanation.

### 12. Major — Stage B §8.6 is not the reconstructed per-year-scaling pipeline

**Where:** `scripts/stage_b_secondary.py`, “8.6 original-pipeline view”; `src/models.py::Scaling`; reconstruction runner.

**Evidence/problem:** reconstruction with per-year scaling fits the model using a scaler computed on all 2014 rows. The Stage B variant loads `gbm_s0`, trained with a scaler fitted on the 2014 training subset, and feeds it annually standardised values, including a different 2014 scaling. It also uses harmonised features rather than reconstruction's raw features. Thus even its starting representation differs from the reconstruction it is described as continuing.

**Fix:** either call it a preprocessing perturbation of the harmonised frozen model, or fit and freeze a separate precisely specified per-year-scaling model before archiving. Define the original-year scaling consistently and explain how harmonisation changes the comparison. Do not train the new variant after seeing held-out outcomes.

### 13. Major — Harmonisation diagnostics do not justify the stated bound on recoding effects

**Where:** preregistration §§3/9; `src/harmonise.py`; log D014/D017; recoding-check analysis.

**Evidence/problem:** small aggregate occupation-share changes do not bound group-specific or prediction effects: opposing changes can cancel, and real changes coexist with recoding. Cyprus is assigned to a residual region despite the log admitting no official destination and describing another plausible destination. The raw-versus-harmonised comparison changes multiple feature mappings and refits models, so it is a sensitivity contrast, not an identified occupation-recoding effect.

**Fix:** remove language implying a measured bound on harmonisation error. Provide a mapping provenance table with exact source/version and distinguish documented mappings from analyst assumptions. Add race/sex-specific diagnostics and allowed-cohort prediction sensitivity for ambiguous mappings. Label the raw/harmonised contrast accurately. Where possible isolate mapping changes one at a time. Do not infer negligible model impact solely from small counts.

### 14. Question — Weighted inference after the extra train/test subsample needs justification

**Where:** `src/common.py::state_split`; `src/analysis.py::weighted`; preregistration §7.3.

The replication coefficient and ratio calculations are correct as implemented. The unresolved issue is applying supplied survey replicate weights after an additional random person-level 20% selection while later years use full eligible samples. Does the inferential target include this second-stage randomisation, and is its variance represented? Simply multiplying all weights by five would not resolve ratio-variance questions. A derivation, survey-methodology reference or appropriate simulation should settle this. Do not treat this review as proof of underestimation.

Relatedly, household-cluster sandwich SEs are model-based approximations, not a full reconstruction of ACS survey design. Census documentation also identifies group-quarter sampling and additional PUMS processing. State clearly what unweighted uncertainty means. A simple clustered simulation validates that simulation, not the entire ACS design. Person-level train/test splitting leaves household members across the split; preserve it for reconstruction fidelity but discuss the resulting deployment-generalisation target and consider a household-held-out sensitivity.

### 15. Question — Randomised predictors require an explicit deployment/uncertainty convention

**Where:** `src/pipeline.py::Frozen.predict`; `src/models.py`; Fairlearn installed `predict` implementations.

Both relevant Fairlearn predictors compare positive probabilities with random uniforms. Passing the same integer seed on each call restarts the random stream. Therefore row ordering and call batching affect which person receives which random draw; different years reuse the stream prefix. The fitted policy is frozen, but the realised binary predictor is not solely a function of features and a stable person identifier.

**Fix/settlement:** decide whether the target is expected randomised-policy performance or one realised deployment. For the former, use expected prediction probabilities with suitable estimators; for the latter, specify independent year streams or stable row-key randomness, archive that convention, and account for relevant randomisation uncertainty. Quantify sensitivity on allowed years before changing the implementation. Do not assume this necessarily materially changes the current results.

### 16. Major — Promised outputs and enforcement are incomplete

**Where:** preregistration §6 sensitivity curves, §8.9; `scripts/stage_b_secondary.py`; archive protocol.

No margin-curve generator was identified in the inspected analysis scripts despite the promise of curves over 0.005–0.03. Section 8.9's dedicated output stores levels for selected model/metric combinations rather than explicitly producing every promised change; the trajectory file contains additional material but no complete reporting contract. Archive permission is a file-existence flag, not validation of the archived package or required artifacts. The plan archives hashes but does not clearly ensure preservation of actual model bytes needed for exact evaluation.

**Fix:** maintain a preregistration-to-output checklist, implement each promised output or narrow the promise before archive, and validate a complete required inventory. Archive actual frozen models where permitted (or preserve them in durable redundant storage with clear retrieval instructions), the exact code/environment, mappings, numeric margins, reference estimates and yardsticks. Record archive identifiers and hashes in a machine-readable receipt. The flag is useful as an accidental-access guard, not evidence of successful third-party archiving.

### 17. Major — Novelty is not independently established, and the draft overstates it

**Where:** `docs/prior_work_search_2026-11-18.md`; log D009; manuscript Related work and Introduction.

The search record openly lists incomplete reading, unavailable full text and limited indexed/screenshot coverage. The draft nevertheless makes categorical absence claims and calls the anchor the most frequently cited evidence without a supporting bibliometric comparison. I did not independently establish those claims. The prior-work record also needs reconciliation where later checks revise earlier descriptions.

**Fix:** use “we did not identify…” scoped to the actual search; distinguish the exact confirmatory re-test from overlapping fairness-drift, attribution and temporal/geographic studies. Complete outstanding design-only reading safely, using a human or filtered extraction if necessary to avoid later-year outcomes. Verify citation identity, venue and version directly before submission. Do not make “first decomposition” or broad drift-novelty claims from the present evidence. The reconstruction and pre-registered extension can stand without them.

### 18. Minor — Figure-recovery precision and legend claims need correction

**Where:** `scripts/reconstruct.py::plans`; `scripts/digitise_figure4.py`; manuscript Reconstruction; D013/D015.

The saved file contains 56 successful, unique jobs, matching the current `all` plan (40 GBM combinations plus 16 additional intervention configurations). No missing-run finding is warranted from the job count. Re-executing the figure digitisation against the local anchor PDF exactly reproduced both saved JSON files; this validates reproducibility of the extraction, not unrounded source precision.

The digitiser rounds to four decimals, and near-zero residual at axis ticks validates a coordinate transform—not exact recovery of unrounded source values. Legend series names are hard-coded in the script; the manuscript's claim of matching legend entries should reflect the actual manual assumption and visual validation.

**Fix:** freeze an explicit reconstruction inventory and distinguish completed, pending, and exploratory variants. Assert required series before generating macros. Say “values recovered from vector graphics to approximately four decimal places,” and retain an annotated figure/legend verification. Do not describe them as exact original values.

### 19. Minor — Small-group handling and numeric failure policies are underspecified

**Where:** `src/pipeline.py::kept_categories/pool_categories`; preregistration §4; `src/analysis.py` metric functions; secondary thresholds.

The implementation assigns an insufficient pooled remainder to the largest category, a fallback not fully stated in §4. The estimators do not define a consistent failure policy for zero group/positive denominators or non-finite outputs. C8 counts ties as false, and the truncating noise correction can create ties at zero. Base-rate anchoring searches only $20,000–$150,000 and chooses the first minimum; these bounds/tie rules are not specified in the plan.

**Fix:** document pooling, unseen-category behavior, tie rules, denominator checks, and failure handling; assert finite results before decisions. For base-rate anchoring, specify the grid bounds and what happens at a boundary. For C8, removing confirmatory status does not remove the need to report ties transparently.

### 20. Minor — Manuscript and metadata are out of sync with the actual protocol

**Where:** manuscript abstract/introduction/contributions; preregistration header; module docstrings; log D021/D022.

The draft says every model is trained on 2014 although 2018-trained models were added. The plan header's change references stop before later additions. The loader is listed as a contribution despite earlier decisions to treat it as an enabling artifact; this is a scope inconsistency, not a scientific prohibition. The “employed adults” shorthand is narrower than the explicit ACSIncome filters, which do not require current employment. Several numerical statements remain hard-coded despite a universal claim that paper numbers are generated.

**Fix:** reconcile the final protocol, exposure record, manuscript and artifact inventory. Define the universe by its filters. Use version-specific language and complete the remaining sections before submission. Keep deployment and fairness-certification generalisations proportionate to a Census prediction benchmark rather than implying operational decisions were studied.

## Things checked and supported

- The anchor's temporal stability claim and EO extension are real, and Appendix C describes state-wise 80/20 splits and inclusion of Puerto Rico. Its printed GBM configuration includes five estimators; its LFR settings match those copied into this project. This supports investigating a reconstruction discrepancy, not certainty about the original executed code.
- Local folktables code supports the stated ACSIncome filter/feature conventions and geography list. The `np.nan_to_num(x, -1)` observation is correct: the second positional argument is `copy`, not the NaN replacement value.
- DP and EO estimators use the stated signed pairwise contrasts. Race categories are single-race categories, not White/non-White except for the LFR intervention; make that distinction visible.
- The influence-value formulas have the expected denominators and signs. Household influence values are summed before covariance construction. Weighted replicate calculations recompute ratios and use the stated `4/80` factor.
- The variance of an equally weighted five-year baseline is divided by 25 under the assumed cross-year independence.
- Mean per-seed SE is a scalar upper bound without requiring positive correlation. Likewise, the mean of per-seed covariance matrices upper-bounds the covariance of the seed-mean vector in positive-semidefinite order: for any projection, the square of an average is at most the average square. **Do not “fix” C7 by simply dividing its covariance by five.** This conservative covariance fact does not prove coverage of its nonlinear percentile interval.
- The three-way interval logic matches the plan; synthetic examples returned holds, inconclusive and violated in the expected cases. Two-sided 1−alpha intervals are conservative for an equivalence decision and are not a bug merely because conventional TOST uses a different interval level.
- Documentation checks found identical OCCP code-key sets between the 2018 dictionary and each available 2019/2021–2024 CSV dictionary. The inspected 2019 RELSHIPP labels agree with the implemented relationship-category mapping. These checks do not certify all crosswalk assumptions or measurement comparability.
- Re-running the digitiser reproduced both saved Figure 4 and Figure 13 JSON files exactly.
- The saved reconstruction has 56 successful unique jobs matching the current plan count, with evaluation keys restricted to 2014–2018. The common/per-year 100-tree accuracy declines were independently recomputed from those saved aggregates.
- The inflation-threshold algebra is coherent: equating adjusted real incomes produces the stated ADJINC ratio times the CPI ratio, assuming the specified annual factors and series. This does not validate all future input values or the substantive choice of CPI series.
- The DFL odds include the sample-size ratio in the correct direction. A small DP residual is a useful necessary diagnostic, although not sufficient validation.
- The prior-shift DP formula follows directly from `P(pred=1|g)=TPR_g*pi_g+FPR_g*(1−pi_g)` when group-conditional TPR/FPR are unchanged. Its reported ratio to observed change can be unstable near zero and should not be called an explained-variance fraction.
- Guards are present in the primary person-data loading and Stage B download routes. They are useful safeguards, though not a complete provenance or archive-verification system.

## Corrections and qualifications to the first chat review

1. Retain the C8 objection, but do not claim that purposeful state selection alone invalidates every possible sign-test formulation. The missing joint/null model is central.
2. Treat C7 coverage and weighted-split inference as unresolved methodological questions requiring validation, not numerically demonstrated failures on these data.
3. Do not interpret historical margin selection as intrinsically improper. Its conditioning and scientific meaning need to be fixed.
4. The preprocessing criticism is now stronger and more specific: the percentage formula itself includes unexplained reconstruction error, in addition to the causal overstatement.
5. The earlier coverage list did not establish a full source-to-result rebuild. Neither does this review. Correct arithmetic and source inspection are narrower evidence.
6. A household-robust estimator is not automatically a complete survey-design variance estimator; the distinction matters for the weighted/unweighted interpretation.

## Recommended resolution order and archive gate

1. Resolve C8's status and define the inferential targets/conditioning for C1–C7. Decide whether C3/C4 are envelope-retention or certification questions. Freeze the resulting family and reporting language.
2. Correct the preprocessing calculation and qualify reconstruction attribution. Resolve §8.6's intended model before any new outcome access.
3. Implement artifact identity verification, exact inventory checks, nonzero failure exits, mandatory geography, atomic downloads/writes, and a fresh-checkout setup path.
4. Finish the harmonisation provenance table and decomposition reliability rules. Specify numerical edge cases and promised sensitivity outputs.
5. Validate statistical decision procedures on synthetic cases and allowed historical summaries; retain a reproducible validation script and concise results. No later-year data are needed for this.
6. Complete and verify Stage A, including all intended frozen models, numeric margins, yardsticks, baseline estimates and historical diagnostics. A running or partial manifest is not a finished archive package. Do not interrupt or refit active jobs merely because this review exists.
7. Reconcile manuscript, prior-work claims, exposure record, protocol version and deviations policy. Archive a concrete immutable package and verify it before enabling Stage B.

For the implementing AI's response, use a disposition table: finding number; accepted/rebutted/needs evidence; exact proposed change; whether model artifacts or estimands change; validation performed; remaining blocker. Rebuttals should cite code or primary sources. Do not dismiss issues because an earlier log says they were checked, and do not make every suggestion a mandatory redesign when a clear limitation or narrower claim suffices.

**Final recommendation:** proceed with the research, but not with archiving this version. Prioritise a defensible, smaller confirmatory core over retaining an eight-test headline. The reconstruction discrepancies are potentially valuable findings if reported with the correct uncertainty and attribution.
