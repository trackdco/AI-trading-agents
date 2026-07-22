#!/usr/bin/env python3
"""Grade the FULL-SPAN fresh-eyes conviction run (Angus 22 Jul). Compares, on the same covered
days, year-by-year and total:

  A  blind fresh-eyes baseline      (original ledger action, full size)
  P  enriched agent, PRE-MARKET only (premarket_regime/premarket_stand_down, binary)
  B  enriched agent, 09:50 verdict, BINARY (full size or flat)     -> B vs P = adaptation value
  C  B x agent conviction            (size_multiplier x confidence weight {low .5, med .75, high 1})
  D  B x mechanical conviction       (coil AND absorp both above OTHER-year median -> 0.25)
  E  full stack                      (C x mechanical)

Sizing scales the day's chosen-book P&L linearly. Mechanical thresholds are out-of-fit (other
year's median), fixed a priori -- nothing here is tuned to test-set P&L.

    python -m scripts.grade_fresheyes_full output/fe_full/verdicts.json
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CONF_W = {"low": 0.5, "medium": 0.75, "high": 1.0}


def act_of(regime, stand):
    if stand:
        return "FLAT"
    return "E3" if regime in ("balance", "trap") else "E4" if regime == "war" else "FLAT"


def book_pl(row, action):
    return row.e3 if action == "E3" else row.e4 if action == "E4" else 0.0


def main():
    vpath = sys.argv[1] if len(sys.argv) > 1 else "output/fe_full/verdicts.json"
    V = {d["day"]: d for d in json.loads(Path(vpath).read_text())}
    L = pd.read_csv("output/fe_full/labels.csv")
    L = L[L.day.isin(V)].copy().reset_index(drop=True)
    L["yr"] = L.day.str[:4].astype(int)
    L["both_red"] = (L.e3 <= 0) & (L.e4 <= 0)

    # out-of-fit mechanical thresholds (other year's median)
    med = {yr: (L[L.yr != yr].coil.median(), L[L.yr != yr].absorp_corr.median()) for yr in (2025, 2026)}
    def mech_factor(r):
        cm, am = med[r.yr]
        return 0.25 if (r.coil == r.coil and r.coil >= cm and r.absorp_corr >= am) else 1.0

    rows = []
    for r in L.itertuples():
        v = V[r.day]
        pre_act = act_of(v.get("premarket_regime"), v.get("premarket_stand_down"))
        fin_act = act_of(v.get("regime"), v.get("stand_down") or float(v.get("size_multiplier", 1)) == 0)
        conv = float(v.get("size_multiplier", 1)) * CONF_W.get(v.get("confidence", "medium"), 0.75)
        mf = mech_factor(r)
        rows.append(dict(
            day=r.day, yr=r.yr, both_red=r.both_red, oracle=r.oracle_act, revised=bool(v.get("revised")),
            A=book_pl(r, r.orig_act), A_act=r.orig_act,
            P=book_pl(r, pre_act), P_act=pre_act,
            B=book_pl(r, fin_act), B_act=fin_act,
            C=book_pl(r, fin_act) * conv,
            D=book_pl(r, fin_act) * mf,
            E=book_pl(r, fin_act) * conv * mf,
        ))
    D = pd.DataFrame(rows)
    oracle = L.apply(lambda r: max(r.e3, r.e4, 0), axis=1).groupby(L.yr).sum()

    print(f"### FULL-SPAN FRESH-EYES CONVICTION RUN — {len(D)} days ###\n")
    variants = [("A", "blind baseline"), ("P", "enriched, pre-market only"),
                ("B", "enriched, 09:50 binary"), ("C", "B x agent conviction"),
                ("D", "B x mechanical (coil&absorp)"), ("E", "full stack (C x mech)")]
    for yr in (2025, 2026, None):
        s = D if yr is None else D[D.yr == yr]
        lab = "ALL" if yr is None else str(yr)
        orc = oracle.sum() if yr is None else oracle.get(yr, 0)
        print(f"--- {lab}  ({len(s)} days, oracle ceiling ${orc:+,.0f}) ---")
        print(f"  {'variant':32s} {'P&L':>10s} {'hit':>5s} {'flat':>5s} {'BR-caught':>10s}")
        for k, name in variants:
            akey = f"{k}_act" if f"{k}_act" in s else "B_act"
            hit = (s[akey] == s.oracle).mean() * 100
            flat = (s[akey] == "FLAT").mean() * 100
            br = s[s.both_red]
            brc = (br[akey] == "FLAT").mean() * 100 if len(br) else 0
            print(f"  {k}  {name:29s} ${s[k].sum():+9,.0f} {hit:4.0f}% {flat:4.0f}% {brc:9.0f}%")
        print()
    n_rev = D.revised.sum()
    rev = D[D.revised]
    print(f"adaptation: agent revised its pre-market thesis on {n_rev}/{len(D)} days "
          f"({n_rev/len(D)*100:.0f}%)")
    if len(rev):
        print(f"  on revised days:   pre-market P&L ${rev.P.sum():+,.0f}  ->  final ${rev.B.sum():+,.0f}  "
              f"(adaptation delta {rev.B.sum()-rev.P.sum():+,.0f})")
        keep = D[~D.revised]
        print(f"  on unrevised days: ${keep.B.sum():+,.0f} (pre==final by construction? "
              f"{int((keep.P_act==keep.B_act).mean()*100)}% agree)")


if __name__ == "__main__":
    main()
