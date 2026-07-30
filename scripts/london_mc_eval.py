#!/usr/bin/env python3
"""LONDON Monte Carlo eval survival — rev-3 baseline (cut@09:45), $200 micros.

Brake ruling 2026-07-30 (the LAST window move on fit evidence, third-look disclosure
in docs/LONDON-REV3-BASELINE.md): window 08:00-09:45. Stack = cut@09:45 + score-0
veto (thresholds frozen at the previously declared numbers) + one-position-at-a-time.

EVAL FRAME (context/next-tasks.md, Spec-4): 50K account, $2,000 trailing drawdown on
day-end equity, +$3,000 target, $200 flat risk in MNQ micros. 10,000 iid bootstrap
paths over ALL fit sessions (no-trade days draw $0).

THREE EDGE SCENARIOS, because P(bust) at full fit edge is mostly a compliment:
  full edge   day P&L drawn as measured
  half edge   each traded day's P&L shifted down by half the traded-day mean —
              "the holdout comes back at half strength"
  zero edge   traded days fully demeaned — pure risk-of-ruin of the RISK PROFILE

FIT ONLY (the pools are fit outcomes); the scenarios are the honesty ladder.

    python -m scripts.london_mc_eval
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
from scripts.london_mgmt_tournament import swap_outcomes
from scripts.london_tf_conviction import serial_walk

SEED = 20260730
N_PATHS = 10_000
TRAIL, TARGET = 2_000.0, 3_000.0
MAX_DAYS = 250
NQ_PT = 20.0
CUT = 585                                       # 09:45 London — rev-3 ruling
THR = {"dep_thick": None, "dep_resist": None, "trigdens_30": None}  # frozen below


def stack(P: pd.DataFrame, thr: dict) -> pd.DataFrame:
    b = lon_book(P[P.mins < CUT], floor=9.5, lifetime=math.inf,
                 cap=999).reset_index(drop=True)
    conv = ((b.W == 1) & (b.FAR == 1)).astype(int)
    for f, t in thr.items():
        conv = conv + (b[f] > t).astype(int)
    return serial_walk(b[conv > 0].assign(conv=conv[conv > 0])).reset_index(drop=True)


def fund200(b: pd.DataFrame) -> pd.Series:
    stop_pts = (b.risk / NQ_PT).values
    micros = np.minimum(40, np.round(200.0 / (stop_pts * 2.0)).astype(int))
    return pd.Series(micros * b.dollars.values / 10.0, index=b.day.values)


def run_mc(pool: np.ndarray, rng) -> dict:
    bust = passed = 0
    days_to, path_dd = [], []
    for _ in range(N_PATHS):
        eq = peak = 0.0
        worst = 0.0
        for d in range(MAX_DAYS):
            eq += pool[rng.integers(0, len(pool))]
            peak = max(peak, eq)
            worst = max(worst, peak - eq)
            if eq <= peak - TRAIL:
                bust += 1
                break
            if eq >= TARGET:
                passed += 1
                days_to.append(d + 1)
                break
        path_dd.append(worst)
    dt = np.array(days_to) if days_to else np.array([np.nan])
    return {"bust": bust / N_PATHS, "pass": passed / N_PATHS,
            "d50": float(np.nanmedian(dt)), "d25": float(np.nanpercentile(dt, 25)),
            "d75": float(np.nanpercentile(dt, 75)),
            "dd50": float(np.percentile(path_dd, 50)),
            "dd95": float(np.percentile(path_dd, 95)),
            "dd99": float(np.percentile(path_dd, 99))}


def main() -> None:
    rng = np.random.default_rng(SEED + 9)
    P = load_pop("fit")
    P["mins"] = lonmins(P.fill)
    P["exit_ts"] = pd.to_datetime(P["exit"], format="mixed", utc=True)
    # frozen veto thresholds — the originally declared numbers (09:30-book medians),
    # kept as ABSOLUTE values under rev 3 (perturbation showed +/-10% is flat)
    b0 = lon_book(P[P.mins < 570], floor=9.5, lifetime=math.inf,
                  cap=999).reset_index(drop=True)
    thr = {f: float(np.nanmedian(b0[f].astype(float)))
           for f in ("dep_thick", "dep_resist", "trigdens_30")}

    n_sessions = P.day.nunique()
    books = {"V8 @ 09:45": stack(P, thr),
             "V1 BE@1R @ 09:45": stack(
                 swap_outcomes(P, "output/l2_outcomes_london_fit_v1.parquet"), thr)}

    L = ["# London Monte Carlo eval survival — rev-3 baseline (cut@09:45)\n",
         "\n**50K / $2,000 trailing / +$3,000 target · $200 flat micros · "
         f"{N_PATHS:,} paths over {n_sessions} fit sessions (no-trade days = $0). "
         "Edge scenarios are the honesty ladder: full = fit as measured; half = "
         "traded days shifted down by half their mean; zero = fully demeaned "
         "(risk profile only).**\n"]
    for name, b in books.items():
        b = b.sort_values(["day", "fill_ts"])
        f = fund200(b)
        grouped = f.groupby(level=0).sum()
        pool = np.zeros(n_sessions)
        pool[:len(grouped)] = grouped.values
        traded = pool[:len(grouped)]
        mu = traded.mean()
        L.append(f"\n## {name} — {len(b)} trades, funded net "
                 f"${f.sum():+,.0f}, funded maxDD "
                 f"${maxdd(pd.Series(fund200(b).values)):,.0f}\n\n"
                 "| scenario | P(bust) | P(pass) | days to pass (q25/med/q75) | "
                 "path maxDD med / p95 / p99 |\n|---|---|---|---|---|\n")
        for scen, shift in (("full edge", 0.0), ("half edge", mu * 0.5),
                            ("zero edge", mu)):
            p = pool.copy()
            p[:len(grouped)] = traded - shift
            r = run_mc(p, rng)
            L.append(f"| {scen} | **{r['bust'] * 100:.1f}%** | "
                     f"{r['pass'] * 100:.1f}% | {r['d25']:.0f}/{r['d50']:.0f}/"
                     f"{r['d75']:.0f} | ${r['dd50']:,.0f} / ${r['dd95']:,.0f} / "
                     f"${r['dd99']:,.0f} |\n")
    L.append("\n(Unresolved-in-250-day paths count in neither bust nor pass. iid "
             "bootstrap — fit clustering measured benign. Zero-edge P(bust) is the "
             "price of TRYING the eval if the edge is illusory; half-edge is the "
             "declared-shrinkage world. All pools are fit outcomes — the holdout "
             "still owns the question of whether the edge is real.)\n")
    write("LONDON-MC-EVAL.md", "".join(L))


if __name__ == "__main__":
    main()
