# EXIT STRUCTURES — testing the exit on the M2/M3 race population

2026-08-08. Population: `race_wide.parquet` restricted to `mech in {M2, M3}`
— **1,612 fights, 786 M2 / 826 M3, 286 session-days** — joined to
`race_runs.parquet` for the untruncated run (`run_mfe_r`, `run_mae_r`,
`reach_*r`). **M1 is out of scope, stated not silently dropped**: M1's
target *is* the 15m MA itself (`m1_out` in `race_wide`; confirmed
`near_name` is null on all 1,541 M1 rows), so "1st/2nd/3rd structure beyond
entry" is not a coherent redefinition of M1's exit — there is nothing to
move it to.

New files, no existing parquet modified: `scripts/exit_structures.py`,
`output/htf_ma_census/exit_structures.parquet` (30,628 rows: 8 variants ×
1,612 fights, plus a stop-grid sweep on variants 1/4/5/6/8, plus one
legacy-cost diagnostic row per fight).

---

## 1. IMPLEMENTATION

**Structure rebuild.** Per fight, at the decision row `p` (one bar before
entry — proved algebraically equal to `j0-1` for every winning TF, and
confirmed empirically below), POC/VAH/VAL/VWAP±0,1,2 are recomputed exactly
as `race_outcomes.py` does (`bb_ma_asof`, `vwap_bands`,
`profile_at_minutes`, all as-of, no lookahead). Candidates are the menu
levels strictly ahead of entry in the trade direction, sorted by distance;
**structure 1/2/3 = the 1st/2nd/3rd of that sorted list.** A level's price
is a *moving* target after entry (VWAP/VAH/VAL walk forward every minute)
— first-passage crossing checks the level's value one bar back
(`tv = tgt_arr[j-1]`), identical convention to the shipped walk.

**The eight variants + one control**, all first-passage, same-bar → stop
wins, EOD flatten at the session segment's last close:

| # | rule |
|---|---|
| 1 | Full exit at structure 1 (**current baseline — control**) |
| 2 | Full exit at structure 2 |
| 3 | Full exit at structure 3 |
| 4 | 75% @ structure 1, 25% @ structure 2, remainder to break-even after the partial |
| 5 | 75% @ structure 1, 25% trailed on the 15m BB MA (exit on a 15m candle close through the MA against the position), remainder to break-even |
| 6 | 50% @ structure 1, 50% @ structure 2, remainder to break-even |
| 7 | Fixed 3R full exit (**control**) |
| 8 | 75% @ structure 1, 25% runner, no target, rides to stop/EOD, remainder to break-even |

