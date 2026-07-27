#!/usr/bin/env python3
"""THE DOLLAR TEST — the one part of the YouTuber's spec that has never been checked.

He claims the dollar filter is his single biggest edge: base win rate ~80%, "boosted to 83%" by
requiring DXY to be moving against the gold trade. Every gold script in this repo has carried the
disclaimer that this was UNTESTED, not disproven, because DXY is an ICE product and the earlier
pull was CME-only. That gap is now closed: DX is the actual ICE Dollar Index, and 6E is the CME
euro leg kept as an independent cross-check.

PRE-REGISTERED, fixed before any result was looked at:
  PRIMARY     instrument DX. Lookback 15 minutes -- the same timescale as the 1-min structure
              shift the entry is built on, chosen for that reason and not swept.
  RULE        CONFIRM when the dollar moves AGAINST the gold trade over the lookback:
                gold SELL -> DX return > 0   (dollar bid, gold should fall)
                gold BUY  -> DX return < 0   (dollar offered, gold should rise)
  TIMING      the window is [fill - 15min, fill), strictly BEFORE the fill bar. Nothing at or
              after the fill is read. This is the exact shape of the CVD lookahead bug found
              earlier in the NQ book, so it is stated explicitly rather than left to inference.
  VERDICT     the filter earns its place only if confirmed E[R] beats unconfirmed AND the gap
              survives a day-block permutation AND it survives WITHIN tgt_R quartiles.

  SIGN NOTE ON 6E. Gold and the euro are BOTH inverse-dollar, so they move TOGETHER. His
  "inversion on DXY" becomes "AGREEMENT with 6E". Getting this backwards would silently invert
  the entire test, so 6E's rule is spelled out separately rather than derived on the fly.

THREE FALSIFIERS, pre-registered, run regardless of the primary result:
  F1 DIRECTION-BLIND  does a large |DX move| read as well as the direction-aware version? In the
                      NQ order-flow campaign the direction-blind variant matched the direction-
                      aware one, which is what exposed that whole family as activity, not signal.
  F2 PLACEBO LAG      the same rule on the window ending 60 minutes BEFORE the fill. Stale
                      information should be worthless. If the placebo reads as well as the real
                      thing, the "signal" is a market-wide drift artifact.
  F3 tgt_R CONTROL    the target is a fixed price and the stop is the extension extreme, so any
                      variable correlated with stop width mimics an edge. Three prior candidates
                      died here. This one gets the same treatment.

DATA HYGIENE. DX is thin in Asia (67% of minutes, mean 11 lots/bar); 6E is dense (99%, 45 lots).
Quotes are matched as-of with a staleness tolerance, and any return spanning a contract ROLL is
discarded rather than silently computed across the price gap.

    python3 scripts/gold_dxy_test.py
"""
import importlib.util
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "grt", os.path.join(HERE, "scripts", "gold_reversal_test.py"))
grt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grt)

rng = np.random.default_rng(91)
H, L, C, TS = grt.H, grt.L, grt.C, grt.TS
SL, PB, SPLIT = grt.SHIFT_LOOK, grt.PULLBACK, grt.SPLIT
LOOKBACK_MIN = 15                 # PRE-REGISTERED primary
PLACEBO_LAG_MIN = 60              # F2
STALE_TOL_MIN = 10                # a quote older than this is not "current"
NPERM = 20000


class Ref:
    """As-of quote lookup with staleness and roll awareness."""

    def __init__(self, path, name):
        d = pd.read_parquet(path).sort_values("ts").reset_index(drop=True)
        self.name = name
        self.ts = d.ts.values.astype("datetime64[ns]")
        self.px = d.close.values.astype(float)
        self.cid = pd.factorize(d.contract)[0]
        print(f"  {name}: {len(d):,} bars  {d.ts.min()} -> {d.ts.max()}")

    def at(self, when):
        """(price, contract_id) of the last bar at or before `when`, or NaN if stale/absent."""
        k = int(np.searchsorted(self.ts, np.datetime64(when, "ns"), side="right")) - 1
        if k < 0:
            return np.nan, -1
        age = (np.datetime64(when, "ns") - self.ts[k]) / np.timedelta64(1, "m")
        if age > STALE_TOL_MIN:
            return np.nan, -1
        return self.px[k], self.cid[k]

    def ret(self, end_when, minutes):
        """Return over [end - minutes, end). NaN if either endpoint is stale or a roll spans it."""
        end = pd.Timestamp(end_when) - pd.Timedelta(minutes=1)     # strictly before the fill bar
        start = end - pd.Timedelta(minutes=minutes)
        p1, c1 = self.at(end)
        p0, c0 = self.at(start)
        if not (np.isfinite(p0) and np.isfinite(p1)) or c0 != c1 or p0 <= 0:
            return np.nan
        return (p1 - p0) / p0


