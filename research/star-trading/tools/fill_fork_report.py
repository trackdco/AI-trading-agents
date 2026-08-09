#!/usr/bin/env python3
"""Amendment 05 (round 2), item 3 — geometry-only report on the fill-accounting fork.

Across all 1,472 admitted trades (pinned pre-A14/A15 spec is irrelevant here; this uses
the CURRENT admission list under A1-A15, the same one the discarded Stage 3 run screened):

  - distribution of (realised RR - screened RR)
  - fraction realising below 1.5R / 1.0R / 0.5R
  - distribution of the adverse entry gap, points and ticks
  - how many trades would NOT fill at all under single-bar true-limit semantics
    (the fill bar's range never reaches the limit), and their screened-RR distribution
    vs. the trades that DO reach it

No outcome is computed. R and RR are distances and ratios between prices already fixed
at signal time (entry/stop/target) or realised at the fill bar (its own OHLC) - no exit,
no P&L, no win/loss appears anywhere.
"""
import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]
import json
import statistics
from pathlib import Path

from invariants_2b import build_trade_list
from vwapbb_signals import build_sessions

TICK = 0.25
OUT = Path(__file__).resolve().parents[2] / "vwap-bb" / "data" / "fill_fork_report.json"


def quantiles(xs):
    xs = sorted(xs)
    n = len(xs)
    def q(p):
        return xs[min(n - 1, max(0, int(p * n)))]
    return {"n": n, "min": xs[0], "p05": q(.05), "p25": q(.25), "median": q(.5),
            "p75": q(.75), "p95": q(.95), "max": xs[-1], "mean": sum(xs) / n}


