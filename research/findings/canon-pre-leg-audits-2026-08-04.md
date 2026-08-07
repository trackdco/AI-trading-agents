---
date: 2026-08-04
status: reference
tags: [ny-pre, news, audit]
sources: ["output/funded_book_lucid_fit.parquet", "data/reference/nq_1m_master.parquet"]
---

# AUDIT — the shipped canon's pre leg on event days (2026-08-04)

Tape-defined event flags (no external calendar; self-contained and reproducible):
"8:30-event day" = the 08:30 ET 1-min bar's range in the top decile of all days
(92 days, 10%); "14:00-event day" (FOMC proxy) = 14:00 bar range in the top 3%
(27 days ≈ 8/yr — the FOMC cadence). Canon book = funded lucid fit
(2025-06..2026-07).

## Findings

| Split | Trades | Net | Avg/trade | Win rate |
|---|---|---|---|---|
| Pre leg, 8:30-event days | 7 | **−$461** | −$66 | 29% |
| Pre leg, other days | 220 | +$20,132 | +$92 | 55% |
| Pre leg, FOMC-proxy days | 5 | **−$914** | −$183 | **0%** |
| Pre leg, other days | 222 | +$20,585 | +$93 | 56% |
| Gold leg, 8:30-event days (contrast) | 32 | +$2,937 | +$92 | — |

The canon's pre leg has NEVER won a trade on a Fed day in the fit span (0/5),
and averages −$66/trade on big-data mornings vs +$92 elsewhere. Gold is fine on
event days (+$92/trade) — the damage is specific to pre, consistent with the
documented mechanism (pre-event mornings are fuel-starved; breakout-style
entries fire into compression).

## Honest limits

- n = 7 and n = 5 — direction, not significance. The mechanism (documented
  FOMC-morning compression, pre-8:30 liquidity withdrawal) is what earns the
  follow-up, not the sample.
- The tape flag is DESCRIPTIVE (known only after 08:30/14:00); a live rule must
  be CALENDAR-based (release dates are known in advance) — that reconstruction
  is the next step and also powers nypre-0830-event-tree.

## Routing (per the 5-day-loop law, VALIDATION-PROCESS §9)

A live-canon change ("no pre entries on FOMC days; halve/skip tier-1 8:30
mornings") is an OPTIMIZATION CANDIDATE: logged here, to be validated offline
on the reconstructed calendar (proper n, both eras), then to Angus as a
versioned-release proposal with re-certification. Nothing changes on the live
box off the back of 12 trades.
