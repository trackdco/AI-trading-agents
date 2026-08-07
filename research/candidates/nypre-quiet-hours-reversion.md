---
date: 2026-08-04
status: killed
tags: [ny-pre, session-structure]
sources: ["articles/sweep-2026-08-04-nypre-stats.md#T4", "articles/sweep-2026-08-04-nypre-structure.md#S5"]
---

# nypre-quiet-hours-reversion — fade false breaks in the dead hours before the data

## Thesis (for Angus)

By 04:00 ET Europe's repricing is done and the US information anchor (08:30)
hasn't arrived: the 04:00–08:30 stretch is structurally drift-free (the
around-the-clock decomposition puts all the average return in the Euro-open
hours; the rest is noise). In a thin book with nobody initiating size before
the number, hourly-range breakouts lack follow-through: the published NQ
numbers say false breaks of the prior hour's range revert to the hour midpoint
at 76–83.5%, best at 06:00–08:00 ET. Wrong side: the breakout chaser in a book
where no institutional flow ratifies the move. Two honest warnings baked in:
this exact stat was POPULARIZED in 2025 (dashboards, scripts) so the
pre/post-2025 decay split is mandatory, and the real enemy is slippage in a
thin tape, not the win rate — our depth data prices that properly.

## Skeleton

Hours 06:00/07:00/08:00: break of prior hour's high/low then a 1-min close back
inside → toward the hour midpoint; stop beyond the false-break extreme;
time-stop end of hour. Skip when a tier-1 08:30 release is <30 min away.

## Flags

- Candles-only; depth used for slippage realism. Fully pre-09:30 — no
  semantics ruling needed.
- Canon redundancy: LOW-MEDIUM (earlier clock than the canon's 08:00 start for
  two of three hours; the 08:00 hour overlaps — test exclusion).
- Sister of the London hourly family — if both survive, they're cousins by
  construction (input-family accounting applies).

## Trial ledger — NYP-QH-01
### Trial 1 — L0 census (2026-08-04) — KILLED
Reversion-to-mid after prior-hour false breaks, our definition (1-min close
beyond → close back inside → mid touch before hour end): 43–53% across all
three hour-slots in BOTH eras (n=87–178 per cell) — nowhere near the published
76–83.5%, below the 60% kill floor everywhere. Popularization split flat
(49/49/48%) — no decay because no edge existed in our sample. Kill 1 executes.
TOMBSTONE: the Magic Hours stat does not replicate on 2025–26 NQ under a
mechanical trigger. Reopening burden: evidence our trigger definition
materially differs from the source's AND a re-census under the source's exact
definition clearing 65% in both eras.
