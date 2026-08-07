---
date: 2026-08-06
status: CORRECTION — a per-day/full-dataset indexing bug voided most FVT results. Rerun.
supersedes: parts of research/findings/FVT-TOMBSTONE.md
tags: [fvt, bug, correction, nq, friction]
---

# FVT correction — the displacement flag was read from the wrong array

## The bug

`scripts/fvt_model.run()` computed the displacement flags on the **full dataset** and then
indexed them with a **per-day** counter:

```python
disp_up = bull & (...)              # length 1,251,240 (whole dataset)
for day, g in b.groupby("day"):
    g = g.reset_index(drop=True)
    for i in idx:                   # i is 0..1379, per day
        ... disp_up[i] ...          # reads bar i of 2023-01-02, every day
```

`hi`, `lo`, `cl`, `hm`, `atr`, `sw_hi`, `sw_lo` were all correctly taken from `g`. **Only the
displacement test was wrong**, so every session in every year was screened against
2023-01-02's candle shapes. Agreement with the correct flags: **40%**.

A second, smaller inconsistency: `run()` used `== max` for the fractal, allowing ties with the
right-hand bar, where `fvt_optimise.entries()` required strict inequality. That alone accounted
for 13 setups. Both are fixed and the two builds now agree **exactly** (4,123 setups, gross
+1.1496).

## What was void

Everything routed through `run()`: the original five-session table, the RR sweep, the fidelity
grid, the flow-inversion layer, the continuation-vs-reversion comparison, and the headline
claim that **gross expectancy was zero**.

## What was never affected

`scripts/fvt_optimise.py` (`entries`/`evaluate`), `scripts/fvt_oos.py` and
`scripts/fvt_quality.py` always indexed per-day correctly. The fit-vs-2023 holdout test and
the 800-cell optimisation therefore stand.

## The corrected result

Base config — JJ's rules unchanged, RR 2.5, stop ×1.0, 15-minute continuation window, first
attempt per window, five sessions:

| friction | net/trade | 2023 | 2024 | 2025 | 2026 |
|---:|---:|---:|---:|---:|---:|
| 0.25 pt | +0.90 | +0.36 | +0.15 | +1.83 | +1.56 |
| **0.50 pt** (realistic NQ) | **+0.65** | +0.11 | −0.10 | +1.58 | +1.31 |
| 1.00 pt | +0.15 | −0.39 | −0.60 | +1.08 | +0.81 |
| 2.00 pt (previously charged) | −0.85 | −1.39 | −1.60 | +0.08 | −0.19 |

**Gross is +1.150 and positive in all four years** (+0.61 / +0.40 / +2.08 / +1.81).
3.74 trades/day, 45.6% green days, +2,678 pts over 1,103 sessions.

The 2.0 pt friction was inherited from the canon work and is ~4× realistic cost on NQ
(commission ≈ 1 tick, slippage ≈ 1 tick, so ≈ 0.5 pt round trip). It was not the cause of the
bug but it compounded it.

### Per session, net at 0.5 pt

| session | /day | net | 2023 | 2024 | 2025 | 2026 | 4/4 |
|---|---:|---:|---:|---:|---:|---:|:---:|
| **NY PM** | 0.73 | **+1.27** | +2.01 | +0.34 | +0.94 | +2.29 | **yes** |
| 8PM | 0.81 | +1.08 | −1.37 | +0.44 | +0.60 | +7.81 | |
| London | 0.80 | +0.75 | +2.42 | +0.20 | −0.59 | +1.16 | |
| NY AM | 0.71 | +0.17 | −3.29 | +1.05 | +5.04 | −4.49 | |
| 6PM | 0.70 | −0.13 | +0.52 | −2.69 | +2.27 | −1.09 | |

## The reconciliation

Friction is a constant subtraction, so it cannot change a **rank** correlation. The tombstone's
finding that optimised configs fail to transfer to 2023 (−0.413 NY AM, −0.394 NY PM) therefore
still holds. Combined with the corrected base result, the story is coherent for the first time:

**JJ's base rules carry a small, real, four-year-consistent edge, and optimising them destroys
it.** That explains his payouts, my failed 800-cell grid, and the negative rank correlation
simultaneously. His "don't overthink it, no trade management" framing is load-bearing.

## Caveats

- +0.65 pt/trade at 3.74/day is ~2.4 pts/day per contract. Real but thin.
- The 0.5 pt friction assumption is load-bearing: at 1.0 pt it falls to +0.15.
- NY PM being 4/4 is a 1-in-5 session pick and carries selection.
- 2023 and 2024 are essentially break-even; the edge is concentrated in 2025-2026.

## Process note

Two independent implementations of the same model disagreed (4,123 vs 2,756 setups; +1.150 vs
+0.006 gross) and that discrepancy is what surfaced the bug. **Building the second
implementation was not wasted effort — it was the only reason this was caught.** Cross-checking
two builds of the same rules should be standard before any result is reported.
