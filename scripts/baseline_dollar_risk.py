#!/usr/bin/env python3
"""THE COMBINED BASELINE BOOK under conviction-based dollar-risk sizing (Angus 24-Jul).

This is the canonical ground truth the agent replay (Jun2025->Jul2026) must reproduce
trade-for-trade. The sizing rulebook is now PART of the baseline definition: if the
baseline P&L were still computed off the old static micro counts (10/15/22...), agents
sizing off the dollar-risk rulebook would diverge and 'fail' parity for the wrong reason.

Sizing (floor schedule, deterministic per-trade — no path dependence):
    risk_$   = min($400, conviction * $200)           # 1.0=200 1.5=300 2.25=400(cap)
    micros   = min(40, round(risk_$ / (stop_pts * $2)))  # integer MNQ, $2/pt, 40-clamp
    pl       = micros * dollars_1lot / 10                # micro = 1/10 of NQ mini
Every trade of a conviction tier risks the same dollars, normalized by stop width.
Live-account DD-scaling is an overlay applied identically by baseline and agents from
the same account-state feed; the frozen ground truth is this floor schedule.

Combines NY (canon_book) + London (london_canon_book) into one chronological book.
Writes output/baseline_book.parquet.

    python -m scripts.baseline_dollar_risk
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def dollar_risk_micros(conv, risk_pts):
    risk_d = min(400.0, conv * 200.0)
    return min(40, int(round(risk_d / (risk_pts * 2.0))))


def size_book(d, session):
    t = d[d["size"] > 0].copy()
    conv = t["size"].round(4).to_numpy()
    risk = t["risk"].astype(float).to_numpy()
    micros = np.array([dollar_risk_micros(c, r) for c, r in zip(conv, risk)])
    return pd.DataFrame({
        "session": session,
        "day": t["day"].astype(str).to_numpy(),
        "fill": pd.to_datetime(t["fill"], utc=True).to_numpy(),
        "direction": t["direction"].to_numpy(),
        "conviction": conv,
        "risk_pts": risk,
        "risk_dollars": np.minimum(400.0, conv * 200.0),
        "micros": micros,
        "dollars_1lot": t["dollars"].astype(float).to_numpy(),
        "pl": micros * t["dollars"].astype(float).to_numpy() / 10.0,
        "yr": t["yr"].astype(int).to_numpy(),
    })


def main():
    ny = pd.read_parquet("output/canon_book.parquet")
    lo = pd.read_parquet("output/london_canon_book.parquet")
    B = pd.concat([size_book(ny, "NY"), size_book(lo, "LONDON")], ignore_index=True)
    B = B.sort_values("fill").reset_index(drop=True)
    B.to_parquet("output/baseline_book.parquet")

    print("COMBINED BASELINE (dollar-risk floor schedule) — agent-replay ground truth\n")
    for yr in (2025, 2026):
        d = B[B.yr == yr]
        cum = d.groupby("day").pl.sum().cumsum()
        mdd = (cum.cummax() - cum).max() if len(cum) else 0
        gw = d.pl[d.pl > 0].sum(); gl = -d.pl[d.pl < 0].sum()
        print(f"  {yr}: ${d.pl.sum():+9,.0f}   {len(d)} trades ({d.day.nunique()} days)   "
              f"WR {(d.pl>0).mean()*100:.0f}%   PF {gw/max(gl,1):.2f}   maxDD ${mdd:,.0f}")
        for s in ("NY", "LONDON"):
            ds = d[d.session == s]
            print(f"       {s:7s} ${ds.pl.sum():+9,.0f}  {len(ds)}t  WR {(ds.pl>0).mean()*100:.0f}%")
    print(f"\n  combined 2yr: ${B.pl.sum():+,.0f}   wrote output/baseline_book.parquet ({len(B)} rows)")
    print("\n  per-tier constant dollar risk (parity anchor):")
    for c in sorted(B.conviction.unique()):
        row = B[B.conviction == c]
        print(f"    conv {c:>4}: risk ${row.risk_dollars.iloc[0]:>3.0f}  "
              f"micros {row.micros.min()}-{row.micros.max()} (median {int(row.micros.median())})  n={len(row)}")


if __name__ == "__main__":
    main()
