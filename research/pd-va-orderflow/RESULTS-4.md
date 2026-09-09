# PREREGISTRATION-4 — results (footprint tape 2025-06 → 2026-07)

days: bullish 121, bearish 74, neutral 96; level taps 4172; sequences found T-a 736, T-b 1098; limit unfilled T-a 15, T-b 22

| reading | n | WR% | mean net $ | mean R | PF | LB95 $ | max DD $ |
|---|---|---|---|---|---|---|---|
| **baseline, unfiltered, X-on** | 436 | 19.5 | +5.17 | +0.127 | 1.02 | -58.51 | 18,595 |
| **baseline, unfiltered, X-2R** | 439 | 27.3 | +2.07 | -0.242 | 1.01 | -46.16 | 17,915 |
| T-a / E-market / X-on | 184 | 30.4 | -2.85 | -0.077 | 0.99 | -173.04 | 20,430 |
| T-a / E-market / X-2R | 184 | 30.4 | -30.73 | -0.112 | 0.94 | -190.77 | 33,930 |
| T-a / E-limit / X-on | 176 | 30.1 | +20.03 | -0.050 | 1.04 | -155.75 | 17,825 |
| T-a / E-limit / X-2R | 177 | 31.1 | -26.30 | -0.100 | 0.95 | -187.24 | 32,975 |
| T-b / E-market / X-on | 274 | 28.1 | -37.96 | -0.137 | 0.92 | -147.98 | 24,555 |
| T-b / E-market / X-2R | 275 | 30.2 | -22.27 | -0.127 | 0.95 | -131.98 | 28,560 |
| T-b / E-limit / X-on | 263 | 28.1 | -15.99 | -0.124 | 0.96 | -125.09 | 19,180 |
| T-b / E-limit / X-2R | 264 | 29.9 | -22.33 | -0.141 | 0.95 | -127.25 | 25,235 |

**By bias / direction (reading T-a / E-market / X-on and the X-on baseline)**

| bias, direction | confirmed n | mean $ | WR% | baseline n | mean $ | WR% |
|---|---|---|---|---|---|---|
| bullish, long | 59 | -9.92 | 31 | 137 | +24.53 | 23 |
| bearish, short | 34 | -265.88 | 12 | 80 | +19.25 | 24 |
| neutral, short | 50 | +94.00 | 32 | 116 | -57.07 | 12 |
| neutral, long | 41 | +107.32 | 44 | 103 | +38.59 | 19 |

**Verdict (§6, minimum across the eight readings): NOT DEMONSTRATED**

## Reading (2026-09-09)

291 cash sessions, 4,172 taps of a prior-day value-area level, 736 completed absorption →
aggression → inversion sequences at the stricter threshold, 176–275 trades per reading.

1. **Seven of the eight readings lose money; the eighth (+$20 a trade on 176 trades) has a lower
   bound of −$156.** Profit factors 0.92–1.04, mean R −0.05 to −0.14: this is zero before costs,
   not an edge eaten by costs.
2. **The confirmation does one real thing: it raises the win rate from ~20–27% to ~30%.** It does not
   raise expectancy, because the confirmed entries are later and higher, the stops sit under the
   whole absorption-to-aggression range, and the targets are the same. Better hit rate, worse
   geometry, same money.
3. The unfiltered baseline — trade the level tap with a tight stop, no order flow — is also zero
   (+$5 and +$2 a trade, PF 1.01–1.02, drawdowns $18k on one contract). Neither the level nor the
   confirmation is where an edge lives.
4. **By bias, one slice stands out and one collapses** (post-hoc, reported, not a rule): confirmed
   fades on neutral-open days earned +$94 (shorts at VAH, n=50) and +$107 (longs at VAL, n=41), the
   only cells with a positive mean and the highest win rates (32–44%); confirmed shorts at VAL on
   bearish-open days lost **−$266 a trade on 34 trades with a 12% win rate** — the bias rule was
   wrong on 55% of those days (§11 of `EXTRACTED-RULES.md`), and "confirmation" put a short into
   the rally. The neutral-fade cell is the same small effect the bias test found (inside-open days
   close inside value 30% vs 21%); with n=91 and no lower bound it is a lead for a future test on
   data not yet seen, nothing more.
5. Two things the test cannot say: whether a human reading big single prints (the video's
   45-contract filter on MNQ) sees something the per-price aggregates hide, and whether gamma
   levels change the picture. Both are untestable here, and the first would need tick data.

**Net:** the video's execution method, defined as literally as its own description allows and run
across eight readings on thirteen months of real aggressor-tagged tape, does not produce a positive
expectancy at prior-day value-area levels, and does not beat trading the level with no order flow
at all. The bias half failed on nine years; the execution half fails on the thirteen months where
it can be tested.
