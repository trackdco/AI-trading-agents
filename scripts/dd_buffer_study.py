#!/usr/bin/env python3
"""The OTHER [ANGUS] number in the arming gate: the available-drawdown floor.

Tier-1 rule #1 halts the day when `available_dd <= dd_halt_buffer`. The spine ships
$250; the arming gate proposes $400 ("one max-risk trade"). This sweeps it, and also
sweeps the daily loss halt expressed in **R** rather than dollars — because the sizer
is DD-scaled, a fixed-dollar day limit silently tightens as the account grows, while an
R limit is invariant to the sizing schedule.

    python -m scripts.dd_buffer_study
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
NSIM = 20000
NDAYS = 252
SEED = 20260726


def load_days():
    d = pd.read_parquet(BOOK)
    b = pd.DataFrame({
        "day": d["day"].astype(str),
        "conv": d["conviction"].astype(float),
        "risk": d["risk_pts"].astype(float),
        "Rm": (d["dollars_1lot"] / (d["risk_pts"] * 20.0)).astype(float),
    })
    return [g[["conv", "risk", "Rm"]].values for _, g in b.groupby("day")]


def base_dollar(ad):
    return 200.0 + 75.0 * max(0, int((ad - 3000) // 1000)) if ad > 3000 else 200.0


def sim_year(rng, days, buf, day_R):
    """day_R: daily loss halt in R units of the day's own base_dollar (None = off)."""
    bal, line = 0.0, -DD
    for _ in range(NDAYS):
        day = days[rng.integers(len(days))]
        avail = bal - line
        base = base_dollar(avail)
        stop_at = None if day_R is None else day_R * base
        dpl = 0.0
        for conv, risk, Rm in day:
            if (bal - line) + dpl <= buf:
                break
            if stop_at is not None and dpl <= stop_at:
                break
            m = min(40, int(round(min(2.0, conv) * base / (risk * 2.0))))
            dpl += m * (Rm * risk * 20.0) / 10.0
            if bal + dpl <= line:
                return bal + dpl, True
        bal += dpl
        line = min(0.0, max(line, bal - DD))
    return bal, False


def run(days, buf, day_R):
    rng = np.random.default_rng(SEED)
    finals = np.empty(NSIM)
    busts = 0
    for i in range(NSIM):
        f, b = sim_year(rng, days, buf, day_R)
        finals[i] = f
        busts += b
    return busts / NSIM * 100, np.median(finals), np.percentile(finals, 10)


def main() -> None:
    days = load_days()
    print(f"funded year, {NSIM:,} sims, EOD DD $2,000, DD-scaled dollar-risk sizing\n")
    print("A. available-DD halt buffer sweep (daily loss halt OFF, so the buffer is isolated)")
    print(f"{'buffer':>10} {'bust%':>8} {'median':>12} {'p10':>12}")
    for buf in (0, 100, 250, 400, 600, 800, 1000):
        bu, md, p10 = run(days, buf, None)
        print(f"${buf:>9,} {bu:>7.2f}% ${md:>11,.0f} ${p10:>11,.0f}")

    print("\nB. daily loss halt in R (buffer held at the shipped $250)")
    print(f"{'day halt':>10} {'bust%':>8} {'median':>12} {'p10':>12}")
    for r in (None, -3.0, -2.5, -2.0, -1.5):
        bu, md, p10 = run(days, 250.0, r)
        print(f"{('off' if r is None else f'{r}R'):>10} {bu:>7.2f}% ${md:>11,.0f} ${p10:>11,.0f}")

    print("\nC. the recommended pair vs the shipped pair")
    for buf, r, tag in ((250.0, None, "shipped (buffer $250, no R halt)"),
                        (250.0, -2.0, "buffer $250 + -2R"),
                        (400.0, -2.0, "buffer $400 + -2R  <- proposal")):
        bu, md, p10 = run(days, buf, r)
        print(f"  {tag:<36} bust {bu:>5.2f}%  median ${md:>9,.0f}  p10 ${p10:>9,.0f}")


if __name__ == "__main__":
    main()
