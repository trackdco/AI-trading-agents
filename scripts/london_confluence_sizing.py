#!/usr/bin/env python3
"""LONDON confluence-based sizing — 1.5x high / 0.5x low, priced. FIT ONLY.

THE ASK (Brake, 2026-07-30): "test having the high confluence is 1.5x sizing, low
confluence 0.5." Two readings tested side by side, because "confluence" is overloaded:
  L-CONF   the literal cluster confluence_count (level TYPES stacked at entry — on this
           book it is binary: 2 vs 3)
  L-WALL   the tier test's validated axis (both W+FAR = 1.5, exactly-one = 0.5) — the
           order-flow reading of the same instinct
  L-APLUS  the A+ two-tier (B2 & both-wall = 1.5, everything else = 0.5)

All at MATCHED TOTAL RISK on the cut@09:30 baseline (144 trades), flat book risk as the
budget, so every row deploys identical dollars and only the allocation moves. Zero-edge
column = same weights on within-era outcome-shuffled trades (mean of 5000): the
risk-shuffling floor any ladder must clear before its gain means anything.

THE HEADLINE, KNOWN BEFORE PRICING (burn list #1 — pooled means hide era crossings):
confluence_count INVERTS across eras on this book. conf=3 ran 89%WR/+1.04R in 2025 and
52%/+0.36 in 2026; conf=2 ran 54%/+0.34 then 62%/+0.77. The 2025 and 2026 columns below
are therefore the verdict; the pooled column is the trap.

Sizing stays flat 1 lot live (standing ANGUS ruling) — this is measurement for the
post-holdout sizing decision, adopted nowhere.

    python -m scripts.london_confluence_sizing
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, maxdd, write
from scripts.london_conviction import CUT_MIN, era_cells, fmt_cell, grade, lonmins
from scripts.london_holdout_report import load_pop

SEED = 20260730
N_PERM = 5000


def main() -> None:
    P = load_pop("fit")
    P["mins"] = lonmins(P.fill)
    b = lon_book(P[P.mins < CUT_MIN], floor=9.5, lifetime=math.inf,
                 cap=999).reset_index(drop=True)
    b["both"] = ((b.W == 1) & (b.FAR == 1)).values
    b["aplus"] = ((b.pattern == "B2").values & b.both.values)

    L = ["# London confluence sizing — 1.5x/0.5x, three readings priced\n",
         "\n**FIT ONLY. Sealed span untouched. Sizing frozen at flat 1 lot live (ANGUS "
         "ruling); this doc measures, adopts nothing.**\n"]

    L.append("\n## The cells first (cut@09:30 baseline, 144 trades)\n\n"
             "| cell | n | WR | mean R | Wilson LB | 2025 | 2026 | grade |\n"
             "|---|---|---|---|---|---|---|---|\n")
    cells = [("confluence 3 (high)", (b.confluence_count == 3).values),
             ("confluence 2 (low)", (b.confluence_count == 2).values),
             ("both-wall", b.both.values),
             ("exactly-one wall", (~b.both).values),
             ("A+ (B2 & both-wall)", b.aplus.values),
             ("not A+", (~b.aplus).values)]
    for name, m in cells:
        c = era_cells(b, m)
        L.append(f"| {name} | {fmt_cell(c)} | {grade(c)} |\n")
    L.append("\n**confluence_count is an ERA CROSSING** — high-confluence was the best "
             "cell in 2025 (89%/+1.04) and a below-average cell in 2026 (52%/+0.36); "
             "low-confluence moved the other way. The same shape that rejected risk "
             "floor 5 (prereg §1). The wall and A+ axes do NOT cross.\n")

    # ---- ladders at matched risk
    risk = b.risk.values.astype(float)
    dollars = b.dollars.values.astype(float)
    total_risk = risk.sum()
    eras = b.era.values
    idx25, idx26 = np.where(eras == "2025")[0], np.where(eras == "2026")[0]
    order = np.lexsort((b.fill_ts.values, b.day.values))
    ladders = {
        "flat 1.0": np.ones(len(b)),
        "L-CONF 1.5 conf3 / 0.5 conf2": np.where(b.confluence_count == 3, 1.5, 0.5),
        "L-WALL 1.5 both / 0.5 one": np.where(b.both, 1.5, 0.5),
        "L-APLUS 1.5 A+ / 0.5 rest": np.where(b.aplus, 1.5, 0.5),
    }
    L.append("\n## Ladders at matched total risk (flat book risk = the budget)\n\n"
             "| ladder | net | 2025 net | 2026 net | maxDD (trade) | net/maxDD | "
             "zero-edge net |\n|---|---|---|---|---|---|---|\n")
    rng = np.random.default_rng(SEED + 3)
    flat_era = {}
    for name, w in ladders.items():
        wn = w * total_risk / (w * risk).sum()
        pnl = dollars * wn
        n25, n26 = pnl[idx25].sum(), pnl[idx26].sum()
        if name.startswith("flat"):
            flat_era = {"2025": n25, "2026": n26}
        ze = np.empty(N_PERM)
        dp = dollars.copy()
        for i in range(N_PERM):
            dp[idx25] = dollars[idx25][rng.permutation(len(idx25))]
            dp[idx26] = dollars[idx26][rng.permutation(len(idx26))]
            ze[i] = (dp * wn).sum()
        eq = pd.Series(pnl[order])
        d25 = f"${n25:+,.0f} ({n25 - flat_era['2025']:+,.0f})"
        d26 = f"${n26:+,.0f} ({n26 - flat_era['2026']:+,.0f})"
        L.append(f"| {name} | ${pnl.sum():+,.0f} | {d25} | {d26} | ${maxdd(eq):,.0f} | "
                 f"{pnl.sum() / max(maxdd(eq), 1):.1f} | ${ze.mean():+,.0f} |\n")
    L.append("\n(Parentheses = delta vs flat within the era, at identical deployed "
             "risk.)\n")

    L.append("\n## Verdict\n\n"
             "- **L-CONF fails the era test before it gets to pricing.** Whatever its "
             "pooled number, sizing up 3-type clusters is a 2025 trade that 2026 "
             "punished; the axis crosses eras, and the project's standing rule (the "
             "floor-5 precedent) is that era crossings are disqualifying, not "
             "averageable.\n"
             "- **L-WALL is the same instinct pointed at an axis that does not cross** "
             "— both-wall beats exactly-one in 2025 AND 2026, with prior tier-test "
             "evidence (permutation p=0.0085). If 'size the confluent trades bigger' "
             "becomes a rule post-holdout, THIS is its defensible form.\n"
             "- **L-APLUS concentrates harder** (adds the B2 requirement) at the cost "
             "of resting on an axis never guard-tested. Declared candidate, one rung "
             "more speculative than L-WALL.\n"
             "- Nothing here ships now: flat 1 lot until the holdout validates the "
             "book, then the sizing decision is made against these pre-declared "
             "numbers (prereg S2 is the declared descriptive input for the wall "
             "split).\n")
    write("LONDON-CONFLUENCE-SIZING.md", "".join(L))


if __name__ == "__main__":
    main()
