# LDN-PO3-01 / LDN-OBK-01 — L3 flow pass on RAW triggers

Authorised by `docs/PREREG-london-obk-L3-flow-and-autopsy.md`. **Unconditioned default arms only** — no cuts, no
filters. Predictions were declared before the join and are printed with each
feature. 2023/24 tape and the sealed depth are not read.

Flow span coverage: 1787 of 2346 L1 trades carry tape state
(270 days). Discover era is **2025 H2 only** — the tape
starts 2025-06-01, so a '2025' row here is half a year, not a year.

### F1

_Book features present on 277 of 277 F1 trades (depth window is 07:00-08:59 UTC; macro-hour reads are seasonally incomplete and barred as gates)._

#### F1 · `delta_entry` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 51 | 33% | -68 | 0.81 | -0.216 |
| low | 2025 | strict | 51 | 33% | -119 | 0.70 | -0.333 |
| mid | 2025 | base | 49 | 24% | -148 | 0.60 | -0.418 |
| mid | 2025 | strict | 49 | 22% | -197 | 0.52 | -0.560 |
| high | 2025 | base | 52 | 35% | -187 | 0.66 | -0.224 |
| high | 2025 | strict | 52 | 33% | -239 | 0.60 | -0.312 |
| low | 2026 | base | 42 | 43% | +275 | 1.65 | +0.484 |
| low | 2026 | strict | 42 | 43% | +233 | 1.52 | +0.412 |
| mid | 2026 | base | 40 | 22% | -143 | 0.70 | -0.345 |
| mid | 2026 | strict | 40 | 22% | -183 | 0.64 | -0.429 |
| high | 2026 | base | 41 | 34% | -93 | 0.85 | -0.099 |
| high | 2026 | strict | 41 | 34% | -134 | 0.79 | -0.158 |

#### F1 · `delta_pre5` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 51 | 35% | -65 | 0.85 | -0.344 |
| low | 2025 | strict | 51 | 35% | -116 | 0.75 | -0.449 |
| mid | 2025 | base | 50 | 32% | -89 | 0.75 | -0.255 |
| mid | 2025 | strict | 50 | 28% | -139 | 0.64 | -0.393 |
| high | 2025 | base | 51 | 25% | -250 | 0.51 | -0.253 |
| high | 2025 | strict | 51 | 25% | -300 | 0.45 | -0.355 |
| low | 2026 | base | 42 | 29% | -10 | 0.98 | -0.126 |
| low | 2026 | strict | 42 | 29% | -52 | 0.91 | -0.195 |
| mid | 2026 | base | 41 | 34% | +42 | 1.09 | +0.061 |
| mid | 2026 | strict | 41 | 34% | +0 | 1.00 | -0.016 |
| high | 2026 | base | 42 | 36% | -23 | 0.96 | +0.073 |
| high | 2026 | strict | 42 | 36% | -65 | 0.88 | +0.004 |

#### F1 · `delta_sweep` — _HIGH should help the fade (big trapped cohort) — the mechanism variable_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 51 | 33% | -178 | 0.65 | -0.341 |
| low | 2025 | strict | 51 | 33% | -229 | 0.57 | -0.432 |
| mid | 2025 | base | 50 | 30% | -43 | 0.86 | -0.238 |
| mid | 2025 | strict | 50 | 26% | -93 | 0.73 | -0.394 |
| high | 2025 | base | 51 | 29% | -183 | 0.62 | -0.272 |
| high | 2025 | strict | 51 | 29% | -234 | 0.55 | -0.370 |
| low | 2026 | base | 43 | 37% | +251 | 1.48 | +0.218 |
| low | 2026 | strict | 43 | 37% | +208 | 1.38 | +0.157 |
| mid | 2026 | base | 40 | 25% | -120 | 0.71 | -0.383 |
| mid | 2026 | strict | 40 | 25% | -160 | 0.64 | -0.479 |
| high | 2026 | base | 42 | 36% | -123 | 0.79 | +0.148 |
| high | 2026 | strict | 42 | 36% | -165 | 0.73 | +0.089 |

