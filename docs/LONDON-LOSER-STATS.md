# London loser stats — the 40 losers of the working stack (cut@09:30 + veto + one-at-a-time, 110 trades)

**FIT ONLY. Sealed untouched. Descriptive unless a row clears its charge; patterns found here are declared priors, not rules.**

## 1. What a loss looks like

- 40 losers / 110 trades (36%). Exit reasons: {'stop': 37, 'partial+stop': 3}
- Loss size: mean -0.78R / $-229, worst -1.03R / $-735. 25 of 40 are full stops.
- Speed: median loser dies in 8 min vs 12 min for winners; 17/40 losers are gone within 3 minutes of fill.
- Eras: 2025 16 losers of 46 trades; 2026 24 of 64.

## 2. Where the losers live (share of each cell that loses)

**bucket**

| value | trades | losers | loss rate | cell net |
|---|---|---|---|---|
| 08:00-08:30 | 35 | 13 | 37% | $+3,176 |
| 08:30-09:00 | 37 | 13 | 35% | $+6,552 |
| 09:00-09:30 | 38 | 14 | 37% | $+8,212 |

**tf**

| value | trades | losers | loss rate | cell net |
|---|---|---|---|---|
| 1min | 14 | 7 | 50% | $+1,579 |
| 2min | 21 | 8 | 38% | $+4,750 |
| 3min | 37 | 12 | 32% | $+5,591 |
| 5min | 38 | 13 | 34% | $+6,021 |

**pattern**

| value | trades | losers | loss rate | cell net |
|---|---|---|---|---|
| A | 10 | 5 | 50% | $+856 |
| B | 52 | 19 | 37% | $+7,286 |
| B2 | 48 | 16 | 33% | $+9,799 |

**direction**

| value | trades | losers | loss rate | cell net |
|---|---|---|---|---|
| long | 54 | 18 | 33% | $+7,951 |
| short | 56 | 22 | 39% | $+9,990 |

**htf_flag**

| value | trades | losers | loss rate | cell net |
|---|---|---|---|---|
| counter_trend | 37 | 17 | 46% | $+5,024 |
| range | 44 | 15 | 34% | $+7,441 |
| with_trend | 29 | 8 | 28% | $+5,476 |

**wall**: both 30/83 lose (36%) vs exactly-one 10/27 (37%)

## 3. Clustering

- Longest losing streak (chronological): 4 trades.
- Red days: 26/80 (32%), mean red day $-267, worst $-735. Multi-loss days (2+ losers): 5.
- Month with most losers: 2026-03 (10).

## 4. Loser-vs-winner discriminators (23 declared features; AUC = P(loser value > winner value); charged worst-of-23)

| feature | AUC | 2025 AUC | 2026 AUC | p(worst-of-K) | consistent? |
|---|---|---|---|---|---|
| ent_vs_vwap_sd_dir | 0.380 | 0.329 | 0.412 | 0.454 | YES |
| room_ahead | 0.593 | 0.675 | 0.537 | 0.822 | YES |
| confluence_count | 0.430 | 0.346 | 0.492 | 0.985 | YES |
| lvl_churn_30 | 0.431 | 0.485 | 0.398 | 0.986 | YES |
| dep_support | 0.434 | 0.409 | 0.431 | 0.990 | YES |
| indec_30 | 0.563 | 0.669 | 0.486 | 0.994 | no |
| vwap_cross_30 | 0.442 | 0.439 | 0.441 | 0.998 | YES |
| dep_thick | 0.455 | 0.477 | 0.420 | 1.000 | YES |
| dep_spread | 0.544 | 0.590 | 0.517 | 1.000 | YES |
| dep_imb | 0.459 | 0.409 | 0.478 | 1.000 | YES |
| on_extreme_age | 0.467 | 0.453 | 0.476 | 1.000 | YES |
| wicky_10 | 0.522 | 0.542 | 0.506 | 1.000 | YES |

(Top 12 of 23 by |AUC-0.5| shown; all 23 were in the null. AUC > 0.5 = losers have MORE of it; < 0.5 = losers have less. 0.5 = no information.)
