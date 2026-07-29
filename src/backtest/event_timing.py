"""Event-day timing floor (v0.6 B1/B2) — the mechanical half of the event-day fix.

Angus's 4-year delayed-entry test (docs/ENGINE-RESPONSE-2026-panel-leak.md) found that a
blanket delay sign-flips by year, but two RELEASE-TIME-CONDITIONAL rules hold up
(+$13k/4yr event-day floor, green 3 of 4 years):

  R1  release <= 09:30 ET  ->  MOMENTUM-book entries wait until release + N min (N=10)
  R2  release >= 10:00 ET  ->  ROTATION-book entries are blocked pre-release

Tape logic: an early (08:30-class) release resolves into momentum structure — wait for the
number, trade the reaction. A late (10:00) release leaves the morning as pre-event chop
that poisons rotation reclaims — don't fade a market that's waiting. The rules are
book-specific and bucket-specific; per Angus, do NOT extend either beyond its bucket
(rotation-early and momentum-late both sign-flip).

This is a TRIGGER FILTER (same semantics as the tested harness — a pre-release trigger is
dropped, not deferred), so it needs no change to simulate()'s hot path and is byte-identical
when not applied. The R1/R2 policy lives here; the caller decides which book it is running
and whether the floor is enabled (config-gated, split-testable).
"""

from __future__ import annotations

from datetime import time as dtime

import pandas as pd

R1_CUTOFF = dtime(9, 30)      # releases at/before this fire R1 (momentum delay)
R2_CUTOFF = dtime(10, 0)      # releases at/after this fire R2 (rotation pre-release block)
DEFAULT_DELAY_MIN = 10
WINDOW_END = dtime(10, 15)    # the desk's trade window; releases after it don't gate the AM


def event_entry_floor(calendar: pd.DataFrame, book: str,
                      delay_min: int = DEFAULT_DELAY_MIN) -> dict[str, pd.Timestamp]:
    """Earliest allowed entry ts per day for `book` in {"momentum", "rotation"}, from the
    high-impact release schedule. Days with no applicable release are absent (no floor).

    calendar: columns datetime_ET (tz-aware), impact. Only high-impact releases inside the
    morning window (<= WINDOW_END) are considered — a 14:00 FOMC does not gate the AM.
    """
    if book not in ("momentum", "rotation"):
        raise ValueError(f"book must be 'momentum' or 'rotation', got {book!r}")
    hi = calendar[(calendar["impact"] == "high")
                  & (calendar["datetime_ET"].dt.time <= WINDOW_END)]
    floor: dict[str, pd.Timestamp] = {}
    for _, e in hi.iterrows():
        rel = e["datetime_ET"]
        t = rel.time()
        if book == "momentum" and t <= R1_CUTOFF:              # R1
            g = rel + pd.Timedelta(minutes=delay_min)
        elif book == "rotation" and t >= R2_CUTOFF:            # R2
            g = rel                                            # block only pre-release
        else:
            continue
        d = rel.strftime("%Y-%m-%d")
        floor[d] = max(floor.get(d, g), g)                     # latest gating release wins
    return floor


def apply_timing_floor(triggers: list, floor: dict[str, pd.Timestamp]) -> list:
    """Drop triggers whose ts falls before the day's floor. Empty floor -> unchanged list
    (byte-identical to no-floor). A trigger's day is the calendar date of its ts."""
    if not floor:
        return list(triggers)
    kept = []
    for t in triggers:
        ts = pd.Timestamp(t.ts)
        g = floor.get(ts.strftime("%Y-%m-%d"))
        if g is None or ts >= g:
            kept.append(t)
    return kept
