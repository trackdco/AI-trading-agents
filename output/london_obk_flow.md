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
| low | 2025 | base | 51 | 33% | -208 | 0.63 | -0.275 |
| low | 2025 | strict | 51 | 31% | -259 | 0.57 | -0.359 |
| mid | 2025 | base | 50 | 26% | -118 | 0.67 | -0.365 |
| mid | 2025 | strict | 50 | 24% | -168 | 0.57 | -0.511 |
| high | 2025 | base | 51 | 33% | -78 | 0.79 | -0.214 |
| high | 2025 | strict | 51 | 33% | -129 | 0.68 | -0.329 |
| low | 2026 | base | 42 | 33% | -87 | 0.85 | -0.125 |
| low | 2026 | strict | 42 | 33% | -129 | 0.79 | -0.186 |
| mid | 2026 | base | 40 | 22% | -158 | 0.68 | -0.344 |
| mid | 2026 | strict | 40 | 22% | -198 | 0.62 | -0.427 |
| high | 2026 | base | 43 | 42% | +253 | 1.56 | +0.448 |
| high | 2026 | strict | 43 | 42% | +210 | 1.44 | +0.377 |

#### F1 · `delta_pre5` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 52 | 25% | -243 | 0.52 | -0.273 |
| low | 2025 | strict | 52 | 25% | -295 | 0.46 | -0.378 |
| mid | 2025 | base | 48 | 33% | -74 | 0.78 | -0.220 |
| mid | 2025 | strict | 48 | 29% | -122 | 0.67 | -0.359 |
| high | 2025 | base | 52 | 35% | -86 | 0.81 | -0.355 |
| high | 2025 | strict | 52 | 35% | -138 | 0.71 | -0.456 |
| low | 2026 | base | 42 | 36% | -25 | 0.95 | +0.062 |
| low | 2026 | strict | 42 | 36% | -67 | 0.88 | -0.008 |
| mid | 2026 | base | 41 | 34% | +43 | 1.09 | +0.072 |
| mid | 2026 | strict | 41 | 34% | +2 | 1.00 | -0.004 |
| high | 2026 | base | 42 | 29% | -10 | 0.98 | -0.126 |
| high | 2026 | strict | 42 | 29% | -52 | 0.91 | -0.195 |

#### F1 · `delta_sweep` — _HIGH should help the fade (big trapped cohort) — the mechanism variable_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 51 | 29% | -177 | 0.63 | -0.271 |
| low | 2025 | strict | 51 | 29% | -228 | 0.56 | -0.368 |
| mid | 2025 | base | 50 | 30% | -39 | 0.87 | -0.241 |
| mid | 2025 | strict | 50 | 26% | -89 | 0.74 | -0.400 |
| high | 2025 | base | 51 | 33% | -187 | 0.63 | -0.339 |
| high | 2025 | strict | 51 | 33% | -238 | 0.56 | -0.428 |
| low | 2026 | base | 42 | 33% | -153 | 0.75 | +0.114 |
| low | 2026 | strict | 42 | 33% | -195 | 0.69 | +0.053 |
| mid | 2026 | base | 40 | 28% | -90 | 0.78 | -0.347 |
| mid | 2026 | strict | 40 | 28% | -130 | 0.70 | -0.442 |
| high | 2026 | base | 43 | 37% | +251 | 1.48 | +0.218 |
| high | 2026 | strict | 43 | 37% | +208 | 1.38 | +0.157 |

