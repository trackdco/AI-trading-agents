# Daily book

Holdout fill is 91.8% with `ib` after 11:00, against 43.9% for the overnight pull alone. Holdout eval pass is 31.9% in 5.3 days, against 41.7% in 11.1 days overnight-only. Per eval: Topstep $209 against $522 overnight-only; LucidFlex $96 against $321 overnight-only; FundedNext Futures Flex $86 against $162 overnight-only.

Disarmed. Nothing here places an order. LucidFlex evals are modeled at 50%, and the fee in the lifecycle is the assumed $100. One account takes at most one full-risk trade a day.

The overnight pull is armed at 09:30. It buys the overnight low after an up open and sells the overnight high after a down open, 15-point stop. If that order fills, nothing else is placed. If it has not filled by the cancel time, it is cancelled and the fallback limit starts. On a day the overnight order cannot be armed, the fallback starts as soon as its own level is known. The cancel time and the fallback are chosen on the validation window, from 1 Jul 2024 to 1 Jul 2025. A book has to fill at least 90% of validation days to be eligible. Among those, the highest average validation pass rate across the three firms wins. The tie-break is the validation 1.7 hit rate. Holdout, from 1 Jul 2025, is reported after that choice.

Fills are trade-through of one tick. The stop is a market, one tick worse, and it is checked before the target. Research R subtracts Topstep's $1.22. A 0.75R no-drift hit rate is about 57%, and the cost breakeven is about 60%. A 1.7R no-drift hit rate is 37%, and the cost breakeven at a 15-point stop is 38.9%. Benjamini-Hochberg at 10% is applied to the validation 1.7 hit-rate tests. It describes the list. It is not the sort key.

Validation days 257, holdout days 269. The overnight pull alone fills 48.2% of validation days and 43.9% of holdout days.

## Why stacking lowered the pass rate

The earlier combined order rested the prior-day high and low and the overnight pull at the same time and took whichever traded through first. That replaced some overnight-pull trades with an earlier prior-day trade. On the validation window the overnight pull alone passed about 62% of the time and the combined order about 44%. A flat day does not risk the max loss. An earlier, weaker trade does. Conditional fallback does not do that. The overnight trade, if it fills before the cancel, is kept. The fallback can only add a trade on a day that would otherwise have been flat, or replace an overnight trade that had not filled yet.

On the selected fallback, the race version, both orders live together, has validation pass 40.3% against 41.7% for the conditional book and 61.4% for the overnight pull alone. Holdout pass is 30.5% for the race and 31.9% for the conditional book. The race is about one point under the conditional book. The conditional book is about twenty points under the overnight pull alone. Keeping the overnight fill does remove the old stacking problem. It does not protect the pass rate. The added trades are full-risk trades on days that would have been flat, and a flat day cannot blow the account.

## Validation

Eligible books fill at least 90% of validation days. The table is sorted by validation pass rate. Holdout is not in this table.

| fallback | cancel | val fill | onhl share | fallback share | val pass | val days | val 1.7 hit | p vs 37% | BH |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ib | 11:00 | 92.2% | 31.5% | 60.7% | 41.7% | 5.6 | 42.6% (36.3% to 48.9%) | 0.038 | yes |
| ib | 10:00 | 97.7% | 15.2% | 82.5% | 35.2% | 4.7 | 40.2% (34.2% to 46.3%) | 0.147 | no |
| or30 | 10:00 | 99.6% | 15.2% | 84.4% | 19.3% | 4.7 | 32.0% (26.3% to 37.7%) | 0.951 | no |

Books in the list: 44. Validation 1.7 tests that survived Benjamini-Hochberg: 34. Most of those survivors still contain the overnight pull, so the count is not that many separate edges. A 40-point VWAP band cancelled at 10:00 filled 89.9% of validation days, and the 15-minute opening range at the same time filled 88.7%. Both were under the 90% line, so neither was ranked.

## Holdout of the selected book

`ib` with the overnight order cancelled at 11:00. Holdout fill 91.8%. Of holdout days, 30.9% are the overnight pull, 61.0% are the fallback, and 8.2% are flat. Eval pass 31.9% in 5.3 days. Funded 1.7 hit 38.9% (32.8% to 44.9%) on 247 fills, mean R 0.012 (-0.153 to 0.177). The cost breakeven is 38.9%. The hit interval includes 37%, and the mean-R interval includes zero. The validation test had survived the correction. The holdout does not confirm it.

| firm | book | holdout pass | days |
|---|---|---:|---:|
| Topstep | selected | 34.5% (30.7% to 38.3%) | 3.7 |
| LucidFlex | selected | 34.3% (30.5% to 38.1%) | 6.2 |
| FundedNext Futures Flex | selected | 27.0% (23.4% to 30.6%) | 6.0 |
| Topstep | onhl only | 41.0% (37.1% to 44.9%) | 8.3 |
| LucidFlex | onhl only | 42.2% (38.2% to 46.1%) | 12.4 |
| FundedNext Futures Flex | onhl only | 42.0% (38.1% to 45.9%) | 12.6 |

## Lifecycle

Eval trades are the 0.75R book. The funded shot is the same entry at 1.7R, one trade, sized to the max loss. Later days use the 0.75R holdout hit rate. A win on those days is the firm's minimum, and a loss is that minimum divided by 0.75. The month opens the cap on day one and runs 21 sessions. Evals passed per month are the accounts that pass and take a funded slot inside that window.

| firm | book | EV per eval | payouts / 100 | evals passed / month | 21-day cash | P(month negative) |
|---|---|---|---:|---:|---|---:|
| Topstep | onhl only | $522 ($378 to $666) | 42.6 | 4.71 | $3,397 ($2,971 to $3,822) | 12.5% |
| LucidFlex | onhl only | $321 ($232 to $409) | 43.6 | 3.54 | $808 ($548 to $1,069) | 36.2% |
| FundedNext Futures Flex | onhl only | $162 ($103 to $221) | 29.0 | 3.53 | $770 ($572 to $968) | 31.2% |
| Topstep | selected | $209 ($113 to $305) | 22.6 | 4.39 | $1,992 ($1,552 to $2,431) | 28.7% |
| LucidFlex | selected | $96 ($39 to $153) | 20.4 | 2.93 | $685 ($450 to $920) | 41.9% |
| FundedNext Futures Flex | selected | $86 ($38 to $134) | 20.4 | 3.19 | $592 ($394 to $789) | 41.9% |

- Topstep: 15 Combines opened on day one. Topstep publishes no Combine cap; 15 is the comparison batch in the rules file. At most 5 can be funded.
- LucidFlex: 10 evaluations opened on day one, which is also the household combined cap. At most 5 can be funded.
- FundedNext Futures Flex: 10 challenges opened on day one. The help centre allows 10 issued in a calendar month. The survey's eval_cap of 15 is not used for this month. At most 5 can be funded.

