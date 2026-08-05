# NYA-LVL-01 stage 3b — winner/loser discriminant

Authorised by `docs/PREREG-level-interaction-stage3.md`. Ten declared variables, list closed. Each evaluated
ALONE at a frozen split; continuous cuts set on the DISCOVER era (2025) and
applied to both. Thin = fewer than 30 a side in an era, and thin means no
verdict. **Survival requires positive lift in BOTH eras AND a positive R at
strict cost.**

4,759 real events, 4,059 placebo events.

## S20/T30

Unconditioned baseline: n=4,759 WR 44% PF 1.07 R +0.041

**5 of 34 cells survive** (both eras positive lift, positive at strict cost).

| variable | value | n | WR | PF | R base | R strict | lift 25 | lift 26 | placebo | class |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `t5` | green | 2,337 | 80% | 5.45 | +0.933 | +0.883 | +0.864 | +0.926 | +0.845 | CONTEXT |
| `t15` | green | 2,332 | 74% | 3.99 | +0.799 | +0.749 | +0.781 | +0.729 | +0.770 | CONTEXT |
| `level_type` | PM_50 | 1,006 | 46% | 1.16 | +0.093 | +0.043 | +0.044 | +0.058 | +0.040 | CONTEXT |
| `level_type` | PD_50 | 721 | 45% | 1.12 | +0.071 | +0.021 | +0.014 | +0.067 | -0.021 | LEVEL-BORNE |
| `age` | mid | 922 | 45% | 1.15 | +0.085 | +0.035 | +0.001 | +0.093 | -0.005 | LEVEL-BORNE |

**Thin cells (no verdict):** 0 of 34.

## S10/TRAIL

Unconditioned baseline: n=4,759 WR 43% PF 3.09 R +1.222

**15 of 34 cells survive** (both eras positive lift, positive at strict cost).

| variable | value | n | WR | PF | R base | R strict | lift 25 | lift 26 | placebo | class |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `t5` | green | 2,337 | 77% | 16.67 | +3.271 | +3.171 | +1.593 | +2.598 | +1.590 | CONTEXT |
| `t15` | green | 2,332 | 69% | 10.60 | +2.891 | +2.791 | +1.384 | +2.016 | +1.346 | CONTEXT |
| `hour` | 9:00 | 570 | 41% | 4.49 | +2.208 | +2.108 | +0.453 | +1.558 | +0.663 | CONTEXT |
| `atr15` | high | 2,527 | 43% | 3.80 | +1.697 | +1.597 | +0.405 | +0.180 | +0.383 | CONTEXT |
| `level_type` | PD_LOW | 506 | 43% | 3.66 | +1.565 | +1.465 | +0.292 | +0.445 | -0.145 | LEVEL-BORNE |
| `tap` | 1st | 1,023 | 43% | 3.90 | +1.771 | +1.671 | +0.285 | +0.804 | +0.519 | CONTEXT |
| `tap` | 2nd | 817 | 44% | 3.87 | +1.657 | +1.557 | +0.283 | +0.548 | +0.156 | CONTEXT |
| `level_type` | PM_LOW | 873 | 44% | 3.58 | +1.483 | +1.383 | +0.222 | +0.336 | -0.004 | LEVEL-BORNE |
| `age` | low | 1,048 | 41% | 3.84 | +1.768 | +1.668 | +0.173 | +0.935 | +0.410 | CONTEXT |
| `dist_atr` | mid | 1,613 | 41% | 3.48 | +1.517 | +1.417 | +0.159 | +0.432 | +0.214 | CONTEXT |
| `hour` | 10:00 | 1,274 | 42% | 3.67 | +1.610 | +1.510 | +0.092 | +0.650 | +0.037 | LEVEL-BORNE |
| `gap_atr` | mid | 1,406 | 44% | 3.12 | +1.209 | +1.109 | +0.055 | +0.090 | +0.129 | CONTEXT |
| `gap_atr` | low | 1,727 | 43% | 3.34 | +1.383 | +1.283 | +0.034 | +0.200 | -0.069 | LEVEL-BORNE |
| `side` | long | 2,421 | 45% | 3.29 | +1.301 | +1.201 | +0.019 | +0.160 | +0.178 | CONTEXT |

**Thin cells (no verdict):** 0 of 34.
