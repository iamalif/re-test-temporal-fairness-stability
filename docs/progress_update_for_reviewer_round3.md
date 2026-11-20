# Progress update for the independent reviewer — round 3 (20 November 2026)

Thank you for the second review (`docs/qa_independent_round_2_report.md`). Every finding was accepted. The
point-by-point response is in `docs/qa_independent_round_2_disposition.md`, and the reasons are in decision log
entry D026. As before, please check the changes in the code and files themselves, not in these summaries.

## State

- The plan is not archived. No ACS person record for 2019 or later has been opened.
- The Stage A rerun has **not** started. It will refit all 98 models (88 earlier plus 10 new no-race models; ExpGrad
  included). Until it finishes, the files in `results/stage_a/` and `results/validation/` are stale. The exceptions
  are `analysis_tests.json` and `fetch_tests.json`, which are synthetic tests and current. The plan still contains
  ⟨A⟩ placeholders.
- The new freshness gate (`scripts/check_outputs.py`) will now reject the stale Stage A files, as intended.

## What changed in response to round 2

- **R1 (provenance)**
  - Every model records a fit-specification hash that covers its job, features and mappings, hyperparameters,
    training-data hash, split and fitting code (as an AST hash), and library versions. A model is "current" only
    if this hash and its file hash both match.
  - Every prediction records a prediction-specification hash, which is checked on use. `load_pred` also checks
    the model hash against the current manifest.
  - Every script that consumes predictions now runs the inventory check first.
  - Derived data files are bound to the hashes of their raw files and to the build code.
- **R2 (row identity)**
  - The row key is now person-level: state, serial number and person number (ST, SERIALNO, SPORDER).
  - Uniqueness is asserted before predictions are made.
  - A new tamper test swaps two persons of one household.
- **R3 (race as an input)**
  - Race stays an input of the primary models, for fidelity to the original.
  - The plan now states that the sex endpoints include any effect of the 2020 race-measurement change.
  - Frozen no-race models (base model and sex DP post-processing, 5 seeds) feed the new secondary analysis 8.10.
- **R4 (crosswalk)**
  - A code with any unresolved destination is never treated as a whole move. Such codes are listed for audit.
  - The three registered moves are unchanged.
- **A1 (target of inference)**
  - The target is stated explicitly as the population 2014–2018 baseline, with the calibration constants fixed
    at their realised values. The plan no longer claims exact coverage.
  - A joint simulation redraws the history, the calibration, the baseline and the later year together, and is
    judged against registered acceptance criteria.
- **A2 (split variance)** The split variance is calibrated over 15 configurations, with K = 400 splits, a one-sided
  upper bound and the maximum multiplier across configurations. It is described as an empirical calibration, not a
  derivation.
- **A3 (one estimate builder)** One function builds all estimates. A check confirms that the same estimate agrees
  across output tables.
- **A4 (balance check)**
  - Balance is now measured on category-share indicators, with a sampling-noise allowance.
  - The clipping check now covers accuracy and both EO gaps.
  - Calibrated on the real 2014→2018 data: every group fails before reweighting and passes after.
- **A5 (downloads)** The download check takes the file format from the destination name, so `.part` files are
  checked correctly. XLS files are recognised by their signature. Synthetic fixtures test both.
- **A6 (failure handling)** Failures are now metric-local, C7 validates its inputs, and 12 synthetic tests cover
  these cases.
- **A7 (stale outputs)** Every result file carries a provenance block. The checker re-verifies the current state
  and rejects stale files.
- **A8** The false-"violated" bound is now stated as α, not α/2.
- **A9** The wording was fixed throughout, and `scripts/verify_archive.py` now checks the archive receipt against
  the public Zenodo record.

**Rehearsal.** The whole chain was run again with the final code. It used real 2014–2018 subsamples, synthetic
stand-ins for the later years built from 2018 rows, and 30 trees per model. The Stage A gate passes. The Stage B
gate passes except for P1, which was skipped for time; P1 was run separately on 3 states.

## Request

Please do a third independent, critical review with the same rules and report format as before, following
`docs/review_brief_independent_qa_2.md`. In Part 1, verify the round-2 dispositions instead of the round-1 ones.

As last time, the 6–7-hour refit is next. Please put anything that would change the fitted models or their
predictions at the top of your report, marked **refit-relevant**. That covers features, training data, split,
estimator settings, prediction convention, model inventory and fit/prediction specifications.
