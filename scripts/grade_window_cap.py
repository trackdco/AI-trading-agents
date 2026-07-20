#!/usr/bin/env python3
"""Reconcile Tier-2 (shipped) vs the un-starved window/cap shape, on the REAL engine + the
re-detected 2026 cache. Three shapes, same champion (E3/V8 non-WAR + E4-tight WAR), same cache:

  A. Tier-2 shipped     : single 2-trade cap 08:00-10:15, cash-open 09:30-09:40 vetoed, 10pt post-open stop
  B. un-starved         : pre-window 08:00-09:30 cap 2  +  post-window 09:40-10:15 cap 3  (cash open gap)
  C. un-starved, 2+2    : pre cap 2 + post cap 2  (the more conservative un-starve)

    python -m scripts.grade_window_cap
"""
import ast
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")


def load(paths):
    out = []
    for p in paths:
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def books(base):
    return (base.model_copy(update={"mgmt_variant": "V8"}),
            base.model_copy(update={"entry_variant": "E4"}))


def grade(allt, war, df, cfg_maker, tag):
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for segcfg, capwin in cfg_maker():
            cfg_e3, cfg_e4 = books(segcfg)
            for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
                tr, _, _ = simulate(seg, tt, cfg)
                for r in tr:
                    ft = pd.Timestamp(r.fill_ts).time()
                    if capwin and not (capwin[0] <= ft < capwin[1]):
                        continue   # this fill belongs to the other window-segment
                    rows.append(dict(month=m, dollars=r.dollars, win=r.dollars > 0))
    J = pd.DataFrame(rows)
    tot, n, wr = J.dollars.sum(), len(J), J.win.mean() * 100
    print(f"\n{tag}: {n}t  ${tot:+,.0f}  win {wr:.0f}%")
    gm = J.groupby("month").dollars.agg(["count", "sum"]); gm["win"] = J.groupby("month").win.mean() * 100
    for mo, r in gm.iterrows():
        print(f"    {mo}  {int(r['count']):3d}t  ${r['sum']:+8,.0f}  win {r['win']:2.0f}%")
    return tot, n, wr


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    V = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in V.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    cfg0 = load_backtest_config()

    # A. Tier-2 shipped (single cap, cash-open veto + post-open stop already in config)
    def mk_A():
        return [(cfg0.model_copy(update={"win_start": dtime(8, 0), "win_end": dtime(10, 15),
                                         "max_trades_per_day": 2}), None)]

    # For B/C the window gap 09:30-09:40 handles the cash-open cut; disable the veto to avoid
    # double-counting, keep the 10pt post-open stop.
    base_bc = cfg0.model_copy(update={"no_trade_start": None, "no_trade_end": None})

    def mk_B():
        return [(base_bc.model_copy(update={"win_start": dtime(8, 0), "win_end": dtime(9, 30),
                                            "max_trades_per_day": 2}), (dtime(8, 0), dtime(9, 30))),
                (base_bc.model_copy(update={"win_start": dtime(9, 40), "win_end": dtime(10, 15),
                                            "max_trades_per_day": 3}), (dtime(9, 40), dtime(10, 15)))]

    def mk_C():
        return [(base_bc.model_copy(update={"win_start": dtime(8, 0), "win_end": dtime(9, 30),
                                            "max_trades_per_day": 2}), (dtime(8, 0), dtime(9, 30))),
                (base_bc.model_copy(update={"win_start": dtime(9, 40), "win_end": dtime(10, 15),
                                            "max_trades_per_day": 2}), (dtime(9, 40), dtime(10, 15)))]

    print("=" * 64)
    a = grade(allt, war, df, mk_A, "A · Tier-2 shipped (single 2-cap)")
    b = grade(allt, war, df, mk_B, "B · un-starved (pre 2 + post 3)")
    c = grade(allt, war, df, mk_C, "C · un-starved (pre 2 + post 2)")
    print("\n" + "=" * 64)
    print(f"A shipped     {a[1]:3d}t  ${a[0]:+,.0f}")
    print(f"B pre2+post3  {b[1]:3d}t  ${b[0]:+,.0f}   (Δ vs A ${b[0]-a[0]:+,.0f})")
    print(f"C pre2+post2  {c[1]:3d}t  ${c[0]:+,.0f}   (Δ vs A ${c[0]-a[0]:+,.0f})")


if __name__ == "__main__":
    main()
