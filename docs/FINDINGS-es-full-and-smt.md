# FINDINGS — ES full history, and SMT divergence: both KILLED (2026-09-03)

Two questions settled with the full ES pull (2023-01-01 → 2026-09-02).

1. **ES standalone: dead flat.** +102R over 807 session-days = **+0.13R/day**.
   The 3-month look that showed +0.083R/trade was 2026 only — the best of
   the four years. Classic §3 selection artifact.
2. **SMT divergence (NQ vs ES): NULL.** Trades where ES confirms
   (+0.1958R) and trades where it diverges (+0.1976R) are
   indistinguishable. The cross-market signal carries no information.

## 0. Data

Databento GLBX.MDP3 `ES.FUT`, ohlcv-1m, 2023-01-01 → 2026-09-02.
Outrights only, volume-rolled front month: **1,299,123 bars, 954
session-days, 14 rolls**, price 3816.75–7837.75. 807 days survive the
engine's completeness filter. Screen: median active-session 1m candle
**1.50pt = 6.0 ticks** (NQ 28, GC 21) — fails the ≥20 bar.

## 1. ES over four years

Certified cell (depth 0.75 = 3 ticks, 1R), honest fills, SAR, news gate.
Cost model: $4/RT commission always, plus one tick of spread **only on
market exits** (STOP/SAR/FLAT ≈ 46% of trades) — the entry and the target
are resting limits and pay no spread.

| | n | WR | raw EV | net EV | IS | OOS | net R | R/day |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ES best cell | 8,529 | 63.4% | +0.1228 | **+0.0120** | +0.0017 | +0.0194 | **+102** | +0.13 |

Technically positive in both halves, but +0.0017R in-sample is zero with
extra steps. Every other cell in the 20-cell grid is negative.

Year by year:

| year | median 1m candle | ticks | n | WR | raw EV | net EV | net R |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 1.25pt | 5.0 | 1,870 | 64.0% | +0.1273 | +0.0091 | +17 |
| 2024 | 1.25pt | 5.0 | 2,025 | 63.4% | +0.1204 | +0.0037 | +7 |
| 2025 | 1.75pt | 7.0 | 2,588 | 62.1% | +0.1010 | −0.0067 | −17 |
| 2026 | 2.00pt | 8.0 | 2,046 | 64.5% | +0.1484 | **+0.0466** | +95 |

**93% of the four-year total comes from 2026 alone.** The earlier 3-month
result (+0.083R/trade on 57 days) sampled exactly that window. This is
the §3 lesson repeating: a short look lands on the best regime and reads
like an edge.

**An overclaim, corrected.** A first pass called this "the edge appears
as the tick ratio grows", which would have made the ≥20-tick screen a
proven mechanism rather than a heuristic. It does not hold: raw EV is
**not** monotone in ticks (2025 has more ticks than 2024 and the worst
result). Four annual points cannot separate the tick ratio from "2026 was
simply a good year" — NQ's 2026 was also its strongest. The screen remains
a useful heuristic with three supporting instruments, not a demonstrated
mechanism.

**Verdict: ES is not dead the way 6E is — it is flat.** The raw edge is
real and consistent (WR 62–65% every year, raw EV +0.10 to +0.15R), and
cost removes essentially all of it. Not worth trading standalone. Its
remaining value is as a *signal source*, which is question 2.

## 2. SMT divergence: NULL

Feature, as-of the signal bar, 30-bar lookback, no lookahead. For a long
break: did NQ's signal bar exceed the prior 30-bar high, and did ES?
`confirm` both did · `diverge` NQ only (classic SMT) · `es_leads` ES only
· `neither`. Population: NQ PD value area certified cell, 7,307 trades
over 764 days — **every one matched to ES bars** (1,261,153 shared
minutes).

| SMT state | n | share | WR | net EV | IS | OOS |
|---|---:|---:|---:|---:|---:|---:|
| confirm | 1,428 | 19.5% | 69.7% | **+0.1958** | +0.1922 | +0.1986 |
| diverge | 522 | 7.1% | 70.4% | **+0.1976** | +0.1392 | +0.2561 |
| es_leads | 271 | 3.7% | 67.1% | +0.1870 | +0.1459 | +0.2222 |
| neither | 5,086 | 69.6% | 66.2% | +0.1388 | +0.1622 | +0.1214 |

**confirm − diverge: IS +0.0530, OOS −0.0574.** Sign flips, and the
smallest half-cell is 261 against the rule's 400. **NULL** on both counts.

More telling than the verdict: confirm (+0.1958) and diverge (+0.1976)
are the same number. Whether the other index agrees does not move the
trade at all. The classic reading — NQ making a high alone means
distribution — is not visible in 764 days of data.

**Collapsing the cross-market part away:** does NQ making a 30-bar
extreme matter *at all*, ignoring ES?

| group | IS n | IS EV | OOS n | OOS EV |
|---|---:|---:|---:|---:|
| NQ made the extreme | 892 | +0.1767 | 1,058 | +0.2128 |
| NQ did not | 2,290 | +0.1613 | 3,067 | +0.1262 |

Spread IS +0.0154 / OOS +0.0866 — same sign, but the in-sample half is
under the 0.03 WATCH floor. **NULL** as well, and in any case this is a
single-market displacement feature already covered by the conviction
audit's `excur`.

## 3. What this closes

- **ES:** not a second NQ, not a diversifier. Flat after cost, and 0.855
  correlated with NQ on 1-minute returns even if it were not.
- **SMT:** the first cross-market feature tested, and it is null. That is
  worth knowing — it means the failure of every internal feature (candle
  shape, volume, confluence, distance-to-level, prior-day shape) is not
  simply "we looked in the wrong place inside NQ". Cross-market
  information does not help either, at least not in this form.
- The instrument screen now has a fourth data point and its ordering
  held: NQ 28 ticks works, GC 21 works, ES 6 is flat, 6E 3 is negative.

## 4. Caveats

- One SMT encoding (30-bar extreme). A level-based variant — is ES
  breaking its own value area at the same moment — was looked at on the
  short sample and every cell was noise; it has not been re-run on the
  full history. It is the one remaining version of this idea.
- The ES constants are ratio-derived, not natively calibrated. Gold's
  native sweep landed on its ratio cell, so the prior is decent, but a
  native sweep was not run — there was no positive result to defend.
- Cost model is $4/RT plus one tick on market exits. At $2/RT commission
  ES's best cell reaches roughly +0.03R/trade; still not tradeable.
