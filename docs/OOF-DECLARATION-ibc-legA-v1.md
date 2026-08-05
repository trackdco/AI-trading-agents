# OOF DECLARATION #2 — NYA-IBC-01 frozen spec v1 (leg A), sealed months

Date: 2026-08-05. AUTHORIZATION: Angus — "we need to validate this out of
fit now." Second sealed-data spend, logged. Scope: sealed FLOW at leg-A
touch minutes (unread by look #1, which was scoped to leg-B mid-touch
minutes); candles of those months were never sealed. Run ONCE.

## The spec under test (frozen, byte-identical to fit)
Entry: first touch of intact 30-min IB extreme, 10:00-10:30, close-break
veto. Stop: 0.5 x legacy risk (0.125xIB). Target: developing near VWAP
sigma band (vwap - side*sd), valid when >= 0.125xIB from entry. Scratch:
t+10 close if red. Sizing: $160 base / $400 confirmed (Angus ruling).

## Conviction flags (thresholds FROZEN from fit — not recomputed)
1. early: touch at 10:00 exactly (fit median entry minute = 0).
2. stretched: session cvd (cumulative delta from 18:00, signed to trade)
   < 0 at entry minute. [sealed footprint flow]
3. delta_with: touch-minute delta signed to trade > 0. [sealed flow]
4. near_target: side*(entry - band_at_entry)/stop >= -1.7874 (fit
   median) — i.e. the developing band within ~1.79 true-R of entry.
   LABEL CORRECTION disclosed: previously mis-described as "wide band";
   the computed and tested flag is target PROXIMITY.
CONFIRMED = >= 3 of 4; else BASE.

## Pre-committed verdict rule
- PASS: total $ at ruled sizing > 0 AND confirmed-tier WR >= base-tier
  WR + 10pp AND confirmed n >= 8. -> spec v1 validated OOF; shadow
  becomes confirmation, not gatekeeper.
- PARTIAL: total $ > 0 but tier test fails -> ladder UNPROVEN; spec
  survives flat-$160 only; conviction sizing waits for shadow.
- FAIL: total $ <= 0 -> spec to bench; shadow-only path; no re-looks.
Expected n ~ 50 (leg-A cadence ~2/wk over 6 months). No other outcome
may be claimed; near-misses are what the rule says they are.