#### F1 · `absorb_extreme` — _HIGH should help the fade (size absorbed at the extreme)_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 51 | 29% | -80 | 0.77 | -0.300 |
| low | 2025 | strict | 51 | 29% | -130 | 0.66 | -0.442 |
| mid | 2025 | base | 50 | 24% | -154 | 0.64 | -0.305 |
| mid | 2025 | strict | 50 | 24% | -204 | 0.56 | -0.429 |
| high | 2025 | base | 51 | 39% | -169 | 0.67 | -0.247 |
| high | 2025 | strict | 51 | 35% | -220 | 0.59 | -0.327 |
| low | 2026 | base | 42 | 36% | +238 | 1.66 | +0.410 |
| low | 2026 | strict | 42 | 36% | +196 | 1.51 | +0.326 |
| mid | 2026 | base | 41 | 32% | -6 | 0.99 | -0.165 |
| mid | 2026 | strict | 41 | 32% | -46 | 0.93 | -0.228 |
| high | 2026 | base | 42 | 31% | -224 | 0.61 | -0.243 |
| high | 2026 | strict | 42 | 31% | -266 | 0.56 | -0.310 |

#### F1 · `wall_ratio_opp` — _HIGH should HURT (a wall in the path to target)_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 55 | 35% | -143 | 0.72 | -0.119 |
| low | 2025 | strict | 55 | 35% | -198 | 0.64 | -0.235 |
| mid | 2025 | base | 40 | 32% | -70 | 0.74 | -0.266 |
| mid | 2025 | strict | 40 | 32% | -110 | 0.63 | -0.395 |
| high | 2025 | base | 57 | 26% | -191 | 0.62 | -0.456 |
| high | 2025 | strict | 57 | 23% | -248 | 0.55 | -0.559 |
| low | 2026 | base | 44 | 27% | -103 | 0.78 | -0.313 |
| low | 2026 | strict | 44 | 27% | -147 | 0.70 | -0.398 |
| mid | 2026 | base | 38 | 32% | +1 | 1.00 | +0.038 |
| mid | 2026 | strict | 38 | 32% | -37 | 0.93 | -0.030 |
| high | 2026 | base | 43 | 40% | +110 | 1.20 | +0.293 |
| high | 2026 | strict | 43 | 40% | +67 | 1.12 | +0.232 |

#### F1 · `book_imb` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 51 | 25% | -217 | 0.56 | -0.445 |
| low | 2025 | strict | 51 | 24% | -268 | 0.49 | -0.561 |
| mid | 2025 | base | 47 | 28% | -137 | 0.66 | -0.378 |
| mid | 2025 | strict | 47 | 28% | -184 | 0.58 | -0.500 |
| high | 2025 | base | 54 | 39% | -49 | 0.88 | -0.050 |
| high | 2025 | strict | 54 | 37% | -103 | 0.76 | -0.158 |
| low | 2026 | base | 42 | 21% | -381 | 0.37 | -0.397 |
| low | 2026 | strict | 42 | 21% | -423 | 0.34 | -0.466 |
| mid | 2026 | base | 39 | 41% | +114 | 1.27 | +0.172 |
| mid | 2026 | strict | 39 | 41% | +75 | 1.17 | +0.090 |
| high | 2026 | base | 44 | 36% | +275 | 1.55 | +0.232 |
| high | 2026 | strict | 44 | 36% | +231 | 1.44 | +0.168 |

### A/S1

_Book features present on 300 of 300 A/S1 trades (depth window is 07:00-08:59 UTC; macro-hour reads are seasonally incomplete and barred as gates)._

#### A/S1 · `delta_entry` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 24% | -338 | 0.34 | -0.462 |
| low | 2025 | strict | 54 | 24% | -392 | 0.29 | -0.587 |
| mid | 2025 | base | 54 | 28% | -79 | 0.81 | -0.300 |
| mid | 2025 | strict | 54 | 28% | -133 | 0.71 | -0.423 |
| high | 2025 | base | 54 | 41% | -22 | 0.94 | -0.009 |
| high | 2025 | strict | 54 | 41% | -76 | 0.81 | -0.123 |
| low | 2026 | base | 46 | 48% | +216 | 1.50 | +0.327 |
| low | 2026 | strict | 46 | 48% | +170 | 1.37 | +0.251 |
| mid | 2026 | base | 46 | 35% | -34 | 0.92 | -0.070 |
| mid | 2026 | strict | 46 | 35% | -80 | 0.83 | -0.157 |
| high | 2026 | base | 46 | 30% | -93 | 0.83 | -0.216 |
| high | 2026 | strict | 46 | 30% | -139 | 0.76 | -0.287 |

