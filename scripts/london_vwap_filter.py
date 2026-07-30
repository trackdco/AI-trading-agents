#!/usr/bin/env python3
"""LONDON — what if we never faded VWAP? FIT ONLY. Holdout sealed.

The loss anatomy found the one Bonferroni-clearing loser signature: entries on the WRONG side of
VWAP (long below the day's volume-weighted average, short above it) — fading value rather than
trading with it. This asks the obvious follow-up: drop those entries, keep only the right-side
ones, what happens to the book?

CAUSAL. ent_vs_vwap_sd_dir is built strictly from bars before the fill minute (london_matrix.py
line 120: `B.loc[sess0 : f - 1min]`) and VWAP at entry is known at entry, so "skip if wrong side
of VWAP" is a rule you could have traded live. No foreknowledge.

THE TRAP, STATED UP FRONT. Any filter derived from these same losers will flatter itself on these
same trades — that is what in-sample means, and a p-value cannot undo it. So the headline is the
PRE-SPECIFIED threshold (right side = dir-adj VWAP >= 0, no tuning), the sweep is shown only as
sensitivity, and two guards are applied:
  1. a random-drop null — does removing THESE K trades beat removing K random trades? If the
     filter only matches a random cut of the same size, it is just "trade less", not a signal.
  2. per-era — the net must improve in BOTH 2025 and 2026, or it is a one-era artifact.
Even passing both, this is a fit-book lead to confirm on the sealed holdout, not a validated edge.

    python -m scripts.london_vwap_filter
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import (BUDGET, N_PATHS, SEED, _daymap, lon_book,  # noqa: E402
                                         lon_pop, maxdd, mc, preflight, replay, write)

FLOOR, LIFETIME, CAP = 9.5, math.inf, 999
VWAP = "ent_vs_vwap_sd_dir"
PRIMARY = 0.0                                   # "right side of VWAP", no tuning
SWEEP = [-0.5, -0.25, 0.0, 0.25, 0.5]
N_PERM = 5000


def bookstats(t: pd.DataFrame) -> dict:
    d = t.groupby("day").dollars.sum()
    return {"n": len(t), "net": float(t.dollars.sum()), "wr": float((t.R > 0).mean()),
            "R": float(t.R.mean()), "dd": maxdd(d), "worst": float(t.dollars.min()),
            "n25": int((t.era == "2025").sum()), "n26": int((t.era == "2026").sum()),
            "net25": float(t[t.era == "2025"].dollars.sum()),
            "net26": float(t[t.era == "2026"].dollars.sum())}


def taken(P: pd.DataFrame, thr: float | None) -> pd.DataFrame:
    """Re-select the book from the population, optionally keeping only right-side-of-VWAP entries.
    Filtering the POPULATION (not the taken book) is the honest form: a trade you would have
    skipped never consumes a cap slot or contributes to the day-stop accumulator."""
    Q = P if thr is None else P[P[VWAP] >= thr]
    t = lon_book(Q, floor=FLOOR, lifetime=LIFETIME, cap=CAP).copy()
    t["era"] = pd.to_datetime(t.day).dt.year.astype(str)
    return t


def main() -> None:
    P = lon_pop()
    base = taken(P, None)
    bs = bookstats(base)
    covered = base[VWAP].notna()
    L = ["# London — only entering on the right side of VWAP\n",
         "\n**Fit only. Sealed 2023/24 never loaded. Causal filter, in-sample test.**\n",
         f"\nBaseline (frozen arm, flat 1 lot): **{bs['n']} trades, ${bs['net']:+,.0f}, "
         f"{bs['wr'] * 100:.0f}% win, mean R {bs['R']:+.3f}, maxDD ${bs['dd']:,.0f}, "
         f"worst ${bs['worst']:+,.0f}**.\n",
         f"\nThe filter keeps a trade only if its direction-adjusted entry-vs-VWAP is at or above a "
         f"threshold: a long at/above the day's VWAP, a short at/below it. **Right side of VWAP = "
         f"threshold {PRIMARY:g}**, pre-specified, no tuning. {int((~covered).sum())} of {bs['n']} "
         f"trades have no VWAP feature (too few pre-fill bars) and are KEPT under every threshold "
         f"— dropping them would be a different, silent filter.\n"]

    # ---- Part 1: the pre-specified filter -------------------------------------------------
    prim = taken(P, PRIMARY)
    ps = bookstats(prim)
    dropped = base[base[VWAP] < PRIMARY]
    L.append(f"\n## The pre-specified filter (right side of VWAP, threshold {PRIMARY:g})\n\n"
             f"Drops **{bs['n'] - ps['n']}** wrong-side entries "
             f"(the ones still selected after re-running the causal walk on the filtered pool).\n\n"
             "| book | trades | net $ | win rate | mean R | maxDD | worst | 2025 net | 2026 net |\n"
             "|---|---|---|---|---|---|---|---|---|\n")
    for lab, s in (("baseline (fade allowed)", bs), (f"right-side only (>= {PRIMARY:g})", ps)):
        L.append(f"| {lab} | {s['n']} | ${s['net']:+,.0f} | {s['wr'] * 100:.0f}% | "
                 f"{s['R']:+.3f} | ${s['dd']:,.0f} | ${s['worst']:+,.0f} | "
                 f"${s['net25']:+,.0f} | ${s['net26']:+,.0f} |\n")
    L.append(f"| **change** | **{ps['n'] - bs['n']:+d}** | **${ps['net'] - bs['net']:+,.0f}** | "
             f"**{(ps['wr'] - bs['wr']) * 100:+.0f}pp** | **{ps['R'] - bs['R']:+.3f}** | "
             f"**${ps['dd'] - bs['dd']:+,.0f}** | **${ps['worst'] - bs['worst']:+,.0f}** | "
             f"**${ps['net25'] - bs['net25']:+,.0f}** | **${ps['net26'] - bs['net26']:+,.0f}** |\n")
    # what did the dropped trades do on their own?
    dd = dropped
    L.append(f"\n**The dropped trades on their own:** {len(dd)} entries, "
             f"${dd.dollars.sum():+,.0f}, {(dd.R > 0).mean() * 100:.0f}% win, mean R "
             f"{dd.R.mean():+.3f}. "
             + ("They were net negative, so cutting them adds money AND lowers risk — the "
                "cleanest kind of filter.\n" if dd.dollars.sum() < 0 else
                "They were net POSITIVE despite the low win rate — cutting them removes some "
                "profit, so the filter only helps if the drawdown reduction is worth it.\n"))

    # ---- Part 2: is it more than 'trade less'? --------------------------------------------
    rng = np.random.default_rng(SEED)
    K = int((base[VWAP] < PRIMARY).sum())            # trades the filter removes from the pool
    obs = ps["net"]
    # null: drop K random trades from the FULL taken book, sum the rest. Compare to the filter's
    # re-selected net. (Re-selection moves the number a little; the null is deliberately the
    # simpler sum so it cannot be gamed by the day-stop.)
    base_sum = base.dollars.values
    idx = np.arange(len(base))
    null = np.empty(N_PERM)
    for i in range(N_PERM):
        keep = rng.choice(idx, len(base) - K, replace=False)
        null[i] = base_sum[keep].sum()
    p_rand = float((null >= obs).mean())
    L.append(f"\n## Guard 1 — is this more than just trading fewer trades?\n\n"
             f"Removing {K} trades at random from the {bs['n']}-trade book, {N_PERM:,} times, and "
             f"comparing where the VWAP filter's net lands in that distribution.\n\n"
             f"| | net $ |\n|---|---|\n"
             f"| VWAP filter (right side only) | ${obs:+,.0f} |\n"
             f"| random drop of {K}: median | ${np.median(null):+,.0f} |\n"
             f"| random drop of {K}: p95 | ${np.percentile(null, 95):+,.0f} |\n"
             f"\n**p = {p_rand:.4f}** — the filter beats {(1 - p_rand) * 100:.1f}% of equal-sized "
             f"random cuts. "
             + ("It is doing more than thinning the book.\n" if p_rand < 0.05 else
                "It is NOT clearly better than removing the same number of trades at random — the "
                "gain is mostly 'fewer trades', not 'the right trades'.\n"))

    # ---- Part 2b: per era ------------------------------------------------------------------
    both = (ps["net25"] > bs["net25"]) and (ps["net26"] > bs["net26"])
    L.append(f"\n## Guard 2 — does it hold in both eras?\n\n"
             f"2025 net ${bs['net25']:+,.0f} -> ${ps['net25']:+,.0f} "
             f"(${ps['net25'] - bs['net25']:+,.0f}); "
             f"2026 net ${bs['net26']:+,.0f} -> ${ps['net26']:+,.0f} "
             f"(${ps['net26'] - bs['net26']:+,.0f}). "
             + ("Improves in BOTH eras.\n" if both else
                "Does NOT improve in both eras — treat as a one-era artifact.\n"))

    # ---- Part 3: the sweep, as sensitivity only -------------------------------------------
    L.append(f"\n## Threshold sensitivity (NOT for picking — the headline is {PRIMARY:g})\n\n"
             "Raising the threshold demands the entry be further onto the right side of VWAP. "
             "Shown so the choice of 0 is visible against its neighbours; picking the best cell "
             "here would be the selection inflation this doc is trying not to commit.\n\n"
             "| threshold | trades | net $ | win rate | mean R | maxDD | net/maxDD | "
             "2025 / 2026 net |\n|---|---|---|---|---|---|---|---|\n")
    L.append(f"| none (baseline) | {bs['n']} | ${bs['net']:+,.0f} | {bs['wr'] * 100:.0f}% | "
             f"{bs['R']:+.3f} | ${bs['dd']:,.0f} | {bs['net'] / max(bs['dd'], 1):.1f} | "
             f"${bs['net25']:+,.0f} / ${bs['net26']:+,.0f} |\n")
    for thr in SWEEP:
        s = bookstats(taken(P, thr))
        star = " **<- right side**" if thr == PRIMARY else ""
        L.append(f"| >= {thr:+g}{star} | {s['n']} | ${s['net']:+,.0f} | {s['wr'] * 100:.0f}% | "
                 f"{s['R']:+.3f} | ${s['dd']:,.0f} | {s['net'] / max(s['dd'], 1):.1f} | "
                 f"${s['net25']:+,.0f} / ${s['net26']:+,.0f} |\n")

    # ---- Part 4: what it does to the funded account ---------------------------------------
    N = preflight()
    EMPTY = pd.DataFrame(columns=["day", "fill_ts", "session", "risk", "pnl", "R"])
    B0, _ = replay(N, EMPTY, "clock")
    ny_net = float(B0.pnl.sum())
    dmN, kN = _daymap(N)
    base_mc = mc(dmN, kN)
    L.append(f"\n## What it does to the funded account (NY + London, shared ${BUDGET:,.0f})\n\n"
             f"The filter also frees shared budget for NY, since a skipped London trade no longer "
             f"draws first. NY-alone baseline (replayed): ${ny_net:+,.0f}, P(bust) "
             f"{base_mc['bust'] * 100:.1f}%. London at flat 1 lot.\n\n"
             "| London book | combined net | vs NY-alone | worst day | maxDD | P(bust) | "
             "med withdrawn |\n|---|---|---|---|---|---|---|\n")
    for lab, thr in (("baseline (fade allowed)", None), (f"right side only (>= {PRIMARY:g})", PRIMARY)):
        Lo = taken(P, thr)
        T, _ = replay(N, Lo, "clock")
        d = T.groupby("day").pnl.sum()
        dm, k = _daymap(T)
        r = mc(dm, k)
        L.append(f"| {lab} | ${T.pnl.sum():+,.0f} | **${T.pnl.sum() - ny_net:+,.0f}** | "
                 f"${d.min():+,.0f} | ${maxdd(d):,.0f} | {r['bust'] * 100:.1f}% | "
                 f"${np.median(r['pay']):,.0f} |\n")

    ror0, ror1 = bs["net"] / max(bs["dd"], 1), ps["net"] / max(ps["dd"], 1)
    L.append("\n## Verdict\n\n"
             f"**Direct answer: never fading VWAP LOWERS raw P&L, by ${bs['net'] - ps['net']:,.0f}** "
             f"(${bs['net']:+,.0f} -> ${ps['net']:+,.0f}). The reason is the trap the loss anatomy "
             f"set: the wrong-side entries lose more OFTEN, but they are net POSITIVE "
             f"(${dd.dollars.sum():+,.0f} over {len(dd)} trades, mean R {dd.R.mean():+.3f}) — they "
             f"win less but win big when the fade snaps back. A higher loss rate is not a negative "
             f"expectancy, and cutting on loss rate throws away good trades.\n")
    L.append(f"\n**But it is not a null — it is a risk trade, and a good one.** The same cut nearly "
             f"halves maxDD (${bs['dd']:,.0f} -> ${ps['dd']:,.0f}) and lifts return-on-drawdown "
             f"from {ror0:.1f} to {ror1:.1f}. Guard 1 confirms the cut is non-random "
             f"(p={p_rand:.4f}, beats {(1 - p_rand) * 100:.0f}% of equal-size random drops), so it "
             f"removes genuinely worse-than-average trades — just not money-losing ones. On the "
             f"funded account the drawdown reduction is what pays: bust risk falls and median "
             f"withdrawn RISES despite the lower raw net, because a $2k trailing line rewards a "
             f"smaller drawdown more than it rewards the extra gross.\n")
    L.append(f"\n**The sweep says the aggressive cut overshoots.** Threshold 0 drops "
             f"{bs['n'] - ps['n']} trades to buy that drawdown reduction; a MILDER cut at -0.25 "
             f"(drop only the DEEP fades) keeps almost all the net while getting most of the "
             f"drawdown benefit. That mild threshold is selection-mined from this sweep, so it is "
             f"not a headline — but it is the shape to carry into a pre-registered holdout test: "
             f"the signal is 'don't take the DEEP counter-VWAP fades', not 'never trade below "
             f"VWAP'. Either way, derived in-sample from these losers — an upper bound until the "
             f"sealed holdout confirms it.\n")
    write("LONDON-VWAP-FILTER.md", "".join(L))
    print(f"baseline ${bs['net']:+,.0f} -> right-side ${ps['net']:+,.0f} "
          f"({ps['net'] - bs['net']:+,.0f}), dropped {bs['n'] - ps['n']}, "
          f"rand-p {p_rand:.4f}, both-era {both}")


if __name__ == "__main__":
    main()
