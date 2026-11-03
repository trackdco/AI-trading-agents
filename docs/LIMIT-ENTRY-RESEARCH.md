# Limit-entry research

Disarmed. Nothing here places an order. Eval and funded are two different setups, and each one was chosen on the validation window (1 July 2024 through 30 June 2025) before the holdout from 1 July 2025 was opened. The eval search ranks by pass rate. The funded search ranks by the share of fills that hit a 1.7:1 target before the stop. The holdout scores those choices once. It is not a second search.

The eval book is allowed to lose money per trade. Its job is to pass. A target of 0.75R needs about a 57% hit rate before costs, and about 60% at a 16-point stop after the MNQ commission and one tick of stop slippage, just to break even on the trade. The funded book is the opposite shape: $3,400 against a $2,000 stop where the max loss is $2,000, and $2,550 against a $1,500 stop on FundedNext, whose max loss is $1,500. A random path hits 1.7R about 37% of the time. Fifty percent would be an edge. The earlier ±$500 coin passes a Topstep combine about 26% of the time. That 26% figure is a different payoff, so a 0.75R book can beat it with no edge at all.

There are 64 limit variants. Ranking all of them and then quoting the winner's validation p-value would overstate the result. The holdout of the single validation winner is the check that accounts for the search.

## Fills

The order is live only on a bar after the level was known. Trade-through, which is the rule that chooses the setups: a buy fills at the limit only if the low is at least one tick through it, and the bar did not open already through it. A gap through the limit is not a fill. Touch-fill is reported afterwards, only for the chosen setups, and it is not allowed to change the choice. The stop is a market order, one tick worse, and it is checked before the target on the same bar. The target is a limit at its price, with no extra slippage. Research R subtracts Topstep's MNQ $1.22 from the points. The lifecycle uses each firm's own card. FundedNext does not print an MNQ rate, so that row is charged $1.22 and labelled. Lucid's card is $0.50 per side, $1.00 round turn.

Levels: prior-day high and low, prior settle, overnight high and low as of 09:30, the 5-minute opening range, the 30-minute opening range, the 60-minute initial balance, VWAP plus or minus one ATR taken from the 09:34 bar and first eligible at 09:35, and the 100-point rounds around the open, first eligible at 09:31. Fade rests both sides and takes the first fill. If both sides fill on the same bar, there is no trade. Pullback rests only the side of the open versus the prior settle. Filters: none; skip a session whose overnight range is wider than the prior day's range; a gap rule that turns fades off and pullbacks on when the open is more than 30% of the prior day's range away from the settle; a hot-open rule, known only after 10:00, that does the same when the first 30 minutes are wider than their prior-20 median or heavier than 1.5 times that volume median. The stop is the maximum of 8 points and 10% of the prior day's range, and no wider than 80.

## Eval: pass rate

One trade a day. The stop risks the account's max loss, and no more than $2,000. The target is 0.75 of that risk: $1,500 where the max loss is $2,000, and $1,125 on FundedNext. A variant needs at least 80 validation fills to be ranked. The winner for each firm is the highest validation pass rate. Days to pass are the mean among the paths that passed, inside a 40-day horizon.

The interval on a pass rate is the simulation error from 1,500 resamples of the recorded days. Those days are treated as the true distribution. The interval does not add a second layer of uncertainty for the size of the holdout.

| firm | chosen on validation | val pass | val days | holdout pass | holdout days | holdout fills | holdout hit | fill rate | missed winners | mean R |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Topstep | onhl_pull_none | 50.2% | 7.2 | 49.8% (47.3% to 52.3%) | 7.9 | 116 | 72.4% | 44.3% | 55.7% | 0.251 |
| LucidFlex | onhl_pull_none | 50.0% | 7.3 | 49.3% (46.8% to 51.9%) | 8.0 | 116 | 72.4% | 44.3% | 55.7% | 0.251 |
| FundedNext Futures Flex | onhl_pull_none | 48.3% | 7.4 | 48.9% (46.4% to 51.5%) | 8.0 | 116 | 72.4% | 44.3% | 55.7% | 0.251 |

`pdhl_fade_none` was named before the ranking. It is not the selection unless it also won the validation pass rate.

