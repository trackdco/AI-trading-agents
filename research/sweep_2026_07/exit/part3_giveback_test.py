#!/usr/bin/env python3
"""EXIT-TIMING STUDY — PART 3: the give-back gap, scored against its pre-registration.

Registration: research/sweep_2026_07/exit/PART3_PREREG.md, committed BEFORE this ran.
  PRIMARY   conditional give-back  P(finished red | reached +1R), by segment
  STATISTIC early-minus-late difference in that rate
  NOISE     day-block permutation of the OUTCOME labels, 2,000 draws (segment membership is a
            fixed property of fill time and is never permuted)
  RULE      p < 0.05 AND a day-clustered CI excluding zero, else INCONCLUSIVE
"""
import json
import os

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/exit"
NPERM, NBOOT, MIN_CELL = 2000, 4000, 10
rng = np.random.default_rng(20260729)

F = pd.read_csv(f"{OUT}/part1_frame.csv")
assert len(F) == 182 and abs(F.pl.sum() - 21097.875) < 1e-6
F["reached1R"] = F.mfe_life >= 1.0
F["gave_back"] = F.reached1R & (F.pl < 0)
SEGS = ("early 08:00-08:29", "mid 08:30-08:59", "late 09:00-09:29")
days = F.day.values
u_days = pd.unique(days)
day_idx = {d: np.flatnonzero(days == d) for d in u_days}
print(f"{len(F)} trades | {int(F.reached1R.sum())} reached +1R | "
      f"{int(F.gave_back.sum())} gave back")

def cond_rate(idx, seg):
    m = (F.seg.values[idx] == seg) & F.reached1R.values[idx]
    if m.sum() == 0:
        return np.nan
    return float(F.gave_back.values[idx][m].mean())

def uncond_rate(idx, seg):
    m = F.seg.values[idx] == seg
    if m.sum() == 0:
        return np.nan
    return float(F.gave_back.values[idx][m].mean())

ALL = np.arange(len(F))
print("\n" + "=" * 100)
print("OBSERVED RATES BY SEGMENT")
print("=" * 100)
print(f"{'segment':22s} {'n':>4} {'n reached 1R':>13} {'CONDITIONAL':>12} {'unconditional':>14}")
obs = {}
for s in SEGS:
    g = F[F.seg == s]
    nr = int(g.reached1R.sum())
    c, u = cond_rate(ALL, s), uncond_rate(ALL, s)
    ins = nr < MIN_CELL
    obs[s] = dict(n=len(g), n_reached=nr, cond=c, uncond=u, insufficient=bool(ins))
    print(f"{s:22s} {len(g):>4} {nr:>13} {c*100:>11.1f}% {u*100:>13.1f}%"
          + ("   INSUFFICIENT" if ins else ""))
stat_obs = obs[SEGS[0]]["cond"] - obs[SEGS[2]]["cond"]
rates = [obs[s]["cond"] for s in SEGS]
maxmin_obs = float(np.nanmax(rates) - np.nanmin(rates))
print(f"\n  PRIMARY statistic  early - late (conditional) = "
      f"{stat_obs*100:+.1f} percentage points")
print(f"  SECONDARY          max - min across segments   = {maxmin_obs*100:+.1f} pp")

# ---------------------------------------------------------------- noise floor
print("\n" + "=" * 100)
print(f"NOISE FLOOR — day-block permutation of outcome labels, {NPERM} draws")
print("=" * 100)
gb = F.gave_back.values.copy()
r1 = F.reached1R.values.copy()
blocks = [np.flatnonzero(days == d) for d in u_days]
null_stat, null_mm = [], []
for _ in range(NPERM):
    order = rng.permutation(len(blocks))
    perm_idx = np.concatenate([blocks[k] for k in order])
    g2 = np.empty_like(gb)
    r2 = np.empty_like(r1)
    g2[np.concatenate(blocks)] = gb[perm_idx]
    r2[np.concatenate(blocks)] = r1[perm_idx]
    def cr(seg):
        m = (F.seg.values == seg) & r2
        return float(g2[m].mean()) if m.sum() else np.nan
    a, b, c = cr(SEGS[0]), cr(SEGS[1]), cr(SEGS[2])
    if np.isfinite(a) and np.isfinite(c):
        null_stat.append(a - c)
    vals = [v for v in (a, b, c) if np.isfinite(v)]
    if len(vals) == 3:
        null_mm.append(max(vals) - min(vals))
