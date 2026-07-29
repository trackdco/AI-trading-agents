# London overnight audit — Stage 2: combination search

**Fit only. Sealed 2023/24 never loaded.**

Population: risk >= 9.5 candidates, n=884 (2025: 390, 2026: 494) over 195 days (~39 weeks).

## Acceptance bar (fixed in advance)

- >= 65% WR in 2025 and 2026 **separately**
- pooled Wilson 95% lower bound >= 60%
- >= ~1 trade/week pooled (n >= 39), and n >= 25 per era so a 65% WR is never 2-of-3
- 2000-shuffle permutation null **per era**, outcomes shuffled within era
- family-wise correction (Šidák) across every combination tested

## Result

**29,161 combinations tested** (all singles and all pairs of 241 atomic conditions derived from the L3 features). **0 cleared the deterministic bar** before any null was run.

**CLEAN NULL.** No feature combination reaches 65% win rate in both eras at ~1 trade/week with a pooled Wilson floor of 60% and a family-wise-corrected permutation null. Searching 29,161 combinations and finding nothing that survives correction is exactly what an honest search over a population with one real signal looks like. There is no London elite cell at this resolution.
