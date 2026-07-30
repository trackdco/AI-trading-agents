# London holdout — REHEARSAL on the fit span [rev3]

**Config: rev 3: 08:00-09:45 / V1 BE@1R / score-0 veto (frozen literals) / one-position-at-a-time.**

**This is not a result — it is the dress rehearsal: the same script, pointed at the fit span, gated on exact reproduction of every committed anchor.** The sealed run is `--span holdout --config rev3 --authorized-by "..."` with zero code changes.

## Items 1-8 — the book (flat 1 NQ lot)

| item | value |
|---|---|
| 1. trades / days with a take | 130 / 93 |
| 2. net P&L | $+22,665 |
| 3. win rate | 29% |
| 4. mean R | +0.758 |
| 5. maxDD (chronological, trade-level) | $1,310 |
| 6. months green | 10/14 |
| 7. worst month | $-1,100 (2026-02) |
| 8. trades per week | 2.2 |

(Under rev 3 the WR optic is structural, not a health metric: V1 scratches ~40% of trades at BE, so wins concentrate — mean R and net are the health metrics.)

Per era:

| era | n | net | WR | mean R | maxDD |
|---|---|---|---|---|---|
| 2025 | 57 | $+7,965 | 26% | +0.578 | $775 |
| 2026 | 73 | $+14,700 | 32% | +0.898 | $1,310 |

## Item 9 — W/FAR lift (floor-passing candidates, either vs neither)

| slice | either n | either R | neither n | neither R | lift |
|---|---|---|---|---|---|
| pooled | 191 | +0.609 | 619 | -0.145 | **+0.754** |
| 2025 | 73 | +0.496 | 289 | -0.088 | **+0.584** |
| 2026 | 118 | +0.679 | 330 | -0.195 | **+0.874** |

## Item 10 / S2 — the either cell split (DESCRIPTIVE, no inference)

both W+FAR: n=97, mean R +0.894 · exactly one: n=33, mean R +0.358

Prereg §4: no decision may be taken on this number in this run — doing so retroactively makes the family 3 tests.

## The two gated tests (two-sided Student t, PASS = mean > 0 and p <= alpha)

| test | n | mean R | SE | t | p | alpha | verdict |
|---|---|---|---|---|---|---|---|
| PRIMARY — book mean R | 130 | +0.758 | 0.177 | +4.29 | 3.4e-05 | 0.0253 | **PASS** |
| S1 — sub-9.5 band mean R | 275 | +0.523 | 0.103 | +5.05 | 8.0e-07 | 0.0253 | **PASS** |

S1 is **reported, not acted on** (standing ANGUS ruling — the floor stays 9.5 regardless; the era crossing already rejected floor 5).

S1 band per era:

| era | n | net | WR | mean R |
|---|---|---|---|---|
| 2025 | 153 | $+14,705 | 28% | +0.751 |
| 2026 | 122 | $+2,875 | 19% | +0.237 |

## Bucket profile (DESCRIPTIVE)

| bucket | n | share | WR | mean R | net | R 2025 | R 2026 |
|---|---|---|---|---|---|---|---|
| 08:00-08:30 | 36 | 28% | 22% | +0.349 | $+2,755 | +0.357 | +0.344 |
| 08:30-09:00 | 33 | 25% | 39% | +0.967 | $+7,505 | +0.988 | +0.954 |
| 09:00-09:30 | 42 | 32% | 36% | +1.252 | $+12,100 | +0.927 | +1.548 |
| 09:30-09:45 | 19 | 15% | 11% | +0.077 | $+305 | -0.278 | +0.565 |
