#!/usr/bin/env python3
"""Order flow on the ACTUAL fresh-eyes trades, correctly tagged (Angus 22 Jul).

The real fresh-eyes book trades live in output/allyears_book_trades.csv (real dollars/win/pattern/
fill-time) but lack entry price + direction. Recover those by matching each trade to its v2
trigger (same day, book-appropriate entry, matching risk in pts, fill after the trigger), take
the trigger's CORRECT A/B/B2 tag + direction + entry level, then compute the entry order-flow
signals and report win% / $ WITH vs WITHOUT each signal, per setup. 2025 Jun-Dec (footprint span);
keeps only the fresh-eyes chosen book per day (walk_v07 act).

    python -m scripts.fresheyes_orderflow
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import load
from scripts.orderflow_by_setup import load_fp_all, stacked_imb
NY = "America/New_York"


def main():
    bt = pd.read_csv("output/allyears_book_trades.csv")
    bt = bt[(bt.day >= "2025-06") & (bt.day <= "2025-12")].copy()
    led = pd.read_csv("output/v07/walk_v07/ledger.csv")
    sel = {d: {"MOMENTUM": "E4", "ROTATION": "E3"}.get(a) for d, a in zip(led.day, led.act)}
    bt = bt[bt.apply(lambda r: sel.get(r.day) == r.book, axis=1)].copy()   # fresh-eyes chosen book
    bt["fmin"] = bt.day + " " + bt.fill
    print(f"real fresh-eyes 2025 trades (chosen book, Jun-Dec): {len(bt)}  ${bt.dollars.sum():+,.0f}")

    trg = [t for t in load(["output/triggers_hist2326_ob_v2.csv"])
           if "2025-06" <= t.ts[:7] <= "2025-12"]
    T = pd.DataFrame([{"day": t.ts[:10], "dir": t.direction, "entry_ref": t.entry_ref,
                       "close": t.close, "stop": t.stop_ref, "pattern": t.pattern} for t in trg])
    T["ts"] = pd.to_datetime([t.ts for t in trg], utc=True).tz_convert(NY)

    rows = []
    for r in bt.itertuples():
        cand = T[T.day == r.day].copy()
        if len(cand) == 0:
            continue
        # entry+risk depend on book: E3 fills at entry_ref, E4 at close; risk = |entry - stop|
        cand["entry"] = np.where(r.book == "E3", cand.entry_ref, cand.close)
        cand["risk"] = (cand.entry - cand.stop).abs()
        cand = cand[(cand.risk - r.risk).abs() <= 1.0]                 # match on risk pts
        cand = cand[cand.ts <= pd.Timestamp(f"{r.day} {r.fill}", tz=NY) + pd.Timedelta(minutes=1)]
        if len(cand) == 0:
            continue
        m = cand.iloc[(cand.ts - pd.Timestamp(f"{r.day} {r.fill}", tz=NY)).abs().argmin()]
        rows.append(dict(day=r.day, book=r.book, fill=str(m.ts), direction=m["dir"],
                         entry=float(m.entry), dollars=float(r.dollars), pattern=m.pattern))
    S = pd.DataFrame(rows)
    S["yr"] = 2025
    print(f"matched to a trigger (recovered entry+dir+tag): {len(S)}/{len(bt)}  "
          f"{S.pattern.value_counts().to_dict()}")
    S.to_parquet("output/fresheyes_trades_2025.parquet")

    fp = load_fp_all()
    dmed = fp.groupby(fp.index.strftime("%Y-%m-%d %H:%M")).volume.sum()
    dmed = dmed.groupby(dmed.index.str[:10]).median()
    S["fillmi"] = pd.to_datetime(S.fill, utc=True).dt.tz_convert(NY).dt.floor("min")
    ab, dd, ini, im = [], [], [], []
    for t in S.itertuples():
        try:
            sl = fp.loc[t.fillmi - pd.Timedelta(minutes=2):t.fillmi]
        except KeyError:
            ab.append(np.nan); dd.append(np.nan); ini.append(np.nan); im.append(np.nan); continue
        wf = sl[(sl.price >= t.entry - 2) & (sl.price <= t.entry + 2)]
        if wf.empty:
            ab.append(np.nan); dd.append(np.nan); ini.append(np.nan); im.append(np.nan); continue
        med = dmed.get(t.fillmi.strftime("%Y-%m-%d"), np.nan); a = 0
        for _, g in wf.groupby(level=0):
            b = g[g.side == "B"].volume.sum(); aa = g[g.side == "A"].volume.sum()
            if med == med and (b + aa) >= 2.5 * med and min(b, aa) / max(max(b, aa), 1) >= 0.7:
                a = 1
        net = wf.sd.sum()
        ini.append(int((net > 0 and t.direction == "long") or (net < 0 and t.direction == "short")))
        dd.append(int((net < 0 and t.direction == "long") or (net > 0 and t.direction == "short")))
        im.append(int(stacked_imb(wf, t.direction) >= 2)); ab.append(a)
    S["absorption"] = ab; S["delta_div"] = dd; S["initiation"] = ini; S["stacked_imb"] = im
    S = S.dropna(subset=["absorption"]); S["win"] = S.dollars > 0
    print(f"with footprint coverage: {len(S)}\n")
    for setup in ["A", "B", "B2"]:
        d = S[S.pattern == setup]
        print(f"== {setup}  n={len(d)}  base win {d.win.mean()*100:.0f}%  ${d.dollars.mean():+.0f}/t  tot ${d.dollars.sum():+,.0f}")
        for s in ["absorption", "delta_div", "initiation", "stacked_imb"]:
            on = d[d[s] == 1]; off = d[d[s] == 0]
            if len(on) < 2 or len(off) < 2:
                print(f"    {s:12s} n+={len(on)} (too few)"); continue
            print(f"    {s:12s} on n={len(on):3d} win {on.win.mean()*100:3.0f}% ${on.dollars.mean():+6.0f}   "
                  f"off n={len(off):3d} win {off.win.mean()*100:3.0f}% ${off.dollars.mean():+6.0f}")


if __name__ == "__main__":
    main()
