# Parity Report (spec-1 Step 4)

Data coverage: **2023-01-02 18:00:00-05:00 → 2026-01-30 16:59:00-05:00**

Angus: compare each COMPUTED value below to the reference-chart value; each must agree within **1.0 NQ pt**. Do not sign off on rows marked NO DATA.

| Timestamp (ET) | Note | BB basis | daily VWAP | +1σ | −1σ | NY VWAP | daily POC | chart value | Δ | ✓ |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-02-11T09:48 | PARITY reference (Feb NFP short) — needs Feb data | — | — | — | — | — | — | _fill_ | _fill_ | ❌ NO DATA |
| 2026-02-17T09:50 | PARITY reference — needs Feb data | — | — | — | — | — | — | _fill_ | _fill_ | ❌ NO DATA |
| 2026-01-13T09:50 | IN-COVERAGE illustration (format/computation proof only) | 25971.0 | 25950.38 | 25997.95 | 25902.81 | 25963.0 | 25970.25 | _fill_ | _fill_ | ⬜ |

## Gate status
- ❌ **BLOCKED — parity cannot be signed off.** The two required reference dates (Feb 11 & Feb 17 2026) are outside data coverage.
- **Unblock:** pull Feb 2026 (ideally Feb–Jul for out-of-sample) 1m NQ GLBX.MDP3 from Databento **historical**, then re-run `python -m scripts.parity`.
- Steps 5-9 detection is built but must be treated as UNCALIBRATED until this gate and the §12 February calibration pass.