#!/usr/bin/env python3
"""TWO JOBS: (A) control the bracket-geometry confound, (B) test a liquidity-sweep entry filter.

WHY THESE TOGETHER. gold_failure_diagnosis.py reported big winner/loser separations on stop
distance (sep +5.06), range width (-3.47) and distance-to-session-extreme (+6.01). All three are
suspected ARTIFACTS: the target is a fixed price (mean of the 5h range) while the stop is the
extension extreme, so anything that widens the stop shrinks the target measured in R and makes it
mechanically easier to reach. Win rate and E[R] moved in OPPOSITE directions across those buckets,
which is the fingerprint of exactly that confound.

A liquidity sweep -- price running a prior swing high/low to take out resting stops, then
reversing -- has the same problem: a sweep by definition pushes the extension extreme further,
widening the stop. So the sweep filter cannot be evaluated on its own; it must be evaluated at
CONSTANT target-distance-in-R. That is what this script does.

JOB A  compute tgt_R = |target - entry| / risk for every trade. Show E[R] by tgt_R quartile, then
       re-run the winner/loser separations WITHIN quartiles. A separation that vanishes inside
       strata was geometry, not behaviour, and gets dropped.

JOB B  PRE-REGISTERED liquidity-sweep filter, fixed before looking at any result:
         pivot      fractal high/low, 5 bars each side, on 1-min
         confirmed  the pivot must be CONFIRMED (index <= i - SHIFT_LOOK - 5) before the
                    extension window opens -> no lookahead
         lookback   pivots in [i - SHIFT_LOOK - 125, i - SHIFT_LOOK - 5]
         SELL sweep the extension high took out the highest prior pivot high AND price has closed
                    back below it by the signal bar. BUY mirrors.
         verdict    the filter earns its place only if the swept book beats the unswept book
                    WITHIN tgt_R strata. Beating it only in aggregate = it is a stop-width proxy.
       Session-extreme and prior-day-extreme sweeps are reported as a DESCRIPTIVE family of 3;
       the p-value belongs to the pivot definition. Best-of-3 is noted, not hidden.

STATUS: this sample (488 trades, one bull regime, Jul-2025 -> Jul-2026) has been queried many
times. Job A can only REMOVE candidates, which is safe. Job B adds one pre-registered test.
Nothing here is shippable without the 6E-filtered book and 2021-22 data.

    python3 scripts/gold_sweep_filter.py
"""
import importlib.util
import os

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "grt", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gold_reversal_test.py"))
grt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grt)

rng = np.random.default_rng(57)
H, L, C, TS, n = grt.H, grt.L, grt.C, grt.TS, grt.n
SL, PB, SPLIT = grt.SHIFT_LOOK, grt.PULLBACK, grt.SPLIT
PIVOT_K = 5                 # fractal half-width
SWEEP_LOOK = 125            # how far back to hunt for the swing being swept
NPERM = 5000

