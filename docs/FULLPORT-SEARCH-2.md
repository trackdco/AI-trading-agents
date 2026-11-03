# Full-port search 2

Prior-day value area does not replace `onhl_pull_s15`. The reaction, a resting limit at the prior cash value-area high and low, is `fade_rth_any_off0_rest_1.7`: holdout hit 37.9% (30.9% to 45.0%) on 182 fills, mean R -0.027. That is the 37% no-drift line, and the order filled on 95.3% of holdout days an order was placed. The best value-area 1.7:1 row on validation is `disp_rth_tf1_atr_fixed_x60_1.7`, holdout hit 40.7% (32.7% to 48.7%) on 145 fills. `onhl_pull_s15` in this same fill code is 48.3% (39.3% to 57.3%) on 118 fills. No top value-area holdout interval sits entirely above that point. The failed-auction rows top out at 41 validation fills, under the 80-fill line, so they were not ranked. Across the rest of the search the validation winner is `week_open_s15_ladder_1.7`, holdout hit 38.1% (27.7% to 48.5%). No top-five holdout interval sits entirely above the onhl point. The best validation eval book is `onhl_pull_s15`, average validation pass 60.2%.

Disarmed. Nothing here places an order. LucidFlex evals are modeled at 50%: two equal winning days pass. The funded shot is one 1.7:1 trade. The eval shot is a 0.75R trade risking the max loss, up to $2,000, aimed at about $1,500. FundedNext is sized to its $1,500 max loss.

The LucidFlex rows in `docs/FULLPORT-LIFECYCLE.md` were recomputed at that 50% rule. Two 0.75R wins on a $2,000 stop still finish a little short of the $3,000 target after commission, so the $2,000 overnight-pull pass rate barely moved. The one-trade full-target path did move: LucidFlex validation pass 33.0% in 3.2 days. The $2,000 lifecycle is EV $266 ($201 to $332), 37.6 payouts per 100, and the 21-day book is $806 with P(negative) 37.0%.

Every variant below was named before the holdout was opened. A row needs 80 validation fills to be ranked. Funded rows are sorted by the validation hit rate. Eval rows are sorted by the average validation pass rate across the three firms. Holdout is printed beside them and was not the sort key. Benjamini-Hochberg at 10% covers 153 funded tests against 37% and 126 eval tests against 57%. The smallest funded p-value has to be about 0.0007 to survive on its own. Context splits of one entry are in that list, so the correction is strict. A native target has no single hit-rate null. Its mean R interval is the check.

Costs are the same as the rest of this stack. A limit fills only if the bar trades one tick through and did not open already through. The stop is a market, one tick worse, and it is checked before the target. Research R subtracts Topstep's $1.22. The no-drift hit rate is 37% at 1.7R and 57% at 0.75R. Breakeven after costs at a 15-point stop is about 38.9% at 1.7R and about 60% at 0.75R. A ±$500 coin is a different payoff, about 26% to pass, and a higher pass rate on a full-port day is not by itself an edge over that coin.

The order-flow filter was not run. The MBP-10 files in the repo are sample days, not a continuous book, and a one-minute snapshot is too coarse to confirm a touch. FOMC and CPI days come from `data/reference/news_archive.csv`.

`onhl_pull_s15`, same fill code: validation hit 54.8% on 124 fills, holdout hit 48.3% (39.3% to 57.3%) on 118 fills. That is the bar.

## Prior-day value area

The value area is 70% of volume around the prior session's point of control, in 1-point bins, with each minute's volume booked at the close. `rth` is the prior cash session, 09:30 to 15:59 ET. `eth` is the prior full session, from 18:00 ET through that cash close. Today's profile is not used.

