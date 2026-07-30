#!/usr/bin/env python3
"""LONDON de-risk test — halve risk after a same-day realized loss. FIT ONLY.

THE ASK (Brake, 2026-07-30): "if you lose first trade then risk half on the next trade."
NY precedent exists (lucid spine soft de-risks to half at -$280 realized), and Angus's
London escalation instinct ("if it lost the first, the second needed extra conviction")
is the same idea expressed as a conviction bar instead of a size cut.

CAUSALITY, NON-NEGOTIABLE: 26/144 entries occur while a prior position is still open, so
"the first trade lost" is not always knowable at the next fill. Every rule below keys
ONLY on trades already EXITED before the candidate's fill time — what a live account
actually knows. An open first trade = no information = full size.

THE SIGNAL FIRST, THE RULE SECOND (burn list: price the cut, never assume it): halving
post-loss trades only beats flat if post-loss trades are WORSE than average. If their
expectancy is normal, the rule is a pure risk trade — less net for less DD — and should
be judged as one (the VWAP-filter lesson).

RULES PRICED (funded flat-$250 baseline from docs/LONDON-FUNDED-TEST.md, OVERLAY book):
  R1 LAST-LOSS   most recently exited same-day trade lost -> this trade $125; a win
                 restores $250 (loss-triggered, win-reset)
  R2 FIRST-LOSS  the day's FIRST trade exited as a loss before this fill -> $125 for
                 the REST of the day (the literal reading of the ask)
  R3 NY-STYLE    day's realized P&L at fill <= -$250 -> $125 (the lucid spine's shape)

Sizing stays flat live (ANGUS ruling); measurement for the post-holdout decision.

    python -m scripts.london_derisk_test
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
from scripts.london_funded_test import fund
from scripts.london_holdout_report import load_pop

RISK_D = 250.0


def states(b: pd.DataFrame) -> pd.DataFrame:
    """Per trade, the same-day realized state AT FILL TIME (exited trades only)."""
    t = b.sort_values(["day", "fill_ts"], kind="mergesort").reset_index(drop=True)
    f = pd.to_datetime(t.fill_ts, utc=True)
    x = pd.to_datetime(t.exit_ts, utc=True)
    last_loss = np.zeros(len(t), dtype=bool)     # most recently exited trade lost
    first_loss = np.zeros(len(t), dtype=bool)    # day's first trade exited as a loss
    real_pl = np.zeros(len(t))                   # realized 1-lot dollars at fill
    for day, g in t.groupby("day", sort=False):
        idx = list(g.index)
        first_i = idx[0]
        for i in idx:
            done = [j for j in idx if j != i and x[j] <= f[i]]
            if done:
                last_j = max(done, key=lambda j: x[j])
                last_loss[i] = t.at[last_j, "dollars"] <= 0
            first_loss[i] = (first_i != i and x[first_i] <= f[i]
                             and t.at[first_i, "dollars"] <= 0)
            real_pl[i] = sum(t.at[j, "dollars"] for j in done)
    t["last_loss"], t["first_loss"], t["real_pl"] = last_loss, first_loss, real_pl
    return t


def report(t: pd.DataFrame) -> dict:
    d = t.groupby("day").pl.sum()
    mo = t.assign(mo=t.day.astype(str).str[:7]).groupby("mo").pl.sum()
    out = {"n": len(t), "halved": int((t.risk_d < RISK_D).sum()),
           "net": float(t.pl.sum()), "dd": maxdd(t.pl.reset_index(drop=True)),
           "worst_day": float(d.min()), "green": int((mo > 0).sum()), "months": len(mo)}
    for era in ("2025", "2026"):
        g = t[t.era == era]
        out[era] = f"${g.pl.sum():+,.0f} / dd ${maxdd(g.pl.reset_index(drop=True)):,.0f}"
    return out


def row(name: str, r: dict) -> str:
    return (f"| {name} | {r['n']} | {r['halved']} | ${r['net']:+,.0f} | ${r['dd']:,.0f} | "
            f"${r['worst_day']:+,.0f} | {r['green']}/{r['months']} | {r['2025']} | "
            f"{r['2026']} |\n")


def main() -> None:
    P = load_pop("fit")
    P["mins"] = lonmins(P.fill)
    b = lon_book(P[P.mins < CUT_MIN], floor=9.5, lifetime=math.inf,
                 cap=999).reset_index(drop=True)
    t = states(b)

    L = ["# London de-risk test — half size after a same-day realized loss\n",
         "\n**FIT ONLY. Sealed untouched. Rules keyed on exited-before-fill outcomes "
         "only (what live knows). Sizing frozen live; measurement for the post-holdout "
         "decision.**\n"]

    L.append("\n## 1. The signal — are post-loss trades actually worse?\n\n"
             "| state at fill | n | WR | mean R | Wilson LB | 2025 | 2026 | grade |\n"
             "|---|---|---|---|---|---|---|---|\n")
    cells = [("no same-day realized loss", ~(t.last_loss | t.first_loss).values),
             ("last exited trade LOST (R1 trigger)", t.last_loss.values),
             ("day's first trade LOST (R2 trigger)", t.first_loss.values),
             ("realized P&L <= -$250 1-lot (R3-ish)", (t.real_pl <= -250).values)]
    for name, m in cells:
        c = era_cells(t, m)
        L.append(f"| {name} | {fmt_cell(c)} | {grade(c)} |\n")

    L.append("\n## 2. The rules, priced (funded flat $250 baseline; halved = $125)\n\n"
             "| rule | n | trades halved | net | maxDD | worst day | months green | "
             "2025 | 2026 |\n|---|---|---|---|---|---|---|---|---|\n")
    flat = fund(t, np.ones(len(t)))
    L.append(row("FLAT $250 (baseline)", report(flat)))
    for name, trig in [("R1 last-loss -> half, win resets", t.last_loss.values),
                       ("R2 first-loss -> half rest of day", t.first_loss.values),
                       ("R3 realized <= -$250 funded -> half", None)]:
        if name.startswith("R3"):
            # funded realized: recompute state on funded dollars (micros x d/10);
            # approximate with 1-lot realized scaled by the flat book's per-trade
            # funded/1-lot ratio at matched trades — states are per-day sums, so use
            # funded pl of exited trades directly
            ff = fund(t, np.ones(len(t)))
            xs = pd.to_datetime(ff.exit_ts, utc=True)
            fs = pd.to_datetime(ff.fill_ts, utc=True)
            trig = np.zeros(len(ff), dtype=bool)
            for day, g in ff.groupby("day", sort=False):
                for i in g.index:
                    done = [j for j in g.index if j != i and xs[j] <= fs[i]]
                    trig[i] = sum(ff.at[j, "pl"] for j in done) <= -250.0
        w = np.where(trig, 0.5, 1.0)
        L.append(row(name, report(fund(t, w))))

    L.append("\n## Read it\n\n"
             "- Judge each rule by what §1 says about its trigger cell: if the cell's "
             "expectancy is normal, the rule is a pure risk trade (less net, less DD) "
             "— legitimate as a RULING, but not an edge. If the cell is genuinely weak "
             "AND era-consistent, the rule earns its keep on expectancy too.\n"
             "- Angus's original instinct for slot 2 was a HIGHER CONVICTION BAR after "
             "a loss, not a size cut (L4 escalation, currently inactive at London "
             "threshold 1.0/1.0). If §1 shows post-loss weakness concentrated in "
             "low-conviction cells, the bar beats the haircut and both should go to "
             "the post-holdout table together.\n"
             "- All fit-side; trigger counts are small; era columns rule.\n")
    write("LONDON-DERISK-TEST.md", "".join(L))


if __name__ == "__main__":
    main()
