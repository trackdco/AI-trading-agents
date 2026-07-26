#!/usr/bin/env python3
"""SCALE-OUT test for the London 10-13 UK book (last untested variant from the handoff).

Bank a fraction of the position at +XR, let the rest run to the 3R target with the stop
UNCHANGED (this is deliberately NOT the breakeven move, which was tested and lost).

Trade selection/entry/stop/target logic is copied verbatim from london_conviction.py so the
trade set is identical; the only addition is tracking whether +XR was touched before the
trade resolved.

INTRABAR AMBIGUITY: when a single M15 bar contains both the scale-level and the stop, we
cannot know the order from OHLC. The book builder already checks stop before target, so we
mirror that and report BOTH readings:
  conservative = stop assumed first (scale did NOT fill)   <- headline
  optimistic   = scale assumed first (scale filled)
The truth is between; if the two agree on the sign of the verdict, the verdict is robust.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_scaleout.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
TICK, PV, COMM = 0.25, 20.0, 5.0

print("load bars...", flush=True)
b = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b["uk"] = b.ts.dt.tz_convert("Europe/London")
b = b.sort_values("ts").reset_index(drop=True)
b["ukt"] = b.uk.dt.time

m = (b.set_index("ts").resample("15min", label="right", closed="right")
     .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
          close=("close", "last"), volume=("volume", "sum")).dropna(subset=["close"]))
_uk = m.index.tz_convert("Europe/London")
m["ukt"] = _uk.time
m["ukday"] = _uk.strftime("%Y-%m-%d")
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["v10"] = m.volume.rolling(10).mean().shift(1)
m["slo"] = m.low.rolling(5).min()
m["shi"] = m.high.rolling(5).max()
M = m.reset_index(names="uts").dropna(subset=["ma200"])
M = M[(M.ukday >= "2025-07-01") & (M.ukday <= "2026-07-15")].reset_index(drop=True)
a = {c: M[c].values for c in
     ["uts", "open", "high", "low", "close", "volume", "ma20", "ma50", "ma200", "v10", "slo", "shi"]}
ud, utt = M.ukday.values, M.ukt.values


def build(scale_R):
    """Walk trades once; return per-trade dict incl. whether +scale_R was touched."""
    rows = []
    for i in range(1, len(M) - 1):
        d = ud[i]
        if d in ("2025-11-28", "2026-04-03") or ud[i + 1] != d or not (dtime(10, 0) <= utt[i] < dtime(13, 0)):
            continue
        up = a["ma20"][i] > a["ma50"][i] > a["ma200"][i] and a["close"][i] > a["ma50"][i] and a["close"][i] > a["ma200"][i]
        dn = a["ma20"][i] < a["ma50"][i] < a["ma200"][i] and a["close"][i] < a["ma50"][i] and a["close"][i] < a["ma200"][i]
        dr = 1 if (up and a["low"][i] <= a["ma50"][i]) else (-1 if (dn and a["high"][i] >= a["ma50"][i]) else 0)
        if dr == 0 or not (a["v10"][i] > 0 and a["volume"][i] < a["v10"][i]):
            continue
        en = a["open"][i + 1] + dr * TICK
        rf = min(a["slo"][i], a["ma50"][i]) if dr > 0 else max(a["shi"][i], a["ma50"][i])
        rk = abs(en - rf) + TICK
        if rk < 5 or rk > 70:
            continue
        st, tg = en - dr * rk, en + dr * 3 * rk
        sc = en + dr * scale_R * rk                      # scale-out level
        gg, j = None, i + 1
        hit_cons = hit_opt = False                       # +scale_R touched?
        while j < len(M) and ud[j] == d:
            if utt[j] >= dtime(16, 30):
                gg = dr * (a["close"][j] - en); break
            hs = (a["low"][j] <= st) if dr > 0 else (a["high"][j] >= st)
            hsc = (a["high"][j] >= sc) if dr > 0 else (a["low"][j] <= sc)
            ht = (a["high"][j] >= tg) if dr > 0 else (a["low"][j] <= tg)
            if hsc:
                hit_opt = True                           # optimistic: scale fills even on stop bar
                if not hs:
                    hit_cons = True                      # conservative: only if stop not on same bar
            if hs:
                gg = -rk - TICK; break
            if ht:
                gg = 3 * rk - TICK; break
            j += 1
        if gg is None:
            gg = dr * (a["close"][min(j, len(M) - 1)] - en)
        rows.append(dict(day=d, ent=str(utt[i]), rk=rk, gg=gg,
                         hit_cons=hit_cons, hit_opt=hit_opt))
    A = pd.DataFrame(rows).sort_values(["day", "ent"]).reset_index(drop=True)
    A["net"] = A.gg * PV - COMM
    A["R"] = A.net / (A.rk * PV)
    # day-stop: first loss ends the day
    keep, = [[]]
    for d, g in A.groupby("day"):
        stp = False
        for _, r in g.iterrows():
            if stp:
                continue
            keep.append(r.name)
            if r.net < 0:
                stp = True
    return A.loc[keep].copy().reset_index(drop=True)


def scaleout_R(row, frac, scale_R, which):
    """R of the scaled-out variant. frac banked at +scale_R, (1-frac) rides to original exit.
    Extra exit leg -> commission x1.5."""
    hit = row.hit_cons if which == "cons" else row.hit_opt
    if not hit:
        return row.R                                   # never reached the level: unchanged
    gross = frac * (scale_R * row.rk - TICK) + (1 - frac) * row.gg
    return (gross * PV - COMM * 1.5) / (row.rk * PV)


if __name__ == "__main__":
    print("\n=== BASELINE (uncapped 3R, no scale-out) ===")
    base = build(1.0)
    bR = base.R.sum()
    print(f"  {len(base)} trades | net {bR:+.2f}R | WR {(base.R>0).mean()*100:.0f}% "
          f"| avg win {base[base.R>0].R.mean():+.2f}R | avg loss {base[base.R<=0].R.mean():+.2f}R")

    print("\n=== SCALE-OUT SWEEP (R-space; + = better than baseline) ===")
    print(f"{'bank@':>6} {'frac':>6} | {'conservative':>22} | {'optimistic':>22}")
    print(f"{'':>6} {'':>6} | {'netR':>8} {'vs base':>7} {'WR':>5} | {'netR':>8} {'vs base':>7} {'WR':>5}")
    for scale_R in (1.0, 1.5, 2.0):
        D = build(scale_R)
        for frac in (0.25, 0.5, 0.75):
            out = {}
            for which in ("cons", "opt"):
                r = D.apply(lambda x: scaleout_R(x, frac, scale_R, which), axis=1)
                out[which] = (r.sum(), (r > 0).mean() * 100)
            print(f"{scale_R:>6.1f} {frac:>6.0%} | {out['cons'][0]:>8.2f} {out['cons'][0]-bR:>+7.2f} "
                  f"{out['cons'][1]:>4.0f}% | {out['opt'][0]:>8.2f} {out['opt'][0]-bR:>+7.2f} {out['opt'][1]:>4.0f}%")

    D1 = build(1.0)
    print(f"\n  touch stats @+1R: conservative {D1.hit_cons.sum()}/{len(D1)} trades, "
          f"optimistic {D1.hit_opt.sum()}/{len(D1)}")
    L = D1[D1.R <= 0]
    print(f"  losers that touched +1R: cons {L.hit_cons.sum()}/{len(L)}, opt {L.hit_opt.sum()}/{len(L)}"
          f"   (these are the ones scale-out rescues)")
    W = D1[D1.R > 0]
    print(f"  winners (all must pass +1R): cons {W.hit_cons.sum()}/{len(W)}, opt {W.hit_opt.sum()}/{len(W)}"
          f"   (these are the ones scale-out taxes)")
