# Final adversarial pre-archive review

**Date:** 20 November 2026

**Release candidate:** `ff45b43304ad4e14e5c4a9de8ad75b3e847ef5b4`

**Decision: archive. No new blocking or non-blocking defect was substantiated.**

This additional review extended beyond the preceding diff check at the author's request. I reconsidered the analysis and release paths rather than assuming that previous passing checks established correctness. I found no evidence requiring another model fit, scientific change, code fix or documentation amendment before depositing this candidate.

## Findings

| Classification | Result |
|---|---|
| Refit-relevant | None found. |
| Blocking before archive | None found. |
| New non-blocking defects | None substantiated. |

The earlier F2-1 safeguard remains resolved. The previously documented methodological limitations remain limitations; I have not relabelled them as new defects or proposed changes solely to prolong the review cycle.

## What this additional pass checked

### 1. Plan-to-analysis agreement

I traced the registered estimands through `src/analysis.py`, `scripts/stage_a_analysis.py`, `scripts/stage_b_confirmatory.py` and `scripts/stage_b_secondary.py`, with the output checklist and gate alongside them. Particular attention went to:

- Race and sex endpoint routing, the five-year baseline, seed aggregation, signed gaps and historical envelopes.
- The six-test confirmatory family, C5's separate secondary level and C8's descriptive status.
- Expected-prediction accuracy, DP and EO; household clustering; Census replicate-weight covariance; split-variance inflation.
- C7's absolute-value projection, yardstick floor and conservative treatment of seed covariance.
- Training-year test subsets, the distinct 2018 deployment baseline, forward-only prediction eligibility and exclusion of raw-code models after 2018.
- Inflation and base-rate label alternatives; decomposition reliability and clipping checks; P2 suppression; P1 with and without birthplace; no-race sensitivities.
- Metric-local non-computability and the distinction between empirical operating characteristics and a uniform or conditional guarantee.

I found no new substantive mismatch affecting the registered analysis. In particular, the plan explicitly limits the statistical guarantees and explains the historical calibration. Passing simulations have not been treated as a proof of universal error control.

### 2. Independent numerical oracles

These were additional tests written for this review, rather than repetitions of the project's assertions:

| Check | Independent comparison | Result |
|---|---|---|
| Weighted estimates and full covariance | Direct ratio estimates for the full and all 80 replicate weights, followed by independent covariance construction, over 25 random synthetic cases | Pass |
| Household-cluster covariance | Numerical derivatives of metric estimates with respect to household case weights, summed as an independent covariance calculation, over the same 25 cases | Pass |
| C7 projection interval | Exact extrema over interval endpoints and zero crossings, for 1,000 random configurations including yardsticks below the floor | Pass |
| Frozen calibration constants | Recomputed all primary temporal margins, DP/EO envelopes and geographic yardsticks from the stored allowed-year estimates and geographic-pair table | Pass |
| Claim assembly | Independently reconstructed C1–C7 for both weightings from synthetic data and stored synthetic baselines, checking endpoint, baseline subtraction, seed aggregation, SE, interval and decision | All 14 combinations pass |

The numerical derivative checks matter because they test the implemented influence-value covariance without simply copying its formula. The claim-assembly checks test the runner's routing and aggregation separately from the already-tested estimator functions.

### 3. Complete synthetic analysis rehearsal using the current frozen models

I constructed entirely synthetic frames for all ten registered survey years, with all 51 geographies, household/person identifiers, both sexes, White and Black groups, varied labels and positive full/replicate weights. Each year contained 2,448 synthetic persons. These were newly generated fixtures, not disguised later-year ACS data.

Using the actual frozen model files and prediction code, I generated all **915 eligible model/year prediction sets**. The analysis then completed:

1. Stage A calibration and stored estimates on the synthetic original-cohort years.
2. The confirmatory runner, including both weightings and all trajectories.
3. The complete secondary runner, **including P1 and P1 without birthplace**; neither expensive branch was skipped.

Independent output checks established:

- Exactly **10,300 trajectory rows**, with the exact expected unique `(model, year, label rule, weighting, metric)` set—not merely the right row count.
- Agreement in both value and SE for **all 50** overlapping seed-0 GBM nominal/unweighted metric-year estimates between the trajectory and secondary-label tables.
- Presence of all C1–C8 outputs for both weightings and completion of all secondary sections, including deployment in 2018 and the no-race sensitivities.

**Harness boundary:** fitting was not repeated. Because the frozen models were not trained on these artificial frames, the harness replaced the fit-specification inventory preflight with checks of every applicable stored prediction using the real prediction validator. It redirected data and outputs into scratch space, used a synthetic-path-only access guard and marked result provenance as synthetic. Model hash checking, prediction generation, row-key checking, prediction loading, estimators and analysis runners remained active. Consequently, this is a substantive execution test of the analysis paths, not a claim that synthetic artifacts satisfy the real release gate or reproduce the study's empirical findings.

### 4. Real-artifact gate and regression checks

Separately from the synthetic rehearsal, I reran the **actual Stage A gate** in an isolated analysis copy against the permitted original-cohort artifacts. It passed:

> stage_a: all promised outputs present, current and passing their acceptance criteria

I checked that all Python files in that copy's `src/` and `scripts/` matched the release candidate. This avoids attributing a passing check from older code to the current candidate.

The current regression suites also passed in an isolated copy:

- **15/15** estimator, decision-rule and decomposition-balance tests.
- **24/24** archive tests, including incorrect identities, content mismatches, extra/duplicate members and unpublished-record rejection.

I re-read the archive builder/verifier and release sequence. The preceding final diff review's actual isolated build remains applicable because HEAD is unchanged: it verified all **267 members** against the exact new commit and frozen reference/model hashes. This pass does not turn the mocked remote verification into evidence of a real publication. The actual Zenodo package and Software Heritage revision still require the normal release verification.

## Safeguards and limits

The original project remained clean at the stated commit. I made no project edits, did not refit models, did not publish anything and did not create `prereg/ARCHIVED`. All new test outputs are outside the project. No ACS person records for 2019 or later, or empirical results from those years, were accessed.

This review establishes additional evidence for the current release candidate; it cannot prove absence of every possible software defect or guarantee that future data contain no unexpected condition. The existing plan already requires failures and deviations to be disclosed. The manuscript is still a pre-results draft: archive readiness is not a claim that the eventual completed paper has already passed submission-level review.

## Recommendation

There is no substantiated new issue for the other AI to fix. Proceed with the established archive workflow for **`ff45b43304ad4e14e5c4a9de8ad75b3e847ef5b4`** and its frozen inputs. Verify the actual deposited package and the same revision in Software Heritage before creating the guard flag or accessing later-year person data.

**Final recommendation: archive.**
