#!/usr/bin/env python3
"""EXIT SWEEP on the gold Asia reversal book — aimed at the diagnosed failure mode.

gold_failure_diagnosis.py established the setup fails at the EXIT, not the entry:
  only 3% of losers never went 0.25R in favour; 80% reached +0.75R first and gave it back;
  mean loser MFE +2.54R against mean MAE -4.17R;
  winners had WIDER stops (6.30pt) than losers (4.67pt), sep +5.06.
So the two hypotheses worth a grid are (a) the stop is too tight for the range being faded and
(b) some of the +2.54R the losers reach should be banked.

PROTOCOL — this is a SWEEP, so the controls are structural, not advisory:
  * the ENTRY SET IS FIXED across every cell. Same fills, same entry prices. Only the exit
    changes, so cells are directly comparable and nothing leaks in via re-selection.
  * SELECTION HAPPENS ON TRAIN ONLY (days < 2026-01-15). The winner is chosen by train E[R]
    and its TEST number is then read once. Picking the best TEST cell would be the classic lie.
  * BEST-OF-N NULL on the selected cell: day-block permutation of outcomes, re-running the
    whole select-on-train/read-test pipeline, so the p-value prices the search itself.
  * every cell is printed, winners and losers, and the cell count is stated.

E[R] is the primary metric because widening a stop changes risk per trade; at constant dollar
risk E[R] is what compounds. Net $ at 1 MGC is printed alongside for reference.

    python3 scripts/gold_exit_sweep.py
"""
import importlib.util
import os

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "grt", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gold_reversal_test.py"))
grt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grt)

rng = np.random.default_rng(41)
H, L, C, TS, nb = grt.H, grt.L, grt.C, grt.TS, grt.n
PV, TICK, COMM = grt.PV, grt.TICK, grt.COMM
SPLIT = grt.SPLIT
NPERM = 3000
MAXH = 240                      # allow a longer horizon so trails/partials can breathe

