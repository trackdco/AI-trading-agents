# London deep fades — can order flow give conviction on which reverses?

**Fit only. Sealed 2023/24 never loaded. Subset-of-a-subset mining — hypothesis generation, not a filter.**

Deep fade = direction-adjusted entry-vs-VWAP below -0.25 (long well below the day's VWAP, short well above). **73 trades, 44% win, $+3,992, mean R +0.332** — the near-coin-flip bucket the VWAP filter would drop. The question is whether flow strength at the extreme sorts the reversals from the continuations.

**How to read it.** AUC = P(the confluence ranks higher on a reverting/winning fade than a losing one); 0.5 is nothing, >0.5 means MORE strength predicts the reversal (the hypothesis). 5,000-shuffle permutation p. With 8 features the Bonferroni bar is p<0.0063. **n is ~32 winners / 41 losers, so power is low by construction** — expect few or zero survivors, and read a clean p as a lead to test on the holdout, never as a switch to flip.

**Excluded for coverage** (fewer than 40 of 73 rows carry the feature, so no honest read is possible): `wall_behind` (2/73). `wall_behind` in particular is structural, not bad luck — London's W check IS 'no wall behind the entry', so a taken trade almost never has one, and scoring its size would be circular.

## Does strength-at-the-extreme separate the reversals?

| confluence (dir-adjusted) | n | loser med | winner med | AUC | perm p | Bonferroni | reverse-rate low / high |
|---|---|---|---|---|---|---|---|
| book imbalance toward trade | 73 | -0.07 | 0.00 | 0.620 (strength->reversal) | 0.074 | no | 32% / 56% |
| support - resist depth | 73 | -3.00 | 0.00 | 0.615 (strength->reversal) | 0.093 | no | 31% / 59% |
| support-side depth (raw) | 73 | 25.00 | 26.50 | 0.586 (strength->reversal) | 0.211 | no | 41% / 47% |
| signed delta, 30-min | 69 | -22.00 | 27.00 | 0.576 (strength->reversal) | 0.289 | no | 37% / 50% |
| book thickening, 5-min | 71 | 0.50 | 5.00 | 0.572 (strength->reversal) | 0.310 | no | 38% / 50% |
| session CVD in trade dir | 69 | -494.00 | -816.00 | 0.430 (strength->continuation) | 0.325 | no | 54% / 32% |
| delta at fill (absorption) | 69 | -12.00 | -10.00 | 0.533 (strength->reversal) | 0.638 | no | 40% / 47% |
| signed delta, 15-min | 69 | 53.00 | 24.50 | 0.521 (strength->reversal) | 0.762 | no | 49% / 38% |

## Conviction composite (the most overfit object in the project — labelled as such)

Mean z-score of three DISTINCT strength lenses — book imbalance toward trade, session CVD in trade dir, delta at fill (absorption) — built AND scored on the same 73 trades. AUC 0.523, perm p 0.734. Reversal rate and net by composite tercile:

| conviction | trades | reverse rate | mean R | net $ |
|---|---|---|---|---|
| low | 26 | 46% | +0.818 | $+4,185 |
| mid | 23 | 43% | +0.125 | $+748 |
| high | 24 | 42% | +0.005 | $-940 |

### If you took only the high-conviction half of the deep fades

| | trades | reverse rate | mean R | net $ |
|---|---|---|---|---|
| high-conviction half (kept) | 36 | 44% | +0.102 | $+176 |
| low-conviction half (dropped) | 37 | 43% | +0.557 | $+3,816 |

Random-half guard (5,000 draws): the high-conviction half nets $+176 vs a random half's median $+2,041 (p=0.8242). Does not clearly beat a random split of the same size — the composite is not demonstrably sorting the fades on this data.

## Per-era check on the strongest single lead (book imbalance toward trade)

- **2025**: n=35, AUC 0.612
- **2026**: n=38, AUC 0.625

## Verdict

**Nothing clears Bonferroni** — expected at n=73. 
**On the mechanism:** the direction of the tilt is what matters more than any one p-value here. If the strength lenses point 'more strength -> higher reversal rate' (AUC>0.5), Angus's intuition is at least consistent with the fit data and deserves a pre-registered holdout test: a deep-fade is only taken when flow confirms someone is defending the extreme. If they point the other way, the deep fades that reverse are the ones flow had ALREADY given up on — a squeeze, not absorption — and the conviction story is wrong. Read the AUC arrows above for which world we are in.
