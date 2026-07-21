#!/usr/bin/env python3
"""Angus's rule: a big stop must justify a big target (40pt stop -> 100-150pt+ ~= 2.5-3.75R).
Current rr_floor is a flat 2.0. Sweep it on the cap-killed golden window (no 15pt cap,
min-stop 15) to see if big-stop->big-target restores CONSISTENCY (fewer red months). CVD-gated.
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


def run(allt, war, df, delta, cfgbase):
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war]
        for tt, cfg in ((e3in, books(cfgbase)[0]), (e4in, books(cfgbase)[1])):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                if not (GOLD[0] <= ft < GOLD[1]):
                    continue
                rows.append(dict(month=m, date=r.trade_date, dollars=r.dollars, win=r.dollars > 0,
                                 r=r.r_multiple, cvd=-conviction(delta, r.fill_ts, r.direction)))
    J = pd.DataFrame(rows)
    V = pd.read_csv("output/regime_vector.csv")[["day", "open_vs_value"]].rename(columns={"day": "date"})
    return J.merge(V, on="date", how="left")


def main():
    allt = [t for t in load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]) if gw(t.ts)]
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    print("loading CVD ...", flush=True); delta = load_cvd_delta()
    filt = load_selection_filters()
    base = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None,
        "win_start": GOLD[0], "win_end": GOLD[1], "max_trades_per_day": 2, "post_open_min_stop": 15.0})
    print("\n### GOLDEN cap-killed + min15 — rr_floor sweep (big stop -> big target) ###")
    for rr in [2.0, 2.5, 3.0, 3.5]:
        G = apply_selection_gate(run(allt, war, df, delta, base.model_copy(update={"rr_floor": rr})), filt)
        mg = G.groupby("month").dollars.sum(); g = (mg > 0).sum()
        exp = G.dollars.mean() if len(G) else 0
        print(f"\nrr_floor={rr}: gated {len(G):3d}t (~{len(G)/6:.1f}/mo)  ${G.dollars.sum():+,.0f}  "
              f"win {G.win.mean()*100 if len(G) else 0:.0f}%  exp ${exp:+.0f}/t  green {g}/{len(mg)}")
        for m in MONTHS:
            s = G[G.month == m]
            if len(s):
                print(f"    {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%  {'GRN' if s.dollars.sum()>0 else 'red'}")


if __name__ == "__main__":
    main()
