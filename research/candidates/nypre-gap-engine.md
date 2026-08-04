---
date: 2026-08-04
status: greenlit
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

## Trial ledger — NYP-GAP-01
### Trial 1 — L0 census (2026-08-04)
LOCATION leg PASSES both eras: inside-prior-range opens fill-by-EOD 70%/72%
(2025 n=143 / 2026 n=75) vs outside 47%/35%. CLOCK leg PASSES: fill-by-10:00
37%/39%; gaps unfilled at 10:00 fill later only 36%/26% — the survival flip is
real. CAUSE leg (event-day conditioning) ERA-FLIPS (2025: 44% vs 62% as
claimed; 2026: 67% vs 54% inverted, n=12) → dropped per prereg kill 2; may
only return via the calendar build with proper n and a fresh declaration.
Status: ADVANCING on location+clock to L1 mechanics.

### Trial 2 — L1 mechanics (2026-08-04) — PROFITABLE both eras (base friction)
Inside-range small-gap fade to prior close, stop 1×gap, TS 10:00: 2025 +78 pts
(n=87, +0.89/t, WR 54%; dies at 2pt strict friction −9); 2026 +461 pts (n=34,
+13.55/t, WR 68%; robust at strict +427). Concentration OK (top-3 = 33% of
gross). Era-consistent positive at base; 2025 marginal at the strict bar —
refinement targets 2025 (size/vol conditioning) before grading. Status:
ADVANCING — strongest gap result.
