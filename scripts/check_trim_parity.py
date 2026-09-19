"""Pin FRAME_WARMUP: the trimmed per-bar detector frame must be trigger-identical to a
much deeper one on real reference days.

ny_run hands the detector a frame trimmed to `bar_ts - FRAME_WARMUP` (14 days) instead
of the full accumulated history — the full rebuild cost ~1 real minute per in-band bar
on the box (the R13 practice-day replay took 3.5 hours; a live bar would flirt with the
60s budget). detect_triggers' deepest lookback is the 10-day OTE window, so 14 days is
expected to be exhaustive; this script PROVES it by comparing against a 60-day frame.

Run (repo root; ~2-5 min):

    python -m scripts.check_trim_parity

Pinned 2026-08-01 (R13 cert weekend): 2026-07-14 / 2026-07-09 / 2026-06-24 all
IDENTICAL (72 / 32 / 69 triggers), and the same days at 100x prices fire 1 / 0 / 0 —
the practice-day zero-trigger failure, reproduced and closed.
"""
from __future__ import annotations

import pandas as pd

from src.engine.triggers import detect_triggers

NY = "America/New_York"
REFERENCE = "data/reference/nq_1m_master.parquet"
DAYS = ("2026-07-14", "2026-07-09", "2026-06-24")
TRIM_DAYS, DEEP_DAYS = 14, 60          # TRIM must match scripts.ny_run.FRAME_WARMUP


def _trigs(frame: pd.DataFrame, day: str) -> list:
    lo = pd.Timestamp(f"{day} 07:45", tz=NY)
    hi = pd.Timestamp(f"{day} 11:00", tz=NY)
    return [t for t in detect_triggers(frame, start=lo, end=hi)
            if t.pattern != "unclassified"]


def _key(t) -> tuple:
    return (str(t.ts), t.direction, round(float(t.entry_ref), 2), t.pattern)


def main() -> int:
    df = pd.read_parquet(REFERENCE)
    df["ts_event"] = pd.to_datetime(df["ts_event"])
    failures = 0
    for day in DAYS:
        anchor = pd.Timestamp(day, tz=NY)
        end = anchor + pd.Timedelta(days=1)
        trim = df[(df.ts_event >= anchor - pd.Timedelta(days=TRIM_DAYS))
                  & (df.ts_event <= end)]
        deep = df[(df.ts_event >= anchor - pd.Timedelta(days=DEEP_DAYS))
                  & (df.ts_event <= end)]
        a, b = _trigs(trim, day), _trigs(deep, day)
        same = sorted(map(_key, a)) == sorted(map(_key, b))
        failures += 0 if same else 1
        print(f"{day}:  {TRIM_DAYS}d={len(a)}  {DEEP_DAYS}d={len(b)}  "
              f"{'IDENTICAL' if same else 'DIFFER  <-- FRAME_WARMUP too shallow'}")
    print("TRIM PARITY:", "PASS" if failures == 0 else f"FAIL ({failures} day(s) differ)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
