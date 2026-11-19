# Pre-registration: Does fairness stay put? A re-test of temporal fairness stability on ACS 2014–2024

**Status:** DRAFT v0.1 (19 Nov 2026). Not yet archived. Values marked ⟨A⟩ are filled from
`results/stage_a/margins.json` once Stage A finishes; the rules that produce them are fixed here.
**Author:** single author (name withheld in this draft).
**Archiving:** this file, `results/models_manifest.json`, `results/stage_a/margins.json` and the code at the
archived commit will be deposited on Zenodo (GitHub release) and saved by Software Heritage before any ACS person
record for 2019 or later is downloaded. The SHA-256 of this file will be quoted in the paper.

---

## 1. Claim under test

Ding, Hardt, Miller and Schmidt, *Retiring Adult: New Datasets for Fair Machine Learning* (NeurIPS 2021;
arXiv:2108.04884v3), Section 4.1 and Appendix D.3. A gradient-boosted tree trained on 2014 US-wide ACSIncome and
evaluated on 2014–2018 loses some accuracy, while its demographic-parity (DP) violation stays "stable and
essentially constant over time". A classifier that satisfies DP on 2014 data "continues to satisfy the constraint"
on 2015–2018 data, and the same holds for the interventions studied. Appendix D.3 reports the same for equality of
opportunity (EO). Section 5 asks why there appears to be more temporal than geographic stability.

We test whether these statements still hold when the 2014 models are evaluated on 2019 and 2021–2024, and whether
fairness is more stable over time than across states when both are measured on one scale.

## 2. What has been seen before archiving (exposure record)

- **Original cohort, 2014–2018 (allowed):** all person records were downloaded and analysed: data counts, feature
  distributions, the reconstruction of Figures 4 and 13 (decision log D012–D015), and every Stage A result
  (metrics of the frozen models on 2014–2018, margins and yardsticks; Section 6).
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

## 3. Data

- **Source:** US Census Bureau ACS 1-year PUMS person files (`csv_pus.zip`, 50 states + DC; `csv_ppr.zip`, Puerto
  Rico), survey years 2014–2019 and 2021–2024. Excluded: 2020 (experimental weights only; Census advises against
  comparison) and 2025 (release not available when archiving). SHA-256 of every raw file: `logs/raw_sha256.txt`.
- **Universe (folktables ACSIncome):** AGEP > 16, PINCP > 100, WKHP > 0, PWGTP ≥ 1; 50 states and Puerto Rico; DC
  excluded (it is not in folktables' state list). This reproduces folktables' row counts exactly
  (2014: 1,587,856; 2018: 1,664,500).
- **Label:** nominal `PINCP > 50000` (as folktables; no inflation adjustment). Alternatives in Section 8.3.
- **Harmonised features** (`src/harmonise.py`; derived from Census documentation only; decision log D014):
  AGEP, COW, SCHL, MAR, WKHP, SEX, RAC1P unchanged (codes identical in the 2014–2018, 2019 and 2024 dictionaries);
  occupation as 25 major groups (label prefixes of each year's own dictionary; 8 whole-code cross-group moves in the
  official crosswalk assigned their 2018 group); relationship mapped to RELP categories with roomer/boarder,
  housemate/roommate and other nonrelative merged (RELSHIPP mapped to the same categories from 2019); place of birth
  with three discontinued codes merged into regional residual codes (Census variable-change notes: Tunisia
collapsed into "Northern Africa, not specified" from 2022; South Sudan deleted in 2024; Cyprus code used only
through 2016, destination not stated, merged into "Other Europe, not specified"; about 60–190 rows a year). Missing values become 0, as in folktables.
  The harmonised scheme leaves a residual 2018 shift of at most 0.5 points in any occupation group's share
  (Section 9, recoding check).
- **Race comparability:** the race question and coding changed in 2020 (Census: compare with caution). Race-based
  confirmatory estimands therefore end in **2019**. Sex is co-primary and runs to **2024**.
- **Groups:** race, White (RAC1P = 1) minus Black (RAC1P = 2), as in the original; sex, male minus female.

## 4. Models (fitted once on 2014 and frozen before archiving)

All models are trained on the 2014 training split (within-state 80/20 random split, seeded) and saved with their
preprocessing. Their SHA-256 hashes are in `results/models_manifest.json` (hash of that file: ⟨A⟩).

- **Base model (reconstruction rule, D015):** `GradientBoostingClassifier(loss="exponential", max_depth=5,
  n_estimators=100)`. The 5 trees stated in the paper do not reproduce its figures (accuracy 0.10–0.15 below the
  published values in every year and seed). Under the preprocessing that reproduces the published accuracy curve
  (per-year standardisation), 100 trees gives the smallest mean absolute deviation from it among 50, 100 and 200
  trees (about 0.001, against 0.004 and 0.002); with 100 trees the 2014 accuracy matches the published value.
- **Preprocessing (primary):** one standardisation fitted on the 2014 training split and frozen, as a deployed model
  would use it. (Trees are invariant to it; it matters for LFR.) The original pipeline appears to have standardised
  each year separately (D012/D015); that variant is reported as a secondary analysis (Section 8.6).
- **Seeds:** unconstrained GBM and all post-processed models: seeds 0–4. ExpGrad and LFR: seed 0 (cost: about
  7.5 CPU-hours per ExpGrad fit).
- **Interventions:** (i) post-processing: fairlearn `ThresholdOptimizer` on the GBM's scores (group-specific
  thresholds; objective accuracy; randomised predictions with a fixed seed), separately for DP and EO
  (`true_positive_rate_parity`) and separately for race (RAC1P) and sex (SEX); (ii) ExpGrad: fairlearn
  `ExponentiatedGradient` with `DemographicParity`, library defaults, race; (iii) LFR: AIF360 LFR with the
  hyperparameters of the original appendix (k = 10, Ax = 0.1, Ay = 1, Az = 2, maxiter = maxfun = 5000), binary White
  indicator, base model trained on the representation. Small race categories (fewer than 100 training rows or fewer
  than 20 of either label) are pooled for the interventions; the pooled categories are recorded in the manifest.
