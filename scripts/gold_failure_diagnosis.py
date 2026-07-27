#!/usr/bin/env python3
"""WHERE DOES THE GOLD REVERSAL SETUP FAIL? — diagnosis, not testing.

The Asia-2nd-hour mean-reversion book sits at E[R] +0.238, p=0.090. Before adding confluences we
should know WHY the losers lose. This profiles winners vs losers across every characteristic
computable from 1-minute OHLCV, so any confluence we then test is aimed at a real failure mode
rather than picked from a list.

STATUS: DESCRIPTIVE / HYPOTHESIS-GENERATING. These are in-sample comparisons on one regime and
this same year of data has already been queried repeatedly. Nothing here is a validated result;
anything promising must be re-tested on the 6E-filtered book and on 2021-22 data before use.

WHAT CAN AND CANNOT BE COMPUTED
  available   the gold file is OHLCV 1-minute only -> VWAP, Bollinger, volume profile
              (POC/VAH/VAL), prior-day and session levels, relative volume, choppiness /
              efficiency ratio, trend alignment, extension geometry, MAE/MFE path shape
  NOT available  CVD, footprint, delta divergence, order-book heatmap. There is no tape or
              depth data for gold in this repo -- those confluences cannot be tested at all
              until trades/mbp-10 gold data is pulled.

    python3 scripts/gold_failure_diagnosis.py
"""
import importlib.util
import os

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "grt", os.path.join(os.path.dirname(os.path.abspath(__file__)), "gold_reversal_test.py"))
grt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grt)

b, O, H, L, C = grt.b, grt.O, grt.H, grt.L, grt.C
V = b.volume.values.astype(float)
TS = grt.TS
n = grt.n
BIN, VA = 0.5, 0.70

