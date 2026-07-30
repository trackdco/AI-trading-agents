# Optimal retained payout buffer

**Fit only. Sealed 2023/24 never loaded.**

Payout rule: **5 trading days of +$100 or better** since the last withdrawal (ANGUS 2026-07-30). On eligibility, withdraw everything above the retained buffer.

2,000 paths x 252 days, seeded (20260730). Day-level bootstrap, intraday order preserved. Floor: $2,000 trailing, locks at start once equity reaches $52,000.

## lucid  — base $150 STATIC, no size feedback

| retained buffer | P(bust) | payout cycles med | total withdrawn p10/med/p90 | min buffer med |
|---|---|---|---|---|
| $2,000 | **18.4%** | 27 | $46,079 / $92,397 / $112,111 | $534 |
| $3,000 | **3.9%** | 27 | $74,580 / $93,304 / $112,217 | $1,267 |
| $4,000 | **2.4%** | 27 | $73,805 / $92,552 / $111,011 | $1,521 |
| $5,000 | **2.1%** | 27 | $73,384 / $91,580 / $110,571 | $1,568 |
| $6,000 | **2.1%** | 27 | $72,571 / $90,716 / $109,395 | $1,577 |
| $8,000 | **2.1%** | 26 | $70,306 / $88,673 / $107,402 | $1,577 |
| $10,000 | **2.1%** | 26 | $68,468 / $86,409 / $105,662 | $1,577 |
| $12,000 | **2.1%** | 25 | $66,265 / $84,673 / $103,493 | $1,577 |
| $16,000 | **2.1%** | 24 | $62,399 / $80,670 / $99,322 | $1,577 |

**Most withdrawn:** $3,000 buffer ($93,304 median). **Lowest bust:** $5,000 buffer (2.1%).

| buffer | median withdrawn | P(bust) | withdrawn per 1% bust |
|---|---|---|---|
| $2,000 | $92,397 | 18.4% | $5,008 |
| $3,000 | $93,304 | 3.9% | $24,235 |
| $4,000 | $92,552 | 2.4% | $38,563 |
| $5,000 | $91,580 | 2.1% | $43,610 |
| $6,000 | $90,716 | 2.1% | $43,198 |
| $8,000 | $88,673 | 2.1% | $42,225 |
| $10,000 | $86,409 | 2.1% | $41,147 |
| $12,000 | $84,673 | 2.1% | $40,320 |
| $16,000 | $80,670 | 2.1% | $38,414 |

## scaled600  — base SCALES with buffer, size feedback modelled

| retained buffer | P(bust) | payout cycles med | total withdrawn p10/med/p90 | min buffer med |
|---|---|---|---|---|
| $2,000 | **14.3%** | 28 | $65,628 / $104,331 / $137,946 | $622 |
| $3,000 | **2.9%** | 28 | $87,308 / $118,752 / $156,078 | $1,339 |
| $4,000 | **1.9%** | 28 | $102,043 / $137,463 / $180,696 | $1,554 |
| $5,000 | **1.7%** | 28 | $125,549 / $169,335 / $218,956 | $1,590 |
| $6,000 | **1.7%** | 28 | $144,285 / $193,864 / $247,129 | $1,590 |
| $8,000 | **1.7%** | 28 | $182,315 / $240,680 / $303,260 | $1,590 |
| $10,000 | **1.7%** | 28 | $212,121 / $276,053 / $343,514 | $1,590 |
| $12,000 | **1.7%** | 28 | $234,666 / $301,984 / $372,639 | $1,590 |
| $16,000 | **1.7%** | 28 | $258,225 / $328,138 / $399,378 | $1,590 |

**Most withdrawn:** $16,000 buffer ($328,138 median). **Lowest bust:** $5,000 buffer (1.7%).

| buffer | median withdrawn | P(bust) | withdrawn per 1% bust |
|---|---|---|---|
| $2,000 | $104,331 | 14.3% | $7,296 |
| $3,000 | $118,752 | 2.9% | $40,949 |
| $4,000 | $137,463 | 1.9% | $72,349 |
| $5,000 | $169,335 | 1.7% | $99,609 |
| $6,000 | $193,864 | 1.7% | $114,037 |
| $8,000 | $240,680 | 1.7% | $141,576 |
| $10,000 | $276,053 | 1.7% | $162,384 |
| $12,000 | $301,984 | 1.7% | $177,638 |
| $16,000 | $328,138 | 1.7% | $193,022 |

## Reading it

On **lucid** the buffer is a pure safety/liquidity trade: the risk unit is fixed at $150 so a larger buffer cannot buy more size, it only moves the account away from the line and delays cash out. On **scaled600** the buffer sets the risk unit, so raising it compounds — bigger buffer, bigger position, faster buffer growth — which is why the two profiles can disagree about the optimum. Pick the profile first, then the buffer.
