# NEWS LAB — verdict, 12 Aug 2026

Three tests, both lanes, all on unsealed high-impact events (cpi, nfp, fomc,
pce, ppi) over 2023-01 → 2025-09. **The sealed era (2025-10-01 onward, 37
events) has not been touched and remains a clean holdout.**

## NO-TRADE on both lanes

### 1. Pre-print, futures — CLOSED

`CEILING-TEST.md`. Enter before the print with a stop. Even with **perfect
foresight of direction**, break-even accuracy is 81.7% at a 20pt stop and
64.2% at 50pt (worst-bound fills). Right pays +0.77R; wrong costs −3.43R,
because the print gaps and the stop fills in the hole.

The killer detail: break-even is **39.8% at best-bound fills and 81.7% at
worst-bound, same stop**. The lane is decided by fill quality, not by
prediction skill — so no predictor (Cleveland nowcast, feeder chain, Kalshi
skew, pre-drift) competes on the binding axis.

### 2. Pre-print, stop-width sweep — CLOSED, and it explains why

`bracket_test.py`. Break-even accuracy by stop width, 1:1, 120m hold:

| stop | 50pt | 100pt | 200pt | 300pt |
|---|---|---|---|---|
| break-even | 64.4% | 53.9% | 50.6% | 50.2% |

**It asymptotes to exactly 50%.** Widening the stop never creates edge — it
only removes the stop's own damage. In the limit you hold a symmetric coin
flip while risking $6,000 to do it. On news entries the stop is *pure cost,
never protection*: a tight stop does not control risk, it guarantees eating
the worst of the release bar at the worst available price.

Angus's proposed 50pt/150pt structure: the $3,000 target is reached **9.8%**
of the time. Coin-flip EV −$343/trade.

### 3. Post-print reaction — NO EDGE

`post_print_test.py`. Stay flat through the release bar, enter at T+1m open on
the bar's own direction. This deletes the gap term entirely — entry is an
ordinary fill in a normal minute — and needs no actuals, consensus or
predictor.

**54 configurations** swept (continuation vs fade × entry delay 1/5/15m ×
stop 50/100pt × R:R 1:1 and 1:2 × hold 30/60/120m):

- 19 nominally profitable
- **0 with Wilson CI-low > 0.50**

Best of the 54: fade, T+1m entry, 100pt stop, 1:1, 120m hold — 57.5% win,
+$251/trade, +$38,465 total, **CI-low 49.6%**. It fails PREREG-L3 kill rule
(a) by a hair, and having been selected as the best of 54 it is exactly what
noise produces. Head-to-head at 50pt/1:1/60m: continuation 48.4%
(−$148/trade), fade 51.6% (−$7/trade). Both CIs straddle 50%.

## What this means

NQ prices these releases efficiently in the release bar itself. The violence
is real — a median CPI release bar spans **120.5 points** — but it is
volatility, not exploitable direction, in either lane at any horizon tested.

Two things follow, and they matter more than the negative result:

1. **Direction was never the bottleneck.** The pre-print lane is beaten by
   fill mechanics; the post-print lane is beaten by efficiency. Building the
   predictor stack (L0b actuals, consensus scrape, L2 predictors) would have
   spent weeks improving a term that does not bind.
2. **The discovery budget on this signal family is now spent.** 54 configs is
   a lot of multiple testing. Any further variant of "pick a direction, bracket
   it" needs the sealed era to mean anything, and that is one shot.

## Not closed

- **Defined risk / long premium.** Every negative result above is dominated by
  the gap term or by symmetric-coin-flip payoffs. A long option or debit
  spread caps loss at premium with no fill uncertainty, and turns a volatility
  event into a bounded-risk bet. **Untestable here — the repo has futures
  OHLCV only, no options prices or IV surface.** Needs an options data source
  before it is anything more than a hypothesis.
- **Surprise-conditioned buckets.** Everything above keys on realised price,
  not on surprise size. The SPEC's `continuation_table` (by surprise z) is
  still unrun because L0b has no actuals or consensus. It is a different
  signal and could behave differently — but note the pre-print result closes
  regardless of surprise quality, so this only bears on the post-print lane.
- **pce alone.** Consistently the least-damaged family (−$58/trade at a 100pt
  stop vs cpi's −$300; lowest stop rate; 41.8pt median release bar) and the
  most predictable release via CPI+PPI. Small-n, and not significant on its
  own, but the one place the numbers lean.
- **The sealed era.** 37 events, untouched, still worth one confirmation shot
  if a hypothesis ever earns it.

## Recommendation

Do not trade this lane on futures. Do not build the predictor stack for it.

If the idea is worth another pass, the next step is an **options data source**
— not more predictors and not more stop/target variants. That is the only
change that attacks the mechanism the evidence actually indicts.

## What was built and is worth keeping regardless

- `output/events.parquet` — 453 verified US events, GATE L0 PASS at 100% of
  adjusted expected on every family (`GATE-L0.md`).
- `output/us_calendar.{csv,json,parquet}` — forward US high-impact calendar,
  agent-consumable, official schedules only.
- `output/news_census.parquet` — 442 measured events, 99.5% bar coverage.
- The gap-fill tables, which are reusable evidence for **any** strategy that
  holds a stop through a scheduled release, not just this one.
