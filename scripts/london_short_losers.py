#!/usr/bin/env python3
"""WHAT DO THE FAST LOSERS LOOK LIKE? -- anatomy of the sub-1-hour trades in the
London 10-13 UK book.

Hold-time analysis showed everything resolving in under an hour is flat-to-negative
(<=15m -1.05R, 16-30m -0.03R, 31-60m -0.22R) while >2h runs +2.10R. Hold time is only
known AFTER the fact, so it cannot be traded. The only useful question is whether
anything KNOWN AT ENTRY separates the fast losers from the slow winners.

This script rebuilds the book (trade logic byte-identical to london_conviction.py),
attaches every entry-time feature we can legitimately see before the trade is placed,
and profiles fast (<=60m) vs slow (>60m) resolutions.

ANTI-TUNING NOTE: this is DIAGNOSIS, not a filter search. 55 trades cannot support a
multi-feature screen; anything that looks separating here needs the 2023-24 holdout
before it is allowed near the plan. The tail law also applies -- every previous
intervention that cut trades lost money.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_short_losers.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
TICK, PV, COMM = 0.25, 20.0, 5.0

print("load bars ...", flush=True)
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
m["dow"] = _uk.dayofweek
for p in (20, 50, 200):
    m[f"ma{p}"] = m.close.rolling(p).mean()
m["v10"] = m.volume.rolling(10).mean().shift(1)
m["slo"] = m.low.rolling(5).min()
m["shi"] = m.high.rolling(5).max()
m["tr"] = np.maximum(m.high - m.low,
                     np.maximum((m.high - m.close.shift(1)).abs(),
                                (m.low - m.close.shift(1)).abs()))
m["atr14"] = m.tr.rolling(14).mean().shift(1)          # shift -> known before bar i closes? see note
M = m.reset_index(names="uts").dropna(subset=["ma200"])
M = M[(M.ukday >= "2025-07-01") & (M.ukday <= "2026-07-15")].reset_index(drop=True)
a = {c: M[c].values for c in ["uts", "open", "high", "low", "close", "volume", "ma20",
                              "ma50", "ma200", "v10", "slo", "shi", "atr14", "tr", "dow"]}
ud, utt = M.ukday.values, M.ukt.values


def build(skip=None):
    """skip(feat_dict) -> True to reject the signal. Applied BEFORE the day-stop, so the
    day-stop re-runs on the surviving set (a post-hoc row deletion would be wrong: removing
    a loser un-blocks the trades that loser's day-stop cancelled)."""
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
        rng0 = a["high"][i] - a["low"][i]
        atr0 = max(a["atr14"][i], 1e-9)
        if skip is not None and skip(dict(
                rk=rk, dr=dr, rk_atr=rk / atr0, atr=a["atr14"][i],
                volrat=a["volume"][i] / a["v10"][i], barrng=rng0 / atr0,
                stack=abs(a["ma20"][i] - a["ma200"][i]) / atr0, hour=int(str(utt[i])[:2]))):
            continue
        st, tg = en - dr * rk, en + dr * 3 * rk
        gg, j, how = None, i + 1, None
        mae = 0.0                                    # heat, in R, before resolution
        while j < len(M) and ud[j] == d:
            adv = dr * (a["low"][j] - en) if dr > 0 else dr * (a["high"][j] - en)
            mae = max(mae, -min(0.0, adv) / rk)
            if utt[j] >= dtime(16, 30):
                gg = dr * (a["close"][j] - en); how = "time"; break
            hs = (a["low"][j] <= st) if dr > 0 else (a["high"][j] >= st)
            ht = (a["high"][j] >= tg) if dr > 0 else (a["low"][j] <= tg)
            if hs:
                gg = -rk - TICK; how = "stop"; break
            if ht:
                gg = 3 * rk - TICK; how = "target"; break
            j += 1
        if gg is None:
            gg = dr * (a["close"][min(j, len(M) - 1)] - en); how = "dayend"
        # ---- features KNOWN AT ENTRY (signal bar i, or earlier) ----
        rng = a["high"][i] - a["low"][i]
        rows.append(dict(
            day=d, ent=str(utt[i]), dr=dr, rk=rk, gg=gg, how=how, mins=(j - i) * 15, mae=mae,
            hour=int(str(utt[i])[:2]),
            dow=int(a["dow"][i]),
            volrat=a["volume"][i] / a["v10"][i],                       # how faded (lower = quieter)
            stack=abs(a["ma20"][i] - a["ma200"][i]) / max(a["atr14"][i], 1e-9),   # trend separation in ATRs
            ma50dist=abs(a["close"][i] - a["ma50"][i]) / max(a["atr14"][i], 1e-9),  # close back through 50MA, in ATRs
            wickfrac=(min(a["close"][i], a["open"][i]) - a["low"][i]) / max(rng, 1e-9) if dr > 0
                     else (a["high"][i] - max(a["close"][i], a["open"][i])) / max(rng, 1e-9),
            barrng=rng / max(a["atr14"][i], 1e-9),                     # signal-bar range in ATRs
            atr=a["atr14"][i],
            rk_atr=rk / max(a["atr14"][i], 1e-9),                      # stop width in ATRs
        ))
    A = pd.DataFrame(rows).sort_values(["day", "ent"]).reset_index(drop=True)
    A["net"] = A.gg * PV - COMM
    A["R"] = A.net / (A.rk * PV)
    keep = []
    for d, g in A.groupby("day"):
        stp = False
        for _, r in g.iterrows():
            if stp:
                continue
            keep.append(r.name)
            if r.net < 0:
                stp = True
    return A.loc[keep].copy().reset_index(drop=True)


def band(D, col, edges, labels):
    out = []
    for lab, (lo, hi) in zip(labels, edges):
        g = D[(D[col] >= lo) & (D[col] < hi)]
        if len(g):
            out.append((lab, len(g), g.R.mean(), g.mins.mean(), (g.R > 0).mean() * 100))
    return out


if __name__ == "__main__":
    D = build()
    D["fast"] = D.mins <= 60
    print(f"\nbook: {len(D)} trades | {(D.R>0).sum()}W/{(D.R<=0).sum()}L | net {D.R.sum():+.2f}R")

    F, Sl = D[D.fast], D[~D.fast]
    print(f"\n=== FAST (<=60m) vs SLOW (>60m) ===")
    print(f"  fast  n={len(F):>2}  netR {F.R.sum():>+7.2f}  avgR {F.R.mean():>+6.2f}  WR {(F.R>0).mean()*100:>3.0f}%  "
          f"exits {dict(F.how.value_counts())}")
    print(f"  slow  n={len(Sl):>2}  netR {Sl.R.sum():>+7.2f}  avgR {Sl.R.mean():>+6.2f}  WR {(Sl.R>0).mean()*100:>3.0f}%  "
          f"exits {dict(Sl.how.value_counts())}")

    print("\n=== ENTRY-TIME FEATURES: fast vs slow (mean, and Welch-ish separation) ===")
    print(f"{'feature':<10} {'fast':>8} {'slow':>8} {'gap':>8} {'sep':>6}")
    print("-" * 44)
    for c in ["rk", "rk_atr", "volrat", "stack", "ma50dist", "wickfrac", "barrng", "atr", "hour"]:
        f_, s_ = F[c], Sl[c]
        pooled = np.sqrt(f_.var(ddof=1) / len(f_) + s_.var(ddof=1) / len(s_)) if len(f_) > 1 and len(s_) > 1 else np.nan
        sep = (f_.mean() - s_.mean()) / pooled if pooled and np.isfinite(pooled) and pooled > 0 else np.nan
        print(f"{c:<10} {f_.mean():>8.2f} {s_.mean():>8.2f} {f_.mean()-s_.mean():>+8.2f} {sep:>6.2f}")
    print("  sep = difference in standard errors. |sep| < 2 is not a signal at n=55.")

    print("\n=== SLICES (n, avgR, meanHold, WR) ===")
    slices = {
        "entry hour": band(D, "hour", [(10, 11), (11, 12), (12, 13)], ["10:00-10:59", "11:00-11:59", "12:00-12:59"]),
        "stop size (pt)": band(D, "rk", [(0, 20), (20, 35), (35, 50), (50, 999)], ["<20", "20-35", "35-50", ">=50"]),
        "stop / ATR": band(D, "rk_atr", [(0, 1.0), (1.0, 1.5), (1.5, 2.5), (2.5, 99)], ["<1.0", "1.0-1.5", "1.5-2.5", ">=2.5"]),
        "vol / v10": band(D, "volrat", [(0, .55), (.55, .75), (.75, .9), (.9, 1.0)], ["<0.55", "0.55-0.75", "0.75-0.90", "0.90-1.00"]),
        "trend sep (ATR)": band(D, "stack", [(0, 2), (2, 4), (4, 99)], ["<2", "2-4", ">=4"]),
        "signal bar rng": band(D, "barrng", [(0, 1.0), (1.0, 1.6), (1.6, 99)], ["<1.0", "1.0-1.6", ">=1.6"]),
        "day of week": band(D, "dow", [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)], ["Mon", "Tue", "Wed", "Thu", "Fri"]),
    }
    for name, rowsx in slices.items():
        print(f"\n  {name}")
        for lab, n, ar, mh, wr in rowsx:
            print(f"    {lab:<12} n={n:>2}  avgR {ar:>+6.2f}  hold {mh:>4.0f}m  WR {wr:>3.0f}%")

    print("\n=== DIRECTION ===")
    for dr, g in D.groupby("dr"):
        print(f"  {'long ' if dr>0 else 'short'} n={len(g):>2}  avgR {g.R.mean():>+6.2f}  "
              f"hold {g.mins.mean():>4.0f}m  WR {(g.R>0).mean()*100:>3.0f}%  fast {int((g.mins<=60).sum())}/{len(g)}")

    print("\n=== THE FAST LOSERS, ONE BY ONE ===")
    FL = D[(D.mins <= 60) & (D.R <= 0)].sort_values("mins")
    print(f"{'day':<11} {'entry':<9} {'dir':>4} {'mins':>5} {'R':>6} {'stop':>6} {'rk/ATR':>7} {'vol/v10':>8} {'MAE R':>6}")
    for _, r in FL.iterrows():
        print(f"{r.day:<11} {r.ent:<9} {'long' if r.dr>0 else 'short':>4} {int(r.mins):>5} {r.R:>+6.2f} "
              f"{r.rk:>6.1f} {r.rk_atr:>7.2f} {r.volrat:>8.2f} {r.mae:>6.2f}")

    print("\n=== HEAT: does a fast trade show its hand early? ===")
    print("  MAE = worst adverse excursion in R before resolution.")
    for lab, g in [("fast winners", D[(D.mins <= 60) & (D.R > 0)]), ("fast losers", FL),
                   ("slow winners", D[(D.mins > 60) & (D.R > 0)]), ("slow losers", D[(D.mins > 60) & (D.R <= 0)])]:
        if len(g):
            print(f"    {lab:<14} n={len(g):>2}  meanMAE {g.mae.mean():>5.2f}R  medMAE {g.mae.median():>5.2f}R")

    print("\n=== IF YOU ACTUALLY FILTERED ON IT (day-stop re-run, not post-hoc deletion) ===")
    base = D.R.sum()
    FILTERS = [
        ("skip stop < 20pt",          lambda f: f["rk"] < 20),
        ("skip stop < 25pt",          lambda f: f["rk"] < 25),
        ("skip stop < 1.0 ATR",       lambda f: f["rk_atr"] < 1.0),
        ("skip ATR < 25 (quiet day)", lambda f: f["atr"] < 25),
        ("skip ATR < 30",             lambda f: f["atr"] < 30),
        ("skip vol/v10 > 0.90",       lambda f: f["volrat"] > 0.90),
        ("skip trend sep < 2 ATR",    lambda f: f["stack"] < 2),
        ("skip signal bar >= 1.0 ATR", lambda f: f["barrng"] >= 1.0),
        ("skip the 10:00 hour",       lambda f: f["hour"] == 10),
        ("shorts only",               lambda f: f["dr"] > 0),
        ("skip stop<25 AND sep<2",    lambda f: f["rk"] < 25 or f["stack"] < 2),
    ]
    print(f"{'filter':<26} {'n':>3} {'netR':>8} {'vs base':>8} {'avgR':>6} {'WR':>5} {'hold':>6}")
    print("-" * 68)
    print(f"{'(none - the book)':<26} {len(D):>3} {base:>+8.2f} {0.0:>+8.2f} {D.R.mean():>+6.2f} "
          f"{(D.R>0).mean()*100:>4.0f}% {D.mins.mean():>5.0f}m")
    for name, fn in FILTERS:
        Z = build(skip=fn)
        if not len(Z):
            print(f"{name:<26}   0   (no trades)")
            continue
        print(f"{name:<26} {len(Z):>3} {Z.R.sum():>+8.2f} {Z.R.sum()-base:>+8.2f} {Z.R.mean():>+6.2f} "
              f"{(Z.R>0).mean()*100:>4.0f}% {Z.mins.mean():>5.0f}m")
    print("  avgR/WR can RISE while netR FALLS -- that is the tail law. Only the netR column pays.")

    print("\nDIAGNOSIS ONLY. n=55. Nothing here is a filter until it survives 2023-24 out-of-sample.")
