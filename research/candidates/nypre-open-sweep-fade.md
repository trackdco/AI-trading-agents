---
date: 2026-08-04
status: greenlit
tags: [ny-pre, order-flow, session-structure]
sources: ["articles/sweep-2026-08-04-nypre-stats.md#T7", "articles/sweep-2026-08-04-nypre-stats.md#T1"]
---

# nypre-open-sweep-fade — fade the first-minutes stop-run of the WRONG extreme

## Thesis (for Angus)

The open's version of the London sweep trade, with a conditioning nobody has
published: the polarity stat says which overnight extreme SHOULD break first
(76%). When the first minutes of RTH instead break the OTHER extreme by a small
increment and close back inside, that break is a stop harvest against the
grain — the trapped party is the breakout chaser buying the pre-market high
break in minutes 1–15, providing exit liquidity before the range rotates. The
"Judas at 9:30" narrative is the most crowded story in retail NQ, which cuts
both ways: crowded stops make the sweep real; the unpublished
wrong-side-conditional is our edge over the crowd trading it naively.

## Skeleton

Minutes 1–15 post-open: break of the NON-predicted PM/ON extreme by <25% of ON
range + CVD divergence + 1-min close back inside → fade toward premarket VWAP
then ON mid. Stop beyond sweep extreme.

## Flags

- Candles + CVD (absorption at the extreme is load-bearing → strongest on the
  flow span). Event-tree pair with `nypre-on-polarity`.
- **Trades after 09:30** — outside the canon's pre window entirely; execution-
  semantics ruling needed (new session territory on the shared account).
- Canon redundancy: LOW (canon is flat post-09:30 pre-leg).
- In-house number to extract first: P(reverse | wrong-side first break).
