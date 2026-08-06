---
date: 2026-08-06
status: KILL — FVT continuation does not generalise. Optimisation surface is anti-predictive.
tags: [fvt, jj-simon, tombstone, holdout, overfitting, nq]
scripts: scripts/fvt_model.py, scripts/fvt_optimise.py, scripts/fvt_oos.py
data: output/fvt_oos_grid.parquet
---

# FVT tombstone — optimised on 2024-2026, dead on 2023

800 cells (5 sessions x 160 configs: stop multiplier, RR target, continuation window, attempt
cap) fitted on 2024-01-01 -> 2026-07-15 (793 sessions, 19,469 entries), then run unchanged on
**all of 2023** (310 sessions, 7,554 entries) which had never been touched.

## Every session's fit-best config loses out of sample

| session | best config on fit | fit | 2024 | 2025 | 2026 | **2023** |
|---|---|---:|---:|---:|---:|---:|
| NY AM | stop×1.25 RR4.0 cont25m cap1 | +4.28 | +4.15 | +4.73 | +3.68 | **−7.29** |
| NY PM | stop×1.5 RR1.5 cont10m cap1 | +0.48 | +1.38 | +0.61 | −1.43 | **−2.05** |
| 6PM | stop×1.0 RR4.0 cont10m cap2 | −0.60 | −3.09 | +1.36 | +0.14 | −1.05 |
| 8PM | stop×1.5 RR2.0 cont25m cap1 | +1.07 | +0.39 | −1.15 | +6.39 | **−2.54** |
| London | stop×1.5 RR4.0 cont10m cap1 | −0.57 | −1.37 | +0.80 | −1.58 | +1.28 |

NY AM ran **+4.15 / +4.73 / +3.68** across three independent fit years and then **−7.29**.

## The ranking inverts

Rank correlation between fit and 2023 net-per-trade, across all 160 cells in a session:

| NY AM | NY PM | 6PM | 8PM | London |
|---:|---:|---:|---:|---:|
| **−0.413** | **−0.394** | +0.246 | +0.083 | +0.662 |

Negative on both NY sessions means the configs that scored best on 2024-26 are *systematically
the worst* in 2023. Optimising did not merely fail — it pointed the wrong way.

## The finding that matters most

| population | 2023 |
|---|---|
| all 800 cells | 18% positive, mean **−1.74** pt/trade |
| the 13 positive in ALL THREE fit years | **0% positive, mean −6.19** pt/trade |

**The three-era consistency bar is anti-predictive here.** It was introduced as a *stronger*
test after two-era consistency passed NY AM and 6PM, both of which later collapsed. It turned
out to select for cells that had fitted 2024-26's particular character hardest. All 13
survivors were NY AM; all 13 lost badly.

Multi-era consistency is not evidence of robustness when the eras share a regime. 2024-2026
are three slices of one market character; 2023 is a different one.

## PBO called it

The session sweep returned **PBO 0.709** before the holdout was spent — literally "the
in-sample winner is usually a below-median out-of-sample performer." The holdout confirmed it
exactly. `src/validation/overfit.py` works, and it is cheaper than a holdout because it can be
re-run.

## What survives FVT

Nothing session-specific or parameter-specific. Only the three mechanisms that were established
*before* any optimisation:

1. **The exit regime** — fixed ATR-tier stop, fixed R target, no management, no partials.
   31.7% target-hit and 42.5% win rate vs the canon's 2.9% and 22.7%.
2. **Continuation beats reversion** — 5/5 sessions, every era, every parameter setting. The
   strategy is *named* for reversion to fair value and that is the half that bleeds.
3. **The flow inversion** — aggressive flow already agreeing with the trade predicts a worse
   outcome. Replicated twice on different entry models and different measurements.

## Housekeeping

The 2023 holdout is **spent**. Anything next validates on walk-forward + PBO, or on a span
carved out and sealed before fitting begins.
