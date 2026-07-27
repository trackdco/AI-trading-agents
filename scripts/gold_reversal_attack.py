#!/usr/bin/env python3
"""ATTACK the positive gold-reversal result before believing it.

gold_reversal_test.py found the Asia-2nd-hour cell positive in BOTH halves:
  1.5R target  n=504  E[R] +0.117 (train +0.082 / test +0.154)
  mean target  n=488  E[R] +0.234 (train +0.257 / test +0.208)
while the same setup across ALL hours is E[R] ~0.000. That is a big claim and the first
positive thing found in this project, so it gets attacked, not celebrated.

FOUR ATTACKS
  1 CLEAN NULL       the original null used a MARKET entry while the real book uses a 50%
                     PULLBACK entry. A pullback fills at a better price by construction, so the
                     gap may be entry mechanics, not setup selection. Here the null uses the
                     IDENTICAL pullback machinery on random bars in the SAME hours.
  2 DECOMPOSITION    is the edge the SETUP or just the HOUR? Compare:
                       A real setup, Asia hours       B real setup, all hours
                       C random entry, Asia hours     D random entry, all hours
                     If C ~ A the hour is doing the work and the pattern is decoration.
  3 DAY PERMUTATION  shuffle trade outcomes across days (day-block, preserving within-day
                     clustering) and re-read E[R]. Gives a p-value for the observed mean.
  4 SUB-PERIOD       monthly E[R]. A real edge is not one or two months carrying everything.

    python3 scripts/gold_reversal_attack.py
"""
import os

import numpy as np
import pandas as pd

import importlib.util
spec = importlib.util.spec_from_file_location(
    "grt", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gold_reversal_test.py"))
grt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grt)                 # loads bars + defines signals/resolve/build

rng = np.random.default_rng(23)
ASIA = {0, 1}
NPERM = 5000


def rand_same_mechanics(sigs, r_mult, target_mode, hours):
    """Null with IDENTICAL pullback entry machinery, random bars in the same hour window."""
    pool = np.array([i for i in range(grt.RANGE_BARS + grt.SHIFT_LOOK, grt.n - grt.MAX_HOLD - 2)
                     if (hours is None or grt.hour[i] in hours)])
    rows = []
    for (i, d, sp, rh, rl) in sigs:
        for _ in range(4):                              # a few attempts to land a valid draw
            j = int(rng.choice(pool))
            rhj, rlj = grt.roll_hi[j], grt.roll_lo[j]
            if not (np.isfinite(rhj) and np.isfinite(rlj)):
                continue
            rs = rhj - rlj
            if not (grt.MIN_RANGE_PT <= rs <= grt.MAX_RANGE_PT):
                continue
            # same direction, same stop distance, but SAME pullback entry logic
            dist = abs(sp - grt.C[i])
            spj = grt.C[j] + (-d) * max(dist, 1.0)
            r = grt.resolve(j, d, spj, rhj, rlj, r_mult, target_mode, entry_mode="pullback")
            if r:
                rows.append(r); break
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["train"] = df.day < grt.SPLIT
    return df


def stat(df):
    if len(df) < 5:
        return None
    return dict(n=len(df), wr=100 * (df.R > 0).mean(), er=df.R.mean(), net=df.net.sum())


def show(df, lab):
    s = stat(df)
    if not s:
        print(f"  {lab:34s} n={len(df):4d}  (too few)"); return
    print(f"  {lab:34s} n={s['n']:4d}  WR {s['wr']:3.0f}%  E[R] {s['er']:+.3f}  net ${s['net']:+8,.0f}")


def day_perm_p(df):
    """Day-block permutation: shuffle day-mean R across days, keep within-day residuals."""
    if len(df) < 20:
        return np.nan
    d = df.groupby("day").R.transform("mean")
    resid = df.R.values - d.values
    udays, inv = np.unique(df.day.values, return_inverse=True)
    dmean = df.groupby("day").R.mean().values
    obs = df.R.mean()
    cnt = 0
    for _ in range(NPERM):
        perm = resid + dmean[rng.permutation(len(udays))][inv]
        if perm.mean() >= obs:
            cnt += 1
    return (cnt + 1) / (NPERM + 1)


if __name__ == "__main__":
    for tm, rm, lbl in (("R", 1.5, "target 1.5R"), ("mean", 0, "target = mean of range")):
        print(f"\n{'='*94}\n{lbl}\n{'='*94}")
        sa = grt.signals(ASIA)
        sall = grt.signals(None)
        A = grt.build(sa, rm, tm)
        B = grt.build(sall, rm, tm)
        print("  ATTACK 2 — is it the SETUP or the HOUR?")
        show(A, "A  real setup, ASIA hours")
        show(B, "B  real setup, all hours")
        C = rand_same_mechanics(sa, rm, tm, ASIA)
        D = rand_same_mechanics(sall, rm, tm, None)
        print("  ATTACK 1 — clean null (identical pullback mechanics, random bars)")
        show(C, "C  RANDOM entry, ASIA hours")
        show(D, "D  RANDOM entry, all hours")
        sA, sC = stat(A), stat(C)
        if sA and sC:
            print(f"     setup edge over random, same hours: {sA['er']-sC['er']:+.3f} R/trade")
        print("  ATTACK 3 — day-block permutation on A")
        p = day_perm_p(A)
        print(f"     observed E[R] {A.R.mean():+.3f}   permutation p = {p:.4f}")
        print("  ATTACK 4 — monthly E[R] (is it one or two months?)")
        A2 = A.copy()
        A2["m"] = A2.day.str[:7]
        mm = A2.groupby("m").agg(n=("R", "size"), er=("R", "mean"), net=("net", "sum"))
        print("     " + "  ".join(f"{m}:{r.er:+.2f}({int(r.n)})" for m, r in mm.iterrows()))
        print(f"     months positive: {int((mm.er>0).sum())}/{len(mm)}   "
              f"worst {mm.er.min():+.3f}  best {mm.er.max():+.3f}")
