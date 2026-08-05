---
date: 2026-08-05
status: thesis-pending
tags: [london, session-structure, trigger-density]
sources: ["articles/2026-08-05-channel-map-four-traders.md", "findings/london-nq-what-three-traders-agree-on.md", "findings/london-window-LDN-WIN-01.md", "https://www.youtube.com/watch?v=hcVhQBAGGFw", "https://www.youtube.com/watch?v=JySO8cOWOIs", "https://www.youtube.com/watch?v=1noM1ogc5zM"]
---

# london-nq-open-break — the 08:00 UK level break on NQ, with a stop tight enough to pay

## Thesis (for Angus)

At 08:00 UK the London cash market opens and NQ gets its first real European
liquidity of the day. In the ninety minutes before that, price has been drifting
in a thin book and has left obvious marks — a high, a low, the edges of the
overnight balance. Those marks are where the orders sit, because they are the
only structure anyone can see.

When the open arrives, the first thing that happens is one of those marks gets
tested. Either real size is behind the move and it goes, or it isn't and price
snaps back through the people who chased it. **The trade is that resolution**, and
it happens in a tight window because the open is a scheduled event, not a mood.

The wrong side is whoever committed to the pre-open drift — someone who bought
the high at 07:40 on 200 contracts of evidence and finds out at 08:00 what
4,000 contracts think.

**Why I believe the clock and not just the trader.** Three independent sources
land on the same minute and none of them got it from each other:

- Brandan trades it as **08:00 UK sharp**, marking his levels from 07:55
- EzTrades' completely different model (PO3/IFVG) calls **03:00 ET** the
  manipulation window — the same instant
- And our own measurement, `LDN-WIN-01`, found **03:00 ET is the volume peak of
  the entire session, in both eras**, with a second peak at 04:00

I ran that measurement before reading either trader's clock. The agreement was
not arranged.

**Why the geometry is the point, not the setup.** This is a level break — the
most-taught idea in trading, and on its own worth nothing. Tradesharpe, who
trades a version of it, says so outright: naive opening-range breakouts backtest
to *"like a 50% win rate... the issue is stop loss is not optimized."* His fix is
not a better trigger, it is a tighter stop: *"you are wasting so much
profitability by running stops below that whole open candle."*

Brandan runs the same conclusion as a number: **~10-point stop on MNQ,
"predominantly 10", exiting at 1:2.** Fabio, on a different continent and a
different setup, describes his A+ trade as *"really low risk"* and names slippage
as the only thing that worries him.

**That axis is the one this programme has already died on.** `nypre-euro-handoff`
reached 78% win rate and paid +0.02R, tombstoned as *"the handoff is a fact, not
a trade — its natural geometry cannot pay per unit risk."* The published version
of this candidate arrives with the fix already attached. That is the reason to
test it and it is the only genuinely novel thing about it.

**What I do not believe.** The video is titled *"89.5% Win Rate"*. Inside the
same video he says *"if we know there's a 60 to 70% win rate."* In his December
backtest he re-scores a logged loss as *"realistically break even... nearly hit
our take profit."* He sells prop-firm discount codes throughout. **The hit rate
is marketing.** The number that decides this is R, which he never quotes — a
10-point stop at 2R needs about 35% to break even before costs, and that is the
bar we are actually testing against.

## Skeleton

Instrument **NQ** (he trades MNQ; same contract, different multiplier).

Before 08:00 UK: mark the pre-open structure — pre-open high/low over a declared
lookback, plus the overnight extremes we already carry in the substrate.

From 08:00 UK (03:00 ET; **use `euro_open_clock`, never `euro_open_det` —
`docs/FINDING-euro-open-det-is-noise.md`**): on a test of a marked level, trade
the resolution. **Two declared entry arms and they are the whole experiment:**

- **A — close-confirmed** (Tradesharpe): wait for a candle to close beyond the
  level, enter on the break of that candle's high/low
- **B — touch** (Brandan): enter on the reaction at the level, no close required

Stop: beyond the trigger candle, **not** beyond the whole range. Target 2R fixed
initially, with next-structural-level as a declared alternative. Flat by 05:00 ET
per `LDN-WIN-01` — the 05:00–06:00 hour carries the worst efficiency in the
session and should not be inherited.

## Promotion rule — declared BEFORE any tournament (§6.0.1)

Rank-and-promote-the-top-scorer is a condemned procedure. So the winner here is
named in advance, on mechanism, not on results:

**Default spec = arm A, close-confirmed entry.** It is the mechanism prior: the
thesis is that the open *resolves* a level test, and a close beyond the level is
what resolution looks like. An entry on touch is a bet placed before the
resolution the thesis is about. A also inherits the tighter stop the whole
candidate rests on — the trigger candle exists only if you waited for it.

**Arm B (touch entry) may displace A only if BOTH hold:**
1. PBO on the A/B arm matrix is **< 0.5** (CSCV, day-level rows), and
2. the holdout adjudicates in B's favour under §5.9.4's single corrective
   iteration.

**In-sample rank alone never promotes B.** If B out-earns A in sample and fails
either condition, the frozen spec stays A and B is ledgered as a declared
negative result.

**If both arms fail their own bars, neither ships.** The candidate is not
promoted by being the better of two losers.

## Bars — pre-registered per §5.9.3 and §5.9.5

- **Census (L0) kill line, per §5.9.1:** this dies at census ONLY if the claimed
  behaviour does not happen — i.e. if levels marked before 08:00 UK are not
  tested in the window, or tests do not resolve. **Raw profitability does not
  kill at census.** Ugly P&L at raw triggers sends it to the variable search, it
  does not close the family.
- **Sleeve bars:** era consistency (2025/2026 agree in direction, plus the
  inverse pass), cost realism at the standard stack **and at 2× slippage**, and
  **PSR(0) ≥ 0.75** per §5.9.5.
- **Deflation is charged at book level** (§5.9.3), not against this sleeve alone.
- **Every trial goes to `output/trial_ledger.parquet` at trial time**, not just
  into this file's prose (§6.0.2).

## Flags

- **Data: fully in hand.** `nq_1m_master.parquet` and the 912-day London
  substrate. No purchase, no new plumbing.
- **A-vs-B is one binary variable over one trigger**, not two strategies. It is
  the cheapest informative experiment available here and it resolves a real
  disagreement between two live traders.
- **The stop rule is the transferable component.** If trigger-candle stops beat
  structural stops here, that result should be tried on triggers we already own —
  which is worth more than this candidate is.
- Costs are the kill test, not a formality. A ~10-point stop on NQ is a handful
  of ticks; Fabio names NQ slippage as the one thing that breaks his version.
  The 2× slippage arm decides this candidate.
- Redundancy: check `pairwise_overlap` against the canon's fills at census time,
  per program flag 1. Different session from the NY canon, so expected low, but
  measured not assumed.
- Instrument-transfer caveat: Brandan's other content is NAS100/US30 CFDs and
  gold. The structure transfers; the cost stack does not.

## Trial ledger — LDN-OBK-01

_Awaiting Angus greenlight. No trials run._
