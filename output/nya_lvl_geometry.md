# NYA-LVL-01 stage 2 — geometry grid + placebo-level null

Authorised by `docs/PREREG-level-interaction-stage2.md`. 51 declared arms x 2 cost levels, 4,759 events, fit span only.

## 1. The declared default (named on mechanism BEFORE the grid ran)

| arm | cost | n | WR | net pts | PF | R/trade | 2025 R | 2026 R |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **S20/T30** | base | 4,759 | 44% | +3,936 | 1.07 | +0.041 | +0.013 | +0.075 |
| **S20/T30** | strict | 4,759 | 44% | -823 | 0.99 | -0.009 | -0.037 | +0.025 |

## 2. Top 12 of the 52 arms (base cost) — REPORTED, NOT PROMOTED

§6.0.1: in-sample rank never promotes. The default above stays the spec.

| arm | n | WR | net pts | PF | R base | R strict | 2025 R | 2026 R | both eras + |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `S10/TRAIL` | 4,759 | 43% | +58,161 | 3.09 | +1.222 | +1.122 | +0.734 | +1.809 | YES |
| `S15/TRAIL` | 4,759 | 47% | +50,630 | 2.29 | +0.709 | +0.643 | +0.394 | +1.088 | YES |
| `S10/T50` | 4,759 | 31% | +33,520 | 1.93 | +0.704 | +0.604 | +0.506 | +0.943 | YES |
| `S10/LADDER` | 4,310 | 31% | +27,582 | 1.85 | +0.640 | +0.540 | +0.347 | +1.002 | YES |
| `S10/T40` | 4,759 | 34% | +28,191 | 1.82 | +0.592 | +0.492 | +0.450 | +0.763 | YES |
| `S20/TRAIL` | 4,759 | 49% | +43,548 | 1.86 | +0.458 | +0.408 | +0.238 | +0.721 | YES |
| `S10/T30` | 4,759 | 38% | +19,275 | 1.59 | +0.405 | +0.305 | +0.295 | +0.537 | YES |
| `S15/T50` | 4,759 | 34% | +26,614 | 1.53 | +0.373 | +0.306 | +0.279 | +0.485 | YES |
| `S25/TRAIL` | 4,759 | 49% | +37,236 | 1.59 | +0.313 | +0.273 | +0.157 | +0.500 | YES |
| `S10/T25` | 4,759 | 40% | +14,661 | 1.47 | +0.308 | +0.208 | +0.243 | +0.386 | YES |
| `S15/LADDER` | 4,310 | 34% | +19,554 | 1.43 | +0.302 | +0.236 | +0.141 | +0.502 | YES |
| `S15/T40` | 4,759 | 38% | +21,070 | 1.45 | +0.295 | +0.228 | +0.231 | +0.372 | YES |

**30 of 51 arms are positive in BOTH eras at base cost; 24 of those survive strict cost.**

## 3. The null — do the six real levels beat random lines?

Six random levels drawn from the same day's pre-RTH range, identical grammar,
the ENTIRE 51-arm search re-run, 200 times. Statistic is the
family-wise best cell.

| | value |
|---|---:|
| observed best arm (R/trade) | **+1.2221** |
| null median | +1.1687 |
| null 95th pct | +1.2752 |
| null 99th pct | +1.3183 |
| **family-wise p** | **0.2050** |

**Declared bar was p <= 0.01. Result: FAIL.**

Random lines drawn from the same price zone reach the same best-cell
result as the real six. **On this test the six levels are not doing the
work — the geometry is.** That is a premise finding, not a geometry
finding, and it is the thing the family was built on.

## 4. Half-year stability of the default

| half | PF (base) |
|---|---:|
| 2025H1 | 1.14 |
| 2025H2 | 1.00 |
| 2026H1 | 1.14 |
| 2026H2 | 0.96 |

## 5. The early-cut overlay (losers never go green — does cutting them help?)

| arm | n | WR | PF | R base | R strict |
|---|---:|---:|---:|---:|---:|
| `S20/T30` | 4,759 | 44% | 1.07 | +0.041 | -0.009 |
| `DEFAULT+cut5` | 4,759 | 39% | 1.09 | +0.046 | -0.004 |
| `DEFAULT+cut15` | 4,759 | 41% | 1.07 | +0.038 | -0.012 |
| `DEFAULT+cut30` | 4,759 | 42% | 1.07 | +0.040 | -0.010 |
