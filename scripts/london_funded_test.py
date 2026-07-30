#!/usr/bin/env python3
"""LONDON funded test — flat $250 risk per trade, MNQ micros, house sizing convention.

THE ASK (Brake, 2026-07-30): "funded testing... baseline of $250 risk per trade, match
micros accordingly." Sizing follows scripts/baseline_dollar_risk.py exactly:
    micros = min(40, round(risk_$ / (stop_pts * $2)))      # integer MNQ, $2/pt
    pl     = micros * dollars_1lot / 10                    # micro = 1/10 of the mini
with risk_$ = $250 flat. Cut@09:30 baseline (rev 3 draft), fit span, sealed untouched.

TWO BOOKS, BECAUSE THE DAY STOP HAS UNITS. The frozen selection applied the $400 day
stop to 1-NQ-LOT dollars (how the book was built). A funded account's Vault counts
FUNDED dollars. So:
  OVERLAY  = frozen 144-trade selection, funded sizing painted on top (selection
             untouched — comparable to every prior doc)
  REWALK   = same candidates, same L4 policy, but the $400 day-stop accumulator runs
             on funded dollars (the live-true book; composition may differ)
If they diverge materially, the day-stop unit becomes an ANGUS/Vault decision that
must be made BEFORE any funded deployment; it is flagged either way.

Ladder rows (wall / A+ at 1.5x/0.5x of $250 = $375/$125) are carried as the funded
version of docs/LONDON-CONFLUENCE-SIZING.md's declared candidates. Sizing remains
flat-1-lot-equivalent live until the holdout validates the book (ANGUS ruling) — this
doc measures, adopts nothing.

    python -m scripts.london_funded_test
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l4_select import L4Policy, select
from scripts.london_combined_job import lon_book, maxdd, write
from scripts.london_conviction import CUT_MIN, lonmins
from scripts.london_holdout_report import load_pop

SEED = 20260730
RISK_D = 250.0
NQ_PT = 20.0


def micros_for(risk_dollars: np.ndarray, stop_pts: np.ndarray) -> np.ndarray:
    return np.minimum(40, np.round(risk_dollars / (stop_pts * 2.0)).astype(int))


def fund(b: pd.DataFrame, weights: np.ndarray) -> pd.DataFrame:
    t = b.copy()
    t["stop_pts"] = t.risk.astype(float) / NQ_PT
    t["risk_d"] = weights * RISK_D
    t["micros"] = micros_for(t.risk_d.values, t.stop_pts.values)
    t["actual_risk"] = t.micros * t.stop_pts * 2.0
    t["pl"] = t.micros * t.dollars.astype(float) / 10.0
    return t


def report(t: pd.DataFrame) -> dict:
    t = t.sort_values(["day", "fill_ts"], kind="mergesort")
    d = t.groupby("day").pl.sum()
    mo = t.assign(mo=t.day.astype(str).str[:7]).groupby("mo").pl.sum()
    out = {"n": len(t), "net": float(t.pl.sum()), "dd": maxdd(t.pl.reset_index(drop=True)),
           "worst_day": float(d.min()), "best_day": float(d.max()),
           "green": int((mo > 0).sum()), "months": len(mo),
           "worst_mo": float(mo.min()),
           "avg_mi": float(t.micros.mean()), "mi_range": (int(t.micros.min()),
                                                          int(t.micros.max())),
           "avg_risk": float(t.actual_risk.mean()),
           "zero_mi": int((t.micros == 0).sum())}
    for era in ("2025", "2026"):
        g = t[t.era == era]
        out[era] = (f"${g.pl.sum():+,.0f} / dd ${maxdd(g.pl.reset_index(drop=True)):,.0f}"
                    if len(g) else "—")
    return out


def row(name: str, r: dict) -> str:
    return (f"| {name} | {r['n']} | ${r['net']:+,.0f} | ${r['dd']:,.0f} | "
            f"${r['worst_day']:+,.0f} | {r['green']}/{r['months']} | "
            f"${r['worst_mo']:+,.0f} | {r['avg_mi']:.1f} "
            f"({r['mi_range'][0]}-{r['mi_range'][1]}) | ${r['avg_risk']:,.0f} | "
            f"{r['2025']} | {r['2026']} |\n")


def main() -> None:
    P = load_pop("fit")
    P["mins"] = lonmins(P.fill)
    Pc = P[P.mins < CUT_MIN].copy()

    # OVERLAY: frozen selection, funded sizing on top
    b = lon_book(Pc, floor=9.5, lifetime=math.inf, cap=999).reset_index(drop=True)
    b["both"] = ((b.W == 1) & (b.FAR == 1)).values
    b["aplus"] = ((b.pattern == "B2").values & b.both.values)
    flat = fund(b, np.ones(len(b)))

    # REWALK: day stop accumulates on funded dollars during selection
    Q = Pc[Pc.risk >= 9.5].copy()
    Q["stop_pts"] = Q.risk.astype(float)          # population risk is POINTS pre-book
    Q["micros"] = micros_for(np.full(len(Q), RISK_D), Q.stop_pts.values)
    Q["pl_funded"] = Q.micros * Q.dollars.astype(float) / 10.0
    pol = L4Policy(threshold={"london": 1.0}, escalation_threshold={"london": 1.0},
                   cap_per_session=999, day_stop_dollars=400.0)
    rw = select(Q.assign(score=Q.wall), pol, dollars_col="pl_funded")
    rw = rw[rw.taken].copy()
    rw["risk"] = rw.stop_pts * NQ_PT
    rw_f = fund(rw.assign(risk=rw.risk), np.ones(len(rw)))

    L = ["# London funded test — flat $250 risk/trade, MNQ micros (cut@09:30 baseline)\n",
         "\n**FIT ONLY. Sealed untouched. Measurement for the funded lane — nothing "
         "deploys before the holdout + ANGUS sizing decision.** Sizing convention = "
         "`baseline_dollar_risk.py`: micros = min(40, round($250 / (stop_pts x $2))), "
         "pl = micros x dollars_1lot / 10.\n"]

    L.append("\n## The funded books\n\n"
             "| book | n | net | maxDD (trade) | worst day | months green | worst month "
             "| avg micros (range) | avg $ risk | 2025 | 2026 |\n"
             "|---|---|---|---|---|---|---|---|---|---|---|\n")
    r_flat, r_rw = report(flat), report(rw_f)
    L.append(row("OVERLAY flat $250 (frozen selection)", r_flat))
    L.append(row("REWALK flat $250 (day stop on funded $)", r_rw))
    for name, w in [("OVERLAY wall ladder $375/$125",
                     np.where(b.both, 1.5, 0.5)),
                    ("OVERLAY A+ ladder $375/$125",
                     np.where(b.aplus, 1.5, 0.5))]:
        L.append(row(name, report(fund(b, w))))

    same = (len(rw_f) == len(flat)
            and set(zip(rw_f.day, rw_f.fill)) == set(zip(flat.day, flat.fill)))
    L.append(f"\n**Day-stop unit check:** overlay and rewalk "
             f"{'are IDENTICAL — the $400 stop never binds differently at this sizing; '
                'no ruling needed on fit evidence' if same else
                'DIVERGE — the day-stop unit (1-lot vs funded dollars) changes the book '
                'and needs an ANGUS/Vault ruling before any funded deployment'}.\n")

    L.append("\n## Reference points\n\n"
             f"- 1-NQ-lot book (the prereg convention): +$21,801, maxDD $1,435, avg "
             f"risk/trade ${b.risk.mean():,.0f} (stop-dependent, ${b.risk.min():,.0f}-"
             f"${b.risk.max():,.0f}). The funded book risks a CONSTANT ~$250 — "
             "equal-dollar normalization shifts weight from wide-stop to tight-stop "
             "trades.\n"
             "- Prop-eval frame (50K / $2K trailing / $400 Vault day stop): maxDD and "
             "worst-day above are the binding numbers. Rounding to integer micros on "
             "a 9.5-60pt stop book means actual risk wobbles around $250 — the avg $ "
             "risk column states realized truth.\n"
             "- Ladder rows are the funded translation of the declared candidates in "
             "docs/LONDON-CONFLUENCE-SIZING.md; same evidence caveats apply "
             "(wall validated, A+ one rung more speculative).\n")
    write("LONDON-FUNDED-TEST.md", "".join(L))


if __name__ == "__main__":
    main()