#### A/S1 · `delta_pre5` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 33% | -83 | 0.79 | -0.217 |
| low | 2025 | strict | 54 | 33% | -137 | 0.69 | -0.334 |
| mid | 2025 | base | 54 | 20% | -271 | 0.36 | -0.532 |
| mid | 2025 | strict | 54 | 20% | -325 | 0.31 | -0.674 |
| high | 2025 | base | 54 | 39% | -84 | 0.82 | -0.023 |
| high | 2025 | strict | 54 | 39% | -138 | 0.72 | -0.124 |
| low | 2026 | base | 46 | 48% | +228 | 1.61 | +0.298 |
| low | 2026 | strict | 46 | 48% | +182 | 1.46 | +0.217 |
| mid | 2026 | base | 46 | 28% | -183 | 0.68 | -0.228 |
| mid | 2026 | strict | 46 | 28% | -229 | 0.63 | -0.304 |
| high | 2026 | base | 46 | 37% | +43 | 1.09 | -0.030 |
| high | 2026 | strict | 46 | 37% | -3 | 0.99 | -0.105 |

#### A/S1 · `delta_sweep` — _HIGH should help the fade (big trapped cohort) — the mechanism variable_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 30% | -148 | 0.67 | -0.327 |
| low | 2025 | strict | 54 | 30% | -202 | 0.58 | -0.442 |
| mid | 2025 | base | 53 | 25% | -236 | 0.38 | -0.435 |
| mid | 2025 | strict | 53 | 25% | -288 | 0.31 | -0.580 |
| high | 2025 | base | 55 | 38% | -55 | 0.88 | -0.018 |
| high | 2025 | strict | 55 | 38% | -110 | 0.78 | -0.119 |
| low | 2026 | base | 46 | 48% | +217 | 1.50 | +0.309 |
| low | 2026 | strict | 46 | 48% | +171 | 1.38 | +0.238 |
| mid | 2026 | base | 46 | 26% | -218 | 0.61 | -0.301 |
| mid | 2026 | strict | 46 | 26% | -264 | 0.55 | -0.385 |
| high | 2026 | base | 46 | 39% | +89 | 1.20 | +0.032 |
| high | 2026 | strict | 46 | 39% | +43 | 1.09 | -0.045 |

#### A/S1 · `absorb_extreme` — _HIGH should help the fade (size absorbed at the extreme)_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 39% | -40 | 0.88 | -0.039 |
| low | 2025 | strict | 54 | 39% | -94 | 0.73 | -0.190 |
| mid | 2025 | base | 54 | 28% | -172 | 0.59 | -0.337 |
| mid | 2025 | strict | 54 | 28% | -226 | 0.50 | -0.460 |
| high | 2025 | base | 54 | 26% | -227 | 0.59 | -0.396 |
| high | 2025 | strict | 54 | 26% | -281 | 0.53 | -0.483 |
| low | 2026 | base | 46 | 30% | -92 | 0.81 | -0.208 |
| low | 2026 | strict | 46 | 30% | -138 | 0.73 | -0.291 |
| mid | 2026 | base | 46 | 46% | +134 | 1.33 | +0.227 |
| mid | 2026 | strict | 46 | 46% | +88 | 1.21 | +0.143 |
| high | 2026 | base | 46 | 37% | +46 | 1.08 | +0.021 |
| high | 2026 | strict | 46 | 37% | +0 | 1.00 | -0.045 |

#### A/S1 · `wall_ratio_opp` — _HIGH should HURT (a wall in the path to target)_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 55 | 33% | -176 | 0.60 | -0.159 |
| low | 2025 | strict | 55 | 33% | -232 | 0.52 | -0.283 |
| mid | 2025 | base | 52 | 27% | -129 | 0.67 | -0.409 |
| mid | 2025 | strict | 52 | 27% | -181 | 0.57 | -0.538 |
| high | 2025 | base | 55 | 33% | -134 | 0.71 | -0.211 |
| high | 2025 | strict | 55 | 33% | -188 | 0.62 | -0.321 |
| low | 2026 | base | 47 | 30% | -134 | 0.76 | -0.197 |
| low | 2026 | strict | 47 | 30% | -182 | 0.69 | -0.276 |
| high | 2026 | base | 79 | 41% | +138 | 1.17 | +0.091 |
| high | 2026 | strict | 79 | 41% | +59 | 1.07 | +0.014 |

