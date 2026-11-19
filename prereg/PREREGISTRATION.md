# Pre-registration: Does fairness stay put? A re-test of temporal fairness stability on ACS 2014–2024

**Status:** DRAFT v0.3 (20 Nov 2026). Changes since v0.2: decision log D021–D024, D023 in response to an
independent review (`docs/qa_independent_1_report.md`, disposition in `docs/qa_independent_1_disposition.md`).
Not yet archived. Values marked ⟨A⟩ are filled from Stage A result files once the Stage A rerun finishes; the rules
that produce them are fixed here.
**Author:** single author (name withheld in this draft). Independent research; no institution endorses it.
**What this study is:** a pre-registered *extension* of the temporal-stability analysis of Ding et al. (2021),
using a *reconstructed and harmonised* pipeline, together with a reconstruction study on the original 2014–2018
cohort. It is not an exact replication of the original fitted classifier, which is not available.

---

## 1. Claim under test

Ding, Hardt, Miller and Schmidt, *Retiring Adult: New Datasets for Fair Machine Learning* (NeurIPS 2021;
arXiv:2108.04884v3), Section 4.1 and Appendix D.3. A gradient-boosted tree trained on 2014 US-wide ACSIncome and
evaluated on 2014–2018 loses some accuracy, while its demographic-parity (DP) violation stays "stable and
essentially constant over time". A classifier that satisfies DP on 2014 data "continues to satisfy the constraint"
on 2015–2018 data, and the same holds for the interventions studied. Appendix D.3 reports the same for equality of
opportunity (EO). Section 5 asks why there appears to be more temporal than geographic stability.

We ask whether these statements still hold when models frozen in 2014 are evaluated on 2019 (race) and 2024 (sex),
and whether the race DP gap changes less than accuracy relative to geographic yardsticks.

## 2. What has been seen before archiving (exposure record)

- **Original cohort, 2014–2018 (allowed):** all person records were downloaded and analysed: data counts, feature
  distributions, the reconstruction of Figures 4 and 13 (decision log D012–D015), and every Stage A result
  (metrics of the frozen models on 2014–2018, margins, yardsticks, decomposition check and its balance
  diagnostics, split-variance check). A rehearsal of the full chain (D024) used synthetic stand-ins for the later
  years, built from 2018 records; no real later-year record was involved.
- **2019 and later:** no person record has been downloaded or read. Only directory listings, file sizes, data
  dictionaries and documentation (including variable-change notes) were used.
- **Literature with post-2018 outcome content:** we read the design but not the results of Ceross (arXiv
  2609.09788), Tomar (arXiv 2506.23033), Wicker et al. (arXiv 2311.11911), arXiv 2412.10575 and Quy et al.
  (arXiv 2110.00530). Seen by accident: the abstract of an ICLR 2027 submission ("CAFE") states an out-of-distribution
  accuracy result on folktables (years unknown); the README of PartowMoradiK/stable-rankings-shifting-fairness states
  a false-positive-rate gap change of up to 13.4 points across state-year shifts on ACSPublicCoverage (years not
  stated). Neither concerns our estimands. The README of Hnhy1806/fairness-over-time reports Texas 2014–2017 results
  (original-cohort years) and a label-drift explanation, which we treat as prior evidence.
- **Theory read in full:** Chen et al. (NeurIPS 2022, arXiv 2206.00129), including their state-level 2014→2018
  results; Asiaee and Aryan (arXiv 2602.05144).
- **Independent review (19 Nov 2026):** the reviewer inspected code, plan and 2014–2018 aggregate results only; it
  opened no person records and no later-year outcomes.

## 3. Data

- **Source:** US Census Bureau ACS 1-year PUMS person files (`csv_pus.zip`, 50 states + DC; `csv_ppr.zip`, Puerto
  Rico), survey years 2014–2019 and 2021–2024. Both files are required for every year; the build fails unless the
  year contains exactly the 51 registered geographies. Excluded: 2020 (experimental weights only; Census advises
  against comparison) and 2025 (release not available when archiving). SHA-256 of every raw file:
  `logs/raw_sha256.txt`.
