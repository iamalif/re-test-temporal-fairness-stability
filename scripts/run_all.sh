#!/usr/bin/env bash
# Rebuild everything from the raw Census files, in order. Each step is resumable and every step must succeed.
#   bash scripts/run_all.sh stage_a     # before archiving (2014-2018 only)
#   bash scripts/run_all.sh stage_b     # after archiving (needs prereg/ARCHIVED)
set -euo pipefail
cd "$(dirname "$0")/.."
PY="uv run python -W ignore"
case "${1:-}" in
  stage_a)
    bash scripts/test_fetch.sh          # download integrity checks on synthetic files
    $PY scripts/test_analysis.py        # estimator, decision-rule and balance-gate tests on synthetic data
    $PY scripts/test_archive.py         # archive verifier on a synthetic package with a mocked Zenodo record
    bash scripts/download_stage1.sh
    bash scripts/download_docs.sh       # exits 3 with instructions if only the CPI file must be fetched by hand
    $PY src/data.py 2014 2015 2016 2017 2018 --overwrite    # rebuild with build provenance (byte-identical, D027)
    $PY scripts/test_specs.py           # specification-sensitivity and lineage tests (reads data-file hashes)
    $PY scripts/digitise_figure4.py docs/sources/ding2021_arxiv_v3.pdf
    $PY scripts/reconstruct.py --plan all --jobs 6
    $PY scripts/compare_reconstruction.py
    $PY scripts/make_reconstruction_outputs.py
    $PY scripts/harmonisation_report.py
    $PY scripts/stage_a.py fit --jobs 6
    $PY scripts/stage_a.py predict --jobs 5
    $PY scripts/export_inference_only.py   # audit; inference-only model files (D033)
    $PY scripts/stage_a.py verify
    $PY scripts/check_split_variance.py
    $PY scripts/stage_a_analysis.py
    $PY scripts/check_decomposition_2018.py
    $PY scripts/validate_inference.py
    RT_SMOKE_ROWS=20000 RT_SMOKE_TAG=it $PY scripts/stage_a.py fit --jobs 4
    RT_SMOKE_ROWS=20000 RT_SMOKE_TAG=it $PY scripts/stage_a.py predict --jobs 3
    RT_SMOKE_ROWS=20000 RT_SMOKE_TAG=it $PY scripts/test_integrity.py
    $PY scripts/check_outputs.py stage_a
    ;;
  stage_b)
    [ -f prereg/ARCHIVED ] || { echo "prereg/ARCHIVED missing: archive the pre-registration first"; exit 1; }
    bash scripts/download_stage2.sh
    $PY src/data.py 2019 2021 2022 2023 2024
    $PY scripts/stage_a.py predict --jobs 5 --years 2019 2021 2022 2023 2024
    $PY scripts/stage_b_confirmatory.py
    $PY scripts/stage_b_secondary.py
    $PY scripts/check_outputs.py stage_b
    ;;
  *) echo "usage: bash scripts/run_all.sh stage_a|stage_b"; exit 2 ;;
esac
