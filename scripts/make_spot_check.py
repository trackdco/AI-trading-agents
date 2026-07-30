#!/usr/bin/env python3
"""Generate the Angus spot-check sheet — the human calibration pass for London.

The February hand-log calibration did this for NY: a human eyeballs mechanical trades
on a chart and rules "my setup" or "detector drift". London's rebuild never got its
own pass. This sheet = 10 seeded-random trades from the rev-3 stack + the 12 worst
1-lot losers, with everything needed to find each on a TradingView chart: date, fill
time in ET AND London, direction, entry/stop/target prices, TF, pattern, wall state,
conviction conditions, and both managements' outcomes. FIT ONLY.

    python -m scripts.make_spot_check
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import write
from scripts.london_holdout_report import build_book, load_pop, swap_v1

SEED = 20260730


def row(t, v1_map) -> str:
    f_et = pd.to_datetime(t.fill_ts, utc=True).tz_convert("America/New_York")
    f_lon = pd.to_datetime(t.fill_ts, utc=True).tz_convert("Europe/London")
    v1 = v1_map.get((t.ts, t.tf, t.direction), ("?", float("nan")))
    conds = []
    if t.W == 1 and t.FAR == 1:
        conds.append("both walls")
    elif t.W == 1 or t.FAR == 1:
        conds.append("one wall")
    return (f"| {t.day} | {f_et.strftime('%H:%M')} ET / {f_lon.strftime('%H:%M')} UK | "
            f"{t.direction} | {t.tf} | {t.pattern} | {t.entry:.2f} | {t.stop:.2f} | "
            f"{t.risk / 20.0:.1f} | {t.target} | {', '.join(conds) or '—'} | "
            f"{t.exit_reason} {t.R:+.2f}R | {v1[0]} {v1[1]:+.2f}R |\n")


HDR = ("| day | fill | dir | tf | pattern | fill px | stop | risk pts | target | "
       "walls | V8 outcome | V1 outcome |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n")


def main() -> None:
    rng = np.random.default_rng(SEED)
    P = load_pop("fit")
    v8_book, _ = build_book(P, "rev3")           # rev-3 selection, V8 outcomes
    Pv1 = swap_v1(P, "fit")
    v1_book, _ = build_book(Pv1, "rev3")
    v1_map = {(t.ts, t.tf, t.direction): (t.exit_reason, t.R)
              for t in v1_book.itertuples()}

    L = ["# FOR ANGUS — London spot-check sheet (the human calibration pass)\n",
         "\n**The ask: pull each trade up on a chart (NQ, the listed TF, the listed "
         "day) and rule ONE of: (a) my setup — I'd have taken it; (b) my setup but "
         "I'd have skipped it, because ___; (c) NOT my setup — detector drift. "
         "Reply with the row number and a/b/c. The February hand-log did exactly "
         "this for NY; London's rebuild never got its own pass. Rulings feed the "
         "rev-3 signature, not any automatic change.**\n",
         "\nBook: the rev-3 stack (08:00-09:45, wall gate, score-0 veto, "
         "one-position-at-a-time). Times are FILL times; the trigger candle closes "
         "1-4 minutes earlier on the listed TF. V8 = shipped management outcome; "
         "V1 = BE-at-1R candidate outcome for the same entry. NOTE on 41/129 "
         "trades the fill improved through the resting limit, so the fill price "
         "sits closer to the stop than the risk-pts column (sizing basis = "
         "order-time limit-to-stop distance; limits only ever improve).\n",
         "\n## A. Ten seeded-random trades (representative sample)\n\n", HDR]
    pick = v8_book.sample(n=10, random_state=int(rng.integers(0, 2**31))).sort_values("day")
    for t in pick.itertuples():
        L.append(row(t, v1_map))
    L.append("\n## B. The twelve worst 1-lot losers (every big loss, individually)\n\n")
    L.append(HDR)
    for t in v8_book.nsmallest(12, "dollars").sort_values("day").itertuples():
        L.append(row(t, v1_map))
    L.append("\nContext for section B: all twelve were autopsied in "
             "docs/LONDON-VETO-SCAN.md — no shared mechanical cause survived the "
             "guards; several fade value hard (1-2sigma wrong side of VWAP) or enter "
             "at range extremes. The question for the human eye is whether these "
             "look like honest losses on valid setups, or like trades you would "
             "have refused on context the detector cannot see.\n")
    write("FOR-ANGUS-spot-check-sheet.md", "".join(L))


if __name__ == "__main__":
    main()
