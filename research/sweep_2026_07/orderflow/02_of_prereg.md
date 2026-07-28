# Order-flow pre-registration — written BEFORE any outcome is examined

**Status: FROZEN 2026-07-28, before any feature-vs-outcome number was computed. Per Brake's
brief, NO hypothesis testing happens until the baseline ruling and H0 land. This file exists so
the thresholds are on record before anyone looks.**

## The question (framed per the brief)

NOT "can order flow remove losers." That is answered four ways and fails structurally: 26 trades
carry 98.1% of the window, so any loser-culling filter eventually culls one of them and the
window dies. The registered questions are the opposite:

**Q1 — At entry, does order flow separate the trades that go on to reach +4R from everything
else?** Target variable: `mfe_R >= 4.0` (already computed, fill→exit, in `phase2_frame.csv`) —
a 26-vs-190 classification, evaluated by rank separation (AUC) and by the +4R rate in the top
vs bottom tercile of each feature.

**Q2 — Does order flow explain the H5 gap-day concentration?** The 23 wrong-contract-day trades
(46.5% of window P&L, mean R +1.57 vs +0.23) fall in expiry weeks. Question: do those days carry
a distinct order-flow signature at entry (volume, two-sided balance, absorption), or is their
outperformance unrelated to anything visible in flow? Descriptive comparison, day-clustered.

## Pre-registered thresholds and ranges (fixed now)

| item | value | why fixed here |
|---|---|---|
| pre-fill window | 30 completed minutes, strictly before the fill minute | matches the coverage gate in step 2 |
| short window | 5 minutes | the canon's own d5 convention |
| stacked-imbalance ratio | 3:1, ≥3 consecutive levels | the textbook definition; NOT swept |
| divergence sign test | sign(Δprice) ≠ sign(Δcvd) over 15 min | canon's div15 convention |
| tercile edges | computed on the IS half only (trades before 2025-12-11 split) | H4's failure was a threshold from data that included OOS |
| evaluation | AUC + top-vs-bottom tercile +4R rate, day-clustered bootstrap CIs | rank-based, no fitted cutoffs |
| multiplicity | every feature × 2 questions counted and reported; family-wise null priced by day-block permutation of the +4R labels | the London campaign's noise floor discipline |

## What would falsify Q1

The direction-blind twin (|delta|, total volume) matching or beating the signed features — the
falsifier that killed the London and NY-window campaigns — and/or the family-wise best failing
to beat the day-block permutation noise floor.

## Explicitly out of scope until rulings land

- Any evaluation of these features against outcomes (blocked on H0 + baseline ruling).
- Any exit or in-trade rule.
- Any loser-removal framing.
- The 2025 tape's price-derived features (absorption uses range) are computed ONLY after
  band-cleaning to the day's bar [low, high]; delta/CVD features are price-free and unaffected.
