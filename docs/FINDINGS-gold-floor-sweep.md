# FINDINGS — gold stop-floor sweep on the current stack (2026-09-03, post-hoc)

S22 swept floors 1.0–3.0 on the value-area book and ruled 1.5 (flat ridge at
1.0–1.5, ≥2pt bleeds everywhere, a 2025 pick of 1.0 verified *worse* on 2026).
His ask: re-check on what ships now — the 8-level book, with arming, on
dial-on days. Depth 0.9 and cap 9.0 held fixed. **Post-hoc on read data;
the point is whether the ridge is flat or peaked, not to pick a cell.**

## Flat

| floor | trades | WR | EV | net R | R/day | maxDD | Sharpe | floored | 2025 EV | 2026 EV |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 7,530 | 62.5% | +0.069 | +522 | +1.86 | −26.6 | 0.376 | 18% | **+0.106** | +0.047 |
| 1.25 | 7,386 | 63.5% | +0.079 | +582 | +2.07 | −17.7 | 0.432 | 23% | +0.097 | +0.068 |
| **1.5** | 7,208 | 64.0% | **+0.082** | **+590** | **+2.10** | **−15.0** | **0.447** | 31% | +0.094 | **+0.075** |
| 2.0 | 6,805 | 64.4% | +0.067 | +458 | +1.63 | −22.0 | 0.352 | 43% | +0.080 | +0.060 |
| 2.5 | 6,488 | 65.5% | +0.058 | +378 | +1.35 | −37.1 | 0.295 | 54% | +0.074 | +0.049 |

## Armed

| floor | trades | WR | EV | net R | R/day | maxDD | Sharpe | floored | 2025 EV | 2026 EV |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 6,576 | 61.7% | +0.075 | +493 | +1.76 | −39.4 | 0.361 | 21% | +0.108 | +0.054 |
| 1.25 | 6,323 | 63.1% | +0.095 | +599 | +2.15 | −22.7 | 0.462 | 27% | +0.110 | +0.086 |
| **1.5** | 6,083 | 63.8% | +0.103 | **+628** | **+2.25** | −23.1 | **0.476** | 36% | +0.109 | **+0.100** |
| 2.0 | 5,463 | 64.4% | +0.096 | +525 | +1.89 | −25.9 | 0.420 | 48% | +0.112 | +0.087 |
| 2.5 | 4,879 | 66.7% | **+0.107** | +519 | +1.88 | **−16.3** | 0.437 | 58% | **+0.121** | +0.098 |

## Reading

- **1.5 is the peak, not a point on a flat ridge**, on the 8-level book. Flat:
  best on every column. Armed: best net R, R/day and Sharpe.
- **The 2025 → 2026 pattern repeats S22 exactly.** 2025 prefers a tighter
  floor (1.0 flat, 2.5 armed by EV); 2026 prefers 1.5. A pick made on 2025
  would have verified worse on 2026 again. That is the signature of noise
  around a stable optimum, not of a better cell.
- **Why 1.0 fails:** the tick (0.10) and the 0.15pt cost are 25% of a 1.0pt
  stop. The honest-fill tax eats the edge — the same arithmetic that killed
  6E.
- **Why 2.5 looks tempting armed and is not:** +0.107 EV and −16.3 drawdown,
  but 58% of trades sit *on* the floor — it has stopped being a structural
  stop and become a fixed 2.5pt stop — and it gives up 17% of R/day and 20%
  of the trades. A risk-preference alternative at best, and a post-hoc one.

**Ruling unchanged: floor 1.5.** Third time the same cell has won on gold —
ratio-derived, native-swept on the VA book, and now on the shipped stack.

Scripts: `scripts/run_gold_floor.sh`, `scripts/gold_floor_sweep.py`.