| firm | reference val pass | reference val days |
|---|---:|---:|
| Topstep | 31.1% | 6.9 |
| LucidFlex | 30.8% | 7.0 |
| FundedNext Futures Flex | 31.8% | 7.2 |

Four smaller trades, each one quarter of the size. Each copy is an independent draw from the same holdout days, not a second setup and not four fills from one session. It shows what the pass rate would do if four uncorrelated copies of this one edge existed. That was not found, and it was not used to choose.

| firm | four-trade holdout pass | days |
|---|---:|---:|
| Topstep | 90.8% (89.3% to 92.3%) | 13.9 |
| LucidFlex | 91.7% (90.3% to 93.1%) | 14.1 |
| FundedNext Futures Flex | 89.9% (88.3% to 91.4%) | 15.3 |

Same simulator, no limit signal. `50% on the 0.75R payoff` wins 0.75 of the stop or loses the stop, half the time. That hit rate is worse than a no-drift path, which touches 0.75R before the stop about 57.1% of the time. `Random-walk 0.75R` uses that 57.1% rate and the same dollar payoff, with no commission. `±$500` is the earlier small-step coin. On Topstep that coin is the roughly 26% baseline. Beating it does not mean the limit has an edge.

| firm | 50% on 0.75R | random-walk 0.75R | ±$500 coin |
|---|---:|---:|---:|
| Topstep | 25.9% in 2.0 days | 33.2% in 2.0 days | 25.7% in 17.9 days |
| LucidFlex | 16.3% in 3.6 days | 23.0% in 3.5 days | 25.7% in 17.9 days |
| FundedNext Futures Flex | 16.3% in 3.6 days | 23.0% in 3.5 days | 25.4% in 12.6 days |

## Funded: 1.7:1 hit rate

The validation winner is `onhl_pull_none`. Hit rate is target-before-stop among fills. The random-walk line is 37.0%. The p-value is a one-sided normal test against that line, for this one holdout. It is not a corrected p-value across the 64 variants. The validation p-value is there so the ranking can be checked.

- Validation: n=119, hit 48.7% (39.8% to 57.7%), p vs 37% 0.004, fill 47.8%, mean R 0.286.
- Holdout: n=116, hit 42.2% (33.3% to 51.2%), p vs 37% 0.123, fill 44.3%, missed winners 55.7%, mean R 0.180 (-0.063 to 0.424).
- Touch-fill holdout of this funded winner, not used to choose: hit 43.1%, mean R 0.204, fill 44.3%, n=116.

Touch-fill holdout of each firm's eval winner, also not used to choose.

| firm | eval setup | touch hit | touch mean R | touch fill |
|---|---|---:|---:|---:|
| Topstep | onhl_pull_none | 73.3% | 0.266 | 44.3% |
| LucidFlex | onhl_pull_none | 73.3% | 0.266 | 44.3% |
| FundedNext Futures Flex | onhl_pull_none | 73.3% | 0.266 | 44.3% |

Highest validation hit rates, whether or not the row had enough fills to be chosen. A row needed 100 validation fills. Holdout is shown beside them and was not the sort key.

| variant | val n | val hit | val p vs 37% | hold n | hold hit | hold mean R |
|---|---:|---:|---:|---:|---:|---:|
| onhl_pull_wide_on | 98 | 51.0% | 0.002 | 86 | 37.2% | 0.046 |
| settle_fade_hot30 | 14 | 50.0% | 1.000 | 14 | 42.9% | 0.172 |
| onhl_pull_gap | 49 | 49.0% | 0.042 | 53 | 50.9% | 0.384 |
| onhl_pull_none | 119 | 48.7% | 0.004 | 116 | 42.2% | 0.180 |
| pdhl_pull_hot30 | 27 | 48.1% | 0.116 | 29 | 37.9% | 0.040 |
| onhl_fade_hot30 | 93 | 45.2% | 0.052 | 91 | 41.8% | 0.187 |
| vwap_pull_gap | 62 | 43.5% | 0.144 | 80 | 41.2% | 0.082 |
| vwap_fade_hot30 | 42 | 42.9% | 0.217 | 29 | 27.6% | -0.288 |
| pdhl_fade_gap | 89 | 40.4% | 0.252 | 82 | 34.1% | -0.097 |
| pdhl_pull_none | 70 | 40.0% | 0.304 | 66 | 43.9% | 0.216 |
| vwap_pull_none | 124 | 39.5% | 0.284 | 136 | 39.0% | 0.036 |
| or5_pull_wide_on | 163 | 39.3% | 0.278 | 150 | 40.7% | 0.115 |

