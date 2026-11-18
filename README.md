# Temporal fairness stability: a pre-registered re-test (working title)

Pre-registered re-test of the temporal fairness-stability claim in Ding, Hardt, Miller & Schmidt,
"Retiring Adult: New Datasets for Fair Machine Learning" (NeurIPS 2021), Section 4.1 and Appendix D.3,
on ACS 1-year PUMS 2014-2019 and 2021-2024.

Status: planning. No ACS person record for 2019 or later has been downloaded or examined.

## Layout
- `docs/`      brief, collaboration rules, prior-work search records
- `prereg/`    pre-registration (archived with a third-party timestamp before any 2019+ data)
- `logs/`      append-only decision log, exposure log, raw-file hashes
- `src/`       library code (loader, harmonisation, metrics)
- `scripts/`   entry points; one command rebuilds everything from raw data
- `data/`      raw and derived data (not committed)
- `results/`   result files; every number in the paper is generated from these
- `paper/`     manuscript
