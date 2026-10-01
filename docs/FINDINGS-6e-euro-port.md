# FINDINGS — 6E (euro FX future) port: KILLED, and it yields a screening law (2026-09-03)

His ask: test the strategy on EURUSD.

**Verdict: the grammar transfers, the instrument does not.** The level
means something on 6E — at touch fills the win rate is 66.8%, essentially
identical to NQ's 66.4%. But 6E's tick grid is 7–9× coarser relative to
its movement, so the honest-fill rule that costs NQ 40% of its raw edge
costs 6E more than all of it. Negative before costs are even applied, at
every timeframe tested.

The useful output is not the kill. It is a **pre-flight screen for any
future instrument**, in §5.

## 1. Data

Databento GLBX.MDP3, `6E.FUT`, ohlcv-1m, 2025-07-01 → 2026-07-26.
Outrights only (77 of 99 symbols were calendar spreads and were dropped),
volume-rolled to a continuous front month by session volume — the
`gc_continuous.py` rule. **372,149 bars, 279 session-days, 4 rolls**
(2025-09-11, 2025-12-11, 2026-03-12, 2026-06-11), roll days excluded.
223 days survive the engine's session-completeness filter.

Constants derived from 6E's own tape at the NQ/GC ratios: tick 0.00005,
floor 0.0001 (2 ticks), depths 0/1/2/3 ticks, profile bin 1 tick, cap
0.00063. **First warning sign:** the ratio recipe put the profile bin at
0.4 ticks — sub-tick — and it had to be floored at one tick. On NQ the
bin is 4 ticks, on GC 3.

A first pull used `EURUSD.FUT`, which returns the **EFP basis book**, not
the future: prices 0.0000–0.0107 (one negative, impossible for an
outright), 127 bars/day, every symbol `6E:XF:EURUSD:*`. The correct
parent symbol is `6E.FUT`. Recorded so nobody repeats it.

## 2. The structural problem, in one line

| instrument | median active-session 1m candle | in ticks |
|---|---|---|
| NQ | 7.10 pt | **28.4** |
| GC | 2.10 pt | **21.0** |
| 6E | 0.00015 | **3.0** |

6E moves three ticks a minute. Everything downstream follows: the
structural stop has a 4-tick median (35% of trades pinned at the 2-tick
floor, vs NQ 20% / GC 36%), and one tick is a quarter of the whole stop.

| instrument | 1 tick | median stop | tick as % of stop |
|---|---|---|---|
| NQ | 0.25 | 8.50 | **3%** |
| GC | 0.10 | 1.70 | **6%** |
| 6E | 0.00005 | 0.00020 | **25%** |

## 3. The measurement: the grammar works, the fill rule kills it

PD value area, 1m, SAR, news gate, depth 3 ticks / 1R, n≈900:

| fill rule | n | WR | raw EV/trade | EV @1 tick cost |
|---|---:|---:|---:|---:|
| touch (optimistic) | 915 | **66.8%** | **+0.2818** | −0.0188 |
| one tick through (the certified spec) | 850 | **34.5%** | **−0.3312** | −0.6325 |

**Read the first row.** 66.8% at 1R with zero re-tuning is the same
number the NQ 8-level book prints (66.4%). Prior-day value area prices
the euro future exactly as the auction-physics claim (§25) predicts.

**Read the second.** Requiring one tick through the level — the same
honesty haircut that took NQ from 56% to 53.7% and cost 40% of its raw
edge (§2) — takes 6E from 66.8% to 34.5% and costs 118% of it. Same
rule, ten times the bite, because the tick is 25% of the stop instead
of 3%. And even the optimistic touch-fill row is already negative once a
single tick of cost goes on.

Full grid, all 20 depth × target cells: **every one negative**, raw and
net, best case −282R raw / −538R at a 1-tick cost. Split-half on the
best cell: IS −0.342 / OOS −0.321 raw. Consistently, structurally dead —
not noise.

## 4. Does a slower signal rescue it? No.

Honest fills, best depth cell at 1R:

| tf | n | WR | median stop | tick/stop | raw EV | @1 tick | signals/day |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1m | 850 | 34.5% | 4.0t | 25% | −0.3312 | −0.6325 | 3.8 |
| 5m | 928 | 47.3% | 6.0t | 17% | −0.1429 | −0.3377 | 4.2 |
| 15m | 1,042 | 49.9% | 9.0t | 11% | −0.1259 | −0.2592 | 5.0 |

Win rate climbs exactly as the tick/stop ratio falls — which confirms the
mechanism — but it converges on 50%, the break-even line for a 1R target,
and never approaches NQ's 66%. Raw EV stays negative at every timeframe.
30m is not testable: the engine requires ≥50 signal candles per session
and 30m yields ~28.

Note this **inverts** the program's most-replicated gradient. On NQ and
GC, tf1 > tf3 > tf5 monotonically (§22). On 6E slower is strictly better,
because the binding constraint is not signal quality — it is grid
coarseness. Same finding from the other side.

## 5. THE SCREENING LAW (the reusable output)

Before pulling data or writing an instrument entry, measure one number:
**the median active-session 1-minute candle, in ticks.**

| | ticks/candle | tick as % of stop | outcome |
|---|---:|---:|---|
| NQ | 28 | 3% | +0.1375R/trade |
| GC | 21 | 6% | works, 2025-26 |
| **6E** | **3** | **25%** | **dead before costs** |

The grammar needs room between the level and the stop for the honest fill
not to eat the trade. A candidate instrument wants **≥20 ticks of median
1-minute movement**; under ~10 the honest-fill tax is fatal and no
constant re-derivation fixes it, because the problem is the exchange's
price grid, not the tape.

This screen costs one afternoon and would have killed 6E before any of
this work. Apply it to ES, CL, 6B, RTY before anything else.

## 6. Bug found and fixed (affects any fine-tick instrument)

`pd_va_backtest.py` hard-coded 2 decimal places when writing `entry`,
`stop`, `risk` and `pts` to the trade dump. Correct for NQ (0.25 tick)
and GC (0.10). For 6E every risk rounded to **0.0**, which silently
zeroed the field and made the cost overlay divide by zero. Fixed to
derive precision from the tick: `max(2, ceil(-log10(tick)) + 1)` → 2 dp
for NQ, 2 for GC, 6 for 6E. **NQ and GC dumps are unchanged.**

## 7. What was NOT run, and why

The other four level families, the VWAP books, the 8-level merge, arming
and conviction sizing were all skipped. The base spec is negative before
any of them, and layering on a negative base measures nothing. If the
screening law in §5 ever admits a new FX-style instrument, the layers get
their proper out-of-sample run there.

## 8. Caveats

- 13 months of data (223 tradeable days) against NQ's four years. The
  split-half is thin. It does not matter here: the effect is a 32-point
  win-rate collapse, not a marginal call.
- The touch-fill row is not a tradeable result — it is the diagnostic
  that isolates the fill rule as the cause. Touch fills are known
  optimistic (§2) and are not a proposal.
- One cost assumption band (1–2 ticks/RT). The result is negative before
  cost, so the band does not change the verdict.
- The 18:00 ET session anchor and the US-only news gate were used
  unchanged. Both are wrong-ish for the euro (its day is European, and
  the gate misses ECB releases). Neither was corrected, because a
  −0.33R raw edge is not rescued by moving the anchor. If §5 ever
  admits a currency, fix both before testing it.
