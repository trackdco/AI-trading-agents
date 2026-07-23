#!/usr/bin/env python3
"""Golden-window quality features that need raw fp_minutes (Angus 26-Jul golden campaign).

Per gold-window trade of the 7-60pt universe:
  bp5opp       1 if >=3 of the last 5 completed pre-fill 1-min deltas ran OPPOSED to the
               trade direction (limit fill into counter-flow = absorption at the level)
  lon_slope_d  direction-signed OLS slope of London-session (02:00-05:00 ET) cumulative
               delta. London ends hours before any gold fill -> zero lookahead.

Writes output/gold_quality.parquet (one row per gold trade, keyed day/book/fill).

    python -m scripts.gold_quality
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def main():
    T = pd.read_parquet("output/trade_matrix.parquet")
    T = T[(T.risk >= 7) & (T.risk <= 60) & (T.win_ == "gold")].copy()
    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index)
    M = M.sort_index()

    # London cumulative-delta OLS slope per session day
    lon_slope = {}
    hm = M.index.hour * 60 + M.index.minute
    lon = M[(hm >= 120) & (hm < 300)]
    for d, g in lon.groupby("sday"):
        if len(g) < 60:
            continue
        y = g.delta.cumsum().values
        x = np.arange(len(y), dtype=float)
        lon_slope[d] = np.polyfit(x, y, 1)[0]

    rows = []
    for t in T.itertuples():
        f = pd.Timestamp(t.fill).tz_convert(NY).floor("min")
        sgn = 1 if t.direction == "long" else -1
        seg = M.loc[f - pd.Timedelta(minutes=5): f - pd.Timedelta(minutes=1)]
        bp5opp = int((np.sign(seg.delta.values * sgn) < 0).sum() >= 3) if len(seg) >= 5 else np.nan
        ls = lon_slope.get(t.day, np.nan)
        rows.append({"day": t.day, "book": t.book, "fill": t.fill,
                     "bp5opp": bp5opp, "lon_slope_d": ls * sgn if ls == ls else np.nan})
    out = pd.DataFrame(rows)
    out.to_parquet("output/gold_quality.parquet")
    print(f"wrote output/gold_quality.parquet ({len(out)} gold trades, "
          f"bp5opp set on {int(out.bp5opp.notna().sum())}, lon_slope on {int(out.lon_slope_d.notna().sum())})")


if __name__ == "__main__":
    main()
