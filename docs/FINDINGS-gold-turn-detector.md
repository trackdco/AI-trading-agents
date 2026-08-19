# FINDINGS — the Reddit-thread second-derivative turn detector: retired on train

Model B from `docs/RESEARCH-reddit-gold-ea-thread.md`, codified per
`docs/DECLARATIONS-gold-turn-detector.md` (D0–D5), swept on GC train (2023-01-02 →
2025-08-31, 829 days) via `Workflow('gold-turn-detector-sweep')`.

**No cell of 32 clears the +0.10R promotion gate. The rule is retired.** The sealed
2025-09-01 → 2026-03-01 holdout was not read and stays sealed.

## Baseline

EMA span 10 (5m bars, ≈50 min), hold 2 bars, cooldown 12 bars (1h), target 1.5R, risk cap
2.0×ATR, no volume filter, max 6 trades/day, $3 commission + slippage.

| | |
|---|---|
| n | 4,922 |
| win % | 38.9 |
| **EV @ 1 tick** | **−0.100R** [−0.130, −0.072] |
| **EV @ 2 tick** | **−0.184R** [−0.212, −0.155] |
| PF | 0.93 @1t / 0.83 @2t |
| 2023 / 2024 / 2025 | −0.152 / −0.076 / −0.058 (all negative, every year) |

## A. EMA span — no rescue, no monotone order

| span | avg R @1t | @2t | PF@1t |
|---|---|---|---|
| 5 | −0.118 | −0.206 | 0.91 |
| **10 (baseline)** | **−0.100** | −0.184 | 0.93 |
| 20 | −0.113 | −0.193 | 0.88 |
| 40 | −0.108 | −0.187 | 0.87 |

Every cell's 95% CI is entirely below zero. Baseline (10) is the *least-bad* cell but the
gap to its neighbours is shallow — not a real optimum, and trade count barely moves
(4,903–4,928) across the whole axis, since the 12-bar cooldown and 6-trade daily cap set
frequency far more than the smoother does. The "shorter = noisier" prediction doesn't get a
clean test: there's no frequency/quality trade to observe because frequency doesn't move.

## B. Volume confirmation — a spike, and mostly cost-denominator artifact

| threshold | n | avg R @1t | @2t | PF@1t |
|---|---|---|---|---|
| off | 4,922 | −0.100 | −0.184 | 0.93 |
| **1.2×** | 4,321 | **−0.066** | −0.133 | 0.97 |
| 1.5× | 3,792 | −0.081 | −0.148 | 0.94 |
| 2.0× | 2,523 | −0.111 | −0.182 | 0.90 |

Non-monotone — a hump at 1.2×, then worse at 1.5× and worse again at 2.0×, matching the
ORB participation-filter shape from the earlier programme rather than a real dose-response.

**Adversarially verified, does not survive.** Reproduced exactly (n=4,321, avg R −0.0655,
PF 0.970). Pre-cost EV at 1.2× is **+0.021R**, almost identical to baseline's pre-cost
**+0.018R** — the apparent relative improvement is a wider stop (median 3.40 pts vs 2.50)
diluting the fixed per-trade cost in the R denominator, the same artifact the ORB OR-window
ridge was checked against. And it was never positive to begin with: −0.066R is "less bad
than a bad baseline," not an edge.

## C. Target R — a near-null lever

| target | avg R @1t | win % | @2t |
|---|---|---|---|
| 1.0R | −0.099 | 48.2 | −0.189 |
| **1.5R (baseline)** | **−0.100** | 38.9 | −0.184 |
| 2.0R | −0.098 | 33.2 | −0.192 |
| 2.5R | −0.094 | 29.3 | −0.179 |

All four values sit in a tight −0.094R to −0.100R band at 1 tick. Stretching the target
trades win rate against payoff exactly as arithmetic predicts (48% → 29%) and moves EV
almost nowhere — the stop, not the target, is where this rule loses.

## D. Cooldown — inert, because the daily cap already binds

| cooldown | n | avg R @1t | @2t |
|---|---|---|---|
| 0 bars | 4,969 | −0.111 | −0.203 |
| 6 bars | 4,959 | −0.115 | −0.206 |
| **12 bars (baseline)** | 4,922 | **−0.100** | −0.184 |
| 24 bars | 4,698 | −0.116 | −0.201 |

94–100% of train days hit the 6-trade daily cap at every cooldown setting, so lengthening
cooldown mostly discards same-direction re-fires the cap would have truncated anyway. Not a
real lever on this signal as configured.

## Direction-flip check

The one verified cell, mirrored (long↔short, stop re-derived on the mirrored side): avg R
**−0.384R** against the original's −0.066R — far worse, not similar. This rules out a
trivial sign-convention bug: a coin-flip process would look about the same either way, and
this doesn't. D1's direction mapping (concave-down→up = long) is doing something directional;
it's simply on the losing side, not an interchangeable label.

## Not a regime artifact

2023 is the worst year in **every one of the 32 cells** across all four axes; 2024 and 2025
are smaller losses but uniformly negative too. This is a broad, multi-year failure of the
codified rule, not one bad stretch.

## What this does and does not establish

**Does.** Model B's rule, codified per D1 (EMA-smoothed 5m closes, second-derivative
zero-crossing held two bars, next-bar-open fill, local-extreme stop), fails on GC train at
every parameter combination tested across four independent axes, with a real, deep,
multi-year, cost-robust negative expectancy. The failure is not explained by target choice,
cooldown, or volume filtering, and is not a direction-convention error.

**Does not.** Two things were declared out of scope in D1 and remain untested, not refuted:
an ATR-multiple stop (only the local-extreme stop was built and tested), and any smoother
other than EMA (Savitzky-Golay, Kalman — the source names neither, and a materially
different smoother is a different model, not a parameter of this one). Absent is not
refuted, per this repo's own evidence-tier convention.

## Retired

Per the task's instruction: *"if nothing clears +0.10R on train, say so plainly and we
stop."* Nothing did — best cell (volume 1.2×) reaches −0.066R against a +0.10R
requirement, 166% of the gate on the wrong side. Sealed holdout untouched.