## One lifecycle

Each row is one eval purchase. The eval days are the holdout of that firm's validation winner, sized to its max loss, and a day with no fill is a zero. The big funded day is one filled holdout trade from the funded winner, sized the same way. A day that never fills is not treated as a finished attempt. On the 21-day clock, the account waits and tries again. The following days, up to the firm's count of winning days, use the eval setup's holdout target-hit rate: a win is booked at the firm's minimum winning day, and a loss is that amount divided by 0.75. No extra commission is added on those small days. Then the firm's payout rule, including the cap, the split, the buffer, and the stated intraday or end-of-day breach. Lucid's fee is the assumed $100. A passed Topstep combine also pays the $149 activation. Topstep does not cap the number of payouts. The sim stops after eight.

| firm | eval setup | funded setup | stop sized to | grind hit | holdout pass | EV per eval | payouts / 100 |
|---|---|---|---:|---:|---:|---|---:|
| Topstep | onhl_pull_none | onhl_pull_none | $2,000 | 72.4% | 49.8% | $513 ($437 to $589) | 37.5 |
| LucidFlex | onhl_pull_none | onhl_pull_none | $2,000 | 72.4% | 49.3% | $478 ($408 to $547) | 35.2 |
| FundedNext Futures Flex | onhl_pull_none | onhl_pull_none | $1,500 | 72.4% | 48.9% | $390 ($333 to $447) | 35.3 |

LucidFlex: the fee is an assumed $100; the help centre does not print it.
FundedNext Futures Flex: MNQ rate is not printed; this row is charged Topstep's $1.22.

## Monthly cash flow

A month is 21 trading days. Every evaluation the cap allows is opened on day one and its fee is charged then. A failure is not replaced, because the cap is already used. A pass converts to a funded account only while the funded count is under the firm's cap, and it does not trade on the day it passes. Payouts are only the ones that clear inside the 21 days. EV per eval, above, is the full life of the account and can run past the month. P(month negative) is the share of 400 households whose 21-day net is below zero.

| firm | evals opened | funded cap | mean month | 95% CI | P(month negative) |
|---|---:|---:|---:|---|---:|
| Topstep | 15 | 5 | $3,659 | $3,387 to $3,931 | 9.8% |
| LucidFlex | 10 | 5 | $2,623 | $2,375 to $2,870 | 14.8% |
| FundedNext Futures Flex | 10 | 5 | $2,091 | $1,890 to $2,292 | 15.5% |

- Topstep: 15 Combines opened on day one. Topstep publishes no Combine cap; 15 is the comparison batch in the rules file. At most 5 can be funded.
- LucidFlex: 10 evaluations opened on day one, which is also the household combined cap. At most 5 can be funded.
- FundedNext Futures Flex: 10 challenges opened on day one. The help centre allows 10 issued in a calendar month. The survey's eval_cap of 15 is not used for this month. At most 5 can be funded.

## What each improvement is worth

Rows are the eval pass rate. Columns are the funded 1.7:1 hit rate. The cell is the exact expected value of one eval under a one-cycle model, not a sample. Fail, and you lose the fee. Pass, and you pay the activation. The big day then either busts the account or, if it hits, four minimum winning days are assumed to finish and one payout is taken. A winning big day pays the firm's commission on a 16-point stop sized to the max loss. A losing big day also pays one tick of stop slippage. The four small days are assumed, not simulated, so a grind that would have busted the account is not in this grid. Lucid's fee is the assumed $100. Read a cell as: this pass rate and this hit rate are worth this many dollars per eval, before any second payout.

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

