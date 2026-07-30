# London conviction map — grading the taken trades (cut@09:30 baseline)

**FIT ONLY. Sealed 2023/24 untouched. Sizing overlay, not a gate — nothing here ships before the holdout validates the book and Angus lifts the flat-1-lot ruling.** Full-book (187) robustness column included throughout; a cell that only works on one baseline is labelled fragile.

Baseline: **144 trades, WR 62%, mean R +0.630** (2025: 58/66%/+0.57 · 2026: 86/59%/+0.67). Cell format: n | WR | mean R | Wilson-95 LB on WR | per-era n/WR/R.

## 1. The two PRIOR cells (declared in prereg §3 before this sweep — charged at their own k=2, not at today's breadth)

| cell | n | WR | mean R | Wilson LB | 2025 | 2026 | grade |
|---|---|---|---|---|---|---|---|
| dep_resist>33 & ASIA==0 | 12 | 67% | +0.810 | 39% | 6/67%/+0.80 | 6/67%/+0.82 | below-floor |
| cvd_ASIA>737 & wall_above_sz>5 | 11 | 100% | +1.237 | 74% | 7/100%/+1.51 | 4/100%/+0.77 | below-floor |

(Thresholds verbatim from the L3 trial via prereg §3 — raw columns, not direction-adjusted, exactly as originally declared.)

## 2. Univariate sweep — 22 declared features, split at the book median, hi-cell vs book

Every p below is CORRECTED: the observed lift is compared to the distribution of the WORST lift across all 22 features under within-era outcome shuffles (N=5000). Coverage-dropped (<95%): cvd_ASIA, cvd_ON_sofar, d5, d15, d30, fill_delta, deltaz_15, churn_flow_30, fill_vol_rel.

| feature (hi half) | n | WR | mean R | Wilson LB | 2025 | 2026 | lift | p(worst-of-K) | era-consistent | grade |
|---|---|---|---|---|---|---|---|---|---|---|
| vwap_cross_30 | 51 | 71% | +0.819 | 57% | 17/71%/+0.44 | 34/71%/+1.01 | +0.188 | 0.980 | no | hypothesis |
| on_extreme_age | 72 | 65% | +0.805 | 54% | 25/68%/+0.51 | 47/64%/+0.96 | +0.174 | 0.990 | no | CALLABLE |
| dep_spread | 54 | 63% | +0.799 | 50% | 11/73%/+0.88 | 43/60%/+0.78 | +0.169 | 0.995 | YES | hypothesis |
| dep_thick | 65 | 69% | +0.775 | 57% | 35/71%/+0.80 | 30/67%/+0.74 | +0.144 | 1.000 | YES | CALLABLE |
| rng_30 | 72 | 61% | +0.773 | 50% | 21/62%/+0.50 | 51/61%/+0.88 | +0.143 | 1.000 | no | hypothesis |
| lvl_churn_30 | 57 | 65% | +0.759 | 52% | 21/71%/+0.66 | 36/61%/+0.82 | +0.129 | 1.000 | YES | hypothesis |
| dep_resist | 71 | 66% | +0.749 | 55% | 43/67%/+0.69 | 28/64%/+0.84 | +0.118 | 1.000 | YES | CALLABLE |
| dep_sup_m_res (signed) | 61 | 59% | +0.717 | 46% | 21/67%/+0.61 | 40/55%/+0.77 | +0.087 | 1.000 | YES | hypothesis |
| trigdens_30 | 71 | 61% | +0.696 | 49% | 33/67%/+0.66 | 38/55%/+0.72 | +0.065 | 1.000 | YES | CALLABLE |
| confluence_count | 40 | 70% | +0.681 | 55% | 19/89%/+1.04 | 21/52%/+0.36 | +0.051 | 1.000 | no | hypothesis |
| on_range | 70 | 61% | +0.673 | 50% | 23/57%/+0.51 | 47/64%/+0.75 | +0.043 | 1.000 | no | hypothesis |
| dep_imb (signed) | 72 | 62% | +0.668 | 51% | 25/68%/+0.57 | 47/60%/+0.72 | +0.038 | 1.000 | no | CALLABLE |
| wicky_10 | 72 | 62% | +0.659 | 51% | 30/60%/+0.39 | 42/64%/+0.85 | +0.029 | 1.000 | no | CALLABLE |
| indec_30 | 51 | 61% | +0.657 | 47% | 23/52%/+0.23 | 28/68%/+1.01 | +0.027 | 1.000 | no | hypothesis |
| vwap_slope_30 (signed) | 72 | 67% | +0.652 | 55% | 33/67%/+0.49 | 39/67%/+0.79 | +0.021 | 1.000 | no | CALLABLE |
| ent_vs_vwap_sd_dir | 72 | 69% | +0.632 | 58% | 25/80%/+0.79 | 47/64%/+0.55 | +0.002 | 1.000 | no | CALLABLE |
| netpath_30 (signed) | 72 | 67% | +0.621 | 55% | 33/67%/+0.50 | 39/67%/+0.72 | -0.009 | 1.000 | no | CALLABLE |
| room_ahead | 72 | 56% | +0.586 | 44% | 31/52%/+0.25 | 41/59%/+0.84 | -0.044 | 1.000 | no | CALLABLE |
| dep_support | 63 | 65% | +0.563 | 53% | 33/67%/+0.55 | 30/63%/+0.58 | -0.067 | 1.000 | YES | CALLABLE |
| dep_thick_d5m | 66 | 61% | +0.554 | 49% | 27/70%/+0.61 | 39/54%/+0.52 | -0.076 | 1.000 | no | CALLABLE |
| bbw_state | 71 | 61% | +0.513 | 49% | 32/59%/+0.34 | 39/62%/+0.66 | -0.118 | 1.000 | YES | CALLABLE |
| risk | 72 | 58% | +0.371 | 47% | 26/65%/+0.64 | 46/54%/+0.22 | -0.260 | 0.758 | no | CALLABLE |

