#!/usr/bin/env python3
"""THE canon baseline: E3+E4 (both Angus entries), both windows, with the shipped engine stop
caps actually enforcing the rule (golden 30-50, pre-market <=15) -- not a post-hoc filter.
Per-window 2+2 caps. Reports the honest shippable number + months-green.
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
WINDOWS = {"pre": (dtime(8, 0), dtime(9, 30)), "golden": (dtime(9, 40), dtime(10, 15))}


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    rows = []
    for wname, (ws, we) in WINDOWS.items():
        # config DEFAULTS = the shipped canon caps (max_stop 15 / post_open 30-50); only set the window
        base = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None,
            "win_start": ws, "win_end": we, "max_trades_per_day": 2})
        cfg_e3, cfg_e4 = books(base)
        for m in MONTHS:
            trigs = [t for t in allt if t.ts[:7] == m]
            end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
            seg = df[df.ts_event <= end].reset_index(drop=True)
            e3in = [t for t in trigs if t.ts[:10] not in war]   # E3 retest on calm days
            e4in = [t for t in trigs if t.ts[:10] in war]        # E4 displacement on strong days
            for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
                tr, _, _ = simulate(seg, tt, cfg)
                for r in tr:
                    ft = pd.Timestamp(r.fill_ts).time()
                    if ws <= ft < we:
                        rows.append(dict(window=wname, month=m, dollars=r.dollars, win=r.dollars > 0,
                                         risk=abs(r.entry - r.stop_initial)))
    J = pd.DataFrame(rows)

    def rep(s, label):
        mg = s.groupby("month").dollars.sum()
        g = (mg > 0).sum()
        print(f"{label:12s} {len(s):3d}t  ${s.dollars.sum():+8,.0f}  win {s.win.mean()*100:.0f}%  green {g}/{len(mg)}")
    print("### CANON BASELINE (E3+E4, engine caps enforcing golden 30-50 / pre <=15) ###\n")
    rep(J[J.window == "pre"], "pre-market")
    rep(J[J.window == "golden"], "golden")
    rep(J, "COMBINED")
    print("\n=== combined, months-green ===")
    for m in MONTHS:
        s = J[J.month == m]
        if len(s):
            print(f"  {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%  {'GRN' if s.dollars.sum()>0 else 'red'}")


if __name__ == "__main__":
    main()