The funded winner `onhl_pull_none` holdout hit rate is 42.2% (33.3% to 51.2%). That interval does not sit above the 37% random-walk line, so a 50% hit on the 1.7:1 funded day was not found. Holdout mean R is 0.180 (-0.063 to 0.424). That interval covers zero. The eval search was allowed to return a negative-R book. `onhl_pull_none` is not one. Its 0.75R holdout hit rate is 72.4% (64.3% to 80.5%) on 116 fills, against 57.1% for a no-drift path and about 60% to break even after commission and one tick of stop slippage. Holdout mean R is 0.251 (0.109 to 0.393). Validation hit was 73.9% on 119 fills. The same variant won the funded ranking. Topstep holdout pass 49.8% (47.3% to 52.3%), against the ±$500 coin at 25.7% and the random-walk 0.75R book at 33.2%. The interval clears the ±$500 coin. It also clears the random-walk 0.75R book. Lifecycle EV is $513, and that interval is above zero. LucidFlex holdout pass 49.3% (46.8% to 51.9%), against the ±$500 coin at 25.7% and the random-walk 0.75R book at 23.0%. The interval clears the ±$500 coin. It also clears the random-walk 0.75R book. Lifecycle EV is $478, and that interval is above zero. FundedNext Futures Flex holdout pass 48.9% (46.4% to 51.5%), against the ±$500 coin at 25.4% and the random-walk 0.75R book at 23.0%. The interval clears the ±$500 coin. It also clears the random-walk 0.75R book. Lifecycle EV is $390, and that interval is above zero. The lifecycle dollar interval resamples those recorded days. It is not a second test of the 1.7:1 hit rate against 37%.

## Jake Ryan's rules

These are Jake Ryan's rules as written down from two months of reels. The reels are his claims. Nothing in them was checked against a brokerage statement. The rules below were fixed before this run. Every pre-declared rule is in the table. A weak holdout was not a reason to drop one.

Absorption, a trapped-trader wick, and a footprint refresh need tick or market-by-order data. They are not in the 1-minute file, so they are not approximated. The first 15-second candle after 08:30 CT is not in the file either, so that funded-open push is not tested. A 1-minute bar is a different rule. The CPI straddle, a VPN, and buying a batch of accounts for a news release are left out. Those break the firm rules this book is allowed to trade under, or they need a queue-position fill.

The volume profile runs from the Sunday 18:00 ET open (17:00 CT) through 09:29 ET the morning of the trade. Monday afternoon is in Tuesday's profile and is not in Monday's. Volume is the 1-minute bar booked at the close, in 1-point bins. The value area is 70% around the point of control. Limits go out at 09:30 ET and cancel at 11:00 ET (10:00 CT) if they have not traded through. A fade is taken only when the point of control is at least the target distance inside the edge, so a 2R target really is a fade toward the middle.

The open-reversion needs a first-five-minute push of at least 31.8 points, the median of that push on the train window. The stop is 10 points beyond the five-minute extreme and the target is the 09:30 open. The order is live at 09:35.

The trend rule needs an overnight gap of at least 107.9 points, the 75th percentile of the train window. After 09:30 it waits for a sweep through the 09:00-09:30 high or low that closes back inside, then rests a limit at that level on the next bar, with the overnight trend. The stop is 12 points. The target is the overnight extreme, and only when that extreme is at least one stop away.

| rule | val n | val hit | val mean R | hold n | hold hit | hold mean R | random-walk hit |
|---|---:|---:|---:|---:|---:|---:|---:|
| vp_10_2r | 116 | 44.0% | 0.244 | 123 | 41.5% (32.8% to 50.2%) | 0.168 (-0.096 to 0.433) | 33.3% |
| vp_15_2r | 107 | 39.3% | 0.138 | 113 | 43.4% (34.2% to 52.5%) | 0.251 (-0.026 to 0.528) | 33.3% |
| vp_10_3r | 107 | 29.9% | 0.118 | 113 | 32.7% (24.1% to 41.4%) | 0.232 (-0.118 to 0.582) | 25.0% |
| vp_15_3r | 94 | 23.4% | -0.103 | 105 | 30.5% (21.7% to 39.3%) | 0.188 (-0.167 to 0.543) | 25.0% |
| vp_12_poc | 121 | 18.2% | -0.174 | 129 | 20.9% (13.9% to 28.0%) | 0.210 (-0.308 to 0.728) | see mean R |
| revert_open | 183 | 13.1% | -0.322 | 214 | 13.6% (9.0% to 18.1%) | -0.062 (-0.429 to 0.305) | see mean R |
| trend_sweep | 59 | 6.8% | -0.461 | 88 | 8.0% (2.3% to 13.6%) | -0.304 (-0.949 to 0.341) | see mean R |

