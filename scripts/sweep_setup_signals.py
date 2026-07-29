#!/usr/bin/env python3
"""SETUP x SIGNAL conviction sweep (Angus 22 Jul). The reversal+absorption edge (56% vs 24%)
can't be the only one. For every trade, compute footprint/CVD/heatmap signals AT ENTRY, then
cross-tab win-rate WITH vs WITHOUT each signal across setup types (pattern A/B/B2) and books
(E3 reversal / E4 displacement). Find where a signal makes a setup's win rate jump -> that's a
conviction-sizing lever. 2026 chained trades only (full entry detail); DISCOVERY pass, out-of-fit
validation needs 2025 reconstruction. Small cells flagged.

    python -m scripts.sweep_setup_signals
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def load_fp():
    fr = []
    for f in ("footprint_feb_mar2026", "footprint_apr2026", "footprint_may_jul2026"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if p.exists():
            fr.append(pd.read_parquet(p, columns=["ts_minute", "price", "side", "volume"]))
    d = pd.concat(fr, ignore_index=True)
    d["mi"] = d.ts_minute.dt.tz_convert(NY).dt.floor("min")
    d["sd"] = np.where(d.side == "B", d.volume, -d.volume)
    return d.sort_values("mi").set_index("mi")


def stacked_imb(win_fp, direction):
    lv = win_fp.pivot_table(index="price", columns="side", values="volume", aggfunc="sum").fillna(0)
    lv.columns = [str(c) for c in lv.columns]
    if "A" not in lv or "B" not in lv or len(lv) < 2:
        return 0
    lv = lv.sort_index()
    best = stack = 0
    for i in range(1, len(lv)):
        buy = lv["A"].iloc[i] >= 3 * max(lv["B"].iloc[i - 1], 1)
        sell = lv["B"].iloc[i - 1] >= 3 * max(lv["A"].iloc[i], 1)
        hit = buy if direction == "long" else sell
        stack = stack + 1 if hit else 0
        best = max(best, stack)
    return best


def main():
    T = pd.read_csv("output/chained_trades.csv")
    T["fill"] = pd.to_datetime(T.fill_ts, utc=True).dt.tz_convert(NY).dt.floor("min")
    T["win"] = T.dollars > 0
    T["ebook"] = T.book.map({"MOMENTUM": "E4", "ROTATION": "E3"})
    fp = load_fp()
    day_med = (fp.groupby([fp.index.floor("D"), "side"]).volume.sum().groupby(level=0).sum())
    day_med.index = day_med.index.strftime("%Y-%m-%d")
    dmed = fp.groupby(fp.index.strftime("%Y-%m-%d %H:%M")).volume.sum()  # minute totals
    dmed = dmed.groupby(dmed.index.str[:10]).median()

    # depth (heatmap) for coil-at-entry
    depth_idx = {Path(f).stem.split("_")[2]: f for f in glob.glob("data/reference/depth_2026/*.csv")}

    sig = {k: [] for k in ["absorption", "initiation", "stacked_imb", "delta_div", "coil"]}
    for t in T.itertuples():
        w0 = t.fill - pd.Timedelta(minutes=2)
        try:
            sl = fp.loc[w0:t.fill]
        except KeyError:
            for k in sig:
                sig[k].append(np.nan)
            continue
        wf = sl[(sl.price >= t.entry - 2.0) & (sl.price <= t.entry + 2.0)]
        day = t.fill.strftime("%Y-%m-%d")
        if wf.empty:
            for k in sig:
                sig[k].append(np.nan)
            continue
        med = dmed.get(day, np.nan)
        # absorption: a minute with heavy AND two-sided volume near the level
        ab = 0
        for _, g in wf.groupby(level=0):
            b = g[g.side == "B"].volume.sum(); a = g[g.side == "A"].volume.sum()
            if med == med and (b + a) >= 2.5 * med and min(b, a) / max(max(b, a), 1) >= 0.7:
                ab = 1
        net = wf.sd.sum()
        init = int((net > 0 and t.direction == "long") or (net < 0 and t.direction == "short"))
        imb = int(stacked_imb(wf, t.direction) >= 2)
        # delta divergence: net delta OPPOSES the trade's own move direction near entry (fade/absorb)
        ddiv = int((net < 0 and t.direction == "long") or (net > 0 and t.direction == "short"))
        # coil at entry from depth: balance of bid/ask in the fill minute window
        coil = np.nan
        p = depth_idx.get(day)
        if p:
            dep = pd.read_csv(p, parse_dates=["ts"])
            dep = dep[(dep.ts >= w0) & (dep.ts <= t.fill + pd.Timedelta(minutes=1))]
            if len(dep):
                per = dep.groupby("side")["size"].sum()
                if "bid" in per and "ask" in per:
                    coil = min(per["bid"], per["ask"]) / max(max(per["bid"], per["ask"]), 1)
        sig["absorption"].append(ab); sig["initiation"].append(init)
        sig["stacked_imb"].append(imb); sig["delta_div"].append(ddiv); sig["coil"].append(coil)
    for k, v in sig.items():
        T[k] = v
    T["coil_hi"] = (T.coil > 0.8).astype(float)   # balanced book at entry

    signals = ["absorption", "initiation", "stacked_imb", "delta_div", "coil_hi"]
    print(f"2026 chained trades: {len(T)}  overall win {T.win.mean()*100:.0f}%  ${T.dollars.mean():+.0f}/trade\n")

    def block(name, sub):
        print(f"=== {name}  (n={len(sub)}, base win {sub.win.mean()*100:.0f}%, ${sub.dollars.mean():+.0f}/trade) ===")
        print(f"  {'signal':13s} {'n+':>4s} {'win+':>5s} {'$/t+':>7s}   {'n-':>4s} {'win-':>5s} {'$/t-':>7s}   {'LIFT':>6s}")
        rows = []
        for s in signals:
            on = sub[sub[s] == 1]; off = sub[sub[s] == 0]
            if len(on) < 3 or len(off) < 3:
                continue
            lift = (on.win.mean() - off.win.mean()) * 100
            rows.append((lift, s, on, off))
        for lift, s, on, off in sorted(rows, key=lambda x: -x[0]):
            flag = " *small" if min(len(on), len(off)) < 8 else ""
            print(f"  {s:13s} {len(on):4d} {on.win.mean()*100:4.0f}% {on.dollars.mean():+7.0f}   "
                  f"{len(off):4d} {off.win.mean()*100:4.0f}% {off.dollars.mean():+7.0f}   {lift:+5.0f}pp{flag}")
        print()

    for pat in ["A", "B", "B2"]:
        block(f"pattern {pat}", T[T.pattern == pat])
    for bk in ["E3", "E4"]:
        block(f"{bk} book", T[T.ebook == bk])
    # the known reference cell
    block("E3 reversal + pattern A (the 56/24 cell family)", T[(T.ebook == "E3")])


if __name__ == "__main__":
    main()
