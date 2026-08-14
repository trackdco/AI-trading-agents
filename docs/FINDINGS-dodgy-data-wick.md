# FINDINGS — the "data high/low" claim is refuted, and backwards

The load-bearing claim under DodgysDD's 2023 flagship setup:

> *"my friend back tested it… besides one day in the last couple five months, out of
> every single data high or low made, there's only one day where they weren't hit in the
> same day"*

That is roughly a **99%** same-day return rate on abnormal-wick news highs and lows.
Measured on **NQ, 1,251,240 one-minute bars, 2023-01 → 2026-07**, with a control.

## The table

| threshold | cell | n | /day | same-session return | 95% CI | median mins |
|---|---|---|---|---|---|---|
| wick ≥ 2× | **NEWS** | 800 | 1.43 | **83.5%** | [80.9, 85.9] | 12 |
| | control (non-news) | 83,160 | 90.9 | **93.3%** | [93.0, 93.5] | 7 |
| wick ≥ 3× | **NEWS** | 574 | 1.32 | **81.4%** | [78.1, 84.6] | 19 |
| | control | 28,785 | 31.5 | **92.2%** | [91.9, 92.6] | 8 |
| wick ≥ 5× | **NEWS** | 360 | 1.25 | **79.2%** | [74.9, 83.1] | 25 |
| | control | 5,608 | 6.2 | **88.6%** | [87.6, 89.5] | 12 |
| wick ≥ 8× | **NEWS** | 222 | 1.19 | **75.7%** | [70.1, 81.0] | 34.5 |
| | control | 1,114 | 1.9 | **83.6%** | [81.5, 85.5] | 17 |

"Abnormal" is a sweep, not a constant, because the corpus never defines it — the wick
must exceed k × the median wick of the prior 60 minutes, k ∈ {2, 3, 5, 8}, every rung
published. It must also be a 1-minute swing point, per his stated condition, and the
return scan starts only once that pivot is confirmable.

## Three results

**1. The 99% claim is not close.** Measured 76–84% depending on threshold. Even the most
generous rung is fifteen points short of the claim.

**2. News wicks come back LESS often than ordinary ones — by 8 to 11 points, at every
rung, with intervals that never overlap.** The control is the same abnormal wick at a
non-news minute. The news timing does not add to the return rate; it subtracts from it.

That is the opposite of the setup's premise. The stated reasoning was that news candles
leave unfilled orders and therefore a liquidity pool:

> *"usually when this data comes out there's not a lot of orders that get filled down
> here… it's a really nice liquidity pool"*

Whatever is true of the order book, the price does not come back more often. If anything
the plainer reading fits: news repricing tends to stick, so the extreme is less likely to
be revisited than an extreme made on noise.

**3. Something real is in there, but it is not his setup.** Abnormal wicks in general
return **83–93%** of the time, on tens of thousands of events. That is a strong base
rate, comparable to BR-1's 89% on the Bollinger MA. It just has nothing to do with news
— it is "extremes get revisited," available 91 times a day at the 2× threshold rather
than 1.4.

## The direction of the ladder is the sharpest part

If abnormality were the mechanism, a stricter threshold should improve the number.
It does the reverse, monotonically, in **both** cells:

- news: 83.5 → 81.4 → 79.2 → 75.7
- control: 93.3 → 92.2 → 88.6 → 83.6

More abnormal means **less** likely to come back. So no stricter definition of "abnormal"
rescues the claim — the trend runs against it, and a reader hoping the right threshold
was simply not tested can see that tightening makes it worse.

## Caveats, honestly

- **News minutes are a clock proxy, not a calendar.** 08:30, 10:00 and 14:00 ET, every
  day, regardless of whether anything was actually released. That dilutes both cells: the
  NEWS cell contains quiet days, and genuine releases at other times fall into the
  control. A real economic calendar would sharpen the comparison, and it is the one thing
  that could move this result.
- **Session is 18:00-anchored** (the repo convention), so "same day" is the ~23-hour
  futures session. He trades the NY session; on a narrower RTH definition the rates would
  be lower still, which does not help the claim.
- **NQ, not his exact instrument mix** — he trades NQ and ES. NQ is the primary.
- This measures **return to the wick**, which is the base rate the setup rests on. It is
  not a test of the entry model, which also requires a PD array, an inversion and a
  specific exit sequence. A refuted base rate does not automatically refute the trade,
  but it removes its stated justification.

## What this changes

The 2023 *"one setup for life"* framing does not survive: its premise is measurably
backwards on NQ. Note that **he has already moved on** — the 2026 model breakdown drops
data highs/lows as the flagship in favour of trend-line liquidity (see
`docs/RESEARCH-dodgysdd-audit.md` §0). This result is consistent with that drift, though
he gives a different reason for it.

The finding worth keeping is the control: **abnormal wicks return ~93% intraday at 91
events a day.** That is a base rate with real frequency behind it, and unlike the news
version it is not second-hand. Whether anything tradeable sits on top of it is a separate
question — BR-1 was 89% on NQ and the book built over it earned +0.186R, so a high touch
rate is a licence to look, not an edge.

Per the repo's non-negotiables: no threshold was chosen to improve a number, the full
ladder is published, and the control was specified before the result was read.
