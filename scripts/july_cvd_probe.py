#!/usr/bin/env python3
"""DIAGNOSTIC (not a ship): does a higher GLOBAL daily trade cap + the shipped CVD gate
lift July toward green WITHOUT degrading the green months? Tests the finding's claim that
July's gates over-restrict (46 triggers/day, champion took 4). Reports; changes nothing.
"""
import sys
from datetime import time as dtime
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.champion_journal_cvd import load_triggers, load_cvd_delta, conviction  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate                      # noqa: E402
from src.backtest.selection import apply_selection_gate, load_selection_filters      # noqa: E402

NY = "America/New_York"; MONTHS = ["2026-02","2026-03","2026-04","2026-05","2026-06","2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")


def run(cap, allt, df, delta, vec, war, base):
    b = base.model_copy(update={"max_trades_per_day": cap})
    C3 = b.model_copy(update={"mgmt_variant": "V8"}); C4 = b.model_copy(update={"entry_variant": "E4"})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m+"-01",tz=NY)+pd.offsets.MonthBegin(1)).tz_localize(None),tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3 = [t for t in trigs if t.ts[:10] not in war]
        e4 = [t for t in trigs if t.ts[:10] in war and abs(t.close-t.stop_ref) <= 15.0]
        for tt, cfg in ((e3,C3),(e4,C4)):
            tr,_,_ = simulate(seg, tt, cfg)
            for r in tr:
                rows.append(dict(date=r.trade_date, dollars=r.dollars, win=r.dollars>0,
                                 cvd=conviction(delta, r.fill_ts, r.direction)))
    J = pd.DataFrame(rows)
    V = vec[["day","open_vs_value"]].rename(columns={"day":"date"})
    J = J.merge(V, on="date", how="left")
    return J


def report(J, label):
    J = J.copy(); J["m"] = J.date.str[:7]
    mg = J.groupby("m").dollars.sum(); g = (mg>0).sum()
    jul = mg.get("2026-07", 0.0)
    print(f"  {label:22s} {len(J):3d}t  ${J.dollars.sum():+8,.0f}  win {J.win.mean()*100:2.0f}%  "
          f"green {g}/{len(mg)}  |  JULY ${jul:+.0f} {'🟢' if jul>0 else '🔴'}")
    return mg


def main():
    allt = load_triggers(); df = pd.read_parquet(DATA)
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _,r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    print("loading CVD ...", flush=True); delta = load_cvd_delta()
    base = load_backtest_config().model_copy(update={"win_start":dtime(8,0),"win_end":dtime(10,15)})
    filt = load_selection_filters()
    print(f"\nshipped gate = {filt}\n")
    for cap in (2, 3, 4, 6):
        J = run(cap, allt, df, delta, vec, war, base)
        print(f"cap={cap}:")
        report(J, "raw (no gate)")
        report(apply_selection_gate(J, filt), "+ shipped CVD gate")
        print()


if __name__ == "__main__":
    main()
