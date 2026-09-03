#!/usr/bin/env python3
"""VALIDATION SUITE 2 — PBO + Deflated Sharpe + WALK-FORWARD on the union tape.

S37 of docs/BACKTEST-pd-va-strategy.md. Re-runs the S33 overfit audit on
everything the program now has (2020-2022 holdout tape + 2023-2026, cap
30 in-engine), and adds the walk-forward analysis he asked for: roll a
selection window through seven years, pick the best config on each
in-sample stretch, trade it forward on unseen days, and measure how much
of the in-sample edge survives out-of-sample.

PRE-REGISTERED VERDICTS, written before any of this was run:

  PBO (CSCV, S=16, all 12,870 splits, union grid matrix):
      PASS if PBO < 0.10.
  Deflated Sharpe (union armed empire daily series, N up to 10,000
      trials): PASS if DSR >= 0.95 at N=10,000.
  Walk-forward (IS 252 trading days rolling, OOS 63, step 63; selection
      = IS daily Sharpe on the 20-cell depth x target grid):
      PASS if walk-forward efficiency (mean OOS R/day of the adaptive
      picks / mean IS R/day of those picks) >= 0.50 AND >= 70% of OOS
      folds are positive.
  Edge decay (frozen champion cell depth 3 / 1R, fold-OOS R/day
      regressed on fold index): NO-DECAY if the slope's t-stat > -2.

Scope, stated honestly: the grid is the VA-family book - the surface the
original search actually ran over. The other level families were adopted
at the frozen cell with no search (S25), VWAP books likewise; the arm
parameter has its own guard (bucket edge fixed pre-result, re-passed
out of era by 6x, S35-S36). The 2023-26 tape here carries the 39-day
2026 hole (the splice parquet lives on the other machine); union is
~1,690 rail days rather than the full 1,719.

Inputs (regenerable):
  output/analysis/pd_va_trades_xr30_sar_through_tf1_ng.jsonl.gz
  output/analysis/pd_va_trades_nq20a_xr30_sar_through_tf1.jsonl.gz
  the six armed empire dumps of S35/S36 (see FILES_ARM below).
"""
from __future__ import annotations

import gzip
import itertools
import json
from collections import Counter, defaultdict
from math import e as EULER_E
from math import log, sqrt
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "analysis"
COST = 0.5
CHAMPION = (3.0, 1.0)
EM_GAMMA = 0.5772156649
GRID_FILES = ("pd_va_trades_xr30_sar_through_tf1_ng.jsonl.gz",
              "pd_va_trades_nq20a_xr30_sar_through_tf1.jsonl.gz")
FILES_ARM = (("pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",
              "vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",
              "vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz"),
             ("pd_va_trades_nq20a_lvall_xr30_sar_through_tf1_arm1.jsonl.gz",
              "vwap_rev_tf1_retest_nq20a_ng0_xr30_dd_arm1.jsonl.gz",
              "vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd_arm1.jsonl.gz"))


def load(name):
    with gzip.open(OUT / name, "rt") as f:
        return [json.loads(l) for l in f]


def net(t):
    return t["r"] - COST / t["risk"]


def grid_matrix():
    daily = defaultdict(lambda: defaultdict(float))
    for fn in GRID_FILES:
        for t in load(fn):
            daily[(t["depth"], t["target_r"])][t["day"]] += net(t)
    cfgs = sorted(daily)
    days = sorted({d for c in daily for d in daily[c]})
    M = np.array([[daily[c].get(d, 0.0) for d in days] for c in cfgs])
    print(f"grid matrix: {len(cfgs)} configs x {len(days)} days "
          f"({days[0]} -> {days[-1]})")
    return cfgs, days, M


