#!/usr/bin/env python3
"""STEP 2/3 — unconditional both-directions test for cluster alpha on NQ.

The bias rule (previous-day high vs low) is the discretionary core and is not
codable from the transcripts, so it is REMOVED rather than guessed. Both legs
are taken every session and the base rate is measured.

Ambiguous bars resolve STOP-FIRST, always. At RR 0.2 the target sits inside far
more 1-minute bars than the stop does, so target-first accounting inflates the
win rate systematically. That is the signature failure of this style.
"""
from __future__ import annotations

import pickle
import statistics as st
from datetime import date, timedelta
from pathlib import Path

from alpha_data import load

HERE = Path(__file__).resolve().parent
POINT_VALUE = 20.0
R = 0.2
MAX_HOLD_DAYS = 20          # alpha states no time exit; cap so the scan terminates

COSTS = {
    "LOW":  0.225 + 0.25,
    "MID":  0.225 + 0.75,
    "HIGH": 0.225 + 1.75,
}


def pctl(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def resolve(bars, front, day, sym, side, entry, target, stop):
    """Walk forward minute by minute. Returns (outcome, days_held, minutes_held).

    STOP-FIRST: if a single bar spans both levels, it is a loss. Never a win.
    """
    d0 = date.fromisoformat(day)
    minutes = 0
    for k in range(MAX_HOLD_DAYS):
        dd = (d0 + timedelta(days=k)).isoformat()
        if dd not in bars or front.get(dd) != sym:
            if k == 0:
                return "no_data", k, minutes
            continue
        start = 0 if k == 0 else -1
        for m in sorted(bars[dd]):
            if k == 0 and m < start:
                continue
            o, h, l, c, v = bars[dd][m]
            minutes += 1
            if side == "long":
                hit_stop = l <= stop
                hit_tgt = h >= target
            else:
                hit_stop = h >= stop
                hit_tgt = l <= target
            if hit_stop:                      # stop-first, unconditionally
                return "loss", k, minutes
            if hit_tgt:
                return "win", k, minutes
    return "open", MAX_HOLD_DAYS, minutes


def main():
    sess = pickle.loads((HERE / "_alpha_sessions.pkl").read_bytes())
    d = load()
    bars, front = d["bars"], d["front"]

    trades = []
    for s in sess:
        for side in ("long", "short"):
            t = s["t_long"] if side == "long" else s["t_short"]
            if t <= 0:
                continue
            stop_dist = 5 * t
            if side == "long":
                target, stop = s["prev_high"], s["entry"] - stop_dist
            else:
                target, stop = s["prev_low"], s["entry"] + stop_dist
            out, dh, mins = resolve(bars, front, s["day"], s["sym"], side,
                                    s["entry"], target, stop)
            trades.append({"day": s["day"], "side": side, "outcome": out,
                           "t": t, "s": stop_dist, "days_held": dh, "mins": mins})

    print("=" * 78)
    print("STEP 2 — UNCONDITIONAL BOTH-DIRECTIONS TEST (no bias rule)")
    print("=" * 78)
    print(f"sessions: {len(sess)}   legs attempted: {len(trades)}   "
          f"stop-first resolution: ON   max hold: {MAX_HOLD_DAYS}d")

    for side in ("long", "short", "POOLED"):
        sub = trades if side == "POOLED" else [t for t in trades if t["side"] == side]
        res = [t for t in sub if t["outcome"] in ("win", "loss")]
        w = sum(1 for t in res if t["outcome"] == "win")
        openn = sum(1 for t in sub if t["outcome"] == "open")
        print(f"\n--- {side.upper()} ---")
        print(f"  resolved {len(res)}   wins {w}   losses {len(res)-w}   "
              f"unresolved-at-cap {openn}")
        if res:
            print(f"  HIT RATE: {100*w/len(res):.2f}%")
        for lab, c in COSTS.items():
            net = [(t["t"] - c) if t["outcome"] == "win" else (-t["s"] - c) for t in res]
            tot = sum(net)
            print(f"    cost {lab:5s}  mean net {st.mean(net):+9.2f} pts/leg   "
                  f"total {tot:+12,.0f} pts   (${tot*POINT_VALUE:+,.0f}/ct)")

    res_all = [t for t in trades if t["outcome"] in ("win", "loss")]

    # streaks and drawdown on the pooled series, chronological
    res_all.sort(key=lambda t: (t["day"], t["side"]))
    c = COSTS["MID"]
    eq, peak, mdd, streak, worst_streak = 0.0, 0.0, 0.0, 0, 0
    for t in res_all:
        eq += (t["t"] - c) if t["outcome"] == "win" else (-t["s"] - c)
        peak = max(peak, eq)
        mdd = min(mdd, eq - peak)
        if t["outcome"] == "loss":
            streak += 1
            worst_streak = max(worst_streak, streak)
        else:
            streak = 0
    print(f"\n--- pooled path (MID cost) ---")
    print(f"  final equity {eq:+,.0f} pts (${eq*POINT_VALUE:+,.0f}/ct)   "
          f"max drawdown {mdd:,.0f} pts (${mdd*POINT_VALUE:,.0f}/ct)")
    print(f"  longest losing streak: {worst_streak}")

    hold = [t["days_held"] for t in res_all]
    same = sum(1 for t in res_all if t["days_held"] == 0)
    print(f"  resolved same UTC day: {same}/{len(res_all)} ({100*same/len(res_all):.1f}%)"
          f"   median days held {pctl(hold,.5):.0f}   p95 {pctl(hold,.95):.0f}")

    # ---- STEP 3 -----------------------------------------------------------
    print("\n" + "=" * 78)
    print("STEP 3 — REQUIRED LIFT")
    print("=" * 78)
    base = 100 * sum(1 for t in res_all if t["outcome"] == "win") / len(res_all)
    stops = [t["s"] for t in res_all]
    print(f"  unconditional base rate (pooled, stop-first): {base:.2f}%")
    for lab, cc in COSTS.items():
        s_med = pctl(stops, .5)
        p0 = 100 * (s_med + cc) / (s_med * (1 + R))
        print(f"  breakeven at median stop, cost {lab:5s}: {p0:.2f}%   "
              f"REQUIRED LIFT = {p0-base:+.2f} pts")

    # hindsight ceiling: pick the winning side each session with perfect foresight
    byday = {}
    for t in res_all:
        byday.setdefault(t["day"], []).append(t)
    ceil_win = sum(1 for day, ts in byday.items() if any(x["outcome"] == "win" for x in ts))
    print(f"\n  HINDSIGHT CEILING (perfect direction choice each session):")
    print(f"    sessions with >=1 winning leg: {ceil_win}/{len(byday)} = "
          f"{100*ceil_win/len(byday):.2f}%")
    print(f"    this is the absolute upper bound on ANY bias rule.")

    pickle.dumps(trades)
    (HERE / "_alpha_trades.pkl").write_bytes(pickle.dumps(trades, protocol=4))


if __name__ == "__main__":
    main()
