# High-frequency limit research

Disarmed. Nothing here places an order. Angus's thesis is that a small net expectancy, about +0.1R, at five or more fills a day, beats a rare setup, because the variance is smaller and an eval or a payout cycle finishes sooner.

The list below was fixed before the holdout from 1 July 2025 was opened. A setup is eligible only if the validation window averages at least five fills a day and has at least 200 fills. The winner is the eligible setup with the highest validation mean R. Its holdout is the confirmation. Separately, a sign-flip test that mean R is above zero is run on every variant, and Benjamini-Hochberg at 10% is applied across the whole list. A holdout interval above zero is a surviving edge only when that variant also passed the validation correction. Showing other holdout cells is so the ranking can be checked. Those cells were not the sort key.

## Drawdown, from the live pages

All three trails move with the closing balance, not with an intraday high. A spike that is given back by the close does not lift the floor. A dip that reaches the floor, including an open loss, ends the account even if the close would have recovered.

- Topstep, page dated 18 September 2026, [What is the Maximum Loss Limit?](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit): "The MLL is a trailing limit. It rises as your end-of-day balance grows, but never moves down." And: "The MLL updates at the end of each trading day but is monitored in real time throughout the session. Both realized and unrealized P&L count toward it." A 50K combine starts at $50,000 with the floor at $48,000, and the floor locks at $50,000 once it has trailed up to the start. A 50K express funded account starts at $0, the floor starts at -$2,000, and the floor locks at $0 once the balance reaches $2,000. The [daily loss limit](https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account) is optional. If it is on, a 50K account's published figure is $1,000, and hitting it flattens the account for the session. It is not, by itself, the end of the account. The main table does not buy that option.
- LucidFlex, page dated 26 August 2026, [LucidFlex Drawdown](https://support.lucidtrading.com/en/articles/12945815-lucidflex-drawdown): "LucidFlex evaluation and funded accounts use an End-of-Day Drawdown (EOD Drawdown) system to calculate the Max Loss Limit (MLL)." "At the end of each trading session, the system calculates the account's highest closing balance." A 50K account's max loss is $2,000, the trail balance is $52,100, and the locked floor is $50,100. The same page says "If your account balance reached the MLL, your account will be breached." It does not use the words unrealized or floating. Topstep and FundedNext do. This sim still treats a dip to the floor as a breach, which is the stricter reading of that sentence, and it does not lift the floor on an intraday high. The [customization page](https://support.lucidtrading.com/en/articles/16226050-lucidflex-customization) makes a daily loss limit optional and calls it a soft lockout. It does not print the dollar amount, so none is applied. The fee is the assumed $100.
- FundedNext Flex, [Flex Challenge rules](https://helpfutures.fundednext.com/en/articles/17229829-fundednext-futures-flex-challenge-all-rules), updated 13 October 2026: the 50K target is $2,500, the max loss is $1,500, and "The MLL adjusts at the end of each trading day, not in real time." "If your floating loss breaches the MLL during a live trade, your account is breached instantly." "No. The Flex Challenge has no daily loss limit at any stage." The floor in this sim locks at $50,100, which a $1,500 trail reaches when the close is $51,600. The same page caps the account at 30 micros. LucidFlex's funded page caps a 50K at 40 micros. Topstep's combine parameters cap a 50K at 50 micros. Size never exceeds those caps.

Inside a trade, the worst open loss is the path down to the stop, or through it if the bar gaps the stop. If that open loss reaches the floor, the account is over and the later target does not count. The floor is then updated from the close only.

## The search

Families, all resting limits, trade-through of one tick, one position at a time, flat at 15:55 ET. Stops are 4, 8, 12 and 15 points. Targets are 0.75R and 1R, except the round-number fades, which are 1R only.

- VWAP, 6, 10 or 16 points off the prior bar's session VWAP. The band is known before the fill bar.
- The prior 10, 20 or 30 one-minute bars, faded at the high and the low.
- Overnight high and low, the pull side only (the old `onhl_pull_none` idea, allowed to fill more than once) and both sides. Prior-day high and low. The 15-minute opening range, after 09:45. The 60-minute initial balance, after 10:30.
- The 25-point and 50-point rounds around the prior close, updated every bar.
- The high and low of the previous 30-minute block, faded during the next block.

There are 104 variants. Validation sessions: 257. Holdout sessions: 269. Research R subtracts Topstep's $1.22 (0.610 points). A no-drift path hits 0.75R about 57% of the time and 1R about 50% of the time. Breakeven is higher, because the stop fills one tick worse and the commission comes off both outcomes. The lifecycle then uses each firm's own MNQ rate. FundedNext does not print one, so that row is charged $1.22.

| variant | val fills/day | val n | val hit | breakeven | val mean R | val p | BH | hold fills/day | hold mean R | hold Sharpe/day |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| pdhl_s15_r0.75 | 5.79 | 1487 | 68.1% | 59.8% | 0.146 (0.104 to 0.188) | 0.000 | yes | 5.86 | 0.083 (0.042 to 0.125) | 0.225 |
| onhl_fade_s15_r1.0 | 7.36 | 1891 | 59.2% | 52.4% | 0.143 (0.099 to 0.188) | 0.000 | yes | 7.48 | 0.125 (0.082 to 0.169) | 0.309 |
| pdhl_s15_r1.0 | 5.11 | 1312 | 58.9% | 52.4% | 0.134 (0.081 to 0.188) | 0.000 | yes | 5.33 | 0.108 (0.056 to 0.159) | 0.249 |
| pdhl_s12_r1.0 | 5.82 | 1495 | 59.5% | 53.0% | 0.131 (0.081 to 0.181) | 0.000 | yes | 5.85 | 0.056 (0.006 to 0.105) | 0.134 |
| onhl_fade_s15_r0.75 | 8.33 | 2141 | 67.0% | 59.8% | 0.129 (0.094 to 0.164) | 0.000 | yes | 8.20 | 0.106 (0.071 to 0.141) | 0.304 |
| round_50_s15_r1.0 | 62.37 | 16028 | 58.5% | 52.4% | 0.124 (0.108 to 0.139) | 0.000 | yes | 69.74 | 0.118 (0.104 to 0.132) | 0.660 |
| onhl_fade_s12_r1.0 | 8.30 | 2132 | 59.1% | 53.0% | 0.123 (0.081 to 0.166) | 0.000 | yes | 8.21 | 0.105 (0.064 to 0.147) | 0.254 |
| vwap_16_s15_r0.75 | 15.25 | 3919 | 66.2% | 59.8% | 0.114 (0.088 to 0.141) | 0.000 | yes | 13.73 | 0.068 (0.041 to 0.095) | 0.235 |
| range_20_s15_r0.75 | 50.97 | 13099 | 65.9% | 59.8% | 0.110 (0.095 to 0.124) | 0.000 | yes | 50.46 | 0.098 (0.084 to 0.112) | 0.626 |
| range_30_s15_r0.75 | 40.01 | 10282 | 65.7% | 59.8% | 0.106 (0.090 to 0.123) | 0.000 | yes | 39.31 | 0.099 (0.083 to 0.115) | 0.597 |
| vwap_16_s12_r1.0 | 15.22 | 3911 | 58.1% | 53.0% | 0.104 (0.073 to 0.136) | 0.000 | yes | 13.72 | 0.053 (0.021 to 0.086) | 0.158 |
| pdhl_s12_r0.75 | 6.40 | 1646 | 66.3% | 60.5% | 0.103 (0.063 to 0.144) | 0.000 | yes | 6.37 | 0.026 (-0.015 to 0.067) | 0.070 |
| round_50_s12_r1.0 | 73.59 | 18913 | 58.0% | 53.0% | 0.101 (0.087 to 0.115) | 0.000 | yes | 80.67 | 0.072 (0.059 to 0.085) | 0.379 |
| onhl_fade_s12_r0.75 | 9.17 | 2356 | 66.0% | 60.5% | 0.099 (0.066 to 0.133) | 0.000 | yes | 8.87 | 0.062 (0.028 to 0.096) | 0.183 |
| range_20_s12_r0.75 | 59.94 | 15404 | 66.0% | 60.5% | 0.099 (0.086 to 0.112) | 0.000 | yes | 58.68 | 0.080 (0.067 to 0.093) | 0.550 |

Eligible on validation: 98. Variants whose validation sign-flip test survived Benjamini-Hochberg at 10%: 51. Nearby stops and targets are the same idea repeated, so that count is not a count of independent discoveries. The claim is the one pre-chosen variant.

The validation winner is `pdhl_s15_r0.75`. Validation fills per day 5.79, hit 68.1% against a no-drift 57.1% and a breakeven 59.8%. Validation mean R 0.146 (0.104 to 0.188), Sharpe per day 0.349. Holdout fills per day 5.86, hit 64.4% (62.0% to 66.8%), mean R 0.083 (0.042 to 0.125), Sharpe per day 0.225. Benjamini-Hochberg on the validation test: passed.

## Fills at this frequency

A one-tick trade-through is already a stricter fill than a touch. It is not a queue. At five or more attempts a day, the orders you actually get are the ones price went through, which is the adverse selection a resting limit suffers. Two further checks, on the winner only, not used to choose it:

- Drop a random 25% of the holdout fills, as a missed queue: mean R 0.085 (0.038 to 0.133).
- Drop a random 50%: mean R 0.058 (-0.002 to 0.117).
- Require two ticks of trade-through instead of one, and rescan: mean R 0.070 (0.028 to 0.113).

## Lifecycle

The same holdout days are the eval and the funded account. Size is chosen on the validation lifecycle, per firm: dollar risk per trade, a daily loss stop that only ends the session, and a daily profit stop. The stop loss of a new trade has to fit inside the room down to the floor, and inside the contract cap. The holdout column is that one policy. The onhl rows are the current book, replayed with the same floor rules: a 0.75R eval and a 1.7:1 funded day, and the same funded day as two $1,000 risks. Their grind days still use the 0.75R hit rate, booked at the firm's minimum winning day.

| firm | book | policy | holdout pass | days | EV per eval | payouts / 100 |
|---|---|---|---:|---:|---|---:|
| Topstep | `pdhl_s15_r0.75` | risk $400 a trade, no daily loss stop, no daily profit stop | 45.0% | 11.2 | $679 ($558 to $799) | 51.2 |
| LucidFlex | `pdhl_s15_r0.75` | risk $400 a trade, no daily loss stop, no daily profit stop | 40.1% | 14.6 | $544 ($443 to $645) | 47.2 |
| FundedNext Futures Flex | `pdhl_s15_r0.75` | risk $200 a trade, stop for the day after $1,000, stop for the day after $1,500 | 53.1% | 19.8 | $446 ($384 to $509) | 55.8 |
| Topstep | onhl 0.75R / 1.7:1 | the earlier sizing | 43.0% | 8.1 | $492 ($383 to $601) | 38.9 |
| Topstep | onhl two $1,000 risks | the earlier sizing | 43.8% | 7.8 | $425 ($316 to $534) | 52.5 |
| LucidFlex | onhl 0.75R / 1.7:1 | the earlier sizing | 40.0% | 8.9 | $337 ($257 to $417) | 33.0 |
| LucidFlex | onhl two $1,000 risks | the earlier sizing | 42.2% | 8.8 | $161 ($107 to $216) | 24.5 |
| FundedNext Futures Flex | onhl 0.75R / 1.7:1 | the earlier sizing | 38.8% | 8.4 | $305 ($236 to $374) | 35.1 |
| FundedNext Futures Flex | onhl two $1,000 risks | the earlier sizing | 42.9% | 8.6 | $250 ($191 to $310) | 41.9 |

| firm | evals opened | mean 21-day book | 95% CI | P(month negative) |
|---|---:|---:|---|---:|
| Topstep | 15 | $1,441 | $1,213 to $1,670 | 23.6% |
| LucidFlex | 10 | $215 | $39 to $390 | 51.6% |
| FundedNext Futures Flex | 10 | $-577 | $-648 to $-506 | 83.2% |

- Topstep: 15 Combines opened on day one. Topstep publishes no Combine cap; 15 is the comparison batch in the rules file. At most 5 can be funded.
- LucidFlex: 10 evaluations opened on day one, which is also the household combined cap. At most 5 can be funded.
- FundedNext Futures Flex: 10 challenges opened on day one. The help centre allows 10 issued in a calendar month. The survey's eval_cap of 15 is not used for this month. At most 5 can be funded.

A trade that opens and closes inside one minute can be shorter than FundedNext's 10-second micro-scalping clock. The minute bars cannot see that clock, so this study does not claim those trades are exempt.

## Verdict

`pdhl_s15_r0.75` was the eligible validation winner, at 5.79 fills a day. Holdout hit 64.4% (62.0% to 66.8%) against a no-drift 57.1% and a breakeven 59.8%. Holdout mean R is 0.083 (0.042 to 0.125). That interval is above zero, and the validation test was one of 51 that survived Benjamini-Hochberg. Under the one-tick trade-through cost model, this is a holdout edge. Requiring two ticks of trade-through still leaves the mean-R interval above zero. Dropping half the fills, a harsh missed-queue check, makes that interval cover zero. The per-eval EV is the whole life of the account. A 21-day month often ends before that life does. Topstep 21-day book $1,441, P(month negative) 23.6%. LucidFlex 21-day book $215, P(month negative) 51.6%. FundedNext Futures Flex 21-day book $-577, P(month negative) 83.2%.

