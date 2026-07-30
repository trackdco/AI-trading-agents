# London Monte Carlo eval survival — rev-3 baseline (cut@09:45)

**50K / $2,000 trailing / +$3,000 target · $200 flat micros · 10,000 paths over 235 fit sessions (no-trade days = $0). Edge scenarios are the honesty ladder: full = fit as measured; half = traded days shifted down by half their mean; zero = fully demeaned (risk profile only).**

## V8 @ 09:45 — 129 trades, funded net $+15,281, funded maxDD $721

| scenario | P(bust) | P(pass) | days to pass (q25/med/q75) | path maxDD med / p95 / p99 |
|---|---|---|---|---|
| full edge | **0.2%** | 99.8% | 32/47/66 | $475 / $1,168 / $1,578 |
| half edge | **13.6%** | 85.5% | 47/73/108 | $1,023 / $2,147 / $2,279 |
| zero edge | **73.7%** | 25.2% | 47/76/115 | $2,077 / $2,342 / $2,464 |

## V1 BE@1R @ 09:45 — 130 trades, funded net $+19,257, funded maxDD $782

| scenario | P(bust) | P(pass) | days to pass (q25/med/q75) | path maxDD med / p95 / p99 |
|---|---|---|---|---|
| full edge | **0.2%** | 99.8% | 25/37/54 | $428 / $1,115 / $1,573 |
| half edge | **18.8%** | 81.1% | 34/55/82 | $1,116 / $2,169 / $2,292 |
| zero edge | **74.3%** | 25.6% | 32/52/79 | $2,088 / $2,359 / $2,477 |

(Unresolved-in-250-day paths count in neither bust nor pass. iid bootstrap — fit clustering measured benign. Zero-edge P(bust) is the price of TRYING the eval if the edge is illusory; half-edge is the declared-shrinkage world. All pools are fit outcomes — the holdout still owns the question of whether the edge is real.)