#### F1 · `absorb_extreme` — _HIGH should help the fade (size absorbed at the extreme)_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 51 | 24% | -89 | 0.75 | -0.431 |
| low | 2025 | strict | 51 | 24% | -140 | 0.65 | -0.576 |
| mid | 2025 | base | 50 | 26% | -277 | 0.39 | -0.377 |
| mid | 2025 | strict | 50 | 24% | -327 | 0.34 | -0.496 |
| high | 2025 | base | 51 | 43% | -37 | 0.92 | -0.047 |
| high | 2025 | strict | 51 | 41% | -88 | 0.82 | -0.126 |
| low | 2026 | base | 41 | 37% | +222 | 1.52 | +0.440 |
| low | 2026 | strict | 41 | 37% | +181 | 1.40 | +0.360 |
| mid | 2026 | base | 41 | 32% | +11 | 1.02 | -0.199 |
| mid | 2026 | strict | 41 | 32% | -30 | 0.94 | -0.270 |
| high | 2026 | base | 41 | 32% | -192 | 0.67 | -0.182 |
| high | 2026 | strict | 41 | 32% | -234 | 0.62 | -0.245 |

#### F1 · `wall_ratio_opp` — _HIGH should HURT (a wall in the path to target)_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 60 | 18% | -455 | 0.24 | -0.678 |
| low | 2025 | strict | 60 | 17% | -515 | 0.21 | -0.811 |
| mid | 2025 | base | 35 | 37% | -4 | 0.99 | -0.074 |
| mid | 2025 | strict | 35 | 37% | -39 | 0.87 | -0.169 |
| high | 2025 | base | 57 | 40% | +56 | 1.13 | +0.002 |
| high | 2025 | strict | 57 | 39% | -1 | 1.00 | -0.106 |
| low | 2026 | base | 50 | 34% | +187 | 1.34 | +0.055 |
| low | 2026 | strict | 50 | 34% | +137 | 1.24 | -0.025 |
| high | 2026 | base | 61 | 30% | -198 | 0.77 | -0.069 |
| high | 2026 | strict | 61 | 30% | -260 | 0.71 | -0.134 |

#### F1 · `book_imb` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 52 | 33% | -13 | 0.97 | -0.115 |
| low | 2025 | strict | 52 | 33% | -65 | 0.85 | -0.244 |
| mid | 2025 | base | 48 | 29% | -180 | 0.61 | -0.318 |
| mid | 2025 | strict | 48 | 29% | -228 | 0.54 | -0.424 |
| high | 2025 | base | 52 | 31% | -210 | 0.52 | -0.422 |
| high | 2025 | strict | 52 | 27% | -262 | 0.45 | -0.531 |
| low | 2026 | base | 43 | 35% | +157 | 1.33 | -0.004 |
| low | 2026 | strict | 43 | 35% | +114 | 1.23 | -0.076 |
| mid | 2026 | base | 39 | 31% | -70 | 0.86 | +0.017 |
| mid | 2026 | strict | 39 | 31% | -109 | 0.79 | -0.051 |
| high | 2026 | base | 43 | 33% | -79 | 0.86 | -0.006 |
| high | 2026 | strict | 43 | 33% | -122 | 0.79 | -0.079 |

### A/S1

_Book features present on 300 of 300 A/S1 trades (depth window is 07:00-08:59 UTC; macro-hour reads are seasonally incomplete and barred as gates)._

#### A/S1 · `delta_entry` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 41% | -22 | 0.94 | -0.009 |
| low | 2025 | strict | 54 | 41% | -76 | 0.81 | -0.123 |
| mid | 2025 | base | 54 | 26% | -109 | 0.74 | -0.356 |
| mid | 2025 | strict | 54 | 26% | -163 | 0.65 | -0.479 |
| high | 2025 | base | 54 | 26% | -308 | 0.38 | -0.406 |
| high | 2025 | strict | 54 | 26% | -362 | 0.33 | -0.532 |
| low | 2026 | base | 45 | 31% | -71 | 0.87 | -0.198 |
| low | 2026 | strict | 45 | 31% | -116 | 0.79 | -0.269 |
| mid | 2026 | base | 45 | 33% | -72 | 0.85 | -0.113 |
| mid | 2026 | strict | 45 | 33% | -116 | 0.76 | -0.199 |
| high | 2026 | base | 45 | 49% | +243 | 1.58 | +0.379 |
| high | 2026 | strict | 45 | 49% | +198 | 1.45 | +0.302 |

