#!/usr/bin/env python3
"""EXIT / MANAGEMENT VARIABLES TEST, by time-of-day segment — with a best-of-N selection null.

Brake: "run a variables type test and find what the most optimal thing would be, so we could
eradicate unnecessary losses whilst keeping winners."

THE TRAP THIS IS BUILT AROUND. Sweeping 68 management rules and reporting the best one is how
you manufacture an edge. H1 (fixed targets 1.5-4R) and H4 (bar-close MAE cuts) both already
FAILED this book under walk-forward. So the sweep is scored the only way it can be scored
honestly: the rule is chosen on the IN-SAMPLE half ONLY, evaluated on the OUT-OF-SAMPLE half,
and the whole select-then-evaluate procedure is repeated on NSPLIT day-block-permuted IS/OOS
assignments to price the best-of-68 selection itself. If the real OOS improvement is not beyond
the 95th percentile of that null, the sweep found nothing.

RULES (frozen before running; 17 rules x 4 segment scopes = 68 configurations):
  fixed target      T in {1.0, 1.5, 2.0, 2.5, 3.0, 4.0} R
  breakeven stop    move stop to entry once B in {1.0, 1.5, 2.0} R is touched
  trail from peak   arm at {1.5, 2.0} R, trail {0.5, 1.0} R behind the peak
  time stop         exit at the close of bar {15, 30, 45, 60}
  scopes            all trades | early 08:00-08:29 | mid 08:30-08:59 | late 09:00-09:29
                    (outside the scope the canon's own exit stands)

COSTS, stated: $1.24/micro round trip; $0.50/micro extra on MARKETABLE exits (stop, trail,
time). Resting-limit target fills take no slippage. Simulation window: fill bar -> 15:55 ET,
stop always live. The canon baseline is its own recorded P&L and carries its own cost
convention — that difference is stated, not hidden, so rule-vs-rule ranking is the clean
comparison and rule-vs-canon is indicative.

BASELINE: partially remediated (C only) + news filter. W and dep_* leaky in the selection path.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
os.chdir(REPO)
OUT = f"{REPO}/research/sweep_2026_07/micro"
RAW = f"{OUT}/raw"
os.makedirs(RAW, exist_ok=True)
COMM_RT, SLIP_MKT = 1.24, 0.50
NSPLIT = 500

ap = argparse.ArgumentParser()
ap.add_argument("--mode", default="real", choices=["real", "null"])
ap.add_argument("--shard", type=int, default=0)
ap.add_argument("--nshards", type=int, default=1)
a = ap.parse_args()

F = pd.read_csv(f"{OUT}/micro_frame.csv")
F["ft"] = pd.to_datetime(F.ft, utc=True)
F["et"] = F.ft.dt.tz_convert("America/New_York")
bars = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                       columns=["ts_event", "high", "low", "close"])
bars["ts"] = pd.to_datetime(bars.ts_event, utc=True)
bars = bars.drop_duplicates("ts").set_index("ts").sort_index()
BI, BH, BL, BC = bars.index, bars.high.values, bars.low.values, bars.close.values

# ---------------------------------------------------------------- precompute R paths
PATH = []
for r in F.itertuples(index=False):
    d = 1 if r.direction == "long" else -1
    k0 = int(r.k0)
    close_et = r.et.replace(hour=15, minute=55, second=0, microsecond=0)
    kend = min(int(BI.searchsorted(close_et.tz_convert("UTC"), side="right")), len(BI) - 1)
    kend = max(kend, k0 + 1)
    hi = ((BH[k0:kend + 1] - r.entry) if d > 0 else (r.entry - BL[k0:kend + 1])) / r.risk_pts
    lo = ((BL[k0:kend + 1] - r.entry) if d > 0 else (r.entry - BH[k0:kend + 1])) / r.risk_pts
    cl = ((BC[k0:kend + 1] - r.entry) if d > 0 else (r.entry - BC[k0:kend + 1])) / r.risk_pts
    PATH.append((hi, lo, cl))

RULES = ([("target", t) for t in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)]
         + [("be", b) for b in (1.0, 1.5, 2.0)]
         + [("trail", (t, s)) for t in (1.5, 2.0) for s in (0.5, 1.0)]
         + [("time", k) for k in (15, 30, 45, 60)])
SCOPES = ("all", "early 08:00-08:29", "mid 08:30-08:59", "late 09:00-09:29")


def sim(i, kind, par):
    """Return (R_realised, marketable) for trade i under one rule. Stop always live."""
    hi, lo, cl = PATH[i]
    n = len(hi)
    if kind == "target":
        for k in range(n):
            if lo[k] <= -1.0:
                return -1.0, True
            if hi[k] >= par:
                return par, False
        return cl[-1], True
    if kind == "be":
        armed = False
        for k in range(n):
            if armed and lo[k] <= 0.0:
                return 0.0, True
            if not armed and lo[k] <= -1.0:
                return -1.0, True
            if hi[k] >= par:
                armed = True
        return cl[-1], True
    if kind == "trail":
        arm, back = par
        peak, armed = -np.inf, False
        for k in range(n):
            if armed and lo[k] <= peak - back:
                return max(peak - back, -1.0), True
            if not armed and lo[k] <= -1.0:
                return -1.0, True
            peak = max(peak, hi[k])
            if peak >= arm:
                armed = True
        return cl[-1], True
    if kind == "time":
        kk = min(par, n - 1)
        for k in range(kk + 1):
            if lo[k] <= -1.0:
                return -1.0, True
        return cl[kk], True
    raise ValueError(kind)


CACHE = {}
def rule_pl(kind, par):
    """Per-trade dollar P&L for every trade under one rule (cached)."""
    key = (kind, par)
    if key in CACHE:
        return CACHE[key]
    out = np.empty(len(F))
    for i, r in enumerate(F.itertuples(index=False)):
        R_, mkt = sim(i, kind, par)
        per_micro = R_ * r.risk_pts * 2.0 - COMM_RT - (SLIP_MKT if mkt else 0.0)
        out[i] = r.micros * per_micro
    CACHE[key] = out
    return out


BASE = F.pl.values.astype(float)
SEG = F.seg.values


def config_pl(kind, par, scope):
    p = rule_pl(kind, par)
    if scope == "all":
        return p
    m = SEG == scope
    return np.where(m, p, BASE)


CONFIGS = [(k, v, s) for (k, v) in RULES for s in SCOPES]


def evaluate(mask_is, mask_oos):
    """Select the best config on IS by total P&L, then report its OOS improvement over canon."""
    best, best_v = None, -np.inf
    for (k, v, s) in CONFIGS:
        p = config_pl(k, v, s)
        val = float(p[mask_is].sum() - BASE[mask_is].sum())
        if val > best_v:
            best, best_v = (k, v, s), val
    p = config_pl(*best)
    return best, best_v, float(p[mask_oos].sum() - BASE[mask_oos].sum())


is_m, oos_m = (~F.oos.values.astype(bool)), F.oos.values.astype(bool)
days = F.day.values
u_days = pd.unique(days)
n_is_days = len(pd.unique(days[is_m]))

if a.mode == "real":
    print(f"{len(F)} trades | {len(CONFIGS)} configurations "
          f"({len(RULES)} rules x {len(SCOPES)} scopes)")
    rows = []
    for (k, v, s) in CONFIGS:
        p = config_pl(k, v, s)
        rows.append(dict(rule=f"{k}{v}", scope=s,
                         total=float(p.sum()), is_=float(p[is_m].sum()),
                         oos=float(p[oos_m].sum()),
                         d_is=float(p[is_m].sum() - BASE[is_m].sum()),
                         d_oos=float(p[oos_m].sum() - BASE[oos_m].sum())))
    T = pd.DataFrame(rows).sort_values("d_is", ascending=False)
    T.to_csv(f"{OUT}/exit_sweep_table.csv", index=False)
    print(f"\ncanon baseline: total ${BASE.sum():+,.0f}  IS ${BASE[is_m].sum():+,.0f}  "
          f"OOS ${BASE[oos_m].sum():+,.0f}")
    print(f"\nTOP 12 BY IN-SAMPLE IMPROVEMENT (this is the selection step — OOS is the test)")
    print(f"{'rule':12s} {'scope':20s} {'IS delta':>11} {'OOS delta':>11} {'total':>11}")
    for r in T.head(12).itertuples(index=False):
        print(f"{r.rule:12s} {r.scope:20s} {r.d_is:>+11,.0f} {r.d_oos:>+11,.0f} {r.total:>+11,.0f}")
    best, bis, boos = evaluate(is_m, oos_m)
    print(f"\nIS-SELECTED RULE: {best[0]}{best[1]} on '{best[2]}'")
    print(f"  in-sample improvement  : ${bis:+,.0f}   (this is the number that is NOT evidence)")
    print(f"  OUT-OF-SAMPLE outcome  : ${boos:+,.0f}   (this is the number that matters)")
    n_better = int((T.d_oos > 0).sum())
    print(f"\n  configurations that beat canon OOS: {n_better}/{len(CONFIGS)} "
          f"({n_better/len(CONFIGS)*100:.0f}%) — with 68 tries, ~half beating by chance is the "
          f"null expectation, not a finding")
    json.dump(dict(n_configs=len(CONFIGS), canon_total=float(BASE.sum()),
                   canon_is=float(BASE[is_m].sum()), canon_oos=float(BASE[oos_m].sum()),
                   best=dict(rule=f"{best[0]}{best[1]}", scope=best[2], d_is=bis, d_oos=boos),
                   n_beat_oos=n_better,
                   top=T.head(12).to_dict("records")),
              open(f"{OUT}/exit_sweep_real.json", "w"), indent=1, default=float)
    print(f"\nwrote {OUT}/exit_sweep_real.json + exit_sweep_table.csv")
else:
    rs = np.random.default_rng(4242 + a.shard)
    mine = [k for k in range(NSPLIT) if k % a.nshards == a.shard]
    path = f"{RAW}/null_{a.shard:02d}.jsonl"
    done = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                done.add(json.loads(line)["k"])
            except Exception:
                pass
    with open(path, "a", buffering=1) as fh:
        for k in mine:
            if k in done:
                continue
            pick = set(rs.choice(u_days, size=n_is_days, replace=False))
            m_is = np.array([d in pick for d in days])
            _, bi, bo = evaluate(m_is, ~m_is)
            fh.write(json.dumps(dict(k=k, d_is=bi, d_oos=bo)) + "\n")
    print(f"null shard {a.shard}/{a.nshards}: {len(mine)} splits -> {path}")