A fade rests a short at the prior high and a long at the prior low, and only once price is inside the area, so the approach is from inside. `rest` leaves the order working until the first fill. `first` cancels a side when its first touch does not trade through. An offset of 4 points rests the limit beyond the edge. A displacement is the first candle that closes through an edge, either by 4 points with a body of at least half its range, or with a range at least as large as the prior 20 one-minute bars' average true range and that same body rule, on a 1, 2, 3, or 5 minute bar built from the one-minute data. The retest is a limit back at the broken edge, in the breakout direction. It is cancelled after 30 or 60 minutes, or if the other edge trades. The stop is 15 points beyond the edge, or the displacement candle's midpoint when that distance is between 8 and 80 points. A failed auction opens outside the area, closes back inside for two 30-minute blocks (or 60 one-minute closes), then limits the retest of that edge. The native targets are the point of control, the opposite edge, and, for a displacement, one candle-range beyond the broken level. A native target closer than one point is not taken.

### Funded, 1.7:1, top validation hit rates

| variant | val n | val hit | p vs 37% | BH | val mean R | val fill | hold n | hold hit | hold mean R | hold fill |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| disp_rth_tf1_atr_fixed_x60_1.7 | 149 | 44.3% (36.3% to 52.3%) | 0.033 | no | 0.146 | 59.6% | 145 | 40.7% (32.7% to 48.7%) | 0.070 | 55.8% |
| disp_rth_tf1_atr_fixed_x30_1.7 | 129 | 42.6% (34.1% to 51.2%) | 0.094 | no | 0.101 | 51.6% | 128 | 39.8% (31.4% to 48.3%) | 0.050 | 49.2% |
| disp_eth_tf2_close_fixed_x30_1.7 | 125 | 42.4% (33.7% to 51.1%) | 0.107 | no | 0.095 | 51.4% | 139 | 43.9% (35.6% to 52.1%) | 0.135 | 54.7% |
| fade_rth_any_off0_rest_1.7 | 187 | 42.2% (35.2% to 49.3%) | 0.070 | no | 0.108 | 97.4% | 182 | 37.9% (30.9% to 45.0%) | -0.027 | 95.3% |
| disp_eth_tf2_close_fixed_x60_1.7 | 140 | 42.1% (34.0% to 50.3%) | 0.105 | no | 0.088 | 57.6% | 150 | 45.3% (37.4% to 53.3%) | 0.174 | 59.1% |

The cash-session fade is the reaction in the table above. First-touch and a 4-point offset are in the same ranked list. Targeting the point of control on that same fade left validation mean R 0.257 (-0.101 to 0.615) and holdout mean R 0.220 (-0.266 to 0.706). Targeting the opposite edge hit 8.2% of holdout fills and mean R -0.085. A failed auction needs an open outside value, two closes back inside, and a later retest, so the samples stay small. The combined rows: fail_rth_m30_any_1.7 41 validation fills, fail_rth_m60_any_1.7 26 validation fills, fail_eth_m30_any_1.7 33 validation fills, fail_eth_m60_any_1.7 23 validation fills. Under 80 validation fills, they stay out of the ranking. Displacement missed-winner rates near 40% to 50% mean many breaks ran away without a trade-through. The retests that did fill are the ones that came back.

### Native target

Point of control, the opposite edge, or one displacement range past the broken level. Ranked by validation mean R among rows with 80 validation fills.

| variant | val n | val hit | val mean R | hold n | hold hit | hold mean R |
|---|---:|---:|---:|---:|---:|---:|
| fade_rth_any_off0_rest_poc | 183 | 30.6% | 0.257 (-0.101 to 0.615) | 178 | 22.5% | 0.220 (-0.266 to 0.706) |
| fade_rth_inside_off0_rest_poc | 93 | 28.0% | 0.248 (-0.299 to 0.794) | 89 | 16.9% | 0.189 (-0.564 to 0.942) |
| fade_rth_any_off0_first_poc | 178 | 29.8% | 0.233 (-0.130 to 0.596) | 172 | 24.4% | 0.311 (-0.192 to 0.814) |
| fade_rth_inside_off0_first_poc | 88 | 27.3% | 0.227 (-0.338 to 0.791) | 85 | 17.6% | 0.248 (-0.539 to 1.034) |
| disp_eth_tf1_close_mid_x60_meas | 143 | 58.0% | 0.129 (-0.059 to 0.317) | 147 | 51.7% | 0.074 (-0.122 to 0.270) |
| disp_eth_tf1_close_mid_x30_meas | 125 | 56.0% | 0.107 (-0.095 to 0.308) | 134 | 50.7% | 0.062 (-0.148 to 0.273) |
| disp_eth_tf1_close_fixed_x60_meas | 152 | 42.8% | 0.071 (-0.154 to 0.295) | 147 | 38.1% | -0.005 (-0.241 to 0.232) |
| fade_rth_any_off4_first_poc | 177 | 26.6% | 0.058 (-0.287 to 0.403) | 177 | 19.8% | 0.044 (-0.406 to 0.494) |

