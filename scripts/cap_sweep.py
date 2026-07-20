#!/usr/bin/env python3
"""Champion cap-sweep + cash-open cut + RTH-extension test (Angus, 20 Jul).
Lean re-run of the Pass-29 champion (P&L only, no feature computation) to answer:
  1. Cut 09:30-09:45 (cash open) -> confirmed loser, remove it.
  2. Does lifting the 2-trade/day cap unlock the starved post-open window?
  3. Does extending win_end past 10:15 into RTH capture more?

    python -m scripts.cap_sweep
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402
import ast

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
CASH_OPEN = (dtime(9, 30), dtime(9, 45))   # the loser window to cut


def load(path):
    rows = pd.read_csv(path).to_dict("records")
    for r in rows:
        ct = r.get("cluster_types")
        r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
    ts = [Trigger(**{k: v for k, v in r.items() if k != "session_day"}) for r in rows]
    return [t for t in ts if t.pattern != "unclassified"]


def win_bucket(fill_t):
    if fill_t < dtime(9, 30):
        return "pre"
    if fill_t < dtime(9, 45):
        return "open"
    if fill_t < dtime(10, 15):
        return "post"
    return "rth"   # 10:15+


def run(allt, df, war, cap, win_end, cut_cashopen, win_start=dtime(8, 0)):
    base = load_backtest_config().model_copy(
        update={"win_start": win_start, "win_end": win_end, "max_trades_per_day": cap})
    CFG_E3 = base.model_copy(update={"mgmt_variant": "V8"})
    CFG_E4 = base.model_copy(update={"entry_variant": "E4"})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        if cut_cashopen:
            trigs = [t for t in trigs
                     if not (CASH_OPEN[0] <= pd.Timestamp(t.ts).time() < CASH_OPEN[1])]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3 = [t for t in trigs if t.ts[:10] not in war]
        e4 = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for tt, cfg in ((e3, CFG_E3), (e4, CFG_E4)):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                # exact cash-open cut on FILL time (belt + suspenders vs trigger filter)
                if cut_cashopen and CASH_OPEN[0] <= ft < CASH_OPEN[1]:
                    continue
                rows.append(dict(day=r.trade_date, w=win_bucket(ft), dollars=r.dollars,
                                 win=r.dollars > 0))
    return pd.DataFrame(rows)


def report(J, label):
    if not len(J):
        print(f"{label}: (no trades)"); return
    byw = J.groupby("w").dollars.agg(["count", "sum"])
    wl = "  ".join(f"{w}:{int(byw.loc[w,'count'])}t${byw.loc[w,'sum']:+,.0f}"
                   for w in ["pre", "open", "post", "rth"] if w in byw.index)
    print(f"{label:34s} {len(J)}t ${J.dollars.sum():+7,.0f}  win {J.win.mean()*100:.0f}%  | {wl}")


def main():
    df = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    allt = (load("output/triggers_feb_ob.csv") + load("output/triggers_marjul_ob.csv")
            + load("output/triggers_junjul_ob.csv"))
    dt = pd.read_csv("output/amt_daytypes.csv")
    dtv = dt[dt.type != "unknown"].reset_index(drop=True)
    share = dtv.type.eq("imbalanced").rolling(20, min_periods=5).mean()
    war = {d for d, s in zip(dtv.day, share) if pd.notna(s) and s >= 0.5}

    print("=== BASELINE (current champion, full day 08:00-10:15, cap=2) ===")
    report(run(allt, df, war, 2, dtime(10, 15), False), "baseline (full day)")

    print("\n=== ISOLATED POST-OPEN: sit out to 09:40, own 2-trade cap (Angus's test) ===")
    post_1015 = run(allt, df, war, 2, dtime(10, 15), True, win_start=dtime(9, 40))
    report(post_1015, "post-only 09:40-10:15, cap=2")
    report(run(allt, df, war, 2, dtime(10, 30), True, win_start=dtime(9, 40)), "post-only 09:40-10:30, cap=2")
    report(run(allt, df, war, 3, dtime(10, 15), True, win_start=dtime(9, 40)), "post-only 09:40-10:15, cap=3")

    print("\n=== PRE-MARKET ONLY (08:00-09:30, cap=2) for the combined ===")
    pre = run(allt, df, war, 2, dtime(9, 30), False, win_start=dtime(8, 0))
    report(pre, "pre-only 08:00-09:30, cap=2")

    print("\n=== COMBINED per-window caps (pre 2-cap + post 2-cap, sit out 09:30-09:40) ===")
    combined = pd.concat([pre, post_1015], ignore_index=True)
    report(combined, "COMBINED (2 pre + 2 post)")
    print(f"    vs baseline full-day cap=2: ${combined.dollars.sum() - run(allt, df, war, 2, dtime(10,15), False).dollars.sum():+,.0f} delta")


if __name__ == "__main__":
    main()
