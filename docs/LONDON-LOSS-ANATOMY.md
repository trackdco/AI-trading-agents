# London loss anatomy — is there a pattern to the losers?

**Fit only. Sealed 2023/24 never loaded. Descriptive mining, not a validated edge.**

Frozen arm's taken book: **187 trades, 81 losers, 57% win rate, mean R +0.513, $+22,795** at flat 1 lot.

**How to read it.** AUC is P(the feature ranks higher on a winner than on a loser): 0.5 is no separation, and how far it sits from 0.5 is the effect size. `perm p` is 2,000 label shuffles. With 14 features tested the Bonferroni bar is p < 0.0036; a column only earns 'yes' if it clears that, and even then on fit data it is a lead to test on the holdout, not a result.

## Loss structure

Every loss is a stop; there is no third failure mode.

| exit | trades | share of losers |
|---|---|---|
| partial+stop | 69 | 6 (7%) |
| stop | 75 | 75 (93%) |

So 75 clean stops and 6 that banked a partial then stopped out for a net loss. The pure stop is the trade to explain.

## 1. Trade duration

| feature | n | loser median | winner median | AUC | perm p | Bonferroni | loss rate low / med / high |
|---|---|---|---|---|---|---|---|
| hold time (min) | 187 | 9.00 | 11.00 | 0.596 (winners higher) | 0.025 | borderline | 59% / 35% / 36% |

Hold time is measured from fill to final exit. A stop that fires in the first couple of minutes is a different animal from one that grinds for an hour, so the distribution below the median matters more than the median itself:

| hold bucket | trades | loss rate | mean R |
|---|---|---|---|
| 0-3 min | 34 | 68% | +0.213 |
| 3-8 min | 40 | 40% | +0.429 |
| 8-20 min | 67 | 39% | +0.230 |
| 20+ min | 46 | 35% | +1.220 |

## 2. The day's character — volume & choppiness

| feature | n | loser median | winner median | AUC | perm p | Bonferroni | loss rate low / med / high |
|---|---|---|---|---|---|---|---|
| indecision, 30-min | 187 | 0.27 | 0.23 | 0.426 (losers higher) | 0.091 | no | 38% / 53% / 47% |
| level churn, 30-min | 187 | 3.00 | 4.00 | 0.553 (winners higher) | 0.194 | no | 49% / 35% / 40% |
| net-path efficiency, 30-min | 187 | 0.11 | 0.10 | 0.459 (losers higher) | 0.334 | no | 38% / 45% / 47% |
| 30-min range (pts) | 187 | 52.25 | 49.12 | 0.462 (losers higher) | 0.383 | no | 34% / 51% / 45% |
| order-flow churn, 30-min | 177 | 0.03 | 0.04 | 0.534 (winners higher) | 0.449 | no | 47% / 39% / 44% |
| Bollinger width state | 187 | 1.34 | 1.21 | 0.471 (losers higher) | 0.496 | no | 44% / 39% / 47% |
| wick ratio, last 10 bars | 187 | 0.47 | 0.49 | 0.508 (winners higher) | 0.846 | no | 35% / 55% / 40% |
| relative volume at fill | 177 | 1.72 | 1.53 | 0.501 (winners higher) | 0.984 | no | 42% / 49% / 39% |

### Day-level: are losses clustered on the choppy/low-volume days?

Aggregating to the day and bucketing days by their median **indecision, 30-min** (the strongest single day-character separator above), then asking what share of each bucket's trades lost:

| day bucket | days | trades | loss rate | mean R | net $ |
|---|---|---|---|---|---|
| calm/low | 37 | 62 | 39% | +0.537 | $+8,981 |
| mid | 36 | 72 | 44% | +0.424 | $+6,769 |
| choppy/high | 34 | 53 | 47% | +0.605 | $+7,045 |

## 3. Where we entered

| feature | n | loser median | winner median | AUC | perm p | Bonferroni | loss rate low / med / high |
|---|---|---|---|---|---|---|---|
| entry vs VWAP, SD (dir-adj) | 187 | -0.44 | 0.09 | 0.628 (winners higher) | 0.003 | **yes** | 57% / 42% / 31% |
| room ahead of entry (dir-adj) | 187 | 0.64 | 0.47 | 0.382 (losers higher) | 0.007 | borderline | 34% / 33% / 63% |
| age of the session extreme | 187 | 77.00 | 104.00 | 0.566 (winners higher) | 0.117 | no | 51% / 47% / 32% |
| entry position on range (raw) | 187 | 0.47 | 0.49 | 0.554 (winners higher) | 0.199 | no | 52% / 34% / 44% |
| position within session range | 187 | 198.25 | 185.75 | 0.475 (losers higher) | 0.559 | no | 41% / 40% / 48% |

`room_ahead` and `ent_vs_vwap_sd_dir` are direction-adjusted (a long entering low on the range and a short entering high both read as high room ahead). `ent_on_pos` is the raw un-adjusted version, kept only as a check — it should separate LESS than the adjusted one if entry location matters the way we think.

## Strongest entry signal x day character

Crossing the strongest entry separator (**entry vs VWAP, SD (dir-adj)**) against the strongest day separator (**indecision, 30-min**), median split on each:

| | calm/low day | choppy/high day |
|---|---|---|
| low entry vs VWAP, SD (dir-adj) | 43% loss, R +0.57 (n=54) | 62% loss, R +0.40 (n=40) |
| high entry vs VWAP, SD (dir-adj) | 33% loss, R +0.64 (n=43) | 38% loss, R +0.43 (n=50) |

## Verdict

Clears Bonferroni (a real lead to test on the holdout): **entry vs VWAP, SD (dir-adj)** (AUC 0.63, p 0.003).

Borderline (p < 0.05 raw but not after correction — suggestive, not trustworthy alone): hold time (min) (AUC 0.60, p 0.025), room ahead of entry (dir-adj) (AUC 0.38, p 0.007).

This is the honest shape of it: the losers are stops, they do not cluster in time-in-trade, and whatever tilt exists in day-character or entry is measured above with its p-value so you can see how much of it to believe.
