#!/usr/bin/env python3
"""Condense the raw CVD footprint (per-minute-per-price aggressor volume) into a
per-minute delta/cumulative-delta series for April 2026.

SIGN CORRECTED 2026-09-05. This file previously documented and computed delta = A - B.
That is BACKWARDS. Measured over 207,520 matched minutes against the 1m master bars,
corr(minute price change, B - A) = +0.657 and corr(..., A - B) = -0.657. So:
    B = BUY aggressor (lifted the offer), A = SELL aggressor (hit the bid), delta = B - A
which matches data/reference/cvd/README.md. Any result built with the old sign is inverted.

    python -m scripts.build_cvd_minute  -> output/cvd_minute_apr2026.csv
"""
import pandas as pd

TZ = "America/New_York"


def main():
    df = pd.read_parquet("data/reference/cvd/footprint_apr2026.parquet")
    g = df.groupby(["ts_minute", "side"]).volume.sum().unstack("side").fillna(0)
    g = g.rename(columns={"B": "buy_vol", "A": "sell_vol"})
    g["delta"] = g.buy_vol - g.sell_vol
    g.index = g.index.tz_convert(TZ)
    g = g.sort_index()
    g["cum_delta_day"] = g.groupby(g.index.date).delta.cumsum()
    g.to_csv("output/cvd_minute_apr2026.csv")
    print(f"wrote output/cvd_minute_apr2026.csv ({len(g)} minutes, "
          f"{g.index.date[0]}..{g.index.date[-1]})")


if __name__ == "__main__":
    main()
