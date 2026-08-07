# PREREG — HTF MA census follow-on studies

This file pre-registers analyses on the Census A/B fit artifacts. It does NOT
authorize unsealing `output/sealed/` (SPEC §6.8 requires an explicit unseal
prereg; this is not one).

## E — the exit study (declared 2026-08-07, BEFORE the run)

ANGUS: the leads are hit-rate improvements on a half-basis-point proposition;
"the exit is the multiplier on all of it." Two rules from the trader, not from
a sweep — a two-trial study, not a search.

**Population.** Census B fit events, both arms separately: REJECT (entry =
event close at t) and BREAK-RETEST (entry = retest_px at the retest minute;
only retraced events). Initial stop in all arms: trigger-candle extreme ±1
tick. Costs: 0.5pt per round trip, converted to W per event. Session close
17:00 is the final exit everywhere.

**Declared cells (3):**
- **E1 TRAIL (the Tuesday rule):** after entry, each completed 15m bar whose
  close remains on the trade side of the as-of 15m BB MA ratchets the stop to
  that bar's adverse extreme (never backward). Exit at stop touch, filled at
  the stop level.
- **E2 / E3 PROGRESS-30 / PROGRESS-45 (the Wednesday rule):** if by minute
  M ∈ {30, 45} the trade has neither touched its first structural target nor
  reached +0.5W favorable excursion, exit at the close of minute M; otherwise
  hold to session close with the initial stop.

**Baselines (2):** B1 first-target-or-stop; B2 hold-to-close with initial stop.

**Metric.** Captured W per event, net (mean, median, p75), era × side × arm,
row-level AND cluster-collapsed. **Adoption bar:** a rule must beat BOTH
baselines on cluster-collapsed mean net capture in BOTH eras, per arm. No
undeclared variants; misses are reported as misses.

## Query results logged with this prereg (run before it, no bearing on E)

- Stratum sizes: BLOCKED = 21.6% / 23.0% of reject events (eras), 26.7% /
  29.9% of break-retests — a fifth to a third of the book, not a rounding
  error; the precision story is real.
- Circularity check: close_dist_bw survives constant-target-distance
  stratification — Q1→Q4 monotone WITHIN every target-distance tercile, both
  eras (mid/far: +23 to +32pp; near compressed by an 85-90% ceiling);
  corr(close_dist_bw, target_dist) = +0.115. NOT circular. Carrier confirmed.
- Findings 4 vs 5: corr(close_dist_bw, admissible) = +0.162 — distinct leads,
  one shared corner: in the top close_dist quartile admissibility stops
  mattering (76% vs 76%) — the decisive close has already cleared the field;
  elsewhere admissibility separates within every quartile (e.g. Q1: 63% vs
  40%). Two names, two findings, one overlapping corner.
- Placebo pattern (both censuses, 4 era-cells: small real edge over fake-line
  mean, p95 cleared nowhere): consistent with confluence-as-mechanism rather
  than line-identity — strengthens the case for a Census D (confluence), not
  a weaker model.
