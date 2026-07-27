#!/usr/bin/env python3
"""ONE PRE-REGISTERED FILTER: does an ADX trend-strength gate rescue the gold reversal setup?

CONTEXT. gold_reversal_test.py found the Asia-2nd-hour mean-reversion setup at E[R] +0.234
(train +0.257 / test +0.208) but day-block permutation p = 0.088 -- suggestive, underpowered.
Its obvious structural weakness: it fades range extremes even when price is in a strong trend,
which is exactly when fading gets run over.

THE HYPOTHESIS (from a Reddit trend-continuation EA that uses ADX+DI for regime): mean reversion
should work when the market is NOT trending. ADX measures trend strength specifically -- a
different question from the ATR/volatility regime we already tested and rejected on NQ.

PRE-REGISTRATION, fixed before looking at any result:
  * indicator  ADX(14), Wilder-smoothed, on H4 bars (his timeframe), last CLOSED H4 bar before
               the entry -> no lookahead
  * rule       TAKE the reversal trade when ADX < 25
  * threshold  25 is the TEXTBOOK non-trending level, not fitted here. One number, one test.
  * primary    the mean-of-range target book (the stronger of the two cells)
  * verdict    the filter earns its place only if it raises E[R] AND improves the day-block
               permutation p. Raising E[R] while shrinking n into insignificance is not a pass.

The ADX>=25 complement is reported because it is the same partition, not a second search.
A threshold sensitivity table is printed DESCRIPTION ONLY -- the p-value belongs to ADX<25.

    python3 scripts/gold_adx_filter.py
"""
import importlib.util
import os

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "grt", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gold_reversal_test.py"))
grt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grt)

rng = np.random.default_rng(31)
ASIA = {0, 1}
ADX_N = 14
ADX_THRESH = 25.0          # PRE-REGISTERED
NPERM = 20000

# ---------------------------------------------------------------- ADX(14) on H4, Wilder
print("build H4 ADX ...", flush=True)
b = grt.b
h4 = (b.set_index("ts").resample("4h", label="right", closed="right")
      .agg(high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna())
H, L, C = h4.high.values, h4.low.values, h4.close.values
pc = np.roll(C, 1); pc[0] = C[0]
tr = np.maximum(H - L, np.maximum(np.abs(H - pc), np.abs(L - pc)))
up_move = H - np.roll(H, 1)
dn_move = np.roll(L, 1) - L
up_move[0] = dn_move[0] = 0.0
plus_dm = np.where((up_move > dn_move) & (up_move > 0), up_move, 0.0)
minus_dm = np.where((dn_move > up_move) & (dn_move > 0), dn_move, 0.0)


def wilder(x, n):
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    out[n] = np.nansum(x[1:n + 1])
    for i in range(n + 1, len(x)):
        out[i] = out[i - 1] - out[i - 1] / n + x[i]
    return out


atr_w = wilder(tr, ADX_N)
pdm_w = wilder(plus_dm, ADX_N)
mdm_w = wilder(minus_dm, ADX_N)
with np.errstate(invalid="ignore", divide="ignore"):
    pdi = 100 * pdm_w / atr_w
    mdi = 100 * mdm_w / atr_w
    dx = 100 * np.abs(pdi - mdi) / (pdi + mdi)
adx = np.full(len(dx), np.nan)
first = ADX_N * 2
if len(dx) > first:
    adx[first] = np.nanmean(dx[ADX_N + 1:first + 1])
    for i in range(first + 1, len(dx)):
        adx[i] = (adx[i - 1] * (ADX_N - 1) + dx[i]) / ADX_N
h4_lab = h4.index.values
print(f"  H4 bars {len(h4)}  ADX finite on {np.isfinite(adx).sum()}", flush=True)


def adx_at(ts_arr):
    """ADX of the last CLOSED H4 bar strictly before each timestamp."""
    k = np.searchsorted(h4_lab, ts_arr, side="right") - 1
    k = np.clip(k, 0, len(adx) - 1)
    return adx[k], pdi[k], mdi[k]


# ---------------------------------------------------------------- build books
def attach(df):
    ts = grt.TS[df.i.values]
    a, p_, m_ = adx_at(ts)
    df = df.copy()
    df["adx"], df["pdi"], df["mdi"] = a, p_, m_
    return df[np.isfinite(df.adx)]


def day_perm_p(df):
    if len(df) < 20:
        return np.nan
    dmean = df.groupby("day").R.mean()
    inv = pd.factorize(df.day.values)[0]
    resid = df.R.values - dmean.values[inv]
    dm = dmean.values
    obs = df.R.mean()
    cnt = 0
    for _ in range(NPERM):
        if (resid + dm[rng.permutation(len(dm))][inv]).mean() >= obs:
            cnt += 1
    return (cnt + 1) / (NPERM + 1)


def show(df, lab, with_p=False):
    if len(df) < 5:
        print(f"  {lab:32s} n={len(df):4d}   (too few)"); return
    p = f"  perm p {day_perm_p(df):.4f}" if with_p else ""
    print(f"  {lab:32s} n={len(df):4d}  WR {100*(df.R>0).mean():3.0f}%  "
          f"E[R] {df.R.mean():+.3f}  net ${df.net.sum():+8,.0f}{p}")


if __name__ == "__main__":
    sigs = grt.signals(ASIA)
    for tm, rm, lbl in (("mean", 0, "PRIMARY: target = mean of range"),
                        ("R", 1.5, "secondary: target 1.5R")):
        base = attach(grt.build(sigs, rm, tm))
        print(f"\n{'='*92}\n{lbl}\n{'='*92}")
        show(base, "UNFILTERED (baseline)", with_p=True)
        keep = base[base.adx < ADX_THRESH]
        drop = base[base.adx >= ADX_THRESH]
        print(f"\n  PRE-REGISTERED FILTER: ADX(14) H4 < {ADX_THRESH:g}")
        show(keep, f"  ADX < {ADX_THRESH:g}  (TAKE)", with_p=True)
        show(drop, f"  ADX >= {ADX_THRESH:g}  (SKIP)")
        for sp, nm in ((True, "train"), (False, "TEST")):
            sub = keep[keep.day < grt.SPLIT] if sp else keep[keep.day >= grt.SPLIT]
            show(sub, f"    filtered {nm}")
        if len(keep) > 5 and len(base) > 5:
            print(f"    -> E[R] change {keep.R.mean()-base.R.mean():+.3f}   "
                  f"trades kept {len(keep)}/{len(base)} ({100*len(keep)/len(base):.0f}%)")

    # description only -- NOT the pre-registered test
    print(f"\n{'='*92}\nTHRESHOLD SENSITIVITY (DESCRIPTION ONLY — p-value belongs to ADX<25)\n{'='*92}")
    base = attach(grt.build(sigs, 0, "mean"))
    print(f"  {'thresh':>7} {'n':>5} {'WR':>5} {'E[R]':>8}")
    for t in (15, 20, 25, 30, 35, 40, 100):
        s = base[base.adx < t]
        if len(s) > 20:
            print(f"  {t:>7} {len(s):>5} {100*(s.R>0).mean():>4.0f}% {s.R.mean():>+8.3f}")
    print("\n  A plateau across thresholds = the effect is structural.")
    print("  A spike only at 25 = the textbook number got lucky and this is noise.")
