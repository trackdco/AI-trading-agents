---
date: 2026-08-04
status: greenlit
tags: [ny-pre, session-structure]
sources: ["articles/sweep-2026-08-04-nypre-stats.md#T2", "articles/sweep-2026-08-04-nypre-structure.md#S7"]
---

# nypre-euro-handoff — trade the Europe→US handoff the ALN numbers describe

## Thesis (for Angus)

The best-measured concept in the entire pre-market file: classify how London
treated the Asia range, at 08:00 ET. When London broke the Asia high but held
the Asia low ("partial engulf up" — 41% of sessions), NY goes on to break that
pattern high 80.8% of the time; the mirror runs 75% — two independent datasets
(2,542 and 4,262 days) agree, and the edge degrades ~30 points if the wrong
side breaks first, giving a built-in invalidation. Meanwhile 08:00–09:30 is
Europe's afternoon squaring window, so the handoff often starts with a partial
retrace as European desks book profits — that retrace is the entry location,
not a contradiction. Wrong side: the US pre-market fader calling a
Europe-established trend "extended" at 08:30. This is also the candidate most
likely to twin with your canon's pre entries (with-trend pullbacks, same
clock) — the redundancy check against the canon's actual fills decides whether
it's a strategy or a rediscovery.

## Skeleton

08:00: ALN classification from session boxes. Engulf-up → buy 08:00–09:30
pullbacks toward London mid / premarket VWAP, target the pattern-high break;
stop under London low; invalidate/flip if the wrong side breaks first.

## Flags

- Candles-only. Target break often lands post-09:30 — semantics ruling needed
  for the carry variant; a flat-by-09:29 variant tests separately.
- Canon redundancy: **HIGHEST of the nine** — pairwise vs canon pre fills is
  the first gate, before any other work.
- Stats are public with TradingView tooling (2024–26 audience growth) —
  recency-weighted decay check mandatory.

## Trial ledger — NYP-EUR-01
### Trial 1 — L0 census (2026-08-04)
ALN base rates re-based on 2025–26: engulf-up → pattern-high first 68.6%
(n=105) / 76.9% (n=65) — PASSES both eras. Engulf-down → 66.2% (n=74) / 60.5%
(n=38) — 2026 marginal, survives the 60% kill by half a point. Published
80.8/75.0 → measured lower but well above coin. Status: census PASSED →
MANDATORY next gate: pairwise redundancy vs the canon's actual pre fills
before any L1 work (highest-overlap candidate by design).
