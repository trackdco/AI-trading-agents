# London holdout — THE sealed 2023/24 run [rev3] (opens once)

**Config: rev 3: 08:00-09:45 / V1 BE@1R / score-0 veto (frozen literals) / one-position-at-a-time.**

**Authorized by: ANGUS, 2026-07-31 (verbal, in person; relayed by Brake).** Prereg: `docs/LONDON-PREREGISTRATION.md` rev 2a + the signed revision (`docs/LONDON-REV3-BUNDLE.md` if rev3). Two gated tests at Sidak alpha 0.0253. Declared resolution: a near-miss on mean R +0.48 is not decay; a sign flip is.

## Items 1-8 — the book (flat 1 NQ lot)

| item | value |
|---|---|
| 1. trades / days with a take | 56 / 38 |
| 2. net P&L | $+740 |
| 3. win rate | 18% |
| 4. mean R | +0.134 |
| 5. maxDD (chronological, trade-level) | $2,115 |
| 6. months green | 2/6 |
| 7. worst month | $-905 (2024-04) |
| 8. trades per week | 0.8 |

(Under rev 3 the WR optic is structural, not a health metric: V1 scratches ~40% of trades at BE, so wins concentrate — mean R and net are the health metrics.)

Per era:

| era | n | net | WR | mean R | maxDD |
|---|---|---|---|---|---|
| 2023 | 14 | $-485 | 14% | -0.125 | $1,030 |
| 2024 | 42 | $+1,225 | 19% | +0.220 | $2,115 |

## Item 9 — W/FAR lift (floor-passing candidates, either vs neither)

| slice | either n | either R | neither n | neither R | lift |
|---|---|---|---|---|---|
| pooled | 74 | +0.135 | 237 | -0.167 | **+0.302** |
| 2023 | 17 | -0.104 | 64 | -0.129 | **+0.025** |
| 2024 | 57 | +0.206 | 173 | -0.181 | **+0.388** |

## Item 10 / S2 — the either cell split (DESCRIPTIVE, no inference)

both W+FAR: n=38, mean R +0.159 · exactly one: n=18, mean R +0.081

Prereg §4: no decision may be taken on this number in this run — doing so retroactively makes the family 3 tests.

## The two gated tests (two-sided Student t, PASS = mean > 0 and p <= alpha)

| test | n | mean R | SE | t | p | alpha | verdict |
|---|---|---|---|---|---|---|---|
| PRIMARY — book mean R | 56 | +0.134 | 0.167 | +0.80 | 0.4278 | 0.0253 | **FAIL** |
| S1 — sub-9.5 band mean R | 146 | +0.560 | 0.125 | +4.49 | 1.4e-05 | 0.0253 | **PASS** |

S1 is **reported, not acted on** (standing ANGUS ruling — the floor stays 9.5 regardless; the era crossing already rejected floor 5).

S1 band per era:

| era | n | net | WR | mean R |
|---|---|---|---|---|
| 2023 | 53 | $+1,925 | 21% | +0.341 |
| 2024 | 93 | $+7,920 | 30% | +0.685 |

## Bucket profile (DESCRIPTIVE)

| bucket | n | share | WR | mean R | net | R 2023 | R 2024 |
|---|---|---|---|---|---|---|---|
| 08:00-08:30 | 25 | 45% | 28% | +0.415 | $+2,395 | -0.002 | +0.547 |
| 08:30-09:00 | 11 | 20% | 9% | -0.201 | $-1,145 | -0.357 | -0.142 |
| 09:00-09:30 | 18 | 32% | 11% | +0.012 | $-235 | -0.159 | +0.061 |
| 09:30-09:45 | 2 | 4% | 0% | -0.453 | $-275 | -0.024 | -0.881 |

If the late window is again the weakest here — on data owing nothing to the fit-side analysis — that is properly evidenced grounds for the window question, later, on its own prereg.
