# Why 2026 broke the tight-stop band (and not the shipped book)

**Fit only. Sealed 2023/24 never loaded. Diagnosis of an observed crossing — NOT a proposal to change the floor.**

## First, correct the premise: 2026 was a GOOD year for the shipped strategy

| era | n | win rate | mean R | net (1 lot) | avg win R | avg loss R |
|---|---|---|---|---|---|---|
| 2025 | 78 | 61.5% | +0.434 | $+8,178 | +1.21 | -0.82 |
| 2026 | 109 | 53.2% | +0.570 | $+14,618 | +1.78 | -0.80 |

2026 made **$+6,440 more** on 31 more trades at a HIGHER mean R. The win rate fell 62% -> 53%, but the average winner grew +1.21 -> +1.78 R while the average loser stayed flat (-0.82 -> -0.80 R). That is the signature of a higher-volatility regime: you are right less often, the stop still contains the damage, and the wins run further. **Only the tight-stop band broke.**

## The regime: volatility roughly doubled

Medians over the whole candidate population, so this is the market, not a selection effect.

| measure | 2025 | 2026 | change |
|---|---|---|---|
| session range (pts) | 100.75 | 179.00 | **+77.7%** |
| 30-min range (pts) | 27.50 | 44.25 | **+60.9%** |
| structural stop width (pts) | 3.25 | 5.25 | **+61.5%** |

## The mechanism: the stops did not follow

A stop only works if it sits OUTSIDE the day's noise. What matters is therefore not the stop in points but the stop as a share of the session's own range.

| book | era | median stop | median session range | **stop / range** |
|---|---|---|---|---|
| shipped >=9.5pt | 2025 | 12.25pt | 173.9pt | **8.07%** |
| shipped >=9.5pt | 2026 | 13.00pt | 233.0pt | **5.61%** |
| sub-9.5pt band | 2025 | 6.50pt | 105.8pt | **5.80%** |
| sub-9.5pt band | 2026 | 6.50pt | 188.0pt | **3.52%** |

The band's stop did not move at all — 6.50pt in both eras — while the range it had to survive went 106pt -> 188pt. So it fell from 5.80% of the range to 3.52%, i.e. **39% tighter in real terms** without anyone changing a setting. The shipped book took the same erosion (8.07% -> 5.61%) but started with enough margin to absorb it.

## The fingerprint: how the trades actually died

If the diagnosis is right, the band should show more trades stopped out BEFORE reaching a first partial, and fewer reaching target. Share of trades by exit:


**shipped >=9.5pt**

| era | partial+stop | partial+target | stop | target |
|---|---|---|---|---|
| 2025 | 46% | 13% | 37% | 4% |
| 2026 | 30% | 22% | 42% | 6% |

**sub-9.5pt band**

| era | partial+stop | partial+target | stop | target |
|---|---|---|---|---|
| 2025 | 32% | 24% | 35% | 9% |
| 2026 | 24% | 11% | 57% | 7% |

That is the confirmation. The band's clean-stop rate — stopped out with no partial banked — goes **35% -> 57%**, and its partial+target rate halves **24% -> 11%**. The shipped book's clean-stop rate barely moves (37% -> 42%) and its partial+target rate nearly DOUBLES (13% -> 22%): the same volatility that killed the tight stops paid the wide ones.

## Is it one bad patch, or decay?

| month | band n | band mean R | band WR | shipped n | shipped mean R |
|---|---|---|---|---|---|
| 2025-06 | 24 | +0.838 | 58% | 14 | +0.081 |
| 2025-07 | 28 | +0.250 | 46% | 7 | -0.615 |
| 2025-08 | 18 | +0.778 | 67% | 6 | +1.145 |
| 2025-09 | 24 | +0.490 | 67% | 12 | +0.635 |
| 2025-10 | 28 | +0.889 | 57% | 12 | +0.852 |
| 2025-11 | 25 | +2.491 | 72% | 22 | +0.552 |
| 2025-12 | 17 | +0.482 | 65% | 5 | +0.027 |
| 2026-01 | 27 | +0.168 | 52% | 10 | +0.641 |
| 2026-02 | 12 | +0.234 | 33% | 12 | -0.200 |
| 2026-03 | 23 | +0.379 | 35% | 34 | +0.612 |
| 2026-04 | 17 | +0.669 | 65% | 11 | +0.333 |
| 2026-05 | 23 | +0.428 | 43% | 20 | +1.009 |
| 2026-06 | 25 | -0.007 | 24% | 18 | +0.616 |
| 2026-07 | 9 | -0.940 | 0% | 4 | +0.574 |

**Decay, not a patch.** The band holds up through 2025, wobbles from 2026-02, and is negative in the last two months of the fit span (2026-06 at 24% WR, 2026-07 at 0% on n=9). The shipped book stays healthy across the whole of 2026. A single volatility event would show as one bad month in both books; this is a one-sided trend.

## The point worth keeping

The floor is written in ABSOLUTE POINTS, so its real tightness floats with the market:

| era | median session range | 9.5pt floor as a share of range |
|---|---|---|
| 2025 | 100.8pt | **9.43%** |
| 2026 | 179.0pt | **5.31%** |

To hold 2025's real tightness in 2026 the floor would have had to be **16.9pt**. Nobody loosened the floor — the market did it, by getting bigger. That single fact explains the era crossing that rejected floor 5: the crossing was never evidence that tight-stop SETUPS are bad, it was evidence that a FIXED point floor means different things in different regimes.

### What follows, and what does not

**Does not follow:** any change to the floor. Floor 5 stays rejected (§1). A volatility-scaled floor — expressed as a share of session range or an ATR multiple rather than in points — is a NEW hypothesis resting on n=2 regimes, one of which was used to find it. It would need its own pre-registration and its own out-of-sample test, and it is not going into the current holdout, which is already at 2 gated questions and ~84 projected trades.

**Does follow — a forward risk worth naming.** The shipped book's stop/range also eroded, 8.07% -> 5.61%. It has margin today. If volatility keeps rising, the shipped book meets the same wall the band already hit, and it will look like alpha decay when it is actually a units problem. Worth watching stop/range as a live health metric rather than discovering it later.

**Also follows — a caveat on reading the holdout.** 2023/24 is a different volatility regime, and a fixed 9.5pt floor is relatively TIGHTER in a calm market and LOOSER in a wild one. So part of whatever the holdout reports is a statement about 2023/24's ranges, not purely about the edge. Measuring the sealed span's session ranges would contextualise the result, and `on_range` is a market-condition feature rather than an outcome — but it is still the sealed span, so it is NOT read here. Flagged as an authorisation question, not taken.
