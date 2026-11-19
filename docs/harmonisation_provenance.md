# Harmonisation provenance (src/harmonise.py)

Every mapping, its source, and whether Census documents it or it is an analyst assumption. "Rows" are 2014–2018
person rows in the ACSIncome universe (from `results/harmonisation/report_2014_2018.json`). Sources:
PUMS data dictionaries (`data/raw/dictionaries/`: single-year CSV dictionaries 2017, 2018, 2019, 2021–2024 and the
multi-year CSV dictionaries 2014–2018 and 2017–2021); the 2018 Census occupation code list and crosswalk
(`data/raw/crosswalk/2018-occupation-code-list-and-crosswalk.xlsx`, sheet "Occ Code Changes"); the PUMS
variable-change notes (`data/raw/variable_changes/`). Hashes of all files: `logs/raw_sha256.txt`.

| Feature | Mapping | Years applied | Source | Type | Rows affected |
|---|---|---|---|---|---|
| AGEP, COW, SCHL, MAR, WKHP, SEX, RAC1P | none (identity) | all | dictionaries: identical code lists 2014–2018, 2019, 2024 | documented | — |
| RAC1P | not recoded; race estimands end in 2019 | — | Census 2020 race question and coding change | documented caveat | — |
| OCCP → major group | three-letter prefix of each code's label in that year's own dictionary (2017 dictionary for 2014–2016, which have no CSV dictionary; every 2014–2017 code is in it) | all | dictionaries | documented labels; grouping by prefix is an analyst choice | all |
| OCCP prefixes | 1555 → ENG, 8000 → PRD (prefix missing in the 2018 dictionary only; the 2019 dictionary gives them); 9920 → UNE (no prefix in any year) | all | 2019 dictionary for 1555/8000 | documented (1555, 8000); analyst (9920 own group) | small |
| OCCP whole cross-group moves | 2010 codes 4610 → HLS, 5620 → TRN, 5800 → CMM in 2014–2017 | 2014–2017 | crosswalk: each has a single 2018 destination, in another major group; re-derived and checked by `scripts/harmonisation_report.py` | documented | 1.97–2.01% a year (31,213 in 2014) |
| OCCP split codes | 430, 1107, 2160, 2900, 3540, 4320, 9520, 9820 keep their own group (one of their 2018 destinations is in it) | — | crosswalk | analyst rule (split codes cannot be mapped one-to-one) | codes with any cross-group edge: 5.5–5.8% of 2014–2017 rows |
| RELP | 11 roomer/boarder and 12 housemate/roommate → 15 other nonrelative | 2014–2018 | 2019 form no longer separates them | analyst merge forced by a documented break | 2.3–2.4% |
| RELSHIPP → RELP categories | 20→0; 21, 23 (opposite-/same-sex spouse) → 1; 22, 24 (unmarried partner) → 13; 25–33 → 2–10; 34 roommate/housemate → 15; 35 foster child → 14; 36 other nonrelative → 15; 37 → 16; 38 → 17 | 2019 on | label correspondence in the 2017 and 2019 dictionaries | documented labels; correspondence by label is an analyst mapping | all from 2019 |
| POBP | 456 Tunisia → 464 Northern Africa n.s. | all | variable-change notes: collapsed from the 2022 file | documented | ≈60 a year (2017–2018) |
| POBP | 463 South Sudan → 469 Eastern Africa n.s. | all | dictionaries: deleted in 2024 | documented deletion; destination is an analyst choice | 33–187 a year |
| POBP | 208 Cyprus → 169 Other Europe n.s. | all | dictionaries: "Cyprus (2016 or earlier)", no destination stated | analyst assumption. Census places 208 in its Asia code range, so 254 "Other Asia, n.s." is an equally defensible alternative | 58–65 a year (2014–2016) |
| ST / STATE | STATE renamed to ST | 2023 on | dictionaries | documented | all from 2023 |
| Missing values | → 0, as folktables | all | folktables issue #39 (`np.nan_to_num(x, -1)` passes −1 as `copy`) | reproduces the benchmark | — |

Note on D023: an earlier version also assigned five split codes (2160, 2900, 3540, 4320, 9520) to a destination
group outside their own, contrary to the stated rule; 0.33% of 2014 rows. Corrected before archiving; all affected
models were refitted.
