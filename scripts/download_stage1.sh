#!/usr/bin/env bash
# Stage 1 downloads: ORIGINAL COHORT ONLY (2014-2018 person files), documentation for all years, papers.
# Never add 2019+ person files here. They are downloaded only after the pre-registration is archived (stage 2).
set -euo pipefail
cd "$(dirname "$0")/.."
PUMS=https://www2.census.gov/programs-surveys/acs/data/pums
DICT=https://www2.census.gov/programs-surveys/acs/tech_docs/pums/data_dict/

# 1. US-wide 1-year person files, 2014-2018 (about 600 MB each)
for Y in 2014 2015 2016 2017 2018; do
  mkdir -p data/raw/$Y
  [ -s data/raw/$Y/csv_pus.zip ] || curl -fL --retry 3 -o data/raw/$Y/csv_pus.zip "$PUMS/$Y/1-Year/csv_pus.zip"
  # Puerto Rico is not in the US-wide file but is part of folktables' US-wide data (50 states + PR)
  [ -s data/raw/$Y/csv_ppr.zip ] || curl -fL --retry 3 -o data/raw/$Y/csv_ppr.zip "$PUMS/$Y/1-Year/csv_ppr.zip"
done

# 2. Data dictionaries (documentation only; allowed for every year)
curl -fsL "$DICT" | grep -oE 'href="[^"]+"' | sed 's/href="//; s/"$//' \
  | grep -iE 'PUMS_Data_Dictionary_(2014|2015|2016|2017|2018|2019|2021|2022|2023|2024)' \
  | grep -viE '5-?yr|5yr|2015-2019|2019-2023|2018-2022|2020' | sort -u > data/raw/dictionaries/_files.txt
while read -r f; do
  [ -s "data/raw/dictionaries/$f" ] || curl -fL --retry 3 -o "data/raw/dictionaries/$f" "$DICT$f"
done < data/raw/dictionaries/_files.txt

# 3. 2018 occupation code list and crosswalk
[ -s data/raw/crosswalk/2018-occupation-code-list-and-crosswalk.xlsx ] || curl -fL --retry 3 \
  -o data/raw/crosswalk/2018-occupation-code-list-and-crosswalk.xlsx \
  https://www2.census.gov/programs-surveys/demo/guidance/industry-occupation/2018-occupation-code-list-and-crosswalk.xlsx

# 4. Papers (kept locally, not committed)
S=docs/sources
get(){ [ -s "$S/$1" ] || curl -fL --retry 3 -A "Mozilla/5.0" -o "$S/$1" "$2"; }
get ding2021_neurips.pdf      https://proceedings.neurips.cc/paper/2021/file/32e54441e6382a7fbacbbbaf3c450059-Paper.pdf
get ding2021_supplement.pdf   https://proceedings.neurips.cc/paper_files/paper/2021/file/32e54441e6382a7fbacbbbaf3c450059-Supplemental.pdf
get ding2021_arxiv_v3.pdf     https://arxiv.org/pdf/2108.04884v3
get chen2022_arxiv.pdf        https://arxiv.org/pdf/2206.00129
get asiaee_aryan2026.pdf      https://arxiv.org/pdf/2602.05144
get facchini2026.pdf          https://arxiv.org/pdf/2611.20901

# 5. Hashes of every raw file (committed)
find data/raw -type f ! -name '_files.txt' -print0 | sort -z | xargs -0 shasum -a 256 > logs/raw_sha256.txt
echo "Done."; cat data/raw/dictionaries/_files.txt; ls -la $S; wc -l logs/raw_sha256.txt
