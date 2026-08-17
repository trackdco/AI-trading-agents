#!/usr/bin/env python3
"""ARE WE CHOPPING? — his definition, hard-coded.

    python -m scripts.chop_state 2026-06-02
    python -m scripts.chop_state 2026-06-02 --at 09:42 --json

HIS DEFINITION, given plainly and implemented literally:

    "How I define chop is there's a small range that price is trading
     between. It's not rocket science. If the high to the low of the range
     we've been trading in is small and we've been trading in it for a few
     hours, then that is chop."

Two things, and only two: the range is SMALL, and it has LASTED. No
oscillation counting, no efficiency ratio, no regime score — an earlier
version of this file counted midline crossings and fired on two thirds of
all entries, because a trailing window always has a high and a low and price
always wobbles inside them. Size and duration are what he actually said.

WHAT "SMALL" MEANS, calibrated rather than invented. The normal 3-hour range
on NQ, sampled across 44 independent session-days (2026-01…04), is:

    p10 80pt · p25 104pt · median 167pt · p75 213pt · p90 266pt

So SMALL = the trailing `HOURS`-hour range sits in the bottom quartile of
that distribution (`SMALL_PT`, ~104pt). It is a percentile of real NQ
behaviour, not a number chosen to fit a result, and it should be re-measured
if volatility regime shifts.

WHAT "A FEW HOURS" MEANS: `HOURS = 3`, his word "hours" taken at its
smallest plural. The range must ALSO have been small for the whole of it —
checked at the midpoint too, so a violent hour followed by two quiet ones
does not qualify.

THE STATE

    CHOP       small range, sustained
    TRENDING   range not small
    FORMING    not enough tape yet

Plus, for the range doctrine, WHERE price sits: `zone_now` is low edge /
middle / high edge, with the middle being the inner half — reusing T50's
existing definition rather than inventing a second one. His doctrine on top
of the state: *"on a chop session it should only be either targeting the
bottom of the chop from the top, or vice versa"* — edges only, middle dead.

EVERYTHING IS AS-OF: minute t uses only bars strictly before t, so it is
live-safe and briefing-safe.

WHAT THIS DETECTOR DOES NOT DO, measured and stated so nobody expects it.
It does NOT predict which trades win. Across the 40 graded takes of the two
complete agent weeks it fires on 18% of them, and those trades did BETTER
than average (+0.98R mean vs +0.39R). More pointedly, the churn day
(2026-06-02, -1.56R) and the best trend day (2026-05-31, +7.07R) had nearly
IDENTICAL trailing 3-hour ranges through London — 81/85/99pt against
148/73/90pt. Both mornings were ranges. One held and paid; the other kept
failing at the same edge.

So this is a STATE detector for applying the range doctrine — mark the
edges, trade edge-to-edge, leave the middle alone — and not a filter that
tells you the day will be bad. A separate, measured day-level signal exists
for that (`docs/PREREG-chop-regime-gate.md` §1).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.offline_briefings import (get_bars, hist_before,     # noqa: E402
                                       session_bounds)

EDGE_FRAC = 0.25        # inner half = the middle, reusing T50's definition
HOURS = 3.0             # "a few hours", smallest plural
SMALL_PT = 104.0        # p25 of the normal 3h NQ range, measured on 44 days
MIN_BARS = 60           # don't call a range off a handful of minutes


def _zone(px: float, lo: float, hi: float) -> str:
    """Which third of the range price is in: low edge, middle, high edge."""
    w = hi - lo
    if w <= 0:
        return "middle"
    if px <= lo + EDGE_FRAC * w:
        return "low"
    if px >= hi - EDGE_FRAC * w:
        return "high"
    return "middle"


def state_at(bars: pd.DataFrame, sess_day: str, minute: str,
             hours: float = HOURS, small_pt: float = SMALL_PT) -> dict:
    """CHOP when the trailing `hours`-hour range is small AND has stayed
    small for the whole stretch. His definition, nothing added."""
    t0, t = session_bounds(sess_day, minute)
    start = max(t0, t - pd.Timedelta(hours=hours))
    seg = bars[(bars.index >= start) & (bars.index < t)]
    if len(seg) < MIN_BARS:
        return {"state": "FORMING", "reason": f"only {len(seg)} bars of tape",
                "range_high": None, "range_low": None, "zone_now": None,
                "in_middle": False}

    hi, lo = float(seg.high.max()), float(seg.low.min())
    w = hi - lo
    # sustained: the first half of the stretch must also have been tight,
    # so one violent hour followed by two quiet ones does not qualify
    mid_t = start + (t - start) / 2
    first = seg[seg.index < mid_t]
    w_first = float(first.high.max() - first.low.min()) if len(first) else w

    px = float(seg.close.iloc[-1])
    zone = _zone(px, lo, hi)
    hours_held = (t - start).total_seconds() / 3600.0

    if w <= small_pt and w_first <= small_pt:
        state = "CHOP"
        reason = (f"{w:.0f}pt range held for {hours_held:.1f}h "
                  f"({lo:.2f}–{hi:.2f}) — small and sustained")
    elif w <= small_pt:
        state = "FORMING"
        reason = (f"{w:.0f}pt now, but {w_first:.0f}pt earlier in the "
                  f"stretch — not yet sustained")
    else:
        state = "TRENDING"
        reason = f"{w:.0f}pt range over {hours_held:.1f}h — not small"

    return {"state": state, "reason": reason,
            "range_high": round(hi, 2), "range_low": round(lo, 2),
            "range_width": round(w, 2), "hours_held": round(hours_held, 1),
            "small_threshold_pt": small_pt,
            "zone_now": zone, "in_middle": zone == "middle",
            "middle_band": [round(lo + EDGE_FRAC * w, 2),
                            round(hi - EDGE_FRAC * w, 2)],
            "as_of": f"{t:%Y-%m-%d %H:%M}",
            "doctrine": ("CHOP + in_middle -> the middle is dead. CHOP + at "
                         "an edge -> the only licensed trade is from that "
                         "edge toward the opposite edge.")}


def day_profile(bars: pd.DataFrame, sess_day: str, step: int = 15) -> list:
    """State every `step` minutes across the trading windows — a day's shape."""
    out = []
    for hm in range(3 * 60, 11 * 60 + 1, step):
        m = f"{hm // 60:02d}:{hm % 60:02d}"
        try:
            s = state_at(bars, sess_day, m)
        except (ValueError, KeyError):
            continue
        out.append((m, s))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sess_day")
    ap.add_argument("--at", default=None, help="one decision minute, HH:MM")
    ap.add_argument("--hours", type=float, default=HOURS)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    bars = get_bars()
    if a.at:
        s = state_at(bars, a.sess_day, a.at, a.hours)
        print(json.dumps(s, indent=1) if a.json else
              f"  {a.sess_day} {a.at}: {s['state']} — {s['reason']}\n"
              f"    range {s['range_low']}–{s['range_high']}, "
              f"price in the {s['zone_now']} zone")
        return 0

    print(f"\n  CHOP STATE — {a.sess_day}\n")
    print(f"  {'time':<7}{'state':<10}{'width':>7}{'zone':>8}   range")
    for m, s in day_profile(bars, a.sess_day):
        print(f"  {m:<7}{s['state']:<10}"
              f"{(s.get('range_width') or 0):>6.0f}pt{str(s['zone_now']):>8}   "
              f"{s['range_low']}–{s['range_high']}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
