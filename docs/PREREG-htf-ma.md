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

## THE STOP-WIDTH LAW (ANGUS 2026-08-07, protocol, permanent)

Any variable correlated with stop width must be tested in R, never hit rate —
close_dist_bw bought win rate with denominator (stop ≈ close_dist + wick) and
neither side caught it until capture. Corollary: DUAL-CURRENCY BY DEFAULT —
every study from here reports hit rate AND net R from the outset; a hit-rate
pass alone is a known-unreliable filter. G runs dual-currency.

## D-capture pre-checks (run before the prereg below, logged)

1. corr(confluence_count, stop_dist_W) = -0.20..-0.24 in ALL four arm×era
   cells — NEGATIVE. Confluence associates with TIGHTER stops; the
   close_dist death mechanism is absent, directionally reversed.
2. Tolerance is W-DENOMINATED (code: 0.25×w15) — the manufactured-confluence-
   by-low-volatility channel does not exist. corr with w15 mildly positive
   (+0.16/+0.22). HOWEVER: corr(confluence, profile_min) = -0.51/-0.49 —
   confluence is strongly a property of the EARLY session (asia mean 3.78 vs
   ~2.1-2.4 elsewhere): the immature profile packs POC/VAH/VAL/VWAP together
   mechanically. CONFOUND FLAGGED: D may partly proxy session time. The
   capture study reports session-stratified and profile-age-stratified tables
   alongside the bar; the bar itself is unchanged.

## §D-capture — declared 2026-08-07 BEFORE the run (ANGUS two-part bar)

Population: Census B fit, shipped exits per arm (reject: hold-with-stop;
break: first-target-or-stop). Currency: NET R = (exit-entry)/stop_distance,
cost 0.5pt converted per event. Bins: confluence 1/2/3/4/5+. Minimum 30
clustered observations per bin; an underpowered bin cannot carry a pass and
monotonicity is read on powered bins only.
BAR (on the REJECT arm; break reported alongside):
  (a) bin mean net R non-decreasing across powered bins, BOTH eras;
  (b) the top powered bin's mean net R positive with its 95% cluster interval
      clear of zero, BOTH eras.
Context tables (reported, unbarred): session-stratified bins; profile_min
tercile bins. One run, no variants.

## D-capture — RESULT (run 2026-08-07)

```
STUDY D-capture — confluence bins in NET R (prereg bar on reject arm)

[reject]
  H2-2025: 1:+0.056[-0.602,+0.714](n134) 2:-0.277[-0.573,+0.020](n413) 3:-0.417[-0.686,-0.148](n257) 4:-0.670[-0.909,-0.431](n195) 5+:-0.506[-1.043,+0.030](n113)
          monotone(powered)=N | top-bin>0 w/ CI clear=N
  H1-2026: 1:+0.584[-0.377,+1.545](n140) 2:-0.073[-0.457,+0.311](n370) 3:-0.229[-0.518,+0.059](n251) 4:+0.548[-1.265,+2.362](n158) 5+:+0.578[-0.537,+1.692](n84)
          monotone(powered)=N | top-bin>0 w/ CI clear=N

[break]
  H2-2025: 1:-0.284[-0.467,-0.101](n87) 2:+0.107[-0.033,+0.248](n272) 3:-0.003[-0.156,+0.151](n160) 4:-0.199[-0.349,-0.050](n117) 5+:+0.131[-0.027,+0.289](n65)
          monotone(powered)=N | top-bin>0 w/ CI clear=N
  H1-2026: 1:+0.177[-0.048,+0.401](n102) 2:+0.181[-0.010,+0.372](n236) 3:+0.001[-0.168,+0.170](n139) 4:+0.052[-0.134,+0.237](n75) 5+:+0.039[-0.137,+0.215](n44)
          monotone(powered)=N | top-bin>0 w/ CI clear=N

PREREG BAR (reject arm, both parts, both eras): FAIL — miss recorded, no variants

== context (unbarred): reject netR by bin x session (pooled eras) ==
  asia       1:+0.95(n35) 2:-0.24(n175) 3:-0.52(n172) 4:+0.39(n156) 5+:+0.02(n180)
  london     1:+0.91(n87) 2:-0.17(n242) 3:-0.39(n127) 4:-1.06(n78) 5+:--
  ny_pre     1:+0.55(n39) 2:+0.18(n118) 3:-0.77(n34) 4:-- 5+:--
  ny_rth_am  1:-0.14(n65) 2:+0.22(n122) 3:-0.07(n81) 4:-0.10(n56) 5+:--
  ny_pm      1:-0.08(n61) 2:-0.28(n187) 3:+0.05(n115) 4:+0.02(n59) 5+:--

== context (unbarred): reject netR by bin x profile-age tercile ==
  early  1:+1.09(n43) 2:-0.35(n195) 3:-0.48(n185) 4:+0.34(n161) 5+:+0.02(n180)
  mid    1:+0.69(n117) 2:-0.01(n331) 3:-0.60(n152) 4:-1.05(n90) 5+:--
  late   1:-0.03(n119) 2:-0.14(n291) 3:+0.05(n185) 4:-0.09(n107) 5+:--
```

