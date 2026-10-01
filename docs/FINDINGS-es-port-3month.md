# FINDINGS — ES port, 3-month look (2026-09-03)

His ask: run the NQ strategy on ES, three months, "to see if it would
work at all."

**Answer: the signal works, the economics do not — on this evidence.**
ES prints a 66.7% win rate at 1R, the same number NQ prints, and carries
73% of NQ's raw edge per trade. Then cost eats 73% of that edge (NQ: 20%),
because **an ES tick is $12.50 and an NQ tick is $5.00** while ES moves a
quarter as much per minute. It lands at +0.05R/trade at the most generous
cost assumption and goes negative at a realistic one.

Not dead like 6E. Not viable on 57 days either. It is the boundary case.

## 1. The screen predicted this

`docs/FINDINGS-6e-euro-port.md` §5: measure the median active-session
1-minute candle in ticks; want ≥20.

| instrument | median 1m candle | in ticks | screen | outcome |
|---|---:|---:|---|---|
| NQ | 7.10 pt | 28.4 | pass | +0.1375R/trade |
| GC | 2.10 pt | 21.0 | pass | works, 2025-26 |
| **ES** | **1.75 pt** | **7.0** | **fail** | **marginal — this file** |
| 6E | 0.00015 | 3.0 | fail | dead before costs |

ES sits between gold and the euro, and so does the result. The screen
was built on three points and ES is the fourth; it called the ordering
correctly.

## 2. Data

Databento GLBX.MDP3 `ES.FUT`, ohlcv-1m, 2026-06-03 → 2026-09-02.
Outrights only (calendar spreads dropped), volume-rolled front month:
**90,597 bars, 67 session-days, 1 roll (2026-06-14)**, price 7233–7838.
57 days survive the engine's completeness filter.

Constants at the ratio recipe off ES's own tape: floor 1.25 (5 ticks),
depths 0.25/0.50/0.75, profile bin 0.25, cap 7.5. Certified cell =
deepest depth (0.75 = 3 ticks, the 0.42× analog of NQ's 3pt) at 1R.

## 3. Result, with NQ over the same days as the control

Certified cell, honest fills, SAR, news gate:

| | n | WR | median stop | raw EV/trade | cost in R | net EV | R/day |
|---|---:|---:|---:|---:|---:|---:|---:|
| **ES** (cost 0.25pt = 1 tick = $12.50) | 766 | **66.7%** | 1.75pt | **+0.1840** | 0.1343 | **+0.0497** | +0.67 |
| **NQ** (cost 0.50pt = 2 ticks = $10.00) | 427 | 69.8% | 11.00pt | +0.2507 | 0.0509 | **+0.1998** | +2.59 |

**The level prices ES.** 66.7% at 1R is NQ's number (69.8% here, 66.4%
for the 8-level book over four years). The raw edge is 73% of NQ's. The
grammar is not instrument-specific — that is now three markets.

**Two more structural replications, both unfitted:**
- Depth gradient monotone: net EV −0.070 / −0.070 / −0.023 / **+0.050**
  at depths 0 / 1 / 2 / 3 ticks. Deeper is better, same as NQ and GC.
- 1R dominates every higher target at every depth, same as NQ and GC.

## 4. Why it still does not clear: the tick is the wrong size

| cost per round trip | in $ | cost in R | net EV | net R | R/day |
|---|---:|---:|---:|---:|---:|
| 0.25pt = 1 tick | $12.50 | 0.1343 | **+0.0497** | +38 | +0.67 |
| 0.375pt = 1.5 ticks | $18.75 | 0.2014 | **−0.0174** | −13 | −0.23 |
| 0.50pt = 2 ticks | $25.00 | 0.2686 | **−0.0845** | −65 | −1.14 |

**ES pays more in dollars at one tick ($12.50) than NQ pays in total
($10.00).** NQ's assumed 0.5pt is two of its $5 ticks; ES cannot be
charged less than one $12.50 tick without assuming free execution. And
because the ES stop is 1.75pt against NQ's 11pt, that larger dollar cost
lands on a stop six times smaller.

Cost as a share of the raw edge: **ES 73%, NQ 20%.** The strategy flips
negative somewhere between one and one-and-a-half ticks of round-trip
cost — which is exactly where real retail execution sits.

## 5. Caveats, and they are large

- **57 session-days.** §3 of the main receipts is explicit that one month
  of replay was the best of 43. One quarter cannot distinguish an edge
  from a quarter. No split-half is possible at this n.
- **The NQ control covers only 33 of those 57 days** — `nq_1m_master.parquet`
  ends 2026-07-15 and the August–September slice does not close the gap.
  The head-to-head is directionally right but not day-matched.
- Only the PD value-area family was run. No 8-level book, no VWAP books,
  no arming, no conviction sizing. Layering those onto a knife-edge base
  measures nothing until the base is settled.
- The 30pt-analog cap (7.5) and the 5-tick floor are ratio-derived, not
  natively calibrated. Gold's native sweep landed on its ratio cell
  (§22), so the prior is decent, but it is a prior.

## 6. What would settle it

One more Databento pull — same job, `"start": 2023-01-01`. That turns 57
days into ~900 and makes a split-half possible. It is the only honest way
to know whether the +0.05R survives.

Manage the expectation before spending it: even in the best case ES runs
at roughly a **quarter of NQ's net edge per trade**, and the cost
sensitivity above says a realistic execution assumption already puts it
underwater. ES is a candidate diversifier, not a second NQ.

The better use of the next pull may be **RTY** (0.10 tick against
2–3pt/min movement should screen near 20–30 ticks, the passing band),
which the screen predicts is the strongest untested candidate. That is a
prediction from three data points, and it is cheap to falsify.