**Two-phase engine.** Phase 1 is the shared, full-size position under the
original stop, racing structure-1 (or the fixed-3R price, or nothing for
variants 2/3). If it stops out, the *whole* position exits there — no
partial has happened yet. If structure-1 prints, that fraction locks in
and phase 2 begins **the following bar** (a disclosed no-same-bar-transition
rule — avoids using one bar's range to resolve two different decisions) for
the remainder, stop moved to break-even (= entry), watching its own target
(structure 2 / trail / nothing). If a fight has no candidate for a given
leg (menu is empty — 8.2% of the book has no structure ahead of entry at
all), that leg simply has no target and rides to stop/EOD, rather than
being dropped from the population.

**Cost — 0.5pt/side, i.e. 1.0pt round trip.** Per the equivalence already
established in `docs/real-exit-rescore.md` for this exact style of split
exit: apportioning a flat exit-side cost by leg weight is mathematically
identical to subtracting one flat `cost_r = (0.5+0.5)/risk` from the
**weighted-average gross R** once, regardless of leg count. So every
variant computes `gross_R = Σ wᵢ·Rᵢ` (no cost) then `total_R = gross_R −
1.0/risk`. This is **double** `race_outcomes.py`'s own `walk()` convention
(`COST_PTS=0.5` applied once = 0.5pt total, not 1.0pt) — that distinction
matters for the control below and is handled explicitly, not blended in.

**Stop dimension.** For the two variants selected as best (§3), phase 1's
stop is re-run at −0.5R / −0.75R / −1.0R (cutting the trade early rather
than waiting for the full loss) — **phase 1 only**; the break-even stop in
phase 2 is untouched, since the stop-dimension question ("does the pre-peak
heat finding argue for a tighter initial stop") is about the shared
position before any partial exists, not the runner's management.

### Sanity gates

**Gate 1 — no variant beats its own `run_mfe_r`.** `run_mfe_r` is the
untruncated max favorable excursion under the *original* stop, no target;
every leg's exit price is a point on that same path, and the break-even
stop only shortens the window a leg can run in, never extends it — so
weighted gross R is bounded above by `run_mfe_r` by construction. Checked
over all 30,628 rows: **max(gross_R − run_mfe_r) = 0.0 — PASS, no
violations.**

**Gate 2 — worst outcome ≥ −(1+cost).** Checked against the general
`−(1+cost_r)` floor (`cost_r=1.0/risk`) across every variant and every
stop level: **min slack = 0.0 — PASS** (the tightest-stop, tightest-risk
fights sit exactly on the floor, never breach it). The tighter,
stop_X-specific floor `−(X+cost_r)` also holds exactly (min slack 0.0).

**Gate 3 — structure-1 control reproduces the recorded `out`.** Run twice:
under the task's 0.5pt/side convention (**does not** match `near_out` —
expected, see below) and under `race_outcomes.py`'s own legacy 0.5pt-total
convention (should match exactly). Legacy-convention result: **1,596/1,612
(99.01%) reproduce `near_out` to floating-point-exact** (max abs diff
0.0 on the matched rows), including all 132 open-space fights (both sides
correctly agree `near_out`/`out` is null there — 8.2% of the book, silently
dropped from every prior `.mean()`-based EV on this family, scored
explicitly here instead).

**The remaining 16/1,612 (0.99%) were investigated, not papered over.**
Root cause: `race_outcomes.py`'s `cluster()` does
`F.groupby('scid', as_index=False).first()` — pandas `GroupBy.first()`
defaults to `skipna=True`, so it takes the first **non-null** value
*per column independently*, not literally the first row. For a cluster
whose true first-in-time trigger has entry/stop/risk (never null) but a
null `near_name`/`near_out` (open space at *that* trigger), the surviving
row's `entry`/`stop` correctly come from the true first trigger while
`near_name`/`near_out`/`out` silently leak in from a **later** trigger in
the same cluster. Confirmed by hand on all 16 (e.g.
`2025-09-02:M2:long:S7`: recorded entry 23408.25 has genuinely no
candidate ahead — vwap_p2 sits 0.94pt *behind* it — but the stored
`near_name=vwap_p2`/`near_out=-1.333` belongs to the cluster's next
raw trigger three minutes later, entry 23405.75). This is a **real,
previously undocumented micro-defect in `race_wide.parquet`'s upstream
build**, affecting 1% of the M2/M3 population; this rebuild is unaffected
by it (candidates recomputed fresh at each fight's own recorded entry/t)
and is, on this point, more correct than the column it's being checked
against. Cost-convention gap (0.5pt/side vs legacy 0.5pt-total) reproduces
exactly `= 0.5/risk` on every one of the other 1,596 rows (max diff
7×10⁻¹⁶) — confirmed pure convention, not logic drift. **Gate 3: PASS with
one disclosed, quantified, root-caused 0.99% upstream artifact.**

---

## 2. EV AND WIN RATE, EVERY VARIANT, PER SESSION × MECHANISM

Day-clustered 95% bootstrap (`dboot_mean`, seed 20260807, 2000 draws).
Stop = the recorded stop (X=1.0) throughout this table. **Bold** = CI
entirely negative.

### LONDON M2 (n=280, 137 days)
| variant | EV | 95% CI | win% |
|---|---:|---|---:|
| **1 (baseline)** | **−0.387** | [−0.547,−0.225] | 33.6% |
| **2** | **−0.637** | [−0.863,−0.350] | 12.1% |
| **3** | **−0.805** | [−1.018,−0.532] | 5.4% |
| **4** | **−0.418** | [−0.569,−0.263] | 33.9% |
| **5** | **−0.409** | [−0.568,−0.246] | 33.6% |
| **6** | **−0.449** | [−0.598,−0.297] | 31.1% |
| 7 (control) | −0.127 | [−0.344,+0.084] | 26.1% |
| **8** | **−0.458** | [−0.608,−0.305] | 33.2% |

### LONDON M3 (n=334, 168 days)
| variant | EV | 95% CI | win% |
|---|---:|---|---:|
| 1 (baseline) | −0.114 | [−0.388,+0.245] | 40.1% |
| 2 | −0.101 | [−0.677,+0.746] | 18.3% |
| 3 | −0.084 | [−0.719,+0.870] | 10.2% |
| 4 | −0.151 | [−0.420,+0.198] | 38.9% |
| 5 | −0.193 | [−0.451,+0.159] | 38.3% |
| 6 | −0.188 | [−0.453,+0.157] | 35.0% |
| 7 (control) | −0.050 | [−0.271,+0.152] | 27.5% |
| 8 | −0.219 | [−0.473,+0.136] | 38.3% |

### NY_PRE M2 (n=243, 143 days)
| variant | EV | 95% CI | win% |
|---|---:|---|---:|
| 1 (baseline) | −0.204 | [−0.450,+0.070] | 32.9% |
| **2** | **−0.648** | [−0.897,−0.293] | 12.8% |
| **3** | **−0.632** | [−0.957,−0.174] | 7.0% |
| **4** | **−0.268** | [−0.504,−0.004] | 33.3% |
| **5** | **−0.271** | [−0.497,−0.030] | 32.1% |
| **6** | **−0.333** | [−0.565,−0.051] | 31.3% |
| **7 (control)** | **−0.232** | [−0.445,−0.024] | 22.6% |
| **8** | **−0.282** | [−0.503,−0.050] | 32.1% |

### NY_PRE M3 (n=244, 137 days)
| variant | EV | 95% CI | win% |
|---|---:|---|---:|
| 1 (baseline) | −0.164 | [−0.358,+0.036] | 35.7% |
| 2 | +0.703 | [−0.330,+2.257] | 16.8% (thin/noisy, see §5) |
| 3 | +0.749 | [−0.440,+2.440] | 10.7% (thin/noisy, see §5) |
| 4 | −0.092 | [−0.349,+0.207] | 35.7% |
| 5 | −0.167 | [−0.408,+0.124] | 35.2% |
| 6 | −0.019 | [−0.354,+0.406] | 34.0% |
| 7 (control) | −0.091 | [−0.314,+0.155] | 25.8% |
| 8 | −0.164 | [−0.407,+0.126] | 35.2% |

### NY_AM M2 (n=263, 116 days)
| variant | EV | 95% CI | win% |
|---|---:|---|---:|
| 1 (baseline) | −0.064 | [−0.211,+0.111] | 59.7% |
| 2 | −0.056 | [−0.247,+0.153] | 41.1% |
| 3 | −0.064 | [−0.355,+0.265] | 23.2% |
| 4 | −0.062 | [−0.208,+0.111] | 59.3% |
| 5 | −0.021 | [−0.175,+0.159] | 58.2% |
| 6 | −0.060 | [−0.208,+0.116] | 55.5% |
| 7 (control) | −0.026 | [−0.244,+0.201] | 26.6% |
| 8 | −0.026 | [−0.180,+0.153] | 58.2% |

### NY_AM M3 (n=248, 128 days)
| variant | EV | 95% CI | win% |
|---|---:|---|---:|
| 1 (baseline) | −0.164 | [−0.304,+0.001] | 51.2% |
| 2 | −0.021 | [−0.375,+0.437] | 32.3% |
| 3 | −0.142 | [−0.486,+0.325] | 18.5% |
| 4 | −0.117 | [−0.292,+0.080] | 50.4% |
| 5 | −0.104 | [−0.286,+0.101] | 50.0% |
| 6 | −0.070 | [−0.283,+0.195] | 49.6% |
| **7 (control)** | **−0.296** | [−0.502,−0.078] | 19.4% |
| 8 | −0.111 | [−0.292,+0.094] | 50.0% |

**Zero of the 48 (session × mech × variant) cells clear positive.** 15
clear negative. Win rate and EV agree everywhere — this is not a Law-3
"high win rate, negative EV" pattern; win rate and EV move together and
both point the same direction. Variant 3 (LONDON M2, win 5.4%) is the
starkest illustration of the same mechanism flagged in the established
facts: chasing a farther, rarer target trades win rate for a size of win
that doesn't compensate, matching the fixed-target decline shape past 2R.

---

## 3. THE STOP GRID — two best variants

**Selection.** Among the six real redesigns (2,3,4,5,6,8 — 1 and 7 are
controls), variants 2/3 (full exit further out) are excluded from "best"
despite occasionally large point estimates: win rates of 5–22% and CIs
regularly 1–2R wide mean their apparent gains are thin-tail artifacts (see
§5). Among 4/5/6/8, ranked by mean EV across the 6 cells (context, not a
reported headline): V2/V3 aside, **V5 (75%@s1 + 15m trail, mean −0.194)**
and **V6 (50/50 s1/s2, mean −0.186)** edge out V4 (−0.185, effectively
tied with V6) and V8 (−0.210, worst of the four). V5 and V6 are selected —
**with the explicit caveat that §5 calibration shows neither reliably
beats the baseline anywhere**, so "best" here means best point estimate
among the redesigns, not a calibrated winner.

### V5 — 75% @ structure 1, 25% trailed on the 15m BB MA
| session | mech | X=0.50R | X=0.75R | X=1.00R (baseline stop) |
|---|---|---|---|---|
| LONDON | M2 | −0.298 [−0.412,−0.174] win 23.6% | −0.349 [−0.489,−0.204] win 29.3% | −0.409 [−0.568,−0.246] win 33.6% |
| NY_PRE | M2 | −0.177 [−0.344,−0.005] win 22.2% | −0.256 [−0.425,−0.078] win 28.0% | −0.271 [−0.497,−0.030] win 32.1% |
| NY_AM  | M2 | −0.119 [−0.203,−0.020] win 40.7% | −0.132 [−0.229,−0.030] win 49.8% | −0.021 [−0.175,+0.159] win 58.2% |
| LONDON | M3 | −0.212 [−0.307,−0.114] win 29.6% | −0.302 [−0.412,−0.190] win 33.2% | −0.193 [−0.451,+0.159] win 38.3% |
| NY_PRE | M3 | −0.109 [−0.317,+0.152] win 23.0% | −0.078 [−0.307,+0.200] win 31.1% | −0.167 [−0.408,+0.124] win 35.2% |
| NY_AM  | M3 | −0.035 [−0.190,+0.156] win 37.5% | −0.059 [−0.229,+0.144] win 44.8% | −0.104 [−0.286,+0.101] win 50.0% |

### V6 — 50% @ structure 1, 50% @ structure 2
| session | mech | X=0.50R | X=0.75R | X=1.00R (baseline stop) |
|---|---|---|---|---|
| LONDON | M2 | −0.311 [−0.414,−0.199] win 21.1% | −0.375 [−0.512,−0.236] win 26.8% | −0.449 [−0.598,−0.297] win 31.1% |
| NY_PRE | M2 | −0.250 [−0.377,−0.108] win 21.8% | −0.342 [−0.481,−0.199] win 27.6% | −0.333 [−0.565,−0.051] win 31.3% |
| NY_AM  | M2 | −0.131 [−0.211,−0.041] win 38.0% | −0.146 [−0.238,−0.043] win 46.8% | −0.060 [−0.208,+0.116] win 55.5% |
| LONDON | M3 | −0.208 [−0.316,−0.084] win 26.9% | −0.302 [−0.422,−0.168] win 30.2% | −0.188 [−0.453,+0.157] win 35.0% |
| NY_PRE | M3 | +0.038 [−0.270,+0.438] win 22.1% | +0.070 [−0.259,+0.484] win 29.9% | −0.019 [−0.354,+0.406] win 34.0% |
| NY_AM  | M3 | −0.008 [−0.197,+0.251] win 37.5% | −0.024 [−0.229,+0.241] win 44.8% | −0.070 [−0.283,+0.195] win 49.6% |

**Tighter stops mostly make it worse, not better,** in both EV and win
rate — cutting at −0.5R doesn't just shrink the loss, it converts a chunk
of would-be structure-1 winners into guaranteed small losers before they
recover, exactly what the pre-peak-heat established fact predicts (46.2%
of eventual runners dip past −0.5R before running; a −0.5R stop forecloses
them). None of these differences clear their own permutation null either
(§6) — the direction is consistent (worse) but not statistically load-
bearing at this n.

---

## 4. WHICH STRUCTURE LEVEL IS THE RIGHT TARGET — per mechanism

**Candidate availability** (how often a structure even exists ahead of
entry) rises sharply from LONDON to NY_AM, both mechanisms:

| session | mech | s1 avail | s2 avail | s3 avail |
|---|---|---:|---:|---:|
| LONDON | M2 | 81.4% | 43.6% | 24.6% |
| LONDON | M3 | 85.9% | 49.4% | 36.8% |
| NY_PRE | M2 | 90.1% | 53.5% | 35.8% |
| NY_PRE | M3 | 93.9% | 59.4% | 45.1% |
| NY_AM  | M2 | 98.1% | 79.5% | 50.6% |
| NY_AM  | M3 | 98.0% | 70.2% | 44.8% |

**M2: structure 1 is the right level, and nothing tested beats it.**
Structure 2 and structure 3 are **reliably worse** — calibrated, not just
lower point estimates (§6, Calibration 4): LONDON and NY_PRE both land
outside their permutation null for variant 2 *and* 3, both in the negative
direction, both sessions. NY_AM (where a structure exists almost every
time — s2 available 79.5%, s3 50.6% — so this is the closest thing to a
fair test of "is the level itself the problem") is flat, inside null.
Every partial variant (4/5/6/8) also scores worse than the plain
structure-1 baseline in M2, though none of those differences clear their
own null (§6) — so in M2 the honest statement is "nothing beats structure
1, and moving further out is calibrated worse in the two sessions where
it's testable."

**M3 is murkier and mostly a null result, with one thin exception.**
Point estimates for structure 2/3 are less bad or even positive in M3
(NY_PRE M3: +0.703 / +0.749), but win rates of 10.7–18.3% and CIs 1.5–2.7R
wide say this is a small number of large winners, not a repeatable edge.
Permutation calibration (§6) confirms: **NY_PRE M3 is the only cell (of
6) where variant 2/3 clears its null against the baseline** — a single
hit with no replication in the other two M3 sessions is within the noise
rate this method is known to produce at n=10 permutations (see
`real-exit-rescore.md`'s own "3/18 hits, no consistent sign" calibration
note). **Verdict: structure 1 remains the defensible default in M3 too**;
the apparent NY_PRE M3 lift from a further target is not trusted.

---

## 5. WHAT THE RUNNER IS WORTH — variant 8 vs 4 vs 5

Among the 735 fights (of 1,612) where structure-1 actually prints before
the stop (the runner leg only exists in these — leg1-hit rate below),
here is what happens to the trailing 25%/50%:

**Structure-1 hit rate** (probability the shared position survives to the
partial at all), per session × mech:

| session | M2 | M3 |
|---|---:|---:|
| LONDON | 39.3% | 43.7% |
| NY_PRE | 36.2% | 37.7% |
| NY_AM | 62.4% | 54.4% |

**Runner (leg-2) resolution**, pooled M2/M3, among the 735 leg1-hits:

| variant | leg2 outcome | M2 % | M3 % | mean leg2 R (when it happens) |
|---|---|---:|---:|---:|
| 5 (trail) | break-even stop | 89.5% | 91.2% | 0.000 |
| 5 (trail) | 15m trail exit | 8.0% | 5.4% | +5.52R (M2) / +4.35R (M3) |
| 5 (trail) | EOD flatten | 2.5% | 3.5% | +11.58R (M2) / +16.26R (M3) |
| 6 (target-2) | break-even stop | 72.7% | 73.2% | 0.000 |
| 6 (target-2) | structure-2 hit | 26.0% | 23.6% | +2.07R (M2) / +2.59R (M3) |
| 6 (target-2) | EOD flatten | 1.4% | 3.2% | +3.46R (M2) / +15.60R (M3) |
| 8 (no target) | break-even stop | 93.6% | 94.6% | 0.000 |
| 8 (no target) | EOD flatten | 6.4% | 5.4% | +8.32R (M2) / +12.96R (M3) |

**The runner's ceiling is real — the mean payoff when it survives ranges
+2R to +16R, the fat right tail from the established facts is genuinely
there. But the break-even stop forecloses it 90–95% of the time,
regardless of which variant.** That is the mechanism, not "which target is
chosen for the 25%": V8 gives the runner unlimited room and V5 gives it a
trend-following trail and V6 gives it a second fixed level, and it barely
matters, because in 9 or 10 fights out of 10 the runner never gets past
its own break-even stop long enough to reach any of them. Permutation
calibration confirms this reads as noise, not signal (§6): V8 vs V5 and
V8 vs V4 are inside their null in **all 6 cells, both comparisons** — the
three runner designs are statistically indistinguishable from each other.
**The runner is worth what a break-even stop is worth: not much, on this
population, because the stop is the binding constraint, not the target.**

---

## 6. CALIBRATION

10-permutation label-shuffle null per (session, mech) cell (seed 20260807):
pool the paired total_R values of the two variants being compared, reshuffle
which n go to which label 10×, recompute the mean difference each time.
Reported as `diff` (true) vs `null[min,max]` (the 10-draw spread) —
"outside" means the true diff falls outside that spread, same reporting
convention as `docs/real-exit-rescore.md`.

**V5 vs V1, V6 vs V1 (does the best redesign beat the baseline?)** — **0 of
12 cells (6 per variant) fall outside their null.** Neither V5 nor V6
reliably beats the structure-1 baseline anywhere, in either direction.

**V5 vs V6 head-to-head** — **0 of 6 cells outside null.** The two
selected-as-best variants are statistically indistinguishable from each
other.

**Stop-grid, X=0.5/0.75 vs X=1.0, V5 and V6** — **0 of 24 comparisons (12
per variant) outside null.** The visible "tighter stop looks worse" pattern
in §3 is directionally consistent but does not clear noise at this n —
report it as a consistent-direction, uncalibrated observation, not a
finding.

**V2/V3 vs V1 in M2 (does a farther target hurt?)** — **4 of 6 outside
null**, LONDON and NY_PRE for both variant 2 and variant 3, all in the
negative direction; NY_AM inside null both times. This is the one family
of comparisons in this report that clears calibration with a consistent
sign — moving the M2 target farther out is a real, reproduced-across-two-
sessions degradation, not noise.

**V2/V3 vs V1 in M3** — **1 of 6 outside null** (NY_PRE M3 only, both
variants, positive direction — the same cell already flagged as thin in
§4). A single hit out of 6, in the one session already identified by eye
as noisy (win rate 10.7–16.8%, CI width >1.5R), is within the false-
positive rate this method is known to produce at n=10 (`real-exit-rescore.md`:
"3/18 hits... exactly what BR-97's ~5%-of-noise warning predicts"). Not
trusted as a finding.

**V8 vs V5, V8 vs V4 (does the runner's target choice matter?)** — **0 of
12 outside null.** Confirms §5: the three runner designs are
indistinguishable.

**Overall: 5 of 54 calibrated comparisons clear their null, all 5 within
the single M2-farther-target-hurts family (4 real, 1 thin/single-cell in
M3).** Every other claim tested — best-redesign-vs-baseline, the two best
variants against each other, the stop-grid, and the runner's target choice
— is a **calibrated null result**, not a finding.

---

## SUMMARY

**No exit variant tested here rescues the M2/M3 book.** 0 of 48
(session × mechanism × variant) headline cells clear a positive 95% CI;
15 clear negative. The one thing that calibrates cleanly is negative: in
M2, moving the target from structure 1 to structure 2/3 is **reliably
worse** (4/6 cells outside their permutation null, consistent direction),
reproducing the established fixed-target decline-past-2R shape on a moving
menu target, not just a fixed R-multiple. Everywhere else — does a
partial-plus-runner beat the plain structure-1 baseline (0/12), do the two
best redesigns (75%@s1+15m-trail, 50/50 s1/s2) beat each other (0/6), does
a tighter stop help given the pre-peak-heat finding (0/24), does the
runner's target choice (trail vs 2nd level vs none) matter once it's
already past a break-even stop (0/12) — is a calibrated null. The runner's
own mechanism is diagnosed directly: its mean payoff when it survives is
large (+2R to +16R depending on variant and mechanism), but a break-even
stop forecloses it in 90–95% of fights that even reach the partial, which
is why the choice of what to do with the surviving 5–10% barely moves the
number. **Best exit per mechanism: structure 1, full exit, in both M2 and
M3** — not because it is good (LONDON M2 −0.387 [−0.547,−0.225], the
worst calibrated cell in the whole table) but because none of the seven
redesigns tested beat it by more than sampling noise, and moving the
target out is the one change proven to make M2 worse. This matches the
established fixed-target curve: the trades are fairly priced (poorly
priced, but *consistently* so) across the exits tested, and the exit is
not where the fix lives.

Sanity gates: all three pass (Gate 1 max overage 0.0; Gate 2 min slack
0.0; Gate 3 99.01% exact match to the recorded baseline, the 0.99%
residual root-caused to a pre-existing `pandas groupby().first()`
skipna artifact in `race_outcomes.py`'s clustering, not this rebuild).
Calibration: 5 of 54 tested comparisons clear their 10-permutation null,
all inside one reproduced family (M2 target-2/3 is worse); everything
else — which variant is "best," the stop grid, and the runner's target
choice — is statistically indistinguishable from shuffled noise at this
sample size. Word count of this summary is separate from the final
chat message below.