null_stat, null_mm = np.array(null_stat), np.array(null_mm)
p_primary = float(((np.abs(null_stat) >= abs(stat_obs)).sum() + 1) / (len(null_stat) + 1))
p_second = float(((null_mm >= maxmin_obs).sum() + 1) / (len(null_mm) + 1))
print(f"  primary   |early-late|: observed {abs(stat_obs)*100:.1f}pp   null p50 "
      f"{np.median(np.abs(null_stat))*100:.1f}pp  p95 {np.percentile(np.abs(null_stat),95)*100:.1f}pp"
      f"   -> p = {p_primary:.4f}")
print(f"  secondary  max-min    : observed {maxmin_obs*100:.1f}pp   null p50 "
      f"{np.median(null_mm)*100:.1f}pp  p95 {np.percentile(null_mm,95)*100:.1f}pp"
      f"   -> p = {p_second:.4f}")

# ---------------------------------------------------------------- CI + power
boot = []
for _ in range(NBOOT):
    pick = rng.choice(u_days, size=len(u_days), replace=True)
    ix = np.concatenate([day_idx[d] for d in pick])
    a, c = cond_rate(ix, SEGS[0]), cond_rate(ix, SEGS[2])
    if np.isfinite(a) and np.isfinite(c):
        boot.append(a - c)
boot = np.array(boot)
lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
p_boot = float(min(2 * min((boot <= 0).mean(), (boot >= 0).mean()), 1.0))
p1, p2 = obs[SEGS[0]]["cond"], obs[SEGS[2]]["cond"]
pbar = (p1 + p2) / 2
if 0 < pbar < 1 and abs(p1 - p2) > 1e-9:
    h = 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2))
    n_req = float((2.802 / abs(h)) ** 2) if abs(h) > 1e-9 else np.inf
else:
    n_req = np.inf
print(f"\n  effect size        : {stat_obs*100:+.1f} pp "
      f"({p1*100:.1f}% early vs {p2*100:.1f}% late, conditional)")
print(f"  day-clustered 95% CI: [{lo*100:+.1f}pp, {hi*100:+.1f}pp]   bootstrap p = {p_boot:.3f}")
print(f"  n needed PER GROUP for 80% power at this effect: {n_req:,.0f} trades that reach +1R")
print(f"  actual per group   : early {obs[SEGS[0]]['n_reached']}, late {obs[SEGS[2]]['n_reached']}")

established = bool(p_primary < 0.05 and (lo > 0 or hi < 0))
verdict = "ESTABLISHED" if established else "INCONCLUSIVE"
print(f"\n  REGISTERED DECISION RULE: p<0.05 AND CI excluding zero")
print(f"  VERDICT: {verdict}")
n_days_book = int(pd.Series(days).nunique())
shortfall = max(n_req - obs[SEGS[2]]["n_reached"], 0)
late_1r_per_day = obs[SEGS[2]]["n_reached"] / n_days_book
days_needed = shortfall / late_1r_per_day if late_1r_per_day > 0 else np.inf
if not established:
    print(f"  What would settle it: the binding constraint is the LATE segment. It needs "
          f"~{n_req:,.0f} +1R-reaching trades\n    and has {obs[SEGS[2]]['n_reached']} — a "
          f"shortfall of {shortfall:.0f}. The late segment produces "
          f"{late_1r_per_day:.3f} such trades per trading day\n    "
          f"({obs[SEGS[2]]['n_reached']} over {n_days_book} days), so roughly "
          f"{days_needed:,.0f} more trading days (~{days_needed/21:.0f} months) of live or "
          f"shadow data.\n    The early segment is already sufficient at "
          f"{obs[SEGS[0]]['n_reached']}.")
REP_EXTRA = dict(shortfall_late=float(shortfall), days_needed=float(days_needed),
                 n_days_book=n_days_book)
json.dump(dict(**REP_EXTRA, observed=obs, stat_primary=stat_obs, stat_secondary=maxmin_obs,
               p_primary=p_primary, p_secondary=p_second, ci=[lo, hi], p_boot=p_boot,
               n_required_per_group=n_req, verdict=verdict, nperm=NPERM,
               reached1R_rate=float(F.reached1R.mean())),
          open(f"{OUT}/part3_report.json", "w"), indent=1, default=float)
print(f"\nwrote {OUT}/part3_report.json")
