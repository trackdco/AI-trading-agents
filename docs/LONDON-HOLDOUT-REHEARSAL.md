# London holdout — REHEARSAL on the fit span [rev2a]

**Config: rev 2a: 08:00-10:00 / V8 / no veto / no serialization.**

**This is not a result — it is the dress rehearsal: the same script, pointed at the fit span, gated on exact reproduction of every committed anchor.** The sealed run is `--span holdout --config rev2a --authorized-by "..."` with zero code changes.

## Items 1-8 — the book (flat 1 NQ lot)

| item | value |
|---|---|
| 1. trades / days with a take | 187 / 107 |
| 2. net P&L | $+22,795 |
| 3. win rate | 57% |
| 4. mean R | +0.513 |
| 5. maxDD (chronological, trade-level) | $2,550 |
| 6. months green | 11/14 |
| 7. worst month | $-1,108 (2026-02) |
| 8. trades per week | 3.2 |

Per era:

| era | n | net | WR | mean R | maxDD |
|---|---|---|---|---|---|
| 2025 | 78 | $+8,178 | 62% | +0.434 | $1,720 |
| 2026 | 109 | $+14,618 | 53% | +0.570 | $2,550 |

## Item 9 — W/FAR lift (floor-passing candidates, either vs neither)

| slice | either n | either R | neither n | neither R | lift |
|---|---|---|---|---|---|
| pooled | 213 | +0.483 | 671 | -0.076 | **+0.559** |
| 2025 | 80 | +0.398 | 310 | -0.046 | **+0.444** |
| 2026 | 133 | +0.535 | 361 | -0.102 | **+0.637** |

## Item 10 / S2 — the either cell split (DESCRIPTIVE, no inference)

both W+FAR: n=133, mean R +0.682 · exactly one: n=54, mean R +0.096

Prereg §4: no decision may be taken on this number in this run — doing so retroactively makes the family 3 tests.

## The two gated tests (two-sided Student t, PASS = mean > 0 and p <= alpha)

| test | n | mean R | SE | t | p | alpha | verdict |
|---|---|---|---|---|---|---|---|
| PRIMARY — book mean R | 187 | +0.513 | 0.115 | +4.47 | 1.4e-05 | 0.0253 | **PASS** |
| S1 — sub-9.5 band mean R | 300 | +0.590 | 0.111 | +5.33 | 1.9e-07 | 0.0253 | **PASS** |

S1 is **reported, not acted on** (standing ANGUS ruling — the floor stays 9.5 regardless; the era crossing already rejected floor 5).

S1 band per era:

| era | n | net | WR | mean R |
|---|---|---|---|---|
| 2025 | 164 | $+18,746 | 61% | +0.904 |
| 2026 | 136 | $+3,085 | 39% | +0.211 |

## Bucket profile (DESCRIPTIVE)

| bucket | n | share | WR | mean R | net | R 2025 | R 2026 |
|---|---|---|---|---|---|---|---|
| 08:00-08:30 | 45 | 24% | 60% | +0.371 | $+4,722 | +0.159 | +0.488 |
| 08:30-09:00 | 55 | 29% | 67% | +0.759 | $+10,215 | +0.977 | +0.625 |
| 09:00-09:30 | 44 | 24% | 57% | +0.734 | $+6,864 | +0.477 | +0.970 |
| 09:30-10:00 | 43 | 23% | 40% | +0.119 | $+994 | +0.038 | +0.190 |
