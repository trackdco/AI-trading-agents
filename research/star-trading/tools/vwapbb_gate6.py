#!/usr/bin/env python3
"""GATE 6 — sample sufficiency for the VWAP/BB strategy. Pre-flight only.

No backtest. Arithmetic on the hand log's own date span plus a session count
from the existing archives.
"""
from __future__ import annotations

import math
import csv
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from alpha_data import load

NY = ZoneInfo("America/New_York")
P0 = 0.406                      # cost-adjusted breakeven, R=1.5, c/s=1.53%
Z_POWER = 0.842                 # 80% power
RTH_OPEN, RTH_CLOSE = 9 * 60 + 31, 16 * 60


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def z_for(alpha_one_sided):
    """Inverse normal via bisection — no scipy in this environment."""
    lo, hi = 0.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 1 - ncdf(mid) > alpha_one_sided:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def required_n(p1, p0, z_a, z_b=Z_POWER):
    if p1 <= p0:
        return None
    return ((z_a * math.sqrt(p0 * (1 - p0)) + z_b * math.sqrt(p1 * (1 - p1))) ** 2
            / (p1 - p0) ** 2)


def binom_sf(k, n, p):
    """P(X >= k) exact."""
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))


def et_sessions():
    d = load()
    bars = d["bars"]
    days = set()
    for ud in bars:
        base = datetime.fromisoformat(ud).replace(tzinfo=timezone.utc)
        for m in bars[ud]:
            t = (base + timedelta(minutes=m)).astimezone(NY)
            mm = t.hour * 60 + t.minute
            if RTH_OPEN <= mm < RTH_CLOSE:
                days.add(t.date().isoformat())
                break
    return sorted(days)


def main():
    print("=" * 78)
    print("GATE 6 — SAMPLE SUFFICIENCY")
    print("=" * 78)
    print("LEAST BATTLE-TESTED OF THE SIX. Cluster alpha died before sample size")
    print("mattered, so this gate is specified from method, not demonstrated.\n")

    # ---- (d) frequency must come from the post-09:36 subset ---------------
    rows = list(csv.DictReader(open('../../../data/reference/feb2026_hand_log.csv',
                                    encoding='utf-8-sig')))
    def mins(t):
        h, m = t.strip().replace(' ', '').split(':')
        return int(h) * 60 + int(m)
    FIRST_SIG = 9 * 60 + 36
    sessions_in_log = sorted({r['Date'] for r in rows})
    post = [r for r in rows if mins(r['Entry Time ']) >= FIRST_SIG]
    post_sessions = sorted({r['Date'] for r in post})

    print("(a) FREQUENCY, from the hand log's own span")
    print(f"    log span: {sessions_in_log[0]} .. {sessions_in_log[-1]}")
    print(f"    distinct trading sessions in span: {len(sessions_in_log)}")
    print(f"    W1 reading (all 28 trades):        {28/len(sessions_in_log):.3f} trades/session")
    print(f"    RTH reading (post-09:36, 19):      {len(post)/len(sessions_in_log):.3f} trades/session")
    print(f"      sessions with >=1 post-09:36 trade: {len(post_sessions)}/{len(sessions_in_log)}")
    print("    (d) gate 2 removed 32% of the log, so the RTH frequency is the one that")
    print("        applies under the RTH convention. Gate 2 is OPEN, so both are carried.\n")

    # ---- verify the quoted p-values ---------------------------------------
    print("VERIFICATION of the brief's binomial p-values against p0 = 0.406")
    print(f"    full log 20/28 : one-sided p = {binom_sf(20,28,P0):.5f}  (brief: 0.00095)")
    print(f"    subset  13/19  : one-sided p = {binom_sf(13,19,P0):.5f}  (brief: 0.0133)")
    print()

    # ---- required n table --------------------------------------------------
    N_CONFIG_FULL, N_CONFIG_123 = 90, 30
    z_plain = z_for(0.05)
    z_b90 = z_for(0.05 / N_CONFIG_FULL)
    z_b30 = z_for(0.05 / N_CONFIG_123)
    print(f"z_alpha: plain 0.05 -> {z_plain:.3f} | Bonferroni /90 -> {z_b90:.3f} "
          f"| /30 -> {z_b30:.3f}   (z_beta = {Z_POWER})")
    print(f"\n{'true p1':>8} {'margin':>8} {'n @0.05':>9} {'n /30':>8} {'n /90':>8}")
    table = {}
    for p1 in (0.68, 0.60, 0.55, 0.50, 0.45):
        m = p1 - P0
        n0 = required_n(p1, P0, z_plain)
        n30 = required_n(p1, P0, z_b30)
        n90 = required_n(p1, P0, z_b90)
        table[p1] = (n0, n30, n90)
        print(f"{p1:>8.2f} {m:>+8.3f} {n0:>9.0f} {n30:>8.0f} {n90:>8.0f}")

    # ---- (c) available sessions -------------------------------------------
    days = et_sessions()
    work = [d for d in days if d <= '2025-01-31']
    hold = [d for d in days if d >= '2025-02-01']
    print(f"\n(c) AVAILABLE SESSIONS (existing archives, gate-5 pull NOT obtained)")
    print(f"    workbench 2023-01-02 .. 2025-01-31 : {len(work)} sessions")
    print(f"    sealed holdout 2025-02-01 .. {days[-1]} : {len(hold)} sessions")
    print(f"    TOTAL: {len(days)} sessions")

    print(f"\n(b) REQUIRED n CONVERTED TO CALENDAR TIME, and fit against the WORKBENCH")
    for freq, lab in ((28/len(sessions_in_log), 'W1  1.474/sess'),
                      (len(post)/len(sessions_in_log), 'RTH 1.000/sess')):
        avail = len(work) * freq
        print(f"\n  {lab}  -> workbench yields ~{avail:,.0f} trades")
        print(f"    {'p1':>6} {'n@0.05':>8} {'sessions':>9} {'fits?':>7}   "
              f"{'n/90':>8} {'sessions':>9} {'fits?':>7}")
        for p1 in (0.68, 0.60, 0.55, 0.50, 0.45):
            n0, n30, n90 = table[p1]
            s0, s90 = n0 / freq, n90 / freq
            print(f"    {p1:>6.2f} {n0:>8.0f} {s0:>9.0f} {'YES' if n0<=avail else 'NO':>7}   "
                  f"{n90:>8.0f} {s90:>9.0f} {'YES' if n90<=avail else 'NO':>7}")


if __name__ == "__main__":
    main()