## THE REORIENTATION (ANGUS 2026-08-07) + §H declared before run

**The opposite-signs result reread:** every selection variable this week
(close_dist, confluence, admissibility, persistence) was arrival-predicting —
regressed on "does price reach the level." The paycheck is in travel PAST the
level, and arrival-prediction plausibly selects congestion, which caps tails.
0-for-5 is what you'd expect from a whole family pointed the wrong way — a
better explanation than five independent bad guesses. PRE-COMMITTED
ALTERNATIVE READING, equally live tonight: the discretion is not in these
features at all and the mechanical strategy must earn its own validation
rather than cloning the trader. §H distinguishes them.

**G: PARKED** (arrival-family; its tradeable content — fresh breaks only —
is banked). **Bin-1/isolation: preconditions resolved** — NY-am bin-1 netR is
-0.14 (n65), the +1R cells are Asia/London/early only; recorded as a
session-expansion lead with a thin-liquidity caveat, not a book finding.
**Costs: confirmed** — all week's R figures net 0.5pt/RT (NY assumption;
Asia cells optimistic).

### §H — travel regression (dependent variable changed, not the candidates)

Population: Census B reject arm, fit, shipped exit (hold-with-stop).
DVs: net R (money, barred) and travel_max_W (tail proxy, reported); arrival
hit rate reported alongside so the opposition is visible per variable.
Candidates, direction DECLARED in advance, tested as continuous ranks:
  H1 next_level_dist_W — MORE distance to the first level ahead -> MORE netR
     (the inverse of this week's family; room to run).
  H2 path_emptiness — FEWER levels within 1.0W ahead of entry -> MORE netR.
  H3 bw_expansion — w15 now vs 4 completed 15m bars ago (ratio>1 = expanding)
     -> MORE netR.
Context (reported, unbarred): profile_min, session, side.
BAR per candidate: Spearman(rank, netR) with the DECLARED sign in BOTH eras;
family verdict requires >=1 of 3 passing with |rho| >= 0.05 in both eras.
Cluster views reported. One run, no variants, misses recorded as misses.

## H — RESULT (run 2026-08-07)

```
STUDY H — travel regression (prereg §H), reject arm, shipped exit
  H1 next_level_dist_W   H2-2025: netR rho +0.042 MISS | travel +0.054 | arrival -0.360 (n=1,555)
  H1 next_level_dist_W   H1-2026: netR rho +0.029 MISS | travel +0.072 | arrival -0.350 (n=1,420)
    -> FAIL (declared sign, both eras, |rho|>=0.05)
  H2 path_emptiness      H2-2025: netR rho +0.237 OK  | travel +0.168 | arrival -0.102 (n=1,555)
  H2 path_emptiness      H1-2026: netR rho +0.246 OK  | travel +0.157 | arrival -0.057 (n=1,420)
    -> PASS (declared sign, both eras, |rho|>=0.05)
  H3 bw_expansion        H2-2025: netR rho +0.176 OK  | travel +0.133 | arrival +0.090 (n=1,548)
  H3 bw_expansion        H1-2026: netR rho +0.217 OK  | travel +0.122 | arrival +0.088 (n=1,413)
    -> PASS (declared sign, both eras, |rho|>=0.05)

FAMILY VERDICT (>=1 of 3): PASS — the travel direction has at least one live candidate
```

## §H-capture battery — declared 2026-08-08, before run (ANGUS steers baked)

Reject arm, shipped exit, netR currency, frame PERSISTED. Bins on the natural
count: levels within 1.0W ahead = 0 / 1 / 2 / 3+ (emptiness decreasing).
BAR (two-part, D-capture style): (a) bin mean netR monotone DECREASING in
count across powered bins (min 30 clusters), BOTH eras; (b) the count=0 bin
positive with 95% cluster CI clear of zero, BOTH eras.
LODO UNIT = MONTH (14 folds): H2's netR rho must keep its declared sign in
ALL 14 folds; folds failing are named. Same treatment reported for H3 with
day-clustered views (H3 is a regime variable; period dependence is the
expected failure mode).
QUERIES REPORTED WITH THE RESULT: corr(H1,H2) per era — weak => H2 is
DENSITY not distance (aligns with D's congestion finding); strong => the
+0.04/+0.24 gap must be explained before either is trusted. corr(H2,H3) per
era — resolves SPEC A-1 clause 5 at the declared 0.4 threshold.
Dual-currency throughout. One run, no variants.

## H-capture — RESULT (run 2026-08-08)

```
H-CAPTURE BATTERY (prereg §H-capture), reject arm, frame persisted

== queries reported with the result ==
  H2-2025: corr(H1 dist, H2 emptiness=-cnt) = +0.440 | corr(H2, H3 bwx) = +0.003
  H1-2026: corr(H1 dist, H2 emptiness=-cnt) = +0.397 | corr(H2, H3 bwx) = +0.064

== count-ahead bins in netR (two-part bar, both eras) ==
  H2-2025: 0:UNDERPWR(n3) 1:-0.418[-0.714,-0.123]arr61%(n165) 2:-0.428[-0.714,-0.143]arr63%(n197) 3+:-0.266[-0.518,-0.014]arr67%(n724)
          monotone-decreasing=N | count0>0 CI clear=N
  H1-2026: 0:UNDERPWR(n8) 1:+0.766[-0.245,+1.777]arr58%(n161) 2:+0.281[-0.351,+0.912]arr71%(n197) 3+:-0.029[-0.538,+0.480]arr66%(n633)
          monotone-decreasing=Y | count0>0 CI clear=N

== MONTHLY LODO (14 folds): H2 netR rho sign per fold ==
  H2: 14/14 folds keep sign | ALL FOLDS HOLD
  H3: 14/14 folds keep sign | ALL FOLDS HOLD

  H3 day-clustered (mean of within-day rhos): H2-2025 +0.162 (n=141 days) | H1-2026 +0.222 (n=132 days)

BIN BAR: FAIL | LODO read above | SPEC A-1 clause 5 resolves per the H2xH3 corr vs 0.4.
```

## STANDING PROTOCOL (ANGUS): THREE GATES ON EVERY CLAIM, NOT A MENU

Cluster-collapse, period folds, and currency. H2 passed 14/14 monthly folds
and died on clustering — they catch different diseases and passing one says
nothing about the others. Every claim from here passes all three or reports
which it failed.

## Job 2 — fixed-R and scale-out exit sweep (declared before run)

Rationale on the record: every exit tested so far was single-exit and none
was R-denominated; the trader's actual exit is a scale-out (75% partial,
runner behind); a fixed-W target is a VARIABLE-R target because the stop is
the trigger-candle extreme — prior payoff tables pooled 3R and 12R outcomes
in the same cells.
Deliverables: (1) MFE distribution IN R per event, both arms, both eras —
never yet produced. (2) Single fixed targets at 1/1.5/2/2.5/3/4/5/6R.
(3) Partials: {50%,75%} out at {1,1.5,2}R, remainder (a) held with stop,
(b) trailed per the E1 rule. Baselines: first-structural-target and
hold-with-stop. Costs net 0.5pt.
BAR, declared now: the winner must sit in the INTERIOR OF A PLATEAU —
adjacent R values also beating both baselines — clear both baselines in both
eras, per arm, cluster-collapsed; monthly LODO reported.
Pre-committed shape so the result cannot flatter itself: low targets = high
hit rate, thin average; high targets = the reverse; any fixed cap forgoes the
20R+ tail by construction — the partials exist to test exactly that.

## Job 3 — H3 solo bar, declared BLIND now, run AFTER Job 2

H3 is judged under the SHIPPED exit as it stands after Job 2 (the Job-2
winner if one clears its bar, else hold-with-stop). Bar: causal-rank
quartile bins of bw_expansion must be (a) monotone non-decreasing in
cluster-collapsed net R across powered bins (min 30 clusters), BOTH eras;
(b) top quartile positive, 95% cluster CI clear of zero, BOTH eras;
(c) all three gates pass (bins = cluster gate; rho sign in all 14 monthly
folds = period gate; net R = currency gate). Declared before Job 2's result
exists so the bar cannot be tuned to it. One run.

## Declared, NOT run: sparse level set

Count-0 barely exists because OUR set has ~14 lines — a property of the
definition, not the market. Variant declared as a new hypothesis arising
from a failed test (result-independent reason: the original variable had no
dynamic range on the side that mattered): path variables recomputed over a
sparse subset (profile levels + 15m and 1h MAs, ~5 lines), own bar to be
declared before any run. Not scheduled.
