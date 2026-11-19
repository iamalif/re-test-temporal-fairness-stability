# Brief for independent review, round 2

You reviewed this project once (`docs/qa_independent_1_report.md`). The implementing side has responded
(`docs/qa_independent_1_disposition.md`, decision log entry D023 in `logs/decision_log.md`) and changed code, plan
and manuscript. This round has two parts. Please treat both as an independent, critical review: do not assume a
change is correct because the disposition says so, and do not limit yourself to the earlier findings.

## Rules (unchanged)

- Do not open, download or compute on any ACS person record for 2019 or later, and do not read any result that
  could reveal later-year outcomes (including papers or repositories reporting post-2018 folktables results).
  The plan is not archived yet.
- 2014–2018 data, Stage A results, documentation, code and synthetic data are allowed.
- Do not modify project files; write your report as a separate file.

## Part 1: verify each disposition

For each of the 20 earlier findings, state whether the response resolves it, partly resolves it, or does not, citing
code (file and function) or result files. Where a response narrows a claim instead of changing the method, judge
whether the narrower claim is stated consistently in the plan (`prereg/PREREGISTRATION.md`), the code and the
manuscript (`paper/main.tex`).

## Part 2: fresh review of the changed and new material

Including, but not limited to:
- `src/analysis.py` (decision rules, C7 interval, split-variance multipliers, failure policy) and
  `scripts/validate_inference.py` with its output.
- `src/pipeline.py` (expected predictions, provenance records, inventory check, per-year-scaling models, mapping
  fingerprint) and `scripts/stage_a.py`, `scripts/test_integrity.py` with its output.
- `src/harmonise.py`, `scripts/harmonisation_report.py`, `docs/harmonisation_provenance.md` (including the mapping
  correction described in D023).
- `scripts/check_split_variance.py` and its output; `scripts/stage_a_analysis.py` and the Stage A outputs.
- `scripts/stage_b_confirmatory.py`, `scripts/stage_b_secondary.py`, `scripts/check_decomposition_2018.py` and its
  output, `scripts/check_outputs.py`, `prereg/OUTPUT_CHECKLIST.md`.
- Reconstruction scripts and `paper/numbers_reconstruction.tex`.
- The plan as a whole: is it complete and unambiguous enough to be archived and executed without further
  decisions? Is anything promised that the code does not produce, or produced that the plan does not define?

## Report format

Same as round 1: findings ordered by severity (critical, major, minor, question), each with location,
evidence, why it matters and a suggested fix; a list of things checked and found sound; and an archive
recommendation (archive / archive after listed fixes / do not archive).
