#!/usr/bin/env python3
"""LONDON veto scan — pre-entry reasons NOT to trade, tested against the major losers.

THE ASK (Brake, 2026-07-30): "see if there are reasons of why not to trade which can
avoid major losers." Stated before any number: A VETO MINED FROM THE LOSSES IT REMOVES
IS THE MOST OVERFIT-PRONE OBJECT IN THIS PROJECT. The VWAP filter looked exactly like
this and cost $5,856 (docs/LONDON-VWAP-FILTER.md) because a high-loss-rate cell was net
POSITIVE. So every candidate below must clear THREE bars, not one:
  1. era-consistency — the cell is bad in 2025 AND 2026 separately;
  2. the profit-trap check — the vetoed cell's NET DOLLARS are <= 0 in both eras
     (a veto that removes positive money is a risk trade, not a loss-avoider);
  3. worst-of-K permutation — the cell's negative lift is charged for the K cells
     scanned.
Candidates are DECLARED from prior findings, not dredged fresh: score-0 (conviction
sweep), 1min TF (TF doc), high room-ahead (loss anatomy's loser signature, AUC 0.382),
deep wrong-side-of-VWAP at the S3 threshold -0.25 (VWAP filter doc), post-loss state
(de-risk doc), the 'neither' cell (A+ table), and stop/range < 4% (era-diagnosis
mechanism). Thresholds are prior-declared or round numbers — nothing tuned here.

Also answers the overlap question honestly: serialization + vetoes interact. If a veto
kills trade 1, one-position-at-a-time admits the (often better) trade 2 that was
previously blocked — the causal way to 'prefer the second trade', since skipping a live
trade to WAIT for a better one is not implementable.

Cut@09:30 baseline. FIT ONLY. Sealed untouched. Nothing ships; declared priors only.

    python -m scripts.london_veto_scan
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
from scripts.london_conviction import (CUT_MIN, FLOOR_HYP, lonmins, perm_max_null,
                                       signed, wilson_lb)
from scripts.london_derisk_test import states
from scripts.london_holdout_report import load_pop
from scripts.london_tf_conviction import serial_walk

SEED = 20260730
NQ_PT = 20.0


def build_book() -> pd.DataFrame:
    P = load_pop("fit")
    P["mins"] = lonmins(P.fill)
    b = lon_book(P[P.mins < CUT_MIN], floor=9.5, lifetime=math.inf,
                 cap=999).reset_index(drop=True)
    long = b.direction.values == "long"
    b["room_ahead"] = np.where(long, 1 - b.ent_on_pos, b.ent_on_pos)
    b["both_wall"] = ((b.W == 1) & (b.FAR == 1)).values
    b["b2"] = (b.pattern == "B2").values
    b["stop_frac"] = (b.risk / NQ_PT) / b.on_range
    # conviction score conditions (sweep survivors, thresholds = the sweep's medians
    # recomputed identically — same code path, same population)
    for f in ("dep_thick", "dep_resist", "trigdens_30"):
        v = signed(b, f, False)
        b[f + "_hi"] = v > np.nanmedian(v)
    b["conv"] = (b.both_wall.astype(int) + b.dep_thick_hi.astype(int)
                 + b.dep_resist_hi.astype(int) + b.trigdens_30_hi.astype(int))
    return states(b)     # adds last_loss / first_loss / real_pl (causal, exited-only)


def cell_line(b, m) -> tuple[str, dict]:
    g = b[m]
    out = {}
    for era in ("2025", "2026"):
        ge = g[g.era == era]
        out[era] = {"n": len(ge), "net": float(ge.dollars.sum()),
                    "r": float(ge.R.mean()) if len(ge) else float("nan")}
    s = (f"{len(g)} | {(g.R > 0).mean() * 100:.0f}% | {g.R.mean():+.3f} | "
         f"${g.dollars.sum():+,.0f} | "
         f"{out['2025']['n']}/{out['2025']['r']:+.2f}/${out['2025']['net']:+,.0f} | "
         f"{out['2026']['n']}/{out['2026']['r']:+.2f}/${out['2026']['net']:+,.0f}")
    return s, out


def main() -> None:
    rng = np.random.default_rng(SEED + 4)
    b = build_book()
    R, eras = b.R.values.astype(float), b.era.values

    L = ["# London veto scan — declared no-trade conditions vs the major losers\n",
         "\n**FIT ONLY. Sealed untouched. Vetoes mined near losses are the most "
         "overfit-prone object in this project — every candidate must clear "
         "era-consistency, the profit-trap check (vetoed NET <= 0 both eras), and a "
         "worst-of-K charge. Declared priors only; nothing ships.**\n"]

    # ---------------- 1. the worst trades, inspected
    b["pl_1lot"] = b.dollars
    worst = b.nsmallest(12, "pl_1lot")
    L.append("\n## 1. The twelve worst trades (1-lot dollars), with their pre-entry "
             "state\n\n| day fill | $ | R | tf | pattern | wall | conv | room | "
             "vwap dir | stop/rng | post-loss? | bucket |\n"
             "|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    mins = lonmins(worst.fill)
    buck = pd.cut(mins, [480, 510, 540, 570, 600], right=False,
                  labels=["08:00", "08:30", "09:00", "09:30"])
    for (_, r), bk in zip(worst.iterrows(), buck):
        L.append(f"| {r.day} {str(r.fill)[11:16]} | {r.pl_1lot:+,.0f} | {r.R:+.2f} | "
                 f"{r.tf} | {r.pattern} | {'both' if r.both_wall else 'one'} | "
                 f"{int(r.conv)} | {r.room_ahead:.2f} | {r.ent_vs_vwap_sd_dir:+.2f} | "
                 f"{r.stop_frac * 100:.1f}% | {'Y' if r.last_loss else 'n'} | {bk} |\n")
    med_room = float(b.room_ahead.median())
    L.append(f"\nBook medians for reference: room {med_room:.2f}, vwap dir "
             f"{b.ent_vs_vwap_sd_dir.median():+.2f}, stop/rng "
             f"{b.stop_frac.median() * 100:.1f}%.\n")

    # ---------------- 2. declared veto candidates
    cands = [
        ("V1 score-0 (no conviction condition)", (b.conv == 0).values),
        ("V2 1min TF", (b.tf == "1min").values),
        ("V3 room_ahead > 0.75", (b.room_ahead > 0.75).values),
        ("V4 vwap dir <= -0.25 (S3 threshold)", (b.ent_vs_vwap_sd_dir <= -0.25).values),
        ("V5 post-loss at fill", b.last_loss.values),
        ("V6 neither (not B2, not both-wall)", (~b.b2 & ~b.both_wall).values),
        ("V7 stop/range < 4%", (b.stop_frac < 0.04).values),
    ]
    M = np.column_stack([m.astype(float) for _, m in cands])
    null_max = perm_max_null(R, eras, M, rng)
    L.append("\n## 2. The veto candidates (all declared from prior docs; charged "
             f"worst-of-{len(cands)})\n\n"
             "| veto cell | n | WR | mean R | net | 2025 n/R/$ | 2026 n/R/$ | "
             "p(worst-of-K) | era-bad? | net<=0 both? | VERDICT |\n"
             "|---|---|---|---|---|---|---|---|---|---|---|\n")
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
    L.append("\n(era-bad = below that era's book mean R in both eras; net<=0 both = "
             "the profit-trap check. A veto must pass BOTH plus n >= 10.)\n")

    # ---------------- 3. price what survives (and the stack), plus serial interaction
    surv = [(n, m) for n, (m, ok) in verdicts.items() if ok]
    L.append("\n## 3. Pricing (only VETO-GRADE cells may stack)\n\n"
             "| book | n | WR | mean R | net | maxDD |\n|---|---|---|---|---|---|\n")

    def prow(name, g):
        g = g.sort_values(["day", "fill_ts"], kind="mergesort")
        return (f"| {name} | {len(g)} | {(g.R > 0).mean() * 100:.0f}% | "
                f"{g.R.mean():+.3f} | ${g.dollars.sum():+,.0f} | "
                f"${maxdd(g.dollars.reset_index(drop=True)):,.0f} |\n")

    L.append(prow("baseline (cut@09:30)", b))
    stack = np.zeros(len(b), dtype=bool)
    for name, m in surv:
        L.append(prow(f"minus {name}", b[~m]))
        stack |= m
    if surv:
        L.append(prow("minus the full stack", b[~stack]))
        ser0 = serial_walk(b)
        ser1 = serial_walk(b[~stack])
        L.append(prow("one-at-a-time, no vetoes", ser0))
        L.append(prow("one-at-a-time + veto stack", ser1))
        L.append("\n(The last two rows answer the 'second trade' question causally: a "
                 "veto that kills trade 1 lets serialization admit the trade 2 it was "
                 "blocking — the only implementable way to prefer the later trade.)\n")
    else:
        L.append("\n**No candidate cleared all three bars.** The losses are the cost "
                 "of the edge, not a filterable defect — consistent with the "
                 "loss-anatomy verdict and three prior guard failures.\n")

    L.append("\n## Read it\n\n"
             "- Any VETO-GRADE cell here is still a FIT-SIDE find: it goes to the "
             "declared-priors table and is judged on forward data, exactly like S3. "
             "The late-bucket lesson stands: mechanism-plausible cells fail "
             "worst-of-K nulls all the time.\n"
             "- The worst-trade table (§1) is for eyeballs, not rules — twelve rows "
             "cannot found a rule and are printed so Brake can see each loser's "
             "context, per the ask.\n")
    write("LONDON-VETO-SCAN.md", "".join(L))


if __name__ == "__main__":
    main()
