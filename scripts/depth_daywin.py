#!/usr/bin/env python3
"""Depth / order-book (L2) DAY-WINDOW features (Angus 23-Jul round 3).

The modality I skipped: resting liquidity. For each day we have 1-min book snapshots (10 levels
each side, 08:00-10:29 NY). Compute book-imbalance / thickness / replenishment for the pre-market
(08:00-09:30) and open (09:30-09:50) windows -> output/depth_daywin.parquet. These join the flow
features for the multivariate stand-down model.

    python -m scripts.depth_daywin
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
NY = "America/New_York"


def day_features(path):
    d = pd.read_csv(path)
    d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
    d["mi"] = d.ts.dt.floor("min")
    d["hm"] = d.ts.dt.hour * 60 + d.ts.dt.minute
    out = {}
    for wname, lo, hi in [("pre", 480, 570), ("op", 570, 590)]:
        w = d[(d.hm >= lo) & (d.hm < hi)]
        if w.empty:
            continue
        snaps = []
        for mi, g in w.groupby("mi"):
            bid = g[g.side == "bid"]; ask = g[g.side == "ask"]
            if bid.empty or ask.empty:
                continue
            bb = bid.price.max(); ba = ask.price.min()
            tb, ta = bid["size"].sum(), ask["size"].sum()
            nb = bid.nlargest(3, "price")["size"].sum()
            na = ask.nsmallest(3, "price")["size"].sum()
            snaps.append((mi, (tb - ta) / max(tb + ta, 1), (nb - na) / max(nb + na, 1),
                          tb + ta, ba - bb))
        if len(snaps) < 5:
            continue
        s = pd.DataFrame(snaps, columns=["mi", "imb", "nearimb", "totsz", "spread"])
        p = "d_" + wname + "_"
        out[p + "imb_mean"] = s.imb.mean()
        out[p + "imb_std"] = s.imb.std()
        out[p + "imb_last"] = s.imb.iloc[-1]
        out[p + "absimb_mean"] = s.imb.abs().mean()
        out[p + "nearimb_mean"] = s.nearimb.mean()
        out[p + "totsz_mean"] = s.totsz.mean()
        out[p + "totsz_trend"] = np.polyfit(range(len(s)), s.totsz, 1)[0] if len(s) > 3 else 0.0
        out[p + "imb_trend"] = np.polyfit(range(len(s)), s.imb, 1)[0] if len(s) > 3 else 0.0
        out[p + "spread_mean"] = s.spread.mean()
        out[p + "imb_flips"] = int((np.sign(s.imb).diff().abs() > 0).sum())
        out[p + "thin_frac"] = float((s.totsz < s.totsz.median() * 0.6).mean())
    return out


def main():
    rows = {}
    for folder in ("depth_2025", "depth_apr2026"):
        base = Path(f"data/reference/{folder}")
        files = sorted(base.glob("*_ny.csv"))
        for f in files:
            day = f.name.replace("nq_depth_", "").replace("_ny.csv", "")
            try:
                feats = day_features(f)
            except Exception as e:
                print(f"  skip {day}: {e}"); continue
            if feats:
                rows[day] = feats
        print(f"  {folder}: {len(files)} files done", flush=True)
    D = pd.DataFrame(rows).T
    D.index.name = "day"
    D.to_parquet("output/depth_daywin.parquet")
    print(f"wrote output/depth_daywin.parquet: {len(D)} days x {D.shape[1]} depth features")


if __name__ == "__main__":
    main()
