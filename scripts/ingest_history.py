#!/usr/bin/env python3
"""Pass-31: history INGEST — validate + merge any new 1m NQ file into the master dataset.

    python -m scripts.ingest_history <new_file.parquet|csv> [more files...]

Accepts parquet or CSV with columns ts_event/open/high/low/close/volume (extra columns
dropped; common Databento column spellings auto-mapped). Validates tz-awareness, OHLC
sanity, duplicate stamps, and reports coverage + gaps + roll-style price jumps, then
merges with data/reference/nq_1m_feb_jul2026.parquet into data/reference/nq_1m_master.parquet
(sorted, deduped — newer file wins on stamp collisions).

After ingest, the standard pipeline is:
  1. scripts/_amt over master  -> day types (extend output/amt_daytypes.csv)
  2. scripts/build_regime_vector.py (point DATA at master)
  3. scripts/_detect_parallel --start <first new day> --end <last> --out output/triggers_<tag>.csv
  4. scripts/_augment_ob.py (add cache to CACHES)
  5. scripts/l2_analog_benchmark.py + champion v1.1 OOS run
"""
import sys
from pathlib import Path

import pandas as pd

BASE = Path("data/reference/nq_1m_feb_jul2026.parquet")
MASTER = Path("data/reference/nq_1m_master.parquet")
NY = "America/New_York"
COLMAP = {"ts": "ts_event", "timestamp": "ts_event", "time": "ts_event",
          "ts_recv": "ts_event", "o": "open", "h": "high", "l": "low", "c": "close",
          "vol": "volume", "size": "volume"}
NEED = ["ts_event", "open", "high", "low", "close", "volume"]


def load_any(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    df = df.rename(columns={c: COLMAP.get(c.lower(), c.lower()) for c in df.columns})
    missing = [c for c in NEED if c not in df.columns]
    if missing:
        raise SystemExit(f"{path}: missing columns {missing}; have {list(df.columns)}")
    df = df[NEED].copy()
    df["ts_event"] = pd.to_datetime(df["ts_event"], utc=True).dt.tz_convert(NY)
    for c in NEED[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna()
    bad = ((df.high < df.low) | (df.high < df.open) | (df.high < df.close)
           | (df.low > df.open) | (df.low > df.close))
    if bad.any():
        print(f"  WARN {path.name}: {bad.sum()} OHLC-inconsistent rows dropped")
        df = df[~bad]
    return df


def report(df: pd.DataFrame, name: str):
    days = df.ts_event.dt.strftime("%Y-%m-%d")
    uniq = days.nunique()
    print(f"  {name}: {len(df):,} bars, {uniq} days, "
          f"{days.min()} -> {days.max()}")
    # weekday gaps > 3 consecutive missing days
    all_days = pd.bdate_range(days.min(), days.max()).strftime("%Y-%m-%d")
    missing = sorted(set(all_days) - set(days))
    if missing:
        print(f"  missing weekdays: {len(missing)} (holidays expected) "
              f"first few: {missing[:5]}")
    # roll-style jumps: day-boundary close->open gaps > 1%
    dd = df.set_index("ts_event").resample("1D").agg(o=("open", "first"), c=("close", "last")).dropna()
    jump = (dd.o - dd.c.shift()).abs() / dd.c.shift()
    big = jump[jump > 0.01]
    if len(big):
        print(f"  {len(big)} day-boundary jumps >1% (rolls/gaps): "
              f"{[d.strftime('%Y-%m-%d') for d in big.index[:6]]}")


def main(paths):
    frames = [load_any(BASE)]
    print("existing base:")
    report(frames[0], BASE.name)
    for p in paths:
        df = load_any(Path(p))
        report(df, Path(p).name)
        frames.append(df)
    merged = (pd.concat(frames[::-1])                      # newest-listed wins on dup stamps
              .drop_duplicates(subset="ts_event", keep="first")
              .sort_values("ts_event").reset_index(drop=True))
    merged.to_parquet(MASTER, index=False)
    print("\nMASTER:")
    report(merged, MASTER.name)
    print(f"wrote {MASTER} ({MASTER.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
