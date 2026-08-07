# NYA-LVL-01 — RAW UNCAPPED TRIGGER SET (stage 1)

Authorised by `docs/PREREG-level-interaction.md`. **Raw. No filters, no cuts, no optimisation, no arm
selection.** §5.9.1: no bin decision is ever made off the raw trigger set, and
ugly raw is the expected shape at this stage.

Fit span 2025-06-02 -> 2026-07-15. **286 sessions. 4,808 touches, 4,759 filled** (16.6 filled/session). Sealed 2023/24 NOT touched.

## 1. Does the trade exist? (the only kill legal at this stage)

| era | sessions | touches | filled | filled/session | vs floor of 2 |
|---|---:|---:|---:|---:|---|
| 2025 | 149 | 2,629 | 2,597 | **17.4** | PASS |
| 2026 | 137 | 2,179 | 2,162 | **15.8** | PASS |

## 2. Where the touches are (level type — expected first discriminator)

| level | touches | filled | fill rate | share |
|---|---:|---:|---:|---:|
| `PM_HIGH` | 955 | 945 | 99% | 20% |
| `PM_50` | 1,012 | 1,006 | 99% | 21% |
| `PM_LOW` | 883 | 873 | 99% | 18% |
| `PD_HIGH` | 716 | 708 | 99% | 15% |
| `PD_50` | 732 | 721 | 98% | 15% |
| `PD_LOW` | 510 | 506 | 99% | 11% |

## 3. RAW P&L — every arm, side by side, nothing selected

Version B (raw touch), all filled events. `S_LEVEL` = 15m-close stop at the
level scale; `S_FAR` = the original far-extreme stop.

**cost base (1 pt)**

| stop | target | n | WR | net pts | $ @160 risk | PF | R/trade |
|---|---|---:|---:|---:|---:|---:|---:|
| S_LEVEL | T_LADDER | 4,310 | 39% | -25,447 | $-64,146 | 0.79 | -0.093 |
| S_LEVEL | T_SCALP | 4,759 | 61% | -57,594 | $-153,526 | 0.43 | -0.202 |
| S_LEVEL | T_TIME | 4,759 | 39% | -12,143 | $-25,834 | 0.91 | -0.034 |
| S_FAR | T_LADDER | 2,539 | 59% | -4,208 | $-18,345 | 0.96 | -0.045 |
| S_FAR | T_SCALP | 2,988 | 79% | -35,869 | $-56,434 | 0.50 | -0.118 |
| S_FAR | T_TIME | 2,988 | 50% | -4,926 | $-8,588 | 0.94 | -0.018 |

**cost strict (2 pt)**

| stop | target | n | WR | net pts | $ @160 risk | PF | R/trade |
|---|---|---:|---:|---:|---:|---:|---:|
| S_LEVEL | T_LADDER | 4,310 | 38% | -29,757 | $-79,719 | 0.76 | -0.116 |
| S_LEVEL | T_SCALP | 4,759 | 61% | -62,353 | $-170,694 | 0.40 | -0.224 |
| S_LEVEL | T_TIME | 4,759 | 39% | -16,902 | $-43,002 | 0.88 | -0.056 |
| S_FAR | T_LADDER | 2,539 | 59% | -6,747 | $-23,063 | 0.94 | -0.057 |
| S_FAR | T_SCALP | 2,988 | 79% | -38,857 | $-61,610 | 0.46 | -0.129 |
| S_FAR | T_TIME | 2,988 | 49% | -7,914 | $-13,765 | 0.91 | -0.029 |

**Realised stop distance (Angus: oversized stops are disqualifying)**

| stop arm | median pts | p90 pts |
|---|---:|---:|
| S_LEVEL | 48.4 | 87.9 |
| S_FAR | 121.0 | 334.2 |

## 4. Year-halves (§5.11-5 — pooling has hidden a bad half twice)

`S_LEVEL` + `T_SCALP`, base cost.

| half | n | WR | net pts | PF |
|---|---:|---:|---:|---:|
| 2025H1 | 378 | 62% | -1,535 | 0.70 |
| 2025H2 | 2,219 | 58% | -21,701 | 0.47 |
| 2026H1 | 2,016 | 64% | -31,183 | 0.38 |
| 2026H2 | 146 | 62% | -3,175 | 0.30 |

## 5. Per level type (`S_LEVEL` + `T_SCALP`, base cost)

| level | n | WR | net pts | PF | R/trade |
|---|---:|---:|---:|---:|---:|
| `PM_HIGH` | 945 | 60% | -10,909 | 0.44 | -0.233 |
| `PM_50` | 1,006 | 62% | -14,605 | 0.39 | -0.251 |
| `PM_LOW` | 873 | 62% | -10,308 | 0.44 | -0.157 |
| `PD_HIGH` | 708 | 58% | -7,723 | 0.44 | -0.201 |
| `PD_50` | 721 | 62% | -7,252 | 0.48 | -0.158 |
| `PD_LOW` | 506 | 64% | -6,798 | 0.42 | -0.185 |

**Reported, not acted on.** Level type is recorded from birth because Angus
expects it to be the first discriminator — but selecting on it here would be
a bin decision off the raw set, which §5.9.1 forbids.

## 6. Version A (break-then-retest) — the other taught machine

| | n | WR | net pts | PF |
|---|---:|---:|---:|---:|
| Version B (raw touch) | 4,759 | 61% | -57,594 | 0.43 |
| Version A (retest close) | 1,133 | 63% | -1,658 | 0.87 |

## 7. Recorded but NOT applied — the variables for later stages

| variable | recorded | note |
|---|---|---|
| time of day | `clock`, `minute_of_rth` | his opening-candle and ~11:00 rules are later arms |
| tap number | `tap_15m` | his three-tap rule is a later arm |
| level age | `level_age_min` | PM levels only |
| gap context | `gap_context` | RTH open vs prior close |
| distance from open | `dist_from_open` | |
| in-trade path | `mfe`, `mae`, `t5`, `t15`, `t30` | §5.12-5 schema, from birth |