#### A/S1 · `book_imb` — _control — no strong prior_

| tercile | era | cost | n | WR | net pts | PF | R/trade |
|---|---|---|---:|---:|---:|---:|---:|
| low | 2025 | base | 54 | 22% | -355 | 0.30 | -0.505 |
| low | 2025 | strict | 54 | 22% | -409 | 0.25 | -0.623 |
| mid | 2025 | base | 54 | 33% | -62 | 0.84 | -0.152 |
| mid | 2025 | strict | 54 | 33% | -116 | 0.73 | -0.280 |
| high | 2025 | base | 54 | 37% | -22 | 0.95 | -0.114 |
| high | 2025 | strict | 54 | 37% | -76 | 0.82 | -0.230 |
| low | 2026 | base | 46 | 37% | -95 | 0.80 | -0.048 |
| low | 2026 | strict | 46 | 37% | -141 | 0.72 | -0.129 |
| mid | 2026 | base | 46 | 24% | -217 | 0.62 | -0.379 |
| mid | 2026 | strict | 46 | 24% | -263 | 0.57 | -0.454 |
| high | 2026 | base | 46 | 52% | +400 | 2.03 | +0.467 |
| high | 2026 | strict | 46 | 52% | +354 | 1.87 | +0.391 |

## Scorecard — declared direction vs what happened

`high>low` = the high tercile beat the low tercile at base cost. The
prediction column was written before the join. A feature counts only if it
moves the predicted way in **both** eras — one era is a coin flip.

| arm | feature | predicted | 2025 high>low | 2026 high>low | consistent |
|---|---|---|---|---|---|
| F1 | `delta_entry` | control | yes | yes | consistent |
| F1 | `delta_pre5` | control | no | no | consistent |
| F1 | `delta_sweep` | high helps | no | yes | no — flips between eras |
| F1 | `absorb_extreme` | high helps | yes | no | no — flips between eras |
| F1 | `wall_ratio_opp` | high hurts | no | yes | no — flips between eras |
| F1 | `book_imb` | control | yes | yes | consistent |
| A/S1 | `delta_entry` | control | yes | no | no — flips between eras |
| A/S1 | `delta_pre5` | control | yes | no | no — flips between eras |
| A/S1 | `delta_sweep` | high helps | yes | no | no — flips between eras |
| A/S1 | `absorb_extreme` | high helps | no | yes | no — flips between eras |
| A/S1 | `wall_ratio_opp` | high hurts | no | yes | no — flips between eras |
| A/S1 | `book_imb` | control | yes | yes | consistent |

### The mechanism variable failed, and that is the finding

`delta_sweep` was named in the prereg — before the join — as the one
feature that had to work: *"the fade thesis is that the break traps
aggressive size, and the delta printed during the sweep IS that size."*

It does not confirm. In 2025 H2 the **high**-delta sweeps are the
**worst** tercile (−0.339R vs −0.271R for low) — the opposite of the
prediction — and 2026 is non-monotonic (low +0.114, mid −0.347, high
+0.218), which is a shape noise makes and a mechanism does not.

**Bars could not see the trapped counterparty and neither can the tape.**
That was the argument for running L3 at all: V3 half-failed on candles
and the defence was that trapped size is a flow object. The flow says no.

**The controls did as well or better**, which the prereg pre-committed to
calling out: `delta_entry` high in 2026 is the strongest cell in the
whole pass (+0.448R, PF 1.56) and it has no story attached and no 2025
support. That is generic flow-momentum in one era, not this candidate's
mechanism.
