#!/usr/bin/env python3
"""LONDON triggers for the sealed 2023/24 holdout days — SAME detector, SAME window rule.

`run_triggers_london.py` hard-codes the fit span (2025-06 -> 2026-07) and its bar sources.
Rather than fork the detection logic, this imports the identical `detect_triggers` and the
identical `london_window_et` (08:00-10:00 Europe/London, which lands on 03:00-05:00 ET
normally and 04:00-06:00 ET during the ~5 weeks a year UK and US clocks disagree — three of
the six sealed months straddle a changeover, so this is not a detail).

Bars come from nq_1m_master, sliced to LOOKBACK_DAYS before each day rather than handed the
whole 1.25M-bar file: `detect_triggers` calls `indicators_asof` once per candidate bar, so
the segment size is the entire cost. Every indicator is daily- or session-anchored, and the
fit-window run gave its earliest days only 13 days of history, so 30 is generous either way.
Verified lookback-invariant: 60d/30d/20d return byte-identical trigger lists on sampled days.

Writes output/triggers_london_holdout.csv (same schema as output/triggers_london.csv).

    python -m scripts.holdout_london_triggers
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_triggers_london import london_window_et  # noqa: E402
from src.engine.triggers import detect_triggers  # noqa: E402

NY = "America/New_York"
MASTER = ROOT / "data/reference/nq_1m_master.parquet"
SEALED = ROOT / "data/reference/holdout_2023_24_days.csv"
OUT = ROOT / "output/triggers_london_holdout.csv"
LOOKBACK_DAYS = 30


def main() -> None:
    days = sorted(pd.read_csv(SEALED, dtype=str)["day"])
    bars = pd.read_parquet(MASTER)
    print(f"{len(days)} sealed days | {len(bars):,} master bars "
          f"({bars.ts_event.min()} .. {bars.ts_event.max()})\n", flush=True)

    rows, shifted, empty = [], [], []
    for i, d in enumerate(days, 1):
        start, end = london_window_et(d)
        if start.hour != 3:
            shifted.append(d)
        seg = bars[(bars.ts_event >= start - pd.Timedelta(days=LOOKBACK_DAYS))
                   & (bars.ts_event <= end)].reset_index(drop=True)
        if seg.empty or seg.ts_event.max() < start:
            empty.append(d)
            continue
        trigs = detect_triggers(seg, start=start, end=end)
        rows.extend(t.model_dump() for t in trigs)
        print(f"  [{i:>3}/{len(days)}] {d} {start.strftime('%H:%M')}-{end.strftime('%H:%M')} ET "
              f"-> {len(trigs):>3} triggers (total {len(rows)})", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"\nwrote {OUT.relative_to(ROOT)}: {len(out)} triggers over "
          f"{len(days) - len(empty)} days")
    print(f"DST-shifted days (04:00-06:00 ET): {len(shifted)}")
    if empty:
        print(f"NO BARS on {len(empty)} days: {empty}")
    if len(out):
        ts = pd.to_datetime(out.ts, utc=True, format="mixed").dt.tz_convert(NY)
        hm = ts.dt.hour + ts.dt.minute / 60
        print(f"trigger ET hour range: {hm.min():.2f} -> {hm.max():.2f}")
        print(out.pattern.value_counts().to_string())


if __name__ == "__main__":
    main()
