#!/usr/bin/env python3
"""NYA-DS-01 trial 5 — exit/stop tournament per PREREG amendment 2026-08-05b.
Ten declared arms on the L1b population; day-level R matrix -> PBO CSCV.
Today's tournament can only BANK challengers (no holdout declared) — §6.0.

    python -m scripts.nya_ds_exitlab
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation.pbo import pbo_cscv

FR = 1.0

ARMS = {
    "default":   dict(tgt=2.0),
    "t1r":       dict(tgt=1.0),
    "t3r":       dict(tgt=3.0),
    "no_target": dict(tgt=None),
    "be05":      dict(tgt=2.0, be=0.5),
    "be10":      dict(tgt=2.0, be=1.0),
    "partial":   dict(tgt=2.0, partial=True),
    "cap20":     dict(tgt=2.0, cap=20.0),
    "cap30":     dict(tgt=2.0, cap=30.0),
    "hold1555":  dict(tgt=2.0, late=True),
}


def sim(path, side, entry, risk0, arm):
    cap = arm.get("cap")
    risk = min(risk0, cap) if cap else risk0
    stop = entry - side * risk
    tgt = entry + side * arm["tgt"] * risk if arm.get("tgt") else None
    be = arm.get("be")
    partial = arm.get("partial", False)
    filled, pnl = 1.0, 0.0
    p1_done = False
    for hi, lo, cl in path:
        fav = (hi - entry) if side > 0 else (entry - lo)
        if be and fav >= be * risk and (stop - entry) * side < 0:
            stop = entry
        if partial and not p1_done and fav >= risk:
            pnl += 0.5 * risk
            filled = 0.5
            p1_done = True
        if (side > 0 and lo <= stop) or (side < 0 and hi >= stop):
            pnl += filled * side * (stop - entry)
            return pnl, risk
        if tgt is not None and ((side > 0 and hi >= tgt) or (side < 0 and lo <= tgt)):
            pnl += filled * side * (tgt - entry)
            return pnl, risk
    cl = path[-1][2]
    pnl += filled * side * (cl - entry)
    return pnl, risk


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts).set_index("ts").sort_index()
    B["gday"] = pd.Series((B.index + pd.Timedelta(hours=6)).date, index=B.index).astype(str)

    T = pd.read_parquet(ROOT / "output/nya_ds_census.parquet")
    pen_t = pd.qcut(T.pen, 3, labels=["shallow", "mid", "deep"])
    gapc = pd.cut(T.gap, [-1e9, -20, 20, 1e9], labels=["against", "flat", "with"])
    L = T[(gapc != "against") & (pen_t != "deep")].reset_index(drop=True)

    rows = []
    for _, tr in L.iterrows():
        t0 = pd.Timestamp(tr.bar_t) + pd.Timedelta(hours=1)
        day0 = pd.Timestamp(tr.bar_t).normalize()
        cut_def = day0 + pd.Timedelta(hours=12 if tr.window == "AM" else 16)
        cut_late = day0 + pd.Timedelta(hours=15, minutes=55)
        seg = B[(B.index >= t0) & (B.gday == tr.day)]
        for name, arm in ARMS.items():
            cutoff = cut_late if arm.get("late") else cut_def
            path = seg[seg.index < cutoff][["high", "low", "close"]].to_numpy()
            if not len(path):
                continue
            pnl, risk = sim(path, tr.side, tr.entry, tr.risk, arm)
            rows.append(dict(day=tr.day, year=tr.year, arm=name,
                             r=(pnl - FR) / risk))
    R = pd.DataFrame(rows)
    R.to_parquet(ROOT / "output/nya_ds_exitlab.parquet", index=False)

    print("arm results (n / WR / sumR / $ @160 / per-year sumR):")
    for name in ARMS:
        g = R[R.arm == name]
        yrs = " ".join(f"{y}:{x.sum():+.1f}" for y, x in g.r.groupby(g.year))
        print(f"  {name:9s}: n={len(g)} WR {(g.r>0).mean():.0%} "
              f"sumR {g.r.sum():+.1f} ${160*g.r.sum():+,.0f} | {yrs}")

    M = R.pivot_table(index="day", columns="arm", values="r", aggfunc="sum").fillna(0.0)
    res = pbo_cscv(M, n_blocks=8)
    print(f"\nPBO (S=8, {res.n_combinations} splits, {res.n_obs_used} days): "
          f"{res.pbo:.2f} | slope {res.slope:.2f} | P(OOS loss) {res.prob_oos_loss:.2f}")


if __name__ == "__main__":
    main()
