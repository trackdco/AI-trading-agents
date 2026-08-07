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

## E — RESULT (run 2026-08-07, read against the declared bar)

4,272 events. Cluster-collapsed captured W net, (B1 tgt / B2 hold / E1 trail /
E2 p30 / E3 p45):

- reject H2-2025: -0.026 / -0.068 / -0.023 / -0.058 / -0.062
- reject H1-2026: -0.014 / +0.010 / +0.008 / +0.004 / +0.009
- break  H2-2025: +0.008 / -0.031 / -0.017 / -0.035 / -0.032
- break  H1-2026: +0.030 / +0.017 / +0.018 / +0.023 / +0.019

**ADOPTION: NONE.** E1 wins reject-2025 but loses to B2 in 2026 by 0.002W;
E2/E3 beat nothing consistently; on the break arm B1 (first-target-or-stop)
is best in BOTH eras — no E rule tops it. Misses reported as misses.

**The finding above the misses:** the entire 5-exit × 2-arm × 2-era surface
lives within ±0.07W net. The raw M2 book is fairly priced under every exit
tested — the travel tail exists (p95 ~4-5W) but no unconditioned exit
converts it. The exit is a multiplier on the SELECTED book, not a rescue of
the raw one: selection (close_dist_bw, admissibility, break-branch) must move
the base off zero first. Convention note (not an edge claim): break-retest
pairs naturally with B1 first-target-or-stop, best-of-five in both eras.

NEXT per the standing sequence: Census C — the admissibility sweep — the
selection lead with +12/+18pp era-consistent separation on 22-30% of events.

## E — CORRECTION TO THE READING (ANGUS, 2026-08-07)

"E1 loses" is the wrong record: in R terms (stop ≈ 20pt) the entire 5×2×2
surface spans ~0.4R and E1 finished 0.01R behind hold-with-stop. **E1 TIED.**
Recorded as: trail and hold-with-stop are indistinguishable on the raw book.
**Consequence shipped as a simplification:** the live path uses HOLD-WITH-STOP
— no ratchet state to reconstruct after restart, no trailing logic to disagree
with the backtest. Second null this week that made the build smaller.

## E1-CONDITIONAL — declared 2026-08-07, BEFORE Census C results exist

The interaction argument (selection plausibly concentrates the fat tails; a
trail is the rule that pays on tails) is legitimate AND is exactly how a
post-hoc rescue is born. Therefore, declared blind to C:

