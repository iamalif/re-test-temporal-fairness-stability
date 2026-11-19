"""Harmonisation report on the original cohort (2014-2018): feature distributions only, no outcomes.

1. OCCP crosswalk: re-derives, from the official 2010->2018 code-change sheet, the 2010 codes moved WHOLE into
   another major group, and checks that src/harmonise.py DESTINATION_GROUP equals that set (fails otherwise).
   Lists split codes and the share of 2014-2017 rows in codes with any cross-group edge.
2. OCCP group shares per year, overall and within race (White, Black) and sex groups. The 2018 value is compared
   with the linear 2014-2017 trend ("jump"). Jumps combine residual recoding artefact and real change; they are
   diagnostics, not a bound on harmonisation error.
3. RELP / POBP: rows affected by the merges.
Writes results/harmonisation/report_2014_2018.json, occp_group_shares.csv and occp_group_jumps_by_group.csv.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import openpyxl
import pandas as pd

from common import BLACK, WHITE, load_year
from harmonise import (DESTINATION_GROUP, POBP_MERGE, PREFIX_FIXES, RELP_MERGE, dictionary, group_codes, harmonise,
                       occp_group_map)

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


def prefix_group(year):
    """Major group from each code's own label prefix (before any destination override)."""
    out = {}
    for code, lab in dictionary(year)["OCCP"].items():
        if code.isdigit():
            c = int(code)
            m = re.match(r"^([A-Z]{3})-", lab.strip())
            out[c] = PREFIX_FIXES.get(c) or (m.group(1) if m else None)
    return out


def derive_destinations(edges):
    g10, g18 = prefix_group(2017), prefix_group(2018)
    dest = defaultdict(set)
    for a, b in edges:
        dest[a].add(b)
    whole, split, unresolved = {}, [], []
    for a, bs in sorted(dest.items()):
        if a not in g10:
            continue
        gs = {g18.get(b) for b in bs}
        if None in gs:
            unresolved.append((a, sorted(b for b in bs if g18.get(b) is None)))
        gs.discard(None)
        if not gs or gs == {g10[a]}:
            continue
        if len(gs) == 1:
            whole[a] = gs.pop()
        else:
            split.append({"code_2010": a, "own_group": g10[a], "destination_groups": sorted(gs),
                          "own_group_among_destinations": g10[a] in gs})
    return whole, split, unresolved


def shares_by(h, inv, mask):
    return h.loc[mask, "OCCP_GRP"].map(inv).value_counts(normalize=True)


def jump(tab):
    return tab[2018] - (tab[2017] + (tab[2017] - tab[2014]) / 3)


def main():
    out = ROOT / "results" / "harmonisation"
    out.mkdir(parents=True, exist_ok=True)
    inv = {v: k for k, v in group_codes().items()}
    edges = crosswalk_edges()
    whole, split, unresolved = derive_destinations(edges)
    if whole != DESTINATION_GROUP:
        raise SystemExit(f"DESTINATION_GROUP {DESTINATION_GROUP} differs from the crosswalk-derived set {whole}")
    rep = {"years": {}, "occp_crosswalk": {
        "edges": len(edges), "whole_cross_group_moves": {str(k): v for k, v in whole.items()},
        "split_codes_with_cross_group_destination": split,
        "edges_to_codes_not_in_pums_dictionary": unresolved,
        "destination_group_matches_crosswalk": True}}
    cross_any = set(whole) | {s["code_2010"] for s in split}
    groups = {"all": None, "white": ("RAC1P", WHITE), "black": ("RAC1P", BLACK), "male": ("SEX", 1),
              "female": ("SEX", 2)}
    shares = {g: {} for g in groups}
    for y in YEARS:
        df = load_year(y, columns=["OCCP", "RELP", "POBP", "RAC1P", "SEX"])
        h = harmonise(df, y)
        for g, spec in groups.items():
            mask = pd.Series(True, index=h.index) if spec is None else (h[spec[0]] == spec[1])
            shares[g][y] = shares_by(h, inv, mask)
        rep["years"][y] = {
            "rows": int(len(h)),
            "relp_rows_merged": int(df["RELP"].isin(list(RELP_MERGE)).sum()),
            "pobp_rows_merged": {str(k): int((df["POBP"] == k).sum()) for k in POBP_MERGE},
            "rows_in_destination_override_codes": int(df["OCCP"].isin(list(DESTINATION_GROUP)).sum()) if y < 2018 else 0,
            "share_rows_in_codes_with_cross_group_edges": float(df["OCCP"].isin(cross_any).mean()) if y < 2018 else None,
        }
    tab = pd.DataFrame(shares["all"]).fillna(0).sort_index()
    tab["jump_2018_vs_trend"] = jump(tab)
    tab.round(5).to_csv(out / "occp_group_shares.csv")
    rows = []
    for g in groups:
        t = pd.DataFrame(shares[g]).fillna(0)
        for grp, v in jump(t).items():
            rows.append(dict(population=g, occ_group=grp, share_2018=float(t.loc[grp, 2018]), jump=float(v)))
    jumps = pd.DataFrame(rows)
    jumps.round(5).to_csv(out / "occp_group_jumps_by_group.csv", index=False)
    rep["largest_2018_jumps"] = tab["jump_2018_vs_trend"].abs().sort_values(ascending=False).head(8).round(5).to_dict()
    rep["max_abs_jump_by_population"] = jumps.groupby("population")["jump"].apply(lambda s: float(s.abs().max())).to_dict()
    rep["race_gap_in_jumps"] = {
        grp: float(jumps[(jumps.population == "white") & (jumps.occ_group == grp)]["jump"].sum()
                   - jumps[(jumps.population == "black") & (jumps.occ_group == grp)]["jump"].sum())
        for grp in sorted(jumps.occ_group.unique())}
    (out / "report_2014_2018.json").write_text(json.dumps(rep, indent=1, default=str))
    print(tab.round(4).to_string())
    print("whole cross-group moves:", whole)
    print("split codes:", [(s["code_2010"], s["own_group"], s["destination_groups"]) for s in split])
    print("max |jump| by population:", {k: round(v, 4) for k, v in rep["max_abs_jump_by_population"].items()})


if __name__ == "__main__":
    main()
