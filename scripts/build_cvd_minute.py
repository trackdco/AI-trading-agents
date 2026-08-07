#!/usr/bin/env python3
"""Condense the raw CVD footprint (per-minute-per-price aggressor volume) into a
per-minute delta/cumulative-delta series for April 2026. Side 'A' = ask-lift (buy
aggressor), 'B' = bid-hit (sell aggressor); delta = A - B.

    python -m scripts.build_cvd_minute  -> output/cvd_minute_apr2026.csv
"""
import pandas as pd

TZ = "America/New_York"


def main():
    df = pd.read_parquet("data/reference/cvd/footprint_apr2026.parquet")
    g = df.groupby(["ts_minute", "side"]).volume.sum().unstack("side").fillna(0)
    g = g.rename(columns={"A": "buy_vol", "B": "sell_vol"})
    g["delta"] = g.buy_vol - g.sell_vol
    g.index = g.index.tz_convert(TZ)
    g = g.sort_index()
    g["cum_delta_day"] = g.groupby(g.index.date).delta.cumsum()
    g.to_csv("output/cvd_minute_apr2026.csv")
    print(f"wrote output/cvd_minute_apr2026.csv ({len(g)} minutes, "
          f"{g.index.date[0]}..{g.index.date[-1]})")


if __name__ == "__main__":
    main()
