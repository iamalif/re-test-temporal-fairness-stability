# Disposition of the final independent pre-archive review (20 Nov 2026)

Report: `docs/qa_final_pre_archive_review_2026-11-20.md` (reviewed HEAD e612952; Stage A run commit 7d16f23).
Recommendation of the reviewer: archive after correcting PA-1; no refit; PA-2 to PA-4 non-blocking.
Decision log: D031. No fitting, prediction, analysis or validation code changed; no Stage A output changed.

| Finding | Severity | Disposition |
|---|---|---|
| PA-1 combined-error interpretation (plan 7.6) | major, blocking | **Fixed.** Plan 7.6 now reports the largest false-"holds" rate (0.0055, MC SE 0.0005; within its registered tolerance), the largest false-"violated" rate (0.0050), and the largest probability of either error at the boundary (0.0094, MC SE 0.0007, about 1.6 MC SE above 0.05/6). The boundary-cell mean 0.0038 is kept as descriptive only; "beyond the margin" replaced by "among grid points with abs(theta) > 0.01, the largest false-'holds' rate is 0.00035". No uniform or conditional guarantee is claimed. The incorrect sentence in D030 is superseded by D031 (the log is append-only). Acceptance criteria and results unchanged. |
| PA-2 archive not self-contained for reference inputs | minor | **Fixed.** The shared inventory now includes the non-person reference inputs under `data/raw/dictionaries`, `data/raw/crosswalk`, `data/raw/variable_changes` and `data/raw/cpi` (40 files, about 12 MB; US government documents) and a `LICENSE` file. No Census person file is packaged. Archive tests rerun: 9/9 pass; inventory 251 members. |
| PA-3 P1 production-scale runtime | minor | **Recorded; no code change.** P1 will run in full in Stage B with its fixed states, folds, seeds and comparisons; progress is logged; `--skip-p1` is not an acceptable final deliverable (the Stage B gate requires both P1 outputs). A runtime failure leads to a rerun of the same computation, never to omitting or changing P1. |
| PA-4 stale descriptive details | minor | **Fixed.** Exposure record: five rounds plus the final pre-archive review; earlier rounds opened no person records; the final pass read permitted 2014–2018 columns; no 2019+ record accessed. Model size 126,749,100 bytes. |

Also changed for the deposit: plan status set to "v1.0, frozen for archiving"; the DOI and Software Heritage
identifier are recorded in `prereg/ARCHIVE_RECEIPT.json` and `prereg/ARCHIVED`, which are outside the package.
