#!/usr/bin/env python3
"""STAGE 2 — axis-count decision table for the VWAP/BB pre-registration.

Gate 6's tripwire was computed against p0 = 0.406 (the OLD cost basis). Stage 1a
re-derives breakeven at the A5 10-point floor and the measured cost, which moves
p0 and therefore moves required n. This table shows how far it moves for each
plausible multiple-comparison correction.

One-sided one-sample proportion test, 80% power:

    n = [ z_(1-a) * sqrt(p0(1-p0)) + z_(1-b) * sqrt(p1(1-p1)) ]^2 / (p1 - p0)^2

No recommendation is made. Which axis structure to run is a research-design
choice and it is Angus's. N_trials unchanged.
"""
from __future__ import annotations

import math

POWER = 0.80
ALPHA0 = 0.05
P1 = 0.50                      # the effect the study is powered to detect
WORKBENCH_SESSIONS = 539       # gate-6 denominator, as recorded
PROCESSED_SESSIONS = 509       # sessions the detector actually ran on
RATE_A, RATE_D = 2.849, 2.328  # measured admitted trades/session under A4+A5+A7


def ndtri(p):
    """Inverse standard normal CDF by bisection on erf. No scipy here."""
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def n_required(p0, p1, alpha, power=POWER):
    za, zb = ndtri(1 - alpha), ndtri(power)
    num = za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))
    return num * num / (p1 - p0) ** 2


def min_detectable_p1(p0, n, alpha, power=POWER):
    """Smallest true win rate this n can resolve at the given alpha."""
    lo, hi = p0 + 1e-6, 0.999
    for _ in range(200):
        mid = (lo + hi) / 2
        if n_required(p0, mid, alpha) > n:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def breakeven(s, c, R=1.5):
    return (s + c) / (s * (1 + R))


def wilson(k, n, z=1.959963985):
    ph = k / n
    d = 1 + z * z / n
    ctr = ph + z * z / (2 * n)
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return (ctr - half) / d, (ctr + half) / d


