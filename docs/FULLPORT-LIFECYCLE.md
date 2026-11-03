# Full-port lifecycle

Disarmed. Nothing here places an order. The plan is locked. The eval is two full-size high-hit trades, each aimed at about $1,500, with the stop at the account's max loss or at about half of it. The funded account is one full-port trade, about $3,400 against a $2,000 stop where the max loss is $2,000, and $2,550 against $1,500 on FundedNext, then the firm's minimum winning days.

The funded search is one resting limit a day, reward fixed at 1.7R, stops 15, 25, 40 and 60 points. It was ranked by validation hit rate before the holdout from 1 July 2025 was opened. A variant needed 80 validation fills to be eligible. The p-value is a one-sided test against the 37% no-drift hit rate, and Benjamini-Hochberg at 10% is applied across the whole funded list. A setup clears 37% only when its holdout interval sits entirely above that line and its validation test survived the correction.

Fills are trade-through of one tick. The stop is a market, one tick worse, and it is checked before the target. Research R subtracts Topstep's $1.22. The floor moves with the closing balance. A dip to the floor, including an open loss, ends the account. That is Topstep's rule in so many words, FundedNext's floating-loss sentence, and the stricter reading of LucidFlex's "if your account balance reached the MLL". Lucid's page does not say unrealized. Details and the page dates are in `docs/HF-LIMIT-RESEARCH.md`.

Train cuts, frozen before the validation scores: a large gap is at least 108 points and a small gap is at most 23. A wide prior day is at least the train median, 185 points. There are 66 funded variants.

## Funded 1.7:1 search

| variant | val n | val hit | val p vs 37% | BH | val mean R | cost breakeven | hold n | hold hit | hold mean R |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| onhl_pull_s15 | 124 | 54.8% (46.1% to 63.6%) | 0.000 | yes | 0.432 | 38.9% | 118 | 48.3% (39.3% to 57.3%) | 0.270 |
| onhl_pull_s15_nyam | 81 | 51.9% (41.0% to 62.7%) | 0.003 | yes | 0.375 | 38.9% | 83 | 42.2% (31.5% to 52.8%) | 0.134 |
| onhl_pull_s25_skip_mon | 104 | 51.0% (41.4% to 60.6%) | 0.002 | yes | 0.347 | 38.2% | 94 | 38.3% (28.5% to 48.1%) | 0.060 |
| onhl_pull_s25_wide_pd | 100 | 49.0% (39.2% to 58.8%) | 0.007 | yes | 0.294 | 38.2% | 91 | 39.6% (29.5% to 49.6%) | 0.078 |
| onhl_pull_s25 | 124 | 47.6% (38.8% to 56.4%) | 0.008 | yes | 0.255 | 38.2% | 118 | 39.8% (31.0% to 48.7%) | 0.090 |
| vwap40_s15 | 239 | 46.9% (40.5% to 53.2%) | 0.001 | yes | 0.216 | 38.9% | 250 | 47.2% (41.0% to 53.4%) | 0.225 |
| onhl_pull_s25_skip_fri | 100 | 45.0% (35.2% to 54.8%) | 0.050 | no | 0.185 | 38.2% | 99 | 40.4% (30.7% to 50.1%) | 0.115 |
| onhl_s15 | 242 | 44.6% (38.4% to 50.9%) | 0.007 | yes | 0.155 | 38.9% | 254 | 46.5% (40.3% to 52.6%) | 0.212 |
| vp_s15_nyam | 155 | 42.6% (34.8% to 50.4%) | 0.076 | no | 0.137 | 38.9% | 171 | 44.4% (37.0% to 51.9%) | 0.150 |
| pdhl_s25_london | 93 | 41.9% (31.9% to 52.0%) | 0.164 | no | 0.260 | 38.2% | 126 | 24.6% (17.1% to 32.1%) | -0.240 |
| vp_s15 | 196 | 41.8% (34.9% to 48.7%) | 0.082 | no | 0.079 | 38.9% | 201 | 46.8% (39.9% to 53.7%) | 0.213 |
| or15_s15 | 257 | 40.9% (34.8% to 46.9%) | 0.102 | no | 0.058 | 38.9% | 269 | 42.8% (36.8% to 48.7%) | 0.111 |

