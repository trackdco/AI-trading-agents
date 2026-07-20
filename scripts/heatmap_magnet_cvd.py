#!/usr/bin/env python3
"""HEATMAP MAGNET + CVD conviction filter (Angus, 20 Jul): a trade that has BOTH a resting-liquidity
MAGNET at its entry level AND CVD absorption was ~60% win in April (fewer trades, higher P&L).
This tests that on the April champion trades using Brake's depth data.

  magnet = a resting level with size >= MAG (>> p95 of ~8) on the side you reject off, within DIST pts
           of entry (long -> big BID at/below entry = support; short -> big ASK at/above = resistance)
  absorb = CVD <= 0 (flow against the trade = real absorption, not hollow)

Depth: data/reference/depth_apr2026/*_ny.csv (26 days, ~1-min snapshots 08:00-11:00, 20 levels).
NOTE (in-flight when session hit usage cap): confirm the 60%-win April result, then extend the magnet
feature to Feb-Jul once Brake pulls depth for those months (only April exists now).

    python -m scripts.heatmap_magnet_cvd
"""
import glob
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# read the committed journal (travels with the repo); fall back to any local scratchpad copy
JOURNAL = Path("output/handoff/champ_journal_cvd.csv")
MAG, DIST = 15, 6   # magnet size threshold (p95~8), and max distance entry->magnet (points)


def main():
    J = pd.read_csv(JOURNAL)
    J = J[J.date.str.startswith("2026-04")].copy()
    bars = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    bars["key"] = bars.ts_event.dt.strftime("%Y-%m-%d %H:%M")
    cl = dict(zip(bars.key, bars.close))
    J["key"] = J.date + " " + J.fill_t
    J["entry"] = J.key.map(cl)
    J = J.dropna(subset=["entry"])

    dep = {}
    for f in glob.glob("data/reference/depth_apr2026/*_ny.csv"):
        d = pd.read_csv(f)
        d["ts"] = pd.to_datetime(d.ts)
        d["k"] = d.ts.dt.strftime("%Y-%m-%d %H:%M")
        for k, g in d.groupby("k"):
            dep[k] = g[["side", "price", "size"]].values

    def has_magnet(row):
        snap = dep.get(row.key)
        if snap is None:
            return False
        for side, price, size in snap:
            if size < MAG:
                continue
            if row.direction == "long" and side == "bid" and 0 <= row.entry - price <= DIST:
                return True
            if row.direction == "short" and side == "ask" and 0 <= price - row.entry <= DIST:
                return True
        return False

    J["magnet"] = J.apply(has_magnet, axis=1)
    J["absorb"] = J.cvd <= 0
    print(f"April champion trades w/ depth coverage: {len(J)}  win {J.win.mean()*100:.0f}%  ${J.dollars.sum():+,.0f}\n")
    for lab, m in [("ALL", J.index == J.index), ("magnet only", J.magnet), ("CVD-absorb only", J.absorb),
                   ("MAGNET + CVD", J.magnet & J.absorb), ("neither", ~(J.magnet | J.absorb))]:
        s = J[m]
        if len(s):
            print(f"  {lab:16s} {len(s):2d}t  win {s.win.mean()*100:2.0f}%  ${s.dollars.sum():+6,.0f}  avg ${s.dollars.mean():+.0f}")


if __name__ == "__main__":
    main()
