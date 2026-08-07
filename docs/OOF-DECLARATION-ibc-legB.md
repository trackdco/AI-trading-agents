# OOF DECLARATION — NYA-IBC-01 leg B, the single sealed-months look

Date: 2026-08-05. This document is written BEFORE the look and commits the
slate, the mechanics, and the decision rule. The sealed months are spent
ONCE; no re-runs, no added arms after this file exists.

AUTHORIZATION (Angus, 2026-08-05, verbatim): "go ahead, this will probably
look much better with conviction sizing once we can define what a good
trade is... let me know what the go is" — given in response to the
three-spec slate proposal with the decision rule stated.

## The look
- DATA: the six sealed months — 2023-07, 2023-09, 2023-11, 2024-03,
  2024-04, 2024-10. Candles from nq_1m_master; flow from
  data/reference/cvd/footprint_holdout_*.parquet (minute delta = ask-side
  volume minus bid-side volume); depth from data/reference/depth_2023_24
  (per-minute book imbalance from the last snapshot in each minute).
  These flow/depth features have never been consumed by any leg-B trial.
- SLATE (frozen, three specs, mechanics byte-identical to
  scripts/nya_ibc_stage2.py):
  - B0 as-taught: entry first mid-touch 10:23-11:30 (developing levels
    pre-10:30), stop = first-formed extreme, target = predicted extreme,
    wick-death universe, no BE.
  - B1 cap20: B0 with risk capped at 20pts (stop 20pts from entry),
    taught target unchanged.
  - B8 full stack: cap30 + front-run-only entries (10:23-10:29) +
    mechanical early-cut at t+15 (MAE >= 0.5R OR cvd-since-entry <= 0) +
    conviction sizing (units = 1 + score; score = weekday trailing rate
    >= 0.70 [causal, prior days only] + entry-minute delta agreement +
    entry-minute book lean > 0.1 signed).
- COSTS: base 1pt friction. SIZING: $160 per unit-risk.

## The decision rule (pre-committed)
Winner = highest total risk-normalized dollars across the six months,
IF that spec is positive out-of-fit. Then:
- Winner positive -> it becomes the leg-B FROZEN CANDIDATE for stage 4
  (combined-book grading with leg A + conflict rule). Angus still holds
  the §5.11-8 baseline sign-off and the ship decision — this look
  promotes a candidate, not a shipped strategy.
- ALL three negative -> leg B PARKS; the complex proceeds as leg A alone.
- No other outcome is available. Ties/near-ties (within $200): the
  SIMPLER spec wins (B0 > B1 > B8 in simplicity order).

## Honest notes
- 6 months ~ expected 25-35 leg-B events (one-a-day family; Angus:
  "over a couple hundred trades we can still see patterns" — this look
  is a direction check at n~30, not a certification; the certification
  standard stays PSR/grading at stage 4 on the fit span with OOF as
  supporting evidence).
- Conviction-tier refinement (defining "good vs average setups" into a
  calibrated ladder) is STAGE-4+ work on fit data and must satisfy
  §5.12.1-14 monotonicity testing; this look only scores the three
  frozen specs as declared.
