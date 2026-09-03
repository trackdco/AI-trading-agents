#!/usr/bin/env python3
"""GC CONTINUOUS BUILDER — Databento raw batch -> volume-rolled 1m series.

    python -m scripts.gc_continuous

Input: data/reference/gc_1m_raw/glbx-mdp3-*.ohlcv-1m.csv.zst — ALL GC
instruments (outrights + calendar spreads). This script:
  1. keeps OUTRIGHT contracts only (symbol like GCM4; spreads have '-'),
  2. assigns each bar to its session-day (18:00 ET anchor, from UTC),
  3. picks the front month per session-day by total VOLUME (v-roll),
  4. splices those bars into one continuous series (unadjusted, like the
     NQ reference series), and
  5. records roll days — session-days whose front month differs from the
     prior session-day's. PD-level day-pairs that straddle a roll carry a
     price basis jump; the backtest layer excludes them.

Output:
  data/reference/gc_1m.parquet          ts_event (UTC), OHLCV, symbol
  data/reference/gc_roll_days.json      [sess_day, ...] (the day AFTER a roll)
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NY = "America/New_York"


def main() -> int:
    src = sorted(glob.glob(str(ROOT / "data/reference/gc_1m_raw/*.ohlcv-1m.csv.zst")))
    if not src:
        print("no raw file found")
        return 1
    print(f"reading {src[0]} ...", flush=True)
    df = pd.read_csv(src[0], usecols=["ts_event", "open", "high", "low",
                                      "close", "volume", "symbol"])
    df = df[~df.symbol.str.contains("-")]           # outrights only
    print(f"{len(df):,} outright rows", flush=True)
    ts = pd.to_datetime(df.ts_event, utc=True)
    ny = ts.dt.tz_convert(NY)
    df["sess_day"] = (ny - pd.Timedelta(hours=18)).dt.normalize().dt.date.astype(str)
    df["mi"] = ny

    vol = df.groupby(["sess_day", "symbol"]).volume.sum()
    front = vol.groupby(level=0).idxmax().map(lambda x: x[1])
    print(f"{len(front)} session-days", flush=True)

    keep = df.merge(front.rename("front"), left_on="sess_day",
                    right_index=True)
    keep = keep[keep.symbol == keep.front]
    keep = keep.sort_values("mi").drop_duplicates("mi")
    out = keep[["ts_event", "open", "high", "low", "close", "volume",
                "symbol"]].reset_index(drop=True)
    dst = ROOT / "data/reference/gc_1m.parquet"
    out.to_parquet(dst, index=False)

    fr = front.sort_index()
    rolls = [d for prev, d in zip(fr.index[:-1], fr.index[1:])
             if fr[prev] != fr[d]]
    (ROOT / "data/reference/gc_roll_days.json").write_text(json.dumps(rolls))
    mi = pd.to_datetime(out.ts_event, utc=True).dt.tz_convert(NY)
    print(f"DONE: {len(out):,} bars {mi.min()} -> {mi.max()}; "
          f"{len(rolls)} rolls -> {dst}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
