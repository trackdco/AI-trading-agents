#!/usr/bin/env python3
"""Re-tag the existing chained_trades.csv with the corrected A/B/B2 (Angus 22 Jul). Reclassifying
triggers only changed the pattern LABEL, not which triggers fire or their entries — so the trades
in chained_trades.csv are already correct; only `pattern` is stale. Match each trade to its v2
trigger (same day + direction, entry ~ entry_ref for E3 / close for E4, fill after the trigger)
and overwrite the tag. No re-simulation.

    python -m scripts.retag_chained
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import load
NY = "America/New_York"


def main():
    T = pd.read_csv("output/chained_trades.csv")
    T["fillts"] = pd.to_datetime(T.fill_ts, utc=True).dt.tz_convert(NY)
    trg = load(["output/triggers_feb_ob_v2.csv", "output/triggers_marjul_ob_v2.csv"])
    G = pd.DataFrame([{"day": t.ts[:10], "dir": t.direction, "entry_ref": t.entry_ref,
                       "close": t.close, "pattern": t.pattern} for t in trg])
    G["ts"] = pd.to_datetime([t.ts for t in trg], utc=True).tz_convert(NY)

    new = []
    for r in T.itertuples():
        cand = G[(G.day == r.day) & (G["dir"] == r.direction) & (G.ts <= r.fillts + pd.Timedelta(minutes=1))]
        if len(cand) == 0:
            new.append(r.pattern); continue
        # match on entry: E4/MOMENTUM enters at trigger close; E3/ROTATION at entry_ref
        ref = cand.close if r.book == "MOMENTUM" else cand.entry_ref
        cand = cand.assign(d=(ref - r.entry).abs())
        m = cand.sort_values("d").iloc[0]
        new.append(m.pattern if m.d <= 2.0 else r.pattern)   # 2pt tolerance, else keep old
    old = T.pattern.value_counts().to_dict()
    T["pattern"] = new
    T.drop(columns=["fillts"]).to_csv("output/chained_trades.csv", index=False)
    print(f"re-tagged {len(T)} chained trades")
    print(f"  old: {old}")
    print(f"  new: {T.pattern.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
