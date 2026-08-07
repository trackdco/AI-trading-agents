---
date: 2026-08-04
status: greenlit
tags: [london, session-structure, order-flow]
sources: ["articles/sweep-2026-08-04-orderflow.md#OF1", "articles/sweep-2026-08-04-amt.md#AMT2", "articles/sweep-2026-08-04-session-vwap.md#SS1"]
---

# london-asia-sweep-reversal — fade the failed London probe of the Asian range

## Thesis (for Angus)

All night, Asia builds a thin, low-participation range, and the obvious stops
accumulate just beyond its high and low — range traders' stops plus breakout
stop-entries. When European liquidity switches on, the recurring sequence is a
push through one side of that range that finds no real business at the worse
price: the move fills large passive orders against the triggered stops, and once
the stop pool is spent there's nothing behind it. The wrong side is the breakout
chaser and the overnight holder with their stop at the obvious extreme; their
covering is the fuel for the drive back through the range. The sweep also tends
to terminate stretched (+2σ-ish of overnight VWAP), so the fade is buying
rejection at bad-price-for-them, good-location-for-us. This is Dalton's
open-test-drive played at session scale, and it's the single most-taught session
pattern in retail — which cuts both ways: crowded as lore, but the retail
breakout stops ARE the liquidity the trade collects.

## Mechanical skeleton

Asian range = 1-min high/low over a parameterized window (test 19:00→02:00,
20:00→00:00 ET). In 03:00–05:00 ET: break beyond an extreme that FAILS acceptance
(no N consecutive 1-min closes outside; re-entry within M minutes) → enter on the
close back inside. Stop beyond the sweep extreme + buffer. T1 Asia mid /
overnight VWAP; T2 opposite extreme. Time-stop 06:00 ET. Acceptance outside =
this trade stands down and the continuation candidate arms instead.

## Flags

- **Event-tree pair** with `london-asia-sweep-continuation` — same trigger, split
  by acceptance + timing. Tested as ONE family in the trial ledger.
- Data: candles-only; flow overlay (CVD fade / absorption at the extreme) optional.
- Crowding: EXTREME (ICT "Judas swing"). Expect noisy edge; demand the failure
  confirmation — naive London-breakout entries run 40–60% WR in the FX literature.
- NY-canon input-family overlap: MEDIUM-LOW (session structure; NY reads
  overnight structure via AGE).
- Open-type gate applies: stand down on drive opens.