- **Per-state models (geographic arm):** base model and DP post-processing (race) for each of the 20 largest states
  by 2014 rows (Puerto Rico excluded), trained on that state's 2014 training split, seed 0.
- **Evaluation sets:** 2014: the held-out test split of the model's seed; every other year: all rows of that year.
  For per-state models: own state 2014 test split; other states and other years: all rows of that state-year.

## 5. Confirmatory hypotheses (family of 8)

Notation: m(t) is a metric of a frozen model on year t; Δm(t) = m(t) − m(2014). Unless stated, values are the mean
over seeds 0–4, and the standard error is the mean of the per-seed standard errors (an upper bound, because the seeds
share the evaluation data). All are unweighted (primary; Section 7.3 for weighted).

| ID | Question | Model | Estimate | Year | Rule (Section 7) |
|---|---|---|---|---|---|
| C1 | Is the DP violation (race) stable? | GBM | ΔDP_race | 2019 | within ±δ_DP,race |
| C2 | Is the DP violation (sex) stable? | GBM | ΔDP_sex | 2024 | within ±δ_DP,sex |
| C3 | Does a DP-certified model (race) keep satisfying DP? | post-proc. DP, race | DP_race | 2019 | within ±ε_race |
| C4 | Does a DP-certified model (sex) keep satisfying DP? | post-proc. DP, sex | DP_sex | 2024 | within ±ε_sex |
| C5 | Is the EO violation (race) stable? | GBM | ΔEO_race | 2019 | within ±δ_EO,race |
| C6 | Is the EO violation (sex) stable? | GBM | ΔEO_sex | 2024 | within ±δ_EO,sex |
| C7 | Is fairness more stable than accuracy, on a common scale? | GBM | D = abs(ΔDP_race)/G_DP,race − abs(Δacc)/G_acc | 2019 | interval of D below / above 0 |
| C8 | Is temporal change smaller than geographic change? | per-state GBMs | sign test over 20 states | 2019 vs 2014 | Section 7.2 |

C8 in detail: for each state s, the temporal change is the noise-corrected |ΔDP_race| of the state-s model between
its 2014 test split and state s in 2019; the geographic reference is the median over the other 19 states s′ of the
noise-corrected |DP_race(s → s′) − DP_race(s → s)| in 2014 (Section 6). The indicator is 1 if temporal < geographic.