print("session context ...", flush=True)
# CME gold session boundary 18:00 ET = 22:00/23:00 UTC; use 22:00 UTC for a stable session id
sess = (b.ts + pd.Timedelta(hours=2)).dt.strftime("%Y-%m-%d").values
b_sess = pd.Series(sess)
# session VWAP + running extremes
tp = (H + L + C) / 3.0
cv = pd.Series(V).groupby(b_sess).cumsum().values
cvp = pd.Series(tp * V).groupby(b_sess).cumsum().values
vwap = np.where(cv > 0, cvp / cv, np.nan)
run_hi = pd.Series(H).groupby(b_sess).cummax().values
run_lo = pd.Series(L).groupby(b_sess).cummin().values
# prior session extremes
g = pd.DataFrame({"s": sess, "h": H, "l": L}).groupby("s")
PDH = g.h.max().shift(1).to_dict()
PDL = g.l.min().shift(1).to_dict()
# ATR14 on 15-min
m15 = b.set_index("ts").resample("15min", label="right", closed="right").agg(
    high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna()
tr15 = np.maximum(m15.high - m15.low, np.maximum((m15.high - m15.close.shift(1)).abs(),
                                                 (m15.low - m15.close.shift(1)).abs()))
atr15 = tr15.rolling(14).mean()
lab15, atrv = m15.index.values, atr15.values
# Bollinger on 1-min (20, 2)
ma20 = pd.Series(C).rolling(20).mean().values
sd20 = pd.Series(C).rolling(20).std().values
bb_up, bb_dn = ma20 + 2 * sd20, ma20 - 2 * sd20
# relative volume vs prior 60 bars
vol_rel = (pd.Series(V) / pd.Series(V).rolling(60).mean().shift(1)).values


def prior_day_profile(s_prev, idx_map):
    ii = idx_map.get(s_prev)
    if ii is None or len(ii) < 50:
        return None
    lo_i = np.floor(L[ii] / BIN).astype(np.int64)
    hi_i = np.floor(H[ii] / BIN).astype(np.int64)
    span = (hi_i - lo_i + 1).clip(min=1)
    rep = np.repeat(np.arange(len(ii)), span)
    offs = np.concatenate([np.arange(s) for s in span])
    bins = lo_i[rep] + offs
    w = (V[ii] / span)[rep]
    o = np.argsort(bins, kind="stable")
    uq, st = np.unique(bins[o], return_index=True)
    tot = np.add.reduceat(w[o], st)
    if tot.sum() <= 0:
        return None
    centers = (uq + 0.5) * BIN
    poc = int(tot.argmax())
    loi = hii = poc
    cov, tgt = tot[poc], VA * tot.sum()
    while cov < tgt - 1e-9 and (loi > 0 or hii < len(tot) - 1):
        bl = tot[loi - 1] if loi > 0 else -np.inf
        ab = tot[hii + 1] if hii < len(tot) - 1 else -np.inf
        if ab >= bl:
            hii += 1; cov += tot[hii]
        else:
            loi -= 1; cov += tot[loi]
    return dict(poc=centers[poc], vah=centers[hii], val=centers[loi])


idx_map = {s: np.array(ix) for s, ix in pd.Series(sess).groupby(sess).indices.items()}
sess_sorted = sorted(idx_map)
prev_of = {s: sess_sorted[i - 1] for i, s in enumerate(sess_sorted) if i > 0}
PROF = {}
for s in sess_sorted[1:]:
    PROF[s] = prior_day_profile(prev_of[s], idx_map)

# ---------------------------------------------------------------- build the book with features
sigs = grt.signals({0, 1})
df = grt.build(sigs, 0, "mean")
sig_by_fill = {}
for (i, d, sp, rh, rl) in sigs:
    sig_by_fill.setdefault(i, (d, sp, rh, rl))

rows = []
for _, r in df.iterrows():
    k = int(r.i)                       # fill bar
    s = sess[k]
    a = atrv[max(np.searchsorted(lab15, TS[k], side="right") - 1, 0)]
    if not np.isfinite(a) or a <= 0:
        continue
    d = int(r.d)
    # path shape: MAE / MFE ONLY WHILE THE TRADE IS OPEN.
    # BUG FIXED 2026-07-27: this previously walked the full MAX_HOLD horizon regardless of when
    # the trade actually exited, so it counted price action AFTER the stop was hit. That
    # inflated loser MFE from +0.83R to +2.54R and produced the false headline "80% of losers
    # reached +0.75R first" (true figure: 37%). The exit sweep's negative result is what exposed
    # it -- if losers really banked +2.5R first, a 1R target would have printed money.
    horizon = min(k + grt.MAX_HOLD, n - 1)
    adv_hi, adv_lo, _stop_hit = 0.0, 0.0, False
    for _k in range(k + 1, horizon + 1):
        _f = d * (H[_k] - C[k]) if d > 0 else d * (L[_k] - C[k])
        _a = d * (L[_k] - C[k]) if d > 0 else d * (H[_k] - C[k])
        adv_hi, adv_lo = max(adv_hi, _f), min(adv_lo, _a)
        if _a <= -r.risk:                      # stopped out -> stop measuring
            break
    # choppiness of the 60 min before entry: net move / summed absolute move
    p0 = C[max(k - 60, 0):k + 1]
    path = np.abs(np.diff(p0)).sum()
    eff = abs(p0[-1] - p0[0]) / path if path > 0 else np.nan
    # the 5h range this trade faded
    rh, rl = grt.roll_hi[k], grt.roll_lo[k]
    rw = (rh - rl) if np.isfinite(rh) and np.isfinite(rl) else np.nan
    pr = PROF.get(s)
    pdh, pdl = PDH.get(s, np.nan), PDL.get(s, np.nan)
    rows.append(dict(
        R=r.R, net=r.net, day=r.day, d=d, risk=r.risk,
        win=r.R > 0,
        mae=adv_lo / r.risk, mfe=adv_hi / r.risk,
        eff60=eff,
        range_atr=rw / a if np.isfinite(rw) else np.nan,
        vwap_dist=d * (C[k] - vwap[k]) / a if np.isfinite(vwap[k]) else np.nan,
        # positive = entering AGAINST the session VWAP side (fading away from vwap)
        bb_out=1.0 if (d < 0 and C[k] > bb_up[k]) or (d > 0 and C[k] < bb_dn[k]) else 0.0,
        bb_back=1.0 if (d < 0 and C[k] < bb_up[k] and H[k] > bb_up[k]) or
                       (d > 0 and C[k] > bb_dn[k] and L[k] < bb_dn[k]) else 0.0,
        vol_rel=vol_rel[k],
        # distance to the level the trade is fading toward/away from, in ATR
        pd_dist=(min(abs(C[k] - pdh), abs(C[k] - pdl)) / a) if np.isfinite(pdh) else np.nan,
        sess_ext=(abs(C[k] - (run_hi[k] if d < 0 else run_lo[k])) / a),
        poc_dist=(abs(C[k] - pr["poc"]) / a) if pr else np.nan,
        in_va=(1.0 if pr and pr["val"] <= C[k] <= pr["vah"] else 0.0) if pr else np.nan,
        hhmm=pd.Timestamp(TS[k]).strftime("%H:%M"),
    ))
D = pd.DataFrame(rows)
print(f"book: {len(D)} trades   WR {100*D.win.mean():.0f}%   E[R] {D.R.mean():+.3f}\n")


def cmp_col(col, label):
    w, l = D[D.win][col].dropna(), D[~D.win][col].dropna()
    if len(w) < 10 or len(l) < 10:
        return
    pooled = np.sqrt(w.var(ddof=1) / len(w) + l.var(ddof=1) / len(l))
    sep = (w.mean() - l.mean()) / pooled if pooled > 0 else np.nan
    print(f"  {label:26s} win {w.mean():>8.3f}   loss {l.mean():>8.3f}   "
          f"diff {w.mean()-l.mean():>+8.3f}   sep {sep:>+5.2f}")


if __name__ == "__main__":
    print("=" * 96)
    print("1. HOW DO LOSERS DIE?  path shape (MAE/MFE in R, over the trade's life)")
    print("=" * 96)
    for lab, sub in (("winners", D[D.win]), ("losers", D[~D.win])):
        print(f"  {lab:9s} n={len(sub):4d}   mean MFE {sub.mfe.mean():+.2f}R   "
              f"mean MAE {sub.mae.mean():+.2f}R   "
              f"median MFE {sub.mfe.median():+.2f}R")
    los = D[~D.win]
    never = (los.mfe < 0.25).mean() * 100
    halfway = (los.mfe >= 0.75).mean() * 100
    print(f"\n  losers that NEVER went 0.25R in favour : {never:.0f}%   -> instant rejection = bad entry")
    print(f"  losers that DID reach 0.75R+ first     : {halfway:.0f}%   -> gave it back = exit/target problem")

    print("\n" + "=" * 96)
    print("2. WINNER vs LOSER CHARACTERISTICS  (sep = difference in standard errors; |sep|>2 notable)")
    print("=" * 96)
    for c, lab in (("eff60", "efficiency 60m (chop<->trend)"),
                   ("range_atr", "5h range width (ATR)"),
                   ("vwap_dist", "dist from session VWAP (ATR)"),
                   ("vol_rel", "relative volume at entry"),
                   ("risk", "stop distance (pts)"),
                   ("pd_dist", "dist to prior-day H/L (ATR)"),
                   ("sess_ext", "dist to session extreme (ATR)"),
                   ("poc_dist", "dist to prior-day POC (ATR)"),
                   ("bb_out", "closed outside Bollinger"),
                   ("bb_back", "wicked outside BB, closed back"),
                   ("in_va", "inside prior-day value area")):
        cmp_col(c, lab)

    print("\n" + "=" * 96)
    print("3. E[R] BY BUCKET  (descriptive -- where does the money actually come from?)")
    print("=" * 96)
    for c, lab, cuts in (("eff60", "efficiency 60m", [0, .15, .30, .50, 1.01]),
                         ("range_atr", "range width ATR", [0, 3, 5, 8, 99]),
                         ("vol_rel", "relative volume", [0, .8, 1.2, 2.0, 99]),
                         ("vwap_dist", "VWAP dist (ATR)", [-99, -0.5, 0, 0.5, 99]),
                         ("sess_ext", "dist to sess extreme", [0, .25, .75, 1.5, 99])):
        print(f"\n  {lab}")
        for lo, hi in zip(cuts[:-1], cuts[1:]):
            s = D[(D[c] >= lo) & (D[c] < hi)]
            if len(s) >= 15:
                print(f"    [{lo:>5g},{hi:>5g})  n={len(s):4d}  WR {100*s.win.mean():3.0f}%  "
                      f"E[R] {s.R.mean():+.3f}")

    print("\n" + "=" * 96)
    print("4. BINARY CONFLUENCES  (descriptive)")
    print("=" * 96)
    for c, lab in (("bb_out", "close outside Bollinger band"),
                   ("bb_back", "wick outside BB then close back in"),
                   ("in_va", "entry inside prior-day value area")):
        for v, nm in ((1.0, "yes"), (0.0, "no")):
            s = D[D[c] == v]
            if len(s) >= 15:
                print(f"  {lab:34s} {nm:3s}  n={len(s):4d}  WR {100*s.win.mean():3.0f}%  "
                      f"E[R] {s.R.mean():+.3f}")
        print()

    print("=" * 96)
    print("5. BY ENTRY MINUTE (is one part of the 2h window doing the work?)")
    print("=" * 96)
    D["hh"] = D.hhmm.str[:2]
    for h, s in D.groupby("hh"):
        print(f"  {h}:00 UTC   n={len(s):4d}  WR {100*s.win.mean():3.0f}%  E[R] {s.R.mean():+.3f}")
    print("\nNOTE: descriptive only, one regime, sample already queried. Confirm on 6E-filtered")
    print("book and 2021-22 data before treating anything here as a usable confluence.")
