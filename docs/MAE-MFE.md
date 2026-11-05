# MAE and MFE

On train and validation the IB fallback does not beat a random entry at the same minute. The paired difference in MFE minus MAE is -9.2 points (-32.2 to 13.7). The same pre-registered difference on the holdout is 19.4 (-26.2 to 65.1). The validation exit is `s20_r1.7`. Holdout mean R is -0.012 (-0.212 to 0.189) on 164 fills. That interval is not above zero. Topstep per eval is $40 against $430 for the overnight pull.

Disarmed. Nothing here places an order. LucidFlex evals are at 50%. Charts are in `output/mae_mfe/`. That folder is gitignored, so the numbers below are the record.

The entry is the trade-through of a resting limit. The path after that fill is measured with no stop and no target. MAE is the worst point against the trade. MFE is the best point for it. A same-bar print of both extremes counts as the adverse one coming first. Train and validation, through 30 Jun 2025, are the only windows in the distributions and in the exit choice. Holdout, from 1 Jul 2025, is read after the exit is chosen.

IB in this note is the daily-book fallback. The initial-balance high and low are armed at 11:00, and only on days the overnight pull has not filled. The 10:30 version, with no overnight filter, is in the excursion table and is not an exit candidate. The other entries are the overnight pull, London high and low four points beyond the range, the prior-day high and low, and the prior cash-session value area.

Days: train 384, validation 257, holdout 269.

## Excursions, train and validation, held to the close

Mean, median, and 90th percentile, in points. The last column is the share of trades whose favorable extreme printed on an earlier bar than the adverse extreme.

| entry | n | MAE | MFE | MFE before MAE |
|---|---:|---:|---:|---:|
| ib | 388 | 84.1 / 61.2 / 177.3 (n=388) | 78.8 / 55.4 / 162.7 (n=388) | 54.6% |
| ib_1030 | 638 | 74.3 / 48.0 / 164.7 (n=638) | 188.7 / 159.2 / 322.7 (n=638) | 38.4% |
| onhl | 310 | 107.3 / 69.0 / 209.3 (n=310) | 98.0 / 71.1 / 209.7 (n=310) | 48.1% |
| london4 | 592 | 112.8 / 77.9 / 237.7 (n=592) | 117.6 / 82.9 / 246.4 (n=592) | 48.8% |
| pdhl | 461 | 102.5 / 74.5 / 225.2 (n=461) | 102.8 / 74.2 / 217.0 (n=461) | 50.3% |
| va | 462 | 107.7 / 75.2 / 252.0 (n=462) | 106.9 / 77.0 / 218.0 (n=462) | 49.6% |

The 10:30 initial-balance entry, with no overnight filter, has a median favorable excursion of 159 points and a median adverse excursion of 48. Buying the initial-balance low, or selling the high, often sits near the extreme of the rest of the session, so the no-stop path looks generous. The daily-book filter keeps the days that have not returned to the overnight level by 11:00. On those days the median favorable excursion is 55 points and the median heat is 61. A 15 or 20 point stop sits inside that heat. Only 13% of those fills stay inside 15 points of adverse excursion all the way to the close.

## Does the IB entry beat a random entry at the same minute?

For each IB fill, a control enters at that bar's open, long or short with a fixed seed, and is held to the same horizon. The score is MFE minus MAE. The difference is the IB score minus the control score. A same-side entry at that bar's open is not a second test. Both paths see the same highs and lows, so the gap in the score is twice the distance from the open to the limit. That is the trade-through, not a prediction.

| sample | horizon | IB MFE−MAE | random MFE−MAE | paired difference |
|---|---|---:|---:|---:|
| train+validation | 60m | 0.4 | 1.1 | -0.6 (-9.7 to 8.4) |
| train+validation | close | -5.3 | 4.0 | -9.2 (-32.2 to 13.7) |
| holdout | close | 15.1 | -4.3 | 19.4 (-26.2 to 65.1) |
| holdout | 60m | 16.0 | 1.3 | 14.7 (-8.8 to 38.2) |

## Conditional MFE when MAE stays small

Train and validation, IB fallback, held to the close. This is the usual claim that winners do not go far against you. The share is the fraction of all IB fills, not the fraction of winners.

| MAE under | n | share | mean MFE | median MFE |
|---:|---:|---:|---:|---:|
| 4 | 7 | 1.8% | 137.1 | 139.0 |
| 6 | 14 | 3.6% | 133.5 | 126.0 |
| 8 | 24 | 6.2% | 126.0 | 110.9 |
| 10 | 33 | 8.5% | 115.4 | 108.8 |
| 12 | 38 | 9.8% | 138.0 | 110.9 |
| 15 | 52 | 13.4% | 134.4 | 112.2 |
| 20 | 74 | 19.1% | 131.5 | 112.2 |
| 30 | 105 | 27.1% | 126.7 | 105.8 |

## Exit grid

Twenty rules on the IB fallback only. Fixed stops are 8, 12, 15 and 20 points, with a 0.75R target, a 1.7R target, or the other side of the initial balance. Two stops are 10% and 20% of the prior 20 cash-session ranges, with a 1.7R target. Two put the stop two points beyond the entry level. One puts it one point beyond the nearest adverse overnight, prior-day, or value-area price, when that distance is at least four points. Three keep a 15-point stop and a 1.7R target but flat at 30 minutes, 60 minutes, or 11:30. The 15-point 0.75R and 1.7R rows are the daily-book exits. A cell needs 80 validation fills to be eligible. The sort is validation mean R. Benjamini-Hochberg at 10% covers all 20 validation tests of mean R above zero.

