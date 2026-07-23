#!/usr/bin/env python3
"""LONDON depth features from the MBP-10 heatmap data (Angus 27-Jul: 295 days of
per-minute book snapshots, data/reference/depth_london/).

Converts each wide MBP-10 snapshot row (10 levels x bid/ask px+sz) into the same
long-form book NY used, then applies the IDENTICAL depth_at semantics from
scripts/trade_matrix.py: thickness, imbalance, spread, support/resist, wall
above/below (max-size visible level) distance+size, 5-min thickness delta.
Adds dep_* columns to output/london_matrix.parquet in place.

    python -m scripts.london_depth
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"
DIR = Path("data/reference/depth_london")


def load_day(day: str):
    """day 'YYYY-MM-DD' -> long frame (ts, side, price, size) or None."""
    f = DIR / f"glbx-mdp3-{day.replace('-', '')}.mbp-10_condensed.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    ts = pd.to_datetime(d.ts_event, utc=True).dt.tz_convert(NY)
    rows = []
    for lvl in range(10):
        for side, px, sz in (("bid", f"bid_px_{lvl:02d}", f"bid_sz_{lvl:02d}"),
                             ("ask", f"ask_px_{lvl:02d}", f"ask_sz_{lvl:02d}")):
            rows.append(pd.DataFrame({"ts": ts, "side": side,
                                      "price": d[px], "size": d[sz]}))
    out = pd.concat(rows, ignore_index=True).dropna(subset=["price"])
    return out[out["size"] > 0]


def depth_at(dep, minute, entry, direction):
    """Identical semantics to scripts.trade_matrix.depth_at."""
    sub = dep[dep.ts <= minute]
    if sub.empty:
        return {}
    b = sub[sub.ts == sub.ts.max()]
    bid, ask = b[b.side == "bid"], b[b.side == "ask"]
    if bid.empty or ask.empty:
        return {}
    tb, ta = bid["size"].sum(), ask["size"].sum()
    f = {"dep_thick": tb + ta, "dep_imb": (tb - ta) / max(tb + ta, 1),
         "dep_spread": ask.price.min() - bid.price.max(),
         "dep_support": tb if direction == "long" else ta,
         "dep_resist": ta if direction == "long" else tb}
    f["dep_sup_m_res"] = f["dep_support"] - f["dep_resist"]
    above, below = b[b.price > entry], b[b.price < entry]
    if len(above):
        w = above.loc[above["size"].idxmax()]
        f["dep_wall_above_d"] = float(w.price - entry)
        f["dep_wall_above_sz"] = float(w["size"])
    if len(below):
        w = below.loc[below["size"].idxmax()]
        f["dep_wall_below_d"] = float(entry - w.price)
        f["dep_wall_below_sz"] = float(w["size"])
    b5 = dep[dep.ts <= minute - pd.Timedelta(minutes=5)]
    if not b5.empty:
        f["dep_thick_d5m"] = f["dep_thick"] - b5[b5.ts == b5.ts.max()]["size"].sum()
    return f


def main():
    L = pd.read_parquet("output/london_matrix.parquet")
    L = L.drop(columns=[c for c in L.columns if c.startswith("dep_")], errors="ignore")
    cache = {}
    rows = []
    for i, t in enumerate(L.itertuples()):
        if t.day not in cache:
            cache[t.day] = load_day(t.day)
        dep = cache[t.day]
        if dep is None:
            rows.append({})
            continue
        f = pd.Timestamp(t.fill).tz_convert(NY).floor("min")
        rows.append(depth_at(dep, f, t.entry, t.direction))
        if (i + 1) % 200 == 0:
            print(f"  {i+1}/{len(L)}", flush=True)
    X = pd.DataFrame(rows, index=L.index)
    out = pd.concat([L, X], axis=1)
    out.to_parquet("output/london_matrix.parquet")
    cov = out.dep_thick.notna().sum()
    print(f"wrote output/london_matrix.parquet: {len(out)} trades, depth on {cov} "
          f"({cov/len(out)*100:.0f}%), {X.shape[1]} dep_ cols")
    long = out.direction == "long"
    D = pd.Series(np.where(long, out.dep_wall_above_d.notna(), out.dep_wall_below_d.notna()),
                  index=out.index).astype(float).where(out.dep_thick.notna())
    for yr in (2025, 2026):
        d = out[(out.yr == yr) & D.notna()]
        dd = D[d.index]
        a, b = d[dd == 1], d[dd == 0]
        print(f"  {yr} quick look — wall-ahead exists: WR {(a.dollars>0).mean():.0%} (n={len(a)}) "
              f"vs absent {(b.dollars>0).mean():.0%} (n={len(b)})")


if __name__ == "__main__":
    main()
