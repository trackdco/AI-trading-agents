#!/usr/bin/env python3
"""ARE WE CHOPPING? — his definition, v2 (window-local), hard-coded.

    python -m scripts.chop_state 2026-06-02
    python -m scripts.chop_state 2026-06-02 --at 09:42 --json

V2, from his correction 2026-08-19, verbatim:

    "When I'm in London, if we're taking a trade in the second half of
     London and the first half of London was just chopping in a given
     range, then I'm gonna say that's chop. If, in New York, we have 20
     minutes of candles stalling, I call that chop. I'm not looking at
     whether it's been choppy the last three hours and I'm not looking at
     whether it's in a specific point range... if in the last hour we've
     traded in a 50-point range in London... in the second half of London
     I'm gonna be like, this is choppy price action. I got to be careful
     with how I trade this."

So chop is WINDOW-LOCAL and TIMESCALE-ADAPTIVE, not a fixed 3-hour rolling
window (v1's mistake — HOURS=3.0 / SMALL_PT=104.0 was a literal reading of
an earlier, looser description; he corrected it):

    LONDON context (clock < 08:00): the trailing 60 MINUTES — "the first
        half of London" once you are in the second half, the pre-open hour
        when you are coming in.
    NY context (clock >= 08:00): the trailing 20 MINUTES — "20 minutes of
        candles stalling."

WHAT "SMALL" MEANS — calibrated, and it validates his feel. Trailing
ranges pooled across the 87 session-days of 2026-01..04 (frozen BEFORE the
test months; recomputing over 2023+ days deflates the thresholds because
NQ traded at half the price):

    LONDON 60m: p10 36 · p25 44.5 · median 63 · p75 95.5
    NY     20m: p10 36 · p25 53   · median 86 · p75 128

His illustrative number — "a 50-point range in London" — sits at p28 of
the measured London distribution. Feel and measurement agree; the London
threshold uses HIS 50, the NY threshold uses the same percentile (53).

THE STATE

    CHOP       trailing window-local range is small (bottom ~quartile)
    TRENDING   it is not
    FORMING    not enough tape yet

Plus WHERE price sits for the range map: `zone_now` low/middle/high with
the middle as the inner half (T50's definition, unchanged). NOTE (T79):
the map's middle-dead veto is judged by the REJECTED LEVEL, never by
`zone_now` — this detector supplies the state and the edges, it does not
veto anything.

EVERYTHING IS AS-OF: minute t uses only bars strictly before t.

WHAT THIS DETECTOR STILL DOES NOT DO: predict which trades win. It is a
caution flag and a map ("I got to be careful with how I trade this"), not
a day-quality filter.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.offline_briefings import (get_bars, session_bounds)   # noqa: E402

EDGE_FRAC = 0.25          # inner half = the middle (T50), unchanged
NY_CLOCK = 8 * 60         # minutes-of-day boundary between contexts

# his 2026-08-19 definition, calibrated 2026-01..04 (87 days), FROZEN:
LOOKBACK_MIN = {"LONDON": 60, "NY": 20}
SMALL_PT = {"LONDON": 50.0,   # his number; p28 of the measured distribution
            "NY": 53.0}       # the same percentile of the NY 20m distribution


def _context(minute: str) -> str:
    hh, mm = minute.split(":")
    return "NY" if int(hh) * 60 + int(mm) >= NY_CLOCK else "LONDON"


def _zone(px: float, lo: float, hi: float) -> str:
    w = hi - lo
    if w <= 0:
        return "middle"
    if px <= lo + EDGE_FRAC * w:
        return "low"
    if px >= hi - EDGE_FRAC * w:
        return "high"
    return "middle"


def state_at(bars: pd.DataFrame, sess_day: str, minute: str,
             lookback_min: int | None = None,
             small_pt: float | None = None) -> dict:
    """CHOP when the window-local trailing range is small. His v2
    definition, nothing added: London judges the trailing hour, NY the
    trailing 20 minutes."""
    ctx = _context(minute)
    lb = lookback_min or LOOKBACK_MIN[ctx]
    thr = small_pt or SMALL_PT[ctx]
    t0, t = session_bounds(sess_day, minute)
    start = max(t0, t - pd.Timedelta(minutes=lb))
    seg = bars[(bars.index >= start) & (bars.index < t)]
    if len(seg) < lb * 0.8:
        return {"state": "FORMING", "reason": f"only {len(seg)} bars of the "
                f"trailing {lb}m", "context": ctx,
                "range_high": None, "range_low": None, "zone_now": None,
                "in_middle": False}

    hi, lo = float(seg.high.max()), float(seg.low.min())
    w = hi - lo
    px = float(seg.close.iloc[-1])
    zone = _zone(px, lo, hi)

    if w <= thr:
        state = "CHOP"
        reason = (f"{w:.0f}pt trailing {lb}m range ({lo:.2f}–{hi:.2f}) — "
                  f"small for {ctx} (threshold {thr:.0f}pt): "
                  f"'this is choppy price action, be careful how you trade it'")
    else:
        state = "TRENDING"
        reason = f"{w:.0f}pt trailing {lb}m range — not small for {ctx}"

    return {"state": state, "reason": reason, "context": ctx,
            "lookback_min": lb, "small_threshold_pt": thr,
            "range_high": round(hi, 2), "range_low": round(lo, 2),
            "range_width": round(w, 2),
            "zone_now": zone, "in_middle": zone == "middle",
            "middle_band": [round(lo + EDGE_FRAC * w, 2),
                            round(hi - EDGE_FRAC * w, 2)],
            "as_of": f"{t:%Y-%m-%d %H:%M}",
            "doctrine": ("CHOP is a caution and a map: edges are the trade, "
                         "structural targets govern (0.4.9); the middle-dead "
                         "veto is judged by the REJECTED LEVEL, not by "
                         "zone_now (T79).")}


def day_profile(bars: pd.DataFrame, sess_day: str, step: int = 15) -> list:
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
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    bars = get_bars()
    if a.at:
        s = state_at(bars, a.sess_day, a.at)
        print(json.dumps(s, indent=1) if a.json else
              f"  {a.sess_day} {a.at}: {s['state']} — {s['reason']}\n"
              f"    range {s['range_low']}–{s['range_high']}, "
              f"price in the {s['zone_now']} zone")
        return 0

    print(f"\n  CHOP STATE v2 — {a.sess_day}\n")
    print(f"  {'time':<7}{'ctx':<8}{'state':<10}{'width':>7}{'zone':>8}   range")
    for m, s in day_profile(bars, a.sess_day):
        print(f"  {m:<7}{s.get('context','?'):<8}{s['state']:<10}"
              f"{(s.get('range_width') or 0):>6.0f}pt{str(s['zone_now']):>8}   "
              f"{s['range_low']}–{s['range_high']}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