| rule | val n | val hit | null | breakeven | val mean R | p | BH |
|---|---:|---:|---:|---:|---:|---:|---|
| s20_r1.7 | 155 | 43.2% | 37.0% | 38.5% | 0.151 (-0.059 to 0.362) | 0.080 | no |
| s20_r0.75 | 155 | 67.1% | 57.1% | 59.2% | 0.140 (0.009 to 0.270) | 0.018 | no |
| s15_r0.75 | 155 | 66.5% | 57.1% | 59.8% | 0.117 (-0.015 to 0.248) | 0.041 | no |
| s20_opp | 155 | 9.7% | 12.3% | 12.9% | 0.106 (-0.314 to 0.527) | 0.310 | no |
| s12_r0.75 | 155 | 66.5% | 57.1% | 60.5% | 0.105 (-0.027 to 0.237) | 0.059 | no |
| atr10_r1.7 | 155 | 37.4% | 37.0% | 38.0% | 0.039 (-0.166 to 0.243) | 0.356 | no |
| atr20_r1.7 | 122 | 27.0% | 37.0% | 37.6% | 0.024 (-0.185 to 0.233) | 0.410 | no |
| t1130 | 80 | 36.2% | 37.0% | 38.9% | 0.007 (-0.276 to 0.290) | 0.481 | no |
| t60 | 155 | 37.4% | 37.0% | 38.9% | -0.016 (-0.223 to 0.192) | 0.558 | no |
| s15_r1.7 | 155 | 37.4% | 37.0% | 38.9% | -0.018 (-0.225 to 0.189) | 0.568 | no |
| s15_opp | 155 | 7.1% | 9.6% | 10.1% | -0.022 (-0.512 to 0.469) | 0.534 | no |
| t30 | 155 | 36.1% | 37.0% | 38.9% | -0.035 (-0.239 to 0.170) | 0.631 | no |
| s8_r1.7 | 155 | 38.1% | 37.0% | 40.5% | -0.068 (-0.277 to 0.142) | 0.737 | no |
| s8_r0.75 | 155 | 56.1% | 57.1% | 62.2% | -0.108 (-0.247 to 0.032) | 0.935 | no |
| s12_r1.7 | 155 | 34.2% | 37.0% | 39.4% | -0.141 (-0.345 to 0.063) | 0.913 | no |
| s8_opp | 155 | 3.9% | 5.4% | 6.0% | -0.246 (-0.832 to 0.340) | 0.795 | no |
| s12_opp | 155 | 5.2% | 7.9% | 8.4% | -0.316 (-0.771 to 0.138) | 0.914 | no |
| next_opp | 75 | 13.3% | 20.5% | 21.0% | -0.353 (-0.661 to -0.045) | 0.988 | no |
| lvl2_r1.7 | 155 | 18.7% | 37.0% | 50.6% | -0.901 (-1.075 to -0.727) | 1.000 | no |
| lvl2_opp | 155 | 0.6% | 1.4% | 2.0% | -1.076 (-1.770 to -0.382) | 0.999 | no |

## Holdout

The validation choice is `s20_r1.7`, validation mean R 0.151 on 155 fills. Holdout hit 37.2% (29.8% to 44.6%) on 164 fills. Holdout mean R -0.012 (-0.212 to 0.189). The no-drift hit rate for these distances is 37.0%. The cost breakeven is 38.5%.

The daily-book exit, 15 points and 1.7R, was not re-chosen. Its holdout hit is 36.6% (29.2% to 44.0%) on 164 fills, mean R -0.054 (-0.254 to 0.146).

## Lifecycle

The selected exit is used for both the eval and the funded shot. The overnight row is a 0.75R eval and a 1.7R funded shot, 15-point stop. The daily-book row is the initial balance after 11:00 with that same 15-point stop. Later grind days use each book's own holdout hit rate. LucidFlex fee is the assumed $100.

| firm | book | holdout pass | EV per eval | payouts / 100 | evals passed / month | 21-day cash | P(month negative) |
|---|---|---:|---|---:|---:|---|---:|
| Topstep | selected | 22.0% | $40 ($-6 to $86) | 9.2 | 2.81 | $150 ($-69 to $369) | 48.3% |
| LucidFlex | selected | 16.5% | $-27 ($-64 to $9) | 7.5 | 1.76 | $-347 ($-495 to $-199) | 67.5% |
| FundedNext Futures Flex | selected | 10.5% | $-62 ($-77 to $-48) | 3.2 | 1.24 | $-667 ($-741 to $-592) | 89.2% |
| Topstep | onhl | 39.2% | $430 ($257 to $602) | 36.0 | 4.70 | $3,926 ($3,367 to $4,485) | 13.3% |
| LucidFlex | onhl | 38.0% | $280 ($183 to $377) | 38.5 | 3.34 | $746 ($464 to $1,028) | 39.2% |
| FundedNext Futures Flex | onhl | 41.5% | $267 ($191 to $342) | 41.2 | 3.46 | $645 ($394 to $895) | 40.8% |
| Topstep | daily book | 34.0% | $154 ($68 to $240) | 18.5 | 4.49 | $2,097 ($1,687 to $2,508) | 19.2% |
| LucidFlex | daily book | 34.0% | $94 ($44 to $144) | 20.5 | 3.15 | $781 ($514 to $1,048) | 34.2% |
| FundedNext Futures Flex | daily book | 28.7% | $17 ($-18 to $52) | 12.8 | 3.02 | $540 ($288 to $792) | 40.8% |

