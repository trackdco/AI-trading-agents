#!/usr/bin/env python3
"""INTRADAY ORDER-FLOW as the SELECTION signal (Angus 22 Jul). Pre-open features can't predict
the daily action (all AUC ~0.5). This tests whether INTRADAY order flow read at the open
(09:30-09:40) can -- the fork between 'build the intraday reader' and 'selection needs the
agent'. Features from CVD (footprints) + heatmap (depth) + price, vs the oracle labels
(fresh-eyes ledger e3/e4). Split 2025 vs 2026 to check cross-regime consistency.

    python -m scripts.intraday_selection
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from src.engine import footprint as _fp  # band-clean chokepoint


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def auc(x, y):
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    if d.y.nunique() < 2 or len(d) < 12:
        return np.nan
    r = d.x.rank(); n1 = (d.y == 1).sum(); n0 = (d.y == 0).sum()
    return (r[d.y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def load_cvd():
    files = ["footprint_q3_2025", "footprint_q4_2025", "footprint_feb_mar2026",
             "footprint_apr2026", "footprint_may_jul2026"]
    d = _fp.load_footprint([f"data/reference/cvd/{f}.parquet" for f in files],
                           _fp.cached_front_month_bands())
    g = _fp.signed_delta(d, by=("ts_minute",)).rename("delta")
    g.index = g.index.tz_convert(NY)
    return g.sort_index()


def book_feat(path):
    d = pd.read_csv(path, parse_dates=["ts"])
    w = d[(d.ts.dt.hour * 60 + d.ts.dt.minute).between(9 * 60 + 30, 9 * 60 + 39)]
    if not len(w):
        return None
    per = w.groupby(["ts", "side"])["size"].sum().unstack(fill_value=0)
    if "bid" not in per or "ask" not in per:
        return None
    bid, ask = per["bid"].mean(), per["ask"].mean()
    balance = float(np.minimum(bid, ask) / max(np.maximum(bid, ask), 1))   # 1=coiled
    return balance


def main():
    L = pd.read_csv("output/v07/walk_v07/ledger.csv")[["day", "e3", "e4"]]
    L["tradeable"] = (L[["e3", "e4"]].max(axis=1) > 0).astype(int)
    L["e4_best"] = np.where(L[["e3", "e4"]].max(axis=1) > 0, (L.e4 > L.e3).astype(int), np.nan)
    cvd = load_cvd()
    px = pd.read_parquet("data/reference/nq_1m_master.parquet").set_index("ts_event")["close"]
    pxh = pd.read_parquet("data/reference/nq_1m_master.parquet").set_index("ts_event")[["open", "high", "low", "close"]]
    depth = {Path(f).stem.split("_")[2]: f for f in
             glob.glob("data/reference/depth_2025/*.csv") + glob.glob("data/reference/depth_2026/*.csv")}

    rows = []
    for r in L.itertuples():
        day = r.day
        if day not in depth:
            continue
        start = pd.Timestamp(f"{day} 09:30", tz=NY); end = pd.Timestamp(f"{day} 09:40", tz=NY)
        bar = pxh[(pxh.index >= start) & (pxh.index < end)]
        if len(bar) < 5:
            continue
        o, c = bar.open.iloc[0], bar.close.iloc[-1]
        dirn = 1 if c >= o else -1
        rng = bar.high.max() - bar.low.min()
        cvd_open = float(cvd[(cvd.index >= start) & (cvd.index < end)].sum())
        pre = cvd[(cvd.index >= pd.Timestamp(f"{day} 08:00", tz=NY)) & (cvd.index < start)].sum()
        bal = book_feat(depth[day])
        rows.append(dict(day=day, tradeable=r.tradeable, e4_best=r.e4_best,
                         cvd_open_abs=abs(cvd_open), cvd_confirm=cvd_open * dirn,
                         open_range=rng, cvd_premkt=float(pre), book_balance=bal))
    D = pd.DataFrame(rows)
    D["yr"] = D.day.str[:4].astype(int)
    D.to_csv("output/intraday_selection.csv", index=False)
    print(f"{len(D)} days with intraday flow + labels  (2025 {int((D.yr==2025).sum())}, 2026 {int((D.yr==2026).sum())})\n")

    FEATS = ["cvd_open_abs", "cvd_confirm", "open_range", "cvd_premkt", "book_balance"]
    for target, name in (("tradeable", "TRADE vs STAND-DOWN"), ("e4_best", "E4 vs E3 (given trade)")):
        print(f"### {name}: AUC (0.5=noise), 2025 | 2026 | consistency ###")
        for f in FEATS:
            a25 = auc(D[D.yr == 2025][f], D[D.yr == 2025][target])
            a26 = auc(D[D.yr == 2026][f], D[D.yr == 2026][target])
            holds = (not np.isnan(a25) and not np.isnan(a26) and
                     (a25 - .5) * (a26 - .5) > 0 and min(abs(a25 - .5), abs(a26 - .5)) > 0.06)
            print(f"  {f:14s}  2025 {a25:.2f}   2026 {a26:.2f}   {'<- HOLDS both regimes' if holds else ''}")
        print()


if __name__ == "__main__":
    main()
