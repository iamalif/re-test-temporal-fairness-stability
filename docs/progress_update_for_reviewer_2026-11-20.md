# Progress update for the independent reviewer — 20 November 2026

Thank you for the first review (`docs/qa_independent_1_report.md`). This note says what has changed since then
and asks for a second review. The detailed responses are in `docs/qa_independent_1_disposition.md`, and the
reasons are in `logs/decision_log.md`, entries D023 to D025. Please verify the changes yourself rather than taking
these documents at their word.

## Where the project stands

- The plan is still not archived. No ACS person record for 2019 or later has been opened.
- The code, plan and manuscript have been revised. The plan is now `prereg/PREREGISTRATION.md`, v0.3.
- A full Stage A rerun has not started yet. It will refit every model trained on harmonised 2014 features,
  including ExpGrad, and takes about 6–7 hours. Until it finishes, the files in `results/stage_a/` and
  `results/validation/` are from the previous models, and the plan still has ⟨A⟩ placeholders.

## Main changes (summary; details in the disposition file)

1. **Confirmatory family.**
   - The family is now C1, C2, C3, C4, C6 and C7, each tested at α = 0.05/6.
   - C8 (the 20-state comparison) is now descriptive, and no significance test is run on it.
   - C5 (equality-of-opportunity gap by race) is now secondary. At its anticipated standard error, a "holds"
     decision is nearly unreachable even if the true change is zero.
2. **C7 interval.**
   - The old interval was Monte Carlo percentiles. In simulation it covered the true value only about 93% of
     the time near zero changes.
   - The new interval is the exact range of D over a simultaneous Bonferroni box for the two changes. The
     geographic yardsticks are fixed calibration constants with a floor of 0.005.
   - Simulated coverage is at least 0.995 (`scripts/validate_inference.py`).
3. **C3/C4** are now described as retention of each model's historical disparity range (2014–2018), measured as
   the seed-average signed gap. Per-seed values are reported alongside.
4. **Randomised predictors** are evaluated through their expected predictions (positive-class probabilities).
5. **Split variance.** A pre-specified check, run on 2018 with 200 random splits, sets a variance multiplier for
   every estimate made on a 20% test split.
6. **Harmonisation bug, found by the implementing side.**
   - Five 2010 occupation codes were assigned to a destination group although each is split across 2018 codes,
     one of them in its own group. This contradicts the mapping's stated rule. It affected 0.33% of rows.
   - The set of moved codes is now re-derived from the Census crosswalk, and the run fails if the code
     disagrees.
   - This fix is why every harmonised model is being refitted.
   - A provenance table for every mapping is in `docs/harmonisation_provenance.md`.
7. **New frozen per-year-scaling models.** These are for secondary analysis 8.6, which before compared an
   improvised variant.
8. **Reconstruction figure corrected.** The share of the published accuracy decline attributed to preprocessing
   is now the paired contrast within our reconstruction: 0.0075, or 29.5% of the published decline. It is no
   longer presented as an attribution to the original code.
9. **Provenance and failure handling.**
   - Model hashes are verified whenever a model is loaded.
   - Every prediction file carries a provenance record that is checked before use.
   - Files are written atomically.
   - An exact inventory check runs before every analysis.
   - Any failed step exits with an error.
   - Puerto Rico is mandatory.
   - Downloads are checked for integrity.
   - Tamper tests: `scripts/test_integrity.py`.
10. **Decomposition.**
    - Cross-fitting folds keep households together.
    - Overlap, effective-sample-size and group-wise balance diagnostics are reported.
    - Clipping sensitivity is reported.
    - A pre-specified reliability rule decides whether P2 is assessed.
    - The balance threshold was tightened from 0.10 to 0.05 after seeing that on real 2014→2018 data the
      imbalance before reweighting is already at most 0.051 (D024).
11. **Place of birth in P1.** P1 is also reported without place of birth, because place of birth separates states
    almost by construction.
12. **Output checklist.** Every promised output is listed in `prereg/OUTPUT_CHECKLIST.md`, and
    `scripts/check_outputs.py` checks them.
13. **Rehearsal (D024).** The whole chain was run on real 2014–2018 subsamples, with synthetic stand-ins for the
    later years and fewer trees. It exposed four small robustness bugs, all now fixed.
14. **Second audit (D025).** The data dictionaries for 2017–2024 were compared code by code, and the harmonised
    2014–2018 data checked for missing values and unknown codes. The manuscript compiles cleanly. This audit
    changed no fitting or prediction code.

## What I am asking for

Please do a second independent, critical review following `docs/review_brief_independent_qa_2.md`. The rules
are unchanged: no 2019+ person records or outcome-revealing sources, and no edits to project files.

**One request about timing.** The long refit is planned for tomorrow morning. It would help most if you first
report anything that would change the **fitted models or their predictions**, since such problems would need
another 6–7-hour refit after the run. Examples: feature harmonisation, the training data and split, the model or
intervention settings, how predictions are produced or stored, and the model inventory. Please flag these at the
top of your report as "refit-relevant", even when they are uncertain.

Analysis-only issues can be fixed after the run without refitting. These include decision rules, inference,
outputs, the plan's wording and the manuscript.
