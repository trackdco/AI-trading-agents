# CEILING TEST — is the pre-print direction lane tradable at all?

Run 12 Aug 2026 on 442 measured events (99.5% bar coverage), unsealed only,
five high-impact families: cpi, nfp, fomc, pce, ppi. Entry `close(T−1m)`,
horizon +30m. R = points / stop.

This is the test SPEC.md §L3 demands FIRST: **predictor = the actual outcome**,
a deliberate lookahead run. It answers one question — *if you knew the
direction with certainty, was it even tradable after gap-adjusted fills?*
If this fails, every honest predictor fails and the lane closes.

## Result: passes on the mean, fails on what matters

Pooled ceiling EV with **perfect direction foresight**: **+0.77R** per event
(worst-bound fills). Jackknife-stable — dropping any single event moves it
only 0.67R–0.83R, no sign flip. So the number is real, not one lucky print.

But two things gut it.

**1. You get stopped out 46% of the time WHILE BEING RIGHT.** The release bar
whipsaws through a 20pt stop in both directions before resolving. Median
outcome with perfect foresight is **−1.21R for both CPI and NFP** — the
positive mean is carried by a minority of huge winners.

| family | n | p_stopped | EV_R (worst) | median R |
|---|---|---|---|---|
| cpi | 33 | 0.515 | +0.85 | **−1.21** |
| nfp | 32 | 0.562 | +0.50 | **−1.21** |
| fomc | 22 | 0.500 | +0.82 | −0.28 |
| ppi | 33 | 0.424 | +0.66 | +1.14 |
| pce | 32 | 0.312 | +1.04 | +1.08 |
| **POOLED** | **152** | **0.461** | **+0.77** | +0.29 |

**2. The break-even accuracy is out of reach.** When right you make +0.77R;
when wrong you lose **−3.43R**, because the print gaps against you and the
stop fills in the hole. A 4.5:1 adverse ratio.

| stop | EV if right | EV if wrong | break-even accuracy |
|---|---|---|---|
| 10pt | +0.55R | −6.77R | **92.4%** |
| 20pt | +0.77R | −3.43R | **81.7%** |
| 30pt | +0.88R | −2.29R | **72.1%** |
| 50pt | +0.76R | −1.38R | **64.5%** |

Published macro-surprise direction models rarely clear 55–60% out of sample,
and PREREG-L3's kill rule only requires Wilson CI-low > 0.50. **Nothing in the
predictor list — nowcast gap, feeder chain, Kalshi skew, pre-drift — plausibly
reaches 65%, let alone 82%.**

## The finding that actually matters

The verdict is decided by **fill quality, not prediction skill**:

| stop | break-even acc (WORST fill) | break-even acc (BEST fill) |
|---|---|---|
| 20pt | 81.7% | 39.8% |
| 30pt | 72.1% | 42.4% |
| 50pt | 64.5% | 48.1% |

At the best bound (filled at your stop price) you need ~40% accuracy — a coin
flip clears it. At the worst bound (filled in the hole) you need 82%. Truth is
bracketed by these, and for a stop resting through a **median 120pt CPI
release bar** reality sits far closer to WORST. That is precisely why SPEC.md
mandates the worst bound for expectancy.

Release-bar size, unsealed median / p90 / max (points):

| family | median | p90 | max |
|---|---|---|---|
| cpi | 120.5 | 199.7 | 285.2 |
| nfp | 99.5 | 186.6 | 249.8 |
| fomc | 63.0 | 79.5 | 237.5 |
| ppi | 56.0 | 117.1 | 176.2 |
| pce | 41.8 | 73.8 | 103.8 |

## Verdict

**The lane as conceived — enter before the print, futures, stop-protected —
is very likely dead.** Not because the direction is unpredictable, but because
a stop resting through the release bar is not a 1R risk. It is a 2.4–5.1R risk.

This closes the lane before any predictor is built. Building the Cleveland
nowcast fetcher, the Kalshi feed or the CPI+PPI→PCE feeder chain would not
change it: they compete on the axis (accuracy) that is not binding.

## What is NOT closed

1. **Defined-risk structures.** The entire problem is unbounded gap loss. A
   long option or debit spread caps loss at premium and removes the gap term
   from the equation. The ceiling EV of +0.77R is then competing against
   premium, not against a 3.43R tail. Untested here, and the honest next test.
2. **PCE specifically.** Lowest stop rate (0.312), highest ceiling EV
   (+1.04R), positive median (+1.08R), smallest release bar (41.8pt median) —
   AND it is the most predictable release on the calendar via the CPI+PPI
   feeder chain. If any single-family lane survives, it is this one.
3. **The fallback lane.** The post-print reaction map needs no prediction and
   no pre-print entry, so none of the above touches it.
4. **The real slippage number.** This brackets fills between stop-price and
   bar-extreme. A broker fill study through actual prints would collapse the
   bracket and give a single verdict instead of a range.

## Caveats, stated plainly

- Unsealed era only (407 of 444 events); the sealed 37 are untouched.
- +30m horizon; sensitivity at +15m/+60m not yet run.
- "Perfect foresight" is of the **realised move**, not the surprise — the most
  generous possible ceiling for any directional predictor.
- No actuals or consensus exist yet (L0b unrun), so this says nothing about
  whether surprises are predictable. It says that question does not bind.