## 3. Pair cells — hi&hi among the 6 era-consistent positive features (12 pairs with pooled n>=20; charged worst-of-12)

| cell | n | WR | mean R | Wilson LB | 2025 | 2026 | lift | p(worst-of-K) | grade |
|---|---|---|---|---|---|---|---|---|---|
| dep_spread & dep_sup_m_res | 25 | 68% | +1.294 | 48% | 6/67%/+0.92 | 19/68%/+1.41 | +0.664 | 0.121 | below-floor |
| dep_sup_m_res & trigdens_30 | 31 | 65% | +1.051 | 47% | 12/67%/+0.60 | 19/63%/+1.34 | +0.420 | 0.650 | hypothesis |
| dep_thick & trigdens_30 | 33 | 70% | +1.019 | 53% | 19/74%/+1.00 | 14/64%/+1.05 | +0.388 | 0.736 | hypothesis |
| dep_spread & lvl_churn_30 | 26 | 62% | +0.913 | 43% | 5/60%/+0.33 | 21/62%/+1.05 | +0.282 | 0.941 | below-floor |
| dep_resist & trigdens_30 | 41 | 63% | +0.807 | 48% | 26/65%/+0.77 | 15/60%/+0.87 | +0.176 | 0.998 | hypothesis |
| lvl_churn_30 & dep_sup_m_res | 24 | 54% | +0.780 | 35% | 4/50%/+0.06 | 20/55%/+0.92 | +0.149 | 1.000 | below-floor |
| lvl_churn_30 & trigdens_30 | 29 | 62% | +0.766 | 44% | 14/64%/+0.58 | 15/60%/+0.94 | +0.136 | 1.000 | hypothesis |
| dep_thick & dep_resist | 54 | 67% | +0.764 | 53% | 34/71%/+0.76 | 20/60%/+0.76 | +0.133 | 1.000 | hypothesis |
| lvl_churn_30 & dep_resist | 23 | 65% | +0.745 | 45% | 16/69%/+0.70 | 7/57%/+0.85 | +0.114 | 1.000 | below-floor |
| dep_thick & dep_sup_m_res | 27 | 63% | +0.740 | 44% | 13/69%/+0.80 | 14/57%/+0.69 | +0.109 | 1.000 | hypothesis |
| dep_spread & trigdens_30 | 26 | 62% | +0.715 | 43% | 7/71%/+0.57 | 19/58%/+0.77 | +0.085 | 1.000 | below-floor |
| dep_resist & dep_sup_m_res | 28 | 54% | +0.533 | 36% | 15/60%/+0.55 | 13/46%/+0.51 | -0.098 | 1.000 | hypothesis |

## 4. Categorical splits (descriptive — no inference, tiny cells)

**pattern**

| value | n | WR | mean R | 2025 | 2026 |
|---|---|---|---|---|---|
| A | 11 | 45% | +0.383 | 6/33%/+0.22 | 5/60%/+0.57 |
| B | 74 | 58% | +0.425 | 32/66%/+0.50 | 42/52%/+0.37 |
| B2 | 59 | 69% | +0.934 | 20/75%/+0.79 | 39/67%/+1.01 |

**kind**

| value | n | WR | mean R | 2025 | 2026 |
|---|---|---|---|---|---|
| displacement | 85 | 56% | +0.420 | 38/61%/+0.46 | 47/53%/+0.39 |
| rejection_block | 59 | 69% | +0.934 | 20/75%/+0.79 | 39/67%/+1.01 |

