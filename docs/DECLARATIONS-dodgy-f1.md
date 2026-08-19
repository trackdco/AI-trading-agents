# DECLARATIONS — F1, "big overnight move ⇒ choppy New York AM"

Written and committed **before** `scripts/dodgy_f1.py` is run.

**His claim** (`RESEARCH-dodgysdd-lecture.md` F1, class A): *"big overnight move equals
choppy or sideways New York AM session"*, quantified as *"anything above like 300 points is
pretty substantial."*

This needs no entry model, which is why it survived the refutation of everything else. It
is the last cheap item on the board.

## 1 — Windows

- **Overnight**: 18:00 → 08:30 ET, measured as hours elapsed since each session's 18:00
  open (DST-safe, same binning validated in `FINDINGS-dodgy-htf-nest.md`).
- **New York AM**: 08:30 → 11:00 ET — his K2 window and the operator's restriction.

## 2 — The measure, and the confound it exists to avoid

**"Choppy" is his word and he never defines it. The measure must be scale-free, and that
is not a stylistic preference — it is the whole validity of the test.** Overnight range and
NY-AM range are both driven by the day's volatility, and volatility clusters. A raw
NY-AM-range measure would therefore find that big overnight moves precede big NY-AM ranges,
which is volatility autocorrelation and says nothing about chop.

| | measure | role |
|---|---|---|
| **primary** | **efficiency ratio** = \|last−first\| / Σ\|Δclose\| over NY AM 1m closes | scale-free; low = choppy. This is the pre-declared test of F1 |
| secondary | range realisation = \|last−first\| / (high−low) over NY AM | scale-free; low = sideways |
| diagnostic | raw NY-AM range in points | reported **to expose the volatility confound**, not as evidence either way |

**Only the efficiency ratio decides F1.** The other two are reported so the confound is
visible rather than hidden.

## 3 — Arms

1. **Spearman(overnight range, NY-AM efficiency)** across all session days, bootstrapped
   over days. This is the single cleanest statistic and it needs no threshold.
2. **His threshold**: overnight range ≥ 300 points [A] vs below.
3. **A decile sweep** of overnight range, because a gradient is more informative than a
   binary split and guards against a threshold that happens to land well.
4. **Era halves** on the threshold split (E1.4).

## 4 — A problem with his threshold, recorded in advance

**300 points is a fixed number on an index that roughly doubled across this sample.** It is
~2.7% of NQ at 11,000 in early 2023 and ~1.2% at 25,000 in 2026, so the same rule selects a
drifting and non-comparable set of days. His threshold is therefore run as stated **and**
alongside a percentile-matched version, so the two can be separated.

## 5 — PREDICTIONS

1. **Spearman will be positive, not negative — refuting him.** Directional efficiency
   tends to be *higher* on high-volatility days, because trend days are volatile days. I
   expect big overnight moves to precede *more* directional NY AM sessions, not choppier
   ones. Stated plainly so it cannot be reinterpreted after the fact.
2. **His 300-point threshold will select at least twice the share of days in H2 as in H1**,
   purely from index drift.
3. **Raw NY-AM range will rise strongly with overnight range.** This is the confound, and
   it is *not* evidence for or against F1.
4. **Whatever the sign, the effect will be small** relative to day-to-day variance — an
   efficiency difference under 0.05 between the extreme deciles.

## 6 — Decision rule

- **Spearman clears zero on the negative side, AND the ≥300 split shows lower efficiency,
  AND it holds in both era halves** → **F1 CONFIRMED.** It would be the first confirmed
  claim in the entire audit, and would be reported as such.
- **Interval spans zero** → no relationship; F1 unsupported.
- **Clears zero on the positive side** → F1 **refuted with its sign reversed**, which is a
  stronger result than a null and must be reported that way.

## 7 — What this cannot establish

F1 is a claim about market state, not about trades. Confirming it would not make any book
profitable; it would mean he has correctly described a regime relationship. Given that
`FINDINGS-dodgy-htf-nest.md` refuted the model itself, F1's only remaining value is as a
check on whether his *observations* are sound even where his *edge* is not.