A 2R target is touched by a no-drift path about 33% of the time. A 3R target about 25%. The point-of-control fade, the open reversion, and the trend sweep do not have one reward, so that single percentage is not their null. Their mean R interval is.

Pass rate, one trade a day, stop sized to the max loss and no more than $2,000. A 2R win on that size is about $4,000, and a 3R win is about $6,000. The consistency rule then raises the target, because one day is more than half the profit. The fair coin wins at the no-drift rate for that reward and loses the whole stop otherwise. The ±$500 coin is the same roughly 26% baseline as the rest of this note.

| rule | firm | val pass | holdout pass | holdout days |
|---|---|---:|---:|---:|
| vp_10_2r | Topstep | 29.5% | 26.3% (24.0% to 28.5%) | 6.1 |
| vp_10_2r | LucidFlex | 23.4% | 20.1% (18.1% to 22.2%) | 12.3 |
| vp_10_2r | FundedNext Futures Flex | 23.3% | 19.3% (17.3% to 21.3%) | 12.6 |
| vp_15_2r | Topstep | 24.5% | 26.9% (24.7% to 29.2%) | 7.1 |
| vp_15_2r | LucidFlex | 17.5% | 21.9% (19.8% to 24.0%) | 13.3 |
| vp_15_2r | FundedNext Futures Flex | 15.4% | 21.7% (19.6% to 23.8%) | 13.4 |
| vp_10_3r | Topstep | 16.3% | 18.6% (16.6% to 20.6%) | 9.3 |
| vp_10_3r | LucidFlex | 14.5% | 16.5% (14.6% to 18.3%) | 14.6 |
| vp_10_3r | FundedNext Futures Flex | 13.6% | 17.2% (15.3% to 19.1%) | 14.0 |
| vp_15_3r | Topstep | 11.3% | 16.7% (14.8% to 18.6%) | 9.6 |
| vp_15_3r | LucidFlex | 7.8% | 13.9% (12.2% to 15.7%) | 15.9 |
| vp_15_3r | FundedNext Futures Flex | 6.4% | 13.7% (11.9% to 15.4%) | 15.6 |
| vp_12_poc | Topstep | 2.2% | 5.5% (4.3% to 6.6%) | 15.5 |
| vp_12_poc | LucidFlex | 0.9% | 2.5% (1.7% to 3.3%) | 24.9 |
| vp_12_poc | FundedNext Futures Flex | 0.4% | 1.9% (1.2% to 2.6%) | 21.1 |
| revert_open | Topstep | 2.7% | 3.7% (2.8% to 4.7%) | 11.3 |
| revert_open | LucidFlex | 1.0% | 2.0% (1.3% to 2.7%) | 16.2 |
| revert_open | FundedNext Futures Flex | 0.9% | 1.7% (1.0% to 2.3%) | 15.8 |
| trend_sweep | Topstep | 0.3% | 0.7% (0.3% to 1.1%) | 17.1 |
| trend_sweep | LucidFlex | 0.1% | 0.2% (-0.0% to 0.4%) | 27.7 |
| trend_sweep | FundedNext Futures Flex | 0.2% | 0.1% (-0.1% to 0.3%) | 17.0 |

| firm | fair 2R coin | fair 3R coin | ±$500 coin |
|---|---:|---:|---:|
| Topstep | 15.3% in 2.9 days | 10.9% in 3.8 days | 23.9% in 17.8 days |
| LucidFlex | 11.9% in 5.0 days | 8.5% in 7.4 days | 23.9% in 17.8 days |
| FundedNext Futures Flex | 11.9% in 5.0 days | 8.5% in 7.4 days | 23.3% in 12.7 days |

