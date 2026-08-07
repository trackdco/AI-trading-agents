#!/usr/bin/env python3
"""ORDER FLOW PER SETUP (Angus 22 Jul). On the correctly-tagged substrate (A = daily-VWAP ±2
touch reversal, B = with-trend continuation, B2 = rejection), for each setup type separately,
does an order-flow signal at entry lift win-rate / P&L? Reported WITH vs WITHOUT each signal,
per setup, OUT-OF-FIT (2025 vs 2026) so only edges that hold both years count.

Signals at entry (3 min ending at fill, within ±2pt of entry level):
  absorption   : a minute with >=2.5x median vol AND two-sided (min(B,A)/max>=0.7)
  delta_div    : net delta OPPOSES the trade's move (fade/absorb flavor)
  initiation   : net delta AGREES with the trade direction
  stacked_imb  : >=2 stacked 300% diagonal imbalances on the trade's side

    python -m scripts.orderflow_by_setup
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def load_fp_all():
    fr = []
    for f in ("footprint_q3_2025", "footprint_q4_2025", "footprint_feb_mar2026",
              "footprint_apr2026", "footprint_may_jul2026"):
        p = Path(f"data/reference/cvd/{f}.parquet")
        if not p.exists():
            continue
        d = pd.read_parquet(p, columns=["ts_minute", "price", "side", "volume"])
        ny = d.ts_minute.dt.tz_convert(NY)
        hm = ny.dt.hour.values * 60 + ny.dt.minute.values
        keep = (hm >= 475) & (hm <= 620)
        d = d[keep].copy(); d["mi"] = ny[keep].dt.floor("min")
        d["sd"] = np.where(d.side == "B", d.volume, -d.volume)
        fr.append(d[["mi", "price", "side", "volume", "sd"]])
    return pd.concat(fr, ignore_index=True).sort_values("mi").set_index("mi")


def stacked_imb(wf, direction):
    lv = wf.pivot_table(index="price", columns="side", values="volume", aggfunc="sum").fillna(0)
    lv.columns = [str(c) for c in lv.columns]
    if "A" not in lv or "B" not in lv or len(lv) < 2:
        return 0
    lv = lv.sort_index(); best = stack = 0
    for i in range(1, len(lv)):
        buy = lv["A"].iloc[i] >= 3 * max(lv["B"].iloc[i - 1], 1)
        sell = lv["B"].iloc[i - 1] >= 3 * max(lv["A"].iloc[i], 1)
        hit = buy if direction == "long" else sell
        stack = stack + 1 if hit else 0; best = max(best, stack)
    return best


def add_signals(S, fp):
    dmed = fp.groupby(fp.index.strftime("%Y-%m-%d %H:%M")).volume.sum()
    dmed = dmed.groupby(dmed.index.str[:10]).median()
    S = S.copy(); S["fillmi"] = pd.to_datetime(S.fill, utc=True).dt.tz_convert(NY).dt.floor("min")
    ab, dd, ini, im = [], [], [], []
    for t in S.itertuples():
        w0 = t.fillmi - pd.Timedelta(minutes=2)
        try:
            sl = fp.loc[w0:t.fillmi]
        except KeyError:
            ab.append(np.nan); dd.append(np.nan); ini.append(np.nan); im.append(np.nan); continue
        wf = sl[(sl.price >= t.entry - 2.0) & (sl.price <= t.entry + 2.0)]
        if wf.empty:
            ab.append(np.nan); dd.append(np.nan); ini.append(np.nan); im.append(np.nan); continue
        med = dmed.get(t.fillmi.strftime("%Y-%m-%d"), np.nan)
        a = 0
        for _, g in wf.groupby(level=0):
            b = g[g.side == "B"].volume.sum(); aa = g[g.side == "A"].volume.sum()
            if med == med and (b + aa) >= 2.5 * med and min(b, aa) / max(max(b, aa), 1) >= 0.7:
                a = 1
        net = wf.sd.sum()
        ini.append(int((net > 0 and t.direction == "long") or (net < 0 and t.direction == "short")))
        dd.append(int((net < 0 and t.direction == "long") or (net > 0 and t.direction == "short")))
        im.append(int(stacked_imb(wf, t.direction) >= 2)); ab.append(a)
    S["absorption"] = ab; S["delta_div"] = dd; S["initiation"] = ini; S["stacked_imb"] = im
    return S.dropna(subset=["absorption"])


def report(S):
    S = S.copy(); S["win"] = S.dollars > 0
    sigs = ["absorption", "delta_div", "initiation", "stacked_imb"]
    for setup in ["A", "B", "B2"]:
        sub = S[S.pattern == setup]
        print(f"\n===== SETUP {setup}  (n={len(sub)}, base win {sub.win.mean()*100:.0f}%, "
              f"${sub.dollars.mean():+.0f}/t, total ${sub.dollars.sum():+,.0f}) =====")
        print(f"  {'signal':12s} {'yr':>5s} {'n+':>4s} {'win+':>5s} {'$/t+':>7s}  {'n-':>4s} {'win-':>5s} {'$/t-':>7s}")
        for s in sigs:
            for yr in (2025, 2026):
                d = sub[sub.yr == yr]
                on = d[d[s] == 1]; off = d[d[s] == 0]
                if len(on) < 2 or len(off) < 2:
                    print(f"  {s:12s} {yr:5d} {len(on):4d}  (too few)"); continue
                print(f"  {s:12s} {yr:5d} {len(on):4d} {on.win.mean()*100:4.0f}% {on.dollars.mean():+7.0f}  "
                      f"{len(off):4d} {off.win.mean()*100:4.0f}% {off.dollars.mean():+7.0f}")


def main():
    S = pd.read_parquet("output/substrate_v2.parquet")
    print(f"substrate: {len(S)} trades  {S.pattern.value_counts().to_dict()}")
    fp = load_fp_all()
    S = add_signals(S, fp)
    print(f"with footprint coverage: {len(S)}")
    S.to_parquet("output/substrate_v2_signals.parquet")
    report(S)


if __name__ == "__main__":
    main()
