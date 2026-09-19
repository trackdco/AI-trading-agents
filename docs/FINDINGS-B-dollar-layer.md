# FINDINGS — PHASE B: the dollar layer (2026-08-07)

Book under test: A+S1 (first-of-fight reject, flow-agreeing fights only) —
832 fights over 275 fit days, ~3.0/day, +0.257R/fight. All sims: day-block
bootstrap, whole days resampled with intraday order preserved, 2,000
draws, seed 20260807. Declared constants: eval target +$3,000, trailing
EOD DD $2,000, qualifying-day floor $250 (exact Lucid figure to be pulled
from the dashboard — sensitivity shown), 5 qualifying days, 90-day eval
horizon. The partial-target generalization was verified to reproduce the
stored book exactly at T=3 (max error 4e-16) before the grid ran.

⚠ Scope caveat on every number here: the book is the FIT book with S1
applied — in-sample on both counts. The dollar layer RANKS configurations;
absolute pass rates are optimistic upper bounds until forward/holdout
validation.

## B1 — joint (partial target, size) grid

Score = P(+$3,000 AND ≥5 days ≥$250 before a $2,000 EOD-trailing breach):

| T | size | EV(R)/fight | $/day | qday% | score | med days |
|---|---|---|---|---|---|---|
| 2R | 150 | +0.187 | 85 | 29.1% | 86.5% | 29 |
| 2R | 300 | +0.187 | 170 | 40.7% | 68.0% | 13 |
| 2R | 600 | +0.187 | 340 | 45.8% | 41.2% | 8 |
| 3R | **150** | +0.257 | 117 | 35.3% | **87.8%** | 21 |
| 3R | 300 | +0.257 | 233 | 43.3% | 67.0% | 10 |
| 3R | 450 | +0.257 | 350 | 46.5% | 50.5% | 9 |
| 3R | 600 | +0.257 | 466 | 47.3% | 37.5% | 8 |
| 4R | 150 | +0.298 | 135 | 35.6% | 87.2% | 19 |
| 5R | 150 | +0.341 | 155 | 35.6% | 88.0% | 16 |
| 5R | 600 | +0.341 | 619 | 42.9% | 30.9% | 8 |

Floor sensitivity at (T=3, $300): $150 floor → 67.5%, $250 → 67.0%,
$350 → 65.8% — the floor is nearly irrelevant to the score.

**Verdict — the premise inverts.** "Size is the binding constraint" is
wrong for the EVAL: the binding constraint is the size:DD ratio. The
$2,000 trailing line is fixed, so doubling size doubles daily variance
against a fixed ruin barrier — score falls monotonically with size at
every T (87.8% → 37.5% at T=3). The $112/day-vs-$250-floor arithmetic
misled because qualifying days come from the day P&L *distribution*, not
its mean: at $150 risk, 35% of days clear $250 and five arrive well
inside the horizon (median pass 21 days). The eval is won by surviving,
not by daily-dollar throughput. Bigger partial targets (T=4–5) raise EV
but not eval score — the tail helps the year, not the evaluation.

**Recommended eval configuration from this grid: T=3, $150 risk —
87.8% pass, median 21 days.** Patience is the price of the pass rate.

## B2 — two-phase sizing across the drawdown lock

Funded stage, 250 days: line trails at peak−$2,000 until it locks at the
50k start (peak ≥ +$2,000, median lock day 14 at S_pre=$150), then
everything above start is cushion. Payout $2,000 when balance ≥ $4,000
and ≥5 qualifying days since last payout.

| S_pre | S_post | P(bust) | med $/yr withdrawn | med lock day |
|---|---|---|---|---|
| 150 | 150 | **24.4%** | 24,000 | 14 |
| 150 | 300 | 41.5% | **36,000** | 14 |
| 150 | 600 | 50.9% | 10,000 | 14 |
| 300 | 300 | 47.4% | 36,000 | 6 |
| 600 | 150 | 44.3% | 24,000 | 3 |
| 600 | 600 | 57.6% | 2,000 | 3 |

**Verdict — the two-regime instinct is right.** Low-size-until-lock
strictly dominates: every S_pre=$150 row beats its size-matched
constant-sizing counterpart on P(bust) at equal-or-better extraction.
(150→150) is the survival pick (24.4% annual bust); (150→300) is the
extraction pick ($36k/yr median at 41.5% bust — acceptable only because
Lucid resets are cheap relative to a funded year; that trade-off is a
business decision, not a statistics one). Sizing up BEFORE the lock is
pure damage: (600,600) busts 57.6% of years for $2k median extraction.

## B3 — stop-once-green-by-X

Size $300, entries stop once cumulative booked day P&L ≥ X (approximation
declared: booked at trigger order — the table does not record exit
minutes; the builder extension to add them is queued):

| X | trades | $/day | qday% | score |
|---|---|---|---|---|
| $250 | 613 | 133 | 48.7% | 62.0% |
| $400 | 637 | 160 | 47.3% | 65.5% |
| $600 | 656 | 161 | 45.8% | 64.8% |
| $1,000 | 784 | 202 | 43.3% | 66.2% |
| none | 832 | 233 | 43.3% | **67.0%** |

**Verdict — rejected as scored.** The policy does what it promises
(qualifying-day rate rises to 48.7%) and still loses: it truncates
exactly the tail fights that reach the +$3k target, so P(pass) falls at
every X. Stopping-once-green trades target progress for day-greening,
and the eval pays for target progress. Possible residual use post-lock
for a consistency-rule, if the specific plan has one — not modeled, and
not needed for the eval.
