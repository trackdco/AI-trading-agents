# Market Engine

Deterministic NQ setup detector. Consumes 1-minute NQ bars, computes the
strategy indicators (VWAP/BB/volume-profile/structure), detects the documented
mechanical setups, and emits a candidate JSON. **No LLM calls, no order
execution, no account state** (architecture firewall).

## Status — honest

| Piece | State |
|---|---|
| Indicator stack (daily+NY VWAP w/ vol-weighted bands, BB, volume profile POC/VAH/VAL) | ✅ built, computes on real data |
| Structure (15m swings, HTF flag, liquidity pools + sweeps) | ✅ built |
| Cluster + trigger detection (rejection block, displacement, patterns A/B/B2) | ✅ built |
| 20-field candidate payload (pydantic-validated) | ✅ built |
| Historical replay proof on real 2023→Jan-2026 data | ✅ **proven** (see below) |
| **Calibration (§12 February re-run)** | ❌ **blocked — no Feb 2026 data in repo** |
| **Step-4 parity sign-off (Angus)** | ❌ **blocked — needs Feb data + chart values** |
| Live Databento feed | ⏸️ **deliberately not built** — gated behind the two gates above |
| Docker / VPS deploy | ⏸️ **deliberately not built** — same gate |

### Output contract (per user directive)
The Engine emits **20 market-observation fields only**. The four account/history
fields — `recent_trade_history`, `setup_historical_performance`,
`account_risk_percent_per_trade`, `proposed_position_size_and_risk` — are
injected by the **Vault** downstream, right before the merged candidate goes to
Hermes. This keeps the Engine's no-account-visibility firewall intact
(`architecture.md` layer contract). See `engine/schema.py`.

## Proof (real data, no live feed)

```
python -m scripts.replay --data ../glbx-mdp3-20251002-20260131.ohlcv-1m.csv.zst \
    --start 2026-01-05 --end 2026-01-30
```
Result on the real Jan-2026 NQ data:
- RAW per-bar triggers: **401** (20.1/session)
- DISTINCT setups (Vault one-position rule, 20-min cooldown): **105** (5.2/session)
- Strategy §10 expectation: **2–3 genuine setups/session**

→ The pipeline works end-to-end and emits valid schema JSON, **but the
uncalibrated detector over-fires ~2× even after one-position collapse.** This is
the expected, honest calibration gap — it is *why* §12 calibration and the
Step-4 parity sign-off gate live trading. No thresholds were tuned to hide it
(spec-1 §5 forbids tuning-to-fit). Sample validated payload:
`output/sample_detection.json`.

## The blocker you need to clear next

`strategy-definition-v1.0.md §12` and `spec-1` Step 4/Step 8 validate against
the **Feb 2026** hand-log period. **That data is not in the repo** — coverage
ends `2026-01-31` (`python -m scripts.parity` confirms it). To clear the gate:

1. Pull **Feb 2026 (ideally Feb–Jul) 1m NQ GLBX.MDP3 from Databento
   *historical*** (cheap; not the live streaming entitlement).
2. Re-run `python -m scripts.parity`, fill in Angus's chart values, get sign-off.
3. Run the §12 calibration vs the 28 hand trades.

Only after that: live feed + Docker + VPS deploy (all deferred by design).

## Layout
```
config/strategy.yaml     every number traced to a § of the strategy doc (starting values)
config/news_calendar.csv Feb-2026 seed; rest is a TODO
engine/                  data, sessions, indicators, structure, clusters, triggers, payload, schema, detector, run
scripts/replay.py        historical detection proof
scripts/parity.py        Step-4 parity harness (currently BLOCKED on Feb data)
tests/                   invariant tests (NY-VWAP-pre-0930, profile) — `python -m pytest`
```

## Run
```
pip install -r requirements.txt
python -m pytest tests -q
python -m scripts.replay --data <file.csv.zst> --start YYYY-MM-DD --end YYYY-MM-DD
```
`FEED=live` refuses to start until the gates clear (see `engine/run.py`).
