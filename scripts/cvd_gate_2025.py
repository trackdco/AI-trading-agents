#!/usr/bin/env python3
"""CVD GATE ON 2025 H2 (Angus 22 Jul). First test of whether the 2026 order-flow edge
generalizes. Replicates the window22 canon pipeline (per-window 2+2 caps + 20pt pre cap +
E3/E4 war-routing) on 2025 H2, then applies the SAME CVD-absorption gate that took 2026 from
154t/34% -> 89t/43%. Question: does the identical gate lift 2025 the same way, or was it a
2026-only fit?

    python -m scripts.cvd_gate_2025
"""
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load                       # noqa: E402
from scripts.champion_journal_cvd import conviction                     # noqa: E402
from src.backtest.engine import load_backtest_config, simulate          # noqa: E402
from src.backtest.selection import apply_selection_gate, load_selection_filters  # noqa: E402

NY = "America/New_York"
MONTHS = ["2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]
PRE = (dtime(8, 0), dtime(9, 30))
GOLD = (dtime(9, 40), dtime(10, 15))


def load_delta_2025():
    frames = []
    for f in ("footprint_q3_2025", "footprint_q4_2025"):
        d = pd.read_parquet(f"data/reference/cvd/{f}.parquet", columns=["ts_minute", "side", "volume"])
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["signed"] = np.where(d["side"] == "B", d["volume"], -d["volume"])
    g = d.groupby("ts_minute")["signed"].sum().rename("delta")
    g.index = g.index.tz_convert(NY)
    return g.sort_index()


def build(allt, war, df, delta, vec):
    cfg0 = load_backtest_config()
    base = cfg0.model_copy(update={"no_trade_start": None, "no_trade_end": None})
    windows = [("pre", base.model_copy(update={"win_start": PRE[0], "win_end": PRE[1],
                                               "max_trades_per_day": 2, "max_stop_points": 20.0}), PRE),
               ("golden", base.model_copy(update={"win_start": GOLD[0], "win_end": GOLD[1],
                                                  "max_trades_per_day": 2}), GOLD)]
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for wname, wcfg, wwin in windows:
            cfg_e3, cfg_e4 = books(wcfg)
            for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
                tr, _, _ = simulate(seg, tt, cfg)
                for r in tr:
                    ft = pd.Timestamp(r.fill_ts).time()
                    if not (wwin[0] <= ft < wwin[1]):
                        continue
                    rows.append(dict(month=m, date=r.trade_date, window=wname, direction=r.direction,
                                     dollars=r.dollars, win=r.dollars > 0,
                                     cvd=-conviction(delta, r.fill_ts, r.direction)))  # same negation as 2026
    J = pd.DataFrame(rows)
    V = vec[["day", "open_vs_value"]].rename(columns={"day": "date"})
    return J.merge(V, on="date", how="left")


def rep(J, label):
    if not len(J):
        print(f"  {label:34s}  (0 trades)"); return
    mg = J.groupby("month").dollars.sum(); g = (mg > 0).sum()
    print(f"  {label:34s} {len(J):3d}t  ${J.dollars.sum():+8,.0f}  win {J.win.mean()*100:2.0f}%  green {g}/{len(mg)}")


def main():
    allt = load(["output/triggers_hist2326_ob.csv"])
    allt = [t for t in allt if t.ts[:7] in MONTHS]
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    df = df[df.ts_event >= pd.Timestamp("2025-06-15", tz=NY)].reset_index(drop=True)   # warmup + 2025 H2
    print("loading 2025 CVD ...", flush=True)
    delta = load_delta_2025()
    J = build(allt, war, df, delta, vec)
    filt = load_selection_filters()
    print("\n### CVD ABSORPTION GATE ON 2025 H2 (Jul-Dec) — does the 2026 edge generalize? ###\n")
    rep(J, "raw (2+2 caps, no gate)")
    rep(J[J.cvd <= 0], "CVD absorption only (cvd<=0)")
    G = apply_selection_gate(J, filt)
    rep(G, "shipped gate (below-val + cvd)")
    print("\n  per-month, shipped gate:")
    for m in MONTHS:
        s = G[G.month == m]
        if len(s):
            print(f"    {m}  {len(s):2d}t  ${s.dollars.sum():+7,.0f}  win {s.win.mean()*100:2.0f}%  "
                  f"{'GREEN' if s.dollars.sum() > 0 else 'red'}")
    print("\n  reference: on 2026 this gate did 154t/34% -> 89t/43%, +$15,381, 5/6 green.")
    J.to_csv("output/cvd_gate_2025_trades.csv", index=False)


if __name__ == "__main__":
    main()