Validation tests that survived Benjamini-Hochberg at 10%: 8 of 66. Nearby stops are the same idea, so that is not 8 independent discoveries.

The validation winner is `onhl_pull_s15`. Validation hit 54.8% (46.1% to 63.6%), p vs 37% 0.000, Benjamini-Hochberg passed. Holdout hit 48.3% (39.3% to 57.3%) on 118 fills. Holdout mean R 0.270 (0.025 to 0.515). The cost breakeven at this stop is 38.9%.

## Eval: two full-size trades

Each row is one trade a day unless the name says `two`, which is up to two fills. A $2,000 risk with a $1,500 target is 0.75R. The $1,000 column is a different trade, 1.5R, so the target stays about $1,500. It is not the negative-R shape. FundedNext's max loss is $1,500, so the full-size risk there is $1,500, not $2,000. Pass rates use the path: the floor moves at the close, and a dip to the floor ends the attempt. `combo` rests the prior-day high and low and the overnight pull side, and takes the first fill. `combo_two` allows a second fill.

| setup | firm | val pass at $2,000 | holdout pass at $2,000 | holdout days | val pass at $1,000 |
|---|---|---:|---:|---:|---:|
| onhl_pull_s15 | Topstep | 61.7% | 44.4% (41.3% to 47.5%) | 8.0 | 49.6% |
| onhl_pull_s15 | LucidFlex | 64.0% | 41.2% (38.1% to 44.3%) | 12.3 | 47.2% |
| onhl_pull_s15 | FundedNext Futures Flex | 60.1% | 37.4% (34.4% to 40.4%) | 12.1 | 36.3% |
| onhl_pull_s25 | Topstep | 52.0% | 38.6% (35.6% to 41.6%) | 7.3 | 45.0% |
| onhl_pull_s25 | LucidFlex | 50.5% | 40.3% (37.3% to 43.3%) | 7.3 | 41.7% |
| onhl_pull_s25 | FundedNext Futures Flex | 46.9% | 37.0% (34.0% to 40.0%) | 7.7 | 31.5% |
| onhl_s25 | Topstep | 50.4% | 40.8% (37.8% to 43.8%) | 3.6 | 26.8% |
| onhl_s25 | LucidFlex | 47.8% | 40.2% (37.2% to 43.2%) | 3.5 | 22.2% |
| onhl_s25 | FundedNext Futures Flex | 45.3% | 39.5% (36.5% to 42.5%) | 3.6 | 19.7% |
| onhl_s15 | Topstep | 45.6% | 30.9% (28.0% to 33.8%) | 3.7 | 38.8% |
| onhl_s15 | LucidFlex | 46.6% | 27.7% (24.9% to 30.5%) | 5.7 | 33.7% |
| onhl_s15 | FundedNext Futures Flex | 47.9% | 26.1% (23.4% to 28.8%) | 5.3 | 29.3% |
| combo_s15 | Topstep | 43.1% | 26.1% (23.4% to 28.8%) | 4.3 | 34.5% |
| combo_s15 | LucidFlex | 45.3% | 27.8% (25.0% to 30.6%) | 6.8 | 34.5% |
| combo_s15 | FundedNext Futures Flex | 44.5% | 27.6% (24.8% to 30.4%) | 6.7 | 25.4% |
| onhl_pull_struct | Topstep | 45.0% | 42.7% (39.6% to 45.8%) | 7.8 | 37.8% |
| onhl_pull_struct | LucidFlex | 42.1% | 40.0% (37.0% to 43.0%) | 7.9 | 35.6% |
| onhl_pull_struct | FundedNext Futures Flex | 42.7% | 38.7% (35.7% to 41.7%) | 8.0 | 26.2% |
| combo_s25 | Topstep | 41.9% | 35.2% (32.2% to 38.2%) | 4.2 | 29.0% |
| combo_s25 | LucidFlex | 40.7% | 35.1% (32.1% to 38.1%) | 4.2 | 24.9% |
| combo_s25 | FundedNext Futures Flex | 37.5% | 32.8% (29.9% to 35.7%) | 4.1 | 19.2% |
| pdhl_s15 | Topstep | 36.0% | 28.3% (25.5% to 31.1%) | 4.8 | 28.1% |
| pdhl_s15 | LucidFlex | 38.6% | 24.6% (21.9% to 27.3%) | 7.9 | 22.8% |
| pdhl_s15 | FundedNext Futures Flex | 36.9% | 24.6% (21.9% to 27.3%) | 7.3 | 19.8% |
| onhl_struct | Topstep | 35.3% | 40.4% (37.4% to 43.4%) | 3.7 | 18.3% |
| onhl_struct | LucidFlex | 33.2% | 41.1% (38.1% to 44.1%) | 4.0 | 14.3% |
| onhl_struct | FundedNext Futures Flex | 35.3% | 41.8% (38.7% to 44.9%) | 4.0 | 11.5% |
| pdhl_s25 | Topstep | 36.1% | 36.4% (33.4% to 39.4%) | 4.5 | 20.6% |
| pdhl_s25 | LucidFlex | 33.2% | 37.1% (34.1% to 40.1%) | 4.6 | 17.4% |
| pdhl_s25 | FundedNext Futures Flex | 32.0% | 35.3% (32.3% to 38.3%) | 4.4 | 13.8% |
| combo_struct | Topstep | 33.7% | 35.5% (32.5% to 38.5%) | 4.2 | 24.6% |
| combo_struct | LucidFlex | 30.9% | 34.0% (31.1% to 36.9%) | 4.8 | 21.1% |
| combo_struct | FundedNext Futures Flex | 30.4% | 32.8% (29.9% to 35.7%) | 4.6 | 17.1% |
| combo_two_s15 | Topstep | 31.1% | 24.7% (22.0% to 27.4%) | 3.7 | 32.7% |
| combo_two_s15 | LucidFlex | 29.6% | 21.5% (19.0% to 24.0%) | 5.8 | 30.9% |
| combo_two_s15 | FundedNext Futures Flex | 32.4% | 21.3% (18.8% to 23.8%) | 6.2 | 23.4% |
| pdhl_struct | Topstep | 28.4% | 34.1% (31.2% to 37.0%) | 4.6 | 22.4% |
| pdhl_struct | LucidFlex | 26.5% | 32.1% (29.2% to 35.0%) | 4.8 | 22.4% |
| pdhl_struct | FundedNext Futures Flex | 24.5% | 33.0% (30.1% to 35.9%) | 4.8 | 13.8% |
| pdhl_two_s15 | Topstep | 24.7% | 24.9% (22.2% to 27.6%) | 4.1 | 27.6% |
| pdhl_two_s15 | LucidFlex | 24.8% | 21.5% (19.0% to 24.0%) | 6.3 | 20.6% |
| pdhl_two_s15 | FundedNext Futures Flex | 25.3% | 22.3% (19.7% to 24.9%) | 6.0 | 15.2% |

