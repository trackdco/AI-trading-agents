# Combined job — Stage 4: Monte Carlo suite

**Fit only. Sealed 2023/24 never loaded.**

2,000 paths, 252 days, seeded (20260730). Day-level bootstrap resampling whole calendar days with BOTH books' trades in the SAME draw, intraday order preserved. Resampling the books independently would manufacture diversification and flatter the combined distribution.

Funded rules: start $50,000, $2,000 trailing EOD DD locking at start once equity reaches $52,000, full $2,000 payout at $54,000.

## Sanity check

**NY-alone P(bust) = 11.8%** (must be near 1%, not 39% — 39% would mean the wrong book was loaded).

## Headline

| config | P(bust) | cycles med/p90 | net payout p10/med/p90 |
|---|---|---|---|
| NY alone | **11.8%** | 47/57 | $66,000/$94,000/$114,000 |
| NY + London (window-end x uncapped, clock) | **12.1%** | 53/62 | $78,000/$106,000/$124,000 |
| NY + London (22pt x 2/session, clock) | **14.0%** | 54/64 | $71,800/$108,000/$128,000 |
| London separate account (window-end x uncapped) | **35.5%** | 23/31 | $4,000/$46,000/$62,000 |
| London separate account (22pt x 2/session) | **37.0%** | 20/28 | $4,000/$40,000/$56,000 |

## Sensitivity 1 — haircut London's mean R

Margin of safety on an unspent holdout: at what degradation does London's contribution reach zero?

| haircut | arm | combined net | vs NY-alone |
|---|---|---|---|
| 0% | window-end x uncapped | $+109,060 | **$+19,045** |
| 0% | 22pt x 2/session | $+110,916 | **$+20,901** |
| 25% | window-end x uncapped | $+110,194 | **$+20,179** |
| 25% | 22pt x 2/session | $+106,566 | **$+16,551** |
| 50% | window-end x uncapped | $+102,923 | **$+12,908** |
| 50% | 22pt x 2/session | $+100,541 | **$+10,526** |
| 75% | window-end x uncapped | $+96,289 | **$+6,274** |
| 75% | 22pt x 2/session | $+95,061 | **$+5,046** |

## Sensitivity 2 — weekly blocks

Daily blocks assume no week-scale autocorrelation. Repeat at 5-day blocks.

| config | P(bust) daily | P(bust) weekly | med payout daily | med payout weekly |
|---|---|---|---|---|
| NY alone | 11.8% | 5.5% | $94,000 | $94,000 |
| NY+London (window-end x uncapped) | 12.1% | 5.9% | $106,000 | $106,000 |
| NY+London (22pt x 2/session) | 14.0% | 6.9% | $108,000 | $108,000 |

## Sensitivity 3 — second NY profile (scaled600)

scaled600 NY-alone: 927 trades, $+320,662, P(bust) 97.2%, med payout $30,000

| arm | combined net | vs NY-alone | P(bust) |
|---|---|---|---|
| window-end x uncapped | $+101,193 | **$-219,469** | 83.8% |
| 22pt x 2/session | $+118,672 | **$-201,991** | 80.5% |

scaled600's budget scales with buffer, so contention behaves differently — a larger NY risk unit crowds London harder under one shared budget.
