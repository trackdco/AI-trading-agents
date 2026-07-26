#!/usr/bin/env python3
"""NO-LOCK vs LOCK trailing-drawdown comparison for the London 10-13 UK book.

Open thread from docs/HANDOFF-LONDON-BOOK.md: the funded plan models a $2,000 trailing
max-DD that LOCKS at the $50k start once you're +$2k (that lock IS the buffer). Some prop
firms trail WITHOUT locking -- the floor follows the equity peak forever, so a drawdown can
blow you at ANY equity level, not just in the first $2k of profit.

This script runs both models side by side on the same book: historical path, Monte-Carlo
blow probability (order-shuffle + bootstrap), across static base$ and the userB ladder.

CVD CAVEAT: footprint_q3_2025 / q4_2025 are absent from the repo, so Jul-Dec 2025 trades
carry no CVD confirm flag and size at the unconfirmed half-rung. That understates profit
vs the original run (15 confirms here vs 29 reported). We therefore BRACKET the answer:
  lower = as-is (those days unconfirmed)   upper = those days all treated as confirmed
The truth sits between. Restore the two parquets to collapse the bracket.

    LONDON_SCRATCH=<dir> python3 scripts/funded_nolock.py
"""
import os
import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
rng = np.random.default_rng(7)
START, DDLIM, NPATH = 50_000.0, 2_000.0, 8_000

D = pd.read_csv(f"{S}/london_conviction_book.csv").sort_values(["day", "ent"]).reset_index(drop=True)
D = D.rename(columns={"cov": "cvcov", "ok": "cvok"})
confirmed = (D.cvcov & D.cvok).values
# days with no CVD coverage at all == the missing quarters
nocvd = (~D.cvcov).values & (D.day.str[:4] == "2025").values


def weights(scheme):
    """Scheme A conviction multiplier: confirm 1.0 / else 0.5."""
    c = confirmed.copy()
    if scheme == "upper":          # optimistic: missing-CVD days would have confirmed
        c = c | nocvd
    return np.where(c, 1.0, 0.5)


def sim(seq_wR, base_fn, lock):
    """Walk the equity path. lock=True -> floor never rises above START (locks at $50k).
    lock=False -> floor trails the peak forever. Returns (pnl, worstDD, blown)."""
    bal = peak = START
    worst = 0.0
    blown = False
    for w in seq_wR:
        base = base_fn(bal - START)
        bal += w * base
        floor = min(peak - DDLIM, START) if lock else (peak - DDLIM)
        if bal <= floor:
            blown = True
            break
        peak = max(peak, bal)
        worst = max(worst, peak - bal)
    return bal - START, worst, blown


def mc(wR, base_fn, lock, mode):
    """Monte-Carlo P(blow). mode: 'shuffle' (reorder same trades) | 'boot' (resample w/ replacement)."""
    blow = 0
    finals = []
    n = len(wR)
    for _ in range(NPATH):
        seq = rng.permutation(wR) if mode == "shuffle" else rng.choice(wR, n, replace=True)
        p, _, b = sim(seq, base_fn, lock)
        blow += b
        finals.append(p)
    return blow / NPATH * 100, float(np.median(finals)), float(np.percentile(finals, 5))


LADDER = [(750, 250, 125), (2000, 350, 175), (4000, 500, 250), (10**9, 700, 350)]


def ladder_base(buf):
    """userB ladder: risk scales with locked buffer. Returns the 1.0-mult risk $."""
    for hi, conf, _ in LADDER:
        if buf < hi:
            return conf
    return LADDER[-1][1]


if __name__ == "__main__":
    print(f"book: {len(D)} trades | confirmed as-is: {confirmed.sum()} | "
          f"missing-CVD 2025 trades: {nocvd.sum()}\n")

    for scheme, lbl in (("lower", "as-is (missing CVD = unconfirmed)"),
                        ("upper", "upper bracket (missing CVD = confirmed)")):
        wR = D.R.values * weights(scheme)
        print(f"===== {lbl} =====")
        print(f"{'base$':>7} {'model':>8} {'histP&L':>10} {'histDD':>8} "
              f"{'P(blow)shuf':>12} {'P(blow)boot':>12} {'medFinal':>10} {'5th-pct':>9}")
        for base in (150, 250, 300, 400):
            for lock in (True, False):
                fn = (lambda b, _base=base: _base)
                pnl, dd, blown = sim(wR, fn, lock)
                ps, med, p5 = mc(wR, fn, lock, "shuffle")
                pb, _, _ = mc(wR, fn, lock, "boot")
                print(f"{base:>7} {'LOCK' if lock else 'NO-LOCK':>8} {pnl:>+10,.0f} {dd:>8,.0f} "
                      f"{ps:>11.2f}% {pb:>11.2f}% {med:>+10,.0f} {p5:>+9,.0f}"
                      + ("   <-- BLEW" if blown else ""))
        # ladder
        for lock in (True, False):
            pnl, dd, blown = sim(wR, ladder_base, lock)
            ps, med, p5 = mc(wR, ladder_base, lock, "shuffle")
            pb, _, _ = mc(wR, ladder_base, lock, "boot")
            print(f"{'ladder':>7} {'LOCK' if lock else 'NO-LOCK':>8} {pnl:>+10,.0f} {dd:>8,.0f} "
                  f"{ps:>11.2f}% {pb:>11.2f}% {med:>+10,.0f} {p5:>+9,.0f}"
                  + ("   <-- BLEW" if blown else ""))
        print()
