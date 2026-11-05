# Order-flow and volume-profile videos

The print count is already on the footprint, in the `trades` column. The bubble test that uses it is `docs/OF-VP-FOOTPRINT-TEST.md`. This note does not ask for another trades purchase.

Neither A nor C beats `onhl_pull_s15` on the holdout. C never reached 80 validation fills. The best ranked A row, `a_mkt_poc`, has mean R 0.010 (-0.210 to 0.231) on 207 fills. The overnight pull is 0.270 (0.025 to 0.515) on 118 fills. Topstep per eval is $135 against $451.

Disarmed. Nothing here places an order. LucidFlex evals are at 50%, and the lifecycle fee is the assumed $100. The two videos sell a room and a Discord. The examples are winners. One video calls the value-area edges the prices with the least volume. That is not how a value area is built. These tests use the ordinary 70% area around the heaviest price.

Variant A anchors the profile at 18:00 ET and stops it at 09:29. Volume is the one-minute close, in one-tick bins. From 09:30 to 11:30, a bar trades at least one tick outside the area and a one-minute close is back inside within three bars, counting the poke bar. The market version fills on the next bar's open, one tick worse. The limit version rests at the reclaimed edge after that close. The stop is the poke extreme plus two ticks. The targets, each its own row, are the point of control, the opposite edge, and 1.7 times the stop.

The footprint filter in this note asks for 60 contracts of aggressive volume at the extreme price of the poke minute. That sum can be many small prints. The later note splits it with the `trades` column, which is the print count at that minute and price. Variant B marks wick volume versus body volume on the finished bar. The footprint gives the price of each aggressor row, so body versus wick is testable. It does not give the order of those prints inside the minute.

Variant C keeps an overnight push only when the overnight range is at least half the prior 20 cash-session ranges and the 09:29 close is in the outer 30% of that range. The leg is profiled from the overnight extreme to 09:29. A vacuum is a thin tail, rows under the median volume, covering at least 15% of the leg. A five-minute close back through the leg's point of control enters, at the next open plus one tick. The stop is four points beyond that point of control. The target is the far end of the thin tail. After the target prints, the stop trails to the completed five-minute bar, and it only tightens. Two attempts, and the second only if the first never reached the target.

A row needs 80 validation fills to be ranked. Variant B is never ranked: the minute footprint is not the rule in the video. The sort is validation mean R among A and C. Holdout, from 1 July 2025, is scored after that choice. Benjamini-Hochberg at 10% covers every validation test of mean R above zero, including the rows that are too small to rank. Costs match the rest of this stack: trade-through for limits, one tick of adverse slippage on a market entry, one tick on the stop, commission of $1.22 in the research R.

## Validation

| rule | n | hit | null | breakeven | mean R | p | BH | ranked |
|---|---:|---:|---:|---:|---:|---:|---|---|
| b_reload | 9 | 44.4% | 34.2% | 35.7% | -0.088 (-0.903 to 0.728) | 1.000 | no | no |
| a_mkt_poc | 181 | 38.1% | 40.1% | 41.5% | -0.147 (-0.375 to 0.082) | 0.896 | no | yes |
| a_mkt_1.7 | 218 | 32.6% | 37.0% | 38.8% | -0.171 (-0.341 to -0.000) | 0.975 | no | yes |
| a_lim_poc | 166 | 25.3% | 28.6% | 30.2% | -0.245 (-0.579 to 0.088) | 0.925 | no | yes |
| a_mkt_edge | 218 | 17.4% | 22.0% | 22.7% | -0.288 (-0.548 to -0.028) | 0.985 | no | yes |
| a_lim_1.7 | 180 | 28.3% | 37.0% | 40.5% | -0.335 (-0.517 to -0.153) | 1.000 | no | yes |
| a_lim_edge | 180 | 7.8% | 12.7% | 13.5% | -0.474 (-0.942 to -0.006) | 0.976 | no | yes |
| c_lvn | 11 | 9.1% | 12.8% | 13.4% | -0.770 (-1.365 to -0.174) | 1.000 | no | no |
| a_flow_poc | 1 | 0.0% | 48.0% | 49.7% | n/a (n/a to n/a) | 1.000 | no | no |
| a_flow_edge | 1 | 0.0% | 21.3% | 22.1% | n/a (n/a to n/a) | 1.000 | no | no |
| a_flow_1.7 | 1 | 0.0% | 37.0% | 38.4% | n/a (n/a to n/a) | 1.000 | no | no |

