#!/usr/bin/env python3
"""Intra-trade ORDER FLOW path — can a loser be detected by flow before price shows it?

ANGUS 2026-08-06: *"I wanted to look at order flow during a trade and see if losers can be cut
early while keeping winners… HOW CAN WE DETECT A LOSER BEFORE IT LOSES… You are too monotone
with ur approach."*

Fair. `scripts/fvt_intratrade.py` tested the PRICE path (mark-to-market at minute N) and every
one of 28 rules lost to base, because a third of eventual winners are underwater at any given
minute. But price is only one of the two things happening inside a trade. This file tests the
FLOW path, and specifically the cases where the two DISAGREE:

  price flat + flow with you      absorption in your favour, should resolve your way
  price flat + flow against you   you are being leaned on, should resolve against you
  price up + flow against you     rally on no buying -- distribution, a warning
  price down + flow with you      selling absorbed -- accumulation

That divergence is invisible to a mark-to-market rule, which is what makes it a genuinely
different test rather than the same one re-run.

MEASURES, all cumulative from entry and all causal at the minute they are read:
  cum_delta   signed to trade direction, normalised by cumulative volume
  efficiency  points of price movement per unit of signed delta -- low efficiency with high
              delta is absorption AGAINST the position
  vol_trend   volume since entry vs the 30 bars before it -- is anyone actually there

THE BAR IS NOT "DO THE MEANS DIFFER". It is whether the populations SEPARATE enough to
classify. The price path failed on exactly that: means diverged steadily, overlap never
cleared. So every table here reports the overlap, not just the gap.

Flow data (output/fp_minutes.parquet) starts 2025-06, so this runs on a ~1,300 trade subset.

    python -m scripts.fvt_flowpath
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.fvt_model as F  # noqa: E402

FRIC, RR, ATR_TF = 0.5, 1.5, 30
MARKS = (3, 5, 10, 15, 20, 30)


def build(b: pd.DataFrame, fp: pd.DataFrame) -> list[dict]:
    b = b.copy()
    b["atr"] = F.atr_series(b, ATR_TF)
    rng = (b.high - b.low).to_numpy()
    upw = (b.high - np.maximum(b.open, b.close)).to_numpy()
    dnw = (np.minimum(b.open, b.close) - b.low).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        du = (b.close > b.open).to_numpy() & (np.where(rng > 0, dnw / rng, 1.0) <= F.WICK_MAX)
        dd = (b.close < b.open).to_numpy() & (np.where(rng > 0, upw / rng, 1.0) <= F.WICK_MAX)
    b["du"], b["dd"] = du, dd
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(F.NY)
    b = b.merge(fp[["delta", "vol"]], left_on="mi", right_index=True, how="left")

    out = []
    for day, g in b.groupby("day"):
        g = g.reset_index(drop=True)
        hi, lo, cl = g.high.to_numpy(float), g.low.to_numpy(float), g.close.to_numpy(float)
        hm, atr = g.hm.to_numpy(), g.atr.to_numpy(float)
        gu, gd = g.du.to_numpy(), g.dd.to_numpy()
        dl = g.delta.to_numpy(float)
        vl = g.vol.to_numpy(float)
        sh = np.full(len(g), np.nan); sl = np.full(len(g), np.nan)
        lh = ll = np.nan
        for i in range(len(g)):
            if i >= 2:
                if hi[i - 1] > hi[i - 2] and hi[i - 1] > hi[i]:
                    lh = hi[i - 1]
                if lo[i - 1] < lo[i - 2] and lo[i - 1] < lo[i]:
                    ll = lo[i - 1]
            sh[i], sl[i] = lh, ll
        for wn, wlo, whi in F.WINDOW_SETS["all"]:
            seg = np.flatnonzero(hm >= wlo)
            if not len(seg):
                continue
            fv = float(g.open.iloc[seg[0]])
            start = wlo + (F.SKIP_FIRST_MIN if wn == "AM" else 0)
            taken = False
            for i in np.flatnonzero((hm >= start) & (hm < wlo + 15)):
                if taken or not np.isfinite(atr[i]):
                    continue
                above = cl[i] > fv
                d_ = 0
                if above and np.isfinite(sh[i]) and cl[i] > sh[i] and gu[i]:
                    d_ = 1
                elif (not above) and np.isfinite(sl[i]) and cl[i] < sl[i] and gd[i]:
                    d_ = -1
                if d_ == 0:
                    continue
                taken = True
                fwd = np.flatnonzero((hm > hm[i]) & (hm < whi))
                if len(fwd) < 5 or not np.isfinite(dl[fwd[:5]]).all():
                    continue
                e, sd = cl[i], next(s for a, s in F.TIERS if atr[i] > a)
                adv = np.maximum.accumulate((e - lo[fwd]) if d_ == 1 else (hi[fwd] - e))
                fav = np.maximum.accumulate((hi[fwd] - e) if d_ == 1 else (e - lo[fwd]))
                mtm = (cl[fwd] - e) * d_
                cd = np.nancumsum(dl[fwd] * d_)          # signed cumulative delta
                cv = np.nancumsum(np.nan_to_num(vl[fwd]))
                pre = np.nanmean(vl[max(0, i - 30):i]) if i > 5 else np.nan
                ts = int(np.argmax(adv >= sd)) if (adv >= sd).any() else 10**9
                tt = int(np.argmax(fav >= tgt_i(sd)) ) if (fav >= tgt_i(sd)).any() else 10**9
                R = ((-sd if ts <= tt else tgt_i(sd)) - FRIC) / sd if min(ts, tt) < 10**9 \
                    else (mtm[-1] - FRIC) / sd
                out.append({"day": day, "yr": day[:4], "dir": d_, "stop": sd, "R": R,
                            "mtm": mtm, "cd": cd, "cv": cv, "pre_vol": pre,
                            "exit_i": min(ts, tt)})
    return out


def tgt_i(sd):
    return sd * RR


def main() -> int:
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    b = F.load()
    b = b[b.day >= "2025-06-01"]
    P = build(b, fp)
    R = np.array([p["R"] for p in P])
    win = R > 0
    print(f"{len(P):,} trades with flow paths | win {win.mean():.1%} avgR {R.mean():+.3f} "
          f"avgWin {R[win].mean():+.3f} avgLoss {R[~win].mean():+.3f} "
          f"PF {R[win].sum()/abs(R[~win].sum()):.2f}", flush=True)

    L = ["# Intra-trade ORDER FLOW — can a loser be spotted before price shows it?", "",
         "The price path failed (28 rules, none beat base) because a third of eventual winners",
         "are underwater at any minute. This tests the **flow** path, and the cases where price",
         "and flow disagree — which a mark-to-market rule cannot see.", "",
         f"**{len(P):,} trades** (flow data starts 2025-06). Base: win {win.mean():.1%}, "
         f"avg R {R.mean():+.3f}, PF {R[win].sum()/abs(R[~win].sum()):.2f}", "",
         "## Do winners and losers differ on FLOW — and does it separate?", "",
         "| min | metric | winners | losers | gap | **overlap** |",
         "|---:|---|---:|---:|---:|---:|"]

    def at(p, k, key):
        a = p[key]
        return a[k] if k < len(a) else np.nan

    for m in MARKS:
        k = m - 1
        for key, nm, norm in [("cd", "cum delta / cum vol", True),
                              ("mtm", "price MTM (R)", False)]:
            wv, lv = [], []
            for p, isw in zip(P, win):
                v = at(p, k, key)
                if not np.isfinite(v):
                    continue
                if norm:
                    cv = at(p, k, "cv")
                    v = v / cv if np.isfinite(cv) and cv > 0 else np.nan
                else:
                    v = v / p["stop"]
                if np.isfinite(v):
                    (wv if isw else lv).append(v)
            if len(wv) < 80 or len(lv) < 80:
                continue
            wv, lv = np.array(wv), np.array(lv)
            thr = np.median(np.concatenate([wv, lv]))
            # overlap = share of winners on the WRONG side of the best simple split
            ov = (wv < thr).mean() if np.mean(wv) > np.mean(lv) else (wv > thr).mean()
            L.append(f"| {m} | {nm} | {wv.mean():+.4f} | {lv.mean():+.4f} | "
                     f"{wv.mean()-lv.mean():+.4f} | **{ov:.0%}** |")

    L += ["", "## Divergence quadrants — price vs flow at minute 10", "",
          "| quadrant | n | win% | avg R | avg win | avg loss | PF |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    k = 9
    rows = {}
    for p, r in zip(P, R):
        mt, cd, cv = at(p, k, "mtm"), at(p, k, "cd"), at(p, k, "cv")
        if not (np.isfinite(mt) and np.isfinite(cd) and np.isfinite(cv) and cv > 0):
            continue
        if p["exit_i"] <= k:
            continue                      # already resolved, no decision to make
        q = ("price+ flow+" if mt > 0 and cd > 0 else "price+ flow-" if mt > 0 else
             "price- flow+" if cd > 0 else "price- flow-")
        rows.setdefault(q, []).append(r)
    for q, v in sorted(rows.items()):
        v = np.array(v)
        if len(v) < 40:
            continue
        w = v > 0
        pf = v[w].sum() / abs(v[~w].sum()) if (~w).any() else np.nan
        L.append(f"| {q} | {len(v):,} | {w.mean():.1%} | **{v.mean():+.3f}** | "
                 f"{v[w].mean() if w.any() else np.nan:+.3f} | "
                 f"{v[~w].mean() if (~w).any() else np.nan:+.3f} | {pf:.2f} |")

    L += ["", "## Flow-based exit sweep — cut if signed delta is against you at minute N", "",
          "| min | delta threshold | n cut | win% | avg R | avg loss | PF | vs base |",
          "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    base = R.mean()
    for m in MARKS:
        k = m - 1
        for thr in (0.0, -0.05, -0.10):
            out = []
            for p, r in zip(P, R):
                cd, cv, mt = at(p, k, "cd"), at(p, k, "cv"), at(p, k, "mtm")
                if (p["exit_i"] > k and np.isfinite(cd) and np.isfinite(cv) and cv > 0
                        and cd / cv < thr):
                    out.append((mt - FRIC) / p["stop"] if np.isfinite(mt) else r)
                else:
                    out.append(r)
            o = np.array(out)
            w = o > 0
            ncut = sum(1 for p, a, c in zip(P, out, R) if a != c)
            L.append(f"| {m} | {thr:+.2f} | {ncut:,} | {w.mean():.1%} | **{o.mean():+.3f}** | "
                     f"{o[~w].mean():+.3f} | {o[w].sum()/abs(o[~w].sum()):.2f} | "
                     f"{o.mean()-base:+.3f} |")

    text = "\n".join(L)
    print(text)
    (ROOT / "output/fvt_flowpath.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
