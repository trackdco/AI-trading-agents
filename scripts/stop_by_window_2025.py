#!/usr/bin/env python3
"""STOP SIZE x PROFITABILITY by WINDOW, 2025 H2 (Angus 22 Jul). Same breakdown that found the
pre-market <=20pt / golden 30-40pt split in 2026 -- rerun on 2025's regime to see if the
window-specific stop sweet spots differ. Base 2+2 trades (pre 08:00-09:30 cap2 + 20pt cap,
golden 09:40-10:15 cap2), war-routed E3/E4. No CVD gate (inert on 2025).

    python -m scripts.stop_by_window_2025
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load                       # noqa: E402
from src.backtest.engine import load_backtest_config, simulate          # noqa: E402

NY = "America/New_York"
MONTHS = ["2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]
PRE = (dtime(8, 0), dtime(9, 30))
GOLD = (dtime(9, 40), dtime(10, 15))


def main():
    allt = [t for t in load(["output/triggers_hist2326_ob.csv"]) if t.ts[:7] in MONTHS]
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    df = df[df.ts_event >= pd.Timestamp("2025-06-15", tz=NY)].reset_index(drop=True)
    base = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None})
    wins = [("pre", base.model_copy(update={"win_start": PRE[0], "win_end": PRE[1], "max_trades_per_day": 2, "max_stop_points": 20.0}), PRE),
            ("golden", base.model_copy(update={"win_start": GOLD[0], "win_end": GOLD[1], "max_trades_per_day": 2}), GOLD)]
    rows = []
    print("simulating 2025 H2 ...", flush=True)
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for wname, wcfg, wwin in wins:
            cfg_e3, cfg_e4 = books(wcfg)
            for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
                tr, _, _ = simulate(seg, tt, cfg)
                for r in tr:
                    ft = pd.Timestamp(r.fill_ts).time()
                    if not (wwin[0] <= ft < wwin[1]):
                        continue
                    rows.append(dict(window=wname, risk_pts=round(abs(r.entry - r.stop_initial), 2),
                                     dollars=r.dollars, win=r.dollars > 0))
    T = pd.DataFrame(rows)
    T.to_csv("output/stop_by_window_2025.csv", index=False)
    bins = [0, 10, 15, 20, 25, 30, 40, 60, 1000]
    labs = ["<=10", "10-15", "15-20", "20-25", "25-30", "30-40", "40-60", ">60"]

    def tbl(df, title):
        print(f"\n=== {title}: {len(df)}t  ${df.dollars.sum():+,.0f}  win {df.win.mean()*100:.0f}% (2025 H2) ===")
        df = df.assign(b=pd.cut(df.risk_pts, bins=bins, labels=labs, right=True))
        for b in labs:
            s = df[df.b == b]
            if len(s):
                print(f"  {b:6s}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:3.0f}%  ${s.dollars.mean():+6.0f}/t")
    tbl(T[T.window == "pre"], "PRE-MARKET 08:00-09:30")
    tbl(T[T.window == "golden"], "GOLDEN 09:40-10:15")
    print("\n  2026 reference: pre profitable <=20pt (20-25 leaked 0% win); golden best 30-40pt (83% win).")


if __name__ == "__main__":
    main()