def main():
    trades, processed, excl, ndays = build_trade_list()
    sess, _ = build_sessions()

    rows = []
    for t in trades:
        bars = sess[t["session_date"]]
        fb = bars[t["fill_bar"]]           # (o, h, l, c, v)
        o, h, l, c, v = fb
        limit = t["entry"]
        stop, tgt = t["stop_px"], t["tgt_px"]
        R_screen = t["R_int"]
        if t["direction"] == "long":
            reward_screen = tgt - limit
            fill = t["fill_px"]
            R_real = fill - stop
            reward_real = tgt - fill
            gap = fill - limit                       # >0 = worse (paid more)
            reaches = (l <= limit)                    # true-limit fill test
        else:
            reward_screen = limit - tgt
            fill = t["fill_px"]
            R_real = stop - fill
            reward_real = fill - tgt
            gap = limit - fill                        # >0 = worse (received less)
            reaches = (h >= limit)
        rr_screen = reward_screen / R_screen
        rr_real = reward_real / R_real if R_real > 0 else float("-inf")
        rows.append({
            "key": (t["session_date"], t["cm"], t["tf"], t["direction"]),
            "rr_screen": rr_screen, "rr_real": rr_real, "rr_delta": rr_real - rr_screen,
            "gap": gap, "reaches": reaches,
        })

    n = len(rows)

    # ---- (a) distribution of realised RR - screened RR ----
    deltas = [r["rr_delta"] for r in rows]
    q_delta = quantiles(deltas)

    # ---- (b) fraction realising below thresholds ----
    below15 = sum(1 for r in rows if r["rr_real"] < 1.5)
    below10 = sum(1 for r in rows if r["rr_real"] < 1.0)
    below05 = sum(1 for r in rows if r["rr_real"] < 0.5)

    # ---- (c) adverse entry gap, points and ticks (worse-direction only, gap>0) ----
    adverse_gaps_pts = [r["gap"] for r in rows if r["gap"] > 1e-9]
    adverse_gaps_ticks = [g / TICK for g in adverse_gaps_pts]
    favorable = sum(1 for r in rows if r["gap"] < -1e-9)
    exact = n - len(adverse_gaps_pts) - favorable

    # ---- (d) true single-bar limit reachability ----
    no_fill = [r for r in rows if not r["reaches"]]
    would_fill = [r for r in rows if r["reaches"]]
    rr_screen_nofill = quantiles([r["rr_screen"] for r in no_fill]) if no_fill else None
    rr_screen_fill = quantiles([r["rr_screen"] for r in would_fill]) if would_fill else None

    report = {
        "n_trades": n,
        "rr_delta_realised_minus_screened": q_delta,
        "below_1_5R": {"count": below15, "pct": below15 / n * 100},
        "below_1_0R": {"count": below10, "pct": below10 / n * 100},
        "below_0_5R": {"count": below05, "pct": below05 / n * 100},
        "adverse_gap_points": quantiles(adverse_gaps_pts) if adverse_gaps_pts else None,
        "adverse_gap_ticks": quantiles(adverse_gaps_ticks) if adverse_gaps_ticks else None,
        "gap_direction_counts": {"worse": len(adverse_gaps_pts), "better": favorable,
                                 "exact": exact},
        "true_limit_no_fill": {
            "count": len(no_fill), "pct_of_all": len(no_fill) / n * 100,
            "screened_rr_distribution": rr_screen_nofill,
        },
        "true_limit_would_fill": {
            "count": len(would_fill), "pct_of_all": len(would_fill) / n * 100,
            "screened_rr_distribution": rr_screen_fill,
        },
    }

    print("=" * 92)
    print("FILL-ACCOUNTING FORK — GEOMETRY-ONLY REPORT, all 1,472 admitted trades")
    print("=" * 92)
    print(f"trades: {n}\n")

    print("(a) realised RR - screened RR, distribution:")
    for k in ("n", "min", "p05", "p25", "median", "p75", "p95", "max", "mean"):
        print(f"    {k:<8} {q_delta[k]:>10.4f}")

    print(f"\n(b) realised RR falls below:")
    print(f"    < 1.5R : {below15:>5} of {n}  ({below15/n*100:.1f}%)")
    print(f"    < 1.0R : {below10:>5} of {n}  ({below10/n*100:.1f}%)")
    print(f"    < 0.5R : {below05:>5} of {n}  ({below05/n*100:.1f}%)")

    print(f"\n(c) fill-vs-limit gap direction: worse {len(adverse_gaps_pts)}  "
          f"favorable {favorable}  exact {exact}")
    print("    adverse gap, POINTS:")
    if adverse_gaps_pts:
        qp = quantiles(adverse_gaps_pts)
        for k in ("min", "p05", "p25", "median", "p75", "p95", "max", "mean"):
            print(f"        {k:<8} {qp[k]:>10.4f}")
    print("    adverse gap, TICKS:")
    if adverse_gaps_ticks:
        qt = quantiles(adverse_gaps_ticks)
        for k in ("min", "p05", "p25", "median", "p75", "p95", "max", "mean"):
            print(f"        {k:<8} {qt[k]:>10.2f}")

    print(f"\n(d) TRUE SINGLE-BAR LIMIT REACHABILITY (fill bar's own range vs the limit):")
    print(f"    would NOT fill (bar range never reaches the limit): "
          f"{len(no_fill)} of {n}  ({len(no_fill)/n*100:.1f}%)")
    print(f"    would fill (bar reaches or opens through the limit): "
          f"{len(would_fill)} of {n}  ({len(would_fill)/n*100:.1f}%)")
    print(f"\n    screened RR distribution — NO-FILL population:")
    if rr_screen_nofill:
        for k in ("n", "min", "p25", "median", "p75", "max", "mean"):
            print(f"        {k:<8} {rr_screen_nofill[k]:>10.4f}")
    print(f"    screened RR distribution — WOULD-FILL population:")
    if rr_screen_fill:
        for k in ("n", "min", "p25", "median", "p75", "max", "mean"):
            print(f"        {k:<8} {rr_screen_fill[k]:>10.4f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, default=str))
    print(f"\nwritten {OUT}")


if __name__ == "__main__":
    main()
