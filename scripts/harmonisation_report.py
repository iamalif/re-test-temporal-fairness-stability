"""Harmonisation report on the original cohort (2014-2018): feature distributions only, no outcomes.

1. OCCP: row share by harmonised major group, per year. A jump at 2018 that does not continue the
   2014-2017 trend indicates residual recoding artefact in the harmonised scheme.
2. OCCP crosswalk: edges of the official 2010->2018 code-change sheet whose two codes carry different group
   prefixes (cross-group moves), and the share of 2014-2017 rows in such 2010 codes.
3. RELP / POBP: rows affected by the merges.
Writes results/harmonisation/report_2014_2018.json and occp_group_shares.csv.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import openpyxl
import pandas as pd

from common import load_year
from harmonise import POBP_MERGE, RELP_MERGE, group_codes, harmonise, occp_group_map

YEARS = (2014, 2015, 2016, 2017, 2018)


def crosswalk_edges():
    wb = openpyxl.load_workbook(ROOT / "data/raw/crosswalk/2018-occupation-code-list-and-crosswalk.xlsx",
                                read_only=True)
    name = [n for n in wb.sheetnames if n.strip().startswith("Occ Code")][0]
    edges, cur = [], None
    for r in list(wb[name].iter_rows(values_only=True))[3:]:
        c10, _, c18 = (list(r) + [None] * 3)[:3]
        if c10 is not None and str(c10).strip():
            cur = int(str(c10).strip())
        if c18 is not None and str(c18).strip() and cur is not None:
            edges.append((cur, int(str(c18).strip())))
    return edges


def main():
    out = ROOT / "results" / "harmonisation"
    out.mkdir(parents=True, exist_ok=True)
    inv = {v: k for k, v in group_codes().items()}
    shares, rep = {}, {"years": {}}
    g10, g18 = occp_group_map(2017), occp_group_map(2018)
    cross = [(a, b, g10.get(a), g18.get(b)) for a, b in crosswalk_edges()]
    cross_group = [(a, b, ga, gb) for a, b, ga, gb in cross if ga and gb and ga != gb]
    unresolved = [(a, b) for a, b, ga, gb in cross if not ga or not gb]
    rep["occp_crosswalk"] = {"edges": len(cross), "cross_group_edges": cross_group,
                             "edges_with_code_not_in_pums_dictionaries": len(unresolved)}
    cross_codes_2010 = {a for a, *_ in cross_group}
    for y in YEARS:
        df = load_year(y, columns=["OCCP", "RELP", "POBP", "RELSHIPP"] if y >= 2019 else ["OCCP", "RELP", "POBP"])
        h = harmonise(df, y)
        shares[y] = h["OCCP_GRP"].map(inv).value_counts(normalize=True)
        rep["years"][y] = {
            "rows": int(len(h)),
            "relp_rows_merged": int(df["RELP"].isin(list(RELP_MERGE)).sum()),
            "pobp_rows_merged": {str(k): int((df["POBP"] == k).sum()) for k in POBP_MERGE},
            "share_rows_in_cross_group_2010_codes": (float(df["OCCP"].isin(cross_codes_2010).mean())
                                                     if y < 2018 else None),
        }
    tab = pd.DataFrame(shares).fillna(0).sort_index()
    tab["jump_2018_vs_trend"] = tab[2018] - (tab[2017] + (tab[2017] - tab[2014]) / 3)
    tab.round(5).to_csv(out / "occp_group_shares.csv")
    rep["largest_2018_jumps"] = tab["jump_2018_vs_trend"].abs().sort_values(ascending=False).head(8).round(5).to_dict()
    (out / "report_2014_2018.json").write_text(json.dumps(rep, indent=1, default=str))
    print(tab.round(4).to_string())
    print(json.dumps({k: v for k, v in rep.items() if k != "occp_crosswalk"}, indent=1, default=str))
    print("cross-group crosswalk edges:", len(cross_group), cross_group[:15])


if __name__ == "__main__":
    main()
