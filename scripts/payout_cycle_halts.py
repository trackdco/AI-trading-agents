#!/usr/bin/env python3
"""The decision instrument: payout-cycle MC with the Tier-1 halts as swept parameters.

Why not the funded-year MC. `scripts/mc_dollar_risk.py` lets the balance compound for
252 days with no withdrawals, so available DD runs to six figures and the sizer pins at
the 40-micro clamp. In that world a fixed-dollar day limit is priced against a sizing
regime we will never actually trade. The REAL band, under the chosen Build-6 withdrawal
policy, is available DD ~$2k-$6k => 1R = $200-$425. That is where a daily loss halt has
to be judged, and the KPI is annual cash withdrawn, not paper equity.

Sweeps, on top of scripts/mc_payout_cycles.py (Build-6, $2k/withdrawal, 5 winning days):
  * dd_halt_buffer  — Tier-1 rule 1
  * daily loss halt — Tier-1 rule 2, in BOTH shapes: fixed dollars, and R (R scales with
    the sizer's own base_dollar, so it is invariant to the DD-scaling schedule)

    python -m scripts.payout_cycle_halts
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# The ARMING REFERENCE is the leakage-clean book (+$52,522.81 / 404 trades). Set
# CANON_BOOK=output/baseline_book.parquet to reproduce the pre-lookahead-fix figures.
BOOK = os.environ.get("CANON_BOOK", "output/baseline_book_clean.parquet")

DD = 2000.0
INC = 75.0
BASE0 = 200.0
PAYOUT = 2000.0
MIN_WIN_DAYS = 5
MIN_WIN_PL = 150.0
TRIGGER = 6000.0        # Build-6 (chosen policy)
NSIM = 20000
NDAYS = 252
SEED = 20260726

d = pd.read_parquet(BOOK)
_b = pd.DataFrame({"day": d["day"].astype(str), "conv": d["conviction"].astype(float),
                   "risk": d["risk_pts"].astype(float),
                   "Rm": (d["dollars_1lot"] / (d["risk_pts"] * 20.0)).astype(float)})
DAYS = [g[["conv", "risk", "Rm"]].values for _, g in _b.groupby("day")]
ND = len(DAYS)


def base_dollar(ad):
    return BASE0 + INC * max(0, int((ad - 3000) // 1000)) if ad > 3000 else BASE0


def sim_account(rng, buf, day_stop, in_R):
    """day_stop: None=off. in_R => interpreted as R of the day's own base_dollar."""
    bal, line, withdrawn, payouts, win_days, first = 0.0, -DD, 0.0, 0, 0, 0
    halt_days = 0
    for day_i in range(1, NDAYS + 1):
        day = DAYS[rng.integers(ND)]
        avail = bal - line
        base = base_dollar(avail)
        stop_at = None if day_stop is None else (day_stop * base if in_R else day_stop)
        dpl = 0.0
        for conv, risk, Rm in day:
            if buf is not None and (bal - line) + dpl <= buf:
                halt_days += 1
                break
            if stop_at is not None and dpl <= stop_at:
                halt_days += 1
                break
            m = min(40, int(round(min(2.0, conv) * base / (risk * 2.0))))
            dpl += m * (Rm * risk * 20.0) / 10.0
            if bal + dpl <= line:
                return withdrawn, first, True, halt_days
        bal += dpl
        if dpl >= MIN_WIN_PL:
            win_days += 1
        line = min(0.0, max(line, bal - DD))
        if bal >= TRIGGER and win_days >= MIN_WIN_DAYS:
            bal -= PAYOUT
            withdrawn += PAYOUT
            payouts += 1
            win_days = 0
            if first == 0:
                first = day_i
    return withdrawn, first, False, halt_days


def run(label, buf, day_stop, in_R):
    rng = np.random.default_rng(SEED)
    cash = np.empty(NSIM)
    firsts, busts, halts = [], 0, 0
    for i in range(NSIM):
        w, f, b, h = sim_account(rng, buf, day_stop, in_R)
        cash[i] = w
        busts += b
        halts += h
        if f:
            firsts.append(f)
    med = np.median(cash)
    print(f"  {label:<30} cash/acct ${med:>7,.0f}  x5 ${med*5:>8,.0f}  "
          f"bust {busts/NSIM*100:>5.2f}%  p25 ${np.percentile(cash,25):>7,.0f}  "
          f"1st payout {np.median(firsts) if firsts else float('nan'):>4.0f}d  "
          f"halt-days/yr {halts/NSIM:>5.1f}")
    return med, busts / NSIM * 100


def main() -> None:
    print(f"Lucid 50k, BUILD-6 payout cycle, {NSIM:,} sims x {NDAYS} days, "
          f"baseline_book day-bootstrap\n")

    print("naked (what mc_payout_cycles.py reports today):")
    run("no halts at all", None, None, False)

    print("\nTier-1 rule 1 only — available-DD halt buffer:")
    for buf in (250.0, 400.0, 600.0):
        run(f"buffer ${buf:,.0f}, no day stop", buf, None, False)

    print("\n+ Tier-1 rule 2 as a FIXED DOLLAR day stop (buffer $250):")
    for s in (-1600.0, -1200.0, -800.0, -600.0):
        run(f"buffer $250 + ${s:,.0f}/day", 250.0, s, False)

    print("\n+ Tier-1 rule 2 as an R day stop (buffer $250) — invariant to DD-scaling:")
    for r in (-3.0, -2.5, -2.0, -1.5):
        run(f"buffer $250 + {r}R/day", 250.0, r, True)

    print("\nthe proposal, head to head:")
    run("buffer $400 + -2.0R/day", 400.0, -2.0, True)
    run("buffer $400 + -$800/day (shipped $)", 400.0, -800.0, False)


if __name__ == "__main__":
    main()
