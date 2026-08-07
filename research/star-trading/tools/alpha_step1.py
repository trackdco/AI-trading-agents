#!/usr/bin/env python3
"""STEP 1 — cost gate for cluster alpha on NQ. Run before any backtest.

Geometry is self-defining at RR 0.2 with a level-based target:
    target distance t = |00:00 UTC open - previous-day level|
    stop distance   s = 5 * t
Breakeven with round-trip cost c:  p0 = (s + c) / (s * (R + 1)),  R = 0.2
"""
from __future__ import annotations

import statistics as st
from datetime import date, timedelta

from alpha_data import load

POINT_VALUE = 20.0          # NQ: $20 per index point, $5 per 0.25 tick
R = 0.2

# Round-trip cost in POINTS. Entry is a limit (no spread paid); the target is a
# limit at a level (no slip); the stop is a market order when triggered, so it
# pays spread plus depth. Commission $4.50 RT = 0.225 pt at $20/pt.
# Slip levels bracket ordinary / thin / stressed overnight depth at 19:00-21:00 ET,
# where NQ top-of-book depth is a fraction of RTH. NOT MEASURED — no trade-level
# data exists (Stage 0 audit), so these are declared assumptions.
COSTS = {
    "LOW  (comm + 1 tick stop slip)": 0.225 + 0.25,
    "MID  (comm + 3 tick stop slip)": 0.225 + 0.75,
    "HIGH (comm + 7 tick stop slip)": 0.225 + 1.75,
}


