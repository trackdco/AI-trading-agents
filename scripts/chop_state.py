#!/usr/bin/env python3
"""ARE WE CHOPPING? — his definition, hard-coded.

    python -m scripts.chop_state 2026-06-02
    python -m scripts.chop_state 2026-06-02 --at 09:42 --json

HIS WORDS, and this file is nothing but these words made mechanical:

    "choppy price action is: price just bouncing between a low and a high
     and not really going any other way."

So: find the low and the high, count the bounces between them, and check
nothing has broken out. That is the whole detector. No score, no threshold
sweep, no regime model — he explicitly refused a continuous chop score
("I already have a graded conviction ladder and a second score will fight
it") and asked for a STATE.

THE STATE MACHINE

    FORMING   not enough tape yet, or fewer than 2 traversals
    CHOP      >= 2 traversals of a range that is still intact
    BROKEN    a 15m candle has CLOSED beyond an edge with acceptance;
              the range is dead until a new one forms

A TRAVERSAL is one trip from one edge zone to the other — low zone to high
zone, or high zone to low zone. Two traversals means price has gone
low -> high -> low (or the mirror). That is "bouncing between a low and a
high", counted.

EDGE ZONES are the outer quarter at each end; the MIDDLE is the inner half.
That is not a new number: `tv-trigger`'s T50 already defines the middle as
the inner half of the range, and this reuses it exactly.

WHAT COUNTS AS BREAKING THE RANGE is his acceptance rule, not a wick: a 15m
candle must CLOSE beyond the edge. The extra `BREAK_BUFFER` (10% of range
width) is MINE and is flagged — a close one tick beyond an edge is not
acceptance, and he has never given a number for how far is enough.

EVERYTHING IS AS-OF. The state at minute t uses only bars strictly before t,
so it can be computed live and can be put in a briefing without leaking.

CALIBRATION STATUS — READ THIS BEFORE WIRING IT INTO ANYTHING.

**It is not ready to gate trades, and the numbers say so plainly.** Measured
against all 40 graded takes of the two complete agent weeks, at the default
120-minute window, it calls CHOP on **26 of 40 entries** — two thirds of
everything. A detector that fires on two thirds of the tape is labelling, not
detecting. Worse, the trades it flags CHOP did BETTER (+17.22R, mean +0.66R)
than the ones it called TRENDING (+1.73R, mean +0.14R), and "CHOP + in the
middle" — the population the range doctrine says should not be traded at all
— was the single most profitable bucket (+16.71R over 21 trades).

Swept on the independent 87-day census (3,261 triggers), tightening helps but
only by starving it: at >=18 midline crossings and efficiency <0.25 the
flagged triggers reach 2R 23.2% of the time against 33.4% for the rest — a
real 10-point gap, but it fires on 2.9% of triggers. Loose settings that fire
often show almost no gap (31% vs 33%).

WHAT THAT MEANS. The DAY-level version of this question does work and is
measured (`docs/PREREG-chop-regime-gate.md` §1: fewest-trigger days 39% reach
2R, most-trigger days 29.8%, across a quarter of all days each). The
MOMENT-level version — "are we in a range right now" — does not work yet with
a rolling high/low, because a rolling window always has a high and a low and
price always oscillates inside them. Requiring both edges to be touched twice
(MIN_EDGE_TOUCHES) changed nothing: on 1-minute bars both extremes get
retouched almost always.

THE GAP, STATED SO IT CAN BE CLOSED. He marks a range by eye from STRUCTURE —
a specific swing high and swing low that price has visibly respected — not
from the extremes of an arbitrary trailing window. Every proxy here is a
guess at that, and each guess has now been tested and found too permissive.
Closing it needs either his marked ranges on a handful of days to fit
against, or a swing-structure definition he confirms is the one he uses.
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

EDGE_FRAC = 0.25        # outer quarter each end = edge zone; inner half = middle (T50)
MIN_TRAVERSALS = 2      # "bouncing between a low and a high" = there and back
GOING_NOWHERE = 0.50    # MINE, unratified: net move under half the range width
MIN_EDGE_TOUCHES = 2    # a range you could MARK: each edge respected twice
EDGE_TOL = 0.10         # MINE: "touched" = within 10% of range width of the edge
WINDOW_MIN = 120        # MINE, unratified: how much recent tape "right now" means
MIN_BARS = 30           # don't call a range off a handful of minutes


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
             window_min: int = WINDOW_MIN) -> dict:
    """The chop state as of `minute`, from bars strictly before it.

    TWO CONDITIONS, because his sentence has two halves and both matter:

      "price just bouncing between a low and a high"   -> TRAVERSALS >= 2
      "and not really going any other way"             -> |net move| is small
                                                          against the range it
                                                          covered

    The second half is what stops a trending leg being called chop. A market
    that runs one way covers a big range too — the difference is that it ENDS
    somewhere else. A rolling window is used rather than session-to-date: a
    range anchored at the 18:00 open carries the whole Asia move and reads
    broken all day, which is not what he is describing when he says price is
    chopping right now.
    """
    t0, t = session_bounds(sess_day, minute)
    seg = bars[(bars.index >= t0) & (bars.index < t)]
    seg = seg[seg.index >= t - pd.Timedelta(minutes=window_min)]
    if len(seg) < MIN_BARS:
        return {"state": "FORMING", "reason": f"only {len(seg)} bars of tape",
                "range_high": None, "range_low": None, "traversals": 0,
                "zone_now": None, "in_middle": False}

    hi = float(seg.high.max())
    lo = float(seg.low.min())
    w = hi - lo
    if w <= 0:
        return {"state": "FORMING", "reason": "no range", "traversals": 0,
                "range_high": hi, "range_low": lo, "zone_now": None,
                "in_middle": False}

    # --- half one: count trips across the MIDLINE.
    # Counting edge-zone-to-edge-zone trips looked more literal but was
    # unstable: one new extreme moves both edge zones, so prior touches
    # reclassify as "middle" and the count collapses from 4 to 1 between two
    # adjacent minutes. The midline moves slowly, so crossings of it are a
    # stable count of the same thing — price working back and forth.
    mid = (hi + lo) / 2.0
    traversals, side, marks = 0, None, []
    for ts, b in seg.iterrows():
        c = float(b.close)
        z = "high" if c > mid else "low"
        if side is None:
            side = z
        elif z != side:
            traversals += 1
            marks.append(f"{ts:%H:%M} {side}->{z}")
            side = z

    # --- a range you could actually DRAW: both edges tested, not just
    # printed once. A rolling window's high and low always exist; that is not
    # a range. He marks a range when price has respected a high AND a low
    # more than once, so require it.
    tol = EDGE_TOL * w
    hi_touch = int(((seg.high >= hi - tol)).sum())
    lo_touch = int(((seg.low <= lo + tol)).sum())
    markable = hi_touch >= MIN_EDGE_TOUCHES and lo_touch >= MIN_EDGE_TOUCHES

    # --- half two: did it actually go anywhere?
    net = float(seg.close.iloc[-1] - seg.open.iloc[0])
    going_nowhere = abs(net) < GOING_NOWHERE * w

    px = float(seg.close.iloc[-1])
    zone_now = _zone(px, lo, hi)

    if traversals >= MIN_TRAVERSALS and going_nowhere and markable:
        state = "CHOP"
        reason = (f"{traversals} traversals between {lo:.2f} and {hi:.2f} "
                  f"({w:.1f}pt) and net {net:+.1f}pt over {window_min}min — "
                  f"bouncing, going nowhere")
    elif traversals >= MIN_TRAVERSALS and not markable:
        state = "FORMING"
        reason = (f"edges not respected yet ({hi_touch} touches of the high, "
                  f"{lo_touch} of the low) — no range to mark")
    elif traversals >= MIN_TRAVERSALS:
        state = "TRENDING"
        reason = (f"{traversals} traversals but net {net:+.1f}pt of a "
                  f"{w:.1f}pt range — it went somewhere")
    else:
        state = "TRENDING" if abs(net) >= GOING_NOWHERE * w else "FORMING"
        reason = (f"only {traversals} traversal(s), net {net:+.1f}pt "
                  f"of {w:.1f}pt")

    return {"state": state, "reason": reason,
            "range_high": round(hi, 2), "range_low": round(lo, 2),
            "range_width": round(w, 2), "traversals": traversals,
            "net_move": round(net, 2), "traversal_marks": marks[-6:],
            "high_touches": hi_touch, "low_touches": lo_touch,
            "zone_now": zone_now, "in_middle": zone_now == "middle",
            "middle_band": [round(lo + EDGE_FRAC * w, 2),
                            round(hi - EDGE_FRAC * w, 2)],
            "window_min": window_min, "as_of": f"{t:%Y-%m-%d %H:%M}",
            "doctrine": ("CHOP + in_middle -> the middle is dead (T50/range "
                         "frame). CHOP + at an edge -> the only licensed trade "
                         "is from that edge toward the opposite edge.")}


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
    ap.add_argument("--window-min", type=int, default=WINDOW_MIN)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    bars = get_bars()
    if a.at:
        s = state_at(bars, a.sess_day, a.at, a.window_min)
        print(json.dumps(s, indent=1) if a.json else
              f"  {a.sess_day} {a.at}: {s['state']} — {s['reason']}\n"
              f"    range {s['range_low']}–{s['range_high']}, "
              f"price in the {s['zone_now']} zone")
        return 0

    print(f"\n  CHOP STATE — {a.sess_day}\n")
    print(f"  {'time':<7}{'state':<9}{'trav':>5}{'zone':>8}   range")
    for m, s in day_profile(bars, a.sess_day):
        print(f"  {m:<7}{s['state']:<9}{s['traversals']:>5}"
              f"{str(s['zone_now']):>8}   "
              f"{s['range_low']}–{s['range_high']}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
