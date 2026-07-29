#!/usr/bin/env python3
"""CONFLUENCE STUDY — registered falsifiers (b) and the conviction-sizing DIAGNOSTIC.

Falsifier (a) direction-blind twin and (c) random-weights are computed here / in the random
shards; (b) single-best-feature runs the identical walk-forward with ONE feature at a time.

CONVICTION PART 1 (runs regardless of the composite's fate — it is a diagnostic on code already
running): conditional on a trade being TAKEN, do nth-escalation state, governor state and
day-ladder position predict realised R out of sample? Measured on the walk-forward frame with
day-clustered intervals, plus the n needed for 80% power beside every effect size.

CONVICTION PART 2 (score-proportional vs flat sizing under funded rules) is GATED on the
composite clearing its noise floor and is NOT run here — aggregate.py decides and reports.

BASELINE: partially remediated (C only) + news filter. W and dep_* remain LEAKY.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pipeline import (BLIND, POOL, headline, load, spearman,  # noqa: E402
                      walk_forward)

REPO = "/home/user/AI-trading-agents"
NBOOT, MIN_CELL = 4000, 10
rng = np.random.default_rng(20260729)
R = {"baseline": "PARTIALLY REMEDIATED (C only) + news filter; W and dep_* STILL LEAKY"}

J = load()
W = walk_forward(J, POOL, seed=0)
real = headline(J, W)
print(f"REAL composite: rho {real:+.4f} over {len(W)} walk-forward predictions "
      f"({J.day.nunique()} days, {len(J)} trades)")
R["real"] = dict(rho=real, n_pred=int(len(W)), n_trades=int(len(J)),
                 n_days=int(J.day.nunique()))

# ---------------------------------------------------------------- falsifier (a) + (b)
Wb = walk_forward(J, BLIND, seed=0)
blind = headline(J, Wb)
print(f"\nFALSIFIER (a) direction-blind twin ({len(BLIND)} unsigned features): rho "
      f"{blind:+.4f}  -> "
      f"{'FIRES: signed adds nothing' if blind >= real - 1e-9 else 'signed exceeds blind'}")
R["blind"] = dict(rho=blind, features=BLIND, fires=bool(blind >= real - 1e-9))

print("\nFALSIFIER (b) single-feature baselines — identical walk-forward, one feature at a time")
singles = {}
for f in POOL:
    Ws = walk_forward(J, [f], seed=0)
    singles[f] = headline(J, Ws)
    print(f"   {f:16s} rho {singles[f]:+.4f}")
best_f = max(singles, key=lambda k: singles[k])
print(f"   best single: {best_f} rho {singles[best_f]:+.4f}")
beats = real > singles[best_f] + 1e-9
print(f"   -> composite {'BEATS' if beats else 'DOES NOT BEAT'} its own best component: "
      f"{'confluence adds something' if beats else 'FIRES: confluence adds nothing'}")
R["singles"] = singles
R["best_single"] = dict(feature=best_f, rho=singles[best_f], composite_beats=bool(beats))

# ---------------------------------------------------------------- conviction diagnostic
print("\n" + "=" * 96)
print("CONVICTION PART 1 — do nth / governor / day-ladder state predict realised R, OOS?")
print("=" * 96)
mech = pd.read_parquet(f"{REPO}/research/sweep_2026_07/orderflow/job2_books/mech_C_news.parquet")
mech["ft"] = pd.to_datetime(mech.fill.astype(str).str.replace("T", " "), utc=True).astype(str)
mech["rk"] = mech["risk"].round(4)
mech = mech[(mech["size"] > 0) & (mech.win_ == "pre") & (mech.fillhm >= 480) & (mech.fillhm < 570)]
P0 = pd.read_csv(f"{REPO}/research/sweep_2026_07/orderflow/part0_frame.csv")
P0["ft"] = pd.to_datetime(P0.ft, utc=True).astype(str)
P0["rk"] = P0.risk_pts.round(4)
K = P0[["ft", "direction", "rk"]].merge(
    mech[["ft", "direction", "rk", "nth", "governor", "cold", "struct", "score", "size"]]
    .drop_duplicates(["ft", "direction", "rk"]), on=["ft", "direction", "rk"], how="left")
assert len(K) == len(J), (len(K), len(J))
J2 = J.copy()
for c in ("nth", "governor", "cold", "struct", "score", "size"):
    J2[c] = pd.to_numeric(K[c], errors="coerce").values
J2["day_pos"] = J2.groupby("day").cumcount() + 1     # day-ladder position

days = J2.day.values
u_days = pd.unique(days)
day_idx = {d: np.flatnonzero(days == d) for d in u_days}

def day_boot(fn):
    out = []
    for _ in range(NBOOT):
        pick = rng.choice(u_days, size=len(u_days), replace=True)
        ix = np.concatenate([day_idx[d] for d in pick])
        v = fn(ix)
        if np.isfinite(v):
            out.append(v)
    if len(out) < 100:
        return np.nan, np.nan, np.nan
    o = np.array(out)
    return (float(np.percentile(o, 2.5)), float(np.percentile(o, 97.5)),
            float(min(2 * min((o <= 0).mean(), (o >= 0).mean()), 1.0)))

def req_n(rho):
    if not np.isfinite(rho) or abs(rho) < 1e-6:
        return np.inf
    return float((2.802 / np.arctanh(min(abs(rho), 0.999))) ** 2 + 3)

STATE = ["nth", "governor", "cold", "day_pos", "struct", "score"]
oos = J2.oos.values.astype(bool)
print(f"{'state var':12s} {'rho (all)':>10} {'95% CI':>20} {'p':>7} {'rho OOS half':>13} "
      f"{'n needed':>10}  cells")
conv = {}
for c in STATE:
    x = J2[c].values.astype(float)
    y = J2.R.values.astype(float)
    rho = spearman(x, y)
    lo, hi, p = day_boot(lambda ix: spearman(x[ix], y[ix]))
    rho_o = spearman(x[oos], y[oos])
    nn = req_n(rho)
    vc = pd.Series(x).value_counts()
    thin = int((vc < MIN_CELL).sum())
    conv[c] = dict(rho=rho, ci=[lo, hi], p=p, rho_oos=rho_o, n_required=nn,
                   n=int(np.isfinite(x).sum()), thin_levels=thin,
                   levels={str(k): int(v) for k, v in vc.items()})
    print(f"{c:12s} {rho:>+10.3f} [{lo:>+8.3f},{hi:>+8.3f}] {p:>7.3f} {rho_o:>+13.3f} "
          f"{nn:>10,.0f}  {len(vc)} levels, {thin} under n={MIN_CELL}")
R["conviction_state"] = conv
sig = [c for c in STATE if np.isfinite(conv[c]["p"]) and conv[c]["p"] <= 0.05 / len(STATE)]
print(f"\n  surviving Bonferroni over {len(STATE)} state variables: {sig if sig else 'NONE'}")
R["conviction_survivors"] = sig

json.dump(R, open(f"{HERE}/falsifiers.json", "w"), indent=1, default=float)
print(f"\nwrote {HERE}/falsifiers.json")
