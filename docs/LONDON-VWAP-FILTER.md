# London — only entering on the right side of VWAP

**Fit only. Sealed 2023/24 never loaded. Causal filter, in-sample test.**

Baseline (frozen arm, flat 1 lot): **187 trades, $+22,795, 57% win, mean R +0.513, maxDD $2,440, worst $-735**.

The filter keeps a trade only if its direction-adjusted entry-vs-VWAP is at or above a threshold: a long at/above the day's VWAP, a short at/below it. **Right side of VWAP = threshold 0**, pre-specified, no tuning. 0 of 187 trades have no VWAP feature (too few pre-fill bars) and are KEPT under every threshold — dropping them would be a different, silent filter.

## The pre-specified filter (right side of VWAP, threshold 0)

Drops **90** wrong-side entries (the ones still selected after re-running the causal walk on the filtered pool).

| book | trades | net $ | win rate | mean R | maxDD | worst | 2025 net | 2026 net |
|---|---|---|---|---|---|---|---|---|
| baseline (fade allowed) | 187 | $+22,795 | 57% | +0.513 | $2,440 | $-735 | $+8,178 | $+14,618 |
| right-side only (>= 0) | 97 | $+16,939 | 68% | +0.695 | $935 | $-440 | $+5,666 | $+11,272 |
| **change** | **-90** | **$-5,856** | **+11pp** | **+0.182** | **$-1,505** | **$+295** | **$-2,511** | **$-3,345** |

**The dropped trades on their own:** 100 entries, $+9,094, 47% win, mean R +0.438. They were net POSITIVE despite the low win rate — cutting them removes some profit, so the filter only helps if the drawdown reduction is worth it.

## Guard 1 — is this more than just trading fewer trades?

Removing 100 trades at random from the 187-trade book, 5,000 times, and comparing where the VWAP filter's net lands in that distribution.

| | net $ |
|---|---|
| VWAP filter (right side only) | $+16,939 |
| random drop of 100: median | $+10,678 |
| random drop of 100: p95 | $+15,326 |

**p = 0.0126** — the filter beats 98.7% of equal-sized random cuts. It is doing more than thinning the book.

## Guard 2 — does it hold in both eras?

2025 net $+8,178 -> $+5,666 ($-2,511); 2026 net $+14,618 -> $+11,272 ($-3,345). Does NOT improve in both eras — treat as a one-era artifact.

## Threshold sensitivity (NOT for picking — the headline is 0)

Raising the threshold demands the entry be further onto the right side of VWAP. Shown so the choice of 0 is visible against its neighbours; picking the best cell here would be the selection inflation this doc is trying not to commit.

| threshold | trades | net $ | win rate | mean R | maxDD | net/maxDD | 2025 / 2026 net |
|---|---|---|---|---|---|---|---|
| none (baseline) | 187 | $+22,795 | 57% | +0.513 | $2,440 | 9.3 | $+8,178 / $+14,618 |
| >= -0.5 | 126 | $+21,640 | 64% | +0.674 | $1,135 | 19.1 | $+6,728 / $+14,912 |
| >= -0.25 | 124 | $+22,040 | 65% | +0.701 | $1,135 | 19.4 | $+7,128 / $+14,912 |
| >= +0 **<- right side** | 97 | $+16,939 | 68% | +0.695 | $935 | 18.1 | $+5,666 / $+11,272 |
| >= +0.25 | 71 | $+11,736 | 69% | +0.697 | $935 | 12.6 | $+5,131 / $+6,605 |
| >= +0.5 | 67 | $+10,836 | 69% | +0.677 | $935 | 11.6 | $+5,361 / $+5,475 |

## What it does to the funded account (NY + London, shared $800)

The filter also frees shared budget for NY, since a skipped London trade no longer draws first. NY-alone baseline (replayed): $+90,249, P(bust) 2.4%. London at flat 1 lot.

| London book | combined net | vs NY-alone | worst day | maxDD | P(bust) | med withdrawn |
|---|---|---|---|---|---|---|
| baseline (fade allowed) | $+109,060 | **$+18,811** | $-797 | $1,528 | 1.6% | $105,021 |
| right side only (>= 0) | $+107,837 | **$+17,588** | $-782 | $1,398 | 1.2% | $108,141 |

## Verdict

**Direct answer: never fading VWAP LOWERS raw P&L, by $5,856** ($+22,795 -> $+16,939). The reason is the trap the loss anatomy set: the wrong-side entries lose more OFTEN, but they are net POSITIVE ($+9,094 over 100 trades, mean R +0.438) — they win less but win big when the fade snaps back. A higher loss rate is not a negative expectancy, and cutting on loss rate throws away good trades.

**But it is not a null — it is a risk trade, and a good one.** The same cut nearly halves maxDD ($2,440 -> $935) and lifts return-on-drawdown from 9.3 to 18.1. Guard 1 confirms the cut is non-random (p=0.0126, beats 99% of equal-size random drops), so it removes genuinely worse-than-average trades — just not money-losing ones. On the funded account the drawdown reduction is what pays: bust risk falls and median withdrawn RISES despite the lower raw net, because a $2k trailing line rewards a smaller drawdown more than it rewards the extra gross.

**The sweep says the aggressive cut overshoots.** Threshold 0 drops 90 trades to buy that drawdown reduction; a MILDER cut at -0.25 (drop only the DEEP fades) keeps almost all the net while getting most of the drawdown benefit. That mild threshold is selection-mined from this sweep, so it is not a headline — but it is the shape to carry into a pre-registered holdout test: the signal is 'don't take the DEEP counter-VWAP fades', not 'never trade below VWAP'. Either way, derived in-sample from these losers — an upper bound until the sealed holdout confirms it.