### Opening context, cash-session profile

This splits the fills of `fade_rth_any_off0_rest_1.7` by where the cash open sat relative to the prior cash value area. It is the same book as that row, not an extra test.

| window | open | days | fills | hit | mean R |
|---|---|---:|---:|---:|---:|
| validation | above | 97 | 57 | 47.4% (34.4% to 60.3%) | 0.230 |
| validation | inside | 100 | 95 | 38.9% (29.1% to 48.8%) | 0.035 |
| validation | below | 60 | 35 | 42.9% (26.5% to 59.3%) | 0.107 |
| holdout | above | 103 | 57 | 33.3% (21.1% to 45.6%) | -0.152 |
| holdout | inside | 100 | 91 | 41.8% (31.6% to 51.9%) | 0.077 |
| holdout | below | 66 | 34 | 35.3% (19.2% to 51.4%) | -0.099 |

### Missed winners

A missed winner is a day an order was working, price never traded through it, and a forced fill at that limit from the first live bar would have hit the target before the stop. Where both a short and a long were working, the counterfactual uses the side closer to the open. The rate is those days divided by days an order was placed.

| variant | val missed | hold missed |
|---|---:|---:|
| disp_rth_tf1_atr_fixed_x60_1.7 | 40.4% | 44.2% |
| disp_rth_tf1_atr_fixed_x30_1.7 | 48.4% | 50.8% |
| disp_eth_tf2_close_fixed_x30_1.7 | 47.7% | 45.3% |
| fade_rth_any_off0_rest_1.7 | 2.6% | 4.7% |
| disp_eth_tf2_close_fixed_x60_1.7 | 42.0% | 40.9% |

### Eval, 0.75R

Pass rates for the value-area names that were in the validation pass-rate table. LucidFlex uses 50%.

| variant | firm | val pass | holdout pass | holdout days |
|---|---|---:|---:|---:|
| disp_eth_tf2_close_fixed_x30_0.75 | Topstep | 51.0% | 20.5% (16.5% to 24.5%) | 5.9 |
| disp_eth_tf2_close_fixed_x30_0.75 | LucidFlex | 55.8% | 22.0% (17.9% to 26.1%) | 10.7 |
| disp_eth_tf2_close_fixed_x30_0.75 | FundedNext Futures Flex | 53.8% | 22.8% (18.6% to 26.9%) | 9.6 |
| disp_eth_tf3_close_fixed_x30_0.75 | Topstep | 56.8% | 31.8% (27.2% to 36.3%) | 7.9 |
| disp_eth_tf3_close_fixed_x30_0.75 | LucidFlex | 48.5% | 25.8% (21.5% to 30.0%) | 11.7 |
| disp_eth_tf3_close_fixed_x30_0.75 | FundedNext Futures Flex | 49.0% | 25.8% (21.5% to 30.0%) | 11.8 |
| disp_eth_tf1_close_fixed_x30_0.75 | Topstep | 51.7% | 23.5% (19.3% to 27.7%) | 7.1 |
| disp_eth_tf1_close_fixed_x30_0.75 | LucidFlex | 51.2% | 21.2% (17.2% to 25.3%) | 10.6 |
| disp_eth_tf1_close_fixed_x30_0.75 | FundedNext Futures Flex | 47.2% | 18.2% (14.5% to 22.0%) | 11.2 |
| disp_eth_tf2_close_fixed_x60_0.75 | Topstep | 53.8% | 29.5% (25.0% to 34.0%) | 6.7 |
| disp_eth_tf2_close_fixed_x60_0.75 | LucidFlex | 46.8% | 28.7% (24.3% to 33.2%) | 10.2 |
| disp_eth_tf2_close_fixed_x60_0.75 | FundedNext Futures Flex | 47.5% | 23.0% (18.9% to 27.1%) | 10.4 |
| disp_eth_tf5_atr_fixed_x30_0.75 | Topstep | 49.5% | 31.5% (26.9% to 36.1%) | 7.6 |
| disp_eth_tf5_atr_fixed_x30_0.75 | LucidFlex | 51.7% | 27.5% (23.1% to 31.9%) | 12.2 |
| disp_eth_tf5_atr_fixed_x30_0.75 | FundedNext Futures Flex | 45.2% | 29.0% (24.6% to 33.4%) | 12.2 |
| disp_eth_tf5_close_fixed_x30_0.75 | Topstep | 46.0% | 32.5% (27.9% to 37.1%) | 9.0 |
| disp_eth_tf5_close_fixed_x30_0.75 | LucidFlex | 48.0% | 30.5% (26.0% to 35.0%) | 12.7 |
| disp_eth_tf5_close_fixed_x30_0.75 | FundedNext Futures Flex | 48.8% | 33.2% (28.6% to 37.9%) | 12.5 |

