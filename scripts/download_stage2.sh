#!/usr/bin/env bash
# Stage 2 downloads: 2019 and 2021-2024 person files (50 states + DC, and Puerto Rico; both required).
# Refuses to run until the pre-registration has been archived (prereg/ARCHIVED, created after archiving).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f prereg/ARCHIVED ] || { echo "Refusing: prereg/ARCHIVED not found. Archive the pre-registration first."; exit 1; }
source scripts/_fetch.sh
PUMS=https://www2.census.gov/programs-surveys/acs/data/pums
for Y in 2019 2021 2022 2023 2024; do
  for F in csv_pus.zip csv_ppr.zip; do fetch "$PUMS/$Y/1-Year/$F" "data/raw/$Y/$F"; done
done
bash scripts/log_raw_hashes.sh
echo "Downloaded. Logged $(wc -l < logs/raw_sha256.txt) raw-file hashes."
