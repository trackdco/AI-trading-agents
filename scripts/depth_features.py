#!/usr/bin/env python3
"""Depth + CVD FEATURE LIBRARY for the golden-window selector study. For each trade in
output/golden_expanded.csv, compute a BROAD, multi-angle feature matrix from the full-year
depth (data/reference/depth_2026) and CVD footprints, then rank which features SEPARATE
winners from losers — i.e. which heatmap/CVD angle can add golden volume at maintained quality.

Static book, dir-aware walls, day-relative regime, dynamic build/pull, and CVD (validated
negated sign) — every angle, so we keep what works and drop only the angles that don't.

    python -m scripts.depth_features
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.champion_journal_cvd import load_cvd_delta  # noqa: E402

DEPTH = Path("data/reference/depth_2026")
NY = "America/New_York"


def load_depth(day):
    p = DEPTH / f"nq_depth_{day}_ny.csv"
    if not p.exists():
        return None
    d = pd.read_csv(p)
    d["ts"] = pd.to_datetime(d.ts)
    return d


def book_at(depth, minute):
    sub = depth[depth.ts <= minute]
    if sub.empty:
        return None
    return sub[sub.ts == sub.ts.max()]


def cvd_window(delta, fill_ts, direction, k):
    t = pd.Timestamp(fill_ts).tz_convert(NY).floor("min")
    win = delta.loc[t - pd.Timedelta(minutes=k): t - pd.Timedelta(minutes=1)]
    if win.empty:
        return np.nan
    d = float(win.sum())
    # NEGATED to the validated convention (cvd<=0 == absorption)
    return -(d if direction == "long" else -d)


def features(depth, day_med, fill_ts, entry, direction, delta):
    minute = pd.Timestamp(fill_ts).tz_convert(NY).floor("min")
    b = book_at(depth, minute)
    f = {}
    if b is not None and not b.empty:
        bids, asks = b[b.side == "bid"], b[b.side == "ask"]
        bd, ad = bids["size"].sum(), asks["size"].sum()
        tot = bd + ad
        f["thickness"] = tot
        f["imbalance"] = (bd - ad) / tot if tot else 0.0
        f["support_depth"] = bd if direction == "long" else ad
        f["resist_depth"] = ad if direction == "long" else bd
        f["support_minus_resist"] = f["support_depth"] - f["resist_depth"]
        f["thickness_vs_day"] = tot / day_med if day_med else np.nan
        above, below = b[b.price > entry], b[b.price < entry]
        if len(above):
            w = above.loc[above["size"].idxmax()]
            f["dist_wall_above"] = float(w.price - entry); f["wall_above_size"] = float(w["size"])
        if len(below):
            w = below.loc[below["size"].idxmax()]
            f["dist_wall_below"] = float(entry - w.price); f["wall_below_size"] = float(w["size"])
        # dir-aware: is the big wall on the SUPPORT side (protects the trade) close?
        if direction == "long" and "dist_wall_below" in f:
            f["support_wall_dist"], f["support_wall_size"] = f["dist_wall_below"], f["wall_below_size"]
        elif direction == "short" and "dist_wall_above" in f:
            f["support_wall_dist"], f["support_wall_size"] = f["dist_wall_above"], f["wall_above_size"]
        # DYNAMIC: thickness build/thin over prior 5 min
        b5 = book_at(depth, minute - pd.Timedelta(minutes=5))
        if b5 is not None and not b5.empty:
            f["thickness_delta_5m"] = tot - b5["size"].sum()
    f["cvd_3m"] = cvd_window(delta, fill_ts, direction, 3)
    f["cvd_1m"] = cvd_window(delta, fill_ts, direction, 2)
    f["cvd_5m"] = cvd_window(delta, fill_ts, direction, 5)
    return f


def main():
    J = pd.read_csv("output/golden_expanded.csv")
    print(f"trades: {len(J)}  win {J.win.mean()*100:.0f}%", flush=True)
    delta = load_cvd_delta()
    day_med = {}
    feats = []
    for _, r in J.iterrows():
        dp = load_depth(r.day)
        if r.day not in day_med and dp is not None:
            day_med[r.day] = dp.groupby("ts")["size"].sum().median()
        f = features(dp, day_med.get(r.day), r.fill_ts, r.entry, r.direction, delta) if dp is not None else {}
        f.update(risk_pts=r.risk_pts, win=bool(r.win), dollars=r.dollars)
        feats.append(f)
    F = pd.DataFrame(feats)
    F.to_csv("output/golden_features.csv", index=False)
    print(f"depth coverage: {F.thickness.notna().sum()}/{len(F)} trades\n")

    cols = [c for c in F.columns if c not in ("win", "dollars")]
    print(f"{'feature':22s} {'win|hi':>7s} {'win|lo':>7s} {'sep':>6s} {'$hi':>7s} {'$lo':>7s}")
    rank = []
    for c in cols:
        s = F.dropna(subset=[c])
        if len(s) < 30 or s[c].nunique() < 4:
            continue
        med = s[c].median()
        hi, lo = s[s[c] > med], s[s[c] <= med]
        if not len(hi) or not len(lo):
            continue
        sep = hi.win.mean() - lo.win.mean()
        rank.append((abs(sep), c, hi.win.mean(), lo.win.mean(), sep, hi.dollars.mean(), lo.dollars.mean()))
    for _, c, wh, wl, sep, dh, dl in sorted(rank, reverse=True):
        print(f"{c:22s} {wh*100:6.0f}% {wl*100:6.0f}% {sep*100:+5.0f} {dh:+7.0f} {dl:+7.0f}")
    print("\n(sep = win-rate gap between above-median and below-median of the feature; "
          "big |sep| = the feature separates winners from losers)")


if __name__ == "__main__":
    main()
