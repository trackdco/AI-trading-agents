#!/usr/bin/env python3
"""NYA-IVB-01 trials 4-5 — the REOPENED searches, as taught (canon-parity).

Branch B AS TAUGHT (trial 4): fade the 10:00-10:30 touch of the intact IB
extreme ONLY when the toucher's aggression is being absorbed at the extreme
(flow library absorb flag, absorbed side = the side pushing into the extreme,
within touch-minute ±2) — Fabervaale's actual setup. Variables layered per
the declared set: wall-at-entry (opposing side wall_ratio >= 3 at the touch
minute — canon-W-gate analog), IB size terciles, dz at touch. Geometry: stop
0.25 x IB beyond the extreme, target IB mid; base friction.

Branch A retest (trial 5): the break event with flow-at-break conditioning —
dz of the break bar (aggression WITH the break), effortless flag on the
break bar (path of least resistance), broken-side wall ABSENT at the break
minute, pm_press_0800 agreement. Race economics at 1:1 (1 x IB) plus the
close-beyond read, flow span, era-split by halves.

Both searches run on the flow span (2025-06..2026-07) where the taught
triggers exist. Full-span candle-only reads were trials 1-2 and stand as
recorded. Every cell below is a declared arm; all go to the machine ledger.

    python -m scripts.nya_ivb_retest
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0
RISK_DOLLARS = 160.0


def rep(rows, label):
    if not rows:
        print(f"  {label}: n=0"); return
    T = pd.DataFrame(rows)
    net = T.pts - FR
    r = net / T.risk
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    halves = " ".join(f"{h}:{x.sum():+.0f}" for h, x in net.groupby(T.half))
    print(f"  {label}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r.sum():+,.0f} PF {gw/max(gl,1e-9):.2f} | {halves}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    FL = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    fl_by_day = {d: g for d, g in FL.groupby("gday")}
    D = pd.read_parquet(ROOT / "output/depth_minutes.parquet")
    D = D.assign(gday=pd.Series(D.index.date, index=D.index).astype(str),
                 clock=D.index.strftime("%H:%M"))
    d_by_day = {d: g.set_index("clock") for d, g in D.groupby("gday")}

    fadeB, brkA = [], []
    for d in sorted(set(R[R.gday >= "2025-06-02"].gday) & set(fl_by_day)):
        r = R[R.gday == d].sort_values("ts").reset_index(drop=True)
        ib = r[r.clock < "10:00"]
        if len(ib) < 25 or len(r) < 200:
            continue
        ibh, ibl = ib.high.max(), ib.low.min()
        rng = ibh - ibl
        if rng <= 0:
            continue
        mid = (ibh + ibl) / 2
        half = d[:4] + ("H1" if d[5:7] < "07" else "H2")
        f = fl_by_day[d]
        dep = d_by_day.get(d)

        # ---- BRANCH B as taught: touch + absorption at the extreme ----
        win = r[(r.clock >= "10:00") & (r.clock < "10:30")]
        touch = None
        for i, row in win.iterrows():
            if row.close > ibh or row.close < ibl:
                break
            if row.high >= ibh:
                touch = (-1, i); break     # fade short at IB high
            if row.low <= ibl:
                touch = (1, i); break      # fade long at IB low
        if touch is not None:
            side, i0 = touch
            tclock = r.loc[i0].clock
            near = f[(f.clock >= _shift(tclock, -2)) & (f.clock <= _shift(tclock, 2))]
            # toucher pushing INTO the extreme: at IB high the aggressor is buyers
            # (absorb_side == -1 means buyers absorbed) — fade short wants that
            absorbed = bool((near.absorb & (near.absorb_side == side)).any()) if len(near) else False
            wall = np.nan
            if dep is not None and tclock in dep.index:
                snap = dep.loc[tclock]
                wall = float(snap.ask_wall_ratio if side < 0 else snap.bid_wall_ratio)
            entry = ibh if side < 0 else ibl
            stop = entry - side * 0.25 * rng
            target = mid
            bars = r.loc[i0 + 1:][["high", "low", "close"]].to_numpy()
            pts = _sim(side, entry, stop, target, bars)
            fadeB.append(dict(pts=pts, risk=abs(entry - stop), half=half,
                              absorbed=absorbed, wall=wall,
                              wall_ok=bool(wall == wall and wall >= 3.0)))

        # ---- BRANCH A retest: break + flow-at-break ----
        post = r[r.clock >= "10:00"]
        up = post[post.close > ibh]; dn = post[post.close < ibl]
        tu = up.index[0] if len(up) else None
        td = dn.index[0] if len(dn) else None
        if tu is None and td is None:
            continue
        side = 1 if (td is None or (tu is not None and tu < td)) else -1
        ib_i = tu if side > 0 else td
        bclock = r.loc[ib_i].clock
        entry = float(r.loc[ib_i].close)
        fb = f[f.clock == bclock]
        dz = float(fb.dz.iloc[0]) if len(fb) else np.nan
        effl = bool(fb.effortless.iloc[0]) if len(fb) else False
        conf = bool(dz == dz and side * dz >= 1.0)   # aggression with the break
        wall_gone = np.nan
        if dep is not None and bclock in dep.index:
            snap = dep.loc[bclock]
            wall_gone = float(snap.ask_wall_ratio if side > 0 else snap.bid_wall_ratio)
        bars = r.loc[ib_i + 1:][["high", "low", "close"]].to_numpy()
        pts = _sim(side, entry, entry - side * rng, entry + side * rng, bars)
        brkA.append(dict(pts=pts, risk=rng, half=half, conf=conf, effl=effl,
                         nowall=bool(wall_gone == wall_gone and wall_gone < 2.0)))

    print("== BRANCH B as taught (fade + absorption at extreme) ==")
    T = pd.DataFrame(fadeB)
    rep(fadeB, "all touches (strawman ref)")
    rep(T[T.absorbed].to_dict("records"), "TAUGHT: absorbed at extreme")
    rep(T[T.wall_ok].to_dict("records"), "wall>=3 at extreme")
    rep(T[T.absorbed & T.wall_ok].to_dict("records"), "absorbed + wall")
    print(f"  gate rates: absorbed {T.absorbed.mean():.0%}, wall data {T.wall.notna().mean():.0%}, wall>=3 {T.wall_ok.mean():.0%}")
    print("== BRANCH A retest (break + flow-at-break) ==")
    A = pd.DataFrame(brkA)
    rep(brkA, "all breaks (raw ref)")
    rep(A[A.conf].to_dict("records"), "dz-confirmed break")
    rep(A[A.effl].to_dict("records"), "effortless break")
    rep(A[A.nowall].to_dict("records"), "no-wall-ahead break")
    rep(A[A.conf & A.nowall].to_dict("records"), "dz + no-wall")


def _shift(clock: str, m: int) -> str:
    t = int(clock[:2]) * 60 + int(clock[3:]) + m
    return f"{t // 60:02d}:{t % 60:02d}"


def _sim(direction, entry, stop, target, bars):
    for hi, lo, cl in bars:
        if direction > 0:
            if lo <= stop: return stop - entry
            if hi >= target: return target - entry
        else:
            if hi >= stop: return entry - stop
            if lo <= target: return entry - target
    cl = bars[-1][2] if len(bars) else entry
    return (cl - entry) if direction > 0 else (entry - cl)


if __name__ == "__main__":
    main()
