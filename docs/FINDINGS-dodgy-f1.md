# FINDINGS — F1, "big overnight move ⇒ choppy NY AM": unsupported, but the closest he came

Run against `DECLARATIONS-dodgy-f1.md`, committed before the run (`77c66d8`).
NQ, 1,251,240 bars → **910 usable session days**, 2023-01-02 → 2026-07-14. Seed 20260819,
4,000 bootstrap resamples over days.

**His claim:** *"big overnight move equals choppy or sideways New York AM session"*, and
*"anything above like 300 points is pretty substantial."*

## 0 — Pre-registering the measure was the whole test

The declaration named the efficiency ratio as the only measure that decides F1, because
overnight range and NY-AM range are both driven by the day's volatility, and volatility
clusters. That was not a formality:

| relationship | Spearman ρ | 95% CI |
|---|---|---|
| overnight range vs **NY-AM efficiency** *(the declared measure)* | **+0.019** | [−0.042, +0.085] |
| overnight range vs **raw NY-AM range** *(the confound)* | **+0.565** | [+0.516, +0.611] |

**Had raw range been used as the measure, this document would report a massive
relationship — and it would be volatility autocorrelation, not chop.** ρ = +0.57 against
ρ = +0.02 on the same days is the entire difference between a scale-free measure and a
scale-dependent one.

## 1 — The primary statistic: nothing

| | ρ | 95% CI | verdict |
|---|---|---|---|
| overnight range in **points** vs efficiency | +0.0194 | [−0.0418, +0.0846] | spans zero |
| overnight range as **% of price** vs efficiency | −0.0053 | [−0.0698, +0.0597] | spans zero |

Threshold-free, and it finds no relationship in either scaling. **The two scalings do not
even agree on the sign.**

## 2 — And no dose-response, which is the strongest evidence against

If the mechanism were real, efficiency should decline as the overnight move grows. It does
not move at all:

| decile | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| median overnight range (pt) | 60 | 82 | 95 | 111 | 127 | 146 | 175 | 214 | 290 | 418 |
| **NY-AM efficiency** | .093 | .087 | .097 | .085 | .102 | .089 | .097 | .104 | .098 | .085 |
| mean NY-AM range (pt) | 120 | 134 | 158 | 173 | 169 | 187 | 199 | 241 | 274 | 344 |

**Efficiency is flat and non-monotone across a 7× span of overnight range.** The bottom
decile (0.093) and the top (0.085) differ by 0.008 — and decile 4, at 0.085, matches the
top decile exactly. Meanwhile the raw-range row climbs monotonically from 120 to 344, which
is the confound doing precisely what the declaration predicted.

## 3 — The threshold splits: every point estimate leans his way, none of it holds

| arm | n big | n rest | eff big | eff rest | difference | 95% CI | verdict |
|---|---|---|---|---|---|---|---|
| his 300pt [A], pooled | 131 | 779 | 0.0854 | 0.0952 | **−0.0098** | [−0.0214, **+0.0021**] | spans zero |
| top quartile, points | 229 | 681 | 0.0916 | 0.0946 | −0.0030 | [−0.0129, +0.0074] | spans zero |
| top quartile, % of price | 228 | 682 | 0.0882 | 0.0957 | −0.0075 | [−0.0168, +0.0022] | spans zero |
| **his 300pt · H2 only** | 121 | 334 | 0.0835 | 0.1009 | **−0.0174** | [−0.0307, **−0.0038**] | **choppier — his claim** |
| his 300pt · H1 only | **10** | — | — | — | — | — | **untestable** |
| top quartile pts · H2 | 114 | 341 | — | — | −0.0162 | [−0.0298, −0.0027] | choppier |
| top quartile % · H2 | 114 | 341 | — | — | −0.0091 | [−0.0233, +0.0051] | spans zero |
| top quartile pts · H1 | 114 | 341 | — | — | −0.0043 | [−0.0189, +0.0097] | spans zero |
| top quartile % · H1 | 114 | 341 | — | — | −0.0064 | [−0.0201, +0.0073] | spans zero |

**In fairness to him: all eight testable point estimates are negative — his direction, 8
for 8.** That deserves stating plainly, and then immediately qualifying: these arms are
nested subsets of the same 910 days, so their agreement is close to automatic and carries
nothing like the weight of eight independent tests. A sign test would be invalid here and
is not offered.

**The one cell that clears does not survive scrutiny.** H2 at −0.0174 clears on the
**points** threshold and fails on the **% of price** threshold (−0.0091, spans zero) over
almost the same number of days. Within-era Spearman spans zero in both halves (H1 −0.028,
H2 −0.021). A result that appears on one scaling, in one era half, with no gradient behind
it, is not a finding.

## 4 — His threshold is not a rule, it is a date

Recorded in declaration §4 before the run, and it came in far worse than predicted:

| | median NQ level | median overnight range | **days clearing 300pt** |
|---|---|---|---|
| H1 (2023 → mid-2024) | 15,893 | 106.5 pt (0.66%) | **2.2%** |
| H2 (mid-2024 → 2026) | 23,613 | 196.8 pt (0.83%) | **26.6%** |

**A twelve-fold difference.** I predicted at least 2×. On a index that went from ~11,000 to
~25,000, "above 300 points" selects one day in forty-five early in the sample and one day in
four late in it. **E1.4 both-era clearance is not merely unmet for his threshold — it is
structurally impossible, because H1 contains only 10 qualifying days.** Any fixed-point
threshold quoted by a trader has this problem and it is worth carrying forward as a general
caution: it is a rule that silently becomes a different rule as price levels drift.

## 5 — Predictions, scored

| # | prediction | outcome |
|---|---|---|
| 1 | Spearman **positive**, refuting him | **WRONG** — it is a null (+0.019 pts, −0.005 %), not a reversal. I over-predicted the volatility/trend link |
| 2 | 300pt selects ≥2× the share of days in H2 vs H1 | **CONFIRMED, by 12×** |
| 3 | raw NY-AM range rises strongly with overnight range | **CONFIRMED** — ρ +0.565 |
| 4 | extreme-decile efficiency difference under 0.05 | **CONFIRMED** — 0.008 |

## 6 — Decision rule, applied

§6: *"Interval spans zero → no relationship; F1 unsupported."* That is the branch. The
primary statistic spans zero in both scalings, there is no dose-response, and the single
clearing cell fails under rescaling.

**F1 is unsupported. It is not refuted with a reversed sign either** — unlike the news-wick
claim, whose premise ran backwards. The honest verdict is a null with a consistent
directional lean too weak to distinguish from noise.

**This is the closest any claim in the audit came to confirming**, and it is worth saying
why that is faint praise: F1 is a statement about market state, not about trades.
Confirming it would not have made any book profitable. Its only value was as a check on
whether his *observations* are sound where his *edge* is not, and the answer is that this
one is directionally plausible and quantitatively unsupported — with a threshold that
drifts out from under it.
