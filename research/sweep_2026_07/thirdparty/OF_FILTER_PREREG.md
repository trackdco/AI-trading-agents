# PRE-REGISTRATION — does order flow refine the Currency-Pros entries?
### Written and committed BEFORE any filtered outcome was computed. 2026-08-03.

**Question (Brake).** The strategy tests as a coin flip (24.2% WR against a 25.0% geometric
breakeven). Would taking only the setups that ALIGN with order flow — heatmap, CVD, or delta
divergence — lift it above breakeven?

**Prior, stated honestly.** Order flow at entry has been tested five ways in this project and
returned null every time (Q1, Q2-beyond-gap, exit-side flow, the 13-feature confluence
composite, entry-candle features). BUT all five were run on canon trades whose selection already
contained order-flow-derived checks. The CP strategy contains none, so there is genuinely more
room here. That is why this is worth running rather than assuming.

**Sample (frozen).** CP primary cell = NY RTH 09:30-16:00, fib 0.75, score >= 3. Restricted to
footprint-tape coverage (2025-06-01 onward): **n = 465 trades over 209 days**. The heatmap
sub-test is further restricted to depth-file hours (08:00-10:29 ET), giving **n = 210**, and
that reduced count is reported next to every heatmap number.

**The three filters — exactly the three asked about, no others, no thresholds swept.**
1. **CVD aligned** — `cvd_15 * direction > 0`. Sign only. No magnitude threshold, so there is
   nothing to tune.
2. **Delta divergence present** — `sign(price change over 15 min) != sign(cvd_15)`, both
   non-zero. The textbook reversal confirmation, appropriate because every CP entry is a
   retracement entry.
3. **Heatmap wall ahead** — at the fill-minus-one depth snapshot (strictly pre-fill), the
   largest resting level on the target side exists within the visible book.
4. **All three combined** (on the depth-covered subset).

All features are computed **strictly before the fill minute**. The tape is source-band-cleaned
to the ET-day bar band +/-25pt, the same convention registered and used throughout this project.

**Metric (frozen).** Win rate of the FILTERED subset against the geometry-forced breakeven of
**25.0%**. Mean R reported alongside. The payoff is fixed at 3.00R, so win rate is the whole
question.

**Inference (frozen).** One-sided binomial against 25.0%; day-clustered bootstrap 95% CI
(4,000 draws); and a 2,000-draw day-block permutation of the outcome labels holding the filter
fixed, which asks whether an equally sized day-blocked subset drawn at random does as well.

**Multiplicity.** Four tests, Sidak family-wise alpha = 1-0.95^(1/4) = **0.0127**.

**Built-in falsifier.** For each filter the COMPLEMENT (anti-aligned trades) is reported. If a
filter carries information, its complement must do worse. If aligned and anti-aligned perform
the same, the filter is noise regardless of its own p-value.

**Decision rule (frozen).** A filter is called useful only if the filtered win rate beats 25.0%
at p < 0.0127 **and** its day-clustered CI excludes 25.0% **and** its complement is worse.
Anything else is reported as no improvement. Cells under 30 trades are marked insufficient,
since at a 25% base rate fewer than 30 trades cannot separate 25% from 40%.
