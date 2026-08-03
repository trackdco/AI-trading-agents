#!/usr/bin/env python3
"""Score the Currency-Pros strategy test. Parameters were frozen before the run; nothing here
changes them. The decisive test is the win rate against the breakeven the geometry forces.
"""
import json
import os

import numpy as np
import pandas as pd
from scipy import stats

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/thirdparty"
T = pd.read_csv(f"{OUT}/cp_trades_all.csv")
T["won"] = T.R > 0
rng = np.random.default_rng(20260803)
R = {}


def be(fib):
    return 1.0 - fib                      # breakeven WR for a fib/(1-fib) payoff


def dayboot(df, fn, nb=4000):
    days = df.day.unique()
    idx = {d: df.index[df.day == d].to_numpy() for d in days}
    out = []
    for _ in range(nb):
        pick = rng.choice(days, size=len(days), replace=True)
        ix = np.concatenate([idx[d] for d in pick])
        v = fn(df.loc[ix])
        if np.isfinite(v):
            out.append(v)
    o = np.array(out)
    return float(np.percentile(o, 2.5)), float(np.percentile(o, 97.5))


WIN = {"NY RTH 09:30-16:00": lambda d: (d.hm >= 570) & (d.hm < 960),
       "NY 08:00-16:00": lambda d: (d.hm >= 480) & (d.hm < 960),
       "all hours": lambda d: pd.Series(True, index=d.index)}

print("=" * 106)
print("THE DECISIVE TEST — win rate vs the breakeven the geometry forces")
print("=" * 106)
print("Stop and target are the range extremes and entry is a fib of that range, so payoff is")
print("FIXED at fib/(1-fib) and breakeven win rate is exactly (1-fib).")
print("  fib 0.75 -> payoff 3.00R -> breakeven 25.0%   |   fib 0.71 -> 2.45R -> breakeven 29.0%\n")
print(f"{'window':22s} {'fib':>5} {'score':>7} {'n':>6} {'WR':>7} {'b/e':>7} {'edge pp':>9} "
      f"{'mean R':>8} {'total R':>10} {'binom p':>9}")
res = []
for wname, wf in WIN.items():
    for fib in (0.75, 0.71):
        for slab in (">=3", "4 only"):
            m = (T.score >= 3) if slab == ">=3" else (T.score == 4)
            d = T[wf(T) & (T.fib == fib) & m]
            if len(d) < 10:
                print(f"{wname:22s} {fib:>5.2f} {slab:>7} {len(d):>6}   INSUFFICIENT")
                continue
            wr, b = d.won.mean(), be(fib)
            p = stats.binomtest(int(d.won.sum()), len(d), b, alternative="greater").pvalue
            res.append(dict(window=wname, fib=fib, score=slab, n=len(d), wr=float(wr), be=b,
                            edge_pp=float((wr - b) * 100), meanR=float(d.R.mean()),
                            totalR=float(d.R.sum()), binom_p=float(p)))
            print(f"{wname:22s} {fib:>5.2f} {slab:>7} {len(d):>6} {wr*100:>6.1f}% {b*100:>6.1f}% "
                  f"{(wr-b)*100:>+9.1f} {d.R.mean():>+8.3f} {d.R.sum():>+10.1f} {p:>9.4f}")
R["headline"] = res

print("\n" + "=" * 106)
print("PRIMARY CELL — NY RTH, fib 0.75, score >=3 (what the video demonstrates)")
print("=" * 106)
P = T[(T.hm >= 570) & (T.hm < 960) & (T.fib == 0.75) & (T.score >= 3)].reset_index(drop=True)
wr = P.won.mean()
lo, hi = dayboot(P, lambda d: d.won.mean())
mlo, mhi = dayboot(P, lambda d: d.R.mean())
print(f"  n = {len(P)} trades over {P.day.nunique()} days, {P.day.min()} .. {P.day.max()}")
print(f"  win rate {wr*100:.1f}%   day-clustered 95% CI [{lo*100:.1f}%, {hi*100:.1f}%]"
      f"   breakeven 25.0%")
