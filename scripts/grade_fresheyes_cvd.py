#!/usr/bin/env python3
"""Grade the CVD-enriched fresh-eyes verdicts vs the original blind agent (Angus 22 Jul).
Reads output/fe_cvd/labels.csv + a verdicts JSON (day -> verdict fields), maps each verdict to
a book action, and compares book-hit + P&L to the original blind agent on the same days. Also
layers the mechanical pre-market-CVD stand-down gate on top.

    python -m scripts.grade_fresheyes_cvd output/fe_cvd/verdicts.json
"""
import json
import sys
from pathlib import Path

import pandas as pd


def action_of(v):
    if v.get("stand_down") or float(v.get("size_multiplier", 1)) == 0:
        return "FLAT"
    r = v.get("regime")
    if r in ("balance", "trap"):
        return "E3"
    if r == "war":
        return "E4"
    return "FLAT"                              # event_risk w/o committed book


def pnl(action, e3, e4):
    return e3 if action == "E3" else e4 if action == "E4" else 0.0


def main():
    vpath = sys.argv[1] if len(sys.argv) > 1 else "output/fe_cvd/verdicts.json"
    V = {d["day"]: d for d in json.loads(Path(vpath).read_text())}
    L = pd.read_csv("output/fe_cvd/labels.csv")
    L = L[L.day.isin(V)].copy()
    L["new_act"] = L.day.map(lambda d: action_of(V[d]))
    L["new_hit"] = (L.new_act == L.oracle_act).astype(int)
    L["new_pnl"] = L.apply(lambda r: pnl(r.new_act, r.e3, r.e4), axis=1)
    L["orig_pnl"] = L.apply(lambda r: pnl(r.orig_act, r.e3, r.e4), axis=1)
    # mechanical CVD gate on top of the new agent: stand down flat/neutral pre-market flow
    L["new_gated_act"] = L.apply(lambda r: "FLAT" if "flat" in str(r.vs_recent).lower()
                                 or "neutral" in str(r.vs_recent).lower() else r.new_act, axis=1)
    L["new_gated_pnl"] = L.apply(lambda r: pnl(r.new_gated_act, r.e3, r.e4), axis=1)

    n = len(L)
    print(f"### CVD-ENRICHED FRESH-EYES — {n} days (2025 H2 validation batch) ###\n")
    print(f"  {'':28s} {'book-hit':>9s} {'P&L':>9s} {'stand-down':>11s}")
    print(f"  {'ORIGINAL blind agent':28s} {L.orig_hit.mean()*100:7.0f}%  ${L.orig_pnl.sum():+7,.0f}  "
          f"{(L.orig_act=='FLAT').mean()*100:9.0f}%")
    print(f"  {'CVD-enriched agent':28s} {L.new_hit.mean()*100:7.0f}%  ${L.new_pnl.sum():+7,.0f}  "
          f"{(L.new_act=='FLAT').mean()*100:9.0f}%")
    print(f"  {'CVD agent + mech gate':28s} {'':8s}  ${L.new_gated_pnl.sum():+7,.0f}  "
          f"{(L.new_gated_act=='FLAT').mean()*100:9.0f}%")
    print(f"\n  oracle-perfect on these days: ${L[['e3','e4']].clip(lower=0).max(axis=1).sum():+,.0f}")
    print(f"  always-E3 ${L.e3.sum():+,.0f}   always-E4 ${L.e4.sum():+,.0f}")
    print("\n  per-day (orig -> new):")
    for r in L.itertuples():
        flag = "  ↑" if r.new_hit and not r.orig_hit else ("  ↓" if r.orig_hit and not r.new_hit else "")
        print(f"    {r.day}  oracle {r.oracle_act:5s}  orig {r.orig_act:5s}  new {r.new_act:5s}  "
              f"cvd {r.vs_recent:26s}{flag}")


if __name__ == "__main__":
    main()
