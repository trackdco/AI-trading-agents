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
# read the committed journal (travels with the repo)
JOURNAL = Path("output/handoff/champ_journal_cvd.csv")
# MAGNET = PERSISTENT liquidity: sum resting size per price across ALL day snapshots (a bright heatmap
# band), then a trade is "on a magnet" if its entry is within BAND pts of one of the day's TOPN bands.
# (First attempt — a single-snapshot wall size>=15 — was too strict: only 1/29 April trades qualified.)
BAND, TOPN = 10, 5


def main():
    J = pd.read_csv(JOURNAL)
    bars = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    bars["key"] = bars.ts_event.dt.strftime("%Y-%m-%d %H:%M")
    cl = dict(zip(bars.key, bars.close))
    J["key"] = J.date + " " + J.fill_t
    J["entry"] = J.key.map(cl)
    J = J.dropna(subset=["entry"])

    # per-day persistent liquidity bands, across ALL committed depth dirs
    # (depth_apr2026 today; a full-year depth_* dir auto-joins the moment it lands — no code change)
    perday = {}
    for f in glob.glob("data/reference/depth*/*_ny.csv"):
        d = pd.read_csv(f)
        day = f.split("nq_depth_")[1][:10]
        perday[day] = d.groupby("price")["size"].sum().nlargest(TOPN).index.values
    # restrict to trades whose day has depth coverage (auto-scales as more months land)
    J = J[J.date.isin(perday)].copy()
    print(f"depth coverage: {len(perday)} days, months {sorted(J.date.str[:7].unique())}")

    def on_magnet(row):
        top = perday.get(row.date)
        return bool(top is not None and (abs(top - row.entry) <= BAND).any())

    J["magnet"] = J.apply(on_magnet, axis=1)
    J["absorb"] = J.cvd <= 0
    print(f"April champion trades w/ depth coverage: {len(J)}  win {J.win.mean()*100:.0f}%  ${J.dollars.sum():+,.0f}")
    print(f"(magnet = entry within {BAND}pt of a top-{TOPN} persistent-liquidity band; absorb = cvd<=0)\n")
    for lab, m in [("ALL", J.index == J.index), ("magnet only", J.magnet), ("CVD-absorb only", J.absorb),
                   ("MAGNET + CVD", J.magnet & J.absorb), ("neither", ~(J.magnet | J.absorb))]:
        s = J[m]
        if len(s):
            print(f"  {lab:16s} {len(s):2d}t  win {s.win.mean()*100:2.0f}%  ${s.dollars.sum():+6,.0f}  avg ${s.dollars.mean():+.0f}")
    # NOTE: MAGNET+CVD = 14t / 50% win / +$3,470 with these params (vs 38% baseline) — directionally
    # confirms Angus's magnet+CVD signal; exact 60% needs his precise magnet definition. Extend to
    # Feb-Jul once Brake pulls depth for the other months.


if __name__ == "__main__":
    main()
