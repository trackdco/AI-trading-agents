#!/usr/bin/env python3
"""PAT'S 11 GATES, run in-house on the CURRENT spec: the armed three-book
empire, union tape 2020-2026 (S39).

Mirrors the external pipeline's scorecard (S38) with its own cost
conventions, applied to what the program actually is now (his ask:
"run the same tests on what we have now, the ARM1R"):

  costs    $2.50/contract/side commission + 1 tick/side slippage
           (= 0.75pt/RT on NQ's $20/pt), DOUBLED to 1.5pt for the
           stressed grade - heavier than this repo's own 0.5pt overlay.
  sizing   1 contract per trade, no sizing search (their rule). $ shown
           at both the NQ ($20/pt) frame they graded and the MNQ ($2/pt)
           frame this program actually trades (S38: the DD gate is a
           sizing-frame fact). Micro commissions are proportionally
           heavier in reality (~2x); that sits inside the stressed grade.
  account  $2,000 EOD-trailing drawdown (Lucid 50k), per their gate.

Differences from their pipeline, stated up front:
  - Their MCPT permutes entry timing inside a from-scratch engine; a
    1,000-permutation re-sim of three books x 7 years is not runnable
    here. The significance gate below is the computable honest form: the
    daily P&L series against a zero-edge null (mean-centered 5-day block
    permutation, 10,000 draws). Their entry-permutation MCPT remains the
    stronger form and is running on their side.
  - Timing jitter here is fill-price jitter: entry moved U(-1,+1)pt
    against/for the trade, exit prices held at their structural levels
    (a 1pt shift cannot flip an exit with a 5pt floor). Their jitter
    lives inside their engine; this repo's own S18 level-jitter RE-SIM
    (86-89% of R retained under measured chart noise) is the stronger
    in-house equivalent.
  - Regime terciles use each day's median trade risk as the realized-vol
    proxy (stops are 0.7x-anchored to candle size, so this is a direct
    vol measure available inside the dumps).

Inputs: the six armed dumps of S35/S36 (regenerable). Rail pass G3/G5/G6
identical to validation_wf.union_armed_daily.
"""
from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "analysis"
BASE_COST = 0.75          # pts per round trip per contract, their base
STRESS_COST = 1.50        # doubled
DD_LIMIT = 2000.0
FILES = (("pd_va_trades_lvall_xr30_sar_through_tf1_ng_arm1.jsonl.gz",
          "vwap_rev_tf1_retest_xr30_dd_arm1.jsonl.gz",
          "vwap_rev_tf1_retest_xr30_nyanc_dd_arm1.jsonl.gz"),
         ("pd_va_trades_nq20a_lvall_xr30_sar_through_tf1_arm1.jsonl.gz",
          "vwap_rev_tf1_retest_nq20a_ng0_xr30_dd_arm1.jsonl.gz",
          "vwap_rev_tf1_retest_nq20a_ng0_xr30_nyanc_dd_arm1.jsonl.gz"))


def load(name):
    with gzip.open(OUT / name, "rt") as f:
        return [json.loads(l) for l in f]


def railed_trades():
    kept = defaultdict(list)
    for lvf, svf, nvf in FILES:
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
                kept[d].append(t)
    return kept


def gate(ok, name, detail):
    print(f"{'PASS' if ok else 'FAIL':>6}  {name:<28}{detail}")
    return ok


