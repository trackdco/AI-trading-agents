# FINDINGS — can the quiet-tape failure be fixed? (2026-09-03, post-hoc, exploratory)

Asked after the 2017–19 holdout failed its bar. Two candidates tested. Both
runs are **post-hoc** on data already read; nothing here is a verdict and the
gate threshold in §1 is fitted, not validated.

## 1. A causal regime gate — skip the day when the prior 20-day median active-session candle < T ticks

Flat railed empire, all three eras. Trailing median uses prior days only.
Day-level, so per the autopsy's structural argument the bucket is the rule
effect (skipping a day leaves every other day identical).

| T | era | days | skipped | R kept | R given up | EV/day skipped | maxDD → gated |
|---|---|---:|---:|---:|---:|---:|---|
| 8 | 2017–19 | 580 | 341 | +623 of +718 | +96 | +0.28 | −75.2 → **−34.3** |
| 8 | 2020–22 | 602 | 0 | all | 0 | — | unchanged |
| 8 | 2023–26 | 736 | 0 | all | 0 | — | unchanged |
| 12 | 2017–19 | 580 | 474 | +506 of +718 | +212 | +0.45 | −75.2 → **−19.3** |
| 12 | 2020–22 | 602 | 20 | +5,680 | +71 | +3.53 | unchanged |
| 12 | 2023–26 | 736 | 0 | all | 0 | — | unchanged |
| 16 | 2017–19 | 580 | 557 | +134 | +584 | +1.05 | −75.2 → −2.7 |
| 16 | 2020–22 | 602 | 89 | +5,157 | **+594** | +6.67 | unchanged |

- At 8–12 the gate never fires on 2023–26 and barely on 2020–22.
- On 2017–19 it halves-to-quarters the drawdown while keeping most of the R.
- 16 is too aggressive: it forgoes +594R of real money on 2020–22.
- **The skipped days are net positive everywhere.** The gate does not remove
  losers; it removes days that pay ~0.3–0.5R for a large drawdown. It is a
  risk rule, not a profit rule.
- The threshold is read off the same data that shows the problem. The *rule*
  (do not trade a tape that cannot reach the stop floor) was declared before
  the holdout; the *number* is fitted. If adopted: write it in at 10, let
  forward time judge.

## 2. A slower signal timeframe — 3-minute and 5-minute close-through on 2017–19

Value-area book, frozen constants, scored window.

| tf | trades | WR | EV/trade | net R | 2017 | 2018 | 2019 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1m (spec) | 1,385 | 62.7% | **+0.0740** | +102 | +0.006 | +0.094 | +0.065 |
| 3m | 1,542 | 58.5% | −0.0059 | −9 | −0.029 | +0.007 | −0.014 |
| 5m | 1,538 | 59.8% | +0.0007 | +1 | −0.061 | +0.037 | −0.016 |

**Worse, not better.** A slower bar does not put ticks back into the tape;
it makes the signal candle wider, which widens the structural stop, which
lowers the win rate on the same honest-fill tax. Same result 6E gave at 5,
15 and 30 minutes. Dead.

## 3. Answer

The 2017–19 tape cannot be fixed. It can be avoided: a regime gate at ~10
ticks costs nothing on any tape this program would trade and would have
removed most of the 2017–19 drawdown. Adopt as a risk rule, pre-registered
for forward time, or not at all.
