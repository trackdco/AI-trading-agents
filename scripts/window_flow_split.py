#!/usr/bin/env python3
"""Split the golden window: does flow-check alignment SHIFT with the clock?

ANGUS 2026-07-26: "break the golden window a bit. lets go 9:40-10, and then 10-10:15.
maybe we'll see specific order flow only aligns at certain times... remember above all
i care about consistent profitability."

One sim of 09:40-10:15 (full TradeRecords, same trade population as the golden reference
probe), features via the canonical src/canon/features.py implementations, then the SAME
both-years survival table per sub-window, side by side with the cached 10:15-10:30 matrix.
The question: where exactly does the flow-confirmation regime flip from golden's
"with-flow" to late-a's "fade-flow"?

    python -m scripts.window_flow_split
"""
from __future__ import annotations

import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.late_a_orderflow as LA          # noqa: E402  (reuse sim/features/analyse)

GOLD_OUT = Path("output/golden_flow_matrix.parquet")


def main() -> None:
    if GOLD_OUT.exists():
        G = pd.read_parquet(GOLD_OUT)
        print(f"loaded cached {GOLD_OUT} ({len(G)} trades)")
    else:
        LA.WS, LA.WE = dtime(9, 40), dtime(10, 15)   # rebind window for the sim leg
        J = LA.run_sim()
        print(f"sim complete: {len(J)} trades")
        G = LA.add_features(J)
        G.to_parquet(GOLD_OUT)
        print(f"wrote {GOLD_OUT}")

    et = pd.to_datetime(G.fill_ts.str.replace("T", " "), utc=True, format="mixed")
    hm = et.dt.tz_convert("America/New_York")
    G["hm"] = hm.dt.hour * 60 + hm.dt.minute

    LA.analyse(G[G.hm < 600].copy(), label="09:40-10:00")
    LA.analyse(G[G.hm >= 600].copy(), label="10:00-10:15")

    late = pd.read_parquet("output/late_a_flow_matrix.parquet")
    LA.analyse(late, label="10:15-10:30 (recap)")


if __name__ == "__main__":
    main()
