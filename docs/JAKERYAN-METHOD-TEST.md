# Jake Ryan method test

No Jake Ryan variant beats `onhl_pull_s15` on this holdout. The best mean R in the nine is `v3_3r`, 0.410 (-0.215 to 1.035) on 38 fills. The overnight pull on the same days, at 1.7R, is mean R 0.270 (0.025 to 0.515) on 118 fills, hit 48.3%. No row has a mean-R interval that sits entirely above that overnight-pull point.

Disarmed. Nothing here places an order. The rules are the four variants in the 5 Nov 2026 YouTube note, and no others. LucidFlex evals are modeled at 50%.

The footprint in the repo is one row per minute, per price, per aggressor side, from 1 Jun 2025 through 15 Jul 2026. A same-minute 80th percentile needs 20 prior sessions, so June is the warmup and the first scored window is the holdout from 1 Jul 2025. There is no train sample and no real validation month for this flag. The list was frozen before that holdout was read. Benjamini-Hochberg at 10% is applied to the holdout test of mean R above zero, across the nine rows. That correction is on the first look, not on a separate validation pass.

His trigger is a sub-minute bubble and an offer that refreshes within seconds. This test uses the whole minute. A minute can show heavy buying and a down close even when the buying was rewarded for most of that minute. The flag is the spec's proxy, and it is coarse.

Coverage: 290 mornings have footprint on at least 100 of the 09:30-11:30 minutes. 21 of those fall before 1 Jul 2025, which is the warmup rather than a selection set. 269 are the holdout.

## How the four variants were frozen

Session is 09:30 to 11:30 ET. One filled trade per variant per day. A completed absorption that is then skipped because the stop is wider than 20 points uses up one of two attempts. The weekly value area is 70% of footprint volume on 1-tick bins, from Sunday 18:00 ET through 09:29 ET that morning. Today's cash session is not in it. Empty ticks add no volume.

The spec says ask volume at or above the 80th percentile of the last 20 days' same minute, and delta at least +X. No transcript gives X, so X is zero: delta has to be strictly positive for a short and strictly negative for a long. A short also needs the close at or below the open plus one tick, and in the lower half of the bar. The next bar needs negative delta and a close below the absorption bar's low. The mirror is the long. The order is a market at the next bar's open, one tick worse. The stop is a market, one tick worse than the stop price, and it is checked before the target. Research R subtracts Topstep's $1.22. A limit does not pay the entry tick. A market does.

V1 fades the weekly high or low, allows a poke of 25 points, and skips a stop wider than 20 points past the fill. The fade has to point at the point of control. Half the size exits there and half at the other edge. On a large-overnight day, defined under V4, this fade stands down.

V2 uses the 06:30-09:29 range only when that range is under 0.4 times the prior 20 cash-session ranges. The stop is 10 points from the fill. The target is the other edge of that profile. If the weekly edge in the same direction is within 10 points of it, the target is the weekly edge.

V3 rests a limit at the weekly high or low only when that price is within 5 points of the overnight high or low, the London high or low (03:00-08:30), or a multiple of 100. The stop is 12 points. The optional filter cancels the long when the 09:25-09:29 delta is at or below the prior 20-day 10th percentile, and cancels the short at the 90th. If those percentiles are not ready, the filtered row does not trade.

V4 requires the overnight range to be more than 1.5 times the prior 20-day median, and the 09:29 close in the top or bottom 20% of that range. A selloff looks for a sweep of the overnight high and the short flag; a rally looks for a sweep of the overnight low. The stop is 10 points beyond the absorption extreme. The target is the other overnight extreme. V1, V2, and V3 do not fade on these days.

## Holdout

Hit rate is the share of trades that reached the target before the stop. For the 50/50 row it is the share that reached the point of control. The null is the no-drift hit rate from that trade's stop and target. The 50/50 row has no single null. Mean R subtracts the commission. The p-value is mean R above zero. The distribution is the 10th, 50th, and 90th percentile of net R.

