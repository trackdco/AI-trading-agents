#!/usr/bin/env python3
"""NYA-IVB-01 trial 10 — the EXPANDED search (prereg amendment 2026-08-05c).

Event expansion: EVERY touch of the intact IB extremes (re-touches included,
one open position at a time) until the IB first breaks, under three window
arms (10:00-10:30 / -11:00 / -12:00). Stop-cap arms (none/30/20 pts) on the
widest window. State-conditional flow: delta-lean at entry re-tested inside
strategy-drawdown and same-day-loser states. Year-level reporting per the
SHIP-CARD masking lesson.

    python -m scripts.nya_ivb_fade_expand
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0


def run_day(r, w_end: str, cap: float | None):
    """All fade trades for one session under the expanded event rule."""
    ib = r[r.clock < "10:00"]
    if len(ib) < 25 or len(r) < 200:
        return []
    ibh, ibl = ib.high.max(), ib.low.min()
    rng = ibh - ibl
    if rng <= 0:
        return []
    mid = (ibh + ibl) / 2
    trades, in_pos = [], None
    arr = r[(r.clock >= "10:00")].reset_index()
    for k, row in arr.iterrows():
        if row.clock >= "15:55":
            break
        if in_pos is None:
            if row.clock >= w_end:
                break
            if row.close > ibh or row.close < ibl:
                break  # IB broke -> day over
            side = -1 if row.high >= ibh else (1 if row.low <= ibl else 0)
            if side:
                entry = ibh if side < 0 else ibl
                stop = entry - side * 0.25 * rng
                if cap is not None and abs(entry - stop) > cap:
                    stop = entry - side * cap
                in_pos = dict(side=side, entry=entry, stop=stop, k=k,
                              tclock=row.clock)
        else:
            s = in_pos["side"]
            if s < 0:
                if row.high >= in_pos["stop"]:
                    trades.append((in_pos, in_pos["entry"] - in_pos["stop"])); in_pos = None
                elif row.low <= mid:
                    trades.append((in_pos, in_pos["entry"] - mid)); in_pos = None
            else:
                if row.low <= in_pos["stop"]:
                    trades.append((in_pos, in_pos["stop"] - in_pos["entry"])); in_pos = None
                elif row.high >= mid:
                    trades.append((in_pos, mid - in_pos["entry"])); in_pos = None
            if in_pos is None and (row.close > ibh or row.close < ibl):
                break
    if in_pos is not None:
        cl = arr.close.iloc[-1]
        pts = (in_pos["entry"] - cl) if in_pos["side"] < 0 else (cl - in_pos["entry"])
        trades.append((in_pos, pts))
    out = []
    for pos, pts in trades:
        out.append(dict(side=pos["side"], tclock=pos["tclock"], pts=pts,
                        risk=abs(pos["entry"] - pos["stop"])))
    return out


def rep(T, label):
    if not len(T):
        print(f"  {label}: n=0"); return
    net = T.pts - FR
    r_ = net / T.risk
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    yrs = " ".join(f"{y}:{x.sum():+.0f}" for y, x in net.groupby(T.year))
    print(f"  {label}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r_.sum():+,.0f} PF {gw/max(gl,1e-9):.2f} | {yrs}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    FL = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    fl_by_day = {d: g for d, g in FL.groupby("gday")}

    days = {d: g.sort_values("ts").reset_index(drop=True) for d, g in R.groupby("gday")}
    for w_end, lbl in [("10:30", "W30 (current)"), ("11:00", "W60"), ("12:00", "W120")]:
        rows = []
        for d, r in days.items():
            for t in run_day(r, w_end, None):
                rows.append({**t, "day": d, "year": d[:4]})
        T = pd.DataFrame(rows)
        rep(T, f"{lbl} all-touches")
        if w_end == "12:00":
            T.to_parquet(ROOT / "output/nya_ivb_fade_expanded.parquet", index=False)
    print("-- stop caps on W120 --")
    for cap in (30.0, 20.0):
        rows = []
        for d, r in days.items():
            for t in run_day(r, "12:00", cap):
                rows.append({**t, "day": d, "year": d[:4]})
        rep(pd.DataFrame(rows), f"W120 cap{int(cap)}")
    # state-conditional flow on W120 uncapped
    T = pd.read_parquet(ROOT / "output/nya_ivb_fade_expanded.parquet").sort_values(["day", "tclock"]).reset_index(drop=True)
    T["net"] = T.pts - FR
    T["trail5"] = T.net.shift(1).rolling(5, min_periods=3).sum()
    dz = []
    for _, row in T.iterrows():
        f = fl_by_day.get(row.day)
        v = np.nan
        if f is not None:
            t = int(row.tclock[:2]) * 60 + int(row.tclock[3:])
            near = f[f.clock.map(lambda c: 0 <= t - (int(c[:2])*60+int(c[3:])) <= 5)]
            if len(near):
                v = float(near.delta.sum())
        dz.append(v)
    T["dz5"] = dz
    FS = T.dropna(subset=["dz5"])
    FS = FS.assign(conf=FS.side * FS.dz5 < 0)  # tape against toucher = fade confirmed
    print(f"-- state-conditional flow, W120, flow span ({len(FS)} trades) --")
    for state, g in [("in drawdown (trail5<0)", FS[FS.trail5 < 0]),
                     ("in profit (trail5>=0)", FS[FS.trail5 >= 0])]:
        for c, gg in [("flow-confirmed", g[g.conf]), ("flow-against", g[~g.conf])]:
            net = gg.net
            pf = net[net > 0].sum() / max(-net[net <= 0].sum(), 1e-9)
            print(f"  {state} + {c}: n={len(gg)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts PF {pf:.2f}")


if __name__ == "__main__":
    main()
