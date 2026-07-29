#!/usr/bin/env python3
"""FAST hand-log A/B/B2 validation (22 Jul). Instead of detecting triggers across all of Feb,
evaluate ONLY the ~28 candles Angus actually traded: for each hand-log trade, run detect_triggers
on a narrow window around that candle and read the engine's pattern. Hand-log Entry Time is the
candle OPEN; engine ts is close = open + TF.

    python -m scripts.validate_handlog_fast
"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.triggers import detect_triggers
NY = "America/New_York"
TFMAP = {"1M": "1min", "2M": "2min", "3M": "3min", "5M": "5min"}


def main():
    df = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    H = pd.read_csv("data/reference/feb2026_hand_log.csv")
    H.columns = [c.strip() for c in H.columns]
    H["date"] = pd.to_datetime(H["Date"], format="%B %d, %Y").dt.strftime("%Y-%m-%d")
    H["etf"] = H["Entry TF"].str.upper().str.strip().map(TFMAP)
    H["etime"] = H["Entry Time"].astype(str).str.strip()
    rows = []
    for h in H.itertuples():
        try:
            open_t = pd.Timestamp(f"{h.date} {h.etime}", tz=NY)
            tfmin = int(h.etf.replace("min", ""))
        except Exception:
            rows.append((h.date, h.etime, h.Direction, h.Pattern, None, "bad-row")); continue
        close_t = open_t + pd.Timedelta(minutes=tfmin)
        trigs = detect_triggers(df, start=open_t - pd.Timedelta(minutes=3),
                                end=close_t + pd.Timedelta(minutes=3))
        # prefer same TF + direction near the close; then any TF same direction; then any near
        def near(ts):
            return abs((pd.Timestamp(ts) - close_t).total_seconds())
        cand = [t for t in trigs if t.tf == h.etf and t.direction == h.Direction and near(t.ts) <= 180]
        if not cand:
            cand = [t for t in trigs if t.direction == h.Direction and near(t.ts) <= 180]
        if not cand:
            cand = [t for t in trigs if near(t.ts) <= 120]
        eng = min(cand, key=lambda t: near(t.ts)) if cand else None
        rows.append((h.date, h.etime, h.Direction, h.Pattern,
                     eng.pattern if eng else None, "matched" if eng else "no-trigger"))
    R = pd.DataFrame(rows, columns=["date", "time", "dir", "angus", "engine", "status"])
    m = R[R.status == "matched"]
    print(f"hand-log trades: {len(R)}   engine fired a trigger there: {len(m)}")
    if len(m):
        print(f"label agreement on matched: {(m.angus==m.engine).mean()*100:.0f}%\n")
        print("Angus (rows) vs engine (cols):")
        print(pd.crosstab(m.angus, m.engine))
    print(f"\nno-trigger (engine saw no setup where Angus traded): {(R.status=='no-trigger').sum()}")
    print("\n" + R.to_string())


if __name__ == "__main__":
    main()
