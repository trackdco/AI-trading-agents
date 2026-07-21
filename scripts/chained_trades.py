#!/usr/bin/env python3
"""Reconstruct the CHAINED AGENT's per-trade set (the correct baseline, not the champion
journal). For each day the agent chose a book (output/v07/chained2026/ledger.csv: act =
ROTATION->E3 / MOMENTUM->E4 / FLAT->nothing), keep that book's trades. Writes
output/chained_trades.csv with per-trade entry/exit detail for depth overlay.
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")


def main():
    led = pd.read_csv("output/v07/chained2026/ledger.csv")
    act = dict(zip(led.day, led.act))  # day -> ROTATION/MOMENTUM/FLAT
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    df = pd.read_parquet(DATA)
    base = load_backtest_config().model_copy(update={"win_start": dtime(8, 0), "win_end": dtime(10, 15),
                                                     "max_trades_per_day": 2})
    cfg_e3, cfg_e4 = books(base)   # E3 = rotation book (V8), E4 = momentum book
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        for book, cfg in (("ROTATION", cfg_e3), ("MOMENTUM", cfg_e4)):
            tr, _, _ = simulate(seg, trigs, cfg)
            for r in tr:
                if act.get(r.trade_date) != book:   # keep only the book the agent chose that day
                    continue
                rows.append(dict(day=r.trade_date, book=book, fill_ts=str(r.fill_ts), exit_ts=str(r.exit_ts),
                                 direction=r.direction, entry=r.entry, stop_initial=r.stop_initial,
                                 exit_price=r.exit_price, exit_reason=r.exit_reason, r_multiple=r.r_multiple,
                                 dollars=r.dollars, pattern=r.pattern, tf=getattr(r, "tf", "")))
    J = pd.DataFrame(rows).sort_values("fill_ts").reset_index(drop=True)
    J.to_csv("output/chained_trades.csv", index=False)
    print(f"chained-agent trades reconstructed: {len(J)}  ${J.dollars.sum():+,.0f}  win {J.dollars.gt(0).mean()*100:.0f}%")
    print("by month:")
    for m in MONTHS:
        s = J[J.day.str.startswith(m)]
        if len(s):
            print(f"  {m}  {len(s):3d}t  ${s.dollars.sum():+8,.0f}  win {s.dollars.gt(0).mean()*100:2.0f}%")
    print(f"\nby book: {J.book.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
