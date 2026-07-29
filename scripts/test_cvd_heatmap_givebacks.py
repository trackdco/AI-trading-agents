#!/usr/bin/env python3
"""April-2026 CVD/heatmap validation test for the give-back/entry-miss autopsy
(docs/TASK-FOR-BRAKE-orderbook-data.md Update 11). CORRECTED after a 3-reviewer
adversarial pass caught two real bugs in the first draft:

  H2 bug: the "5min before entry" window included the entry minute itself, which
  inflated the effect (diff +85.8, p=0.235) into looking like real signal. Fixed to
  strictly exclude the entry minute -> diff +27.4, p=0.79 (no signal).

  H3 bug: joined order-book depth to each trade's own MFE timestamp instead of its
  actual exit timestamp. For winners those coincide; for give-backs the MFE peak can
  precede the real stop-out by minutes at a much better price -- so the original H3
  tested the wrong moment for exactly the population (give-backs) the heatmap-for-
  exits idea was meant to help. Rebuilt around exit_ts.

Also adds the permutation test H1 never had (independently confirmed noise-level,
p~0.12-0.17, by two reviewers) and quantifies the duration/risk_pts confound between
the giveback and winner_mfe_ge1 comparison groups.

    python -m scripts.test_cvd_heatmap_givebacks
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEPTH = Path("data/reference/depth_apr2026")
RNG_SEED = 42
N_PERM = 20000


def classify(row):
    if row.win:
        return "winner_mfe_ge1" if row.mfe_r_stored >= 1.0 else "winner_other"
    if row.mfe_r_stored >= 1.0:
        return "giveback"
    if row.mfe_r_stored < 0.5:
        return "entry_miss"
    return "other_loser"


def perm_test(a, b, n=N_PERM):
    obs = a.mean() - b.mean()
    pool = np.concatenate([a, b])
    n_a = len(a)
    rng = np.random.default_rng(RNG_SEED)
    diffs = np.array([(lambda p: p[:n_a].mean() - p[n_a:].mean())(rng.permutation(pool))
                       for _ in range(n)])
    p = (np.abs(diffs) >= np.abs(obs)).mean()
    return obs, p


def load_depth_day(day):
    fpath = DEPTH / f"nq_depth_{day}_ny.csv"
    if not fpath.exists():
        return None
    d = pd.read_csv(fpath, parse_dates=["ts"])
    d["ts"] = d.ts.dt.tz_convert("America/New_York")
    return d


def snap_at(d, ts):
    target = ts.floor("min")
    snap = d[d.ts == target]
    if snap.empty:
        avail = d.ts.unique()
        if len(avail) == 0:
            return None
        nearest = min(avail, key=lambda x: abs(x - target))
        snap = d[d.ts == nearest]
    return snap


def top3_side(snap, side, ascending):
    s = snap[snap.side == side].sort_values("price", ascending=ascending)
    return s.iloc[:3]["size"].sum() if not s.empty else np.nan


def main():
    t = pd.read_csv("output/april_trade_timestamps.csv",
                     parse_dates=["entry_ts", "exit_ts", "mfe_ts", "mae_ts"])
    cvd = pd.read_csv("output/cvd_minute_apr2026.csv", index_col=0, parse_dates=True)
    t["cls"] = t.apply(classify, axis=1)
    t["dur_entry_to_mfe"] = (t.mfe_ts - t.entry_ts).dt.total_seconds() / 60

    print("=== confound check: giveback vs winner_mfe_ge1 ===")
    print(t[t.cls.isin(["giveback", "winner_mfe_ge1"])]
          .groupby("cls")[["dur_entry_to_mfe", "risk_pts"]].agg(["mean", "median"]))

    # H1: permutation test (previously missing)
    h1 = []
    for _, r in t[t.cls.isin(["giveback", "winner_mfe_ge1"])].iterrows():
        w = cvd.loc[r.mfe_ts - pd.Timedelta(minutes=8):r.mfe_ts]
        if len(w) < 3:
            continue
        sign = 1 if r.dir == "long" else -1
        h1.append(dict(cls=r.cls, cum_signed_delta=(w.delta * sign).sum()))
    h1 = pd.DataFrame(h1)
    obs1, p1 = perm_test(h1[h1.cls == "giveback"].cum_signed_delta.values,
                          h1[h1.cls == "winner_mfe_ge1"].cum_signed_delta.values)
    print(f"\nH1 (CVD into MFE peak, giveback vs winner): obs diff={obs1:+.1f}, p={p1:.3f}")

    # H2 CORRECTED: strictly pre-entry (excludes entry minute)
    h2 = []
    for _, r in t[t.cls.isin(["entry_miss", "winner_mfe_ge1"])].iterrows():
        w = cvd.loc[r.entry_ts - pd.Timedelta(minutes=5):r.entry_ts - pd.Timedelta(minutes=1)]
        if len(w) < 2:
            continue
        sign = 1 if r.dir == "long" else -1
        h2.append(dict(cls=r.cls, signed_delta=(w.delta * sign).sum()))
    h2 = pd.DataFrame(h2)
    obs2, p2 = perm_test(h2[h2.cls == "entry_miss"].signed_delta.values,
                          h2[h2.cls == "winner_mfe_ge1"].signed_delta.values)
    print(f"H2 CORRECTED (pre-entry flow, entry_miss vs winner): obs diff={obs2:+.1f}, p={p2:.3f}")

    # H3 CORRECTED part A: opposing-side buildup, MFE peak -> actual exit (giveback only)
    buildups = []
    for _, r in t[t.cls == "giveback"].iterrows():
        d = load_depth_day(r.day)
        if d is None:
            continue
        opp_side = "ask" if r.dir == "long" else "bid"
        snap_mfe, snap_exit = snap_at(d, r.mfe_ts), snap_at(d, r.exit_ts)
        if snap_mfe is None or snap_exit is None:
            continue
        sz_mfe = top3_side(snap_mfe, opp_side, r.dir == "long")
        sz_exit = top3_side(snap_exit, opp_side, r.dir == "long")
        if pd.notna(sz_mfe) and pd.notna(sz_exit):
            buildups.append(sz_exit - sz_mfe)
    buildups = pd.Series(buildups)
    print(f"\nH3-A (opposing-side book, peak->exit, giveback n={len(buildups)}): "
          f"mean buildup={buildups.mean():+.2f}, zero-change in {(buildups==0).sum()}/{len(buildups)}")

    # H3 CORRECTED part B: own-side book 1min pre-stop (thin-zone test)
    thin = []
    for _, r in t[t.exit_reason == "stop"].iterrows():
        d = load_depth_day(r.day)
        if d is None:
            continue
        own_side = "bid" if r.dir == "long" else "ask"
        snap = snap_at(d, r.exit_ts - pd.Timedelta(minutes=1))
        if snap is None:
            continue
        thin.append(dict(cls=r.cls, top3_own=top3_side(snap, own_side, r.dir != "long")))
    thin = pd.DataFrame(thin)
    print(f"\nH3-B (own-side book pre-stop, thin-zone test):")
    print(thin.groupby("cls").top3_own.agg(["mean", "median", "count"]))


if __name__ == "__main__":
    main()
