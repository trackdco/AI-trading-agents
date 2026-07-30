#!/usr/bin/env python3
"""LONDON ladder lab — conviction x calendar sizing variants at $200 base risk. FIT ONLY.

THE ASK (Brake, 2026-07-30): "mess around with a bunch of conviction setups — A+ 1.5x,
A+ on mon/fri 2x, bad setups at the worser times 0.5x, base size $200 stop loss."

GRADES (declared): A+ = B2 & both-wall (48/69%/+1.007 on the 144 book) · MID = both-wall
or B2 but not both · BASE = neither (the average trade, 55%/+0.214).
CALENDAR (declared from docs/LONDON-DOW-CHARACTER.md): good days = Mon/Fri (Mon is a
different market — 210pt weekend dislocation; Fri prints the best composition);
worser = Tue/Wed (weakest mean R days; Tuesday's non-A+ cell is junk 36%/-0.04).

THE HONESTY PROBLEM, STATED FIRST: the calendar cells were characterized TODAY on the
same fit data being priced, and weekday x grade cells hold 5-16 trades. The DOW doc's
own verdict was "no weekday rule warranted — grade the setup, not the calendar". So the
referee columns are: per-era net (a ladder must win in BOTH), and zero-edge net (same
weights on within-era outcome-shuffled trades — the risk-shuffling floor). A ladder
that only beats flat on the pooled column is noise wearing a costume.

Sizing: house convention, base $200 -> risk_$ = tier x $200, micros = min(40,
round(risk_$/(stop_pts x $2))), pl = micros x dollars_1lot/10. Book = working stack
(cut@09:30 + score-0 veto + one-at-a-time, 110 trades). Sizing frozen at flat live
(ANGUS ruling); declared candidates for the post-holdout table, nothing more.

    python -m scripts.london_ladder_lab
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import maxdd, write
from scripts.london_tf_conviction import serial_walk
from scripts.london_veto_scan import build_book

SEED = 20260730
N_PERM = 5000
BASE_D = 200.0
NQ_PT = 20.0


def main() -> None:
    base = build_book()
    b = serial_walk(base[base.conv > 0]).reset_index(drop=True)
    b["dow"] = pd.to_datetime(b.day).dt.day_name().str[:3]
    both = ((b.W == 1) & (b.FAR == 1)).values
    b2 = (b.pattern == "B2").values
    aplus = b2 & both
    mid = (b2 | both) & ~aplus
    neither = ~b2 & ~both
    goodday = b.dow.isin(["Mon", "Fri"]).values
    badday = b.dow.isin(["Tue", "Wed"]).values

    n = len(b)
    ladders = {
        "FLAT $200": np.ones(n),
        "L1  A+ 1.5 / neither 0.5": np.where(aplus, 1.5, np.where(neither, 0.5, 1.0)),
        "L2  +A+ Mon/Fri 2.0": np.where(aplus & goodday, 2.0,
                                        np.where(aplus, 1.5,
                                                 np.where(neither, 0.5, 1.0))),
        "L3  Brake spec (+neither Tue/Wed 0.5)":
            np.where(aplus & goodday, 2.0,
                     np.where(aplus, 1.5,
                              np.where(neither & badday, 0.5, 1.0))),
        "L4  full grade x day":
            np.where(aplus & goodday, 2.0,
                     np.where(aplus, 1.5,
                              np.where(neither, 0.5,
                                       np.where(mid & badday, 0.75, 1.0)))),
        "L5  calendar only (Mon/Fri 1.5, Tue/Wed 0.75)":
            np.where(goodday, 1.5, np.where(badday, 0.75, 1.0)),
        "L6  wall 1.5/0.5 (tier-test ref)": np.where(both, 1.5, 0.5),
    }

    stop_pts = (b.risk / NQ_PT).values
    d1lot = b.dollars.values.astype(float)
    eras = b.era.values
    i25, i26 = np.where(eras == "2025")[0], np.where(eras == "2026")[0]
    order = np.lexsort((b.fill_ts.values, b.day.values))

    L = [f"# London ladder lab — conviction x calendar at $200 base ({n} trades, "
         "working stack)\n",
         "\n**FIT ONLY. Referee columns: per-era net (must win BOTH) and zero-edge "
         "(risk-shuffling floor). Weekday tiers were characterized today on this same "
         "data — treat any calendar effect as unproven. Declared candidates only; "
         "sizing frozen at flat live (ANGUS ruling).**\n",
         f"\nGrade counts: A+ {int(aplus.sum())} · mid {int(mid.sum())} · neither "
         f"{int(neither.sum())}. Day counts: Mon/Fri {int(goodday.sum())} · Tue/Wed "
         f"{int(badday.sum())}.\n",
         "\n| ladder | net | 2025 | 2026 | maxDD | worst day | net/maxDD | "
         "avg $risk | zero-edge | real gain* |\n"
         "|---|---|---|---|---|---|---|---|---|---|\n"]

    rng = np.random.default_rng(SEED + 7)
    flat_net = flat_ze = None
    for name, w in ladders.items():
        risk_d = w * BASE_D
        micros = np.minimum(40, np.round(risk_d / (stop_pts * 2.0)).astype(int))
        pl = micros * d1lot / 10.0
        day_pl = pd.Series(pl).groupby(b.day.values).sum()
        ze = np.empty(N_PERM)
        dp = d1lot.copy()
        for k in range(N_PERM):
            dp[i25] = d1lot[i25][rng.permutation(len(i25))]
            dp[i26] = d1lot[i26][rng.permutation(len(i26))]
            ze[k] = (np.minimum(40, np.round(risk_d / (stop_pts * 2.0)).astype(int))
                     * dp / 10.0).sum()
        if flat_net is None:
            flat_net, flat_ze = pl.sum(), ze.mean()
        real_gain = (pl.sum() - flat_net) - (ze.mean() - flat_ze)
        eq = pd.Series(pl[order])
        L.append(f"| {name} | ${pl.sum():+,.0f} | ${pl[i25].sum():+,.0f} | "
                 f"${pl[i26].sum():+,.0f} | ${maxdd(eq):,.0f} | "
                 f"${day_pl.min():+,.0f} | {pl.sum() / max(maxdd(eq), 1):.1f} | "
                 f"${(micros * stop_pts * 2).mean():,.0f} | ${ze.mean():+,.0f} | "
                 f"${real_gain:+,.0f} |\n")

    L.append("\n(*real gain = (ladder net - flat net) - (ladder zero-edge - flat "
             "zero-edge): the part of the improvement that comes from outcomes "
             "aligning with the weights, not from deploying more risk. Zero-edge "
             "shuffles outcomes within era, 5,000x.)\n")

    L.append("\n## Read it\n\n"
             "- The A+ tier carries prior evidence one level down (wall: tier test "
             "p=0.0085; B2: era-consistent, unguarded). The CALENDAR tiers carry "
             "none — Mon/Fri outperformance was described today, on this data, and "
             "the DOW doc's own verdict was that the ladder should grade setups, not "
             "days. If L2/L3 beat L1 only via the calendar cells, treat that margin "
             "as the most fragile dollars in the table.\n"
             "- All ladders here deploy DIFFERENT total risk (base is absolute, per "
             "Brake's spec) — net/maxDD and real-gain are the comparable columns, "
             "raw net is not.\n"
             "- Nothing ships: flat 1-lot live until the holdout validates the book; "
             "this table is the declared menu for the post-holdout sizing decision.\n")
    write("LONDON-LADDER-LAB.md", "".join(L))


if __name__ == "__main__":
    main()
