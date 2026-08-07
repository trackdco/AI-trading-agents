---
date: 2026-08-04
status: greenlit
tags: [london, overnight-structure, amt]
sources: ["articles/sweep-2026-08-04-orderflow.md#OF3", "articles/sweep-2026-08-04-amt.md#AMT4"]
---

# london-level-trap-fade — failed breaks of the levels everyone watches

## Thesis (for Angus)

The overnight high/low and prior-day RTH high/low are the most-watched levels on
the board, with stop clusters just beyond them. A London-window break of one that
snaps back inside within minutes was a liquidity run, not a repricing: the stops
beyond the level were the target, and once consumed there's no flow to sustain
the move. The trapped breakout entrants' liquidation fuels the rotation back.
The refinement that lifts this above the generic version is level QUALITY from
profile structure: a poor/flat prior-RTH extreme (multiple equal touches, no
rejection tail) is an incomplete auction — on its FIRST revisit it tends to hold
(fade with the trapped defenders' help), while a second revisit tends to
break-and-run (the defenders are spent; go with it). London is frequently the
session that travels back to these references, and far fewer participants execute
there than at the NY open. This is the closest cousin to how you already trade —
levels plus trapped participants — expressed mechanically.

## Mechanical skeleton

Track ONH/ONL (rolling since 18:00 ET), PDH/PDL (prior RTH), and mark poor/flat
extremes (≥2–3 touches within a few ticks, no excess tail). In 03:00–06:00 ET:
break ≥ X ticks beyond a level, then a 1-min close back through it within ≤ N
minutes → enter the reclaim. Stop beyond the trap extreme. Targets: overnight
VWAP, mid-range, opposite reference. Second-revisit variant flips to stop-entry
through the level. Kill stagnant trades at 30–45 min.

## Flags

- Data: candles-only; footprint (absorption on first touch vs thin pull-away on
  second) upgrades the two-stage logic where flow data exists.
- Crowding: failed-breakout fading is decades old; the London-window NQ
  application and the poor-extreme conditioning are thinly documented.
- NY-canon input-family overlap: MEDIUM (overnight structure).
- Sibling: `london-level-defense-flow` is the flow-native expression of the same
  defense mechanism — one family in the trial ledger.
