#!/usr/bin/env python3
"""PRE-FLIGHT measurements for the VWAP/BB confluence strategy.

Bars-only arithmetic. No trigger detection, no strategy logic, no backtest —
everything here is answerable before any engine exists.
"""
from __future__ import annotations

import math
import statistics as st
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from alpha_data import load

NY = ZoneInfo("America/New_York")
NQ_PT, MNQ_PT = 20.0, 2.0
COSTS = {"lean": 0.25, "base": 0.50, "adverse": 1.00}
RTH_OPEN, FIRST_SIG, RTH_CLOSE = 9 * 60 + 31, 9 * 60 + 36, 16 * 60


def pctl(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def et_bars():
    """Re-index UTC-day bars onto ET session dates. Returns
    {et_date: [(minute_of_et_day, o,h,l,c,v, front_symbol)]} sorted by minute."""
    d = load()
    bars, front = d["bars"], d["front"]
    out: dict[str, list] = {}
    for ud in sorted(bars):
        base = datetime.fromisoformat(ud).replace(tzinfo=timezone.utc)
        sym = front[ud]
        for m, (o, h, l, c, v) in bars[ud].items():
            t = (base + timedelta(minutes=m)).astimezone(NY)
            key = t.date().isoformat()
            out.setdefault(key, []).append((t.hour * 60 + t.minute, o, h, l, c, v, sym))
    for k in out:
        out[k].sort()
    return out


def resample(rows, tf):
    """rows = [(minute,o,h,l,c,v,sym)] -> [(start_minute,o,h,l,c,v)] on tf-minute bars."""
    buckets: dict[int, list] = {}
    for m, o, h, l, c, v, s in rows:
        buckets.setdefault((m // tf) * tf, []).append((m, o, h, l, c, v))
    out = []
    for start in sorted(buckets):
        g = sorted(buckets[start])
        out.append((start, g[0][1], max(x[2] for x in g), min(x[3] for x in g),
                    g[-1][4], sum(x[5] for x in g)))
    return out


def main():
    S = et_bars()
    days = sorted(S)
    # keep only weekday sessions with a real RTH block
    days = [d for d in days if any(RTH_OPEN <= r[0] < RTH_CLOSE for r in S[d])]
    print(f"ET sessions with an RTH block: {len(days)}   {days[0]} -> {days[-1]}\n")

    # ---------------- GATE 1: stop-distance proxy -------------------------
    print("=" * 76)
    print("GATE 1 — SIZING")
    print("=" * 76)
    print("The spec's stop is 'beyond the wick extreme of the trigger candle' (§5.4),")
    print("so the trigger candle's RANGE upper-bounds the entry-to-stop distance.")
    print("Measured over RTH 09:36-16:00, all four entry TFs:\n")
    print(f"{'TF':>4} {'n bars':>9} {'p25':>7} {'median':>7} {'p75':>7} {'p95':>7} {'p99':>7}   points")
    tf_rows = {}
    for tf in (1, 2, 3, 5):
        rng = []
        for d in days:
            rs = [r for r in S[d] if FIRST_SIG <= r[0] < RTH_CLOSE]
            if not rs:
                continue
            for start, o, h, l, c, v in resample(rs, tf):
                rng.append(h - l)
        tf_rows[tf] = rng
        print(f"{tf:>3}m {len(rng):>9,} " + " ".join(f"{pctl(rng,q):7.2f}" for q in (.25,.5,.75,.95,.99)))

    print("\nDollar risk per contract at the median and p95 candle range:")
    print(f"{'TF':>4} {'median NQ':>11} {'median MNQ':>12} {'p95 NQ':>10} {'p95 MNQ':>10}")
    for tf in (1, 2, 3, 5):
        m, p95 = pctl(tf_rows[tf], .5), pctl(tf_rows[tf], .95)
        print(f"{tf:>3}m {m*NQ_PT:>11,.0f} {m*MNQ_PT:>12,.0f} {p95*NQ_PT:>10,.0f} {p95*MNQ_PT:>10,.0f}")

    # ---------------- GATE 2: lookback spanning the open ------------------
    print("\n" + "=" * 76)
    print("GATE 2 — SESSION OVERLAP / LOOKBACK CONTAMINATION")
    print("=" * 76)
    print("BB(20) on the first signal bar 09:36 reaches back 20 bars of the entry TF:\n")
    for tf in (1, 2, 3, 5):
        back = FIRST_SIG - 20 * tf
        print(f"  {tf}m: 20 bars = {20*tf:>3} min -> window opens {back//60:02d}:{back%60:02d} ET"
              f"   {'PRE-OPEN' if back < RTH_OPEN else 'inside RTH'}")
    print("\nATR(20) identical. Volatility of the imported regime vs the traded one:")
    pre, rth = [], []
    for d in days:
        for m, o, h, l, c, v, s in S[d]:
            if 8 * 60 <= m < RTH_OPEN:
                pre.append(h - l)
            elif FIRST_SIG <= m < RTH_CLOSE:
                rth.append(h - l)
    print(f"  pre-open 08:00-09:30  n={len(pre):>8,}  median 1m range {pctl(pre,.5):6.2f} pts")
    print(f"  RTH      09:36-16:00  n={len(rth):>8,}  median 1m range {pctl(rth,.5):6.2f} pts")
    print(f"  ratio RTH/pre-open = {pctl(rth,.5)/pctl(pre,.5):.2f}x")
    print("\nNY VWAP anchors 09:30, so at the 09:36 first signal bar it has 6 bars of data.")
    print("Its +/-1/2/3 sigma bands are computed from a 6-observation volume-weighted variance.")

    # ---------------- GATE 3: breakeven + cost ratio ----------------------
    print("\n" + "=" * 76)
    print("GATE 3 — BREAKEVEN AND COST RATIO")
    print("=" * 76)
    s_med = 32.75           # hand-log median stop, points
    print(f"stop s = {s_med} pts (hand-log median). RR per doc §6.5 floor 1.5R;")
    print("realised mean R on hand-log winners = 4.23R.\n")
    print(f"{'R':>6} {'frictionless':>13} " + " ".join(f"{'p0 '+k:>11}" for k in COSTS))
    for R in (1.5, 2.0, 3.0, 4.23):
        row = [100 * (s_med + c) / (s_med * (1 + R)) for c in COSTS.values()]
        print(f"{R:>6.2f} {100/(1+R):>12.2f}% " + " ".join(f"{x:>10.2f}%" for x in row))
    print(f"\ncost ratio c/s at s={s_med}:")
    for k, c in COSTS.items():
        print(f"  {k:>8}: c/s = {c/s_med*100:.2f}%   -> breakeven inflated by factor {1+c/s_med:.4f}")
    print("  reference: cluster alpha sat at 0.12% and passed this gate on its way to dying at gate 1.")

    # ---------------- GATE 5: roll corruption -----------------------------
    print("\n" + "=" * 76)
    print("GATE 5 — ROLL CORRUPTION")
    print("=" * 76)
    contam = []
    for d in days:
        syms = {r[6] for r in S[d]}
        if len(syms) > 1:
            contam.append((d, syms))
    print(f"ET sessions containing a contract change: {len(contam)}")
    for d, syms in contam[:15]:
        print(f"   {d}  {sorted(syms)}")
    # magnitude of the jump inside those sessions
    print("\nLargest 1-minute price jump inside each mixed-contract session:")
    for d, syms in contam[:15]:
        rows = S[d]
        jumps = [abs(rows[i + 1][4] - rows[i][4]) for i in range(len(rows) - 1)]
        print(f"   {d}  max 1m close-to-close move = {max(jumps):8.2f} pts")
    # does a 09:36 lookback reach across it?
    print("\nDoes the BB(20) window at 09:36 span the contract change?")
    for d, syms in contam[:15]:
        rows = [r for r in S[d]]
        # first bar of each symbol
        firsts = {}
        for r in rows:
            firsts.setdefault(r[6], r[0])
        switch_min = max(firsts.values())
        worst = FIRST_SIG - 20 * 5           # 5m TF reaches furthest back
        print(f"   {d}: switch at {switch_min//60:02d}:{switch_min%60:02d}, "
              f"5m BB window opens {worst//60:02d}:{worst%60:02d} -> "
              f"{'SPANS THE SWITCH' if worst < switch_min <= FIRST_SIG else 'clean at 09:36'}")

    # ---------------- GATE 6: sample sufficiency --------------------------
    print("\n" + "=" * 76)
    print("GATE 6 — SAMPLE SUFFICIENCY")
    print("=" * 76)
    freq = 28 / 19          # hand log: 28 trades over 19 Feb sessions
    avail = len(days)
    print(f"hand-log frequency: 28 trades / 19 sessions = {freq:.2f} trades/session")
    print(f"available RTH sessions 2023-01..2026-01: {avail}")
    print(f"implied available trades: ~{avail*freq:,.0f}")
    print(f"  (Vault caps at 3/day, so this is not capped-out.)\n")

    def need(p1, p0, alpha=0.05, power=0.80):
        za, zb = 1.645, 0.842
        return ((za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))) ** 2
                / (p1 - p0) ** 2)

    p0 = (s_med + 0.50) / (s_med * (1 + 1.5))
    print(f"breakeven at R=1.5, base cost: p0 = {p0*100:.2f}%")
    for lab, p1 in [("hand-log in-window point est.", 0.684),
                    ("hand-log in-window Wilson LOW", 0.460),
                    ("Wilson LOW of all 28 (20 wins)", 0.529)]:
        if p1 <= p0:
            print(f"  {lab:32s} p1={p1*100:5.1f}%  BELOW breakeven — not detectable, direction wrong")
            continue
        n = need(p1, p0)
        print(f"  {lab:32s} p1={p1*100:5.1f}%  required n = {n:6.0f} trades "
              f"= {n/freq:5.0f} sessions ({n/freq/252:.2f} yr)")


if __name__ == "__main__":
    main()