## 6. Margins and yardsticks (rules fixed; values from 2014–2018 only)

- **δ_m (temporal margin):** the largest absolute seed-mean change of metric m for the unconstrained model between
  2014 and any year 2015–2018, floored at 0.01. Rationale: this is the drift the original paper itself described as
  "essentially constant"; a change in a new year within that range is consistent with the claim.
  Values: δ_DP,race ⟨A⟩, δ_DP,sex ⟨A⟩, δ_EO,race ⟨A⟩, δ_EO,sex ⟨A⟩, δ_acc ⟨A⟩.
- **ε_g (constraint tolerance):** the largest absolute seed-mean DP of the DP-post-processed model (group g) in any
  year 2014–2018, floored at 0.01. Rationale: the band within which the original analysis would have regarded the
  constraint as satisfied. Values: ε_race ⟨A⟩, ε_sex ⟨A⟩.
- **G_m (geographic yardstick):** the median, over the 380 ordered pairs of the 20 largest states (2014), of the
  noise-corrected absolute change of metric m when the state-s model is applied to state s′ instead of s.
  Values: G_DP,race ⟨A⟩, G_acc ⟨A⟩ (all metrics in `margins.json`).
- **Noise correction:** |Δ|_c = sqrt(max(Δ² − SE², 0)).
- **Floor:** 0.01 (one percentage point) is fixed a priori as the smallest change we treat as substantive; it binds
  only if the observed 2014–2018 drift is smaller.
- **Sensitivity:** results are also reported as curves over margins 0.005–0.03.

## 7. Inference and decision rules

### 7.1 Standard errors
Unweighted metrics are smooth functions of group means; variances come from influence values. Because the ACS
samples households, influence values are summed within each household (state code and SERIALNO) before squaring,
so that correlation between members of the same household is accounted for (with independent persons this reduces to
the binomial variances behind the original Newcombe and Clopper–Pearson intervals; a simulation with clustered
outcomes confirmed that the clustered standard error matches the empirical one while the unclustered one is too
small). Estimates for different years use independent samples, so variances add. Inference is conditional on the
frozen models.

### 7.2 Decisions
Family-wise error 0.05 over C1–C8 with Bonferroni correction: α = 0.05/8 = 0.00625 per test.
- **C1–C6 (three-way):** with the two-sided (1 − α) normal interval: **holds** if it lies inside [−margin, margin];
  **violated** if it lies entirely outside; **inconclusive** otherwise.
- **C7:** interval for D from 200,000 normal draws of (ΔDP_race, Δacc) with their joint covariance (fixed seed):
  **fairness more stable** if the interval is below 0; **accuracy more stable** if above 0; else inconclusive.
- **C8:** exact two-sided binomial test on the 20 indicators at α: **temporal more stable** if significant with more
  than 10 ones (in practice at least 17 of 20); **geographic more stable** if significant with fewer than 10;
  else inconclusive.
Bonferroni is used instead of Holm because it yields fixed-level intervals, which the three-way rules need.

### 7.3 Survey weights
Primary results are unweighted, as in the original. Every confirmatory test is repeated with person weights
(PWGTP), replicate-weight standard errors (SE² = 4/80 Σ_r (θ_r − θ)²) and margins recomputed by the same rules with
weights. If a weighted decision differs from the unweighted one, the result is reported as weighting-sensitive in
the abstract.

### 7.4 Commitment
All eight outcomes will be reported whatever they are, including inconclusive ones, with point estimates and
intervals, in the main text.

## 8. Secondary analyses (pre-specified, no family-wise claim)

8.1 **Trajectories:** every metric for every model, years 2014–2019 and 2021–2024, with intervals. Race-based
values for 2021–2024 are shown separately with the comparability caveat.

8.2 **Other interventions:** ExpGrad (DP) and LFR, race, rule C3 with their own ε (same rule) at 2019.

