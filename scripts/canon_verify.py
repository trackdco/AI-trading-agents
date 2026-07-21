#!/usr/bin/env python3
"""Verify the CANON on E3-only (the reclaim entry Angus trades; resting limit => intended==actual
stop, so the max/min-stop caps enforce his EXACT rule). Golden 09:40-10:15 (canon 30-50) +
pre-market 08:00-09:30 (canon <=15), canon config defaults. Reports actual-stop bounds + months.
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


def run(win, allt, df):
    cfg = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None,
        "win_start": win[0], "win_end": win[1], "max_trades_per_day": 2})
    cfg_e3, _ = books(cfg)   # E3 ONLY (the reclaim entry)
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        tr, _, _ = simulate(seg, trigs, cfg_e3)
        for r in tr:
            ft = pd.Timestamp(r.fill_ts).time()
            if win[0] <= ft < win[1]:
                rows.append(dict(month=m, dollars=r.dollars, win=r.dollars > 0,
                                 actual=abs(r.entry - r.stop_initial)))
    return pd.DataFrame(rows)


def rep(J, label):
    mg = J.groupby("month").dollars.sum()
    g = (mg > 0).sum()
    print(f"{label}: {len(J)}t  ${J.dollars.sum():+,.0f}  win {J.win.mean()*100:.0f}%  "
          f"green {g}/{len(mg)}  | actual stop {J.actual.min():.0f}-{J.actual.max():.0f}pt "
          f"(outside[30,50]:{((J.actual<30)|(J.actual>50)).sum()})")
    for m in MONTHS:
        s = J[J.month == m]
        if len(s):
            print(f"    {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%  {'GRN' if s.dollars.sum()>0 else 'red'}")


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    df = pd.read_parquet(DATA)
    print("### CANON on E3-only (clean stops) ###\n")
    g = run((dtime(9, 40), dtime(10, 15)), allt, df)
    rep(g, "GOLDEN (canon 30-50)")
    print()
    p = run((dtime(8, 0), dtime(9, 30)), allt, df)
    rep(p, "PRE-MARKET (canon <=15)")
    c = pd.concat([g, p])
    mg = c.groupby("month").dollars.sum()
    gg = (mg > 0).sum()
    print(f"\n### COMBINED canon: {len(c)}t  ${c.dollars.sum():+,.0f}  win {c.win.mean()*100:.0f}%  green {gg}/{len(mg)} ###")


if __name__ == "__main__":
    main()
