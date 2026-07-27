#!/usr/bin/env python3
"""GOLD (GC/MGC) ASIA-RANGE -> LONDON-BREAKOUT — honest first look. NOT a validated strategy.

The one gold-in-Asia idea with a real mechanism: Asia accumulates a range on physical/SGE flow,
then London (the physical AM market) provides the impulse. Test: at the London open, trade the
break of the Asia range; both directions; fixed-R bracket; net of costs.

DATA: data/reference/gc_1m_master.parquet -- Jul 2025 -> Jul 2026, ONE regime (a relentless gold
bull run, 3290 -> 5623). So this can split train/test but CANNOT prove a cross-regime edge. A
long-only result here is just "gold went up". The honest reads are (a) does it work in BOTH
directions, and (b) does it survive first-half -> second-half. Treat everything as provisional
until 2021-22 (choppy/bear) history is added.

SESSIONS (UTC, DST-agnostic first pass):
  Asia range = high/low over 00:00-06:59 UTC (Tokyo/Shanghai hours)
  Breakout   = first 1-min close beyond the Asia range during 07:00-11:00 UTC (London morning)
  entry at that close +1 tick slip; stop = other side of the Asia range; target = R_MULT * risk;
  flat at 15:00 UTC if unresolved. Skip days whose Asia range is <5 or >120 gold points.

COSTS: MGC economics -- $10/point, 0.10 tick. 1 tick slip in + 1 tick out + $1.5 RT commission.
Reported primarily in R (scale-free) plus $ at 1 MGC.

    LONDON_SCRATCH unused; reads the repo parquet directly.
        python3 scripts/gold_asia_firstlook.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET = os.path.join(HERE, "data/reference/gc_1m_master.parquet")
TICK, PV, COMM = 0.10, 10.0, 1.5           # MGC
R_MULTS = [1.0, 1.5, 2.0, 3.0]
ASIA_START, ASIA_END = dtime(0, 0), dtime(7, 0)
BREAK_START, BREAK_END = dtime(7, 0), dtime(11, 0)
FLAT = dtime(15, 0)
RANGE_MIN, RANGE_MAX = 5.0, 120.0
SPLIT = "2026-01-15"                        # ~half the one-year window

b = pd.read_parquet(PARQUET)
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b = b.sort_values("ts").reset_index(drop=True)
b["day"] = b.ts.dt.strftime("%Y-%m-%d")
b["t"] = b.ts.dt.time
O, H, L, C = (b.open.values, b.high.values, b.low.values, b.close.values)
tt, dd = b.t.values, b.day.values


def run(r_mult, direction="both"):
    rows = []
    for day, idx in b.groupby("day").indices.items():
        idx = np.array(idx)
        d_t = tt[idx]
        asia = idx[(d_t >= ASIA_START) & (d_t < ASIA_END)]
        if len(asia) < 60:
            continue
        ah, al = H[asia].max(), L[asia].min()
        if not (RANGE_MIN <= ah - al <= RANGE_MAX):
            continue
        brk = idx[(d_t >= BREAK_START) & (d_t < BREAK_END)]
        # first close beyond the range
        entry = side = None
        for k in brk:
            if C[k] > ah:
                side, entry, ki = 1, C[k] + TICK, k; break
            if C[k] < al:
                side, entry, ki = -1, C[k] - TICK, k; break
        if side is None:
            continue
        if direction == "long" and side < 0:
            continue
        if direction == "short" and side > 0:
            continue
        stop = al if side > 0 else ah          # other side of the range
        risk = abs(entry - stop)
        if risk < RANGE_MIN:
            continue
        tgt = entry + side * r_mult * risk
        rest = idx[idx > ki]
        gross = None
        for k in rest:
            if tt[k] >= FLAT:
                gross = side * (C[k] - entry); break
            hit_stop = (L[k] <= stop) if side > 0 else (H[k] >= stop)
            hit_tgt = (H[k] >= tgt) if side > 0 else (L[k] <= tgt)
            if hit_stop:
                gross = -risk - TICK; break
            if hit_tgt:
                gross = r_mult * risk - TICK; break
        if gross is None:
            gross = side * (C[rest[-1]] - entry) if len(rest) else 0.0
        net = gross * PV - COMM
        rows.append(dict(day=day, side=side, risk=risk, R=net / (risk * PV), net=net,
                         train=day < SPLIT))
    return pd.DataFrame(rows)


def line(df, lab):
    if len(df) < 3:
        print(f"    {lab:16s} n={len(df):3d}  (too few)"); return
    wr = 100 * (df.R > 0).mean()
    eq = df.net.cumsum().values
    dd_ = float((np.maximum.accumulate(eq) - eq).max())
    print(f"    {lab:16s} n={len(df):3d}  WR {wr:3.0f}%  E[R] {df.R.mean():+.3f}  "
          f"net ${df.net.sum():+8,.0f}  maxDD ${dd_:7,.0f}")


if __name__ == "__main__":
    print("=" * 92)
    print("GOLD Asia-range -> London breakout (MGC costs). ONE-REGIME first look, NOT validated.")
    print("=" * 92)
    for rm in R_MULTS:
        print(f"\n--- target {rm:g}R ---")
        both = run(rm, "both")
        for lab, sub in (("BOTH all", both), ("BOTH train", both[both.train]),
                         ("BOTH test", both[~both.train])):
            line(sub, lab)
        lg, sh = run(rm, "long"), run(rm, "short")
        line(lg, "LONG only")
        line(sh, "SHORT only")
        # long vs short is the key tell: if only longs work, it's the bull run, not an edge
    print("\nREAD: if only LONG makes money, that is the 2025-26 gold bull run, not a strategy.")
    print("A real breakout edge shows up on BOTH sides and survives train -> test.")
    print("Cross-regime proof still requires 2021-22 data; this window has no bear/chop phase.")
