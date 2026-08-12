# PREREG — L3 pre-print direction test

STATUS: DRAFT — freeze by committing, record sha
(`python -c "from newslab.l3 import prereg_sha; print(prereg_sha())"`),
export NEWSLAB_PREREG_SHA, THEN unseal. Edits after unsealing void the run.

## Frozen choices (fill before freeze — Angus's rulings)
- Seal boundary (NEWSLAB_SEAL_FROM): __________  (default 2025-10-01)
- Primary horizon: +30m   Sensitivity: +15m, +60m (reported, not selected on)
- Primary stop: 20 pts    Sensitivity: 30, 50 (reported, not selected on)
- Entry reference: close(T−1m)
- Predictors, in priority order (max 4 — every extra predictor spends the
  multiple-testing budget):
    1. nowcast_gap (Cleveland − consensus; cpi/pce)
    2. drift_30m sign (pooled, all families)
    3. kalshi_skew (families with coverage)
    4. feeder-implied PCE residual (pce only)
- Pooling: all families with valid predictor, weighted equally per event.
- Direction map: SURPRISE_TO_NQ_SIGN as committed in config.py.

## Kill rule (binding)
NO-TRADE unless BOTH hold on DISCOVERY, then CONFIRMED on the sealed era:
  (a) pooled accuracy Wilson CI-low > 0.50
  (b) gap-adjusted EV > 0 at WORST-bound stop fills, primary stop/horizon
A discovery pass that fails on the sealed era is recorded as REFUTED —
no re-tuning, no second unseal on this prereg.

## Pre-committed interpretations
- Ceiling test (surprise_z as predictor, labelled lookahead) FAILS →
  the pre-print lane is CLOSED for all predictors; fallback (reaction lane)
  inherits; verdict logged.
- n(pooled, valid predictor) < 150 at freeze time → do not run L3 yet;
  extend the event table / predictors first. Wide-CI fishing is not a lane.
- One giant winner carrying the EV (single-event jackknife flips sign) →
  verdict downgraded to INCONCLUSIVE, logged with the offending event.
