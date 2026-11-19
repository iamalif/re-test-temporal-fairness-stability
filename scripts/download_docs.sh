#!/usr/bin/env bash
# Documentation and price index only (no person records): Census PUMS variable-change notes and the BLS
# R-CPI-U-RS all-items index (used for the inflation-anchored label, pre-registered).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw/variable_changes data/raw/cpi
VC=https://www2.census.gov/programs-surveys/acs/tech_docs/pums/variable_changes/
curl -fsL "$VC" | grep -oE 'href="[^"?/][^"]*"' | sed 's/href="//; s/"$//' | grep -iE '\.(pdf|xlsx|xls|csv|txt)$' \
  | sort -u > data/raw/variable_changes/_files.txt
while read -r f; do
  [ -s "data/raw/variable_changes/$f" ] || curl -fL --retry 3 -o "data/raw/variable_changes/$f" "$VC$f"
done < data/raw/variable_changes/_files.txt
[ -s data/raw/cpi/r-cpi-u-rs-allitems.xlsx ] || curl -fL --retry 3 -A "Mozilla/5.0 (research; contact via GitHub iamalif)" \
  -o data/raw/cpi/r-cpi-u-rs-allitems.xlsx https://www.bls.gov/cpi/research-series/r-cpi-u-rs-allitems.xlsx
find data/raw -type f ! -name '_files.txt' -print0 | sort -z | xargs -0 shasum -a 256 > logs/raw_sha256.txt
cat data/raw/variable_changes/_files.txt; ls -la data/raw/cpi; wc -l logs/raw_sha256.txt
