# FINDINGS — displacement direction (null) and the arming threshold ridge (2026-09-03, post-hoc)

## 1. Displacement direction: NULL

Displacement is always in the trade's own direction by construction. The
untested part was its direction relative to where the session already was —
continuation (long above the session open) versus fade (long below it) — and
the same split against the prior close (gap side). Both causal. Armed empire,
both eras, split-half.

| | 2020–22 IS | OOS | 2023–26 IS | OOS |
|---|---:|---:|---:|---:|
| with session drift | +0.175 | +0.167 | +0.184 | +0.167 |
| against session drift | +0.174 | +0.154 | +0.194 | +0.172 |
| **spread** | −0.001 | −0.012 | **+0.011** | **+0.005** |
| with gap side | +0.177 | +0.162 | +0.187 | +0.165 |
| against gap side | +0.172 | +0.159 | +0.192 | +0.174 |
| **spread** | −0.005 | −0.003 | **+0.005** | **+0.008** |

Spreads ≤ 0.012R, win rates 65.3–66.0% in every cell, and **the sign flips
between eras**. The grammar does not care whether it is fading or following.
Fourth direction-type feature to die (trend filter, session progress alone,
wrong-way bands, this).

## 2. Arming threshold sweep — full empire, 2023–26

All three books railed. Scored as arming was adopted: drawdown-matched R/day
vs flat, both halves at 2024-10-21.

| arm × risk | trades/day | EV | net R | R/day | maxDD | Sharpe | dd-matched IS | OOS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| flat | 79.6 | +0.136 | +10,273 | +10.84 | −18.1 | 1.153 | — | — |
| 0.5 | 75.5 | +0.145 | +10,371 | +10.94 | −17.4 | 1.169 | +6.1% | +4.2% |
| 0.75 | 71.3 | +0.161 | +10,867 | +11.46 | −14.9 | 1.199 | +26.4% | +29.3% |
| **1.0 (adopted)** | 64.6 | +0.178 | **+10,863** | **+11.46** | −14.0 | **1.208** | +33.3% | +38.2% |
| 1.25 | 56.8 | +0.189 | +10,170 | +10.73 | **−12.3** | 1.189 | **+40.4%** | **+48.6%** |
| 1.5 | 47.4 | +0.203 | +9,112 | +9.61 | −11.9 | 1.172 | +38.3% | +32.0% |
| 2.0 | 37.6 | +0.201 | +7,169 | +7.56 | −15.2 | 1.059 | −17.4% | −16.8% |

**Reading.**
- The ridge rises steeply from 0.5 to 1.0, is **flat-topped from 1.0 to
  1.5**, and falls off a cliff at 2.0 (too few trades; the drawdown gets
  *worse* again at −15.2).
- 1.25 edges 1.0 on the drawdown-matched metric (+40/+49 vs +33/+38) — but
  loses on Sharpe (1.189 vs 1.208), raw R/day (−6%) and net R (−693R). The
  dd-matched gain comes entirely from max drawdown moving −14.0 → −12.3, and
  the empire's max drawdown is a **single day**. A parameter should not be
  moved on one day's worth of difference; the standing rule from the first
  arming sweep ("single-book maxDD is too noisy to sweep on") applies.
- 1.0 was chosen **before** results as the audit's own tier line. It sits at
  the Sharpe peak and the raw-R peak. It stays.
- Per-trade EV keeps rising to 1.5 (+0.203) — arming is doing what it says
  at every threshold — but trades/day falls from 80 to 47. For a book whose
  business is count × small edge, 1.0 is where the product is largest.

**Ruling unchanged: arm at 1.0.** 1.25 is a legitimate risk-preference
alternative (−12% drawdown for −6% R/day), not an improvement.

Scripts: `scripts/disp_direction.py`, `scripts/run_arm_sweep.sh`,
`scripts/arm_sweep.py`.
