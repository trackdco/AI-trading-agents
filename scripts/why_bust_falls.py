#!/usr/bin/env python3
"""Paired decomposition: where does 1.44% -> 0.00% come from, and who pays for it?

Angus, 2026-07-26: "how do we go from having the same amount of profit and 1.44% bust to
0.00%?" The two numbers describe DIFFERENT SUB-POPULATIONS, and the payout table is too
coarse to show the price. This proves it by running both policies on the SAME pre-drawn
day sequence per simulation, so every path is directly comparable.

  policy A: naked        (no halts)
  policy B: buffer $400  (Tier-1 rule 1 only)

Reports the rescued paths, the untouched paths, and the paths that merely paid.

    python -m scripts.why_bust_falls
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
BASE0, INC = 200.0, 75.0
PAYOUT, MIN_WIN_DAYS, MIN_WIN_PL = 2000.0, 5, 150.0
TRIGGER = 6000.0          # Build-6
NSIM, NDAYS, SEED = 20000, 252, 20260726

d = pd.read_parquet(BOOK)
_b = pd.DataFrame({"day": d["day"].astype(str), "conv": d["conviction"].astype(float),
                   "risk": d["risk_pts"].astype(float),
                   "Rm": (d["dollars_1lot"] / (d["risk_pts"] * 20.0)).astype(float)})
DAYS = [g[["conv", "risk", "Rm"]].values for _, g in _b.groupby("day")]
ND = len(DAYS)


def base_dollar(ad):
    return BASE0 + INC * max(0, int((ad - 3000) // 1000)) if ad > 3000 else BASE0


def sim(seq, buf):
    """Returns (cash, busted, bust_day, halt_days, first_halt_day, min_avail_dd)."""
    bal, line, cash, win_days = 0.0, -DD, 0.0, 0
    halt_days, first_halt, min_avail = 0, 0, DD
    for i, di in enumerate(seq, 1):
        day = DAYS[di]
        avail = bal - line
        base = base_dollar(avail)
        dpl = 0.0
        for conv, risk, Rm in day:
            live = (bal - line) + dpl
            min_avail = min(min_avail, live)
            if buf is not None and live <= buf:
                halt_days += 1
                if not first_halt:
                    first_halt = i
                break
            m = min(40, int(round(min(2.0, conv) * base / (risk * 2.0))))
            dpl += m * (Rm * risk * 20.0) / 10.0
            if bal + dpl <= line:
                return cash, True, i, halt_days, first_halt, min(min_avail, bal + dpl - line)
        bal += dpl
        if dpl >= MIN_WIN_PL:
            win_days += 1
        line = min(0.0, max(line, bal - DD))
        if bal >= TRIGGER and win_days >= MIN_WIN_DAYS:
            bal -= PAYOUT
            cash += PAYOUT
            win_days = 0
    return cash, False, 0, halt_days, first_halt, min_avail


def main() -> None:
    rng = np.random.default_rng(SEED)
    seqs = rng.integers(0, ND, size=(NSIM, NDAYS))

    A = [sim(s, None) for s in seqs]        # naked
    B = [sim(s, 400.0) for s in seqs]       # buffer $400

    a_cash = np.array([r[0] for r in A]); a_bust = np.array([r[1] for r in A])
    b_cash = np.array([r[0] for r in B]); b_bust = np.array([r[1] for r in B])
    b_halts = np.array([r[3] for r in B]); b_first = np.array([r[4] for r in B])
    a_bustday = np.array([r[2] for r in A])

    print(f"{NSIM:,} paired funded years, identical day sequences in both policies\n")
    print(f"naked        : bust {a_bust.mean()*100:5.2f}%   median cash ${np.median(a_cash):,.0f}"
          f"   mean ${a_cash.mean():,.0f}")
    print(f"buffer $400  : bust {b_bust.mean()*100:5.2f}%   median cash ${np.median(b_cash):,.0f}"
          f"   mean ${b_cash.mean():,.0f}\n")

    rescued = a_bust & ~b_bust
    still = a_bust & b_bust
    untouched = ~a_bust & (b_halts == 0)
    paid = ~a_bust & (b_halts > 0)

    print("--- who is in which group -------------------------------------------------")
    print(f"  RESCUED   busted naked, survives with the buffer : {rescued.sum():>6,} "
          f"({rescued.mean()*100:.2f}%)")
    print(f"  STILL     busts either way                       : {still.sum():>6,}")
    print(f"  UNTOUCHED never came within $400 of the line     : {untouched.sum():>6,} "
          f"({untouched.mean()*100:.1f}%)")
    print(f"  PAID      survived anyway, but got halted        : {paid.sum():>6,} "
          f"({paid.mean()*100:.1f}%)\n")

    print("--- what each group gains or gives up -------------------------------------")
    if rescued.sum():
        print(f"  RESCUED   naked cash ${a_cash[rescued].mean():>7,.0f} (dead) -> "
              f"${b_cash[rescued].mean():>7,.0f} alive. Naked bust hit on day "
              f"{np.median(a_bustday[rescued]):.0f} (median)")
    print(f"  UNTOUCHED cash change ${(b_cash-a_cash)[untouched].mean():>+7,.0f}  "
          f"— by construction the halt never fired")
    if paid.sum():
        dp = (b_cash - a_cash)[paid]
        print(f"  PAID      cash change ${dp.mean():>+7,.0f} mean, ${np.median(dp):>+7,.0f} median, "
              f"worst ${dp.min():>+7,.0f}   ({(dp<0).mean()*100:.0f}% of them lose anything)")
    print()

    print("--- when does the buffer actually fire? -----------------------------------")
    fired = b_halts > 0
    print(f"  paths where it ever fires        : {fired.mean()*100:.1f}%")
    print(f"  halt-days per firing path        : median {np.median(b_halts[fired]):.0f}, "
          f"p90 {np.percentile(b_halts[fired],90):.0f}")
    print(f"  first firing, day of the year    : median {np.median(b_first[fired]):.0f}, "
          f"p10 {np.percentile(b_first[fired],10):.0f}, p90 {np.percentile(b_first[fired],90):.0f}")
    print(f"  halt-days averaged over ALL paths: {b_halts.mean():.1f}/yr\n")

    print("--- why the payout table looked free --------------------------------------")
    print(f"  cash is quantised to ${PAYOUT:,.0f} payouts, so the annual figure moves in steps.")
    for q in (10, 25, 50, 75):
        print(f"    p{q:<3} naked ${np.percentile(a_cash,q):>8,.0f}   "
              f"buffer ${np.percentile(b_cash,q):>8,.0f}")
    print(f"  MEAN cash (not quantised): ${a_cash.mean():,.0f} -> ${b_cash.mean():,.0f} "
          f"({(b_cash.mean()/a_cash.mean()-1)*100:+.2f}%)")


if __name__ == "__main__":
    main()
