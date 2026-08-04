---
date: 2026-08-04
status: greenlit
tags: [ny-pre, overnight-structure, amt]
sources: ["articles/sweep-2026-08-04-nypre-structure.md#S2", "articles/sweep-2026-08-04-nypre-stats.md#T3"]
---

# nypre-inventory-correction — the 09:30 inventory flush, mechanized

## Thesis (for Angus)

The academic and the profile-school stories converge here: overnight returns
NEGATIVELY predict the first half-hour of RTH (published), and Dalton's
doctrine says 100% one-sided overnight inventory gets corrected at the open —
weak-handed overnight holders finally have the liquidity to exit, and
short-covering gets misread as new buying by the crowd that pays. Everyone
TEACHES this; nobody has published hard NQ numbers — the quantification is the
edge. Plus our novel question: does the pre-market front-run its own
correction as cash-linked flow arrives from 09:00? If yes, the entry is
09:00–09:25, not 09:30, and the naive at-open fade gets a worse price.

## Skeleton

Inventory = % of ETH closes above prior settlement (measured 08:55 AND 09:25 —
the difference tests front-running). ≥95% one-sided, not a true outside-range
gap: counter-inventory entry on first 1-min structure failure after 09:00,
target settlement, stop at new ON extreme, hard exit 09:50.

## Flags

- Candles-only. Interacts with gap-engine and euro-handoff on overlapping days —
  the day-classification matrix keeps the fades on disjoint slices.
- **May hold through 09:30** — semantics ruling needed.
- Canon redundancy: LOW-MEDIUM (fade logic vs the canon's with-trend pullbacks).
- Post-2021 re-verification mandatory (the regime the academic result predates).