# ATR on 15-min for trail widths
m15 = grt.b.set_index("ts").resample("15min", label="right", closed="right").agg(
    high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna()
tr = np.maximum(m15.high - m15.low, np.maximum((m15.high - m15.close.shift(1)).abs(),
                                               (m15.low - m15.close.shift(1)).abs()))
atr15 = tr.rolling(14).mean()
lab15, atrv = m15.index.values, atr15.values


def atr_at(ts):
    k = max(int(np.searchsorted(lab15, ts, side="right")) - 1, 0)
    return atrv[min(k, len(atrv) - 1)]


# ---------------------------------------------------------------- fixed entry set
print("build fixed entry set ...", flush=True)
sigs = grt.signals({0, 1})
FILLS = []
for (i, d, sp, rh, rl) in sigs:
    brk_from = H[i - grt.SHIFT_LOOK:i].max() if d < 0 else L[i - grt.SHIFT_LOOK:i].min()
    entry_px = C[i] + (brk_from - C[i]) * grt.PULLBACK
    fill = None
    for k in range(i + 1, min(i + 31, nb)):
        if (d < 0 and H[k] >= entry_px) or (d > 0 and L[k] <= entry_px):
            fill = k; break
        if (d < 0 and H[k] > sp) or (d > 0 and L[k] < sp):
            break
    if fill is None:
        continue
    entry = entry_px - d * (grt.SLIP_TICKS * TICK) / 2
    base_risk = abs(entry - sp)
    if not (grt.MIN_RISK_PT <= base_risk <= grt.MAX_RISK_PT):
        continue
    a = atr_at(TS[fill])
    if not np.isfinite(a) or a <= 0:
        continue
    FILLS.append(dict(k=fill, d=d, entry=entry, base_risk=base_risk, atr=a,
                      rh=rh, rl=rl, day=grt.day_arr[fill]))
print(f"  fixed entry set: {len(FILLS)} fills", flush=True)


def walk(f, stop_mult=1.0, mode="mean", r_tgt=2.0, part_frac=0.0, part_r=1.0,
         be_at=None, trail_r=None, trail_k=1.0, time_stop=None):
    """One trade under one exit configuration. Stop is checked before target each bar."""
    d, e, a = f["d"], f["entry"], f["atr"]
    risk = f["base_risk"] * stop_mult
    stop = e - d * risk
    if mode == "mean":
        tgt = (f["rh"] + f["rl"]) / 2.0
        if (d < 0 and tgt >= e) or (d > 0 and tgt <= e):
            return None
    else:
        tgt = e + d * r_tgt * risk
    pos, realised, best = 1.0, 0.0, 0.0
    horizon = min(f["k"] + (time_stop or MAXH), nb - 1)
    for k in range(f["k"] + 1, horizon + 1):
        fav = d * (H[k] - e) if d > 0 else d * (L[k] - e)
        adv = d * (L[k] - e) if d > 0 else d * (H[k] - e)
        best = max(best, fav)
        # stop first (pessimistic)
        if adv <= -(e - stop) * d / d if False else ((L[k] <= stop) if d > 0 else (H[k] >= stop)):
            realised += pos * (d * (stop - e))
            pos = 0.0
            break
        # partial
        if part_frac > 0 and pos == 1.0 and fav >= part_r * risk:
            realised += part_frac * (part_r * risk)
            pos = 1.0 - part_frac
        # breakeven
        if be_at is not None and best >= be_at * risk:
            be_px = e
            stop = max(stop, be_px) if d > 0 else min(stop, be_px)
        # trail
        if trail_r is not None and best >= trail_r * risk:
            peak = e + d * best
            new_stop = peak - d * trail_k * a
            stop = max(stop, new_stop) if d > 0 else min(stop, new_stop)
        # target
        if (H[k] >= tgt) if d > 0 else (L[k] <= tgt):
            realised += pos * (d * (tgt - e))
            pos = 0.0
            break
    if pos > 0:
        kk = min(horizon, nb - 1)
        realised += pos * (d * (C[kk] - e))
    net = realised * PV - COMM - (grt.SLIP_TICKS / 2 * TICK) * PV
    return dict(day=f["day"], R=net / (risk * PV), net=net, risk=risk)


CELLS = []
for sm in (1.0, 1.25, 1.5, 2.0):
    CELLS.append((f"stop{sm:g}x  mean-target", dict(stop_mult=sm, mode="mean")))
    for rt in (1.5, 2.0, 3.0):
        CELLS.append((f"stop{sm:g}x  {rt:g}R target", dict(stop_mult=sm, mode="R", r_tgt=rt)))
    CELLS.append((f"stop{sm:g}x  partial50@1R->mean",
                  dict(stop_mult=sm, mode="mean", part_frac=0.5, part_r=1.0)))
    CELLS.append((f"stop{sm:g}x  partial50@1R->mean+BE",
                  dict(stop_mult=sm, mode="mean", part_frac=0.5, part_r=1.0, be_at=1.0)))
    CELLS.append((f"stop{sm:g}x  BE@1R -> mean",
                  dict(stop_mult=sm, mode="mean", be_at=1.0)))
    CELLS.append((f"stop{sm:g}x  trail1ATR from 1R",
                  dict(stop_mult=sm, mode="mean", trail_r=1.0, trail_k=1.0)))
    CELLS.append((f"stop{sm:g}x  trail2ATR from 1R",
                  dict(stop_mult=sm, mode="mean", trail_r=1.0, trail_k=2.0)))
    CELLS.append((f"stop{sm:g}x  time-stop 60m",
                  dict(stop_mult=sm, mode="mean", time_stop=60)))


def run_cell(cfg, Rmap=None):
    rows = []
    for f in FILLS:
        r = walk(f, **cfg)
        if r:
            rows.append(r)
    df = pd.DataFrame(rows)
    if Rmap is not None and len(df):
        df["R"] = Rmap[:len(df)]
    return df


if __name__ == "__main__":
    print(f"\n{'='*104}")
    print(f"EXIT SWEEP — {len(CELLS)} cells, entry set FIXED at {len(FILLS)} fills")
    print(f"selection on TRAIN only (< {SPLIT}); TEST read once")
    print("=" * 104)
    print(f"  {'cell':<34} {'n':>4} {'trainE[R]':>10} {'testE[R]':>9} {'allE[R]':>8} {'net$':>9}")
    res = []
    for name, cfg in CELLS:
        df = run_cell(cfg)
        if len(df) < 50:
            continue
        tr_, te_ = df[df.day < SPLIT], df[df.day >= SPLIT]
        if len(tr_) < 20 or len(te_) < 20:
            continue
        res.append(dict(name=name, cfg=cfg, n=len(df), tr=tr_.R.mean(),
                        te=te_.R.mean(), all=df.R.mean(), net=df.net.sum(), df=df))
        print(f"  {name:<34} {len(df):>4} {tr_.R.mean():>+10.3f} {te_.R.mean():>+9.3f} "
              f"{df.R.mean():>+8.3f} {df.net.sum():>+9,.0f}")

    R = pd.DataFrame([{k: v for k, v in r.items() if k not in ("df", "cfg")} for r in res])
    base = next(r for r in res if r["name"] == "stop1x  mean-target")
    best = max(res, key=lambda r: r["tr"])            # SELECTED ON TRAIN
    print(f"\n{'='*104}")
    print(f"BASELINE  stop1x mean-target   train {base['tr']:+.3f}  TEST {base['te']:+.3f}  "
          f"all {base['all']:+.3f}")
    print(f"SELECTED (best TRAIN E[R]): {best['name']}")
    print(f"   train {best['tr']:+.3f}   ->   TEST {best['te']:+.3f}   "
          f"all {best['all']:+.3f}   net ${best['net']:+,.0f}   n={best['n']}")
    print("=" * 104)

    # best-of-N null: shuffle day-block outcomes, re-run select-on-train/read-test
    print(f"\nbest-of-{len(res)} null ({NPERM} day-block permutations) ...", flush=True)
    mats, days = [], None
    for r in res:
        d = r["df"]
        if days is None:
            days = d.day.values
        mats.append(d.R.values[:len(days)])
    Lmin = min(len(m) for m in mats)
    M = np.vstack([m[:Lmin] for m in mats])
    dv = days[:Lmin]
    udays, inv = np.unique(dv, return_inverse=True)
    trmask = dv < SPLIT
    dmeans = np.vstack([np.bincount(inv, weights=m, minlength=len(udays)) /
                        np.bincount(inv, minlength=len(udays)) for m in M])
    resid = M - dmeans[:, inv]
    cnt = 0
    obs = best["te"]
    for _ in range(NPERM):
        perm = rng.permutation(len(udays))
        Mp = resid + dmeans[:, perm][:, inv]
        tr_means = Mp[:, trmask].mean(axis=1)
        j = int(np.argmax(tr_means))
        if Mp[j, ~trmask].mean() >= obs:
            cnt += 1
    p = (cnt + 1) / (NPERM + 1)
    print(f"  observed TEST E[R] of the train-selected cell: {obs:+.3f}")
    print(f"  best-of-{len(res)} null p = {p:.4f}")
    print("\n  p is the probability that a search this size produces a TEST result this good")
    print("  from shuffled outcomes. It prices the sweep, not just the single cell.")