print("load reference instruments ...", flush=True)
DX = Ref(os.path.join(HERE, "data/reference/dx_1m_master.parquet"), "DX")
E6 = Ref(os.path.join(HERE, "data/reference/6e_1m_master.parquet"), "6E")

# ---------------------------------------------------------------- gold book + dollar features
print("build gold book with dollar features ...", flush=True)
rows = []
for (i, d, sp, rh, rl) in grt.signals({0, 1}):
    r = grt.resolve(i, d, sp, rh, rl, 0, "mean", "pullback")
    if not r:
        continue
    k = int(r["i"])                                   # fill bar
    when = pd.Timestamp(TS[k])
    brk_from = H[i - SL:i].max() if d < 0 else L[i - SL:i].min()
    entry = (C[i] + (brk_from - C[i]) * PB) - d * (grt.SLIP_TICKS * grt.TICK) / 2
    tgt_R = abs((rh + rl) / 2.0 - entry) / r["risk"]
    dx_r = DX.ret(when, LOOKBACK_MIN)
    e6_r = E6.ret(when, LOOKBACK_MIN)
    dx_pl = DX.ret(when - pd.Timedelta(minutes=PLACEBO_LAG_MIN), LOOKBACK_MIN)
    rows.append(dict(
        R=r["R"], net=r["net"], day=r["day"], d=d, risk=r["risk"], win=r["R"] > 0, tgt_R=tgt_R,
        ts_fill=when,
        dx_ret=dx_r, e6_ret=e6_r, dx_placebo=dx_pl,
        gold_ret=(C[k] - C[max(k - LOOKBACK_MIN, 0)]) / C[max(k - LOOKBACK_MIN, 0)],
    ))
D = pd.DataFrame(rows)
D["train"] = D.day < SPLIT
# CONFIRM flags. DX: dollar moves AGAINST the trade. 6E: euro moves WITH the trade.
D["dx_conf"] = np.where(D.dx_ret.isna(), np.nan, (np.sign(D.dx_ret) == -D.d).astype(float))
D["e6_conf"] = np.where(D.e6_ret.isna(), np.nan, (np.sign(D.e6_ret) == D.d).astype(float))
D["dx_plac"] = np.where(D.dx_placebo.isna(), np.nan, (np.sign(D.dx_placebo) == -D.d).astype(float))
D["dx_abs"] = D.dx_ret.abs()
D["q"] = pd.qcut(D.tgt_R, 4, labels=False, duplicates="drop")
print(f"  {len(D)} trades   DX available {D.dx_ret.notna().sum()}   "
      f"6E available {D.e6_ret.notna().sum()}")


def line(sub, lab):
    if len(sub) < 10:
        print(f"    {lab:32s} n={len(sub):4d}   (too few)"); return
    print(f"    {lab:32s} n={len(sub):4d}  WR {100*sub.win.mean():3.0f}%  "
          f"E[R] {sub.R.mean():+.3f}  net ${sub.net.sum():+8,.0f}")


def gap_p(sub, col, nperm=NPERM):
    s = sub.dropna(subset=[col])
    f = s[col].values == 1.0
    if f.sum() < 10 or (~f).sum() < 10:
        return np.nan, np.nan
    ud, inv = np.unique(s.day.values, return_inverse=True)
    dm = s.groupby("day").R.mean().values
    resid = s.R.values - dm[inv]
    obs = s.R.values[f].mean() - s.R.values[~f].mean()
    cnt = 0
    for _ in range(nperm):
        Rp = resid + dm[rng.permutation(len(ud))][inv]
        if Rp[f].mean() - Rp[~f].mean() >= obs:
            cnt += 1
    return obs, (cnt + 1) / (nperm + 1)


def report(col, title, sub=None):
    s = (sub if sub is not None else D).dropna(subset=[col])
    print(f"\n  {title}")
    line(s[s[col] == 1], "CONFIRMED")
    line(s[s[col] == 0], "not confirmed")
    g, p = gap_p(s, col)
    if np.isfinite(g):
        wr_c = 100 * s[s[col] == 1].win.mean()
        wr_n = 100 * s[s[col] == 0].win.mean()
        print(f"      gap {g:+.3f} R/trade   win-rate gap {wr_c-wr_n:+.1f}pp   "
              f"day-block perm p = {p:.4f}")
    return s


