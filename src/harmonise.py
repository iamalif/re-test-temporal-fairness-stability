"""Harmonised ACSIncome features across survey years 2014-2024 (built from Census documentation only).

Every mapping below is derived from the PUMS data dictionaries (data/raw/dictionaries) and the Census 2018
occupation crosswalk; none is tuned on outcome data. Breaks handled:

- OCCP (2018): 2010-based codes in 2014-2017, 2018-based codes from 2018. Harmonised to the major
  occupation group given by the three-letter prefix of each code's label in that year's own dictionary
  (e.g. "MGR-", "ENG-", "PRD-"). The prefix scheme exists in both vintages. Codes that the official
  crosswalk moves across major groups are counted in the harmonisation report.
- RELP -> RELSHIPP (2019): spouse and unmarried partner split by sex; "roomer or boarder" dropped.
  Harmonised to RELP's categories, with roomer/boarder (11), housemate/roommate (12) and other nonrelative (15)
  merged into one non-relative category in every year, because the 2019 form no longer separates them.
- POBP: codes deleted in some years (208 Cyprus, through 2016; 456 Tunisia and 463 South Sudan, absent from
  the 2024 dictionary) are merged with a residual code in every year (see POBP_MERGE).
- RAC1P: codes unchanged, but the race question and coding changed in 2020 (Census: compare with caution).
  Not recoded; race-based estimands use 2019 as their last year (pre-registration).
- COW, SCHL, MAR, SEX, WKHP, AGEP: dictionary codes identical in 2014-2018, 2019 and 2024 dictionaries.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DICT_DIR = ROOT / "data" / "raw" / "dictionaries"

HARMONISED_FEATURES = ["AGEP", "COW", "SCHL", "MAR", "OCCP_GRP", "POBP_H", "RELP_H", "WKHP", "SEX", "RAC1P"]

RELP_MERGE = {11: 15, 12: 15}           # RELP: roomer/boarder and housemate/roommate -> other nonrelative
RELSHIPP_TO_RELP = {20: 0, 21: 1, 23: 1, 22: 13, 24: 13, 25: 2, 26: 3, 27: 4, 28: 5, 29: 6, 30: 7, 31: 8,
                    32: 9, 33: 10, 34: 15, 35: 14, 36: 15, 37: 16, 38: 17}
POBP_MERGE = {208: 169, 456: 464, 463: 469}   # Cyprus -> Other Europe n.s.; Tunisia -> Northern Africa n.s.;
                                              # South Sudan -> Eastern Africa n.s. (applied in every year)


def dictionary_file(year: int) -> Path:
    # 2014-2016 single-year CSV dictionaries are not published; the 2017 dictionary carries the same
    # 2010-based occupation codes (verified: every OCCP code in the 2014-2017 data is in it).
    return DICT_DIR / f"PUMS_Data_Dictionary_{max(year, 2017)}.csv"


@lru_cache(maxsize=None)
def dictionary(year: int) -> dict[str, dict[str, str]]:
    d = defaultdict(dict)
    with open(dictionary_file(year), encoding="latin-1") as fh:
        for row in csv.reader(fh):
            if row and row[0] == "VAL":
                d[row[1]][row[4]] = row[6]
    return d


# Labels without a prefix: 1555 and 8000 lack it in the 2018 dictionary only (the 2019 dictionary gives ENG-
# and PRD-); 9920 ("unemployed, last worked 5+ years ago or never") has none in any year.
PREFIX_FIXES = {1555: "ENG", 8000: "PRD", 9920: "UNE"}
# 2010 codes that the official crosswalk moves, whole, into a 2018 code of another major group are assigned
# the destination group in every year (one-to-one moves only; split codes keep their own group).
# Source: "Occ Code Changes" sheet of the 2018 Census occupation crosswalk (scripts/harmonisation_report.py).
DESTINATION_GROUP = {2160: "ENT", 2900: "OFF", 3540: "SCI", 4320: "TRN", 4610: "HLS", 5620: "TRN",
                     5800: "CMM", 9520: "EXT"}


@lru_cache(maxsize=None)
def occp_group_map(year: int) -> dict[int, str]:
    out = {}
    for code, lab in dictionary(year)["OCCP"].items():
        if code.isdigit():
            c = int(code)
            m = re.match(r"^([A-Z]{3})-", lab.strip())
            out[c] = PREFIX_FIXES.get(c) or (m.group(1) if m else "UNK")
            if year <= 2017 and c in DESTINATION_GROUP:
                out[c] = DESTINATION_GROUP[c]
    if "UNK" in out.values():
        raise ValueError(f"{year}: OCCP labels without a group: {[k for k, v in out.items() if v == 'UNK']}")
    return out


def group_codes() -> dict[str, int]:
    """Stable integer codes for the prefix groups (alphabetical), shared by all years."""
    groups = sorted(set(occp_group_map(2017).values()) | set(occp_group_map(2018).values()))
    return {g: i + 1 for i, g in enumerate(groups)}


def harmonise(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Return a copy with harmonised columns OCCP_GRP, RELP_H, POBP_H added. Raises on unmapped codes."""
    out = df.copy()
    gmap, gcode = occp_group_map(year), group_codes()
    occ = out["OCCP"]
    grp = occ.map(lambda v: gcode[gmap[int(v)]] if pd.notna(v) else np.nan)
    unmapped = occ.notna() & grp.isna()
    if unmapped.any():
        raise ValueError(f"{year}: unmapped OCCP codes {sorted(occ[unmapped].unique())[:10]}")
    out["OCCP_GRP"] = grp
    if "RELSHIPP" in out and out["RELSHIPP"].notna().any():
        rel = out["RELSHIPP"].map(RELSHIPP_TO_RELP)
        if rel[out["RELSHIPP"].notna()].isna().any():
            raise ValueError(f"{year}: unmapped RELSHIPP codes")
    else:
        rel = out["RELP"].map(lambda v: RELP_MERGE.get(int(v), int(v)) if pd.notna(v) else np.nan)
    out["RELP_H"] = rel
    out["POBP_H"] = out["POBP"].map(lambda v: POBP_MERGE.get(int(v), int(v)) if pd.notna(v) else np.nan)
    return out