A single winning day does not pass these three default rules. Topstep's best day has to stay within 55% of the target, so one day that takes the whole $3,000 raises the target to about $5,455. LucidFlex's standard rule is 40% and the minimum is two days, so two equal $1,500 days are 50% and do not pass. The 50% add-on would. FundedNext's 40% rule raises a $2,500 target to $6,250 if one day is the whole target. The rows below are still one full-target trade per day, and the paths that pass do it by winning again on a later day. They are not one-day passes.

| firm | one trade at the full target, validation pass | days |
|---|---:|---:|
| Topstep | 29.6% (26.8% to 32.4%) | 2.7 |
| LucidFlex | 25.4% (22.7% to 28.1%) | 5.2 |
| FundedNext Futures Flex | 21.9% (19.3% to 24.5%) | 5.4 |

## Lifecycle

Eval days are the validation-best 0.75R book, scored on the holdout. The big funded day is the validation-best 1.7:1 book, one filled trade, sized to the max loss. The following days use that eval book's holdout hit rate: a win is the firm's minimum winning day ($150 at Topstep and LucidFlex, $200 at FundedNext), and a loss is that amount divided by 0.75. Both dollar risks were specified in advance. The higher one is not a selection.

| firm | eval risk | holdout pass | EV per eval | payouts / 100 |
|---|---:|---:|---|---:|
| Topstep | $2,000 | 41.3% | $409 ($306 to $512) | 35.9 |
| Topstep | $1,000 | 41.6% | $369 ($278 to $461) | 33.1 |
| LucidFlex | $2,000 | 39.6% | $266 ($201 to $332) | 37.6 |
| LucidFlex | $1,000 | 38.3% | $223 ($162 to $283) | 32.7 |
| FundedNext Futures Flex | $1,500 | 39.7% | $269 ($204 to $334) | 41.6 |
| FundedNext Futures Flex | $1,000 | 28.1% | $114 ($67 to $161) | 23.3 |

