#!/usr/bin/env python3
"""VALIDATION SUITE — PBO (CSCV) + Deflated Sharpe for the railed empire.

Two overfit tests run after the program was frozen (§33 of
docs/BACKTEST-pd-va-strategy.md); this file is the receipt.

1) PBO via Combinatorially Symmetric Cross-Validation (Bailey et al.):
   the 20-cell config matrix (4 depths x 5 targets) the tf1 champion was
   selected from, daily P&L per config, S=16 blocks -> C(16,8)=12,870
   IS/OOS splits. PBO = share of splits where the IS-best config lands
   below the OOS median. Result: PBO = 0.000; the champion cell's OOS
   relative rank is 0.95 (median AND minimum across all splits).

2) Deflated Sharpe (Bailey & Lopez de Prado) on the railed empire daily
   series — the three NQ books (8-level + session VWAP + NY VWAP champs)
   passed through guard rails G3 (first-in-wins dedupe within MIN_RISK,
   same dir) / G5 (global cap 4) / G6 (same-dir cap 3), 0.5pt round-trip
   cost. T=921 days, SR_daily 1.156, skew +0.39, kurt 3.3.
   Result: DSR = 1.000000 for any plausible trial count (40..10,000);
   the expected-max-SR haircut (0.05-0.09) is noise next to SR 1.16.
   Honest framing: a sim Sharpe this size mostly reflects the sim's
   idealizations (limit fills, no shocks) — PBO is the informative test.

Inputs (regenerable, gitignored):
  output/analysis/pd_va_trades_sar_through_tf1_ng.jsonl.gz   (champion grid)
  output/analysis/pd_va_trades_lvall_sar_through_tf1_ng.jsonl.gz
  output/analysis/vwap_rev_tf1_retest_dd.jsonl.gz
  output/analysis/vwap_rev_tf1_retest_nyanc_dd.jsonl.gz

Also saves the 921-value daily array (empire_daily.npy) next to this
repo's output dir — the array embedded in the Monte Carlo artifact.
"""
from __future__ import annotations

import gzip
import itertools
import json
from collections import defaultdict
from math import e as EULER_E
from math import log, sqrt
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "analysis"
COST_PTS = 0.5          # NQ round-trip overlay, in points
CHAMPION = (3.0, 1.0)   # depth, target_r
EM_GAMMA = 0.5772156649  # Euler-Mascheroni


def load(name):
    with gzip.open(OUT / name, "rt") as f:
        return [json.loads(l) for l in f]


def net_r(t):
    return t["r"] - COST_PTS / t["risk"]


def pbo_cscv(S=16):
    rows = load("pd_va_trades_sar_through_tf1_ng.jsonl.gz")
    cfgs = sorted({(t["depth"], t["target_r"]) for t in rows})
    daily = defaultdict(lambda: defaultdict(float))
    for t in rows:
        daily[(t["depth"], t["target_r"])][t["day"]] += net_r(t)
    days = sorted({d for c in daily for d in daily[c]})
    M = np.array([[daily[c].get(d, 0.0) for d in days] for c in cfgs])
    print(f"config matrix: {M.shape[0]} configs x {M.shape[1]} days")

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
    print(f"CSCV PBO (S={S}, {len(combos)} splits): "
          f"PBO = {(logits <= 0).mean():.3f}  "
          f"(prob the IS-best underperforms the OOS median; <0.1 excellent)")
    print(f"champion cell OOS relative rank: "
          f"median {np.median(champ_ranks):.2f}, min {min(champ_ranks):.2f}")


def empire_daily():
    """The §32 rail pass: three books, G3/G5/G6, cost overlay."""
    lv = load("pd_va_trades_lvall_sar_through_tf1_ng.jsonl.gz")
    sv = [t for t in load("vwap_rev_tf1_retest_dd.jsonl.gz")
          if t["depth"] == 3.0 and t["target_r"] == 1.0]
    nv = [t for t in load("vwap_rev_tf1_retest_nyanc_dd.jsonl.gz")
          if t["depth"] == 3.0 and t["target_r"] == 1.0]
    byday = defaultdict(list)
    for t in lv + sv + nv:
        byday[t["day"]].append(t)
    kept = defaultdict(float)
    for d, ts in byday.items():
        ts.sort(key=lambda t: (t["fill_hrs"], t["t_sig_hrs"]))
        open_pos = []
        for t in ts:
            f, en = t["fill_hrs"], t["fill_hrs"] + t["hold_min"] / 60
            open_pos = [p for p in open_pos if p[1] > f]
            if any(dr == t["dir"] and abs(px - t["entry"]) <= 5.0
                   for _, _, dr, px in open_pos):
                continue                                   # G3 dedupe
            if len(open_pos) >= 4:
                continue                                   # G5 global cap
            if sum(1 for *_, dr, _ in open_pos if dr == t["dir"]) >= 3:
                continue                                   # G6 same-dir cap
            open_pos.append((f, en, t["dir"], t["entry"]))
            kept[d] += net_r(t)
    return np.array([kept[d] for d in sorted(kept)])


def deflated_sharpe(v):
    nd = NormalDist()
    T = len(v)
    sr = float(v.mean() / v.std())
    z = (v - v.mean()) / v.std()
    sk, ku = float((z ** 3).mean()), float((z ** 4).mean())
    print(f"\nrailed empire daily: T={T}  mean {v.mean():+.2f}R  "
          f"std {v.std():.2f}R  SR_daily {sr:.3f} "
          f"(annualized ~{sr * sqrt(252):.1f})  skew {sk:+.2f}  kurt {ku:.1f}")
    for N in (40, 200, 1000, 10000):
        var_sr = 0.5 / T   # conservative trial-SR variance proxy
        sr0 = sqrt(var_sr) * ((1 - EM_GAMMA) * nd.inv_cdf(1 - 1 / N)
                              + EM_GAMMA * nd.inv_cdf(1 - 1 / (N * EULER_E)))
        zz = ((sr - sr0) * sqrt(T - 1)) / sqrt(
            max(1 - sk * sr + (ku - 1) / 4 * sr ** 2, 1e-9))
        print(f"  N={N:>6} trials: max-SR haircut {sr0:.3f}  "
              f"->  DSR P(true SR>0) = {nd.cdf(zz):.9f}")


if __name__ == "__main__":
    pbo_cscv()
    v = empire_daily()
    deflated_sharpe(v)
    np.save(OUT / "empire_daily.npy", v)
    print(f"\nempire_daily.npy saved ({len(v)} values) — "
          f"the array embedded in the Monte Carlo artifact")
