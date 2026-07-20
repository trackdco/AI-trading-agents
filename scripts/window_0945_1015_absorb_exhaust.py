#!/usr/bin/env python3
"""09:45-10:15 ET window, graded with PROPER order-flow reads of the heatmap + CVD
(engine lane, Brake, 20 Jul 2026).

Signals (entry-known, causal):
  ABSORPTION (heatmap, April-only): a large resting wall on the REJECTION side being hit by
    opposing aggressive flow but holding.  long  -> big BID <= entry (<=DIST) AND pre-entry CVD < 0
    (sellers hitting support, absorbed);  short -> big ASK >= entry AND pre-entry CVD > 0.
    wall size >= MAG (>> p95~6, p99~9).
  EXHAUSTION (CVD divergence, depth-free, full sample): over the 5-min approach the aggressor
    driving price into the level fades.  short -> price higher-high but cum-delta lower-high;
    long -> price lower-low but cum-delta higher-low.
  CVD CONFIRM: net-buy over 3-min pre-entry agrees with trade direction (as before).

Depth = April only (n=5 in this window) -> heatmap results are ANECDOTAL. CVD/exhaustion run on the
full 28-trade window but that is still small + in-sample. Reproduce from getting-started worktree.
"""
import sys, importlib.util, glob
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sst", ROOT / "scripts" / "selection_signal_test.py")
sst = importlib.util.module_from_spec(spec); spec.loader.exec_module(sst)
MAG, DIST = 15, 6
NY = "America/New_York"


def build_cvd():
    fp = pd.concat([pd.read_parquet(f) for f in glob.glob("data/reference/cvd/footprint_*2026.parquet")],
                   ignore_index=True)
    g = fp.groupby(["ts_minute", "side"])["volume"].sum().unstack(fill_value=0)
    nd = (g.get("B", 0) - g.get("A", 0))          # net delta per minute (UTC index)
    nd.index = pd.to_datetime(nd.index, utc=True)
    return nd.sort_index()


def build_bars():
    b = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    b["ts"] = pd.to_datetime(b.ts_event, utc=True)
    return b.set_index("ts")[["high", "low", "close"]].sort_index()


def pre_cvd(nd, t, mins=3):
    w = nd.loc[t - pd.Timedelta(minutes=mins): t - pd.Timedelta(minutes=1)]
    return float(w.sum()) if len(w) else np.nan


def exhaustion(nd, bars, t, direction, win=5):
    lo = t - pd.Timedelta(minutes=win); hi = t - pd.Timedelta(minutes=1)
    d = nd.loc[lo:hi]; p = bars.loc[lo:hi]
    if len(p) < 3 or len(d) < 3:
        return False
    cum = d.cumsum()
    if direction == "short":
        j = p["high"].values.argmax()                       # the high
        earlier = p["high"].values[:j]
        if len(earlier) == 0:
            return False
        # higher-high in price, lower cum-delta at that high than the earlier high => buyers exhausting
        k = earlier.argmax()
        return p["high"].values[j] > p["high"].values[k] and cum.iloc[j] < cum.iloc[k]
    else:
        j = p["low"].values.argmin()
        earlier = p["low"].values[:j]
        if len(earlier) == 0:
            return False
        k = earlier.argmin()
        return p["low"].values[j] < p["low"].values[k] and cum.iloc[j] > cum.iloc[k]


def absorption(day, entry_et, entry, direction, cvd_pre, depth_cache):
    d = depth_cache.get(day, "miss")
    if isinstance(d, str):
        try:
            d = pd.read_csv(f"data/reference/depth_apr2026/nq_depth_{day}_ny.csv")
            d["ts"] = pd.to_datetime(d["ts"])
        except Exception:
            d = None
        depth_cache[day] = d
    if d is None or np.isnan(cvd_pre):
        return np.nan
    snap = d[d["ts"] == entry_et]
    if not len(snap):
        return np.nan
    if direction == "long":
        wall = snap[(snap.side == "bid") & (entry - snap.price >= 0) & (entry - snap.price <= DIST)]["size"]
        return bool(wall.max() >= MAG) and cvd_pre < 0 if len(wall) else False
    else:
        wall = snap[(snap.side == "ask") & (snap.price - entry >= 0) & (snap.price - entry <= DIST)]["size"]
        return bool(wall.max() >= MAG) and cvd_pre > 0 if len(wall) else False


def rep(v, name):
    if not len(v):
        print(f"  {name:30s}  0t"); return
    print(f"  {name:30s} {len(v):2d}t  win {v.win.mean()*100:3.0f}%  ${v.dollars.sum():+7,.0f}  {v.R.mean():+.2f}R")


def main():
    nd = build_cvd(); bars = build_bars()
    J = sst.load(); J["hhmm"] = J.entry_et.dt.strftime("%H:%M")
    W = J[(J.hhmm >= "09:45") & (J.hhmm <= "10:15")].copy().reset_index(drop=True)
    W["cvd_pre"] = W.entry_utc.map(lambda t: pre_cvd(nd, t))
    W["exhaust"] = W.apply(lambda r: exhaustion(nd, bars, r.entry_utc, r.dir), axis=1)
    dc = {}
    W["absorb"] = W.apply(lambda r: absorption(r.day, r.entry_et, r.entry, r.dir, r.cvd_pre, dc), axis=1)

    print(f"09:45-10:15 window — FULL Feb-Jul n={len(W)} (depth-free signals) ; APRIL depth n="
          f"{W.day.str.startswith('2026-04').sum()} (heatmap)\n")
    print("[A] DEPTH-FREE signals over the full 28-trade window")
    rep(W, "baseline (all)")
    rep(W[W.cvd_confirm], "CVD confirm")
    rep(W[W.exhaust == True], "exhaustion (CVD divergence)")
    rep(W[W.real_stop], "real stop >=6pt")
    rep(W[(W.exhaust == True) & W.cvd_confirm], "exhaustion + CVD confirm")

    apr = W[W.day.str.startswith("2026-04")].copy()
    print(f"\n[B] APRIL depth window (n={len(apr)}) — HEATMAP absorption. ANECDOTAL, not a test:")
    cols = ["day", "hhmm", "dir", "risk_pts", "points", "R", "win", "cvd_confirm", "exhaust", "absorb"]
    print(apr[cols].to_string(index=False))
    rep(apr[apr.absorb == True], "absorption (heatmap)")
    rep(apr[(apr.absorb == True) & apr.cvd_confirm], "absorption + CVD")


if __name__ == "__main__":
    main()
