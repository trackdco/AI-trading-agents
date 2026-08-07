#!/usr/bin/env python3
"""NYO-ROT-01 trial 2 — conditioning search per prereg + §5.11: stop caps,
flow-at-touch (overnight is fully covered by fp_minutes on the flow span),
the euro-delta feature (first declared reuse of the euro-handoff residue),
time-of-night buckets. Timestamp-based flow joins (no clock-string ordering
bugs across midnight).

    python -m scripts.nyo_rotation_cond
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0


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
    ON = B[(B.clock >= "18:00") | (B.clock < "09:25")]
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")
    FP = pd.read_parquet(ROOT / "output/fp_minutes.parquet")   # ts-indexed minute delta

    events = []
    for d, r in ON.groupby("gday"):
        if d not in C.index or not (C.loc[d, "comp_age"] >= 2):
            continue
        vah, val = float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"])
        poc, width = float(C.loc[d, "comp_poc"]), float(C.loc[d, "comp_vah"]) - float(C.loc[d, "comp_val"])
        if width <= 0:
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 400:
            continue
        in_pos = None
        for k, row in r.iterrows():
            if in_pos is None:
                if row.close > vah or row.close < val:
                    break
                side = -1 if row.high >= vah else (1 if row.low <= val else 0)
                if side:
                    edge = vah if side < 0 else val
                    in_pos = dict(side=side, entry=edge, t=row.ts, k=k)
            else:
                s = in_pos["side"]
                stop_nat = in_pos["entry"] - s * 0.25 * width
                pts = None
                if s < 0:
                    if row.high >= stop_nat: pts = in_pos["entry"] - stop_nat
                    elif row.low <= poc: pts = in_pos["entry"] - poc
                else:
                    if row.low <= stop_nat: pts = stop_nat - in_pos["entry"]
                    elif row.high >= poc: pts = poc - in_pos["entry"]
                if pts is not None:
                    events.append(dict(day=d, year=d[:4], side=s, t=in_pos["t"],
                                       k0=in_pos["k"], entry=in_pos["entry"],
                                       width=width, poc=poc, pts=pts,
                                       risk=abs(in_pos["entry"] - stop_nat)))
                    in_pos = None
                    if row.close > vah or row.close < val:
                        break
        if in_pos is not None:
            cl = r.close.iloc[-1]
            s = in_pos["side"]
            stop_nat = in_pos["entry"] - s * 0.25 * width
            pts = (in_pos["entry"] - cl) if s < 0 else (cl - in_pos["entry"])
            events.append(dict(day=d, year=d[:4], side=s, t=in_pos["t"],
                               k0=in_pos["k"], entry=in_pos["entry"], width=width,
                               poc=poc, pts=pts, risk=abs(in_pos["entry"] - stop_nat)))
    E = pd.DataFrame(events)

    # stop caps: re-sim with capped stops needs bar paths — approximate legally:
    # a capped stop only changes trades whose natural risk exceeds the cap; re-sim those.
    days_map = {d: g.sort_values("ts").reset_index(drop=True) for d, g in ON.groupby("gday")}
    def resim_cap(ev, cap):
        if ev.risk <= cap:
            return ev.pts, ev.risk
        r = days_map[ev.day]
        stop = ev.entry - ev.side * cap
        for _, row in r.loc[ev.k0 + 1:].iterrows():
            if ev.side < 0:
                if row.high >= stop: return ev.entry - stop, cap
                if row.low <= ev.poc: return ev.entry - ev.poc, cap
            else:
                if row.low <= stop: return stop - ev.entry, cap
                if row.high >= ev.poc: return ev.poc - ev.entry, cap
        cl = r.close.iloc[-1]
        return ((ev.entry - cl) if ev.side < 0 else (cl - ev.entry)), cap

    print(f"events rebuilt: {len(E)}")
    rep(E, "natural stop (trial-1 ref)")
    for cap in (30.0, 20.0):
        res = [resim_cap(ev, cap) for ev in E.itertuples()]
        T = E.copy()
        T["pts"] = [x[0] for x in res]; T["risk"] = [x[1] for x in res]
        rep(T, f"cap{int(cap)}")

    # flow at touch (flow span): delta sum in [t-5m, t-1m]; fade confirmed = tape against toucher
    idx = FP.index
    conf = []
    for ev in E.itertuples():
        if ev.day < "2025-06-02":
            conf.append(np.nan); continue
        w = FP.loc[(idx >= ev.t - pd.Timedelta(minutes=5)) & (idx < ev.t)]
        conf.append(float(w.delta.sum()) if len(w) else np.nan)
    E["d5"] = conf
    FS = E.dropna(subset=["d5"])
    FS = FS.assign(conf=FS.side * FS.d5 < 0)
    print(f"-- flow at touch (flow span, {len(FS)} events) --")
    rep(FS[FS.conf], "fade flow-confirmed (tape against toucher)")
    rep(FS[~FS.conf], "flow-against")
    # euro-delta feature: London-window delta (03:00-05:00 ET) agreement, touches after 05:00 ET only
    eur = []
    for ev in FS.itertuples():
        hh = ev.t.hour
        if not (5 <= hh < 10):
            eur.append(np.nan); continue
        day0 = ev.t.normalize()
        w = FP.loc[(idx >= day0 + pd.Timedelta(hours=3)) & (idx < day0 + pd.Timedelta(hours=5))]
        eur.append(float(w.delta.sum()) if len(w) else np.nan)
    FS["eur"] = eur
    EU = FS.dropna(subset=["eur"])
    EU = EU.assign(agree=EU.side * EU.eur > 0)
    print(f"-- euro-delta feature (post-05:00 touches, {len(EU)} events) --")
    rep(EU[EU.agree], "london-delta agrees with fade")
    rep(EU[~EU.agree], "disagrees")
    # time-of-night
    E["bucket"] = E.t.dt.hour.map(lambda h: "18-22" if h >= 18 else ("22-02" if h >= 22 or h < 2 else ("02-06" if h < 6 else "06-0925")))
    print("-- time-of-night --")
    for b, g in E.groupby("bucket"):
        rep(g, f"bucket {b}")
    E.to_parquet(ROOT / "output/nyo_rotation_cond.parquet", index=False)


if __name__ == "__main__":
    main()