- **Universe (folktables ACSIncome), defined by its filters:** AGEP > 16, PINCP > 100, WKHP > 0 (usual hours worked
  in the past 12 months), PWGTP ≥ 1; 50 states and Puerto Rico; DC excluded (not in folktables' state list). Current
  employment is not required. This reproduces folktables' row counts exactly (2014: 1,587,856; 2018: 1,664,500).
- **Label:** nominal `PINCP > 50000` (as folktables; no inflation adjustment). Alternatives in Section 8.3.
- **Harmonised features** (`src/harmonise.py`; Census documentation only; provenance of every mapping, and whether
  it is documented by Census or an analyst assumption, in `docs/harmonisation_provenance.md`):
  AGEP, COW, SCHL, MAR, WKHP, SEX, RAC1P unchanged (codes identical in the 2014–2018, 2019 and 2024 dictionaries);
  occupation as 25 major groups plus one code for the long-term unemployed, from the label prefixes of each year's
  own dictionary, with the three 2010 codes that the official crosswalk moves *whole* into another major group
  (4610, 5620, 5800) assigned that group in every year (the set is re-derived from the crosswalk by
  `scripts/harmonisation_report.py`, which fails if the code differs; D023 corrects an earlier version that also
  moved five split codes); relationship mapped to RELP categories with roomer/boarder, housemate/roommate and other
  nonrelative merged (RELSHIPP mapped to the same categories from 2019); place of birth with three discontinued codes
  merged into regional residual codes (Tunisia into "Northern Africa, not specified", documented by Census from 2022;
  South Sudan into "Eastern Africa, not specified", deleted in 2024; Cyprus, used only through 2016 with no stated
  destination, into "Other Europe, not specified" — an analyst assumption affecting about 60 rows a year).
  Missing values become 0, as in folktables. The 2019–2024 dictionaries use the same occupation codes and prefixes
  as 2018 (checked). The state variable is named STATE from 2023 and is renamed on reading.
  The harmonisation report gives, overall and within race and sex groups, each occupation group's 2018 share against
  its 2014–2017 trend (largest absolute deviation 0.0051 overall and 0.0056 within any race or sex group). These deviations mix residual recoding artefact with real
  change; they are diagnostics, not a bound on harmonisation error.
- **Race comparability:** the race question and coding changed in 2020 (Census: compare with caution). Race-based
  confirmatory estimands therefore end in **2019**. Sex runs to **2024**. Because the horizons differ, a difference
  between race and sex results cannot be read as a pure group effect.
- **Groups:** race, White (RAC1P = 1) minus Black (RAC1P = 2), as in the original (single-race categories; the LFR
  intervention alone uses White versus non-White, because AIF360's LFR needs a binary attribute); sex, male minus
  female.

## 4. Models (fitted once and frozen before archiving)

All models are trained on a training split (within-state 80/20 random split, seeded, of persons) of their training
year (2014 unless stated) and saved with their preprocessing. Model files (≈135 MB) are deposited with the archive;
their SHA-256 hashes are in `results/models_manifest.json` (hash of that file: ⟨A⟩), and every load verifies them.
Each harmonised model also records a fingerprint of the harmonisation mappings it was trained with.

- **Base model (reconstruction rule, D015):** `GradientBoostingClassifier(loss="exponential", max_depth=5,
  n_estimators=100)`. The 5 trees stated in the paper do not reproduce its figures (accuracy 0.10–0.15 below the
  published values in every year and seed). Under the preprocessing that reproduces the published accuracy curve
  (per-year standardisation), 100 trees gives the smallest mean absolute deviation from it among 50, 100 and 200
  trees; with 100 trees the 2014 accuracy matches the published value.
- **Preprocessing (primary):** one standardisation fitted on the 2014 training split and frozen, as a deployed model
  would use it. (Trees are invariant to it; it matters for LFR.)
- **Seeds:** unconstrained GBM and all post-processed models: seeds 0–4. ExpGrad and LFR: seed 0 (cost: about
  5 hours per ExpGrad fit).
- **Interventions:** (i) post-processing: fairlearn `ThresholdOptimizer` on the GBM's scores (group-specific
  thresholds; objective accuracy), separately for DP and EO (`true_positive_rate_parity`) and separately for race
  (RAC1P) and sex (SEX); (ii) ExpGrad: fairlearn `ExponentiatedGradient` with `DemographicParity`, library defaults,
  race; (iii) LFR: AIF360 LFR with the hyperparameters of the original appendix (k = 10, Ax = 0.1, Ay = 1, Az = 2,
  maxiter = maxfun = 5000), binary White indicator, base model trained on the representation.
- **Small categories:** for the interventions, a sensitive-feature category keeps its own threshold or constraint if
  it has at least 100 training rows and at least 20 rows of each label; the other categories are pooled into one
  category; if that pooled category itself fails the same test, its rows are assigned to the largest category. At
  prediction time any category not kept (including a category never seen in training) is treated as the pooled
  category. The kept categories are recorded in the manifest.
- **Randomised predictors (4.4):** post-processing and ExpGrad output a random label for some persons. They are
  evaluated through their *expected* prediction (the probability of a positive output, from fairlearn's
  `_pmf_predict`), so every reported metric is the expected metric of the randomised policy; no random draws enter.
- **Per-year-scaling models (secondary 8.6):** the base model, seeds 0–4, trained on 2014 standardised with a scaler
  fitted on all eligible 2014 rows; at evaluation every year is standardised with its own full-population scaler,
  as in the reconstruction that reproduces the published accuracy curve.
- **Models deployed in 2018 (secondary 8.9):** the base model (seeds 0–4) and its DP post-processing for race and
  for sex, trained on the 2018 training split.
- **Per-state models (geographic yardsticks):** base model and DP post-processing (race) for each of the 20 largest
  states by 2014 rows (Puerto Rico excluded), trained on that state's 2014 training split, seed 0.
- **Raw-code model (8.7):** the base model on unharmonised codes, seed 0, for 2014–2018 only.
- **Evaluation sets:** training year: the held-out test split of the model's seed; every other year: all eligible
  rows of that year. Per-state models: own state's 2014 test split; other states and other years: all rows of that
  state-year. The person-level split leaves members of one household on both sides; it is kept for fidelity to the
  original and noted as a limitation.

## 5. Questions, estimands and the confirmatory family

**Target population.** Unweighted estimands describe the distribution from which the ACS sample is drawn, as in the
original; weighted estimands (Section 7.3) describe the population represented by the survey weights. All estimands
are conditional on the frozen models and on the calibration constants of Section 6.

Notation: for a frozen model and year t, m(t) is the population value of a metric; for families with several seeds,
the seed-average of the five frozen models. B_m = (1/5) Σ_{t=2014}^{2018} m(t) is the model's **2014–2018 baseline**.

**Confirmatory family (Bonferroni, α = 0.05/6 ≈ 0.00833 per test):**

| ID | Question (claim scope) | Model | Estimand θ | Year | Decision (Section 7) |
|---|---|---|---|---|---|
| C1 | Is the DP gap (race) at the 2019 endpoint within the historical range around its baseline? | GBM, seeds 0–4 | DP_race(2019) − B | 2019 | three-way, margin δ_DP,race |
| C2 | Same for the DP gap (sex) at the 2024 endpoint | GBM | DP_sex(2024) − B | 2024 | three-way, δ_DP,sex |
| C3 | Does the race-DP-post-processed model stay within its historical disparity envelope at 2019? | post-proc. DP race, seeds 0–4 | DP_race(2019) (seed-average signed gap) | 2019 | three-way, envelope ε_race |
| C4 | Same for the sex-DP-post-processed model at 2024 | post-proc. DP sex | DP_sex(2024) | 2024 | three-way, ε_sex |
| C6 | Is the EO gap (sex) at the 2024 endpoint within the historical range around its baseline? | GBM | EO_sex(2024) − B | 2024 | three-way, δ_EO,sex |
| C7 | Relative to geographic yardsticks, did the race DP gap change less than accuracy from 2014 to 2019? | GBM | D = abs(DP_race(2019) − DP_race(2014))/G_DP,race − abs(acc(2019) − acc(2014))/G_acc | 2019 | sign of a conservative interval |

**Reported with the same machinery, outside the family:**
- **C5 (secondary):** EO gap (race), GBM, EO_race(2019) − B, three-way with δ_EO,race at α = 0.05. Moved out of the
  family before any later-year data were seen because, at its anticipated standard error, a "holds" decision is
  almost unreachable even with no true change (Section 7.6).
- **C8 (descriptive):** for each of the 20 states, the noise-corrected |ΔDP_race| of the state's own model between
  its 2014 test split and the state's 2019 rows, against the state's geographic reference (median over the other 19
  states of the noise-corrected |DP_race(s → s′) − DP_race(s → s)| in 2014). We report the count of states with a
  smaller, equal and larger temporal change, and each state's change with its 95% interval. No significance test:
  the 20 comparisons share observations and estimated references, and no valid joint null was specified.

**Scope of the conclusions.** C1–C6 are endpoint statements: they concern 2019 (race) or 2024 (sex), not every year
in between; the full trajectories are reported (8.1) without family-wise control. C3/C4 ask whether a model's
disparity stays inside the range it showed in 2014–2018; they do not certify a model or a fairness level. C7
compares changes scaled by geographic yardsticks; the raw changes are reported beside D. None of the tests concerns
the original fitted classifier; they concern frozen models built by the reconstructed, harmonised pipeline.

**Why the baseline rather than 2014 alone (C1–C6):** the 2014 evaluation set is the 20% test split, so a change
measured from 2014 alone has a standard error of about 0.003 for the race DP gap, and the Bonferroni interval would
need |Δ| below about 0.002 to conclude stability for a 0.01 margin. Against the five-year baseline the standard error
is smaller (Section 7.6), and the original claim concerns the whole 2014–2018 window. C7 measures both changes from
2014, the deployment year in the original question, because accuracy has a trend within 2014–2018 that a baseline
mean would partly absorb.

## 6. Calibration constants (rules fixed; values from 2014–2018 only; frozen before archiving)

These are fixed numbers computed once from the observed 2014–2018 point estimates. The tests are conditional on
them: they do not claim to estimate a "true" historical range, and their sampling uncertainty is not propagated.

- **δ_m (temporal margin):** the largest absolute deviation of a year 2014–2018 from the baseline, for the
  seed-mean trajectory of the unconstrained model, floored at 0.01. It is the year-to-year variation the original
  paper described as "essentially constant". Values: δ_DP,race ⟨A⟩, δ_DP,sex ⟨A⟩, δ_EO,race ⟨A⟩, δ_EO,sex ⟨A⟩.
- **ε_g (historical disparity envelope):** the largest absolute seed-mean DP of the DP-post-processed model (group
  g) in any year 2014–2018, floored at 0.01. Values: ε_race ⟨A⟩, ε_sex ⟨A⟩. Per-seed values are reported.
- **G_m (geographic yardstick):** the median, over the 380 ordered pairs of the 20 largest states (2014), of the
  noise-corrected absolute change of metric m when the state-s model is applied to state s′ instead of s
  (|Δ|_c = sqrt(max(Δ² − SE², 0))), floored at 0.005 for use in C7. Values: G_DP,race ⟨A⟩, G_acc ⟨A⟩.
- **Floor 0.01** is fixed a priori as the smallest change treated as substantive; it binds only if the observed
  2014–2018 variation is smaller.
- **Margin sensitivity:** every three-way decision is also reported for margins 0.005, 0.0075, …, 0.03.
- **Formal statement.** For C1, C2, C6 with margin δ: "holds" rejects H₀: |θ| ≥ δ; "violated" rejects H₀′: |θ| ≤ δ;
  each at level α/2 (Section 7.2). For C3/C4 the same with ε. For C7: "fairness more stable" rejects H₀: D ≥ 0 and
  "accuracy more stable" rejects H₀′: D ≤ 0, with total error probability at most α.

## 7. Inference and decision rules

### 7.1 Standard errors
Unweighted metrics are smooth functions of group means; variances come from influence values. Influence values are
summed within each household (state code and SERIALNO) before squaring, so correlation between members of a household
is accounted for. This is a model-based estimator that treats households as independent draws; it is not a
reconstruction of the full ACS design (stratification, group-quarters sampling, PUMS processing), which the weighted
analysis approximates with the Census replicate weights. Estimates for different years use independent samples, so
variances add. A seed-average uses the mean of the per-seed standard errors (for two-dimensional C7, the mean of the
per-seed covariance matrices), which bounds the variance of the seed-average from above.

**Test-split estimates.** An estimate on a 20% test split carries the variability of the split. Before archiving,
`scripts/check_split_variance.py` compares, on 2018 with 200 random within-state splits, the average variance
estimate on a split (V_split) with the variance of the full-sample estimate plus the between-split variance
(V_full + S). For every metric and weighting, the variance of every training-year test-split estimate is multiplied
by max(1, (V_full + S)/V_split). Values: ⟨A⟩ (`results/validation/split_variance.json`).

### 7.2 Decisions
- **C1–C6 (three-way):** with the two-sided (1 − α) normal interval: **holds** if it lies inside [−margin, margin];
  **violated** if it lies entirely outside; **inconclusive** otherwise. If |θ| ≥ margin, P(holds) ≤ α/2; if
  |θ| ≤ margin, P(violated) ≤ α/2.
- **C7 (conservative projection interval):** a simultaneous (1 − α) box for the two changes, each side the two-sided
  (1 − α/2) normal interval (valid for any correlation); the interval for D is the exact range of D over the box.
  **Fairness more stable** if it lies below 0; **accuracy more stable** if above 0; else inconclusive. If the box
  covers the true changes, the interval covers the true D, so the probability of a wrong directional decision is at
  most α. (An earlier Monte Carlo percentile interval under-covered near zero changes in simulation and was replaced
  before archiving; D023.)
Bonferroni is used instead of Holm because it yields fixed-level intervals, which the three-way rules need.

### 7.3 Survey weights
Primary results are unweighted, as in the original. Every confirmatory test is repeated with person weights
(PWGTP), replicate-weight standard errors (SE² = 4/80 Σ_r (θ_r − θ)²) and calibration constants recomputed by the
same rules with weights. If a weighted decision differs from the unweighted one, the result is reported as
weighting-sensitive in the abstract.

### 7.4 Commitment
All outcomes of C1–C8 will be reported whatever they are, including inconclusive ones, with point estimates and
intervals, in the main text.

### 7.5 Numerical failures and ties
An estimate whose group or denominator is empty, or any non-finite estimate or standard error, is reported as
"not computable" for the affected claim (never dropped or replaced). For the geographic yardsticks, a state pair
that is not computable is recorded as such and left out of the median, and the number of such pairs is reported
(on 2014 every pair is computable: the smallest count of Black persons with income above $50,000 in a source state's
test split is 20). In C8 and 8.8, a state that is not computable is reported as such and left out of the counts.
C8 ties (equal noise-corrected changes, which the truncation at zero can produce) are counted separately.

### 7.6 Anticipated operating characteristics
At the standard errors anticipated from 2014–2018 (later year approximated by 2018 on all rows; baseline variance
Σ_t Var_t / 25), the probabilities of each decision as a function of the true θ are computed exactly and checked by
simulation (`scripts/validate_inference.py`, `results/validation/inference_validation.json`). Anticipated standard
errors and the probability of "holds" at θ = 0 (unweighted / weighted): ⟨A⟩. C7 coverage over a grid of true changes
including zeros and the boundary D = 0, at the anticipated covariance and under stress settings: minimum ⟨A⟩.

## 8. Secondary analyses (pre-specified, no family-wise claim; 95% intervals)

Secondary analyses are unweighted unless stated.

8.1 **Trajectories:** every metric for every model, years 2014–2019 and 2021–2024, with intervals, for both label
rules `>` and `>=`. Race-based values for 2021–2024 are shown separately with the comparability caveat.

8.2 **Other interventions:** ExpGrad (DP) and LFR, race, seed 0: within [−ε, ε] at 2019, with ε the largest
|DP_race| of that model in 2014–2018 (floor 0.01). For LFR, which leaves a large DP gap, this asks whether the gap
stays within its own 2014–2018 range. The EO-post-processed models (race at 2019, sex at 2024, seed means; per-seed
values reported) are assessed the same way for |EO| with ε_EO,g.

8.3 **Label definitions** (accuracy and EO; DP of a frozen model does not depend on the label):
(a) nominal `PINCP > 50000`; (b) `>=` instead of `>`; (c) inflation-anchored: PINCP > T_t, with T_t = 50000 ×
(ADJINC₂₀₁₄ / ADJINC_t) × (CPI_t / CPI₂₀₁₄) rounded to the nearest $1,000, where CPI is the annual average of the BLS
retroactive series R-CPI-U-RS (file `data/raw/cpi/r-cpi-u-rs-allitems.xlsx`, downloaded 19 Nov 2026, hash in
`logs/raw_sha256.txt`) and ADJINC the year's single income adjustment factor (asserted constant within a year).
Rounding to the $1,000 grid keeps the strict-inequality convention at a heaped value (in 2014–2018 about 80% of
incomes of $50,000 or more are multiples of $1,000); (d) base-rate-anchored: in each year, the threshold on the
$1,000 grid from $20,000 to $150,000 (strict inequality) whose unweighted positive rate is closest to the 2014
nominal positive rate; ties go to the lowest threshold; a solution at either end of the grid is flagged.

8.4 **Reweighting decomposition of change (2014 → 2019; sex also → 2024):** DiNardo–Fortin–Lemieux reweighting
splits a change into a *composition* part (2014 rows reweighted to year-t features) and a *residual* = year t −
counterfactual, which is the change in labels given features *plus approximation error* (estimation error of the
density ratio, clipping, lack of overlap). Domain classifier: scikit-learn `HistGradientBoostingClassifier`
(defaults), 5-fold cross-fitted with folds that keep households together; 2014 test rows are reweighted by the odds,
clipped at the 99.9th percentile (primary), 99th percentile and unclipped (sensitivity).
Diagnostics: domain AUC, effective sample size, largest weight relative to the mean, overlap shares, and the largest
absolute standardised mean difference of the features after reweighting within White, Black, male and female rows.
**Reliability rule:** the decomposition is interpreted only if (i) the DP residual is within ±0.005 for race and for
sex (a frozen model's DP depends only on the features, so it must be near zero), (ii) the largest group-wise
standardised mean difference is at most 0.05 (stricter than the usual 0.10 because temporal shifts are small: on
2014 → 2018 the largest group-wise difference before reweighting is about 0.05, so 0.10 could not discriminate), and (iii) the accuracy residual changes by at most 0.005 between 99.9%
clipping and no clipping. Otherwise the split is reported as unreliable and P2 is not assessed. Passing is a
necessary check, not proof that the residual is a label change. The rule was run before archiving on 2014 → 2018
(`results/stage_a/decomposition_2018_check.json`): ⟨A⟩.

8.5 **Theory predictions:**
- P1 (Chen et al. 2022): covariate shift is larger across states than over time. Shift magnitude = cross-fitted AUC
  of the domain classifier (household-grouped folds). Prediction: for most of the 20 states, AUC(s, 2014 → s, 2019)
  < median AUC(s → s′, 2014). Because place of birth separates states almost by construction (most people live in
  their state of birth), P1 is also reported with place of birth left out of the domain classifier.
- P2 (Chen et al. 2022): over time the change is mostly in the labels. Prediction: the residual in 8.4 is larger in
  magnitude than the composition part for accuracy and EO. Assessed only when 8.4 is reliable.
- P3 (Asiaee and Aryan 2026): under group-conditional prior shift alone, a frozen model's EO is unchanged and its
  DP moves with prevalence: DP(t) ≈ DP(2014) + Σ_g ± (TPR_g − FPR_g) Δπ_g, using 2014 group TPR and FPR. We report
  the predicted and observed DP changes side by side, their ratio only when the observed change exceeds 0.005 in
  absolute value (the ratio is not a share of variance), and |ΔEO| against |ΔDP|.

8.6 **Per-year-scaling pipeline:** the frozen per-year-scaling models (Section 4) against the primary models, all
metrics, all years, seed means with standard errors.

8.7 **Raw codes versus harmonised features (2014–2018):** a sensitivity contrast between two pipelines that differ
in several mappings and in their fitted models; not an identified effect of occupation recoding.

8.8 **Constraint transfer across states:** for each of the 20 per-state DP-post-processed models, |DP_race| in its own
state in 2019 against the median |DP_race| when applied to the other 19 states in 2014; we report the number of
states where the constraint transfers better over time than across states (descriptive), and the number of states
for which the comparison is computable.

8.9 **Deployment in 2018:** for the 2018-trained models, every metric's level and its change from the 2018 test
split to 2019 and 2021–2024, with standard errors (seed means). Descriptive: the 2014–2018 calibration constants do
not apply to a model deployed at the end of that window.

## 9. Known limitations and deviations policy

- Harmonisation: occupation groups are coarse and the 2018 recoding leaves residual shifts; the Cyprus mapping is an
  analyst assumption (about 60 rows a year).
- Reconstruction: the original post-processing implementation is underspecified (ours costs less accuracy than the
  published one), the original EO year-to-year pattern was not reproduced, and the published accuracy decline is
  matched only under per-year standardisation (D015). These are reported as reconstruction findings, not as
  properties of the original code.
- Standard errors: unweighted SEs are household-cluster, model-based; weighted SEs use the Census replicate weights.
  The person-level train/test split places members of one household on both sides.
- Any deviation from this plan (software failure, data revision, error found) is logged in `logs/decision_log.md`
  with date and reason and reported in the paper. Confirmatory status is kept only for analyses run as specified.
- If a frozen model file is lost or its hash does not match, it is restored from the archive; only if that fails is
  it refitted with the same code and seed, and the deviation reported.

## 10. Software, archive and reproducibility

Python 3.12, `uv.lock` (numpy 2.5.5, pandas 3.1.1, scikit-learn 1.9.1, scipy 1.17.1, fairlearn 0.15.0, aif360 0.6.1,
folktables @ ebace19). One command per stage: `bash scripts/run_all.sh stage_a` (before archiving) and
`bash scripts/run_all.sh stage_b` (after). Every step exits non-zero on failure; an exact inventory check (models,
hashes, prediction provenance, 20 states, 380 pairs) runs before every analysis; `scripts/check_outputs.py` enforces
`prereg/OUTPUT_CHECKLIST.md`.

**Archive.** Deposited on Zenodo (one immutable record) before any ACS person record for 2019 or later is
downloaded: this file; the code at the archived commit; `uv.lock`; the frozen model files; `results/models_manifest.json`;
the Stage A result files (calibration constants, stored 2014–2018 estimates, validation results); the harmonisation
report and provenance table. The repository is also saved by Software Heritage. `prereg/ARCHIVE_RECEIPT.json` records
the DOI, the Software Heritage identifier and the SHA-256 of every deposited file; `prereg/ARCHIVED` is created only
after the receipt has been checked against the deposited files. It guards against accidental access; the receipt is
the evidence of archiving. The SHA-256 of this file will be quoted in the paper.

## 11. Use of AI assistance

Analysis code and drafts were prepared with the assistance of AI models, and an AI model performed an independent
review; the author reviewed every decision and takes responsibility for the content.