def pbo_cscv(cfgs, M, S=16):
    blocks = np.array_split(np.arange(M.shape[1]), S)
    combos = list(itertools.combinations(range(S), S // 2))
    logits, champ_ranks = [], []
    ci = cfgs.index(CHAMPION)
    for combo in combos:
        is_i = np.concatenate([blocks[i] for i in combo])
        oo_i = np.concatenate([blocks[i] for i in range(S) if i not in combo])
        p_is = M[:, is_i].mean(1) / (M[:, is_i].std(1) + 1e-9)
        p_oo = M[:, oo_i].mean(1) / (M[:, oo_i].std(1) + 1e-9)
        best = int(np.argmax(p_is))
        rank = (p_oo < p_oo[best]).mean()
        w = min(max(rank, 1e-9), 1 - 1e-9)
        logits.append(log(w / (1 - w)))
        champ_ranks.append((p_oo < p_oo[ci]).mean())
    logits = np.array(logits)
    pbo = float((logits <= 0).mean())
    print(f"\nCSCV PBO (S={S}, {len(combos)} splits): PBO = {pbo:.3f}  "
          f"[prereg: PASS < 0.10] -> {'PASS' if pbo < 0.10 else 'FAIL'}")
    print(f"champion cell OOS relative rank: median "
          f"{np.median(champ_ranks):.2f}, min {min(champ_ranks):.2f}")


def walk_forward(cfgs, days, M, is_n=252, oos_n=63):
    ci = cfgs.index(CHAMPION)
    folds = []
    start = is_n
    while start + 1 <= M.shape[1] - 1:
        end = min(start + oos_n, M.shape[1])
        is_sl, oo_sl = slice(start - is_n, start), slice(start, end)
        sharpe_is = M[:, is_sl].mean(1) / (M[:, is_sl].std(1) + 1e-9)
        pick = int(np.argmax(sharpe_is))
        folds.append(dict(
            d0=days[start], d1=days[end - 1], pick=cfgs[pick],
            is_rday=float(M[pick, is_sl].mean()),
            oos_rday=float(M[pick, oo_sl].mean()),
            champ_oos_rday=float(M[ci, oo_sl].mean()),
            oos=M[pick, oo_sl]))
        start = end
    print(f"\nWALK-FORWARD: IS {is_n}d rolling -> OOS {oos_n}d, "
          f"{len(folds)} folds, selection = IS daily Sharpe")
    print(f"{'fold OOS window':<26}{'picked cell':>13}{'IS R/d':>8}"
          f"{'OOS R/d':>9}{'champ OOS':>10}")
    for f in folds:
        print(f"{f['d0']} -> {f['d1']}   {str(f['pick']):>13}"
              f"{f['is_rday']:>+8.2f}{f['oos_rday']:>+9.2f}"
              f"{f['champ_oos_rday']:>+10.2f}")
    is_m = np.mean([f["is_rday"] for f in folds])
    oo_m = np.mean([f["oos_rday"] for f in folds])
    wfe = oo_m / is_m
    pos = np.mean([f["oos_rday"] > 0 for f in folds])
    picks = Counter(f["pick"] for f in folds)
    stitched = np.concatenate([f["oos"] for f in folds])
    eq = np.cumsum(stitched)
    mdd = float((eq - np.maximum.accumulate(eq)).min())
    print(f"\nWFE = mean OOS R/day / mean IS R/day = {oo_m:+.3f}/{is_m:+.3f}"
          f" = {wfe:.2f}   folds positive {pos:.0%}")
    print(f"[prereg: PASS if WFE >= 0.50 AND >= 70% folds positive] -> "
          f"{'PASS' if wfe >= 0.5 and pos >= 0.70 else 'FAIL'}")
    print(f"stitched OOS-only equity: {len(stitched)} days  "
          f"total {stitched.sum():+.0f}R  {stitched.mean():+.2f}R/day  "
          f"Sharpe {stitched.mean()/stitched.std():.3f}  maxDD {mdd:+.1f}R")
    print("selection stability: " + ", ".join(
        f"{k} x{v}" for k, v in picks.most_common()))
    # edge decay through time, on the FROZEN champion so selection noise
    # cannot mask or fake a trend
    y = np.array([f["champ_oos_rday"] for f in folds])
    x = np.arange(len(y), dtype=float)
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    se = sqrt(resid.var(ddof=2) / ((x - x.mean()) ** 2).sum())
    t = b / se
    print(f"\nEDGE DECAY (frozen champion, fold OOS R/day vs time): "
          f"slope {b:+.4f} R/day per fold (t = {t:+.2f})")
    print(f"[prereg: NO-DECAY if t > -2] -> "
          f"{'NO-DECAY' if t > -2 else 'DECAY'}")


def union_armed_daily():
    kept_daily = defaultdict(float)
    for lvf, svf, nvf in FILES_ARM:
        lv = load(lvf)
        sv = [t for t in load(svf)
              if t["depth"] == 3.0 and t["target_r"] == 1.0]
        nv = [t for t in load(nvf)
              if t["depth"] == 3.0 and t["target_r"] == 1.0]
        byday = defaultdict(list)
        for t in lv + sv + nv:
            byday[t["day"]].append(t)
        for d, ts in byday.items():
            ts.sort(key=lambda t: (t["fill_hrs"], t["t_sig_hrs"]))
            op = []
            for t in ts:
                f, en = t["fill_hrs"], t["fill_hrs"] + t["hold_min"] / 60
                op = [p for p in op if p[1] > f]
                if any(dr == t["dir"] and abs(px - t["entry"]) <= 5.0
                       for _, _, dr, px in op):
                    continue
                if len(op) >= 4:
                    continue
                if sum(1 for *_, dr, _ in op if dr == t["dir"]) >= 3:
                    continue
                op.append((f, en, t["dir"], t["entry"]))
                kept_daily[d] += net(t)
    return np.array([kept_daily[d] for d in sorted(kept_daily)])


def deflated_sharpe(v):
    nd = NormalDist()
    T = len(v)
    sr = float(v.mean() / v.std())
    z = (v - v.mean()) / v.std()
    sk, ku = float((z ** 3).mean()), float((z ** 4).mean())
    print(f"\nunion ARMED empire daily: T={T}  mean {v.mean():+.2f}R  "
          f"std {v.std():.2f}R  SR_daily {sr:.3f} "
          f"(~{sr * sqrt(252):.1f} ann.)  skew {sk:+.2f}  kurt {ku:.1f}")
    for N in (40, 200, 1000, 10000):
        var_sr = 0.5 / T
        sr0 = sqrt(var_sr) * ((1 - EM_GAMMA) * nd.inv_cdf(1 - 1 / N)
                              + EM_GAMMA * nd.inv_cdf(1 - 1 / (N * EULER_E)))
        zz = ((sr - sr0) * sqrt(T - 1)) / sqrt(
            max(1 - sk * sr + (ku - 1) / 4 * sr ** 2, 1e-9))
        p = nd.cdf(zz)
        tail = (f"  [prereg: PASS >= 0.95] -> "
                f"{'PASS' if p >= 0.95 else 'FAIL'}" if N == 10000 else "")
        print(f"  N={N:>6} trials: max-SR haircut {sr0:.3f}  ->  "
              f"DSR = {p:.9f}{tail}")


if __name__ == "__main__":
    cfgs, days, M = grid_matrix()
    pbo_cscv(cfgs, M)
    walk_forward(cfgs, days, M)
    deflated_sharpe(union_armed_daily())