**htf_flag**

| value | n | WR | mean R | 2025 | 2026 |
|---|---|---|---|---|---|
| counter_trend | 51 | 55% | +0.606 | 15/53%/+0.51 | 36/56%/+0.65 |
| range | 52 | 65% | +0.698 | 23/70%/+0.57 | 29/62%/+0.80 |
| with_trend | 41 | 66% | +0.575 | 20/70%/+0.61 | 21/62%/+0.54 |

**tf**

| value | n | WR | mean R | 2025 | 2026 |
|---|---|---|---|---|---|
| 1min | 17 | 41% | +0.321 | 7/57%/+0.42 | 10/30%/+0.25 |
| 2min | 27 | 63% | +0.813 | 12/58%/+0.51 | 15/67%/+1.06 |
| 3min | 44 | 64% | +0.506 | 17/76%/+0.72 | 27/56%/+0.37 |
| 5min | 56 | 66% | +0.734 | 22/64%/+0.54 | 34/68%/+0.86 |

**direction**

| value | n | WR | mean R | 2025 | 2026 |
|---|---|---|---|---|---|
| long | 74 | 66% | +0.633 | 34/65%/+0.47 | 40/68%/+0.77 |
| short | 70 | 57% | +0.628 | 24/67%/+0.71 | 46/52%/+0.58 |

## 5. The wall split on this baseline (tier-test axis, re-anchored to cut@09:30)

| cell | n | WR | mean R | Wilson LB | 2025 | 2026 | grade |
|---|---|---|---|---|---|---|---|
| both W+FAR | 102 | 63% | +0.759 | 53% | 37/65%/+0.71 | 65/62%/+0.79 | CALLABLE |
| exactly one | 42 | 60% | +0.319 | 44% | 21/67%/+0.33 | 21/52%/+0.31 | hypothesis |

## 6. Conviction score — count of surviving conditions (3 CALLABLE era-consistent positive: dep_thick, dep_resist, trigdens_30) + both-wall

| score | n | WR | mean R | net | 2025 | 2026 |
|---|---|---|---|---|---|---|
| 0 | 11 | 36% | +0.029 | $-442 | 3/33%/-0.55 | 8/38%/+0.24 |
| 1 | 37 | 65% | +0.499 | $+5,385 | 9/67%/+0.24 | 28/64%/+0.58 |
| 2 | 34 | 59% | +0.711 | $+4,672 | 9/67%/+0.66 | 25/56%/+0.73 |
| 3 | 44 | 66% | +0.631 | $+7,098 | 27/67%/+0.54 | 17/65%/+0.78 |
| 4 | 18 | 67% | +1.113 | $+5,089 | 10/70%/+1.21 | 8/62%/+0.99 |

### Ladder pricing at matched total risk (flat book risk = the budget)

Zero-edge column = same weights applied to outcome-shuffled trades (mean of 5000 within-era shuffles): a ladder must beat flat on REAL outcomes by more than it does on shuffled ones, or it is just risk-shuffling.

| ladder | net | maxDD (trade) | net/maxDD | zero-edge net |
|---|---|---|---|---|
| flat 1.0 | $+21,801 | $1,435 | 15.2 | $+21,801 |
| 0.5-2.0 by score | $+25,200 | $1,479 | 17.0 | $+22,296 |
| 1.5/0.5 both-wall only | $+25,168 | $1,640 | 15.4 | $+21,931 |

## 7. Robustness — same survivors measured on the FULL 08:00-10:00 book

| condition | cut book (n/WR/R) | full book (n/WR/R) | fragile? |
|---|---|---|---|
| dep_thick hi | 65/69%/+0.77 | 76/66%/+0.65 | no |
| dep_resist hi | 71/66%/+0.75 | 84/64%/+0.69 | no |
| trigdens_30 hi | 71/61%/+0.70 | 88/56%/+0.59 | no |

## Read this before quoting any cell

- 144 trades split four ways is 30-40 per cell POOLED — nearly every pair cell is hypothesis-grade by the project's own 25/era floor. A 70% WR on n=30 carries a Wilson-95 lower bound near 52%. The map is for DECLARING priors the holdout and forward data can judge, not for claiming edges today.
- Sizing is frozen at flat 1 lot (ANGUS ruling) until the holdout validates the book. The ladder above is the declared candidate for the post-holdout sizing decision, alongside the tier test's 1.5/0.5.
- This sweep consumed fit-side search breadth and was charged for it; worst-of-K nulls on a 144-trade book are brutal, and that is correct.
