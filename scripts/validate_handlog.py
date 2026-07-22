#!/usr/bin/env python3
"""Validate the corrected A/B/B2 classifier against Angus's hand log (22 Jul). Runs the engine's
detect_triggers over Feb 2026 and matches each hand-logged trade (date + entry time + TF +
direction) to the engine trigger, then compares Angus's Pattern label to the engine's. Hand-log
Entry Time is the candle OPEN (TradingView); engine ts is candle CLOSE = open + TF, so the match
applies that +TF shift.

    python -m scripts.validate_handlog
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
    start = pd.Timestamp("2026-02-01", tz=NY); end = pd.Timestamp("2026-03-01", tz=NY)
    print("running detect_triggers over Feb 2026 (slow)...", flush=True)
    trigs = detect_triggers(df, start=start, end=end)
    E = pd.DataFrame([{"ts": pd.Timestamp(t.ts), "tf": t.tf, "dir": t.direction,
                       "pattern": t.pattern, "kind": t.kind} for t in trigs])
    print(f"engine triggers in Feb: {len(E)}  ({E.pattern.value_counts().to_dict()})", flush=True)

    H = pd.read_csv("data/reference/feb2026_hand_log.csv")
    H.columns = [c.strip() for c in H.columns]
    H["date"] = pd.to_datetime(H["Date"], format="%B %d, %Y").dt.strftime("%Y-%m-%d")
    H["etf"] = H["Entry TF"].str.upper().str.strip().map(TFMAP)
    H["etime"] = H["Entry Time"].astype(str).str.strip()
    rows = []
    for h in H.itertuples():
        try:
            open_t = pd.Timestamp(f"{h.date} {h.etime}", tz=NY)
        except Exception:
            rows.append((h.Pattern, None, "bad-time")); continue
        tfmin = int(h.etf.replace("min", "")) if isinstance(h.etf, str) else None
        close_t = open_t + pd.Timedelta(minutes=tfmin) if tfmin else open_t
        # match engine trigger: same tf+dir, ts within +-2 min of the +TF-shifted close
        cand = E[(E.tf == h.etf) & (E["dir"] == h.Direction) &
                 ((E.ts - close_t).abs() <= pd.Timedelta(minutes=2))]
        if len(cand) == 0:
            # relax: any tf, same dir, near the close time
            cand = E[(E["dir"] == h.Direction) & ((E.ts - close_t).abs() <= pd.Timedelta(minutes=3))]
        eng_pat = cand.iloc[(cand.ts - close_t).abs().argmin()].pattern if len(cand) else None
        rows.append((h.Pattern, eng_pat, "matched" if eng_pat else "no-engine-trigger"))
    R = pd.DataFrame(rows, columns=["angus", "engine", "status"])
    print(f"\nhand-log trades: {len(R)}   matched to an engine trigger: {(R.status=='matched').sum()}")
    m = R[R.status == "matched"]
    if len(m):
        agree = (m.angus == m.engine).mean() * 100
        print(f"label agreement on matched trades: {agree:.0f}%\n")
        print("=== Angus (rows) vs engine (cols) ===")
        print(pd.crosstab(m.angus, m.engine))
    print(f"\nunmatched (engine didn't fire where Angus traded): {(R.status!='matched').sum()}")
    print(R.to_string())


if __name__ == "__main__":
    main()
