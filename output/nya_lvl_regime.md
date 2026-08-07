# NYA-LVL-01 stage 3a — regime diagnostic

Authorised by `docs/PREREG-level-interaction-stage3.md`. **Diagnosis, not a gate.** Fit span, base cost.
The question: is stage 2's result an edge, or a bet that NQ trended?

## S10/TRAIL

### 1. Does daily P&L track how far the market moved?

| vs | correlation |
|---|---:|
| absolute RTH move |close-open| | **+0.169** |
| RTH range | **+0.451** |
| directional efficiency | **-0.141** |

### 2. P&L by directional-efficiency tercile

A trend-capture model earns nearly everything in the top tercile.

| efficiency | sessions | total pts | share of profit | mean/day |
|---|---:|---:|---:|---:|
| chop | 96 | +20,093 | 35% | +209.3 |
| mid | 95 | +22,346 | 38% | +235.2 |
| trend | 95 | +15,722 | 27% | +165.5 |

### 3. Long side vs short side

A model that only earns on one side over a directional 13 months is a
beta bet wearing a strategy label.

| side | n | WR | total pts | mean R |
|---|---:|---:|---:|---:|
| long | 2,421 | 45% | +31,496 | +1.301 |
| short | 2,338 | 41% | +26,665 | +1.140 |

### 4. Monthly P&L vs NQ's own monthly move

| month | NQ net pts | strategy pts |
|---|---:|---:|
| 2025-06 | +217 | +3,082 |
| 2025-07 | -248 | +1,929 |
| 2025-08 | -74 | +2,064 |
| 2025-09 | +460 | +1,723 |
| 2025-10 | -650 | +3,235 |
| 2025-11 | -767 | +4,479 |
| 2025-12 | -407 | +2,547 |
| 2026-01 | -227 | +3,778 |
| 2026-02 | -52 | +6,352 |
| 2026-03 | -187 | +6,718 |
| 2026-04 | +2,378 | +3,506 |
| 2026-05 | +2,118 | +6,430 |
| 2026-06 | -1,418 | +9,266 |
| 2026-07 | -658 | +3,053 |

**Correlation of monthly strategy P&L with NQ's monthly move: -0.112**

## S20/T30

### 1. Does daily P&L track how far the market moved?

| vs | correlation |
|---|---:|
| absolute RTH move |close-open| | **-0.109** |
| RTH range | **-0.071** |
| directional efficiency | **-0.130** |

### 2. P&L by directional-efficiency tercile

A trend-capture model earns nearly everything in the top tercile.

| efficiency | sessions | total pts | share of profit | mean/day |
|---|---:|---:|---:|---:|
| chop | 96 | +2,204 | 56% | +23.0 |
| mid | 95 | +2,704 | 69% | +28.5 |
| trend | 95 | -972 | -25% | -10.2 |

### 3. Long side vs short side

A model that only earns on one side over a directional 13 months is a
beta bet wearing a strategy label.

| side | n | WR | total pts | mean R |
|---|---:|---:|---:|---:|
| long | 2,421 | 45% | +2,735 | +0.056 |
| short | 2,338 | 43% | +1,201 | +0.026 |

### 4. Monthly P&L vs NQ's own monthly move

| month | NQ net pts | strategy pts |
|---|---:|---:|
| 2025-06 | +217 | +627 |
| 2025-07 | -248 | +100 |
| 2025-08 | -74 | +419 |
| 2025-09 | +460 | -844 |
| 2025-10 | -650 | +76 |
| 2025-11 | -767 | +448 |
| 2025-12 | -407 | -124 |
| 2026-01 | -227 | +229 |
| 2026-02 | -52 | +715 |
| 2026-03 | -187 | +1,433 |
| 2026-04 | +2,378 | +290 |
| 2026-05 | +2,118 | +919 |
| 2026-06 | -1,418 | -278 |
| 2026-07 | -658 | -74 |

**Correlation of monthly strategy P&L with NQ's monthly move: +0.256**
