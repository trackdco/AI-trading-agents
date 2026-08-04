---
date: 2026-08-04
status: thesis-pending
tags: [ny-pre, session-structure, news]
sources: ["articles/sweep-2026-08-04-nypre-structure.md#S3", "articles/sweep-2026-08-04-nypre-stats.md#T8", "articles/sweep-2026-08-04-nypre-macro.md#M6"]
---

# nypre-gap-engine — gap logic done with the conditioning retail skips

## Thesis (for Angus)

Gap-fading is the most crowded idea in futures — and the published aggregate
hides three conditionals that change everything: (1) LOCATION — inside
yesterday's range fills at high rates, outside + large fills ~8–21% (fade one,
never the other); (2) CAUSE — a gap minted by an 08:30 print that held resists
filling; a flow-gap on an empty morning reverts; the decomposition (how much
gap existed at 08:25 vs 09:29) appears in no public study; (3) TIME — 34% of
fills happen in the first 5 minutes and only 39% of fills start after the first
half hour, so a gap surviving to 10:00 flips to continuation. The wrong side is
the mechanical fader pricing size but not location, cause, or clock. Includes
the pre-fill variant: entering from the pre-market extreme 08:30–09:25 before
the 09:30 fade crowd.

## Skeleton

At 09:25: classify {size, in/out prior range, pre-vs-post-08:30 components}.
Inside+small+no-news → fade toward prior close (pre-bell entry on PM-extreme
failure), time-stop 10:00. Survival at 10:00 unfilled → flip with the gap.
Outside-range/news-held → no fade, optionally join.

## Flags

- Candles + release calendar. Event tree: fade ↔ survival-flip, one family.
- **Holds through 09:30** in most branches — semantics ruling needed.
- Canon redundancy: LOW (different logic entirely).
- Expect much of the value as AVOIDED losses (not fading the wrong gaps).
