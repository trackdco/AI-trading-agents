#!/usr/bin/env python3
"""OOS detection (pass 14): checkpointed morning-band (07:45-11:00) trigger detection over
Mar 2 - Jul 15 2026 from the full committed dataset. Same band as the Feb cache so window
variants (10:15 vs 11:00 end) stay testable without re-detection. Re-running skips done days.

    python -m scripts._detect_marjul
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.triggers import detect_triggers  # noqa: E402

NY = "America/New_York"
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
CKPT = Path("output/triggers_marjul_checkpoint.csv")
FINAL = Path("output/triggers_marjul.csv")


def main():
    df = pd.read_parquet(DATA)
    done: set[str] = set()
    if CKPT.exists():
        prev = pd.read_csv(CKPT)
        done = set(pd.to_datetime(prev["ts"], utc=True).dt.tz_convert(NY).dt.strftime("%Y-%m-%d"))
        print(f"checkpoint: {len(prev)} triggers over {len(done)} days", flush=True)

    for d in pd.date_range("2026-03-02", "2026-07-15", freq="D"):
        day = f"{d:%Y-%m-%d}"
        if d.weekday() >= 5 or day in done:
            continue
        start = pd.Timestamp(f"{day} 07:45", tz=NY)
        end = pd.Timestamp(f"{day} 11:00", tz=NY)
        if df[(df["ts_event"] >= start) & (df["ts_event"] <= end)].empty:
            continue                                   # holiday / missing session
        trigs = detect_triggers(df, start=start, end=end)
        rows = pd.DataFrame([t.model_dump() for t in trigs])
        if not rows.empty:
            rows.to_csv(CKPT, mode="a", header=not CKPT.exists(), index=False)
        print(f"  {day}: {len(trigs)} triggers", flush=True)

    out = pd.read_csv(CKPT).sort_values("ts").reset_index(drop=True)
    out.to_csv(FINAL, index=False)
    print(f"wrote {FINAL} ({len(out)} triggers)", flush=True)


if __name__ == "__main__":
    main()
