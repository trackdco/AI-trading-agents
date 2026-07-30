#!/usr/bin/env python3
"""Monte Carlo eval survival — the FULL candidate config (V1 + Brake ladder @ 09:45).

Config under test (all declared candidates, nothing adopted live): window 08:00-09:45,
wall gate, score-0 veto, one-position-at-a-time, V1 (BE at +1R, structure targets),
$200 base with 1.5x on Mon/Fri A+ and 0.5x on neither-grade. Fit: +$23,222 / maxDD
$842. Same eval frame and honesty ladder as docs/LONDON-MC-EVAL.md: 50K / $2,000
trailing / +$3,000 target, 10,000 iid paths over all fit sessions, full / half / zero
edge. FIT ONLY.

    python -m scripts.london_mc_ladder
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, maxdd, write
from scripts.london_conviction import lonmins
from scripts.london_holdout_report import load_pop
from scripts.london_mc_eval import run_mc, stack
from scripts.london_mgmt_tournament import swap_outcomes
import math

SEED = 20260730
NQ_PT = 20.0


def main() -> None:
    rng = np.random.default_rng(SEED + 11)
    P = load_pop("fit")
    P["mins"] = lonmins(P.fill)
    P["exit_ts"] = pd.to_datetime(P["exit"], format="mixed", utc=True)
    b0 = lon_book(P[P.mins < 570], floor=9.5, lifetime=math.inf,
                  cap=999).reset_index(drop=True)
    thr = {f: float(np.nanmedian(b0[f].astype(float)))
           for f in ("dep_thick", "dep_resist", "trigdens_30")}
    b = stack(swap_outcomes(P, "output/l2_outcomes_london_fit_v1.parquet"), thr)

    aplus = ((b.pattern == "B2") & (b.W == 1) & (b.FAR == 1)).values
    neither = ((b.pattern != "B2") & ~((b.W == 1) & (b.FAR == 1))).values
    goodday = pd.to_datetime(b.day).dt.day_name().str[:3].isin(["Mon", "Fri"]).values
    w = np.where(aplus & goodday, 1.5, np.where(neither, 0.5, 1.0))
    stop = (b.risk / NQ_PT).values
    micros = np.minimum(40, np.round(w * 200.0 / (stop * 2.0)).astype(int))
    pl = pd.Series(micros * b.dollars.values / 10.0, index=b.day.values)

    n_sessions = P.day.nunique()
    grouped = pl.groupby(level=0).sum()
    pool = np.zeros(n_sessions)
    pool[:len(grouped)] = grouped.values
    traded = pool[:len(grouped)]
    mu = traded.mean()

    L = ["# Monte Carlo — full candidate config (V1 + Brake ladder @ 09:45)\n",
         f"\n**{len(b)} trades, funded net ${pl.sum():+,.0f}, funded maxDD "
         f"${maxdd(pl.reset_index(drop=True)):,.0f} · 50K / $2,000 trailing / "
         f"+$3,000 target · 10,000 paths x {n_sessions} sessions. FIT ONLY — the "
         "holdout owns whether the edge is real.**\n",
         "\n| scenario | P(bust) | P(pass) | days to pass (q25/med/q75) | "
         "path maxDD med / p95 / p99 |\n|---|---|---|---|---|\n"]
    for scen, shift in (("full edge", 0.0), ("half edge", mu * 0.5),
                        ("zero edge", mu)):
        p = pool.copy()
        p[:len(grouped)] = traded - shift
        r = run_mc(p, rng)
        L.append(f"| {scen} | **{r['bust'] * 100:.1f}%** | {r['pass'] * 100:.1f}% | "
                 f"{r['d25']:.0f}/{r['d50']:.0f}/{r['d75']:.0f} | "
                 f"${r['dd50']:,.0f} / ${r['dd95']:,.0f} / ${r['dd99']:,.0f} |\n")
    L.append("\nReference (flat $200, V1 @ 09:45): 0.2% / 18.8% / 74.3% bust across "
             "the same ladder (docs/LONDON-MC-EVAL.md).\n")
    write("LONDON-MC-LADDER.md", "".join(L))


if __name__ == "__main__":
    main()
