"""Load ACS 1-year PUMS person records into the ACSIncome universe, one parquet file per survey year.

Reads the raw Census zip files directly (no folktables download), keeps only the columns needed,
applies the ACSIncome filters of Ding et al. (2021, App. B.1) and writes data/derived/acsincome_<year>.parquet.

Design notes
- Geography follows folktables: the 50 states and Puerto Rico; DC (ST=11) is excluded because folktables'
  state list omits it. The US-wide csv_pus.zip holds the 50 states and DC; Puerto Rico is a separate file
  (csv_ppr.zip), read when present.
- Column names are upper-cased (2014-2016 files use lower-case replicate-weight names); STATE (2023 onward)
  is renamed to ST. Every required column is checked on reading.
- No recoding happens here. Harmonisation of codes across years is a separate, documented step.
- Years after 2018 are refused until prereg/ARCHIVED exists (created only after third-party archiving).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"

ORIGINAL_YEARS = (2014, 2015, 2016, 2017, 2018)
NEW_YEARS = (2019, 2021, 2022, 2023, 2024)
PREREG_ARCHIVED_FLAG = ROOT / "prereg" / "ARCHIVED"

FEATURES = ["AGEP", "COW", "SCHL", "MAR", "OCCP", "POBP", "RELP", "WKHP", "SEX", "RAC1P"]
EXTRA = ["SERIALNO", "SPORDER", "ST", "PINCP", "ADJINC", "PWGTP", "HISP", "RELSHIPP"]
REPWEIGHTS = [f"PWGTP{i}" for i in range(1, 81)]
WANTED = set(FEATURES + EXTRA + REPWEIGHTS) | {"STATE"}   # ST is named STATE from 2023 (dictionaries)
REQUIRED = set(FEATURES + REPWEIGHTS + ["SERIALNO", "SPORDER", "ST", "PINCP", "ADJINC", "PWGTP"]) - {"RELP"}
STRING_COLS = {"SERIALNO"}
EXCLUDED_ST = {11}  # District of Columbia: not in folktables' state list


def check_year_allowed(year: int) -> None:
    if year in NEW_YEARS and not PREREG_ARCHIVED_FLAG.exists():
        raise PermissionError(
            f"Refusing to read {year}: the pre-registration has not been archived "
            f"({PREREG_ARCHIVED_FLAG} missing).")
    if year not in ORIGINAL_YEARS + NEW_YEARS:
        raise ValueError(f"Unsupported year {year}")


def _read_member_filtered(zf: zipfile.ZipFile, name: str, counts: dict) -> pd.DataFrame:
    """Read one CSV member in chunks, applying the ACSIncome filters per chunk to bound memory."""
    out = []
    with zf.open(name) as fh:
        for chunk in pd.read_csv(
            fh,
            usecols=lambda c: c.upper() in WANTED,
            dtype={"SERIALNO": str, "serialno": str},
            na_values=[" ", ""],
            low_memory=False,
            chunksize=200_000,
        ):
            chunk.columns = [c.upper() for c in chunk.columns]
            chunk = chunk.rename(columns={"STATE": "ST"})
            missing = REQUIRED - set(chunk.columns)
            if missing or not ({"RELP", "RELSHIPP"} & set(chunk.columns)):
                raise KeyError(f"{name}: required columns missing: {sorted(missing)} (or RELP/RELSHIPP)")
            kept, steps = acsincome_universe(chunk)
            for k, v in steps.items():
                counts[k] = counts.get(k, 0) + v
            for c in kept.columns:
                if c in REPWEIGHTS:
                    kept[c] = pd.to_numeric(kept[c], errors="raise").astype("int32")
            out.append(kept)
    return pd.concat(out, ignore_index=True)


def read_year_universe(year: int) -> tuple[pd.DataFrame, dict]:
    """ACSIncome universe for the 50 states and (if present) Puerto Rico; DC excluded."""
    check_year_allowed(year)
    parts, members, counts = [], [], {}
    for fname in ("csv_pus.zip", "csv_ppr.zip"):
        zpath = RAW / str(year) / fname
        if not zpath.exists():
            if fname == "csv_ppr.zip":
                continue
            raise FileNotFoundError(zpath)
        with zipfile.ZipFile(zpath) as zf:
            for m in sorted(n for n in zf.namelist() if n.lower().endswith(".csv")):
                parts.append(_read_member_filtered(zf, m, counts))
                members.append(f"{fname}:{m}")
    df = pd.concat(parts, ignore_index=True)
    info = {"year": year, "members": members, "filter_counts": counts,
            "has_puerto_rico": bool((df["ST"] == 72).any())}
    return df, info


def acsincome_universe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply folktables' adult_filter in its order and record the count after each step."""
    steps = {"all_records": int(len(df))}
    d = df[~df["ST"].isin(EXCLUDED_ST)]; steps["exclude_DC"] = int(len(d))
    d = d[d["AGEP"] > 16]; steps["AGEP>16"] = int(len(d))
    d = d[d["PINCP"] > 100]; steps["PINCP>100"] = int(len(d))
    d = d[d["WKHP"] > 0]; steps["WKHP>0"] = int(len(d))
    d = d[d["PWGTP"] >= 1]; steps["PWGTP>=1"] = int(len(d))
    return d.reset_index(drop=True), steps


def build_year(year: int, overwrite: bool = False) -> Path:
    DERIVED.mkdir(parents=True, exist_ok=True)
    out = DERIVED / f"acsincome_{year}.parquet"
    meta_path = DERIVED / f"acsincome_{year}.json"
    if out.exists() and meta_path.exists() and not overwrite:
        return out
    uni, info = read_year_universe(year)
    keep = [c for c in FEATURES + EXTRA + REPWEIGHTS if c in uni.columns]
    uni = uni[keep].copy()
    for c in keep:
        if c not in STRING_COLS and c not in REPWEIGHTS:
            uni[c] = pd.to_numeric(uni[c], errors="raise").astype("float64")
    uni.to_parquet(out, index=False)
    by_st = uni.groupby("ST").size()
    info.update({
        "n_universe": int(len(uni)),
        "n_geographies": int(by_st.size),
        "rows_by_ST": {str(int(k)): int(v) for k, v in by_st.items()},
        "columns": keep,
        "missing_counts": {c: int(uni[c].isna().sum()) for c in keep if c not in REPWEIGHTS},
        "sha256_parquet": hashlib.sha256(out.read_bytes()).hexdigest(),
    })
    meta_path.write_text(json.dumps(info, indent=2))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    for y in a.years:
        p = build_year(y, overwrite=a.overwrite)
        meta = json.loads((DERIVED / f"acsincome_{y}.json").read_text())
        print(y, meta["filter_counts"], "PR:", meta["has_puerto_rico"])
