#!/usr/bin/env python3
"""DYNAMIC (developing) volume-profile features for the selection read (Angus 22 Jul). The
frozen-at-open profile tested as noise. This builds the DEVELOPING profile -- POC/VAH/VAL that
move as the session trades, like VWAP -- read AT the decision time, plus value MIGRATION
(how the POC drifts through the morning). Tests them vs the oracle daily action, all years
(price-only). NY-session scope (from 09:30) so it reflects the developing RTH auction.

    python -m scripts.dynamic_profile_selection
"""
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.indicators import volume_profile                       # noqa: E402

NY = "America/New_York"
BIN, VA = 0.25, 70


def auc(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if d.y.nunique() < 2 or len(d) < 12:
        return np.nan
    r = d.x.rank(); n1 = (d.y == 1).sum(); n0 = (d.y == 0).sum()
    return (r[d.y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def prof(slice_):
    if len(slice_) < 3:
        return None
    try:
        return volume_profile(slice_[["ts_event", "high", "low", "volume"]], BIN, VA)
    except Exception:
        return None


def main():
    L = pd.read_csv("output/v07/walk_v07/ledger.csv")[["day", "e3", "e4"]]
    L["tradeable"] = (L[["e3", "e4"]].max(axis=1) > 0).astype(int)
    L["e4_best"] = np.where(L[["e3", "e4"]].max(axis=1) > 0, (L.e4 > L.e3).astype(int), np.nan)
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    df = df.assign(ny=df.ts_event.dt.tz_convert(NY))
    df["d"] = df.ny.dt.strftime("%Y-%m-%d")
    df["hm"] = df.ny.dt.hour * 60 + df.ny.dt.minute
    by_day = {d: g for d, g in df.groupby("d")}

    rows = []
    for r in L.itertuples():
        g = by_day.get(r.day)
        if g is None:
            continue
        rth = g[g.hm >= 9 * 60 + 30]                       # developing NY (RTH) profile
        p945 = prof(rth[rth.hm < 9 * 60 + 45])             # early read
        p1015 = prof(rth[rth.hm < 10 * 60 + 15])           # decision-window-end read (45m RTH)
        if p1015 is None or p945 is None:
            continue
        bar = rth[rth.hm < 10 * 60 + 15]
        price = bar.close.iloc[-1]
        rows.append(dict(day=r.day, tradeable=r.tradeable, e4_best=r.e4_best,
                         price_vs_poc=price - p1015.poc,               # +above / -below developing POC
                         va_width=p1015.vah - p1015.val,              # narrow=balance, wide=extension
                         poc_migration=p1015.poc - p945.poc,          # developing value drift 09:45->10:15
                         dist_below_poc=max(0.0, p1015.poc - price),  # "trailing under POC" magnitude
                         price_in_va=int(p1015.val <= price <= p1015.vah)))
    D = pd.DataFrame(rows)
    D["yr"] = D.day.str[:4].astype(int)
    D.to_csv("output/dynamic_profile_selection.csv", index=False)
    years = sorted(D.yr.unique())
    print(f"{len(D)} days with developing-profile features  ({', '.join(f'{y}:{int((D.yr==y).sum())}' for y in years)})\n")

    FEATS = ["price_vs_poc", "va_width", "poc_migration", "dist_below_poc", "price_in_va"]
    for target, name in (("tradeable", "TRADE vs STAND-DOWN"), ("e4_best", "E4 vs E3 (given trade)")):
        print(f"### {name}: developing-profile feature AUC per year (0.5=noise) ###")
        print(f"  {'feature':15s} " + "".join(f"{y:>7d}" for y in years) + "   verdict")
        for f in FEATS:
            aucs = [auc(D[D.yr == y][f], D[D.yr == y][target]) for y in years]
            sign = [a - .5 for a in aucs if not np.isnan(a)]
            holds = len(sign) >= 3 and (all(s > 0.03 for s in sign) or all(s < -0.03 for s in sign))
            print(f"  {f:15s} " + "".join(f"{a:7.2f}" if not np.isnan(a) else '     na' for a in aucs)
                  + ("   <- HOLDS" if holds else ""))
        print()


if __name__ == "__main__":
    main()