| variant | target | n | hit | null hit | mean R | R 10 / 50 / 90 | p | BH |
|---|---|---:|---:|---:|---:|---:|---:|---|
| v1_blend | 50/50 at the point of control and the opposite edge | 6 | 0.0% (n/a to n/a) | n/a | -1.064 (n/a to n/a) | -1.081 / -1.061 / -1.050 | 1.000 | no |
| v1_3r | same entry, target 3R | 6 | 0.0% (n/a to n/a) | 0.250 | -1.064 (n/a to n/a) | -1.081 / -1.061 / -1.050 | 1.000 | no |
| v1_5r | same entry, target 5R | 6 | 0.0% (n/a to n/a) | 0.167 | -1.064 (n/a to n/a) | -1.081 / -1.061 / -1.050 | 1.000 | no |
| v2_edge | opposite edge of the 06:30-09:29 profile, or the weekly edge when the two are within 10 points | 74 | 12.2% (4.7% to 19.6%) | 0.124 | -0.190 (-0.790 to 0.410) | -1.086 / -1.086 / 1.257 | 0.733 | no |
| v3_poc | resting limit, target the point of control | 38 | 23.7% (10.2% to 37.2%) | 0.194 | 0.054 (-0.711 to 0.819) | -1.072 / -1.072 / 2.320 | 0.445 | no |
| v3_cancel | same limit, cancelled when the prior five-minute delta is against it at the 90th percentile | 36 | 25.0% (10.9% to 39.1%) | 0.191 | 0.117 (-0.686 to 0.920) | -1.072 / -1.072 / 2.595 | 0.388 | no |
| v3_3r | same limit, target 3R | 38 | 36.8% (21.5% to 52.2%) | 0.250 | 0.410 (-0.215 to 1.035) | -1.072 / -1.072 / 2.949 | 0.099 | no |
| v3_5r | same limit, target 5R | 38 | 13.2% (2.4% to 23.9%) | 0.167 | -0.165 (-0.845 to 0.514) | -1.072 / -1.072 / 4.949 | 0.683 | no |
| v4_on | opposite overnight extreme | 1 | 0.0% (n/a to n/a) | 0.108 | n/a (n/a to n/a) | -1.015 / -1.015 / -1.015 | 1.000 | no |

On the holdout the weekly-edge absorption bar fired 261 times. 11 of those refreshed and were then dropped for a stop wider than 20 points, and 6 became a trade. The rest never printed the next-bar refresh. The three-hour range fade flagged 135 times and filled 74. The continuation flagged 2 times and filled 1. A row with fewer than 20 fills has no interval. Its hit rate is the raw count.

## Same days, overnight pull and London

`onhl_pull_s15` is a 15-point stop. London high and low are rested 4 points beyond the 03:00-08:30 range, same 15-point stop. Both are scored only on the holdout days where the footprint covers the morning, so the comparison is the same calendar. The full-sample overnight-pull holdout from the earlier note was 48.3% (39.3% to 57.3%) on 118 fills at 1.7R.

| book | n | hit | mean R |
|---|---:|---:|---:|
| onhl_pull_s15 1.7R | 118 | 48.3% (39.3% to 57.3%) | 0.270 (0.025 to 0.515) |
| onhl_pull_s15 0.75R | 118 | 71.2% (63.0% to 79.4%) | 0.200 (0.055 to 0.345) |
| london +4pt 1.7R | 251 | 50.2% (44.0% to 56.4%) | 0.320 (0.152 to 0.487) |
| london +4pt 0.75R | 251 | 67.3% (61.5% to 73.1%) | 0.132 (0.029 to 0.235) |

## Lifecycle

Each day is at most one trade, sized to the max loss, up to $2,000. The eval path is the usual one: the account has to clear the target with the firm's consistency rule, so two equal winning days pass LucidFlex and a single day does not. The funded path is one shot of whatever that variant actually pays, then the firm's minimum winning days. The grind uses the share of these holdout trades that finished with a positive gross result. The overnight-pull row is a 0.75R eval and a 1.7R funded shot. The London row is the same shape. A fresh draw of those two is in the table so the dollar comparison uses this sample.

