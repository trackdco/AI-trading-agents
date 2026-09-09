# FINDINGS — gap spliced, empire re-baselined on 954 session-days (2026-09-03)

`nq_1m_master` had a 39-day hole (2026-07-16 → 2026-08-22). Filled from a
fresh `NQ.FUT` pull covering 2026-07-13 → 2026-09-02, deliberately
**after** the 2020–22 holdout was scored so that the holdout's baseline
table kept describing exactly the 927-day tape it was computed on.

## 1. Splice receipt

| check | result |
|---|---|
| overlap with the existing tape | **14,616 shared minutes** (both ends) |
| price bars differing | **1** — 2.5pt on a single low |
| volume bars differing | **9** — max 81 contracts |
| duplicate minutes after splice | 0 |
| gaps longer than a long weekend | **0** |
| index monotonic and unique | yes |

The handful of differences are ordinary Databento revisions, not a
contract or scaling fault. `nq_1m_jul_sep2026.parquet` is listed **before**
the older slices in `BARFILES`, and `load_bars` keeps the first occurrence
on duplicates, so where old and new disagree the newer revision wins.
Reasoning recorded in a comment above `BARFILES` so it need not be
rediscovered.

Tape: **1,261,716 bars / 927 days with a hole → 1,299,540 bars / 954 days
unbroken**, 2023-01-02 → 2026-09-02.

## 2. Re-baselined empire

948 rail-pass days (six days carry no signals).

| | trades | /day | EV/trade | total R | R/day | maxDD | Sharpe | green |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| flat (frozen spec) | 75,481 | 79.6 | +0.1361 | +10,273 | +10.84 | −18.1 | 1.153 | 89% |
| **armed 1R** | 61,194 | 64.6 | **+0.1775** | **+10,863** | +11.46 | **−14.0** | 1.208 | 91% |

Before → after:

| | flat before | flat after | armed before | armed after |
|---|---:|---:|---:|---:|
| trades | 71,961 | 75,481 | 58,401 | 61,194 |
| EV/trade | +0.1375 | +0.1361 | +0.1792 | +0.1775 |
| total R | +9,896 | +10,273 | +10,467 | +10,863 |
| R/day | +10.74 | +10.84 | +11.36 | +11.46 |
| maxDD | −18.1 | **−18.1** | −14.0 | **−14.0** |

**Nothing structural moved.** Expectancy drifted ~1% lower on both books
(the added days are slightly below average), R/day ticked up, and the max
drawdown is **identical** on both — the deepest day was already inside
the retained data, so the new month contributed nothing to the tail.

By year, flat: 2023 +2,179 / 2024 +2,802 / 2025 +2,893 / 2026 **+2,399**
(was +2,022 — the whole increase is the completed July–August).
Armed: +2,280 / +2,918 / +3,108 / +2,557.

45/45 months positive on both books. The worst month improves from +8.1R
to **+18.3R** flat (+20.1R armed) — because the old "worst month" was a
*truncated* month: July 2026 stopped at the 15th and August began on the
23rd. Completing them removes an artefact rather than adding performance.

**Arming's advantage is unchanged by the re-baseline:** +0.1775 vs
+0.1361 per trade (+30%), drawdown −14.0 vs −18.1 (−23%), Sharpe 1.208 vs
1.153. Every conclusion from the arming work stands on the fuller tape.

## 3. What this invalidates

Numbers quoted from the 927-day tape in earlier documents are superseded
for the *empire* figures. Specifically:
- §32/§34 style headlines (71,961 trades, +9,896R, +10.74R/day) → use the
  table above.
- The funded-account sim (`docs/FINDINGS-funded-sim-armed.md`) was run on
  the 921-day export. Its **conclusions** are unaffected — the size sweep
  turns on the shape of the daily distribution, which did not change —
  but the export would need regenerating for exact figures.

**Not affected:** the 2020–22 holdout verdict, which was scored against
the frozen 927-day baseline exactly as pre-registered. That was the
reason for doing it in this order.
