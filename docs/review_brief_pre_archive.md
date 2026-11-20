# Brief for the final pre-archive review (20 November 2026)

The Stage A rerun has finished. The run used commit `7d16f23`; its full log is `logs/stage_a_rerun_D029.txt`. Its
output gate (`scripts/check_outputs.py stage_a`) passed. The plan, `prereg/PREREGISTRATION.md`, is now v0.4,
with every numerical placeholder filled from the result files (decision log D030). This is the last review before
the plan is archived. After archiving, the later-year data will be opened.

## Rules (unchanged)

- No ACS person records for 2019 or later, and nothing that could reveal later-year results.
- 2014–2018 data, result files, code, documentation and synthetic data are allowed.
- Do not modify project files. Write your report as a separate file.

## What to check

1. **Plan against results.** Every number in the plan matches the result files:
   - `results/stage_a/margins.json`
   - `results/validation/split_variance.json`
   - `results/validation/inference_validation.json`
   - `results/stage_a/decomposition_2018_check.json`
   - the SHA-256 of `results/models_manifest.json`

   Also check that the wording around these numbers is accurate, including the interpretation of the
   joint-simulation maxima in Section 7.6.
2. **Run and outputs.** The run log shows a complete, uninterrupted run. The result files are current: run
   `scripts/check_outputs.py stage_a` yourself if possible, using a copy of the project. The model inventory is
   complete, and nothing in the outputs contradicts the plan.
3. **Fit to execute.** The plan as a whole can be archived and executed in Stage B without further decisions.
   Look for:
   - ambiguities,
   - promises the Stage B code does not keep,
   - Stage B code paths that the rehearsals did not exercise on full-size data,
   - anything that would force a deviation after the later-year data are opened.
4. **Archive procedure.** The archive procedure (`scripts/verify_archive.py build` / `verify`) is ready to use. The
   package will contain everything that has to be frozen.

## Report format

Same as before. For each finding give its severity, location, evidence and suggested fix, and mark it **blocking
before archive** or **non-blocking**. End with an archive recommendation: archive / archive after the listed fixes
/ do not archive.