if __name__ == "__main__":
    print("\n" + "=" * 98)
    print("0. SANITY — is gold actually inverse to the dollar in this window?")
    print("=" * 98)
    v = D.dropna(subset=["dx_ret"])
    print(f"  corr(gold 15m return, DX 15m return)  = {v.gold_ret.corr(v.dx_ret):+.3f}  n={len(v)}")
    v6 = D.dropna(subset=["e6_ret"])
    print(f"  corr(gold 15m return, 6E 15m return)  = {v6.gold_ret.corr(v6.e6_ret):+.3f}  n={len(v6)}")
    print("  (expected: NEGATIVE against DX, POSITIVE against 6E. If these are ~0 the premise")
    print("   itself is false in the Asia window and no filter built on it can work.)")

    print("\n" + "=" * 98)
    print(f"1. PRIMARY — DX confirmation, {LOOKBACK_MIN}-minute lookback (PRE-REGISTERED)")
    print("=" * 98)
    line(D, "whole book (reference)")
    report("dx_conf", f"DX moving AGAINST the trade over the prior {LOOKBACK_MIN}m")
    for tr_, nm in ((True, "train"), (False, "TEST ")):
        s = D[(D.train == tr_)].dropna(subset=["dx_conf"])
        line(s[s.dx_conf == 1], f"{nm}  CONFIRMED")
        line(s[s.dx_conf == 0], f"{nm}  not confirmed")

    print("\n" + "=" * 98)
    print("2. CROSS-CHECK — 6E agreement (independent instrument, opposite sign)")
    print("=" * 98)
    report("e6_conf", f"6E moving WITH the trade over the prior {LOOKBACK_MIN}m")

    print("\n" + "=" * 98)
    print("3. FALSIFIERS")
    print("=" * 98)
    print("\n  F1 DIRECTION-BLIND — does raw |DX move| read as well as the signed version?")
    b = D.dropna(subset=["dx_abs"])
    med = b.dx_abs.median()
    line(b[b.dx_abs >= med], "large |DX move|")
    line(b[b.dx_abs < med], "small |DX move|")
    print(f"      gap {b[b.dx_abs>=med].R.mean()-b[b.dx_abs<med].R.mean():+.3f} R/trade")
    print("      if this rivals the signed gap, the signal is activity, not direction.")

    report("dx_plac", f"F2 PLACEBO — same rule, window ending {PLACEBO_LAG_MIN}m BEFORE the fill")

    print("\n  F3 tgt_R CONTROL — DX confirmation within target-distance quartiles")
    gaps = []
    for q in range(4):
        s = D[(D.q == q)].dropna(subset=["dx_conf"])
        a, c_ = s[s.dx_conf == 1], s[s.dx_conf == 0]
        if len(a) < 8 or len(c_) < 8:
            print(f"      Q{q+1}  conf n={len(a):3d}  unconf n={len(c_):3d}   (too few)")
            continue
        g = a.R.mean() - c_.R.mean()
        gaps.append(g)
        print(f"      Q{q+1}  conf n={len(a):3d} E[R] {a.R.mean():+.3f}   "
              f"unconf n={len(c_):3d} E[R] {c_.R.mean():+.3f}   gap {g:+.3f}")
    if gaps:
        print(f"      mean within-quartile gap {np.mean(gaps):+.3f}   "
              f"positive {sum(1 for x in gaps if x>0)}/{len(gaps)}")

    print("\n" + "=" * 98)
    print("4. LOOKBACK SENSITIVITY (DESCRIPTIVE — the p-value belongs to 15m)")
    print("=" * 98)
    print("  A real effect degrades smoothly around the pre-registered value. A spike at 15m")
    print("  alone, or sign flips across neighbours, means the number got lucky.")
    print(f"    {'lookback':>9} {'n':>5} {'confE[R]':>10} {'unconfE[R]':>11} {'gap':>8} {'WRgap':>7}")
    fills = list(D.ts_fill)
    best_gap = -np.inf
    for lb in (5, 15, 30, 60, 120):
        rets = np.array([DX.ret(t, lb) for t in fills])
        conf = np.where(np.isnan(rets), np.nan, (np.sign(rets) == -D.d.values).astype(float))
        s = D.assign(cf=conf).dropna(subset=["cf"])
        a, c_ = s[s.cf == 1], s[s.cf == 0]
        if len(a) < 10 or len(c_) < 10:
            print(f"    {lb:>9} {len(s):>5}   (too few in one arm)")
            continue
        g = a.R.mean() - c_.R.mean()
        best_gap = max(best_gap, g)
        print(f"    {lb:>9} {len(s):>5} {a.R.mean():>+10.3f} {c_.R.mean():>+11.3f} "
              f"{g:>+8.3f} {100*(a.win.mean()-c_.win.mean()):>+6.1f}pp")
    print(f"\n    best gap across the 5-member lookback family: {best_gap:+.3f}")
    print("    Treat that as a best-of-5 number, not a discovery.")

    print("\n" + "=" * 98)
    print("VERDICT CHECKLIST — the filter ships only if ALL of these hold")
    print("=" * 98)
    print("  [ ] primary DX gap positive and day-block perm p < 0.05")
    print("  [ ] same sign in train AND test")
    print("  [ ] 6E cross-check agrees (independent instrument)")
    print("  [ ] direction-blind falsifier does NOT match the signed gap")
    print("  [ ] placebo-lag falsifier is null")
    print("  [ ] gap survives within tgt_R quartiles")
    print("\n  Even a clean sweep is a candidate, not a ship: this is one bull regime and the")
    print("  gold sample has been queried many times. GC 2021-22 remains the deciding data.")