## The wider list

Prior-week high and low, weekly open, monthly open, Asia high and low, London high and low, the midnight open, the 08:30 ET candle, the prior settle, the nearest naked point of control, and a gap-fill limit at the prior close. Also, pre-declared: a 4-point offset beyond the level, a 60-minute cancel, a stop moved to the entry after 8 points of profit, and a three-rung ladder 4 points apart that fills at the average of the rungs the bar trades through. Filters, pre-declared: overnight range in the outer train quartiles, trade only with the gap, skip FOMC and CPI days, skip a level the overnight already traded, level 10 to 40 points from the open, Tuesday to Thursday.

| variant | val n | val hit | p vs 37% | BH | val mean R | val fill | hold n | hold hit | hold mean R | hold fill |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|
| week_open_s15_ladder_1.7 | 80 | 50.0% (39.0% to 61.0%) | 0.008 | no | 0.327 | 31.4% | 84 | 38.1% (27.7% to 48.5%) | 0.015 | 31.5% |
| asia_s15_gap_with_1.7 | 133 | 46.6% (38.1% to 55.1%) | 0.011 | no | 0.209 | 73.1% | 135 | 47.4% (39.0% to 55.8%) | 0.231 | 75.0% |
| gap_s15_1.7 | 142 | 46.5% (38.3% to 54.7%) | 0.010 | no | 0.209 | 58.0% | 135 | 46.7% (38.3% to 55.1%) | 0.210 | 53.4% |
| week_open_s25_1.7 | 80 | 46.2% (35.3% to 57.2%) | 0.044 | no | 0.232 | 31.4% | 84 | 29.8% (20.0% to 39.5%) | -0.205 | 31.5% |
| london_s15_off4_1.7 | 237 | 46.0% (39.6% to 52.3%) | 0.002 | no | 0.192 | 92.2% | 251 | 50.2% (44.0% to 56.4%) | 0.320 | 93.7% |

## Top five overall

Funded rows are every 1.7:1 variant in both families. Eval rows are the 0.75R names whose validation pass rate was simulated, ranked by the average across the three firms. `onhl_pull_s15` is in the eval table as the reference. It is not a new funded candidate.

### Funded

| rank | variant | val hit | hold hit | hold mean R | beats onhl on holdout? |
|---:|---|---:|---:|---:|---|
| 1 | week_open_s15_ladder_1.7 | 50.0% (39.0% to 61.0%) | 38.1% (27.7% to 48.5%) | 0.015 | no |
| 2 | asia_s15_gap_with_1.7 | 46.6% (38.1% to 55.1%) | 47.4% (39.0% to 55.8%) | 0.231 | no |
| 3 | gap_s15_1.7 | 46.5% (38.3% to 54.7%) | 46.7% (38.3% to 55.1%) | 0.210 | no |
| 4 | week_open_s25_1.7 | 46.2% (35.3% to 57.2%) | 29.8% (20.0% to 39.5%) | -0.205 | no |
| 5 | london_s15_off4_1.7 | 46.0% (39.6% to 52.3%) | 50.2% (44.0% to 56.4%) | 0.320 | no |

