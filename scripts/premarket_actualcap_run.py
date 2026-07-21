#!/usr/bin/env python3
"""Pre-market ACTUAL-stop cap (Angus 21 Jul), wired at fill time in the engine.
Loads CVD/parquet once, then evaluates on the CVD baseline (shipped gate):
  control      : no cap                       -> must reproduce 89t / +$15,381
  cap20 no-BF  : skip actual stop >20, slot gone
  cap20 BF     : skip actual stop >20, next setup can fill the freed slot
Golden window is never capped. Reports total + pre-market + per-month.
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load                       # noqa: E402
from scripts.champion_journal_cvd import conviction, load_cvd_delta     # noqa: E402
from src.backtest.engine import load_backtest_config, simulate          # noqa: E402
from src.backtest.selection import apply_selection_gate, load_selection_filters  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
PRE = (dtime(8, 0), dtime(9, 30))
GOLD = (dtime(9, 40), dtime(10, 15))


def build(allt, war, df, delta, vec, cap, backfill):
    cfg0 = load_backtest_config()
    base = cfg0.model_copy(update={"no_trade_start": None, "no_trade_end": None})
    pre_cfg = base.model_copy(update={"win_start": PRE[0], "win_end": PRE[1], "max_trades_per_day": 2,
                                      "max_stop_points": cap, "max_stop_frees_slot": backfill})
    gold_cfg = base.model_copy(update={"win_start": GOLD[0], "win_end": GOLD[1], "max_trades_per_day": 2})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for wname, wcfg, wwin in (("pre", pre_cfg, PRE), ("golden", gold_cfg, GOLD)):
            cfg_e3, cfg_e4 = books(wcfg)
            for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
                tr, _, _ = simulate(seg, tt, cfg)
                for r in tr:
                    ft = pd.Timestamp(r.fill_ts).time()
                    if not (wwin[0] <= ft < wwin[1]):
                        continue
                    rows.append(dict(month=m, date=r.trade_date, window=wname,
                                     direction=r.direction, dollars=r.dollars, win=r.dollars > 0,
                                     risk_pts=round(abs(r.entry - r.stop_initial), 2),
                                     cvd=-conviction(delta, r.fill_ts, r.direction)))
    J = pd.DataFrame(rows)
    V = vec[["day", "open_vs_value"]].rename(columns={"day": "date"})
    J = J.merge(V, on="date", how="left")
    return apply_selection_gate(J, load_selection_filters())   # the shipped CVD gate


def line(J, label):
    mg = J.groupby("month").dollars.sum(); g = (mg > 0).sum()
    pre = J[J.window == "pre"]; gold = J[J.window == "golden"]
    print(f"{label:22s} {len(J):3d}t  ${J.dollars.sum():+8,.0f}  win {J.win.mean()*100:2.0f}%  green {g}/{len(mg)}   "
          f"| pre {len(pre):2d}t ${pre.dollars.sum():+7,.0f}  gold {len(gold):2d}t ${gold.dollars.sum():+7,.0f}")


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    print("loading CVD ...", flush=True)
    delta = load_cvd_delta()
    print("\n### PRE-MARKET ACTUAL-STOP CAP (fill-time, causal) — CVD baseline ###\n")
    ctrl = build(allt, war, df, delta, vec, None, False)
    line(ctrl, "control (no cap)")
    a = build(allt, war, df, delta, vec, 20.0, False)
    line(a, "cap20 no-backfill")
    b = build(allt, war, df, delta, vec, 20.0, True)
    line(b, "cap20 backfill")
    print("\n=== per-month: cap20 no-backfill ===")
    for m in MONTHS:
        s = a[a.month == m]
        if len(s):
            print(f"  {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%  {'GREEN' if s.dollars.sum()>0 else 'red'}")
    print("\n=== per-month: cap20 backfill ===")
    for m in MONTHS:
        s = b[b.month == m]
        if len(s):
            print(f"  {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%  {'GREEN' if s.dollars.sum()>0 else 'red'}")


if __name__ == "__main__":
    main()