def main():
    kept = railed_trades()
    days = sorted(kept)
    trades = [t for d in days for t in kept[d]]
    pts = np.array([t["pts"] for t in trades])
    n = len(trades)
    dpts_base = np.array([sum(t["pts"] - BASE_COST for t in kept[d])
                          for d in days])
    dpts_str = np.array([sum(t["pts"] - STRESS_COST for t in kept[d])
                         for d in days])
    dR = np.array([sum(t["r"] - 0.5 / t["risk"] for t in kept[d])
                   for d in days])

    print(f"ARMED EMPIRE x PAT'S GATES - {n:,} railed trades / "
          f"{len(days)} days, {days[0]} -> {days[-1]}\n")
    yr = defaultdict(float)
    for d, v in zip(days, dR):
        yr[d[:4]] += v
    print("net R by year (own 0.5pt overlay): "
          + "  ".join(f"{k} {v:+,.0f}" for k, v in sorted(yr.items())) + "\n")

    results = []
    # 1 sample size
    results.append(gate(n >= 100, "Sample size", f"{n:,} trades >= 100"))
    # 2 cost-stressed profitability (their cost model)
    nb, ns = dpts_base.sum(), dpts_str.sum()
    results.append(gate(
        nb > 0 and ns > 0, "Cost-stressed profitability",
        f"net {nb:+,.0f}pt base / {ns:+,.0f}pt stressed "
        f"(MNQ ${nb*2:+,.0f} / ${ns*2:+,.0f}; NQ ${nb*20:+,.0f} / "
        f"${ns*20:+,.0f})"))
    # 3 outlier dependency
    tb = np.array([t["pts"] - BASE_COST for t in trades])
    best = tb.max()
    gross = tb[tb > 0].sum()
    results.append(gate(
        (tb.sum() - best) > 0, "Outlier dependency",
        f"net {tb.sum()-best:+,.0f}pt with best trade removed - best is "
        f"{best/gross:.2%} of gross profit"))
    # 4 fill-price jitter, 20 trials
    rng = np.random.default_rng(11)
    wins = sum((tb - rng.uniform(-1, 1, n)).sum() > 0 for _ in range(20))
    results.append(gate(wins >= 10, "Fill-price jitter",
                        f"profitable in {wins}/20 trials (+-1pt) "
                        f"[S18 level-jitter re-sim: 86-89% R retained]"))
    # 5 trailing drawdown, their account
    eq1 = np.cumsum(dpts_base)                       # pts at 1 contract
    dd_pts = float((eq1 - np.maximum.accumulate(eq1)).min())
    dd_mnq, dd_nq = -dd_pts * 2, -dd_pts * 20
    micros = int(DD_LIMIT // dd_mnq) if dd_mnq > 0 else 99
    results.append(gate(
        dd_mnq <= DD_LIMIT, "Trailing drawdown",
        f"worst stretch ${dd_mnq:,.0f} at 1 MICRO vs ${DD_LIMIT:,.0f} "
        f"limit (fits {micros} micros; 1 big NQ = ${dd_nq:,.0f}, fails "
        f"as in their VA-cell grade)"))
    # 6+7 walk-forward efficiency + consistency (frozen spec, no selection)
    is_n, oos_n, folds = 252, 63, []
    start = is_n
    while start + 1 <= len(days) - 1:
        end = min(start + oos_n, len(days))
        folds.append((dpts_base[start - is_n:start].mean(),
                      dpts_base[start:end].mean()))
        start = end
    wfe = np.mean([o for _, o in folds]) / np.mean([i for i, _ in folds])
    pos = sum(o > 0 for _, o in folds)
    results.append(gate(wfe > 0.5, "Walk-forward efficiency",
                        f"OOS/IS {wfe:.3f} over {len(folds)} rolling folds "
                        f"(252d -> 63d) > 0.5"))
    q = defaultdict(float)
    for d, v in zip(days, dpts_base):
        q[(d[:4], (int(d[5:7]) - 1) // 3)] += v
    qpos = sum(v > 0 for v in q.values())
    results.append(gate(qpos == len(q), "Walk-forward consistency",
                        f"{qpos}/{len(q)} calendar quarters profitable "
                        f"({pos}/{len(folds)} rolling folds)"))
    # 8 no lookahead
    bad = sum(1 for t in trades
              if not (0 <= t["t_sig_hrs"] <= t["fill_hrs"] <= 23.01
                      and t["risk"] > 0 and t["hold_min"] >= 0
                      and np.isfinite(t["pts"])))
    results.append(gate(bad == 0, "No lookahead",
                        f"{bad} ordering/validity violations in {n:,} "
                        f"trades (signal <= fill <= exit, prior-day levels "
                        f"by construction)"))
    # 9 data coverage
    results.append(gate(len(q) >= 10, "Data coverage",
                        f"{len(q)} distinct quarters >= 10"))
    # 10 regime coverage (median day-risk terciles as realized-vol proxy)
    dayrisk = {d: float(np.median([t["risk"] for t in kept[d]]))
               for d in days if kept[d]}
    cuts = np.percentile(list(dayrisk.values()), [33.3, 66.7])
    terc = [0, 0, 0]
    for d in days:
        if d in dayrisk:
            terc[int(np.digitize(dayrisk[d], cuts))] += len(kept[d])
    results.append(gate(min(terc) >= 25, "Regime coverage",
                        f"trades per realized-vol tercile: {terc[0]:,} / "
                        f"{terc[1]:,} / {terc[2]:,} (each >= 25)"))
    # 11 significance vs zero-edge null (block permutation)
    rng = np.random.default_rng(11)
    cen = dpts_base - dpts_base.mean()
    nd, nb5 = len(cen), len(cen) // 5 + 1
    obs = dpts_base.mean()
    hits = 0
    P = 10000
    for _ in range(P):
        s = rng.integers(0, nd, nb5)
        idx = (s[:, None] + np.arange(5)[None, :]).ravel()[:nd] % nd
        if cen[idx].mean() >= obs:
            hits += 1
    p = (hits + 1) / (P + 1)
    results.append(gate(p <= 0.01, "Significance (zero-edge null)",
                        f"p = {p:.4f} (10,000 mean-centered 5-day block "
                        f"permutations) <= 0.01 [their entry-permutation "
                        f"MCPT is the stronger form, pending their side]"))

    print(f"\n{sum(results)} OF {len(results)} GATES PASS")


if __name__ == "__main__":
    main()
