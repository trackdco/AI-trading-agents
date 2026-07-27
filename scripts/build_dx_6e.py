#!/usr/bin/env python3
"""Build clean volume-continuous 1-min series for DX (ICE Dollar Index) and 6E (CME Euro FX).

INPUT  the two Databento ohlcv-1m CSV exports (IFUS.IMPACT for DX, GLBX.MDP3 for 6E),
       2025-07-01 -> 2026-07-26, matching the gold master's window.
OUTPUT data/reference/dx_1m_master.parquet and data/reference/6e_1m_master.parquet

WHY THIS EXISTS. The gold reversal book has never been tested against the dollar, which is the
YouTuber's single biggest claimed edge. DX is the ACTUAL dollar index (ICE), not a proxy; 6E is
the CME euro leg, kept as an independent cross-check with the OPPOSITE expected sign (gold and
the euro are both inverse-dollar, so they move together).

SYMBOLOGY DECISIONS, from profiling the raw files -- each one is a place a silent bug would
poison the correlation test, so they are recorded rather than left implicit:
  DX  * publisher 97 is authoritative (319,810 rows); publisher 98 carries 251 rows and is
        dropped, which also removes the 233 duplicate (ts, instrument) rows.
      * the '!' suffix marks the tradable outrights (DX  FMU0025! etc).
      * the '_Z' suffix rows have MEDIAN CLOSE 0.000 -- they are not prices and are dropped.
      * cycle is quarterly only: H/M/U/Z.
  6E  * single publisher, no duplicates.
      * serial months (6EX5, 6EJ6, ...) exist but carry <1% of volume; the front-by-volume rule
        selects quarterlies on its own, so no special handling is needed.
  BOTH * symbols containing '-' are calendar spreads and are dropped before anything else.

ROLL. Front month = the outright with the highest volume that session day. This is the same rule
used to build gc_1m_master.parquet, so the three series roll on comparable logic.

A 'contract' column is kept deliberately. Rolls create price GAPS, so any return computed ACROSS
a roll boundary is fiction. Downstream code must mask those; the column is what makes that
possible. Do not drop it for tidiness.

    python3 scripts/build_dx_6e.py <dir-containing-the-two-csvs>
"""
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data", "reference")


def build(path, label, out_name):
    print(f"\n=== {label}\n  read {os.path.basename(path)} ...", flush=True)
    d = pd.read_csv(path, usecols=["ts_event", "publisher_id", "open", "high", "low",
                                   "close", "volume", "symbol"])
    n0 = len(d)
    d = d[~d.symbol.str.contains("-", regex=False)]                 # drop calendar spreads
    if label.startswith("DX"):
        d = d[d.publisher_id == 97]                                 # authoritative publisher
        d = d[d.symbol.str.endswith("!")]                           # tradable outrights only
    d = d[d.close > 0]                                              # kills the '_Z' zero rows
    print(f"  {n0:,} raw -> {len(d):,} usable outright rows")

    d["ts"] = pd.to_datetime(d.ts_event, utc=True)
    d["day"] = d.ts.dt.strftime("%Y-%m-%d")

    # front month = highest-volume outright that day
    vol = d.groupby(["day", "symbol"], as_index=False).volume.sum()
    front = vol.sort_values("volume").groupby("day").tail(1)[["day", "symbol"]]
    front = front.rename(columns={"symbol": "front"})
    d = d.merge(front, on="day", how="inner")
    d = d[d.symbol == d.front].copy()

    d = d.sort_values("ts").drop_duplicates(subset=["ts"], keep="last").reset_index(drop=True)
    d["contract"] = d.symbol
    d = d[["ts", "open", "high", "low", "close", "volume", "contract"]]

    rolls = (d.contract != d.contract.shift(1)).sum() - 1
    print(f"  {len(d):,} continuous bars   {d.ts.min()} -> {d.ts.max()}   rolls: {rolls}")
    print(f"  contracts used: {', '.join(d.contract.unique())}")

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, out_name)
    d.to_parquet(p, index=False)
    print(f"  -> {p}  ({os.path.getsize(p)/1e6:.1f} MB)")
    return d


def coverage(d, label):
    """FEASIBILITY GATE: does this instrument actually trade in the gold Asia window?

    The whole test is impossible if DX is dark at 00-02 UTC. Better to find that out here than
    to discover it as a wall of NaNs inside the correlation test.
    """
    h = d.ts.dt.hour
    asia = d[h.isin([0, 1])]
    ndays_all = d.ts.dt.strftime("%Y-%m-%d").nunique()
    ndays_asia = asia.ts.dt.strftime("%Y-%m-%d").nunique()
    print(f"\n  {label} coverage in 00-02 UTC (the gold Asia window):")
    print(f"    bars {len(asia):,}   days with any bar {ndays_asia}/{ndays_all}")
    if ndays_asia:
        per_day = len(asia) / ndays_asia
        print(f"    mean bars per day in the 120-min window: {per_day:.0f}/120 "
              f"({100*per_day/120:.0f}% of minutes)")
        print(f"    mean volume per Asia bar: {asia.volume.mean():.0f}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "."
    dx_csv = glob.glob(os.path.join(src, "*ifus-impact*.csv"))
    e6_csv = glob.glob(os.path.join(src, "*glbx-mdp3*.csv"))
    if not dx_csv or not e6_csv:
        sys.exit(f"could not find both CSVs in {src}")
    dx = build(dx_csv[0], "DX  (ICE Dollar Index)", "dx_1m_master.parquet")
    e6 = build(e6_csv[0], "6E  (CME Euro FX)", "6e_1m_master.parquet")
    print("\n" + "=" * 92)
    print("FEASIBILITY GATE")
    print("=" * 92)
    coverage(dx, "DX")
    coverage(e6, "6E")
