#!/usr/bin/env python3
"""NYO-ROT-01 trial 3 — corrected as-taught retest per the 2026-08-05
prereg amendment (RESPEC Spec 5). DVA-event entries replace the trial-1
touch-fade strawman: V-A shift-out and V-B doubled-edge hold, both with the
taught DVA scratch rule. Baseline for comparison: trial-1 touch-fade
(PF 1.10, +345 pts).

    python -m scripts.nyo_rotation_respec
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FR = 1.0
WARMUP = 15


def bands(r):
    tp = (r.high + r.low + r.close) / 3
    v = r.volume.clip(lower=0).astype(float)
    cv = v.cumsum().clip(lower=1)
    vwap = (tp * v).cumsum() / cv
    var = ((tp ** 2 * v).cumsum() / cv - vwap ** 2).clip(lower=0)
    sd = np.sqrt(var)
    return vwap, vwap + sd, vwap - sd


def rep(T, label):
    if not len(T):
        print(f"  {label}: n=0"); return
    net = T.pts - FR
    r_ = net / T.risk
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    print(f"  {label}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r_.sum():+,.0f} PF {gw/max(gl,1e-9):.2f}")
    for y, g in T.groupby("year"):
        gn = g.pts - FR
        yw, yl = gn[gn > 0].sum(), -gn[gn <= 0].sum()
        print(f"     {y}: n={len(g)} WR {(gn>0).mean():.0%} {gn.sum():+.0f}pts "
              f"${160*(gn/g.risk).sum():+,.0f} PF {yw/max(yl,1e-9):.2f}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    ON = B[(B.clock >= "18:00") | (B.clock < "09:25")]
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")

    trades = {"VA": [], "VB": []}
    n_sessions = 0
    for d, r in ON.groupby("gday"):
        if d not in C.index or not (C.loc[d, "comp_age"] >= 2):
            continue
        vah, val = float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"])
        width = vah - val
        if width <= 0:
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 400:
            continue
        n_sessions += 1
        vwap, dvh, dvl = bands(r)
        H, L, Cl = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()
        DVH, DVL = dvh.to_numpy(), dvl.to_numpy()
        year = d[:4]

        out_run = 0
        # per-variant state: None | dict(phase=..., side=..., ...)
        st = {"VA": None, "VB": None}
        pos = {"VA": None, "VB": None}

        for k in range(WARMUP, len(r)):
            c, h, l = Cl[k], H[k], L[k]
            # rotational state death: 3 consecutive closes outside composite
            out_run = out_run + 1 if (c > vah or c < val) else 0
            if out_run >= 3:
                break

            # extreme visit arms both variants (new sequence only when flat)
            side = -1 if h >= vah else (1 if l <= val else 0)
            for v in ("VA", "VB"):
                if side and pos[v] is None and st[v] is None:
                    st[v] = dict(side=side, phase="visited")

            # ---- V-A: re-enter dev VA, then close beyond far dev edge ----
            s = st["VA"]
            if s is not None and pos["VA"] is None:
                if s["phase"] == "visited":
                    near = DVH[k] if s["side"] < 0 else DVL[k]
                    if (s["side"] < 0 and c < near) or (s["side"] > 0 and c > near):
                        s["phase"] = "inside"
                elif s["phase"] == "inside":
                    far = DVL[k] if s["side"] < 0 else DVH[k]
                    if (s["side"] < 0 and c < far) or (s["side"] > 0 and c > far):
                        pos["VA"] = dict(side=s["side"], entry=c, k=k,
                                         scr_i=1)  # scratch line = far dev edge
                        st["VA"] = None

            # ---- V-B: back inside comp edge AND near dev edge, then hold ----
            s = st["VB"]
            if s is not None and pos["VB"] is None:
                edge = vah if s["side"] < 0 else val
                near = DVH[k] if s["side"] < 0 else DVL[k]
                if s["phase"] == "visited":
                    if (s["side"] < 0 and c < min(edge, near)) or \
                       (s["side"] > 0 and c > max(edge, near)):
                        s["phase"] = "inside"
                elif s["phase"] == "inside":
                    touched = (h >= near) if s["side"] < 0 else (l <= near)
                    held = (c < near) if s["side"] < 0 else (c > near)
                    if touched and held:
                        pos["VB"] = dict(side=s["side"], entry=c, k=k,
                                         scr_i=0)  # scratch line = near dev edge
                        st["VB"] = None

            # ---- manage open positions ----
            for v in ("VA", "VB"):
                p = pos[v]
                if p is None or p["k"] == k:
                    continue
                sd_ = p["side"]
                stop = (vah if sd_ < 0 else val) - sd_ * 0.25 * width
                tgt = val if sd_ < 0 else vah
                scr = (DVL[k], DVH[k])[p["scr_i"]] if sd_ < 0 else \
                      (DVH[k], DVL[k])[p["scr_i"]]
                pts = None
                if (sd_ < 0 and h >= stop) or (sd_ > 0 and l <= stop):
                    pts = sd_ * (stop - p["entry"])
                elif (sd_ < 0 and l <= tgt) or (sd_ > 0 and h >= tgt):
                    pts = sd_ * (tgt - p["entry"])
                elif (sd_ < 0 and c > scr) or (sd_ > 0 and c < scr):
                    pts = sd_ * (c - p["entry"])  # DVA scratch at close
                if pts is not None:
                    risk = abs((vah if sd_ < 0 else val) - sd_ * 0.25 * width - p["entry"])
                    trades[v].append(dict(day=d, year=year, pts=pts,
                                          risk=max(risk, 1e-9),
                                          clock=r.clock.iloc[p["k"]],
                                          comp_age=float(C.loc[d, "comp_age"]),
                                          width=width))
                    pos[v] = None

        for v in ("VA", "VB"):  # time-stop
            p = pos[v]
            if p is not None:
                cl = Cl[min(k, len(r) - 1)]
                sd_ = p["side"]
                risk = abs((vah if sd_ < 0 else val) - sd_ * 0.25 * width - p["entry"])
                trades[v].append(dict(day=d, year=d[:4], pts=sd_ * (cl - p["entry"]),
                                      risk=max(risk, 1e-9),
                                      clock=r.clock.iloc[p["k"]],
                                      comp_age=float(C.loc[d, "comp_age"]),
                                      width=width))

    print(f"qualifying overnight sessions: {n_sessions}")
    for v, lbl in (("VA", "V-A shift-out (his executed variant)"),
                   ("VB", "V-B doubled-edge hold (his recommended variant)")):
        T = pd.DataFrame(trades[v])
        if len(T):
            T.to_parquet(ROOT / f"output/nyo_rotation_respec_{v}.parquet", index=False)
        rep(T, lbl)
    print("baseline (trial-1 touch-fade strawman): n=145 PF 1.10 +345pts $-665")


if __name__ == "__main__":
    main()