8.3 **Label definitions** (accuracy and EO; DP of a frozen model does not depend on the label):
(a) nominal `PINCP > 50000`; (b) `>=` instead of `>`; (c) inflation-anchored: PINCP > T_t, with T_t = 50000 ×
(ADJINC₂₀₁₄ / ADJINC_t) × (CPI_t / CPI₂₀₁₄) rounded to the nearest $1,000, where CPI is the annual average of the BLS
retroactive series R-CPI-U-RS (file `data/raw/cpi/r-cpi-u-rs-allitems.xlsx`, downloaded 19 Nov 2026, hash in
`logs/raw_sha256.txt`) and ADJINC the year's single income adjustment factor. Rounding to the $1,000 grid keeps the strict-inequality
convention of the nominal label at a heaped value (in 2014–2018 about 80% of incomes of $50,000 or more are multiples
of $1,000); in 2014 the label equals the nominal one; (d) base-rate-anchored: in each year, the threshold on the
$1,000 grid (strict inequality) whose unweighted positive rate is closest to the 2014 nominal positive rate.

8.4 **Decomposition of change (2014 → 2019; sex also → 2024):** composition (covariate shift) versus change in the
label given the features, by DiNardo–Fortin–Lemieux reweighting. A gradient-boosting domain classifier (scikit-learn
`HistGradientBoostingClassifier`, default settings, 5-fold cross-fitted) separates 2014 test rows from year-t rows
on the harmonised features (race and sex included); 2014 rows are reweighted by the odds (weights clipped at the
99.9th percentile). The reweighted 2014 metric is the counterfactual "year-t features, 2014 labels given features".
Composition = counterfactual − 2014; conditional change = year t − counterfactual. **Built-in check:** a frozen
model's DP depends only on the features, so the DP conditional component must be near zero; an absolute value above
0.005 flags the reweighting as inadequate, and the decomposition is then reported as unreliable. Before archiving,
the procedure is run on 2014 → 2018 (original cohort) to confirm that the check passes on real data
(`results/stage_a/decomposition_2018_check.json`).
Exploratory extension: Shapley values over feature blocks.

8.5 **Theory predictions:**
- P1 (Chen et al. 2022): covariate shift is larger across states than over time. Shift magnitude = cross-fitted AUC
  of the domain classifier. Prediction: for most of the 20 states, AUC(s, 2014 → s, 2019) < median AUC(s → s′, 2014).
- P2 (Chen et al. 2022): over time the shift is mostly in the labels. Prediction: the conditional component in 8.4
  is larger in magnitude than the composition component for accuracy and EO.
- P3 (Asiaee and Aryan 2026): under group-conditional prior shift alone, a frozen model's EO is unchanged and its
  DP moves with prevalence: DP(t) ≈ DP(2014) + Σ_g ± (TPR_g − FPR_g) Δπ_g, using 2014 group TPR and FPR. We report
  the share of the observed DP change this formula explains, and |ΔEO| against |ΔDP|.

8.6 **Original-pipeline view:** the unconstrained model evaluated with each year standardised separately (the
preprocessing that reproduces the original figures), to show how much of the accuracy trajectory depends on it.

8.7 **Recoding artefact:** on 2014–2018 only, models on raw codes versus harmonised features; the 2018 point
crosses the occupation break in the original analysis.

## 9. Known limitations and deviations policy

- The harmonised occupation groups leave a residual 2018 shift (≤ 0.5 points per group); 2019+ changes in
  occupation-sensitive metrics are interpreted with this in mind.
- The original post-processing implementation is underspecified; ours costs less accuracy than the published one
  (D015). The original EO year-to-year pattern was not reproduced (D015). Both are reported as reproduction findings.
- Any deviation from this plan (software failure, data revision, error found) is logged in `logs/decision_log.md`
  with date and reason and reported in the paper. Confirmatory status is kept only for analyses run as specified.
- If a frozen model file is lost or its hash does not match, it is refitted with the same code and seed and the
  deviation is reported.

## 10. Software and reproducibility

Python 3.12, `uv.lock` (numpy 2.5.5, pandas 3.1.1, scikit-learn 1.9.1, scipy 1.17.1, fairlearn 0.15.0, aif360 0.6.1,
folktables @ ebace19). One command per stage (`scripts/stage_a.py`, Stage B evaluation script). Every number in the
paper is generated from result files. Data are not redistributed; the harmonised loader and code will be released.

## 11. Use of AI assistance

Analysis code and drafts were prepared with the assistance of AI models; the author reviewed every decision and
takes responsibility for the content.
