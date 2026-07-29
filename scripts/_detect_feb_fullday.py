#!/usr/bin/env python3
"""FULL-DAY checkpointed Feb trigger detection (ANGUS pass-12 discovery): detects over the
whole CME session per trading day — (D-1) 18:00 ET -> D 16:00 ET — instead of the usual
07:45-11:00 morning band. Checkpoints per day; re-running skips completed days.

Writes output/triggers_feb_fullday.csv (does NOT touch the morning cache triggers_feb.csv).

    python -m scripts._detect_feb_fullday
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.triggers import detect_triggers  # noqa: E402

NY = "America/New_York"
CKPT = Path("output/triggers_feb_fullday_checkpoint.csv")
FINAL = Path("output/triggers_feb_fullday.csv")


def main():
    full, ref = Path("data/nq_1m.parquet"), Path("data/reference/nq_1m_feb2026.parquet")
    df = pd.read_parquet(full if full.exists() else ref)
    feb = df[(df["ts_event"] >= pd.Timestamp("2026-02-01 18:00", tz=NY)) &
             (df["ts_event"] <= pd.Timestamp("2026-02-27 17:00", tz=NY))].reset_index(drop=True)

    done_days: set[str] = set()
    if CKPT.exists():
        prev = pd.read_csv(CKPT)
        # a day is complete only if its 15:xx afternoon triggers could exist; mark by the
        # session label column written per chunk
        done_days = set(prev["session_day"].unique())
        print(f"checkpoint: {len(prev)} triggers over {len(done_days)} days", flush=True)

    for d in pd.date_range("2026-02-02", "2026-02-27", freq="D"):
        day = f"{d:%Y-%m-%d}"
        if d.weekday() >= 5 or day in done_days:
            continue
        start = pd.Timestamp(day, tz=NY) - pd.Timedelta(hours=6)      # (D-1) 18:00
        end = pd.Timestamp(f"{day} 16:00", tz=NY)
        if feb[(feb["ts_event"] >= start) & (feb["ts_event"] <= end)].empty:
            continue
        trigs = detect_triggers(feb, start=start, end=end)
        rows = pd.DataFrame([t.model_dump() for t in trigs])
        rows["session_day"] = day
        rows.to_csv(CKPT, mode="a", header=not CKPT.exists(), index=False)
        print(f"  {day}: {len(trigs)} triggers (full session, checkpointed)", flush=True)

    out = pd.read_csv(CKPT).sort_values("ts").reset_index(drop=True)
    out.drop(columns=["session_day"]).to_csv(FINAL, index=False)
    print(f"wrote {FINAL} ({len(out)} triggers)", flush=True)


if __name__ == "__main__":
    main()
