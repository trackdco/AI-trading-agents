# London overnight audit — Stage 1: loser autopsy at scale
**Fit only. Sealed 2023/24 never loaded** (`fit_only()` refuses any holdout path and raises on any row outside 2025/2026; no override exists).
Book = wall arm (W or FAR), uncapped + day stop. n=187 (2025: 78, 2026: 109).
Book WR: 2025 61.5%, 2026 53.2% | maxDD: 2025 $1,720, 2026 $2,550

## Acceptance bar (fixed before any result was seen)
A cut survives only if, **in 2025 and 2026 separately**: the cut set's WR is below the book's WR, the sign agrees across eras, n>=30 in each era, and removing it **improves maxDD** — net P&L alone is not enough.

**Net requirement:** the cut set must also be net NEGATIVE in each era. A set can sit below book WR and still be profitable via larger winners — cutting that costs money and is not a loser trait.

Every survivor is then jackknifed by dropping one month at a time. Anything that flips sign on a single month's removal is reported as FRAGILE, not as a finding.

## Result

**243 candidate cuts tested across all L3 features. 0 cleared the bar.**

**CLEAN NULL — no cut clears the bar.** No feature, at any quartile threshold, removes a predominantly-losing subset consistently in both eras while also improving drawdown. The book's losers are not separable by any single L3 feature at this resolution. That is a result, not a failure to find one.