onhl_pull_s15 holdout, same code: 48.3% (39.3% to 57.3%).

`london_s15_off4_1.7` is fifth on validation and the strongest holdout in that table: 50.2% (44.0% to 56.4%) on 251 fills, mean R 0.320 (0.152 to 0.487). The hit interval starts above 37% and above the 38.9% cost breakeven at a 15-point stop. It does not sit entirely above the onhl point of 48.3%, and its validation p-value of 0.002 does not survive the correction. Validation put it fifth. It is not the selected book.

### Eval

| rank | variant | avg val pass | Topstep holdout | LucidFlex holdout | FundedNext holdout |
|---:|---|---:|---:|---:|---:|
| 1 | onhl_pull_s15 | 60.2% | 44.2% | 40.2% | 41.8% |
| 2 | disp_eth_tf2_close_fixed_x30_0.75 | 53.5% | 20.5% | 22.0% | 22.8% |
| 3 | disp_eth_tf3_close_fixed_x30_0.75 | 51.4% | 31.8% | 25.8% | 25.8% |
| 4 | disp_eth_tf1_close_fixed_x30_0.75 | 50.1% | 23.5% | 21.2% | 18.2% |
| 5 | disp_eth_tf2_close_fixed_x60_0.75 | 49.3% | 29.5% | 28.7% | 23.0% |

## One signal a day

The members were named first: the overnight pull, the cash-session fade at the edge, the full-session fade, week, London, Asia, midnight, the 08:30 candle, the settle, the naked point of control, and the gap fill, each at a 15-point stop and 1.7R. Priority is the hit rate on the first half of validation, from 1 Jul 2024 to 1 Jan 2025, and only a member with 30 fills in that half is used. Order: asia_s15_1.7 (48.5%), onhl_pull_s15 (48.4%), settle_s15_1.7 (44.6%), gap_s15_1.7 (42.3%), fade_rth_any_off0_rest_1.7 (41.8%), fade_eth_any_off0_rest_1.7 (39.4%), week_s15_1.7 (38.5%), london_s15_1.7 (37.5%), midnight_s15_1.7 (32.0%), c0830_s15_1.7 (24.4%). The second validation half, which did not set the order, hit 41.3% (32.7% to 49.9%) on 126 fills. Holdout hit 42.4% (36.5% to 48.3%) on 269 fills, mean R 0.099. A day takes the first of those signals in that order. It does not stack them.

## Lifecycle

The eval book is the validation-best 0.75R setup among the names whose pass rate was simulated, which includes the overnight pull. The funded book is the validation-best 1.7:1 setup from this search. LucidFlex uses a 50% eval consistency rule. The floor still moves at the close, and a dip to the floor still ends the account. The onhl row is a fresh draw of `onhl_pull_s15` in both phases. The recorded LucidFlex full-port figure stays the one in `docs/FULLPORT-LIFECYCLE.md`. In this draw the overnight-pull row pays more per eval at every firm. The month below is the selected mix.

| firm | book | holdout pass | EV per eval | payouts / 100 |
|---|---|---:|---|---:|
| Topstep | selected | 44.5% | $361 ($261 to $460) | 29.3 |
| LucidFlex | selected | 41.8% | $266 ($188 to $343) | 27.7 |
| FundedNext Futures Flex | selected | 41.8% | $217 ($159 to $274) | 28.0 |
| Topstep | onhl_pull_s15 | 40.0% | $421 ($305 to $536) | 36.0 |
| LucidFlex | onhl_pull_s15 | 37.8% | $297 ($222 to $372) | 41.0 |
| FundedNext Futures Flex | onhl_pull_s15 | 44.0% | $229 ($166 to $292) | 37.7 |

| firm | evals opened | mean 21-day book | 95% CI | P(month negative) |
|---|---:|---:|---|---:|
| Topstep | 15 | $3,670 | $3,119 to $4,221 | 15.6% |
| LucidFlex | 10 | $846 | $553 to $1,140 | 33.1% |
| FundedNext Futures Flex | 10 | $947 | $704 to $1,190 | 26.9% |

