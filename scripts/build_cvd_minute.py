#!/usr/bin/env python3
"""Condense the raw CVD footprint (per-minute-per-price aggressor volume) into a
per-minute delta/cumulative-delta series for April 2026.

Side 'B' = buyer-aggressor (lifted the offer), 'A' = seller-aggressor (hit the bid);
delta = B - A. This sign was INVERTED here until 2026-08-06 -- the docstring claimed
"A = ask-lift (buy aggressor)" and the code computed A - B. Settled empirically against
realised London-window direction over 287 sessions (r = +0.78 on large moves for B - A);
see src/engine/footprint for the audit. Use footprint.signed_delta, never a hand-rolled
subtraction.

Reads through src/engine/footprint so the front-month band-clean is applied: the raw
pull carries calendar-spread and back-month prints (measured 3.91% of London-window
volume, concentrated on roll weeks).

    python -m scripts.build_cvd_minute  -> output/cvd_minute_apr2026.csv
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.engine import footprint as fp  # noqa: E402

TZ = "America/New_York"
SRC = ROOT / "data/reference/cvd/footprint_apr2026.parquet"


def main():
    bands = fp.front_month_bands()
    df = fp.load_footprint([SRC], bands)
    delta = fp.signed_delta(df, by=("ts_minute",)).rename("delta")
    sides = df.groupby(["ts_minute", "side"]).volume.sum().unstack("side").fillna(0)
    g = pd.DataFrame({
        "buy_vol": sides.get("B", 0.0),
        "sell_vol": sides.get("A", 0.0),
    }).join(delta)
    g.index = g.index.tz_convert(TZ)
    g = g.sort_index()
    g["cum_delta_day"] = g.groupby(g.index.date).delta.cumsum()
    out = ROOT / "output/cvd_minute_apr2026.csv"
    g.to_csv(out)
    print(f"wrote {out} ({len(g)} minutes, {g.index.date[0]}..{g.index.date[-1]})")


if __name__ == "__main__":
    main()
