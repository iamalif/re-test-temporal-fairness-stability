#!/usr/bin/env bash
# Rebuild everything from the raw Census files, in order. Each step is resumable.
#   bash scripts/run_all.sh stage_a     # before archiving (2014-2018 only)
#   bash scripts/run_all.sh stage_b     # after archiving (needs prereg/ARCHIVED)
set -euo pipefail
cd "$(dirname "$0")/.."
PY="uv run python -W ignore"
case "${1:-}" in
  stage_a)
    bash scripts/download_stage1.sh
    bash scripts/download_docs.sh || echo "note: download the BLS CPI file manually if blocked (see D017)"
    $PY src/data.py 2014 2015 2016 2017 2018
    $PY scripts/digitise_figure4.py docs/sources/ding2021_arxiv_v3.pdf
    $PY scripts/reconstruct.py --plan all --jobs 6
    $PY scripts/compare_reconstruction.py
    $PY scripts/make_reconstruction_outputs.py
    $PY scripts/harmonisation_report.py
    $PY scripts/stage_a.py fit --jobs 6
    $PY scripts/stage_a.py predict --jobs 5
    $PY scripts/stage_a_analysis.py
    $PY scripts/check_decomposition_2018.py
    ;;
  stage_b)
    [ -f prereg/ARCHIVED ] || { echo "prereg/ARCHIVED missing: archive the pre-registration first"; exit 1; }
    bash scripts/download_stage2.sh
    $PY src/data.py 2019 2021 2022 2023 2024
    $PY scripts/stage_a.py predict --jobs 5 --years 2019 2021 2022 2023 2024
    $PY scripts/stage_b_confirmatory.py
    $PY scripts/stage_b_secondary.py
    ;;
  *) echo "usage: bash scripts/run_all.sh stage_a|stage_b"; exit 2 ;;
esac
