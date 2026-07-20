#!/usr/bin/env python3
"""Recover per-trade MFE/MAE timestamps for the 30 April-2026 champion trades by
replaying 1m bars from entry to exit. journal_champion.csv stores mfe_r/mae_r as
VALUES but not WHEN they happened — CVD/heatmap testing needs the timestamp of each
excursion peak to join against per-minute order-flow/depth data.

    python -m scripts.replay_april_trade_timestamps  -> output/april_trade_timestamps.csv

Validates against the stored mfe_r/mae_r (should match within float rounding) before
trusting the recovered timestamps.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MASTER = "data/reference/nq_1m_master.parquet"
JOURNAL = "output/journal_champion.csv"
TZ = "America/New_York"


def main():
    j = pd.read_csv(JOURNAL)
    apr = j[j.day.str.startswith("2026-04")].copy()
    bars = pd.read_parquet(MASTER)
    bars = bars.set_index("ts_event").sort_index()

    rows = []
    mismatches = 0
    for _, t in apr.iterrows():
        entry_ts = pd.Timestamp(f"{t.day} {t.fill}", tz=TZ)
        exit_ts = entry_ts + pd.Timedelta(minutes=int(t.hold_min))
        window = bars.loc[entry_ts:exit_ts]
        if window.empty:
            print(f"{t.day} {t.fill}: NO BARS in window, skipping")
            continue
        risk = t.risk_pts
        if t.dir == "long":
            fav = (window.high - t.entry) / risk
            adv = (window.low - t.entry) / risk
        else:
            fav = (t.entry - window.low) / risk
            adv = (t.entry - window.high) / risk
        mfe_ts = fav.idxmax()
        mae_ts = adv.idxmin()
        mfe_computed, mae_computed = round(fav.max(), 2), round(adv.min(), 2)
        ok = abs(mfe_computed - t.mfe_r) < 0.15 and abs(mae_computed - t.mae_r) < 0.15
        if not ok:
            mismatches += 1
            print(f"{t.day} {t.fill}: MISMATCH stored mfe={t.mfe_r}/mae={t.mae_r} "
                  f"vs computed mfe={mfe_computed}/mae={mae_computed}")
        rows.append(dict(day=t.day, fill=t.fill, dir=t.dir, entry=t.entry, risk_pts=risk,
                          entry_ts=entry_ts, exit_ts=exit_ts,
                          mfe_ts=mfe_ts, mfe_r_computed=mfe_computed, mfe_r_stored=t.mfe_r,
                          mae_ts=mae_ts, mae_r_computed=mae_computed, mae_r_stored=t.mae_r,
                          win=t.win, dollars=t.dollars, exit_reason=t.exit_reason))
    out = pd.DataFrame(rows)
    out.to_csv("output/april_trade_timestamps.csv", index=False)
    print(f"\n{len(out)} trades replayed, {mismatches} mismatches "
          f"(tolerance 0.15R -> likely trailing/scaling divergence from raw excursion)")


if __name__ == "__main__":
    main()
