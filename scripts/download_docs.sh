#!/usr/bin/env bash
# Documentation and price index only (no person records): Census PUMS variable-change notes and the BLS
# R-CPI-U-RS all-items index (used for the inflation-anchored label, pre-registered).
# Exit codes: 0 ok; 3 = only the CPI file is missing (BLS blocks scripted downloads; get it manually, see D017);
# anything else = a real failure.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/_fetch.sh
mkdir -p data/raw/variable_changes data/raw/cpi logs
VC=https://www2.census.gov/programs-surveys/acs/tech_docs/pums/variable_changes/
curl -fsL "$VC" | grep -oE 'href="[^"?/][^"]*"' | sed 's/href="//; s/"$//' | grep -iE '\.(pdf|xlsx|xls|csv|txt)$' \
  | sort -u > data/raw/variable_changes/_files.txt.part
[ -s data/raw/variable_changes/_files.txt.part ] || { echo "variable-change listing is empty" >&2; exit 1; }
mv -f data/raw/variable_changes/_files.txt.part data/raw/variable_changes/_files.txt
while read -r f; do fetch "$VC$f" "data/raw/variable_changes/$f"; done < data/raw/variable_changes/_files.txt
cpi_rc=0
fetch https://www.bls.gov/cpi/research-series/r-cpi-u-rs-allitems.xlsx data/raw/cpi/r-cpi-u-rs-allitems.xlsx \
  -A "Mozilla/5.0 (research; contact via GitHub iamalif)" || cpi_rc=3
bash scripts/log_raw_hashes.sh
cat data/raw/variable_changes/_files.txt; ls -la data/raw/cpi; wc -l logs/raw_sha256.txt
if [ $cpi_rc -ne 0 ]; then
  echo "CPI file missing: download https://www.bls.gov/cpi/research-series/r-cpi-u-rs-allitems.xlsx in a browser" \
       "and save it as data/raw/cpi/r-cpi-u-rs-allitems.xlsx, then re-run." >&2
  exit 3
fi
