# Pre-registration: scheduled-flow calendar effects in NQ

**Written before any result is computed. 2026-09-04.**

## Why this and not calendar spreads
The true front-vs-back spread test needs per-contract prices side by side; our tapes are a single
stitched continuous series, so that test needs a fresh per-contract Databento pull. This test uses the
same economic logic on data already owned: **index funds, pensions and futures holders must trade on a
published calendar** (month-end rebalance, quarterly expiry, holiday closes). Scheduled flow is
forced, visible in advance, and someone pays to be on the other side of it.

## Measurement (frozen)
- **Headline return = day session**: open of the 09:30 ET bar to close of the 15:59 ET bar, same day,
  in NQ points, minus 0.5 points cost. This is within one contract, so it is free of roll contamination.
- Secondary: 24-hour close-to-close with the quarterly roll window (10 trading days ending on the
  third Friday of Mar/Jun/Sep/Dec) excluded, per the overnight-drift finding.
- Holidays are derived from the tape: a weekday with no session. Day-before / day-after are the
  adjacent sessions.

## The nine buckets, declared now (no others will be added)
A turn of month (last trading day of the month through the first 3 of the next) · B last trading day
of the month · C first trading day of the month · D quarterly expiry week · E monthly expiry week ·
F day before a holiday · G day after a holiday · H last session of the week · I first session of the week.

## Pass/fail, declared now
A bucket **PASSES** only if all four hold:
1. Its mean day-session return exceeds the all-days mean on **all three** tapes.
2. Pooled t-statistic > **2.5** (raised from 2 because nine buckets are being tested at once; with
   nine buckets roughly one t>2 is expected by chance alone).
3. Same sign on all three tapes.
4. **Benchmark**: being long only on that bucket's days beats buy-and-hold **per day of exposure**,
   on all three tapes. (The overnight-drift lesson: a positive result in a rising market is not an
   edge until it beats owning the thing.)

Anything less is a FAIL. No new buckets, no sub-slicing by year, no time-of-day tuning.

## Predictions (scored after)
- P1: turn of month is the strongest bucket.
- P2: at least one bucket clears t>2.5 pooled but fails the all-three-tapes condition (the
  multiple-comparisons trap doing its work).
- P3: no bucket passes all four conditions.
