---
date: 2026-08-04
status: greenlit
tags: [london, order-flow, depth]
sources: ["articles/sweep-2026-08-04-orderflow.md#OF5", "articles/sweep-2026-08-04-orderflow.md#OF6", "articles/sweep-2026-08-04-orderflow.md#OF7"]
---

# london-level-defense-flow — trade with the institution defending a level in a thin tape

## Thesis (for Angus)

Absorption is aggressive market orders hammering a level while price refuses to
move — someone big is passively taking the other side and defending. In the
London tape this is unusually visible: so few natural participants are active
that a defending institution can't camouflage, and the reload pattern (volume at
one price far exceeding displayed depth — icebergs) prints as an anomaly. The
trade is with the defender at overnight/prior-day references: the absorbed
aggressors are underwater immediately, and their covering fuels the rotation away
from the level. CVD exhaustion is the same story at session extremes — a new high
on a delta lower-high is an extension made of covering and stops, not initiative
buying, with the last entrants trapped. And the failure mode is a second trade:
a pulled or consumed iceberg means the level SHOULD break hard — flip with it.
This is the candidate that uses our depth/footprint data advantage hardest, and
the one closest to how order flow validated your NY entries.

## Mechanical skeleton

Flow-essential (June 2025+ span only). Near a tracked level: rolling 3–5 min
aggressive delta into the level ≥ hour-conditioned threshold while price progress
≤ a few ticks → absorption; enter with the defense on the first rejection close
away. Iceberg proxy: volume at one price ≥ N× displayed depth, price pinned.
Stop: a few ticks beyond the defended extreme (defender pulls = thesis dead, out
fast). Targets: session VWAP, overnight mid. Flip rule: post-detection close
beyond the level → reverse with the break. CVD-divergence variant fades new
session extremes on delta non-confirmation.

## Flags

- Data: candles+flow REQUIRED — testable only on June 2025→July 2026 (plus the
  six holdout months' footprint files). Smaller sample; bars must be set with
  that honesty.
- Crowding: LOW in execution terms (data barrier filters retail); ~undocumented
  mechanized on London NQ.
- **NY-canon input-family overlap: HIGH — depth walls + order flow are the NY
  canon's core families. The same-account veto will almost certainly trip;
  Angus waiver decision expected at co-ship time.** Return correlation may still
  be low (different window) — measured at validation.
- Sibling: `london-level-trap-fade` (candles expression, bigger sample) — one family.