def pctl(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def utc_day_hl(bars_for_day):
    hs = [b[1] for b in bars_for_day.values()]
    ls = [b[2] for b in bars_for_day.values()]
    return max(hs), min(ls)


def build_sessions():
    """One record per tradeable session.

    DECLARED PORT — 'previous day' = the prior CALENDAR UTC DAY.
    Alpha is an FX model whose day boundary is 00:00 UTC and whose entry is the
    00:00 UTC candle, so the level it targets is the high/low of the 24h block
    that has just closed at the moment of entry. Prior-calendar-UTC-day is the
    only NQ definition that preserves both properties (boundary coincides with
    entry; period complete and just closed). A Globex-session definition would
    put the boundary at 17:00 ET, hours away from the entry, and an RTH
    definition would exclude the overnight move entirely.
    """
    d = load()
    bars, front = d["bars"], d["front"]
    days = sorted(bars)
    idx = {day: i for i, day in enumerate(days)}

    rolls = {days[i] for i in range(1, len(days)) if front[days[i]] != front[days[i - 1]]}

    out, skipped = [], {"no_0000_bar": 0, "no_prev_day": 0, "roll": 0, "contract_change": 0}
    for day in days:
        prev = (date.fromisoformat(day) - timedelta(days=1)).isoformat()
        if day in rolls:
            skipped["roll"] += 1
            continue
        # also skip the session immediately AFTER a roll
        i = idx[day]
        if i > 0 and days[i - 1] in rolls:
            skipped["roll"] += 1
            continue
        if prev not in bars:
            skipped["no_prev_day"] += 1
            continue
        if front[day] != front[prev]:
            skipped["contract_change"] += 1
            continue
        if 0 not in bars[day]:                 # minute 0 == 00:00 UTC bar
            skipped["no_0000_bar"] += 1
            continue

        entry = bars[day][0][0]                # OPEN of the open-labelled 00:00 bar
        ph, pl = utc_day_hl(bars[prev])
        out.append({"day": day, "sym": front[day], "entry": entry,
                    "prev_high": ph, "prev_low": pl,
                    "t_long": ph - entry, "t_short": entry - pl})
    return out, skipped, days, rolls


def atr14(days_sorted, bars, front, upto_day):
    """True-range ATR over prior 14 UTC days, same contract only."""
    i = days_sorted.index(upto_day)
    trs, prev_close = [], None
    for d in days_sorted[max(0, i - 14):i]:
        if front[d] != front[upto_day]:
            trs, prev_close = [], None          # reset state across a roll
            continue
        h, l = utc_day_hl(bars[d])
        c = bars[d][max(bars[d])][3]
        tr = h - l if prev_close is None else max(h - l, abs(h - prev_close), abs(l - prev_close))
        trs.append(tr)
        prev_close = c
    return sum(trs) / len(trs) if trs else None


def main():
    sess, skipped, days, rolls = build_sessions()
    d = load()
    bars, front = d["bars"], d["front"]

    print("=" * 74)
    print("STEP 1 — COST GATE")
    print("=" * 74)
    print(f"sessions usable: {len(sess)}   skipped: {skipped}")
    print(f"date range: {sess[0]['day']} -> {sess[-1]['day']}   rolls excluded: {len(rolls)}")

    for s in sess:
        s["atr"] = atr14(days, bars, front, s["day"])
    sess = [s for s in sess if s["atr"]]

    # ---- 1a: target distances -------------------------------------------
    print("\n--- 1a. distance from 00:00 UTC open to previous-day level ---")
    print(f"{'':10s} {'median':>9} {'IQR(25-75)':>19} {'p05':>8} {'p95':>8} {'max':>9}")
    for lab, key in (("to prev HIGH", "t_long"), ("to prev LOW", "t_short")):
        v = [s[key] for s in sess]
        print(f"{lab:10s} {pctl(v,.5):9.1f} {pctl(v,.25):8.1f}-{pctl(v,.75):<10.1f} "
              f"{pctl(v,.05):8.1f} {pctl(v,.95):8.1f} {pctl(v,.99):9.1f}   points")
        a = [s[key] / s["atr"] for s in sess]
        print(f"{'':10s} {pctl(a,.5):9.2f} {pctl(a,.25):8.2f}-{pctl(a,.75):<10.2f} "
              f"{pctl(a,.05):8.2f} {pctl(a,.95):8.2f} {pctl(a,.99):9.2f}   ATR units")

    neg = sum(1 for s in sess if s["t_long"] <= 0) + sum(1 for s in sess if s["t_short"] <= 0)
    print(f"\n  sessions where the 00:00 open is already beyond the level "
          f"(no trade possible that side): {neg} of {2*len(sess)} legs")

    # ---- 1b: implied stops and dollar risk -------------------------------
    print("\n--- 1b. implied stop = 5 x target distance, and dollar risk ---")
    allt = [s["t_long"] for s in sess if s["t_long"] > 0] + \
           [s["t_short"] for s in sess if s["t_short"] > 0]
    stops = [5 * t for t in allt]
    print(f"{'':14s} {'p05':>9} {'p25':>9} {'median':>9} {'p75':>9} {'p95':>9}")
    print(f"{'target (pts)':14s} " + " ".join(f"{pctl(allt,q):9.1f}" for q in (.05,.25,.5,.75,.95)))
    print(f"{'stop   (pts)':14s} " + " ".join(f"{pctl(stops,q):9.1f}" for q in (.05,.25,.5,.75,.95)))
    print(f"{'risk   ($/ct)':14s} " + " ".join(f"{pctl(stops,q)*POINT_VALUE:9,.0f}"
                                               for q in (.05,.25,.5,.75,.95)))

    # ---- 1c: cost-adjusted breakeven -------------------------------------
    print("\n--- 1c. cost-adjusted breakeven  p0 = (s + c) / (s * 1.2) ---")
    print("  asymptote as s grows: 1/(1+R) = 83.33%  (cost-free breakeven at RR 0.2)")
    qs = [.05, .25, .5, .75, .95]
    print(f"\n{'cost level':34s} " + " ".join(f"{'s@p'+str(int(q*100)):>9}" for q in qs))
    worst_overall = 0.0
    for lab, c in COSTS.items():
        row = []
        for q in qs:
            s = pctl(stops, q)
            row.append(100 * (s + c) / (s * (1 + R)))
        worst_overall = max(worst_overall, max(row))
        print(f"{lab:34s} " + " ".join(f"{x:8.2f}%" for x in row))

    # smallest stop in the sample = the most cost-hostile case that actually occurred
    smin = min(stops)
    print(f"\n  smallest realised stop in sample: {smin:.2f} pts "
          f"(${smin*POINT_VALUE:,.0f}/contract)")
    for lab, c in COSTS.items():
        print(f"    p0 at that stop, {lab:34s} = {100*(smin+c)/(smin*(1+R)):.2f}%")

    print("\n" + "=" * 74)
    print(f"TERMINATION CHECK: worst-case p0 across the p05-p95 stop range "
          f"and all cost levels = {worst_overall:.2f}%")
    if worst_overall > 95.0:
        print("  -> EXCEEDS 95% EVERYWHERE. Model cannot clear its own costs. STOP.")
    else:
        print("  -> does NOT exceed 95% across plausible stops. Gate NOT triggered.")
        print("     Proceed to Step 2. (Note: this gate tests cost drag only, not")
        print("     whether the required win rate is attainable, and not position size.)")
    print("=" * 74)

    import pickle
    from pathlib import Path
    Path(__file__).resolve().parent.joinpath("_alpha_sessions.pkl").write_bytes(
        pickle.dumps(sess, protocol=4))
    print(f"\n{len(sess)} sessions cached for Step 2.")


if __name__ == "__main__":
    main()
