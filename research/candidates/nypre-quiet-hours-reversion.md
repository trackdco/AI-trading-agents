---
date: 2026-08-04
status: greenlit
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
