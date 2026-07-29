#!/usr/bin/env python3
"""Confirm: is golden's honest loss the E4 (displacement, 1-bar-late) entries? Split golden
E3 vs E4 with the shipped canon caps, and show the clean shape (golden E3-only + pre-market
E3+E4) months-green. No lookahead (engine caps at entry).
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


def run_window(ws, we, allt, war, df):
    base = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None,
        "win_start": ws, "win_end": we, "max_trades_per_day": 2})
    cfg_e3, cfg_e4 = books(base)
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war]
        for book, tt, cfg in (("E3", e3in, cfg_e3), ("E4", e4in, cfg_e4)):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                if ws <= ft < we:
                    rows.append(dict(book=book, month=m, dollars=r.dollars, win=r.dollars > 0))
    return pd.DataFrame(rows)


def rep(s, label):
    mg = s.groupby("month").dollars.sum()
    g = (mg > 0).sum()
    print(f"{label:34s} {len(s):3d}t  ${s.dollars.sum():+8,.0f}  win {s.win.mean()*100 if len(s) else 0:2.0f}%  green {g}/{len(mg)}")


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    g = run_window(dtime(9, 40), dtime(10, 15), allt, war, df)
    p = run_window(dtime(8, 0), dtime(9, 30), allt, war, df)
    print("### GOLDEN split (canon caps, honest) ###")
    rep(g[g.book == "E3"], "golden E3 (retest)")
    rep(g[g.book == "E4"], "golden E4 (displacement, 1-bar late)")
    print("\n### PRE-MARKET split ###")
    rep(p[p.book == "E3"], "pre E3")
    rep(p[p.book == "E4"], "pre E4")
    clean = pd.concat([g[g.book == "E3"], p])   # golden E3-only + pre E3+E4
    print("\n### CLEAN SHAPE: golden E3-only + pre-market E3+E4 ###")
    rep(clean, "CLEAN combined")
    for m in MONTHS:
        s = clean[clean.month == m]
        if len(s):
            print(f"  {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%  {'GRN' if s.dollars.sum()>0 else 'red'}")


if __name__ == "__main__":
    main()
