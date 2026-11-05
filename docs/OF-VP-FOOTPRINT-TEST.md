# Footprint bubbles on the absorption rules

No footprint filter had enough validation fills to compare with the overnight pull on the holdout.

Disarmed. Nothing here places an order. LucidFlex evals are at 50%, and the fee is the assumed $100. FundedNext is charged Topstep's $1.22 MNQ round turn because that firm does not publish an MNQ rate.

The order-flow tape is the per-minute footprint already in `data/reference/cvd/`. Each row is one minute, one price, and one aggressor side. `volume` is the contracts. `trades` is how many prints made that volume. A bubble is `trades == 1` and `volume` at or above a cutoff: one print, not a pile of one-lots. The contiguous files run from June 2025 through July 2026. The 2023 and 2024 files cover 18:00 to 11:00 ET, which is enough for the morning entry and not a full session. This run did not buy anything.

Fifteen contracts is the large-print cutoff. On mornings before 1 July 2025, the 95th percentile of the biggest single print in a 09:30-11:30 minute was 13 contracts, so 15 is that bar rounded up. It was fixed before any of these trades were scored. Sixty is the number in the Faiz video, kept as its own rows. The same video never said whether 60 was NQ or MNQ. On this NQ tape a single 60-lot print is rare.

Jake's row fades the Sunday-to-09:29 value area, 70% on one-tick bins of the one-minute closes, and stands down on his large-overnight regime. The bar has to tag the edge, close without reward, and print a bubble at the extreme. The refresh row also needs the next minute's delta to flip and the close to take out that extreme. The order is a resting limit at the edge, trade-through, cancelled at 11:30. The stop is the extreme plus two ticks, and a risk wider than 20 points is skipped.

The failed-auction row is the overnight value area, a poke outside, and a close back inside within three bars. The filter keeps it only when a bubble sits on the breakout side at the extreme of one of those bars. The limit rests at the reclaimed edge. The reload row keeps a failed auction whose largest bubble is outside the body of the finished poke bar, and rests at that price. A second reload row enters only after a later close back through that price. Body versus wick uses the finished high, low, open, and close. The footprint does not say which print came first inside the minute.

The level-gated rows almost never fire: a 15-lot print on the failed-auction extreme, or within two points of the overnight high, the prior-day high, or the value-area edge, is a handful of days. The extra rows drop the level and keep the absorption itself. The first 09:30-11:30 bar with a single print of at least 15 contracts within one point of the bar's high or low, and a close that does not reward that print, rests a limit at the print on the next bars. The stop is two points past the print. A two-tick stop would be under the two-point minimum this stack already uses, because the print is on the extreme. Sixty contracts is the same row with the video's size.

What the footprint cannot answer is a refill of the offer inside the minute. That would be a sub-second book, not this tape. Last-of-minute depth snapshots are a different file and are not a refill clock, so they are not used. The order of prints inside the minute is not in the file either. GEX walls are not in the footprint.

A footprint row needs 80 validation fills to be ranked on the old line. The mornings with a footprint before 1 July 2025 are October 2024 and June 2025, plus five earlier months in the train window, so 80 fills is not available for a one-trade-a-day filter. If none reach 80, the rank falls to rows with at least 20 validation fills, and the doc says so. The sort is validation mean R. Holdout, from 1 July 2025, is scored after that choice. The plain failed auction is the control. It is in the multiple-testing list and it is not eligible. Benjamini-Hochberg at 10% covers every validation test of mean R above zero. Costs match the rest of the stack.

Validation mornings with a footprint minute: 44. Failed auctions on those mornings: 34. Of those, 1 had a 15-lot bubble at the extreme and 0 had a 60-lot bubble. Reload clusters: 1 at 15 lots and 0 at 60.

## Validation

| rule | n | hit | null | breakeven | mean R | p | BH | ranked |
|---|---:|---:|---:|---:|---:|---:|---|---|
| plain_075 | 180 | 49.4% | 57.1% | 62.1% | -0.231 (-0.366 to -0.096) | 1.000 | no | no |
| plain_17 | 180 | 28.3% | 37.0% | 40.5% | -0.335 (-0.517 to -0.153) | 1.000 | no | no |
| ext15_17 | 4 | 25.0% | 37.0% | 50.6% | -0.724 (-2.108 to 0.661) | 1.000 | no | no |
| ext15_075 | 4 | 25.0% | 57.1% | 76.3% | -0.961 (-1.880 to -0.042) | 1.000 | no | no |
| j15_075 | 1 | 0.0% | 57.1% | 61.2% | n/a (n/a to n/a) | 1.000 | no | no |
| j15_17 | 1 | 0.0% | 37.0% | 39.9% | n/a (n/a to n/a) | 1.000 | no | no |
| j15_ref_17 | 1 | 0.0% | 37.0% | 39.9% | n/a (n/a to n/a) | 1.000 | no | no |
| j60_17 | 0 | n/a | 37.0% | n/a | n/a (n/a to n/a) | 1.000 | no | no |
| a15_075 | 1 | 100.0% | 57.1% | 59.8% | n/a (n/a to n/a) | 1.000 | no | no |
| a15_17 | 1 | 0.0% | 37.0% | 38.9% | n/a (n/a to n/a) | 1.000 | no | no |
| a15_poc | 1 | 0.0% | 34.6% | 36.4% | n/a (n/a to n/a) | 1.000 | no | no |
| a60_17 | 0 | n/a | 37.0% | n/a | n/a (n/a to n/a) | 1.000 | no | no |
| b15_lim_075 | 0 | n/a | 37.0% | n/a | n/a (n/a to n/a) | 1.000 | no | no |
| b15_lim_17 | 0 | n/a | 37.0% | n/a | n/a (n/a to n/a) | 1.000 | no | no |
| b15_mkt_17 | 1 | 0.0% | 37.0% | 41.0% | n/a (n/a to n/a) | 1.000 | no | no |
| b60_lim_17 | 0 | n/a | 37.0% | n/a | n/a (n/a to n/a) | 1.000 | no | no |
| ext15_lvl_17 | 1 | 0.0% | 37.0% | 50.6% | n/a (n/a to n/a) | 1.000 | no | no |
| ext60_17 | 0 | n/a | 37.0% | n/a | n/a (n/a to n/a) | 1.000 | no | no |

The widest bubble row, `ext15_17`, filled 4 validation trades. The plain failed auction filled 180 and its validation mean R is -0.335. No footprint row reached 20 fills, so none is sent to the holdout or the lifecycle.

## Holdout

No footprint row had 20 validation fills, so the holdout stays closed.

## Lifecycle

The selected entry is replayed at 0.75R in the eval and 1.7R once funded, one resting limit, using that entry's stop. The overnight row is a 15-point stop on the same shape. Grind days use each book's own holdout hit rate.

| firm | book | holdout pass | EV per eval | payouts / 100 | evals passed / month | 21-day cash | P(month negative) |
|---|---|---:|---|---:|---:|---|---:|
| Topstep | onhl | 40.8% | $388 ($251 to $525) | 34.5 | 4.73 | $3,859 ($3,196 to $4,522) | 15.0% |
| LucidFlex | onhl | 41.5% | $331 ($235 to $427) | 44.8 | 3.18 | $717 ($413 to $1,021) | 34.0% |
| FundedNext Futures Flex | onhl | 42.8% | $259 ($180 to $339) | 40.0 | 3.62 | $717 ($449 to $984) | 37.0% |