| firm | evals opened | mean 21-day book at the $2,000 eval risk | 95% CI | P(month negative) |
|---|---:|---:|---|---:|
| Topstep | 15 | $3,863 | $3,402 to $4,323 | 13.0% |
| LucidFlex | 10 | $806 | $584 to $1,027 | 37.0% |
| FundedNext Futures Flex | 10 | $750 | $551 to $948 | 34.5% |

- Topstep: 15 Combines opened on day one. Topstep publishes no Combine cap; 15 is the comparison batch in the rules file. At most 5 can be funded.
- LucidFlex: 10 evaluations opened on day one, which is also the household combined cap. At most 5 can be funded.
- FundedNext Futures Flex: 10 challenges opened on day one. The help centre allows 10 issued in a calendar month. The survey's eval_cap of 15 is not used for this month. At most 5 can be funded.

## What a pass rate and a hit rate are worth

One payout cycle, exact, not a sample. Fail and the fee is lost. Pass and the activation is paid. The big day then busts the account, or, if it hits, four minimum winning days are assumed to finish and one payout is taken. A winning big day pays the firm's commission on a 16-point stop sized to the max loss. A losing big day also pays one tick. Lucid's fee is the assumed $100. This grid does not depend on which limit was searched.

### Topstep

| pass \ hit | 30.0% | 37.0% | 45.0% | 50.0% | 60.0% |
|---|---:|---:|---:|---:|---:|
| 20.0% | $27 | $52 | $80 | $98 | $133 |
| 30.0% | $65 | $102 | $145 | $171 | $224 |
| 40.0% | $103 | $153 | $209 | $245 | $315 |
| 50.0% | $141 | $203 | $274 | $318 | $406 |
| 60.0% | $179 | $254 | $338 | $391 | $497 |

### LucidFlex

| pass \ hit | 30.0% | 37.0% | 45.0% | 50.0% | 60.0% |
|---|---:|---:|---:|---:|---:|
| 20.0% | $6 | $31 | $59 | $77 | $113 |
| 30.0% | $59 | $97 | $139 | $166 | $219 |
| 40.0% | $113 | $162 | $219 | $254 | $325 |
| 50.0% | $166 | $228 | $299 | $343 | $432 |
| 60.0% | $219 | $293 | $378 | $432 | $538 |

### FundedNext Futures Flex

| pass \ hit | 30.0% | 37.0% | 45.0% | 50.0% | 60.0% |
|---|---:|---:|---:|---:|---:|
| 20.0% | $1 | $20 | $43 | $58 | $86 |
| 30.0% | $43 | $73 | $107 | $129 | $172 |
| 40.0% | $86 | $126 | $172 | $200 | $257 |
| 50.0% | $129 | $179 | $236 | $271 | $343 |
| 60.0% | $172 | $231 | $300 | $343 | $428 |

## Verdict

`onhl_pull_s15` clears 37%. Holdout hit 48.3% (39.3% to 57.3%) on 118 fills. The interval starts just above 37% and above the 38.9% cost breakeven at this stop. The validation hit was higher, 54.8%. The validation test survived the correction. Stretching the prior-day fade to 1.7R did not beat this overnight pull. Topstep at $2,000 eval risk: EV $409 ($306 to $512), 36 payouts per 100. LucidFlex at $2,000 eval risk: EV $266 ($201 to $332), 38 payouts per 100. FundedNext Futures Flex at $1,500 eval risk: EV $269 ($204 to $334), 42 payouts per 100. FundedNext Futures Flex at $1,000 eval risk: EV $114 ($67 to $161), 23 payouts per 100. Topstep month $3,863, P(negative) 13.0%. LucidFlex month $806, P(negative) 37.0%. FundedNext Futures Flex month $750, P(negative) 34.5%. On the validation window the average pass rate at a $2,000 risk is 37.2% for prior-day levels, 61.9% for the overnight pull, and 44.3% for the two on the same order. Combining them does not raise the pass rate.