def main():
    print("=" * 92)
    print("STAGE 1a — GATE 3 RE-DERIVED at the A5 floor, formally, not inherited")
    print("=" * 92)
    print("\n  p0 = (s + c) / (s * (1 + R)),  R = 1.5 (the RR floor, and under A4 the")
    print("  target is the FIRST level clearing it, so realised RR sits near 1.5).\n")
    print(f"{'stop s':>28} {'c=0.50':>10} {'c=0.975':>10} {'c=1.50':>10}   {'c/s at base':>12}")
    for s, lab in ((10.00, "A5 FLOOR — operative"),
                   (3.12, "old frozen geometry"),
                   (32.75, "hand log, full"),
                   (35.00, "hand log, in-scope")):
        row = "  ".join(f"{breakeven(s, c)*100:>8.2f}%" for c in (0.50, 0.975, 1.50))
        print(f"{lab:>28} {row}   {0.975/s*100:>11.2f}%")

    print("\n  Working at s = 10.00, c = 0.975:")
    print(f"     frictionless  1/(1+R)            = {1/2.5*100:.2f}%")
    print(f"     cost inflation (s+c)/s           = {(10+0.975)/10:.4f}")
    print(f"     p0 = 0.4000 x 1.0975             = {breakeven(10,0.975)*100:.2f}%")

    lo19, hi19 = wilson(13, 19)
    print(f"\n  Hand-log in-scope: 13/19 = {13/19*100:.1f}%, "
          f"Wilson 95% [{lo19*100:.1f}%, {hi19*100:.1f}%]")
    print(f"\n{'cost level':>14} {'p0':>9} {'margin vs 68.4%':>17} {'margin vs Wilson lo':>21}")
    for c, lab in ((0.50, "optimistic"), (0.975, "BASE"), (1.50, "adverse")):
        p0 = breakeven(10.0, c)
        print(f"{lab:>14} {p0*100:>8.2f}% {(13/19-p0)*100:>16.1f}pt "
              f"{(lo19-p0)*100:>20.1f}pt")

    print("\n  PLANNED RR of admitted trades, measured (vwapbb_a7_selector.py, 509 sessions).")
    print("  Known at signal time, before any bar moves - NOT an outcome:")
    print(f"     reading A: p10 1.586 | p25 1.756 | median 2.132 | p75 2.795 | mean 2.481")
    print("  So the 1.5R floor is a floor, not the typical trade. Breakeven at the")
    print("  measured median planned RR:")
    print(f"{'R used':>28} {'c=0.50':>10} {'c=0.975':>10} {'c=1.50':>10}")
    for R, lab in ((1.5, "1.500 - the floor (hard)"),
                   (2.132, "2.132 - median planned"),
                   (2.481, "2.481 - mean planned")):
        print(f"{lab:>28} " + "  ".join(
            f"{breakeven(10.0, c, R)*100:>8.2f}%" for c in (0.50, 0.975, 1.50)))

    print("\n" + "=" * 92)
    print("STAGE 2 — AXIS DECISION TABLE")
    print("=" * 92)
    nA, nD = RATE_A * PROCESSED_SESSIONS, RATE_D * PROCESSED_SESSIONS
    print(f"\n  available trades = rate x {PROCESSED_SESSIONS} processed sessions:")
    print(f"     reading A @ {RATE_A}/sess = {nA:.0f}   reading D @ {RATE_D}/sess = {nD:.0f}")
    print(f"  p1 = {P1}, power = {POWER}, one-sided.")
    print("\n  TWO p0 SCENARIOS. Which to power against is itself a judgement:")
    print("    CONSERVATIVE  p0 = 43.90%  - R at the 1.5 floor. Assumes every win")
    print("                                 realises only the minimum the rule allows.")
    print("    MEASURED      p0 = 35.04%  - R at the median planned RR of 2.132.")
    print("  The pre-registration should commit to the CONSERVATIVE figure; the")
    print("  measured one is shown so the size of the cushion is visible.\n")

    for P0, tag in ((breakeven(10.0, 0.975, 1.5), "CONSERVATIVE  p0 = 43.90%  (R = 1.5)"),
                    (breakeven(10.0, 0.975, 2.132), "MEASURED      p0 = 35.04%  (R = 2.132)")):
        print(f"--- {tag}   effect size p1 - p0 = {P1-P0:.4f} ---")
        hdr = (f"{'div':>5} {'alpha':>9} {'req n':>8} {'tripwire':>9} "
               f"{'A clears':>9} {'D clears':>9} {'res floor A':>12} {'blind zone':>11}")
        print(hdr)
        print("-" * len(hdr))
        for div in (1, 4, 5, 8, 16, 72):
            a = ALPHA0 / div
            n = n_required(P0, P1, a)
            fA = min_detectable_p1(P0, nA, a)
            fD = min_detectable_p1(P0, nD, a)
            print(f"{div:>5} {a:>9.5f} {n:>8.1f} {n/WORKBENCH_SESSIONS:>9.4f} "
                  f"{('YES' if nA>=n else 'NO'):>9} {('YES' if nD>=n else 'NO'):>9} "
                  f"{fA*100:>11.2f}% {(fA-P0)*100:>10.2f}pt")
        print("-" * len(hdr) + "\n")
    print("  tripwire   = required n / 539 workbench sessions (gate-6 convention)")
    print("  res floor  = lowest TRUE win rate resolvable at 80% power on reading A's n")
    print("  blind zone = res floor - breakeven. A true win rate inside this band is")
    print("               PROFITABLE AND UNDETECTABLE by this study.")

    print("\n  For continuity — the same table at the OLD p0 = 0.406:")
    print(f"{'div':>5} {'req n':>8} {'tripwire':>9}")
    for div in (1, 4, 5, 8, 16, 72):
        n = n_required(0.406, P1, ALPHA0 / div)
        print(f"{div:>5} {n:>8.1f} {n/WORKBENCH_SESSIONS:>9.4f}")

    print("\n  What each divisor corresponds to:")
    for div, what in ((1, "no correction - a single pre-committed configuration"),
                      (4, "one axis at a time, management axis at 4 (V3 struck) - CURRENT"),
                      (5, "one axis at a time, management axis at 5 - SUPERSEDED by A6"),
                      (8, "two axes crossed, e.g. entry (3) x management (4), rounded"),
                      (16, "entry x management x window, partially crossed"),
                      (72, "the FULL tournament grid W x E x V x weekly")):
        print(f"     /{div:<3} {what}")


if __name__ == "__main__":
    main()
