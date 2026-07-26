#!/usr/bin/env python3
"""IS IT NO EDGE, OR A REGIME-DEPENDENT EDGE? — the question the holdout alone cannot answer.

The book earns +38.15R in-sample (2025-07 -> 2026-07) and loses -27.49R on the 2023-01 -> 2025-06
holdout. Two very different readings of that:

  (a) NO EDGE. The in-sample window is luck; the setup is a coin flip with costs.
  (b) REGIME-DEPENDENT EDGE. A trend-pullback with a fixed 3R target needs volatility and clean
      trends. 2024 was a low-volatility grind; 2025H2-2026H1 was not. Same setup, different world.

These demand opposite decisions: (a) means stop, (b) means trade it with a regime switch. An
in-sample-only ATR gate cannot distinguish them, because in-sample is ALL good regime -- which is
exactly why the earlier "skip ATR < 30" test lost money and told us nothing about this question.

So this splits the FULL 2023-2026 span by volatility regime and asks: is the book profitable in
high-volatility conditions IN EVERY PERIOD, or only in the window it was built on?

The regime variable is causal: ATR14 on the M15 frame at the signal bar, and its percentile
against a TRAILING 250-session baseline (so no forward information). Both an absolute-ATR and a
percentile-of-trailing view are reported, because absolute ATR drifts with the index level --
NQ at 12,000 and NQ at 26,000 have very different point ranges for the same relative volatility.

    LONDON_SCRATCH=<dir> LONDON_WT=<worktree> python3 scripts/london_regime_test.py
"""
import os
from datetime import time as dtime

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
WT = os.environ.get("LONDON_WT", f"{S}/canon_wt")
TICK, PV, COMM = 0.25, 20.0, 5.0
IS_START = "2025-07-01"
SKIP = {"2025-11-28", "2026-04-03"}

print("load bars ...", flush=True)
b = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
b["ts"] = pd.to_datetime(b.ts_event, utc=True)
b = b.sort_values("ts").reset_index(drop=True)
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
m["tr"] = np.maximum(m.high - m.low, np.maximum((m.high - m.close.shift(1)).abs(),
                                                (m.low - m.close.shift(1)).abs()))
m["atr14"] = m.tr.rolling(14).mean()
m["atr_rel"] = m.atr14 / m.close                     # scale-free: ATR as a fraction of price
M = m.reset_index(names="uts").dropna(subset=["ma200", "atr14"]).reset_index(drop=True)

# trailing percentile of atr_rel against the prior 250 sessions' daily mean -- strictly causal
dmean = M.groupby("ukday").atr_rel.mean()
trail = dmean.shift(1).rolling(250, min_periods=60)
pct = pd.Series(index=dmean.index, dtype=float)
vals = dmean.values
for k in range(len(dmean)):
    lo = max(0, k - 250)
    if k - lo < 60:
        continue
    win = vals[lo:k]
    pct.iloc[k] = (win < vals[k]).mean()
PCT = pct.to_dict()

a = {c: M[c].values for c in ["open", "high", "low", "close", "volume", "ma20", "ma50",
                              "ma200", "v10", "slo", "shi", "atr14", "atr_rel"]}
ud, utt = M.ukday.values, M.ukt.values

rows = []
for i in range(1, len(M) - 1):
    d = ud[i]
    if d in SKIP or ud[i + 1] != d or not (dtime(10, 0) <= utt[i] < dtime(13, 0)):
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
    gg, j = None, i + 1
    while j < len(M) and ud[j] == d:
        if utt[j] >= dtime(16, 30):
            gg = dr * (a["close"][j] - en); break
        hs = (a["low"][j] <= st) if dr > 0 else (a["high"][j] >= st)
        ht = (a["high"][j] >= tg) if dr > 0 else (a["low"][j] <= tg)
        if hs:
            gg = -rk - TICK; break
        if ht:
            gg = 3 * rk - TICK; break
        j += 1
    if gg is None:
        j = min(j, len(M) - 1); gg = dr * (a["close"][j] - en)
    net = gg * PV - COMM
    rows.append(dict(day=d, sig=i, res=j, net=net, R=net / (rk * PV), rk=rk,
                     atr=a["atr14"][i], atrrel=a["atr_rel"][i], pct=PCT.get(d, np.nan),
                     oos=int(d < IS_START)))

