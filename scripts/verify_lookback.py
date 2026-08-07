#!/usr/bin/env python3
"""Prove the 15-day lookback cap is result-identical to full history (Angus 22 Jul). For a
stringent late month (full-context replays many months) and a 2026 month, simulate both books
with FULL context vs a 15-day cap and diff the trades. Identical -> cap adopted, no quality loss.
"""
import sys
from datetime import time as dtime
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load
from src.backtest.engine import load_backtest_config, simulate
NY = "America/New_York"


def trades(m, trig_src, df, base, cap_days):
    cfg_e3, cfg_e4 = books(base)
    end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
    if cap_days:
        start = pd.Timestamp(m + "-01", tz=NY) - pd.Timedelta(days=cap_days)
        seg = df[(df.ts_event >= start) & (df.ts_event <= end)].reset_index(drop=True)
    else:
        seg = df[df.ts_event <= end].reset_index(drop=True)
    trigs = [t for t in trig_src if t.ts[:7] == m]
    rows = []
    for book, cfg in (("E3", cfg_e3), ("E4", cfg_e4)):
        for r in simulate(seg, trigs, cfg)[0]:
            rows.append((book, str(r.fill_ts), r.direction, round(r.entry, 2), round(r.dollars, 2), r.pattern))
    return sorted(rows)


def main():
    base = load_backtest_config().model_copy(update={"win_start": dtime(8, 0),
                                                     "win_end": dtime(10, 15), "max_trades_per_day": 2})
    master = pd.read_parquet("data/reference/nq_1m_master.parquet")
    d26 = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    t25 = load(["output/triggers_hist2326_ob_v2.csv"])
    t26 = load(["output/triggers_feb_ob_v2.csv", "output/triggers_marjul_ob_v2.csv"])
    for m, src, df in (("2025-12", t25, master), ("2026-04", t26, d26)):
        full = trades(m, src, df, base, 0)
        capp = trades(m, src, df, base, 15)
        same = full == capp
        print(f"{m}: full {len(full)} trades, capped {len(capp)} trades  ->  IDENTICAL: {same}")
        if not same:
            fs, cs = set(full), set(capp)
            print(f"   only in full:   {len(fs-cs)}")
            print(f"   only in capped: {len(cs-fs)}")


if __name__ == "__main__":
    main()
