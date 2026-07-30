# Combined job — Stage 4: Monte Carlo suite

**Fit only. Sealed 2023/24 never loaded.**

2,000 paths, 252 days, seeded (20260730). Day-level bootstrap resampling whole calendar days with BOTH books' trades in the SAME draw, intraday order preserved. Resampling the books independently would manufacture diversification and flatter the combined distribution.

Funded rules: start $50,000, $2,000 trailing EOD DD locking at start once equity reaches $52,000, full $2,000 payout at $54,000.

## Sanity check

**NY-alone P(bust) = 2.4%** — must land in 0.5%-4%. PASS

## Headline

| config | P(bust) | cycles med/p90 | net payout p10/med/p90 |
|---|---|---|---|
| NY alone | **2.4%** | 27/30 | $73,805/$92,552/$111,011 |
| NY + London (window-end x uncapped, clock) | **1.6%** | 28/31 | $86,347/$105,021/$122,790 |
| NY + London (22pt x 2/session, clock) | **1.7%** | 29/31 | $86,621/$106,922/$126,399 |
| London separate account (window-end x uncapped) | **9.1%** | 24/27 | $30,013/$47,966/$60,852 |
| London separate account (22pt x 2/session) | **10.3%** | 23/26 | $23,179/$42,148/$53,983 |

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
| NY alone | 2.4% | 0.7% | $92,552 | $92,613 |
| NY+London (window-end x uncapped) | 1.6% | 1.1% | $105,021 | $103,897 |
| NY+London (22pt x 2/session) | 1.7% | 0.9% | $106,922 | $106,485 |

## Sensitivity 3 — second NY profile (scaled600)

scaled600 NY-alone: 927 trades, $+320,662, P(bust) 84.1%, med payout $102,515

| arm | combined net | vs NY-alone | P(bust) |
|---|---|---|---|
| window-end x uncapped | $+101,193 | **$-219,469** | 30.9% |
| 22pt x 2/session | $+118,672 | **$-201,991** | 27.7% |

scaled600's budget scales with buffer, so contention behaves differently — a larger NY risk unit crowds London harder under one shared budget.