#### A/S1 · `delta_pre5` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 39% | -78 | 0.83 | -0.024 |
| low | 2025 | strict | 54 | 39% | -132 | 0.73 | -0.127 |
| mid | 2025 | base | 54 | 20% | -260 | 0.40 | -0.528 |
| mid | 2025 | strict | 54 | 20% | -314 | 0.34 | -0.667 |
| high | 2025 | base | 54 | 33% | -100 | 0.75 | -0.219 |
| high | 2025 | strict | 54 | 33% | -154 | 0.65 | -0.339 |
| low | 2026 | base | 46 | 37% | +65 | 1.13 | -0.029 |
| low | 2026 | strict | 46 | 37% | +19 | 1.04 | -0.103 |
| mid | 2026 | base | 46 | 30% | -194 | 0.66 | -0.186 |
| mid | 2026 | strict | 46 | 30% | -240 | 0.60 | -0.264 |
| high | 2026 | base | 46 | 46% | +218 | 1.56 | +0.255 |
| high | 2026 | strict | 46 | 46% | +172 | 1.42 | +0.174 |

#### A/S1 · `delta_sweep` — _HIGH should help the fade (big trapped cohort) — the mechanism variable_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 35% | -109 | 0.77 | -0.112 |
| low | 2025 | strict | 54 | 35% | -163 | 0.68 | -0.217 |
| mid | 2025 | base | 53 | 28% | -157 | 0.57 | -0.315 |
| mid | 2025 | strict | 53 | 28% | -210 | 0.48 | -0.454 |
| high | 2025 | base | 55 | 29% | -173 | 0.61 | -0.344 |
| high | 2025 | strict | 55 | 29% | -228 | 0.53 | -0.463 |
| low | 2026 | base | 46 | 39% | +70 | 1.15 | +0.033 |
| low | 2026 | strict | 46 | 39% | +24 | 1.05 | -0.044 |
| mid | 2026 | base | 46 | 26% | -197 | 0.63 | -0.321 |
| mid | 2026 | strict | 46 | 26% | -243 | 0.57 | -0.403 |
| high | 2026 | base | 46 | 48% | +215 | 1.49 | +0.328 |
| high | 2026 | strict | 46 | 48% | +169 | 1.37 | +0.255 |

#### A/S1 · `absorb_extreme` — _HIGH should help the fade (size absorbed at the extreme)_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 37% | -33 | 0.89 | -0.068 |
| low | 2025 | strict | 54 | 37% | -87 | 0.75 | -0.223 |
| mid | 2025 | base | 54 | 20% | -347 | 0.31 | -0.553 |
| mid | 2025 | strict | 54 | 20% | -401 | 0.26 | -0.671 |
| high | 2025 | base | 54 | 35% | -58 | 0.88 | -0.150 |
| high | 2025 | strict | 54 | 35% | -112 | 0.78 | -0.239 |
| low | 2026 | base | 45 | 31% | -112 | 0.77 | -0.187 |
| low | 2026 | strict | 45 | 31% | -156 | 0.70 | -0.268 |
| mid | 2026 | base | 45 | 40% | +99 | 1.25 | +0.073 |
| mid | 2026 | strict | 45 | 40% | +54 | 1.13 | -0.015 |
| high | 2026 | base | 45 | 42% | +113 | 1.21 | +0.181 |
| high | 2026 | strict | 45 | 42% | +68 | 1.12 | +0.118 |

