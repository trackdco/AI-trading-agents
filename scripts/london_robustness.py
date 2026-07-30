#!/usr/bin/env python3
"""LONDON robustness suite — cost stress, eval survival, parameter perturbation.

THE ASK (Brake, 2026-07-30): the three tests that can only make the numbers worse.
No alpha is searched for here; nothing in this file can flatter the strategy. FIT
ONLY, sealed untouched.

  1. COST STRESS. Baseline already charges 1 tick/side slippage (4 near news) and
     $2.50/contract/side commission inside the engine. Stress adds MORE: +1/+2/+4
     ticks per side as a linear overlay on both books (V8 stack and V1 stack, 1 NQ
     lot: extra cost = ticks x $5 x 2 sides). APPROXIMATION: overlay does not re-walk
     the day-stop path (costs would trip it marginally sooner — the overlay is
     slightly KIND on that one margin; everything else is adverse).

  2. MONTE CARLO EVAL SURVIVAL. Funded flat-$200 micros day P&L (zero on no-trade
     sessions), iid bootstrap over all fit sessions, 10,000 paths: 50K account,
     bust = day-end equity <= running peak - $2,000 (trailing), pass = +$3,000
     (the Spec-4 eval frame from context/next-tasks.md). Caveat: iid resampling
     destroys any day-to-day autocorrelation; fit clustering was measured benign
     (max streak 4, 5 multi-loss days/80) so iid is close, and it is the declared
     convention of the combined job's stage 4.

  3. PARAMETER PERTURBATION. One frozen knob at a time, one step each way, V8
     outcomes: risk floor {8.5, 9.5, 10.5}pt, window cut {09:15, 09:30, 09:45},
     veto thresholds x{0.9, 1.0, 1.1}. Verdict sought: PLATEAU (graceful) vs CLIFF
     (knife-edge = curve-fit). Not a search — the frozen values do not move on
     anything here.

    python -m scripts.london_robustness
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
from scripts.london_conviction import lonmins
from scripts.london_holdout_report import load_pop
from scripts.london_mgmt_tournament import swap_outcomes, stack
from scripts.london_tf_conviction import serial_walk

SEED = 20260730
N_PATHS = 10_000
START, TRAIL, TARGET = 50_000.0, 2_000.0, 3_000.0
MAX_DAYS = 250
TICK_D = 5.0                     # $/tick, 1 NQ lot
NQ_PT = 20.0


def fund200(b: pd.DataFrame) -> pd.Series:
    stop_pts = (b.risk / NQ_PT).values
    micros = np.minimum(40, np.round(200.0 / (stop_pts * 2.0)).astype(int))
    pl = micros * b.dollars.values / 10.0
    return pd.Series(pl, index=b.day.values)


def mc(day_pl: pd.Series, all_days: int, rng) -> dict:
    pool = np.zeros(all_days)
    grouped = day_pl.groupby(level=0).sum()
    pool[:len(grouped)] = grouped.values          # traded days; rest stay $0
    bust = passed = 0
    days_to = []
    for _ in range(N_PATHS):
        eq = peak = 0.0
        for d in range(MAX_DAYS):
            eq += pool[rng.integers(0, all_days)]
            peak = max(peak, eq)
            if eq <= peak - TRAIL:
                bust += 1
                break
            if eq >= TARGET:
                passed += 1
                days_to.append(d + 1)
                break
        else:
            pass                                   # unresolved inside MAX_DAYS
    return {"bust": bust / N_PATHS, "pass": passed / N_PATHS,
            "med_days": int(np.median(days_to)) if days_to else -1}


def main() -> None:
    rng = np.random.default_rng(SEED + 8)
    P8 = load_pop("fit")
    P8["mins"] = lonmins(P8.fill)
    P8["exit_ts"] = pd.to_datetime(P8["exit"], format="mixed", utc=True)
    b8c = lon_book(P8[P8.mins < 570], floor=9.5, lifetime=math.inf,
                   cap=999).reset_index(drop=True)
    thr = {f: float(np.nanmedian(b8c[f].astype(float)))
           for f in ("dep_thick", "dep_resist", "trigdens_30")}
    v8 = stack(P8, thr)
    v1 = stack(swap_outcomes(P8, "output/l2_outcomes_london_fit_v1.parquet"), thr)
    n_sessions = P8.day.nunique()

    L = ["# London robustness — cost stress, eval survival, perturbation\n",
         "\n**FIT ONLY. Nothing here can flatter the strategy; every test is "
         "adverse or neutral. Frozen values do not move on any result below.**\n"]

    # ---------------- 1. cost stress
    L.append("\n## 1. Cost stress (on top of the engine's 1 tick/side + $2.50/side "
             "already charged)\n\n"
             "| extra slippage | V8 stack net | V8 mean R | V1 stack net | V1 mean R "
             "|\n|---|---|---|---|---|\n")
    for ticks in (0, 1, 2, 4):
        rows = []
        for b in (v8, v1):
            cost = ticks * TICK_D * 2
            net = b.dollars.sum() - cost * len(b)
            r = (b.dollars - cost) / (b.risk * NQ_PT / NQ_PT)   # risk already $
            rows.append((net, ((b.dollars - cost) / b.risk).mean()))
        L.append(f"| +{ticks} tick/side | ${rows[0][0]:+,.0f} | {rows[0][1]:+.3f} | "
                 f"${rows[1][0]:+,.0f} | {rows[1][1]:+.3f} |\n")
    be_n = int((v1.exit_reason == "be_stop").sum())
    L.append(f"\nV1-specific exposure: {be_n} BE-stop exits — each extra tick/side "
             f"turns a $0 scratch into -${2 * TICK_D:.0f}/tick; that cost is inside "
             "the V1 column. Doubling commissions adds another "
             f"-${2.5 * 2 * len(v1):,.0f} to either book.\n")

    # ---------------- 2. MC eval survival
    L.append("\n## 2. Monte Carlo eval survival — 50K / $2K trailing / +$3K target, "
             f"$200 flat micros, {N_PATHS:,} paths x {n_sessions} session pool\n\n"
             "| book | P(bust) | P(pass) | median days to pass |\n|---|---|---|---|\n")
    for name, b in (("V8 stack", v8), ("V1 stack", v1)):
        r = mc(fund200(b), n_sessions, rng)
        L.append(f"| {name} | **{r['bust'] * 100:.1f}%** | {r['pass'] * 100:.1f}% | "
                 f"{r['med_days']} |\n")
    L.append("\n(iid day bootstrap — declared convention of the combined job; fit "
             "clustering was measured benign. Unresolved-in-250-days paths count in "
             "neither column.)\n")

    # ---------------- 3. perturbation
    L.append("\n## 3. Parameter perturbation — one knob, one step, V8 outcomes\n\n"
             "| knob | setting | n | mean R | net |\n|---|---|---|---|---|\n")

    def stk(P, cut=570, floor=9.5, scale=1.0):
        Pc = P[P.mins < cut]
        b = lon_book(Pc, floor=floor, lifetime=math.inf, cap=999).reset_index(drop=True)
        b["both_wall"] = ((b.W == 1) & (b.FAR == 1)).astype(int)
        conv = b.both_wall.copy()
        for f, t in thr.items():
            conv = conv + (b[f] > t * scale).astype(int)
        b["conv"] = conv
        return serial_walk(b[b.conv > 0]).reset_index(drop=True)

    grids = [("risk floor", [("8.5pt", {"floor": 8.5}), ("9.5pt *", {}),
                             ("10.5pt", {"floor": 10.5})]),
             ("window cut", [("09:15", {"cut": 555}), ("09:30 *", {}),
                             ("09:45", {"cut": 585})]),
             ("veto thresholds", [("x0.9", {"scale": 0.9}), ("x1.0 *", {}),
                                  ("x1.1", {"scale": 1.1})])]
    for knob, settings in grids:
        for label, kw in settings:
            g = stk(P8, **kw)
            L.append(f"| {knob} | {label} | {len(g)} | {g.R.mean():+.3f} | "
                     f"${g.dollars.sum():+,.0f} |\n")
    L.append("\n(* = frozen value. PLATEAU = neighbors within ~15% of the frozen "
             "net; a CLIFF anywhere is a curve-fit warning to report, not tune "
             "away.)\n")
    write("LONDON-ROBUSTNESS.md", "".join(L))


if __name__ == "__main__":
    main()