| firm | book | holdout pass | EV per eval | payouts / 100 |
|---|---|---:|---|---:|
| Topstep | onhl_pull_s15 | 41.2% | $546 ($397 to $695) | 44.2 |
| LucidFlex | onhl_pull_s15 | 46.0% | $270 ($186 to $353) | 38.2 |
| FundedNext Futures Flex | onhl_pull_s15 | 40.0% | $275 ($187 to $364) | 42.5 |
| Topstep | london +4pt | 35.8% | $344 ($219 to $470) | 32.8 |
| LucidFlex | london +4pt | 33.5% | $177 ($107 to $247) | 29.5 |
| FundedNext Futures Flex | london +4pt | 33.8% | $169 ($107 to $231) | 31.5 |
| Topstep | v1_blend | 0.0% | $-49 ($-49 to $-49) | 0.0 |
| LucidFlex | v1_blend | 0.0% | $-100 ($-100 to $-100) | 0.0 |
| FundedNext Futures Flex | v1_blend | 0.0% | $-85 ($-85 to $-85) | 0.0 |
| Topstep | v1_3r | 0.0% | $-49 ($-49 to $-49) | 0.0 |
| LucidFlex | v1_3r | 0.0% | $-100 ($-100 to $-100) | 0.0 |
| FundedNext Futures Flex | v1_3r | 0.0% | $-85 ($-85 to $-85) | 0.0 |
| Topstep | v1_5r | 0.0% | $-49 ($-49 to $-49) | 0.0 |
| LucidFlex | v1_5r | 0.0% | $-100 ($-100 to $-100) | 0.0 |
| FundedNext Futures Flex | v1_5r | 0.0% | $-85 ($-85 to $-85) | 0.0 |
| Topstep | v2_edge | 2.0% | $-52 ($-54 to $-50) | 0.0 |
| LucidFlex | v2_edge | 2.0% | $-100 ($-100 to $-100) | 0.0 |
| FundedNext Futures Flex | v2_edge | 0.2% | $-85 ($-85 to $-85) | 0.0 |
| Topstep | v3_poc | 3.0% | $-50 ($-57 to $-43) | 0.2 |
| LucidFlex | v3_poc | 1.8% | $-100 ($-100 to $-100) | 0.0 |
| FundedNext Futures Flex | v3_poc | 0.5% | $-85 ($-85 to $-85) | 0.0 |
| Topstep | v3_cancel | 3.5% | $-54 ($-57 to $-52) | 0.0 |
| LucidFlex | v3_cancel | 1.2% | $-100 ($-100 to $-100) | 0.0 |
| FundedNext Futures Flex | v3_cancel | 0.2% | $-85 ($-85 to $-85) | 0.0 |
| Topstep | v3_3r | 19.0% | $28 ($-10 to $66) | 7.2 |
| LucidFlex | v3_3r | 23.0% | $-3 ($-48 to $42) | 8.8 |
| FundedNext Futures Flex | v3_3r | 14.2% | $-43 ($-63 to $-24) | 5.5 |
| Topstep | v3_5r | 3.5% | $-50 ($-58 to $-41) | 0.2 |
| LucidFlex | v3_5r | 2.0% | $-96 ($-104 to $-87) | 0.2 |
| FundedNext Futures Flex | v3_5r | 1.8% | $-85 ($-85 to $-85) | 0.0 |
| Topstep | v4_on | 0.0% | $-49 ($-49 to $-49) | 0.0 |
| LucidFlex | v4_on | 0.0% | $-100 ($-100 to $-100) | 0.0 |
| FundedNext Futures Flex | v4_on | 0.0% | $-85 ($-85 to $-85) | 0.0 |

## What a real tick test would take

The minute flag cannot see a single large print or an offer that reappears a few seconds later. Those need Databento `GLBX.MDP3`, symbol the NQ front month on the same roll as the one-minute master.

`trades` is every fill with aggressor side, size, and exchange timestamp. That is the bubble and the true footprint profile. `mbo` is every order add, cancel, and modify. That is the refresh and an iceberg. GEX walls are options data. They are not in CME futures, so Databento will not supply the levels he imports from Discord.

To rerun this holdout on the real trigger, pull both schemas from 1 Jun 2025 through 15 Jul 2026. The extra June is the 20-session warmup. Restricting the clock to 18:00 ET through 11:30 ET covers the weekly profile and the entry window. To choose a variant before reading the holdout, the pull has to start where the one-minute master starts, 2 Jan 2023, and run through 15 Jul 2026.

Databento's public pricing page, read 5 Nov 2026, bills historical data by the uncompressed binary size and confirms a usage-based rate plus subscription plans. The page's rate table is drawn in the browser and did not come through as text. The unit-price sheet they still publish, dated 11 Dec 2024, lists `GLBX.MDP3` historical `trades` at $28 per GB and historical `mbo` at $1.80 per GB. New accounts get $125 of credit. The exact bill for a request is their `metadata.get_cost` call, not this note.

This repo's April 2026 footprint note counts about 7.7 million front-month NQ trades in that month. The public `trades` fields pack to about 48 bytes. That is about 0.37 GB, about $10 at $28 per GB, which is the same $10 to $20 per month this project already used for the trades tape. Thirteen months, June 2025 through July 2026, is on the order of $130 to $260 if every month looks like April. The 2023-to-2026 span is longer, and 2023/24 volume was about half, so the trades bill for the whole master is a few hundred dollars. That is an estimate from the tick count, not an invoice.

`mbo` is not priced by the trade count. April's ten-level book export in this repo was described as about 13 GB compressed and about 144 GB raw, and the project had been using about $80 for a month of that book. Market-by-order is a different schema. The $1.80 per GB rate is the listed price. The gigabytes are the part that has to be quoted before anyone buys it.

