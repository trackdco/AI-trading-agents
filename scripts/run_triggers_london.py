#!/usr/bin/env python3
"""LONDON SESSION triggers (Angus 27-Jul: 'lets make london profitable').

Runs the entry engine over the FIRST 2 HOURS of the London session for every trading
day in both data spans. The window is defined in Europe/London time (08:00-10:00) and
converted to ET per day, so the ~5 weeks/year when UK and US clocks are misaligned
(late Oct, mid-late Mar) shift correctly to 04:00-06:00 ET instead of 03:00-05:00.

Writes output/triggers_london.csv (same schema as the morning caches).

    python -m scripts.run_triggers_london
"""
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.triggers import detect_triggers  # noqa: E402

NY = ZoneInfo("America/New_York")
LON = ZoneInfo("Europe/London")


def london_window_et(day: str):
    """08:00-10:00 Europe/London for `day` (the UK calendar date), in ET."""
    start = pd.Timestamp(f"{day} 08:00", tz=LON).tz_convert(NY)
    end = pd.Timestamp(f"{day} 10:00", tz=LON).tz_convert(NY)
    return start, end


def main():
    mb = pd.read_parquet("data/reference/nq_1m_master.parquet")
    mb = mb[mb.ts_event >= pd.Timestamp("2025-05-20", tz=NY)]
    fb = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    df = (pd.concat([mb, fb], ignore_index=True)
          .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))

    days = sorted(set(pd.concat([
        pd.Series(pd.bdate_range("2025-06-02", "2025-12-31")),
        pd.Series(pd.bdate_range("2026-02-02", "2026-07-10")),
    ]).dt.strftime("%Y-%m-%d")))

    rows = []
    shifted = []
    for d in days:
        start, end = london_window_et(d)
        if start.hour != 3:
            shifted.append(d)
        seg = df[(df.ts_event >= start) & (df.ts_event <= end)]
        if seg.empty:
            continue
        trigs = detect_triggers(df, start=start, end=end)
        rows.extend(t.model_dump() for t in trigs)

    out = pd.DataFrame(rows)
    out.to_csv("output/triggers_london.csv", index=False)
    print(f"wrote output/triggers_london.csv: {len(out)} triggers over {len(days)} days")
    print(f"DST-shifted days (window 04:00-06:00 ET): {len(shifted)} — {shifted[:3]}...{shifted[-3:] if len(shifted)>3 else ''}")
    if len(out):
        ts = pd.to_datetime(out.ts, utc=True, format="mixed").dt.tz_convert("America/New_York")
        hm = ts.dt.hour + ts.dt.minute / 60
        print(f"trigger ET hour range: {hm.min():.2f} -> {hm.max():.2f}")
        print(out.pattern.value_counts().to_string())


if __name__ == "__main__":
    main()
