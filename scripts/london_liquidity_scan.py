#!/usr/bin/env python3
"""LONDON liquidity/extremes/bias scan — Brake's three loss-avoidance hypotheses. FIT ONLY.

THE ASK (Brake, 2026-07-30): "how to miss entering those losing trades — liquidity draws
from the heatmap, session highs or lows, then also daily bias." Three USER-DECLARED
mechanisms, stated before measurement — cleaner provenance than any mined candidate, and
they are tested exactly as declared, once, with the standard three bars:
era-consistency, profit-trap (vetoed net <= 0 in both eras), worst-of-K charge.

THE MECHANISMS, OPERATIONALIZED (all pre-entry observable):
  heatmap draw   dep_wall_*_d/sz ARE the heatmap (MBP-10 depth as-of fill). A wall
                 resting just BEYOND the stop is a magnet that pulls price through it:
                 LQ1 = wall behind exists AND its distance <= 2.0x stop.
                 LQ2 = wall behind exists at all (W==0; the gate lets these in via FAR).
  session pools  overnight extremes from ent_on_pos x on_range. A stop sitting IN FRONT
                 of the session-extreme pool gets swept with the pool:
                 SE1 = extreme behind the trade lies within (1.0x, 2.0x] stop — the stop
                 is between entry and the pool.
                 SE2 = extreme behind lies INSIDE the stop (<= 1.0x) — stop is beyond
                 the pool (the protected case; expected GOOD, printed as the control).
  daily bias     DB1 = counter-drift entry: long below the ON midpoint / short above it
                 (fading the overnight drift).
                 DB2 = htf_flag == counter_trend (the 15m flag; known 46% loss rate).

Working stack book (cut@09:30 + score-0 veto + one-at-a-time, 110 trades, 40 losers).
This is the LAST fit-side loss scan this dataset can support — n=40 losers is the whole
evidence pool; whatever fails here goes to forward data, not to a re-cut.

    python -m scripts.london_liquidity_scan
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import maxdd, write
from scripts.london_conviction import FLOOR_HYP, perm_max_null
from scripts.london_tf_conviction import serial_walk
from scripts.london_veto_scan import build_book, cell_line

SEED = 20260730
NQ_PT = 20.0


def main() -> None:
    rng = np.random.default_rng(SEED + 6)
    base = build_book()
    b = serial_walk(base[base.conv > 0]).reset_index(drop=True)
    long = b.direction.values == "long"
    stop_pts = (b.risk / NQ_PT).values

    # heatmap: wall behind the trade (below for longs, above for shorts)
    wall_behind_d = np.where(long, b.dep_wall_below_d, b.dep_wall_above_d)
    has_wall_behind = ~np.isnan(wall_behind_d)
    lq1 = has_wall_behind & (wall_behind_d <= 2.0 * stop_pts)
    lq2 = has_wall_behind.copy()

    # session pools: distance to the overnight extreme BEHIND the trade
    dist_behind = np.where(long, b.ent_on_pos, 1 - b.ent_on_pos) * b.on_range
    se1 = (dist_behind > 1.0 * stop_pts) & (dist_behind <= 2.0 * stop_pts)
    se2 = dist_behind <= 1.0 * stop_pts

    # daily bias
    db1 = np.where(long, b.ent_on_pos < 0.5, b.ent_on_pos > 0.5)
    db2 = (b.htf_flag == "counter_trend").values

    cands = [
        ("LQ1 wall behind within 2x stop (magnet)", lq1),
        ("LQ2 any wall behind (W==0)", lq2),
        ("SE1 stop in front of ON-extreme pool", se1),
        ("SE2 stop beyond the pool (control)", se2),
        ("DB1 counter overnight drift", db1.astype(bool)),
        ("DB2 htf counter_trend", db2),
    ]
    R, eras = b.R.values.astype(float), b.era.values
    M = np.column_stack([m.astype(float) for _, m in cands])
    null_max = perm_max_null(R, eras, M, rng)

    L = [f"# London liquidity / session-pool / bias scan — Brake's three hypotheses\n",
         f"\n**Working stack ({len(b)} trades, {int((b.R <= 0).sum())} losers). FIT "
         "ONLY. User-declared mechanisms, tested once as declared. Three bars: "
         "era-bad, profit-trap (net <= 0 both eras), worst-of-6 charge. This is the "
         "last fit-side loss scan this dataset supports.**\n",
         "\n| cell | n | WR | mean R | net | 2025 n/R/$ | 2026 n/R/$ | p(worst-of-6) | "
         "era-bad? | net<=0 both? | VERDICT |\n"
         "|---|---|---|---|---|---|---|---|---|---|---|\n"]
    verdicts = {}
    for name, m in cands:
        s, out = cell_line(b, m)
        lift = float(b[m].R.mean()) - float(b.R.mean()) if m.sum() else 0.0
        p = float((null_max >= abs(lift)).mean())
        era_bad = all(out[e]["r"] < float(b[b.era == e].R.mean())
                      for e in ("2025", "2026") if out[e]["n"] > 0)
        trap_ok = all(out[e]["net"] <= 0 for e in ("2025", "2026"))
        ok = era_bad and trap_ok and m.sum() >= FLOOR_HYP
        verdicts[name] = (m, ok)
        L.append(f"| {name} | {s} | {p:.3f} | {'Y' if era_bad else 'n'} | "
                 f"{'Y' if trap_ok else 'n'} | "
                 f"{'**VETO-GRADE**' if ok else 'fails'} |\n")

    surv = [(n, m) for n, (m, ok) in verdicts.items() if ok]
    if surv:
        L.append("\n## Pricing the survivors\n\n"
                 "| book | n | WR | mean R | net | maxDD |\n|---|---|---|---|---|---|\n")

        def prow(name, g):
            g = g.sort_values(["day", "fill_ts"], kind="mergesort")
            return (f"| {name} | {len(g)} | {(g.R > 0).mean() * 100:.0f}% | "
                    f"{g.R.mean():+.3f} | ${g.dollars.sum():+,.0f} | "
                    f"${maxdd(g.dollars.reset_index(drop=True)):,.0f} |\n")
        L.append(prow("working stack", b))
        stack = np.zeros(len(b), dtype=bool)
        for name, m in surv:
            L.append(prow(f"minus {name}", b[~m]))
            stack |= m
        if len(surv) > 1:
            L.append(prow("minus all survivors", b[~stack]))
    else:
        L.append("\n## No survivor\n\nNone of the three mechanisms produces a cell "
                 "that is bad in both eras AND removes negative money AND has n >= 10. "
                 "Whatever pattern is in the losers, these three lenses either do not "
                 "see it or see it only as the profit-trap shape (weak cells that "
                 "still net positive). All three go to the declared-priors table for "
                 "forward data as stated hypotheses with their fit numbers attached.\n")

    L.append("\n## Read it\n\n"
             "- Thresholds (2.0x stop, ON midpoint, 1.0x pool) are round declared "
             "numbers, untuned — moving them after seeing this table would convert a "
             "declared test into a mined one.\n"
             "- SE2 is the mechanical control: if SE1 (stop in front of the pool) is "
             "bad, SE2 (stop beyond it) should not be — a sign both are noise is both "
             "landing the same side.\n"
             "- n=40 losers total: only large effects can register; absence of a "
             "verdict is absence of PROOF, not absence of the mechanism.\n")
    write("LONDON-LIQUIDITY-SCAN.md", "".join(L))


if __name__ == "__main__":
    main()
