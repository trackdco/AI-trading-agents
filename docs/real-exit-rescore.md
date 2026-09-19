# REAL-EXIT RESCORE — the HTF-MA race population under the trader's actual shipped exit

2026-08-08. Population: `output/htf_ma_census/race_wide.parquet`, 3,153 fights
(unchanged — same census, same triggers, same clustering). New file:
`output/htf_ma_census/race_realexit.parquet`, one row per fight, `race_wide`'s
183 columns plus the real-exit fields below. No existing parquet was modified.

**Every prior EV number on this family (`out` in `race_wide`, i.e. `m1_out` /
`near_out`) was scored against the wrong exit** — M1 against first passage to
the 15m MA, M2/M3 against first structure beyond entry, both closing at a
median ~0.5R. The untruncated run census (`race_runs.parquet`) showed true
excursions reach p90 7.66R and that 47.4% of fights ran further than their
recorded, target-truncated `mfe_r`. This document re-scores every fight
against what the trader actually does: 75% off at 3R, 25% trailing the 15m
BB middle band.

**Headline: the verdict does not flip.** Under the real exit the whole book
is still negative — in fact slightly *more* negative than the structural-
target read (EV −0.124 vs −0.069), because win rate collapses (25.2% vs
38.6%: most of the structural target's "wins" were 0.3–0.5R touches that
don't survive the walk to 3R) while the losers are still full −1R stops.
Conviction (`cc_flow_clean`, `cc_all_clean`) shows no reliable relationship
with real-exit EV once measured against its own permutation null — 3 of 18
(session × mech × count) cells look "significant" at n=10 permutations, in
line with the ~10–20% false-positive rate that many permutations at n=10
implies. This is a clean, calibrated null result, not a bug.

---

## 1. IMPLEMENTATION

**Exact rules implemented** (`scripts/race_realexit.py`):

- **75% exits at a limit at entry + 3×risk** (in the trade direction) — "3R".
- **25% (the runner) trails the 15m BB(20) middle band**: it exits the first
  time a 15m candle *closes* through the MA against the position (long: close
  < MA; short: close > MA). The MA line judged against is built with
  `bb_ma_asof(hist, 15)` at the candle's own close minute — the identical
  "developing-bar-included, chart convention" grammar the M2/M3 mechanism
  already uses in `trigger_race_census.py` (`ma_at15 = ma15.reindex(f15.index
  - 1min)`), so the trail is graded on the same MA line the rest of the
  programme uses, not a new one.
- **Stop = the recorded `stop`** for the *whole* position until 3R prints.
  Same-bar convention, matching `race_outcomes.walk()`: if a bar's range
  covers both the stop and the 3R level, **the stop wins** — checked first,
  every bar, no exception.
- **Two-phase model**, read directly off the task's own outcome formula
  ("0.75×3 + 0.25×runner when 3R reached; −1 (+cost) when stopped first"):
  before 3R prints there is one position with one risk (the race above); only
  once 3R prints does a runner exist, and it starts watching (a) a breakeven
  stop and (b) the 15m trail from the bar *after* the 3R print — no same-bar
  entanglement between the target fill and the runner's own new risk state.
  This is a disclosed assumption, not part of the literal spec text, and it
  affects at most a handful of fights (see Gate C below).
- **Cost: 0.5pt entry-side + 0.5pt exit-side = 1.0pt round trip**, the
  exit-side apportioned across the two legs by size (0.75/0.25). Because the
  apportioned shares sum back to 1, this is mathematically identical to a
  flat `cost_r = 1.0/risk` subtracted once from the blended result, on every
  path (stopped, 3R+trail, 3R+breakeven, 3R+eod, eod_phase1) — splitting the
  exit into two fills does not by itself inflate total cost. This is **double**
  the old repo convention (`COST_PTS=0.5` applied once in `race_outcomes.py`,
  i.e. a single 0.5pt round-trip); sensitivity below.
- **EOD flatten** at session end (`sess_day` 18:00 + 23h) for whichever leg
  hasn't exited yet — the whole position if neither stop nor 3R ever printed,
  or just the runner if 3R printed but neither the breakeven stop nor the
  trail fired by session end.

### Sanity gates

| Gate | Result |
|---|---|
| **(a)** no fight scores better than its own untruncated `run_mfe_r` | **PASS** — max(`real_out` − `run_mfe_r`) = **−0.262** across all 3,153 fights (i.e. every fight has slack; nothing exceeds its own ceiling) |
| **(b)** worst outcome ≥ −(1+cost) | **PASS** — min slack = **0.000** exactly (the tightest-risk fight, risk=0.25pt → cost_r=4.0, floor = −5.0, realized = −5.0, hits the floor exactly, never breaches it) |
| **(c)** 3R-hit rate vs `race_runs.reach_3r` (independent, untruncated) | ours **24.67%** (778/3,153) vs `race_runs` **25.06%** (790/3,153) — gap **−0.38pp** |

Gate (c)'s gap was chased down, not papered over: **all 12 disagreements**
are fights where the entry bar's stop *and* the 3R level are both crossed
inside the *same* 1-minute bar (verified by hand, e.g. `2025-12-21:M1:short:S2`
— risk 0.25pt, entry 25715.25, stop 25715.5, 3R target 25714.5, and the very
next bar prints high 25716.0 / low 25713.0, sweeping both). `race_runs`'s
untruncated walk has no target and no tie-break — it just records the bar's
favorable extreme into `mfe` *before* checking the stop-break, so it credits
these as reaching 3R. Our walk applies the explicitly specified same-bar
"stop wins" rule and scores them as stopped. That is the correct behavior
under the spec, and it fully explains the 12/3,153 (0.38%) gap — not a bug.

**Cost-convention sensitivity** (for transparency, not used in headline
numbers): whole-book EV_real is −0.124 at the specified 1.0pt round trip,
−0.070 at the old repo's 0.5pt convention, and −0.016 gross of all cost.
The qualitative verdict (does not price) holds under all three.

---

## 2. EV AND WIN RATE — REAL EXIT vs STRUCTURAL TARGET, per session × mechanism (never pooled)

Day-clustered 95% bootstrap CIs (2,000 draws, block = `sess_day`), identical
method to the rest of the programme (`conviction_lib.dboot_mean`).

| session | mech | n | days | EV real | CI real | win real | EV struct (`out`) | CI struct | win struct | Δ EV (real−struct) |
|---|---|---:|---:|---:|---|---:|---:|---|---:|---:|
| LONDON | M1 | 617 | 257 | −0.092 | [−0.239,+0.061] | 26.1% | −0.077 | [−0.234,+0.091] | 28.4% | −0.015 |
| LONDON | M2 | 280 | 137 | **−0.231** | **[−0.436,−0.033]** | 26.1% | −0.139 | [−0.298,+0.016] | 37.5% | −0.092 |
| LONDON | M3 | 334 | 168 | −0.158 | [−0.355,+0.039] | 27.5% | −0.070 | [−0.225,+0.087] | 43.1% | −0.087 |
| NY_PRE | M1 | 438 | 233 | −0.167 | [−0.339,+0.016] | 24.4% | −0.036 | [−0.226,+0.185] | 29.9% | −0.131 |
| NY_PRE | M2 | 243 | 143 | **−0.298** | **[−0.505,−0.085]** | 22.6% | −0.096 | [−0.337,+0.182] | 34.2% | −0.203 |
| NY_PRE | M3 | 244 | 137 | −0.032 | [−0.346,+0.333] | 25.8% | −0.089 | [−0.291,+0.123] | 35.7% | +0.057 |
| NY_AM | M1 | 486 | 226 | +0.005 | [−0.181,+0.197] | 25.9% | +0.005 | [−0.140,+0.149] | 41.6% | −0.000 |
| NY_AM | M2 | 263 | 116 | −0.015 | [−0.250,+0.235] | 26.6% | −0.033 | [−0.179,+0.143] | **60.8%** | +0.019 |
| NY_AM | M3 | 248 | 128 | **−0.254** | **[−0.483,−0.007]** | 19.4% | −0.181 | [−0.307,−0.044] | 52.0% | −0.073 |

**No cell clears positive under either exit.** Three cells clear negative
under the real exit (bold): LONDON M2, NY_PRE M2, NY_AM M3 — the same M2/M3
shape flagged in the earlier structural-target census (`FINDINGS-race-outcomes.md`).
NY_AM M1 is the only cell that is roughly flat under both.

**The win-rate collapse is the clearest artifact of the wrong exit.** NY_AM
M2's structural win rate of 60.8% — which reads, on its face, like a strong
cell — falls to 26.6% once "win" means "actually got to 3R or ended the
session ahead," not "touched a nearby structural level for 0.3R." Every cell
shows the same pattern (structural win rates 28–61%, real-exit win rates a
tight 19–28% band clustered near the whole-book 3R-hit rate). High touch-rate
against a close target was never evidence of a good trade; it was evidence of
a close target.

---

## 3. WHOLE-BOOK PICTURE

| | real exit | structural target |
|---|---:|---:|
| n | 3,153 | 3,153 |
| EV | **−0.124** | −0.069 |
| 95% CI (day-clustered) | **[−0.187,−0.054]** | [−0.131,−0.003] |
| win rate | 25.2% | 38.6% |

Both CIs sit entirely below zero. The real exit is not just "still negative,"
it is a touch more negative and its CI is tighter around that negative value
(win rate compresses toward the true 3R-hit rate, which shrinks the sampling
noise in EV).

**Exit-mode breakdown** (3,153 fights):

| exit_mode | n | % |
|---|---:|---:|
| stop (whole position, −1R + cost) | 2,351 | 74.6% |
| 3R reached, runner stopped at breakeven | 365 | 11.6% |
| 3R reached, runner exits via 15m trail | 356 | 11.3% |
| 3R reached, runner rides to EOD | 57 | 1.8% |
| neither stop nor 3R by session end (EOD flatten, whole position) | 24 | 0.8% |

**3R-hit rate: 24.67% (778/3,153) — matches the independent `race_runs`
figure of 25.06% (790/3,153) closely**, per Gate (c) above (gap fully
explained by 12 same-bar sweep bars, not a bug).

**Runner (25%) contribution, among the 778 fights that reached 3R:**

| runner exit | n | % of reached-3R | mean runner R | median runner R |
|---|---:|---:|---:|---:|
| breakeven stop | 365 | 46.9% | 0.000 | 0.000 |
| 15m trail | 356 | 45.8% | +3.956 | +2.710 |
| EOD flatten | 57 | 7.3% | +12.704 | +8.094 |

Overall mean runner result: **+2.741R**, median +0.844R (pulled up by the
EOD tail — a handful of fights ride enormous, day-spanning trends).

**Trail vs flat-at-3R** (i.e., does letting the 25% run beat just taking the
whole position off at 3R?): among the 778 reached-3R fights, the runner ends
up **above 3.0R only 26.9% of the time**; it ends up **below 3.0R (including
the 46.9% that scratch at breakeven) 73.0% of the time**; ties are ~0.1%
(EOD flatten landing exactly at 3R by coincidence). The mean pickup/giveback
versus simply flattening the whole position at 3R is **−0.259R on the
runner's 25%**, i.e. a **−0.065R drag on the blended result** per reached-3R
fight (blended net-of-cost EV on these fights: **+2.825** actual vs **+2.890**
counterfactual flat-at-3R). **The trail costs EV relative to a flat 3R exit,
on this population** — it gives back more (via breakeven scratches and
premature trail-outs) than the fat right tail (the EOD/trend-day fights) adds
back, though the fat tail keeps the difference small.

---

## 4. CONVICTION UNDER THE REAL EXIT (with permutation calibration)

Question: does real-exit EV rise with `cc_flow_clean` / `cc_all_clean`
(the Law-2-clean conviction counts from `conviction_lib`)? Tested per
session × mechanism cell (never pooled for the primary claim), median split
within each cell (low = at/below the cell's own median count, high = above),
day-clustered 95% CI on each half, and — **mandatory per BR-97** — a
10-permutation null per cell: shuffle `real_out` within the (session, mech)
cell only (fight-level, count/labels untouched), re-split at the *same*
median, recompute the same diff statistic 10 times.

**`cc_flow_clean`** — 1 of 9 cells outside its own null range:

| session | mech | n | EV low | EV high | diff | null range (10 perms) | verdict |
|---|---|---:|---:|---:|---:|---|---|
| LONDON | M1 | 617 | −0.149 | −0.009 | +0.140 | [−0.241,+0.101] | outside null |
| LONDON | M2 | 280 | −0.111 | −0.492 | −0.381 | [−0.400,+0.083] | inside null |
| LONDON | M3 | 334 | −0.050 | −0.281 | −0.231 | [−0.368,+0.487] | inside null |
| NY_PRE | M1 | 438 | −0.238 | −0.078 | +0.160 | [−0.454,+0.219] | inside null |
| NY_PRE | M2 | 243 | −0.256 | −0.391 | −0.135 | [−0.375,+0.541] | inside null |
| NY_PRE | M3 | 244 | +0.028 | −0.156 | −0.184 | [−0.787,+0.474] | inside null |
| NY_AM | M1 | 486 | −0.061 | +0.109 | +0.171 | [−0.414,+0.248] | inside null |
| NY_AM | M2 | 263 | −0.077 | +0.048 | +0.125 | [−0.279,+0.356] | inside null |
| NY_AM | M3 | 248 | −0.218 | −0.311 | −0.093 | [−0.422,+0.424] | inside null |

**`cc_all_clean`** — 2 of 9 cells outside null (one positive-direction, one
negative — i.e. not even a consistent sign):

| session | mech | n | EV low | EV high | diff | null range (10 perms) | verdict |
|---|---|---:|---:|---:|---:|---|---|
| LONDON | M1 | 617 | −0.115 | −0.048 | +0.068 | [−0.287,+0.290] | inside null |
| LONDON | M2 | 280 | −0.197 | −0.273 | −0.076 | [−0.430,+0.222] | inside null |
| LONDON | M3 | 334 | −0.000 | −0.348 | −0.348 | [−0.217,+0.259] | outside null (wrong direction) |
| NY_PRE | M1 | 438 | −0.266 | +0.009 | +0.276 | [−0.404,+0.277] | inside null |
| NY_PRE | M2 | 243 | −0.299 | −0.298 | +0.001 | [−0.229,+0.246] | inside null |
| NY_PRE | M3 | 244 | −0.124 | +0.145 | +0.269 | [−0.595,+0.425] | inside null |
| NY_AM | M1 | 486 | +0.059 | −0.056 | −0.114 | [−0.398,+0.425] | inside null |
| NY_AM | M2 | 263 | −0.007 | −0.025 | −0.018 | [−0.623,+0.415] | inside null |
| NY_AM | M3 | 248 | −0.370 | −0.043 | +0.327 | [−0.476,+0.108] | outside null |

**Whole-book exploratory check** (pooled median split, permutation still
done *within* each session×mech cell so the null respects the cell
structure): `cc_flow_clean` diff +0.025, null [−0.129,+0.088] — inside;
`cc_all_clean` diff +0.002, null [−0.068,+0.125] — inside. Essentially zero
either way.

**3 of 18 cell×count-family tests land outside their own 10-draw null**,
with no consistent sign (2 negative, 1 positive for `cc_flow_clean`'s single
hit; `cc_all_clean`'s two hits point opposite directions). At n=10
permutations, landing outside the observed min/max of the null draws by
chance alone happens at a rate materially above 5% (this is a wide,
noisy band, not a calibrated p-value) — 3/18 hits with no consistent sign is
exactly what BR-97's "~5% of pure noise passes" warning predicts once you
run this many cells, not a signal. **Conviction does not reliably raise
EV under the real exit either.**

---

## 5. WHAT CHANGES WHEN THE EXIT IS RIGHT

1. **The verdict does not flip.** Whole book EV goes from −0.069
   (structural target) to **−0.124** (real exit) — both CIs entirely
   negative. Correcting the exit made the family look *worse*, not better.
2. **Win rate is the artifact that mattered.** Structural win rates of
   30–61% were mostly cheap touches on a nearby level; real win rate
   converges to a tight 19–28% band that tracks the whole-book 3R-hit rate
   (24.67%, independently confirmed at 25.06% by the untruncated run
   census). A high touch rate against a close target was never evidence the
   trade holds.
3. **The 15m trail on the runner is a net drag, not an edge, on this
   population.** It beats flattening the whole position at 3R only 27% of
   the time; the mean pickup is −0.26R on the runner's 25% (−0.065R
   blended). The fat right tail (EOD/trend-day rides, mean +12.7R on 7.3%
   of reached-3R fights) is real but does not offset the much more frequent
   breakeven scratches (46.9% of reached-3R fights) and premature trail-outs.
4. **Conviction still does not price**, now confirmed under the trader's
   own exit and calibrated against its own permutation null (mandatory per
   BR-97) rather than asserted from raw point estimates. This extends the
   earlier chance-level verdict (BR-94, on the wrong exit) to the right one.
5. **What this does *not* rule out**: selection (he trades ~1/6 of what
   fires) and any discretionary management deviation from this exact
   mechanical trail remain untested here, exactly as flagged in
   `FINDINGS-race-outcomes.md`. This document only removes "the exit was
   wrong" as a candidate explanation for the family's negative EV — it was
   not the explanation; the negative EV survives the correction.
