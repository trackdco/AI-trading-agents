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

## Which floor bound the result

2 cell(s) met the >= 65% WR bar in BOTH eras but were rejected by the pooled Wilson floor — a SAMPLE-SIZE objection, not evidence against:

| cell | n | pooled WR | Wilson lo | 2025 | 2026 |
|---|---|---|---|---|---|
| `cvd_ASIA>737 AND dep_wall_above_sz>5` | 67 | 65.7% | **53.7%** | 41/65.9% | 26/65.4% |
| `dep_resist>33 AND ASIA==0` | 61 | 65.6% | **53.0%** | 32/65.6% | 29/65.5% |

The two floors cannot both be satisfied at this population size: ~1 trade/week admits n≈39-70, while a 95% Wilson lower bound of 60% off a ~65% point estimate needs n≈150. Any cell rare enough to be 'low-frequency' is too small to prove itself to 95% confidence. **These cells are not findings** — they are the reason the null is 'unproven at this sample', not 'disproven'. Note that two of them invert or ignore ASIA, consistent with the L3 trial finding ASIA backwards in 2026.

**CLEAN NULL.** No feature combination reaches 65% win rate in both eras at ~1 trade/week with a pooled Wilson floor of 60% and a family-wise-corrected permutation null. Searching 29,161 combinations and finding nothing that survives correction is exactly what an honest search over a population with one real signal looks like. There is no London elite cell at this resolution.
