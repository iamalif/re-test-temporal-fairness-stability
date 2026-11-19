# Brief for an independent review of the pre-registration (draft v0.1, 19 Nov 2026)

You are asked to review, critically and independently, a pre-registration for a re-test of a published claim.
You did not write it. Assume it contains errors. Your job is to find them before the plan is frozen.

## Where everything is
Public repository: https://github.com/iamalif/re-test-temporal-fairness-stability (branch `main`).
Read in this order:
1. `prereg/PREREGISTRATION.md` — the plan under review.
2. `logs/decision_log.md` — every decision so far with its reason (D001–D016).
3. Code the plan relies on: `src/data.py` (loading, filters), `src/harmonise.py` (code harmonisation),
   `src/pipeline.py` (models, frozen predictors), `src/analysis.py` (estimates, standard errors, decision rules),
   `scripts/stage_a.py`, `scripts/stage_a_analysis.py` (margins), `scripts/stage_b_confirmatory.py` (tests).
4. Reconstruction evidence: `results/reconstruction/comparison.csv`, `figure4_digitised.json`,
   `figure13_digitised.json`, `scripts/digitise_figure4.py`.
5. The paper under test: Ding, Hardt, Miller, Schmidt, "Retiring Adult" (arXiv:2108.04884v3), Section 4.1,
   Appendix C, Appendix D.3, Figures 4 and 13.

## Hard rule
Do **not** look up, download, compute on, or report any American Community Survey result for survey years 2019 or
later (person-level data, published metrics, other papers' post-2018 results, repositories' results files). If you
see one by accident, say so and do not repeat it. Your review must be based on the plan, the code and 2014–2018
material only.

## What to check (report every issue you find; these are the minimum)
1. **Validity of the claim operationalisation.** Do C1–C8 test what the original paper claims (Section 1 of the
   plan)? Is anything claimed in the original left untested or tested in a way its authors would reject?
2. **Margins (Section 6).** Are δ (largest 2014–2018 drift, floor 0.01), ε (largest post-processed DP in
   2014–2018, floor 0.01) and G (median noise-corrected cross-state change) defensible, free of post-2018
   information, and not chosen to make any outcome more likely? Is the 0.01 floor justified? Would a reviewer call
   any margin arbitrary or self-serving?
3. **Statistics (Section 7, `src/analysis.py`).** Influence-function variances; independence across years;
   seed averaging with the mean per-seed SE; Bonferroni with three-way intervals; the C7 Monte Carlo interval of a
   difference of absolute values; the C8 sign test and its power with 20 states; noise correction
   sqrt(max(Δ² − SE², 0)); replicate-weight formula. Point out anything incorrect, anti-conservative, or
   underpowered.
4. **Data and harmonisation (Section 3, `src/harmonise.py`).** Is grouping occupation into 25 major groups adequate?
   Is the RELSHIPP → RELP mapping correct against the Census dictionaries? Is ending race estimands in 2019
   sufficient given the 2020 race-coding change? Any other break between 2014 and 2024 we missed (e.g. top-coding,
   income rounding, group-quarters, weighting method changes)?
5. **Models (Section 4).** Is the reconstruction rule (100 trees) justified by the evidence in D012–D015? Is using
   a frozen common standardisation as the primary pipeline defensible given that the original seems to have
   standardised per year? Is the pooling of small race categories for the interventions acceptable?
6. **Code–plan consistency.** Does the code implement exactly what the plan says? List every mismatch (e.g.
   evaluation sets, seeds, which years, which groups, weighting, label rules).
7. **Secondary analyses (Section 8).** Are the label definitions, the DFL decomposition with its built-in DP check,
   and the theory predictions P1–P3 specified precisely enough to be run without further choices?
8. **Contamination and timing.** Is anything in the plan informed by post-2018 information? Is the exposure record
   (Section 2) complete and honest?
9. **Publishability.** As a TMLR reviewer: what would make you reject or demand major revisions? What single change
   would most improve the study?

## Output format
A numbered list of issues, most severe first. For each: location (section or file:line), the problem, why it
matters, and a concrete fix. Mark each as **must-fix before archiving**, **should-fix**, or **minor**. End with a
one-paragraph overall judgement. Do not rewrite the plan yourself.