SIG = pd.DataFrame(rows).sort_values(["day", "sig"]).reset_index(drop=True)


def book_c(D):
    keep = []
    for d, g in D.groupby("day"):
        taken = []
        for _, r in g.iterrows():
            if any(res <= r.sig and nt < 0 for res, nt in taken):
                continue
            if any(res > r.sig for res, _ in taken):
                continue
            keep.append(r.name)
            taken.append((r.res, r.net))
    return D.loc[keep].copy()


C = book_c(SIG)
C["yr"] = C.day.str[:4]
C["h"] = C.day.str[:4] + np.where(C.day.str[5:7].astype(int) <= 6, "H1", "H2")


def show(D, lab):
    if len(D) < 3:
        print(f"  {lab:<34} {len(D):>4} trades   (too few)"); return
    print(f"  {lab:<34} {len(D):>4} trades  WR {(D.R>0).mean()*100:>3.0f}%  "
          f"netR {D.R.sum():>+8.2f}  avgR {D.R.mean():>+6.2f}  ${D.R.sum()*300:>+9,.0f}")


if __name__ == "__main__":
    print(f"\nbook C over the full span: {len(C)} trades  netR {C.R.sum():+.2f}\n")

    print("=" * 96)
    print("THE QUESTION: is the book profitable in HIGH-VOL conditions in EVERY period,")
    print("or only in the window it was built on?")
    print("=" * 96)

    for nm, col, cuts in (("trailing ATR percentile", "pct", [(0, .33), (.33, .67), (.67, 1.01)]),
                          ("ATR / price (scale-free)", "atrrel",
                           [(0, .0009), (.0009, .0013), (.0013, 9)])):
        print(f"\n--- split by {nm} ---")
        for lo, hi in cuts:
            g = C[(C[col] >= lo) & (C[col] < hi)]
            show(g, f"  {lo:g} - {hi:g}")

    print("\n" + "=" * 96)
    print("HIGH-VOL ONLY (top trailing-percentile tercile), BY PERIOD — the decisive table")
    print("=" * 96)
    HI = C[C.pct >= 0.67]
    print(f"  high-vol subset: {len(HI)} trades  netR {HI.R.sum():+.2f}  "
          f"WR {(HI.R>0).mean()*100:.0f}%")
    print(f"\n  {'half':<8} {'n':>4} {'WR':>5} {'netR':>9} {'avgR':>7}   |  "
          f"{'ALL-VOL n':>9} {'netR':>9}")
    for h in sorted(set(C.h)):
        g, ga = HI[HI.h == h], C[C.h == h]
        if len(g):
            print(f"  {h:<8} {len(g):>4} {(g.R>0).mean()*100:>4.0f}% {g.R.sum():>+9.2f} "
                  f"{g.R.mean():>+7.2f}   |  {len(ga):>9} {ga.R.sum():>+9.2f}")
        else:
            print(f"  {h:<8} {0:>4}     -         -       -   |  {len(ga):>9} {ga.R.sum():>+9.2f}")

    print("\n  holdout-only, high vol:")
    show(HI[HI.oos == 1], "    2023-01 -> 2025-06")
    show(HI[HI.oos == 0], "    2025-07 -> 2026-07 (in-sample)")

    print("\n" + "=" * 96)
    print("VERDICT TEST: does the high-vol gate make the HOLDOUT non-negative?")
    print("=" * 96)
    O = C[C.oos == 1]
    for lab, sub in (("all trades", O), ("pct >= 0.50", O[O.pct >= 0.50]),
                     ("pct >= 0.67", O[O.pct >= 0.67]), ("pct >= 0.80", O[O.pct >= 0.80])):
        show(sub, lab)
    print("\n  If the top rows are negative, volatility regime does NOT explain the failure and")
    print("  reading (a) -- no durable edge -- is the one the data supports.")
