#!/usr/bin/env python3
"""Checkpointed Feb trigger detection: detects per day, appending each day's triggers to
a checkpoint CSV immediately. Re-running skips completed days, so a killed process loses
at most one day of work. When all days are present, writes output/triggers_feb.csv (the
runner's cache) in one shot.

    python -m scripts._detect_feb_checkpoint
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.triggers import detect_triggers  # noqa: E402

NY = "America/New_York"
CKPT = Path("output/triggers_feb_checkpoint.csv")
FINAL = Path("output/triggers_feb.csv")


def main():
    full, ref = Path("data/nq_1m.parquet"), Path("data/reference/nq_1m_feb2026.parquet")
    df = pd.read_parquet(full if full.exists() else ref)
    feb = df[(df["ts_event"] >= pd.Timestamp("2026-02-01 18:00", tz=NY)) &
             (df["ts_event"] <= pd.Timestamp("2026-02-27 17:00", tz=NY))].reset_index(drop=True)

    done_days: set[str] = set()
    if CKPT.exists():
        prev = pd.read_csv(CKPT)
        done_days = set(pd.to_datetime(prev["ts"]).dt.strftime("%Y-%m-%d"))
        print(f"checkpoint has {len(prev)} triggers over {len(done_days)} days", flush=True)

    for d in pd.date_range("2026-02-02", "2026-02-27", freq="D"):
        day = f"{d:%Y-%m-%d}"
        if d.weekday() >= 5 or day in done_days:
            continue
        start = pd.Timestamp(f"{day} 07:45", tz=NY)
        end = pd.Timestamp(f"{day} 11:00", tz=NY)
        if feb[(feb["ts_event"] >= start) & (feb["ts_event"] <= end)].empty:
            continue
        trigs = detect_triggers(feb, start=start, end=end)
        rows = pd.DataFrame([t.model_dump() for t in trigs])
        rows.to_csv(CKPT, mode="a", header=not CKPT.exists(), index=False)
        print(f"  {day}: {len(trigs)} triggers (checkpointed)", flush=True)

    out = pd.read_csv(CKPT).sort_values("ts").reset_index(drop=True)
    out.to_csv(FINAL, index=False)
    print(f"wrote {FINAL} ({len(out)} triggers)", flush=True)


if __name__ == "__main__":
    main()