# ---------------------------------------------------------------- ATR + session/prior-day levels
b = grt.b
m15 = b.set_index("ts").resample("15min", label="right", closed="right").agg(
    high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna()
tr15 = np.maximum(m15.high - m15.low, np.maximum((m15.high - m15.close.shift(1)).abs(),
                                                 (m15.low - m15.close.shift(1)).abs()))
lab15, atrv = m15.index.values, tr15.rolling(14).mean().values

sess = (b.ts + pd.Timedelta(hours=2)).dt.strftime("%Y-%m-%d").values
run_hi = pd.Series(H).groupby(pd.Series(sess)).cummax().shift(1).values
run_lo = pd.Series(L).groupby(pd.Series(sess)).cummin().shift(1).values
g = pd.DataFrame({"s": sess, "h": H, "l": L}).groupby("s")
PDH, PDL = g.h.max().shift(1).to_dict(), g.l.min().shift(1).to_dict()

# ---------------------------------------------------------------- confirmed fractal pivots
print("build pivots ...", flush=True)
ph = np.zeros(n, dtype=bool)
pl = np.zeros(n, dtype=bool)
roll_h = pd.Series(H).rolling(2 * PIVOT_K + 1, center=True).max().values
roll_l = pd.Series(L).rolling(2 * PIVOT_K + 1, center=True).min().values
ph[PIVOT_K:n - PIVOT_K] = H[PIVOT_K:n - PIVOT_K] >= roll_h[PIVOT_K:n - PIVOT_K]
pl[PIVOT_K:n - PIVOT_K] = L[PIVOT_K:n - PIVOT_K] <= roll_l[PIVOT_K:n - PIVOT_K]
piv_hi_idx = np.flatnonzero(ph)
piv_lo_idx = np.flatnonzero(pl)
print(f"  {ph.sum():,} pivot highs   {pl.sum():,} pivot lows", flush=True)


def atr_at(k):
    j = max(int(np.searchsorted(lab15, TS[k], side="right")) - 1, 0)
    return atrv[min(j, len(atrv) - 1)]


def swept_pivot(i, d, ext_px):
    """Did the extension take out a CONFIRMED prior swing, and has price closed back through it?

    Returns (flag, depth_in_atr). depth is how far beyond the swing the extension reached.
    """
    hi_end = i - SL - PIVOT_K                       # last pivot confirmable before the extension
    lo_end = hi_end - SWEEP_LOOK
    if hi_end <= 0:
        return np.nan, np.nan
    arr = piv_hi_idx if d < 0 else piv_lo_idx
    lo_p = int(np.searchsorted(arr, max(lo_end, 0), side="left"))
    hi_p = int(np.searchsorted(arr, hi_end, side="right"))
    if hi_p <= lo_p:
        return np.nan, np.nan
    cand = arr[lo_p:hi_p]
    lvl = H[cand].max() if d < 0 else L[cand].min()
    a = atr_at(i)
    if not np.isfinite(a) or a <= 0:
        return np.nan, np.nan
    if d < 0:
        flag = (ext_px > lvl) and (C[i] < lvl)
        depth = (ext_px - lvl) / a
    else:
        flag = (ext_px < lvl) and (C[i] > lvl)
        depth = (lvl - ext_px) / a
    return float(flag), depth


def swept_level(i, d, ext_px, lvl):
    if not np.isfinite(lvl):
        return np.nan
    if d < 0:
        return float((ext_px > lvl) and (C[i] < lvl))
    return float((ext_px < lvl) and (C[i] > lvl))


# ---------------------------------------------------------------- book + geometry + sweep flags
print("build book ...", flush=True)
sigs = grt.signals({0, 1})
rows = []
for (i, d, sp, rh, rl) in sigs:
    r = grt.resolve(i, d, sp, rh, rl, 0, "mean", "pullback")
    if not r:
        continue
    # recompute entry/target deterministically to get target distance in R
    brk_from = H[i - SL:i].max() if d < 0 else L[i - SL:i].min()
    entry_px = C[i] + (brk_from - C[i]) * PB
    entry = entry_px - d * (grt.SLIP_TICKS * grt.TICK) / 2
    tgt = (rh + rl) / 2.0
    tgt_R = abs(tgt - entry) / r["risk"]
    a = atr_at(int(r["i"]))
    if not np.isfinite(a) or a <= 0:
        continue
    fl, dep = swept_pivot(i, d, sp)
    s = sess[i]
    rows.append(dict(
        R=r["R"], net=r["net"], day=r["day"], d=d, risk=r["risk"], win=r["R"] > 0,
        tgt_R=tgt_R,
        range_atr=(rh - rl) / a,
        sess_ext=abs(C[i] - (run_hi[i] if d < 0 else run_lo[i])) / a,
        swept=fl, sweep_depth=dep,
        swept_sess=swept_level(i, d, sp, run_hi[i] if d < 0 else run_lo[i]),
        swept_pd=swept_level(i, d, sp, PDH.get(s, np.nan) if d < 0 else PDL.get(s, np.nan)),
    ))
D = pd.DataFrame(rows)
D["train"] = D.day < SPLIT
print(f"  {len(D)} trades   WR {100*D.win.mean():.0f}%   E[R] {D.R.mean():+.3f}", flush=True)


def sep(sub, col):
    w, l = sub[sub.win][col].dropna(), sub[~sub.win][col].dropna()
    if len(w) < 8 or len(l) < 8:
        return np.nan, np.nan
    pooled = np.sqrt(w.var(ddof=1) / len(w) + l.var(ddof=1) / len(l))
    if not np.isfinite(pooled) or pooled <= 0:
        return np.nan, np.nan
    return w.mean() - l.mean(), (w.mean() - l.mean()) / pooled


def line(sub, lab):
    if len(sub) < 10:
        print(f"    {lab:34s} n={len(sub):4d}   (too few)"); return
    print(f"    {lab:34s} n={len(sub):4d}  WR {100*sub.win.mean():3.0f}%  "
          f"E[R] {sub.R.mean():+.3f}  net ${sub.net.sum():+8,.0f}")


def gap_perm_p(sub, flagcol):
    """Day-block permutation: shuffle day-mean R across days, recompute the flag gap."""
    s = sub.dropna(subset=[flagcol])
    if s[flagcol].nunique() < 2 or len(s) < 30:
        return np.nan
    udays, inv = np.unique(s.day.values, return_inverse=True)
    dmean = s.groupby("day").R.mean().values
    resid = s.R.values - dmean[inv]
    f = s[flagcol].values == 1.0
    if f.sum() < 10 or (~f).sum() < 10:
        return np.nan
    obs = s.R.values[f].mean() - s.R.values[~f].mean()
    cnt = 0
    for _ in range(NPERM):
        Rp = resid + dmean[rng.permutation(len(udays))][inv]
        if Rp[f].mean() - Rp[~f].mean() >= obs:
            cnt += 1
    return (cnt + 1) / (NPERM + 1)


if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("JOB A — IS THE 'CHARACTERISTICS' TABLE JUST BRACKET GEOMETRY?")
    print("=" * 100)
    print("  target distance in R (|target-entry|/risk): "
          f"median {D.tgt_R.median():.2f}   q1 {D.tgt_R.quantile(.25):.2f}   "
          f"q3 {D.tgt_R.quantile(.75):.2f}")
    print("\n  correlation of tgt_R with the suspect variables:")
    for c in ("risk", "range_atr", "sess_ext"):
        print(f"    tgt_R vs {c:12s}  r = {D.tgt_R.corr(D[c]):+.3f}")

    print("\n  E[R] BY tgt_R QUARTILE (if the edge is geometry it lives here)")
    D["q"] = pd.qcut(D.tgt_R, 4, labels=False, duplicates="drop")
    for q, s in D.groupby("q"):
        print(f"    Q{int(q)+1}  tgt_R [{s.tgt_R.min():5.2f},{s.tgt_R.max():5.2f}]  "
              f"n={len(s):4d}  WR {100*s.win.mean():3.0f}%  E[R] {s.R.mean():+.3f}")

    print("\n  WINNER/LOSER SEPARATION, WHOLE BOOK vs WITHIN tgt_R QUARTILES")
    print(f"    {'variable':14s} {'whole':>8s}   " +
          "  ".join(f"{'Q'+str(i+1):>8s}" for i in range(4)) + f"  {'mean|Q|':>8s}")
    for c in ("risk", "range_atr", "sess_ext"):
        _, s_all = sep(D, c)
        qs = [sep(D[D.q == q], c)[1] for q in range(4)]
        mq = np.nanmean(np.abs(qs))
        print(f"    {c:14s} {s_all:>+8.2f}   " +
              "  ".join(f"{v:>+8.2f}" if np.isfinite(v) else f"{'--':>8s}" for v in qs) +
              f"  {mq:>8.2f}")
    print("\n    A separation that collapses inside quartiles was geometry. One that survives")
    print("    at similar magnitude in every quartile is a real behavioural difference.")

    print("\n" + "=" * 100)
    print("JOB B — LIQUIDITY SWEEP FILTER (PRE-REGISTERED: confirmed fractal pivot)")
    print("=" * 100)
    S = D.dropna(subset=["swept"])
    print(f"  evaluable trades (a confirmed prior pivot existed): {len(S)}/{len(D)}")
    print("\n  AGGREGATE")
    line(S[S.swept == 1], "SWEPT prior swing")
    line(S[S.swept == 0], "no sweep")
    if S.swept.nunique() > 1:
        gp = S[S.swept == 1].R.mean() - S[S.swept == 0].R.mean()
        print(f"    -> gap {gp:+.3f} R/trade    day-block perm p = {gap_perm_p(S,'swept'):.4f}")

    print("\n  TRAIN / TEST")
    for tr_, nm in ((True, "train"), (False, "TEST ")):
        sub = S[S.train == tr_]
        line(sub[sub.swept == 1], f"{nm}  SWEPT")
        line(sub[sub.swept == 0], f"{nm}  no sweep")

    print("\n  THE DECIDING TEST — SWEPT vs NOT, WITHIN tgt_R QUARTILES")
    print("    (if the sweep is just a wide-stop proxy the gap dies here)")
    gaps = []
    for q in range(4):
        sub = S[S.q == q]
        a, c_ = sub[sub.swept == 1], sub[sub.swept == 0]
        if len(a) < 10 or len(c_) < 10:
            print(f"    Q{q+1}  swept n={len(a):3d}  unswept n={len(c_):3d}   (too few)")
            continue
        gp = a.R.mean() - c_.R.mean()
        gaps.append(gp)
        print(f"    Q{q+1}  swept n={len(a):3d} E[R] {a.R.mean():+.3f}   "
              f"unswept n={len(c_):3d} E[R] {c_.R.mean():+.3f}   gap {gp:+.3f}")
    if gaps:
        print(f"    mean within-quartile gap {np.mean(gaps):+.3f}   "
              f"quartiles positive {sum(1 for x in gaps if x>0)}/{len(gaps)}")

    print("\n  SWEEP DEPTH (how far past the swing) — descriptive")
    Sd = S[S.swept == 1].dropna(subset=["sweep_depth"])
    if len(Sd) > 40:
        for lo, hi in ((0, .25), (.25, .75), (.75, 99)):
            s = Sd[(Sd.sweep_depth >= lo) & (Sd.sweep_depth < hi)]
            if len(s) >= 10:
                print(f"    depth [{lo:g},{hi:g}) ATR  n={len(s):4d}  WR {100*s.win.mean():3.0f}%  "
                      f"E[R] {s.R.mean():+.3f}")

    print("\n  DESCRIPTIVE FAMILY (best-of-3 — p-value above belongs to the pivot definition)")
    for c, lab in (("swept", "confirmed pivot swing"),
                   ("swept_sess", "session high/low"),
                   ("swept_pd", "prior-day high/low")):
        s = D.dropna(subset=[c])
        a, c_ = s[s[c] == 1], s[s[c] == 0]
        if len(a) >= 10 and len(c_) >= 10:
            print(f"    {lab:24s} swept n={len(a):4d} E[R] {a.R.mean():+.3f}   "
                  f"not n={len(c_):4d} E[R] {c_.R.mean():+.3f}   gap {a.R.mean()-c_.R.mean():+.3f}")

    print("\n  NOTE: one regime, heavily queried sample. A pass here is a candidate for the")
    print("  6E-filtered book and 2021-22 data, not a result.")
