# Temporal fairness stability: a pre-registered re-test (working title)

Pre-registered re-test of the temporal fairness-stability claim in Ding, Hardt, Miller & Schmidt,
"Retiring Adult: New Datasets for Fair Machine Learning" (NeurIPS 2021), Section 4.1 and Appendix D.3,
on ACS 1-year PUMS: the original cohort 2014-2018 and the new years 2019 and 2021-2024 (2020 is excluded: the 2020
1-year data have experimental weights only).

Status: Stage A (models frozen before archiving, trained on 2014 and, for one secondary analysis, on 2018; calibration
constants from 2014-2018). Pre-registration: `prereg/PREREGISTRATION.md` (v1.0; archived on Zenodo before any later
data are accessed; DOI, archived commit and Software Heritage identifier in `prereg/ARCHIVE_RECEIPT.json`). No ACS person record for 2019 or
later has been downloaded or examined; `src/data.py` refuses those years until `prereg/ARCHIVED` exists.

## Reproduce
Environment: `uv sync` (Python 3.12, versions pinned in `uv.lock`).
- `bash scripts/run_all.sh stage_a` - original cohort: download, reconstruction of Figures 4 and 13,
  harmonisation report, frozen models, calibration constants, validation checks (before archiving).
  Every step exits non-zero on failure; `scripts/check_outputs.py` checks the promised outputs.
- `bash scripts/run_all.sh stage_b` - after archiving: 2019 and 2021-2024, confirmatory and secondary analyses.

## Layout
- `prereg/`    pre-registration (archived with a third-party timestamp before any 2019+ data)
- `logs/`      append-only decision log, raw-file hashes
- `src/`       loader (`data.py`), harmonisation, pipeline (frozen models), estimators and decision rules
- `scripts/`   entry points (see `run_all.sh` for the order)
- `results/`   result files (every number in the paper is generated from these)
- `paper/`     manuscript (TMLR template); `scripts/make_reconstruction_outputs.py` writes its numbers and figure
- `docs/`      brief, prior-work search records, review briefs (third-party papers in `docs/sources/` are not committed)
- `data/`      raw and derived data (not committed)

## Licence
Code: MIT. Text, results and figures: CC BY 4.0. Third-party US government files keep their own terms. See `LICENSE`.
