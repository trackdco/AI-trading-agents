#!/usr/bin/env python3
"""Spec 1 Step 6 deliverable: detect triggers over Feb 2-27 2026 -> output/triggers_feb.csv.

Runs the entry-window morning band each trading day (07:45-11:00 ET, covering every
reference-trade entry time 8:06-10:52). Spot-check: triggers must exist at the four
clearest reference trades (Feb 4 09:48, Feb 11 09:48, Feb 17 09:50, Feb 25 09:25).

    python scripts/run_triggers_feb.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.triggers import detect_triggers  # noqa: E402

NY = "America/New_York"


def main():
    df = pd.read_parquet("data/nq_1m.parquet")
    days = pd.date_range("2026-02-02", "2026-02-27", freq="D")
    rows = []
    for d in days:
        if d.weekday() >= 5:
            continue
        start = pd.Timestamp(f"{d:%Y-%m-%d} 07:45", tz=NY)
        end = pd.Timestamp(f"{d:%Y-%m-%d} 11:00", tz=NY)
        if df[(df["ts_event"] >= start) & (df["ts_event"] <= end)].empty:
            continue
        trigs = detect_triggers(df, start=start, end=end)
        rows.extend(t.model_dump() for t in trigs)
        print(f"  {d:%Y-%m-%d}: {len(trigs)} triggers", flush=True)

    out = pd.DataFrame(rows)
    Path("output").mkdir(exist_ok=True)
    out.to_csv("output/triggers_feb.csv", index=False)
    print(f"\nwrote output/triggers_feb.csv: {len(out)} triggers")

    # spot-check. Hand-log times are TradingView OPEN-labeled; engine bars are CLOSE-labeled,
    # so a hand TF-minute candle at t maps to the engine bar stamped at its bin's CLOSE
    # (e.g. Feb 11 "09:48 3M" = engine 09:51; Feb 4 "09:48 5M" sits inside the 09:45-09:50
    # bin -> engine 09:50). Step-8 calibration matching must apply the same +TF shift.
    checks = [("2026-02-04 09:48", "5min", "short"), ("2026-02-11 09:48", "3min", "short"),
              ("2026-02-17 09:50", "2min", "short"), ("2026-02-25 09:25", "5min", "long")]
    ts = pd.to_datetime(out["ts"]) if not out.empty else pd.Series([], dtype="datetime64[ns, UTC]")
    print("\nspot-check (trigger within 5 min of each reference; mapped bar = TV-open + TF):")
    for c, tf, direction in checks:
        ref = pd.Timestamp(c, tz=NY)
        near = out[(ts - ref).abs() <= pd.Timedelta(minutes=5)] if not out.empty else out
        tag = "OK" if len(near) else "MISSING"
        detail = ", ".join(f"{pd.Timestamp(r.ts):%H:%M} {r.tf} {r.direction}" for r in near.itertuples()) if len(near) else ""
        print(f"  [{tag}] {c} ({tf} {direction}): {detail}")
        tfm = int(tf.replace("min", ""))
        mapped = ref - pd.Timedelta(minutes=(ref.hour * 60 + ref.minute) % tfm) + pd.Timedelta(minutes=tfm)
        at = out[ts == mapped] if not out.empty else out
        got = ", ".join(f"{r.tf} {r.direction} {r.kind}/{r.pattern}" for r in at.itertuples()) or "no trigger"
        print(f"       mapped engine bar {mapped:%H:%M}: {got}")


if __name__ == "__main__":
    main()
