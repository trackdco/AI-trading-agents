#!/usr/bin/env python3
"""Cliff vs ramp: is there a better shape than "halt at $X of available drawdown"?

scripts/why_bust_falls.py showed the available-DD halt is an ABSORBING state — halted
means no trades, so the balance doesn't move, so the EOD line doesn't move, so you are
still halted tomorrow. It converts busts into frozen years, and freezes some years that
would have been fine. Every dollar of buffer is a straight trade of cash for bust.

The reason it has to be a cliff is that `base_dollar` FLOORS at $200 and never steps
below it. At $400 of remaining room the sizer still wants to risk $200 on a 1.0 setup.

This measures the alternative: keep stepping down. Below $3k available DD, scale the
1.0-tier base linearly toward zero as the room runs out, and keep only a token hard halt
underneath. A trade that sizes to 0 micros is simply not taken — the account de-risks
instead of freezing, and can grind back.

    python -m scripts.dd_ramp_study

NOTE: this is a SIZING change, which is Angus's call, not the spine's. Measured here so
the decision has numbers under it; nothing is adopted.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DD = 2000.0
BASE0, INC = 200.0, 75.0
PAYOUT, MIN_WIN_DAYS, MIN_WIN_PL = 2000.0, 5, 150.0
TRIGGER = 6000.0
NSIM, NDAYS, SEED = 20000, 252, 20260726
RAMP_TOP = 3000.0        # above this the existing schedule is unchanged

d = pd.read_parquet("output/baseline_book.parquet")
_b = pd.DataFrame({"day": d["day"].astype(str), "conv": d["conviction"].astype(float),
                   "risk": d["risk_pts"].astype(float),
                   "Rm": (d["dollars_1lot"] / (d["risk_pts"] * 20.0)).astype(float)})
DAYS = [g[["conv", "risk", "Rm"]].values for _, g in _b.groupby("day")]
ND = len(DAYS)


def base_cliff(ad):
    """Today's schedule: flat $200 below $3k, +$75/$1k above it."""
    return BASE0 + INC * max(0, int((ad - RAMP_TOP) // 1000)) if ad > RAMP_TOP else BASE0


def base_ramp(ad, hard):
    """Same above $3k; below it, scale the base linearly to zero at the hard halt."""
    if ad > RAMP_TOP:
        return BASE0 + INC * int((ad - RAMP_TOP) // 1000)
    span = RAMP_TOP - hard
    return BASE0 * max(0.0, min(1.0, (ad - hard) / span)) if span > 0 else BASE0


def sim(seq, buf, ramp_hard=None):
    """ramp_hard=None -> today's cliff schedule. Otherwise ramp down to `ramp_hard`."""
    bal, line, cash, win_days = 0.0, -DD, 0.0, 0
    frozen_days, traded_days = 0, 0
    for _, di in enumerate(seq, 1):
        day = DAYS[di]
        avail = bal - line
        base = base_cliff(avail) if ramp_hard is None else base_ramp(avail, ramp_hard)
        dpl, took = 0.0, False
        for conv, risk, Rm in day:
            if buf is not None and (bal - line) + dpl <= buf:
                break
            m = min(40, int(round(min(2.0, conv) * base / (risk * 2.0))))
            if m <= 0:
                continue                     # sized out — de-risked, not halted
            took = True
            dpl += m * (Rm * risk * 20.0) / 10.0
            if bal + dpl <= line:
                return cash, True, frozen_days, traded_days
        traded_days += took
        frozen_days += (not took)
        bal += dpl
        if dpl >= MIN_WIN_PL:
            win_days += 1
        line = min(0.0, max(line, bal - DD))
        if bal >= TRIGGER and win_days >= MIN_WIN_DAYS:
            bal -= PAYOUT
            cash += PAYOUT
            win_days = 0
    return cash, False, frozen_days, traded_days


def run(label, seqs, buf, ramp_hard=None):
    R = [sim(s, buf, ramp_hard) for s in seqs]
    cash = np.array([r[0] for r in R])
    bust = np.array([r[1] for r in R])
    froz = np.array([r[2] for r in R])
    dead = (froz > 100)                       # lost most of the year to stand-down
    print(f"  {label:<34} bust {bust.mean()*100:>5.2f}%   mean ${cash.mean():>7,.0f}   "
          f"median ${np.median(cash):>7,.0f}   p10 ${np.percentile(cash,10):>7,.0f}   "
          f"years lost to stand-down {dead.mean()*100:>4.1f}%")
    return cash.mean(), bust.mean() * 100


def main() -> None:
    rng = np.random.default_rng(SEED)
    seqs = rng.integers(0, ND, size=(NSIM, NDAYS))
    print(f"{NSIM:,} paired funded years, Build-6, identical day sequences throughout.")
    print("MEAN cash is the KPI — the median is quantised to $2,000 payout steps.\n")

    print("A. TODAY'S SHAPE — flat $200 base below $3k, hard halt at the buffer (a cliff):")
    base_mean, _ = run("no halt at all", seqs, None)
    for buf in (100.0, 250.0, 400.0, 600.0):
        run(f"cliff, buffer ${buf:,.0f}", seqs, buf)

    print("\nB. RAMP — base steps down below $3k, token hard halt underneath:")
    for hard in (100.0, 250.0, 400.0):
        run(f"ramp to $0 at ${hard:,.0f}, halt ${hard:,.0f}", seqs, hard, hard)

    print("\nC. RAMP + the shipped buffer, i.e. keep the $250 halt and add the ramp above it:")
    run("ramp to $0 at $250, halt $250", seqs, 250.0, 250.0)
    run("ramp to $0 at $100, halt $250", seqs, 250.0, 100.0)

    print(f"\n(baseline for comparison: no halt at all, mean ${base_mean:,.0f})")


if __name__ == "__main__":
    main()