Variant C built a vacuum leg on 16 validation days and filled 11 trades on 7 of them. That is under 80, so C is not ranked and its holdout return stays closed. The footprint covers June 2025 onward. All 15 validation failed auctions in that month matched a footprint minute, and 1 of them cleared the 60-contract extreme filter. The filter and Variant B stay unranked.

## Holdout

The validation choice is `a_mkt_poc`. Holdout hit 43.5% (36.7% to 50.2%) on 207 fills. Mean R 0.010 (-0.210 to 0.231). No-drift hit 41.9%. Cost breakeven 43.2%.

`onhl_pull_s15` at 1.7R on this same holdout: hit 48.3% (39.3% to 57.3%) on 118 fills, mean R 0.270 (0.025 to 0.515).

On validation `a_mkt_poc` mean R was -0.147 (-0.375 to 0.082). Every ranked row was negative there, and none survived Benjamini-Hochberg.

## Excursion against a random entry

The score is favorable excursion minus adverse excursion, held to the close, with no stop. The control enters at the fill bar's open, long or short from a fixed seed. Train and validation are the measurement. The holdout row is the same statistic and was not used to pick the rule.

| entry | sample | n | entry MFE−MAE | random MFE−MAE | paired difference |
|---|---|---:|---:|---:|---:|
| A | train+validation | 564 | -6.7 | -13.4 | 6.7 (-15.9 to 29.4) |
| A | holdout | 237 | -7.6 | -17.3 | 9.7 (-37.3 to 56.8) |
| C | train+validation | 27 | 1.9 | 34.0 | -32.1 (-97.3 to 33.2) |
| C | holdout | 10 | -133.8 | -252.8 | 119.0 (-6.3 to 244.4) |

On train and validation, both paired differences cover zero. Neither entry beats a random side at the same minute.

## Lifecycle

The lifecycle replays the selected entry, not its native target. The eval is 0.75R and the funded shot is 1.7R, using that entry's own stop, and only the first attempt. Native C may take a second attempt; the lifecycle does not. The overnight row is a 15-point stop, 0.75R in the eval and 1.7R once funded. Grind days use each book's own holdout hit rate. LucidFlex is at 50% with the assumed $100 fee. FundedNext is charged Topstep's $1.22 MNQ round turn because that firm does not publish an MNQ rate.

| firm | book | holdout pass | EV per eval | payouts / 100 | evals passed / month | 21-day cash | P(month negative) |
|---|---|---:|---|---:|---:|---|---:|
| Topstep | selected | 24.5% | $135 ($54 to $216) | 15.2 | 3.30 | $1,574 ($1,027 to $2,121) | 30.0% |
| LucidFlex | selected | 22.8% | $36 ($-17 to $89) | 11.2 | 2.45 | $616 ($264 to $967) | 44.0% |
| FundedNext Futures Flex | selected | 21.2% | $35 ($-13 to $83) | 12.5 | 2.15 | $280 ($8 to $553) | 55.0% |
| Topstep | onhl | 41.8% | $451 ($301 to $600) | 38.2 | 4.73 | $3,859 ($3,196 to $4,522) | 15.0% |
| LucidFlex | onhl | 40.8% | $262 ($175 to $349) | 37.2 | 3.18 | $717 ($413 to $1,021) | 34.0% |
| FundedNext Futures Flex | onhl | 43.0% | $247 ($166 to $328) | 39.2 | 3.62 | $717 ($449 to $984) | 37.0% |

## Print count

The footprints in `data/reference/cvd/` are the condensed trades tape. `trades` is the number of prints behind `volume` at that minute, price, and aggressor side. The bubble test is in `docs/OF-VP-FOOTPRINT-TEST.md`. No further trades file was bought for that test. A sub-second refill is the piece those files do not contain.