print(f"  mean R {P.R.mean():+.3f}   CI [{mlo:+.3f}, {mhi:+.3f}]   total {P.R.sum():+.1f}R")
print(f"  -> {'ABOVE' if lo > 0.25 else 'NOT above'} breakeven at the 95% level")
R["primary"] = dict(n=len(P), days=int(P.day.nunique()), wr=float(wr), ci=[lo, hi],
                    meanR=float(P.R.mean()), meanR_ci=[mlo, mhi], totalR=float(P.R.sum()),
                    beats_be=bool(lo > 0.25))

print("\nSCORE CALIBRATION — does stacking confluences do anything? (NY RTH, fib 0.75)")
A = T[(T.hm >= 570) & (T.hm < 960) & (T.fib == 0.75)]
print(f"  {'score':>6} {'n':>6} {'WR':>7} {'mean R':>8} {'total R':>10}")
cal = {}
for s in sorted(A.score.unique()):
    d = A[A.score == s]
    cal[int(s)] = dict(n=len(d), wr=float(d.won.mean()), meanR=float(d.R.mean()))
    print(f"  {int(s):>6} {len(d):>6} {d.won.mean()*100:>6.1f}% {d.R.mean():>+8.3f} "
          f"{d.R.sum():>+10.1f}" + ("" if len(d) >= 10 else "   INSUFFICIENT"))
if cal.get(4, {}).get("n", 0) >= 10 and cal.get(3, {}).get("n", 0) >= 10:
    d4, d3 = A[A.score == 4], A[A.score == 3]
    ct = stats.fisher_exact([[int(d4.won.sum()), len(d4) - int(d4.won.sum())],
                             [int(d3.won.sum()), len(d3) - int(d3.won.sum())]])
    print(f"  4/4 vs 3/4: {cal[4]['wr']*100:.1f}% vs {cal[3]['wr']*100:.1f}%  "
          f"Fisher exact p = {ct.pvalue:.3f}")
    R["calibration_p"] = float(ct.pvalue)
R["calibration"] = cal

print("\nBY YEAR (NY RTH, fib 0.75, score >=3) — is it stable?")
P["yr"] = P.day.str[:4]
print(f"  {'year':>6} {'n':>6} {'WR':>7} {'mean R':>8} {'total R':>10}")
yr = {}
for y, d in P.groupby("yr"):
    yr[y] = dict(n=len(d), wr=float(d.won.mean()), meanR=float(d.R.mean()))
    print(f"  {y:>6} {len(d):>6} {d.won.mean()*100:>6.1f}% {d.R.mean():>+8.3f} {d.R.sum():>+10.1f}")
R["by_year"] = yr

print("\nHIS CLAIM — 'sessions and timing do not matter' (fib 0.75, score >=3)")
for wname, wf in WIN.items():
    d = T[wf(T) & (T.fib == 0.75) & (T.score >= 3)]
    print(f"  {wname:22s} n={len(d):>6}  WR {d.won.mean()*100:>5.1f}%  meanR {d.R.mean():>+.3f}")

print("\nCOSTS")
med = P.span.median()
risk_pts = med * 0.25
cost_R = 1.74 / max(risk_pts * 2, 1e-9)
print(f"  median leg span {med:.1f} pts -> risk = 25% of span = {risk_pts:.1f} pts "
      f"= ${risk_pts*2:.2f}/micro")
print(f"  $1.24 commission + $0.50 slippage = $1.74 = {cost_R*100:.2f}% of 1R")
print(f"  mean R after costs: {P.R.mean()-cost_R:+.3f}")
R["cost_R"] = float(cost_R)
R["meanR_after_costs"] = float(P.R.mean() - cost_R)
json.dump(R, open(f"{OUT}/cp_results.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/cp_results.json")