## Sizing the funded day

Same eval book as the lifecycle above (`onhl_pull_none`, the validation winner) and the same grind rate. The big day is that setup's filled 1.7:1 holdout trades, resized. Angus risks the max loss, and no more than $2,000. Where the line is $2,000, a target hit is about $3,400 before commission. FundedNext's line is $1,500, so that trade is sized to $1,500. Jake's one trade risks $1,300, the middle of his $1,200 to $1,400 band, so the 1.7 reward lands near $2,210, inside the $2,100 to $2,400 band. His two trades are two independent draws at $1,000 risk, about $1,700 each, and both are taken. They are two resamples of one setup, not two different signals. Topstep and LucidFlex pay at most $2,000 in a cycle. FundedNext Flex pays at most $1,500. A win larger than the cap stays in the account. An up day is the average of days that finished positive. A down day in the two-trade row is both trades losing. The EV is cash after the cap, the split, and the fee.

| firm | sizing | mean up day | mean down day | EV per eval | payouts / 100 |
|---|---|---:|---:|---|---:|
| Topstep | Angus, one trade risking $2,000 | $3,248 | $-2,068 | $513 ($437 to $589) | 37.5 |
| Topstep | Jake, one trade risking $1,300 | $2,111 | $-1,344 | $372 ($307 to $436) | 36.2 |
| Topstep | Jake, two trades risking $1,000 each | $1,414 | $-2,021 | $813 ($708 to $917) | 84.7 |
| LucidFlex | Angus, one trade risking $2,000 | $3,259 | $-2,059 | $478 ($408 to $547) | 35.2 |
| LucidFlex | Jake, one trade risking $1,300 | $2,118 | $-1,339 | $294 ($247 to $341) | 34.9 |
| LucidFlex | Jake, two trades risking $1,000 each | $1,424 | $-2,013 | $276 ($231 to $322) | 38.7 |
| FundedNext Futures Flex | Angus, one trade risking $1,500 | $2,436 | $-1,551 | $390 ($333 to $447) | 35.3 |
| FundedNext Futures Flex | Jake, one trade risking $1,300 | $2,111 | $-1,344 | $337 ($285 to $388) | 34.0 |
| FundedNext Futures Flex | Jake, two trades risking $1,000 each | $1,414 | $-2,021 | $487 ($432 to $542) | 72.9 |

`vp_10_2r` holdout mean R is 0.168 (-0.096 to 0.433). `vp_15_2r` holdout mean R is 0.251 (-0.026 to 0.528). The lower end of the hit-rate interval is above the pre-cost 33.3% line and not above the 35.0% line after commission and one tick of stop slippage. `vp_10_3r` holdout mean R is 0.232 (-0.118 to 0.582). `vp_15_3r` holdout mean R is 0.188 (-0.167 to 0.543). `vp_12_poc` holdout mean R is 0.210 (-0.308 to 0.728). `revert_open` holdout mean R is -0.062 (-0.429 to 0.305). `trend_sweep` holdout mean R is -0.304 (-0.949 to 0.341). Every one of these holdout mean-R intervals covers zero or is below it. The highest holdout pass rate in the list is 26.9% for `vp_15_2r` on Topstep. That is the neighborhood of the ±$500 coin, and it is above the fair high-R coin because a day with no fill does not take the stop. It is not the roughly 49% pass rate of the 0.75R book above. None of these rules replaces that book. The sizing table uses the earlier 1.7:1 fills. A smaller risk does not change their hit rate. On a two-trade row, an up day can be one win and one loss, and a down day is both trades losing, about two full stops. Two trades leave the account alive after a single loss. On Topstep the two-trade EV is $813 against $513 for the single full-risk trade and $372 for the single $1,300 trade. On LucidFlex the two-trade EV is $276 against $478 for the single full-risk trade and $294 for the single $1,300 trade. On FundedNext Futures Flex the two-trade EV is $487 against $390 for the single full-risk trade and $337 for the single $1,300 trade. That is the sizing, not a new signal, and the 1.7:1 hit rate still has a holdout interval that includes 37%.

