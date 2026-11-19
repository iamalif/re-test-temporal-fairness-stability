# Temporal fairness stability: a pre-registered re-test (working title)

Pre-registered re-test of the temporal fairness-stability claim in Ding, Hardt, Miller & Schmidt,
"Retiring Adult: New Datasets for Fair Machine Learning" (NeurIPS 2021), Section 4.1 and Appendix D.3,
on ACS 1-year PUMS 2014-2019 and 2021-2024.

Status: Stage A (models frozen before archiving, trained on 2014 and, for one secondary analysis, on 2018; calibration
constants from 2014-2018). Pre-registration draft: `prereg/PREREGISTRATION.md`. No ACS person record for 2019 or
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
- `paper/`     manuscript (TMLR template); `make_reconstruction_outputs.py` writes its numbers and figure
- `docs/`      brief, prior-work search records, review briefs (third-party papers in `docs/sources/` are not committed)
- `data/`      raw and derived data (not committed)
