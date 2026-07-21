#!/usr/bin/env python3
"""TEST (Angus-approved 21 Jul, report-before-ship): kill the hardcoded 15pt war-day stop
cap and raise the golden min-stop 10->15, letting structural stops run to the 42pt oversized
band (halve past 42). Does the golden window (09:40-10:15) trade MORE without the win rate
tanking? Arm A = current (15pt cap, min-stop 10) vs B = new (no cap, min-stop 15). Reports.
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load  # noqa: E402
from scripts.champion_journal_cvd import conviction, load_cvd_delta  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.backtest.selection import apply_selection_gate, load_selection_filters  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
GOLD = (dtime(9, 40), dtime(10, 15))


def gw(ts):
    hm = str(ts)[11:16]
    try:
        h, m = int(hm[:2]), int(hm[3:5]); x = h * 60 + m
        return 9 * 60 + 40 <= x <= 10 * 60 + 15
    except Exception:
        return False


def run(allt, war, df, delta, base, cap15):
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4pool = [t for t in trigs if t.ts[:10] in war]
        e4in = [t for t in e4pool if abs(t.close - t.stop_ref) <= 15.0] if cap15 else e4pool
        for tt, cfg in ((e3in, books(base)[0]), (e4in, books(base)[1])):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                if not (GOLD[0] <= ft < GOLD[1]):
                    continue
                rows.append(dict(month=m, date=r.trade_date, dollars=r.dollars, win=r.dollars > 0,
                                 wd=pd.Timestamp(r.fill_ts).day_name(),
                                 cvd=-conviction(delta, r.fill_ts, r.direction)))  # negated = validated sign
    J = pd.DataFrame(rows)
    V = pd.read_csv("output/regime_vector.csv")[["day", "open_vs_value"]].rename(columns={"day": "date"})
    return J.merge(V, on="date", how="left")


def rep(J, label, filt):
    for tag, fr in [("raw", J), ("+CVD gate", apply_selection_gate(J, filt))]:
        mg = fr.groupby("month").dollars.sum(); g = (mg > 0).sum()
        wr = fr.win.mean() * 100 if len(fr) else 0
        print(f"  {label} {tag:10s} {len(fr):3d}t (~{len(fr)/6:.1f}/mo)  ${fr.dollars.sum():+8,.0f}  win {wr:2.0f}%  green {g}/{len(mg)}")


def main():
    allt = [t for t in load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]) if gw(t.ts)]
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    print("loading CVD ...", flush=True); delta = load_cvd_delta()
    filt = load_selection_filters()
    A = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None,
        "win_start": GOLD[0], "win_end": GOLD[1], "max_trades_per_day": 2, "post_open_min_stop": 10.0})
    B = A.model_copy(update={"post_open_min_stop": 15.0})
    print("\n### GOLDEN 9:40-10:15 — kill 15pt cap + min-stop 10->15 ###\n")
    JA = run(allt, war, df, delta, A, cap15=True); rep(JA, "A CURRENT (15cap, min10)", filt)
    print()
    JB = run(allt, war, df, delta, B, cap15=False); rep(JB, "B NEW     (no cap, min15)", filt)
    GB = apply_selection_gate(JB, filt)
    print("\n== NEW (B) + CVD gate — monthly ==")
    for m in MONTHS:
        s = GB[GB.month == m]
        if len(s):
            print(f"  {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%  {'GRN' if s.dollars.sum()>0 else 'red'}")
    print("\n== NEW (B) + CVD gate — day of week ==")
    for wd in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]:
        s = GB[GB.wd == wd]
        if len(s):
            print(f"  {wd:9s} {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%")


if __name__ == "__main__":
    main()
