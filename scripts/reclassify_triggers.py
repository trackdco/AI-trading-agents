#!/usr/bin/env python3
"""FAST trigger reclassification (Angus 22 Jul). The trigger DETECTION (which candles fire, their
shape/kind, entry_ref) is unchanged — only the A/B/B2 LABEL rule changed. So we relabel the cached
trigger CSVs instead of re-running the slow per-candle detector:

  rejection_block            -> B2
  displacement -> A  if price TOUCHED the DAILY-VWAP ±2σ band in the trade direction's OPPOSITE
                     extreme within the last EXT_LOOKBACK entry-TF bars (a wick/touch, tol=0.5pt)
               -> B  otherwise (with-trend continuation)

Uses the engine's own vectorized daily_vwap() so the band matches indicators_asof exactly.

    python -m scripts.reclassify_triggers
"""
import sys
from datetime import time as dtime
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import daily_vwap
NY = "America/New_York"
EXT_LOOKBACK = 10
TOL = 0.5
TFMIN = {"1min": 1, "2min": 2, "3min": 3, "5min": 5, "15min": 15}


def band_frame(parquet):
    df = pd.read_parquet(parquet)
    dv = daily_vwap(df, bands=[1, 2, 3])
    B = pd.DataFrame({"ts": pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY),
                      "low": df["low"].values, "high": df["high"].values,
                      "lo2": dv["lower_2"].values, "up2": dv["upper_2"].values})
    return B.set_index("ts").sort_index()


def reclassify(trig_csv, B, out_csv):
    T = pd.read_csv(trig_csv)
    T["tsny"] = pd.to_datetime(T.ts, utc=True).dt.tz_convert(NY)
    lo, up = B["low"], B["high"]
    lo2, up2 = B["lo2"], B["up2"]
    new = []
    for r in T.itertuples():
        if r.kind == "rejection_block":
            new.append("B2"); continue
        tfm = TFMIN.get(r.tf, 3)
        w0 = r.tsny - pd.Timedelta(minutes=EXT_LOOKBACK * tfm)
        sl = B.loc[w0:r.tsny]
        if len(sl) == 0:
            new.append("B"); continue
        if r.direction == "long":
            touched = bool((sl["low"] <= sl["lo2"] + TOL).any())
        else:
            touched = bool((sl["high"] >= sl["up2"] - TOL).any())
        new.append("A" if touched else "B")
    T["pattern"] = new
    T.drop(columns=["tsny"]).to_csv(out_csv, index=False)
    return pd.Series(new).value_counts().to_dict()


def main():
    jobs = [
        ("output/triggers_feb_ob.csv", "data/reference/nq_1m_feb_jul2026.parquet", "output/triggers_feb_ob_v2.csv"),
        ("output/triggers_marjul_ob.csv", "data/reference/nq_1m_feb_jul2026.parquet", "output/triggers_marjul_ob_v2.csv"),
        ("output/triggers_hist2326_ob.csv", "data/reference/nq_1m_master.parquet", "output/triggers_hist2326_ob_v2.csv"),
    ]
    cache = {}
    for trig, pq, out in jobs:
        if pq not in cache:
            print(f"computing daily-VWAP bands from {Path(pq).name} ...", flush=True)
            cache[pq] = band_frame(pq)
        dist = reclassify(trig, cache[pq], out)
        print(f"  {Path(trig).name} -> {Path(out).name}   {dist}", flush=True)


if __name__ == "__main__":
    main()
