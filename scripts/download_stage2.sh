#!/usr/bin/env bash
# Stage 2 downloads: 2019 and 2021-2024 person files (50 states + DC, and Puerto Rico).
# Refuses to run until the pre-registration has been archived (prereg/ARCHIVED, created after archiving).
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f prereg/ARCHIVED ] || { echo "Refusing: prereg/ARCHIVED not found. Archive the pre-registration first."; exit 1; }
PUMS=https://www2.census.gov/programs-surveys/acs/data/pums
for Y in 2019 2021 2022 2023 2024; do
  mkdir -p data/raw/$Y
  for F in csv_pus.zip csv_ppr.zip; do
    [ -s data/raw/$Y/$F ] || curl -fL --retry 3 -o data/raw/$Y/$F "$PUMS/$Y/1-Year/$F"
  done
done
find data/raw -type f ! -name '_files.txt' -print0 | sort -z | xargs -0 shasum -a 256 > logs/raw_sha256.txt
echo "Downloaded. Logged $(wc -l < logs/raw_sha256.txt) raw-file hashes."