#### A/S1 · `wall_ratio_opp` — _HIGH should HURT (a wall in the path to target)_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 35% | -104 | 0.75 | -0.144 |
| low | 2025 | strict | 54 | 35% | -158 | 0.65 | -0.261 |
| mid | 2025 | base | 50 | 32% | -93 | 0.75 | -0.214 |
| mid | 2025 | strict | 50 | 32% | -143 | 0.65 | -0.336 |
| high | 2025 | base | 58 | 26% | -242 | 0.52 | -0.400 |
| high | 2025 | strict | 58 | 26% | -300 | 0.45 | -0.523 |
| low | 2026 | base | 46 | 33% | -62 | 0.89 | -0.121 |
| low | 2026 | strict | 46 | 33% | -108 | 0.81 | -0.193 |
| mid | 2026 | base | 39 | 33% | -187 | 0.60 | -0.097 |
| mid | 2026 | strict | 39 | 33% | -226 | 0.55 | -0.181 |
| high | 2026 | base | 53 | 45% | +337 | 1.78 | +0.211 |
| high | 2026 | strict | 53 | 45% | +284 | 1.61 | +0.134 |

#### A/S1 · `book_imb` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 30% | -105 | 0.73 | -0.269 |
| low | 2025 | strict | 54 | 30% | -159 | 0.62 | -0.403 |
| mid | 2025 | base | 54 | 30% | -265 | 0.47 | -0.301 |
| mid | 2025 | strict | 54 | 30% | -319 | 0.41 | -0.413 |
| high | 2025 | base | 54 | 33% | -69 | 0.83 | -0.201 |
| high | 2025 | strict | 54 | 33% | -123 | 0.73 | -0.317 |
| low | 2026 | base | 46 | 35% | -78 | 0.84 | -0.077 |
| low | 2026 | strict | 46 | 35% | -124 | 0.76 | -0.159 |
| mid | 2026 | base | 46 | 41% | +36 | 1.08 | +0.102 |
| mid | 2026 | strict | 46 | 41% | -10 | 0.98 | +0.023 |
| high | 2026 | base | 46 | 37% | +131 | 1.27 | +0.015 |
| high | 2026 | strict | 46 | 37% | +85 | 1.17 | -0.056 |

## Scorecard — declared direction vs what happened

`high>low` = the high tercile beat the low tercile at base cost. The
prediction column was written before the join. A feature counts only if it
moves the predicted way in **both** eras — one era is a coin flip.

| arm | feature | predicted | 2025 high>low | 2026 high>low | consistent |
|---|---|---|---|---|---|
| F1 | `delta_entry` | control | no | no | consistent |
| F1 | `delta_pre5` | control | yes | yes | consistent |
| F1 | `delta_sweep` | high helps | yes | no | no — flips between eras |
| F1 | `absorb_extreme` | high helps | yes | no | no — flips between eras |
| F1 | `wall_ratio_opp` | high hurts | yes | no | no — flips between eras |
| F1 | `book_imb` | control | no | no | consistent |
| A/S1 | `delta_entry` | control | no | yes | no — flips between eras |
| A/S1 | `delta_pre5` | control | no | yes | no — flips between eras |
| A/S1 | `delta_sweep` | high helps | no | yes | no — flips between eras |
| A/S1 | `absorb_extreme` | high helps | no | yes | no — flips between eras |
| A/S1 | `wall_ratio_opp` | high hurts | no | yes | no — flips between eras |
| A/S1 | `book_imb` | control | yes | yes | consistent |

### The mechanism variable failed, and that is the finding

`delta_sweep` was named in the prereg — before the join — as the one
feature that had to work: *"the fade thesis is that the break traps
aggressive size, and the delta printed during the sweep IS that size."*

It does not confirm. 2025 H2: high -0.272R vs low -0.341R (high is better — WITH the prediction). 2026: high +0.148R vs low +0.218R.
**The two eras point opposite ways, and that is the kill** — an era-flip
is not a weak confirmation, it is the absence of one.

**Bars could not see the trapped counterparty and neither can the tape.**
That was the argument for running L3 at all: V3 half-failed on candles
and the defence was that trapped size is a flow object. The flow says no.

Control reference, which the prereg pre-committed to calling out: `delta_entry` high in 2026 is -0.099R, with no story attached and
no 2025 support.