- IF Census C establishes admissibility separation under its own declared bar,
  E1 (trail) is re-tested ONCE on the C-selected book (the ADMISSIBLE stratum
  at C's winning K), per arm.
- BAR: E1 must beat BOTH B1 and B2 on cluster-collapsed mean net capture in
  BOTH eras on that population.
- This is the SECOND AND FINAL test of E1. No other subsets, no variants, no
  third test regardless of outcome. If C fails its own bar, this conditional
  expires unused.

## Standing principle (three-for-three, recorded)

Failed auction, M1, M2: every raw structural regularity measured this week is
priced at what the risk costs. The edge, if it exists, lives entirely in
SELECTION — which setups are taken — not in the setups existing. Three
well-characterised nulls now sit underneath the live edge; the edge itself
remains unmeasured.

## C — the admissibility sweep (declared 2026-08-07, before the run)

Population: Census B fit events, both arms (DEVIATION from SPEC §5's canon-L0
population, recorded with reason: same coordinate system as the established
headline metric and the +12/+18pp preview; the canon-L0 comparator is deferred,
not cancelled). Strata per event: NO-CEILING / CEILING-BROKEN-within-K /
CEILING-UNBROKEN, ceiling = the stored 5m/60m MA between entry-reference and
target; broken-within-K = that TF closed through its own MA in the trade
direction within its last K completed bars before the event, K swept
{1,2,3,5,10,inf}. Metric: target_before_extreme_20 (the established headline).
Wilson cluster-collapsed, era x side x arm with UNDERPOWERED flags, stratum
sizes mandatory. ESTABLISHED requires: BROKEN(K)+NO-CEILING vs UNBROKEN
separation positive in BOTH eras with non-overlapping intervals at >=2
adjacent K values (a plateau, not a spike). One run, read against this bar.

## Sequencing ruling (ANGUS 2026-08-07) + declared follow-on studies

**The C verdict stands untouched.** Recorded alongside it, worth more than the
verdict it failed: **FRESH BREAKS ONLY** — clause (b) of the admissibility
rule holds for ~one bar of the breaking timeframe, then expires. Actionable
immediately, regardless of any census.

**Methodological note (not a relitigation):** ceiling_broken_K was CUMULATIVE
(within the last K bars), so widening K mechanically dilutes a boundary
effect — K=2's population contains K=1's plus staler events. An adjacent-
cumulative-cell plateau bar cannot pass when the true effect is a monotone
decay from the edge. The bar was built for mid-range spikes; that is what it
catches; the verdict stands because the bar was the bar.

**Role note, recorded:** three ANGUS market hypotheses failed today
(convergence confound, exits-before-C, spent-travel); four ANGUS process
steers flipped or protected results (stop anchoring, circularity check,
stratum sizes, the blind conditional). Division of labour going forward:
trader supplies observations; the desk's job is measurement and adversarial
breakage, not market guesses.

### §F — close_dist_bw as CONTINUOUS conviction weight (FIRST)

Population: Census B reject arm, fit (close_dist_bw is an attempt-bar
magnitude; the break arm has no such bar — scope stated, not hidden).
Capture: the SHIPPED exit convention (hold-with-stop). Variable: within-era
percentile rank of close_dist_bw — continuous, never a cut.
Two declared tests, no variants:
1. Spearman rank corr(close_dist_rank, captured W net) > 0 in BOTH eras.
2. The EXISTING conviction ladder applied without tuning — rank quartiles
   mapped to 0.5/1.0/1.5/2.0 weights — weighted mean capture per unit risk
   beats unweighted in BOTH eras on the cluster view.
Weights, not gates: every trade stays in the book.

### §D — confluence census (SECOND)

Precondition query (logged before D runs): corr(confluence_count,
close_dist_bw) + joint table, per the findings-4/5 protocol.
Then: confluence_count as a continuous monotone variable on the same metric,
rank corr + monotonicity in BOTH eras, both arms. Motivated by three placebo
failures with identical signatures; nothing has tested it.

### §G — fresh-permission, EXCLUSIVE bins (LAST)

Declared as a NEW hypothesis arising from a failed test, held to the
45-minute-timer standard — not a rescue. Exclusive staleness bins {1, 2-3,
4-5, 6-10, never}; the test is MONOTONE DECAY in both eras. Runs after F and
D, not before.

### Holdout rule (standing)

The six sealed months buy ONE clean confirmation. It is reserved for the
ASSEMBLED selection layer (close_dist_bw + confluence + whatever survives),
not for any individual lead. Nothing here authorizes unsealing.

## F — RESULT (run 2026-08-07)

```
STUDY F — close_dist_bw continuous rank (prereg §F), reject arm, shipped exit (hold-with-stop)
  H2-2025: n=1,568 | TEST1 Spearman rho -0.561 (p=5.2e-109) -> FAIL
          TEST2 ladder-weighted -0.0681W vs unweighted -0.0672W per unit weight (cluster view) -> FAIL
          quartile mean caps: Q1 -0.049 Q2 -0.071 Q3 -0.010 Q4 -0.087
  H1-2026: n=1,430 | TEST1 Spearman rho -0.474 (p=1.4e-71) -> FAIL
          TEST2 ladder-weighted +0.0099W vs unweighted +0.0096W per unit weight (cluster view) -> PASS
          quartile mean caps: Q1 -0.038 Q2 +0.006 Q3 +0.137 Q4 +0.048

PREREG BAR (both tests, both eras): FAIL — reported as a miss, no variants
```

## D — RESULT (run 2026-08-07)

```
CENSUS D — confluence_count as continuous monotone (prereg §D)
precondition (logged): corr(confluence, close_dist_bw) = -0.18 — independent variables
  reject  H2-2025: rho +0.153 -> PASS | bins 1:55%(n189) 2:63%(n617) 3:71%(n340) 4:73%(n260) 5+:81%(n162)
  reject  H1-2026: rho +0.119 -> PASS | bins 1:59%(n199) 2:62%(n552) 3:69%(n339) 4:71%(n214) 5+:79%(n126)
  break   H2-2025: rho +0.070 -> PASS | bins 1:61%(n87) 2:71%(n272) 3:71%(n160) 4:66%(n117) 5+:86%(n65)
  break   H1-2026: rho +0.060 -> PASS | bins 1:64%(n102) 2:71%(n236) 3:66%(n139) 4:73%(n75) 5+:82%(n44)
PREREG BAR (rho>0, both eras, both arms): PASS
```
