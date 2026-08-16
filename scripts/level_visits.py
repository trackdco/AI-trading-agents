#!/usr/bin/env python3
"""LEVEL VISITS THIS SESSION — the freshness fact tv-trigger 0.4.8 grades on.

    python -m scripts.level_visits <sess_day> <HH:MM> --level 30595.25 \
        --prior-take 03:18=30595.25 --prior-take 04:06=30713.0 --json

A MECHANICAL FACT, supplied by the orchestrator, never judged by it (runbook
§0c). Two numbers per candidate level:

  level_visits_this_session   how many times THIS SESSION a take has already
                              been adjudicated at this level (within TOL
                              points). The candidate being adjudicated counts
                              as the current visit, so a first trade at a
                              level reports 1.
  tests_15m_60min             completed 15m candles in the last 60 minutes
                              whose range contained the level — read straight
                              from the certified htf_level_behavior block.

Both feed one rule and one rule only: a level may grade A when visits == 1
and tests <= 2. The contract decides what to do with that; this file decides
nothing.

TOL is 15 points on NQ — wide enough that a cluster quoted at slightly
different prices by two candidates counts as one level (his own briefings
name "weekly_vah/vwap_p1/daily_vah cluster" at prices 14pt apart and mean one
level), narrow enough not to merge genuinely separate structure. Unratified:
his call whether a cluster should instead be matched by NAME.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.htf_level_behavior import behavior_at                # noqa: E402
from scripts.offline_briefings import get_bars                    # noqa: E402

TOL = 15.0          # points; see docstring — unratified


def visits(level: float, prior_takes: list[float], tol: float = TOL) -> int:
    """1 for a level never traded this session, 2 for its second trade, ..."""
    return 1 + sum(1 for p in prior_takes if abs(p - level) <= tol)


def freshness(bars, sess_day: str, minute: str, level: float,
              prior_takes: list[float], tol: float = TOL) -> dict:
    v = visits(level, prior_takes, tol)
    try:
        bh = behavior_at(bars, sess_day, minute, float(level))
        t15 = int((bh["by_tf"].get("15m") or {}).get("tests") or 0)
    except SystemExit:
        t15 = -1
    return {"level": round(float(level), 2),
            "level_visits_this_session": v,
            "tests_15m_60min": t15,
            "fresh": bool(v == 1 and 0 <= t15 <= 2),
            "note": ("FRESH — first trade at this level this session and the "
                     "15m has tested it at most twice in the last hour"
                     if v == 1 and 0 <= t15 <= 2 else
                     f"STALE — visit {v}, {t15} tests on the 15m in 60 min")}


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sess_day")
    ap.add_argument("minute", help="decision minute NY, HH:MM")
    ap.add_argument("--level", type=float, action="append", required=True,
                    help="candidate rejected-level price; repeatable")
    ap.add_argument("--prior-take", action="append", default=[],
                    metavar="HH:MM=PRICE",
                    help="a take already adjudicated this session; repeatable")
    ap.add_argument("--tol", type=float, default=TOL)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    prior = []
    for spec in a.prior_take:
        _, _, px = spec.partition("=")
        if px:
            prior.append(float(px))

    bars = get_bars()[["open", "high", "low", "close"]]
    out = [freshness(bars, a.sess_day, a.minute, lv, prior, a.tol)
           for lv in a.level]
    if a.json:
        print(json.dumps(out if len(out) > 1 else out[0], indent=1))
        return 0
    for o in out:
        print(f"  {o['level']:>10.2f}  visits={o['level_visits_this_session']}"
              f"  15m tests={o['tests_15m_60min']}  "
              f"{'FRESH' if o['fresh'] else 'stale'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
