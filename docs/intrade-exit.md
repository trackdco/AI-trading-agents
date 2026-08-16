# Can a bad trade be cut early? In-trade exit, entry+N minutes

**Question.** 3,153 fights; 1,000 (31.7%) run <0.5R before stopping and cost
−1,098R against a book total of −392R (both reproduced exactly from
`race_realexit.parquet` below — 1,000/3,153, sum −1,097.99R, book
−392.06R). Entry-time selection is one attack on that. This is the other:
**in-trade management**. Using only information available in the first N
minutes AFTER entry (N ∈ {1,2,3,5,10}), can junk be told from a runner well
enough to beat a blanket tight stop?

**Short answer: the signal is real (AUC far outside a permutation null at
every horizon) but it does not cash out. No horizon's early-exit policy
beats "do nothing" by a margin distinguishable from zero (day-block
bootstrap CIs all straddle 0). Both do-nothing and the early-exit policy
crush blanket −0.5R/−0.75R stops.** Full detail below.

Code: `scripts/intrade_exit_features.py` (feature construction),
`scripts/intrade_exit_model.py` (models, permutation calibration, policy
sweep), `scripts/intrade_exit_breakdown.py` (per-session/mech, bootstrap,
TP/FP accounting). Outputs in `output/htf_ma_census/intrade_exit_*` and
`race_intrade_features.parquet` (new files; no existing parquet touched).

---

## 1. FEATURE CONSTRUCTION AND THE NO-LEAK ARGUMENT

For every fight and every horizon N, a one-pass bar walk starts at the entry
bar `j0` (`searchsorted` on the 1m index at the fight's own `t`, the same
convention `race_runs.py` uses) and advances bar-by-bar. At each bar the
walk:

1. updates running favourable/adverse excursion (`exc_fav_r`, `exc_adv_r`,
   direction-oriented, in R),
2. updates the current mark (`close_r`), a red/green bar counter, summed bar
   range and volume, and cumulative footprint delta (`fp_minutes_full`,
   oriented by `direction`),
3. **checks the fight's own ORIGINAL stop** — the same price the trader was
   actually risking — same-bar convention (stop checked before the
   snapshot is written, matching `race_realexit.score_one`'s "stop wins" rule),
4. if `k` (minutes elapsed) equals a requested horizon, snapshots the
   running state into that horizon's feature row.

**The freeze rule is the whole discipline.** The instant the original stop
fires, the walk **freezes**: every later horizon for that fight reuses the
exact frozen state and is marked `resolved_early=True`. Nothing computed for
horizon N ever reads a bar at `j0+k` for `k>N`, and once a position is
closed, no later bar contributes to *any* horizon's features — a fight that
spikes green five minutes after being stopped gets no credit for it, because
a trader watching the tape would already be flat. This is the fix for the
brief's own stated trap ("has it gone green yet" is outcome-ish for short
horizons): raw `green_ever` is ~96% true at N=1 (nearly every fight ticks
green for a moment) and is nearly uninformative alone; what carries signal is
the *magnitude* (`exc_fav_r`) and whether the position is *already closed*.

Per-fight, per-horizon features (`h{N}_*`, 15 fields):
`exc_fav_r`, `exc_adv_r`, `close_r`, `green_ever`, `green_now`,
`back_thru_entry` (peaked green, now back through/below entry),
`frac_red_bars`, `mean_bar_range_r`, `range_vs_base` (bar range vs a 30-bar
pre-entry baseline), `vol_ratio` (volume vs the same baseline),
`delta_share` (cumulative oriented footprint delta / window volume, bounded
[-1,1]), `dist_ma15_r` and `ma15_move_r` (15m BB-MA, `bb_ma_asof` — causal
by construction, gated for lookahead elsewhere in this repo), `already_stopped`,
`n_bars`. All are legitimately knowable at entry+N: they are computed from
bars `j0..j0+N` (or earlier, if the position closed first) and nothing else.
Pre-entry covariates (`w15`, `risk`, `disp_w`, `flowconf`, `mech`,
`session`, ...) come straight from `race_wide.parquet`'s decision-time
columns and carry across all horizons unchanged.

**Correctness checks run before any modeling:** (a) `h10_exc_fav_r` never
exceeds `race_runs.run_mfe_r` (0/3,153 violations — the horizon-capped walk
can't see more than the full untruncated walk); (b) for fights whose full
run peaks at ≤10 minutes and aren't stopped by then, `h10_exc_fav_r` equals
`run_mfe_r` exactly (547/547, 100%); (c) `h{N}_already_stopped` agrees with
`race_runs.stopped`/`bars_held` at every boundary check, including the
exact same-bar edge case (a stop firing exactly on the bar that closes a
horizon window) — an initial version of the walk missed this edge case
(68/1,694 mismatches) and was fixed by checking the stop **before** writing
the snapshot; the fixed version is 100% consistent (0/1,694 through 0/632
across all five horizons).

---

## 2. OUT-OF-FOLD AUC BY HORIZON vs PERMUTATION NULL — headline

Target: `is_junk = run_mfe_r < 0.5` (the untruncated, stop-truncated run —
independent of any target/exit choice). Logistic regression + HistGB
(depth-3, early-stopped), fit on static pre-entry covariates + the
horizon's `h{N}_*` features, evaluated with **GroupKFold on `sess_day`** (5
folds, 290 days, no day split across train/test). **Permutation null:**
labels shuffled *within* (session × mech) strata — preserves each cell's
junk base rate, breaks the feature→label link — 20 draws, same CV.

| h (min) | still-open frac | AUC pooled (LR / GBM) | AUC **actionable** subset¹ (LR / GBM) | null mean [95%] | null p |
|---:|---:|---|---|---|---:|
| 1  | 80.0% | 0.931 / 0.950 | 0.880 / 0.898 | 0.501 [0.475,0.527] | 0/20 |
| 2  | 72.1% | 0.959 / 0.976 | 0.909 / 0.926 | 0.503 [0.479,0.529] | 0/20 |
| 3  | 66.4% | 0.971 / 0.985 | 0.924 / 0.939 | 0.501 [0.469,0.534] | 0/20 |
| 5  | 57.9% | 0.982 / 0.993 | 0.942 / 0.949 | 0.500 [0.475,0.532] | 0/20 |
| 10 | 46.3% | 0.990 / 0.999 | 0.966 / 0.975 | 0.501 [0.469,0.536] | 0/20 |

null mean/range = the two models' 20-draw null distributions pooled
(mean averaged, range = the envelope of both); `null p` = 0/20 permutation
AUCs (either model) matched or beat the real AUC, at every horizon.

¹ "actionable subset" = fights **not yet resolved** at horizon N (not
already stopped, session not yet ended) — the population a policy could
actually intervene on. Real AUC beat every one of the 20 permutation draws
at every horizon, both models (p=0.000 throughout) — **this is not noise.**

The pooled AUC climbs toward 1.0 mechanically: by minute 10, 53.7% of fights
are *already resolved* (`already_stopped`), and for those the label is
almost tautological — `race_runs`'s own walk froze at the same bar ours did,
so `h10_exc_fav_r` IS `run_mfe_r` for that subset, no forecasting involved.
The **actionable-subset AUC** (0.88–0.98) is the honest number: real
discrimination among trades still alive at N, and it is still enormous —
far outside the null. Secondary target `real_out<0` (did the trade lose
money at all, the trader's actual exit): AUC 0.72→0.90 (LR) as N grows;
Spearman(OOF P(junk), `real_out`) runs −0.22 (N=1) to −0.43 (N=10), all
correctly signed. **What the model keys on** (LR |standardized coefficient|,
corroborated by GBM permutation importance): overwhelmingly `exc_fav_r`
(favourable excursion so far — by far the largest coefficient at every
horizon) and `already_stopped`/`n_bars`, then `mean_bar_range_r` /
`range_vs_base` (bar volatility vs baseline) and `close_r`. Footprint order
flow (`delta_share`) and volume ratio contribute *marginally* — GBM
permutation importance for `h1_delta_share` is +0.001 AUC vs +0.295 for
`h1_exc_fav_r`. **This is a price-action signal, not an order-flow signal.**

---

## 3. THE POLICY TABLE

Policy: *at entry+N, if OOF P(junk) > threshold, exit at market* (price =
`close_r` at that bar minus the round-trip cost `race_realexit` already
charges, 1.0pt/`risk`). Fights already `resolved_early` by N cannot be
touched (nothing to exit) and keep their real outcome. Compared against
**do-nothing** (`race_realexit.real_out`, the actual shipped 3R+trail exit)
and **blanket −0.5R / −0.75R stops** — re-simulated with the *identical*
`race_realexit.score_one` machinery (same 3R target, same breakeven/trail
runner), only the initial stop distance changed, so the comparison isolates
the stop decision from everything else. (`P(3R)` here = `reached_3r` from
the two-phase real-exit engine — 24.7% do-nothing, vs. the brief's 25.1%
which is `run_mfe_r>=3` on the untruncated walk; both count "reached 3R",
the ~0.4pt gap is the two measurement conventions, not a discrepancy in the
data.)

**Pooled, whole book (n=3,153):**

| policy | EV (R/trade) | sum (R) | P(3R) |
|---|---:|---:|---:|
| do-nothing (actual shipped exit) | **−0.124** | −392.1 | 24.7% |
| blanket −0.50R stop | −0.532 | −1,677.8 | 14.5% |
| blanket −0.75R stop | −0.310 | −978.2 | 20.0% |
| best early-exit, h=1 (LR, thresh 0.45, flags 25.7%) | −0.116 | −366.8 | 20.6% |
| best early-exit, h=1 (GBM, thresh 0.50, flags 12.7%) | −0.119 | −374.4 | 23.2% |
| best early-exit, h=2 (LR, thresh 0.50, flags 16.6%) | −0.121 | −381.9 | 22.1% |
| best early-exit, h=3 (GBM, thresh 0.75, flags 1.7%) | −0.122 | −385.8 | 24.6% |
| best early-exit, h=5 (LR, thresh 0.65, flags 5.8%) | −0.125 | −394.0 | 23.9% |
| best early-exit, h=10 (GBM, thresh 0.35, flags 3.0%) | −0.127 | −399.3 | 24.2% |

(Full 9-threshold sweep × 10 horizon/model combos in
`output/htf_ma_census/intrade_exit_policy.csv` — every row checked; these
are the max-EV row per horizon×model, and none of the 90 rows swept beats
do-nothing by more than the amounts shown.)

**Statistical significance (day-block bootstrap, 4,000 draws, resampling
`sess_day`), best row per horizon:**

| horizon | ΔEV vs do-nothing | 95% CI | significant? |
|---:|---:|---|---|
| h=1 LR | +0.0080R | [−0.0199, +0.0347] | no |
| h=1 GBM | +0.0056R | [−0.0098, +0.0203] | no |
| h=2 LR | +0.0032R | [−0.0191, +0.0249] | no |
| h=2 GBM | +0.0022R | [−0.0060, +0.0097] | no |
| h=3 LR | +0.0022R | [−0.0183, +0.0220] | no |
| h=3 GBM | +0.0020R | [−0.0018, +0.0050] | no |
| h=5 LR | −0.0006R | [−0.0159, +0.0130] | no |
| h=5 GBM | −0.0005R | [−0.0135, +0.0117] | no |
| h=10 LR | −0.0011R | [−0.0135, +0.0096] | no |
| h=10 GBM | −0.0023R | [−0.0136, +0.0074] | no |

**Every CI straddles zero.** Even the best case (h=1 LR, +0.008R/trade,
+25.2R aggregate) is well inside noise. Both blanket stops are
*catastrophically* worse than do-nothing and worse than every early-exit
variant — confirms the brief's warning that a blanket tighter stop is not
free (my re-simulation: −0.5R kills 41.4% of the do-nothing book's runners,
778→456 fights reaching 3R, to buy a shrunk average loss on the junk — net
EV more than 4x worse than doing nothing).

### Why a 0.88–0.98 AUC doesn't turn into money

TP/FP R-accounting at each horizon's best threshold
(`intrade_exit_breakdown.py`):

| horizon (best row) | flagged | TP (junk correctly cut): n, R saved each | FP (not junk): n, R cost each | …of which real runners cut: n, R cost each | net R |
|---|---:|---|---|---|---:|
| h=1 LR | 810 (25.7%) | 423, +0.60 | 387, −0.59 | 129, **−3.18** | +25.2 |
| h=1 GBM | 402 (12.7%) | 261, +0.45 | 141, −0.71 | 47, **−3.22** | +17.6 |
| h=2 LR | 524 (16.6%) | 278, +0.59 | 246, −0.62 | 81, **−3.32** | +10.1 |
| h=3 LR | 441 (14.0%) | 228, +0.61 | 213, −0.62 | 69, **−3.37** | +6.9 |
| h=5 LR | 182 (5.8%) | 95, +0.53 | 87, −0.61 | 25, **−3.51** | −1.9 |
| h=10 GBM | 94 (3.0%) | 53, +0.56 | 41, −0.90 | 15, **−3.53** | −7.2 |

Cutting a genuinely junk trade early saves ~0.45–0.61R. Cutting a trade that
turns out NOT to be junk costs ~0.6–0.9R on average — and the tail of that
bucket, trades that would actually have **reached 3R** through the real
exit process, costs **3.2–3.5R each**, 5–8x the savings on a correctly-cut
junk trade. At the AUC levels achieved here (very high, but precision on
the flagged set only 52–81% depending on threshold), the arithmetic is
close to a wash: a handful of true runners in the flagged set erase several
dozen correct junk cuts. This is the same mechanism the brief flagged for a
blanket stop, just less severe because the classifier is smarter than a
fixed R-threshold — smarter, but not smart enough to clear the bar.

---

## 4. WHICH HORIZON IS BEST, AND WHAT IT KEYS ON

**h=1 minute is the best horizon** — the only one with a (statistically
insignificant) positive ΔEV, and the only one where the flagged fraction
stays large enough (12.7–25.7%) to matter economically at all. This is
consistent with the book's own timing structure (established fact: 43% of
fights peak within 1 minute) — most of what will happen has often already
started happening by minute 1, and the "already stopped" freeze is not yet
dominant (only 20% resolved by then), so there's more "still alive"
population to act on than at later horizons. By h=5 and h=10, 42.1% and
53.7% of the book is already resolved and the flagged population shrinks
to 3–6%, run out of frequency to move the aggregate needle even when the
sign is favorable.

What every horizon's model keys on (Section 2): almost entirely
**how far it has moved (favourably) and whether it has already stopped**.
Footprint delta and volume-vs-baseline ratios are in the feature set and
occasionally rank in the top 10–12 coefficients, but their marginal
contribution to AUC (permutation importance ~0.001) is two orders of
magnitude below `exc_fav_r`'s (~0.30). **The tape's order flow is not
adding meaningfully to what raw price excursion already tells you.**

---

## 5. PER SESSION / PER MECHANISM (never pooled for conclusions)

Full model refit per session/mechanism was not attempted separately — with
290 days split 9 ways (session×mech) the group-CV folds would be too thin
to calibrate reliably; the pooled model already includes `session`/`mech`
as covariates. Instead: the **policy outcome** (which is what the verdict
hangs on) is broken out by session and by mechanism, using the same
pooled-model OOF predictions.

**Per session, do-nothing vs best early-exit vs blanket −0.5R** (EV, R/trade):

| session | n | do-nothing | h1 LR best | h3 GBM best | blanket −0.5R |
|---|---:|---:|---:|---:|---:|
| LONDON | 1,231 | −0.141 | −0.121 | −0.140 | −0.542 |
| NY_PRE | 925 | −0.166 | −0.129 | −0.161 | −0.534 |
| NY_AM  | 997 | −0.065 | −0.099 | −0.064 | −0.518 |

LONDON and NY_PRE show the largest apparent gains from the h=1 policy
(−0.141→−0.121, −0.166→−0.129) — but these are the two sessions with the
worst do-nothing baseline (more junk to cut in absolute terms), and the
pooled bootstrap already shows the *pooled* effect is noise; per-session
splits are thinner still and not separately recalibrated, so this is
suggestive, not a finding. NY_AM — the best-performing session by
do-nothing (−0.065) — gets *worse* under 9 of the 10 horizon/model variants
swept (−0.099 to −0.067), with one essentially-flat exception (h3 GBM,
−0.064, a −0.0004R difference): the session with fewest true junk fights
to cut has the most room to shoot a runner instead.

**Per mechanism** (EV, R/trade):

| mech | n | do-nothing | h1 LR best | h3 GBM best | blanket −0.5R |
|---|---:|---:|---:|---:|---:|
| M1 | 1,541 | −0.083 | −0.099 | −0.082 | −0.538 |
| M2 | 786 | −0.180 | −0.173 | −0.171 | −0.563 |
| M3 | 826 | −0.149 | −0.095 | −0.150 | −0.492 |

Checking all 10 horizon×model "best" variants against each mechanism's own
do-nothing EV (not just the two columns shown): **M1** (reversal off the
15m MA) is worse under 9/10 variants (−0.005R to −0.016R, one +0.0004R
near-tie) — it is also the mechanism with the best do-nothing EV, i.e. the
least junk-heavy of the three, so there is less to gain and more good
trades exposed to being cut. **M2 and M3** (both continuation) are
*better* under 9/10 variants each (M2: +0.003 to +0.019R, one −0.006R
exception; M3: +0.004 to +0.055R, one −0.001R exception) — the two
mechanisms with the worst do-nothing EV have the most junk to correctly
cut. Re-running the day-block bootstrap **within the M3 subset alone**
(h=1 LR @ 0.45, the pooled-book's own best threshold, n=826, 249 days):
ΔEV +0.055R, 95% CI [+0.013, +0.095], one-sided bootstrap p≈0.006 — nominally
significant on its own. It does not survive even a mild multiple-comparison
adjustment for the 3 mechanisms checked (0.05/3≈0.017 two-sided is closer,
0.05/9-ish across mech×session≈0.006 is not), and it reuses the pooled
sweep's own threshold rather than an independently chosen M3 one, so it is
reported as the single most suggestive result in this whole analysis, not
as a standalone discovery. (Full sweep:
`output/htf_ma_census/intrade_exit_mech_table.csv` /
`_session_table.csv`.)

---

## 6. VERDICT

**Can junk be identified early? Yes, decisively.** Out-of-fold AUC
0.88–0.98 on the actionable (still-open) subset at every horizon, 0/20
permutation draws matching it — this is a real, well-calibrated,
day-grouped-CV, permutation-tested effect, keyed overwhelmingly on how far
the trade has moved (favourably) and whether it has already been stopped,
barely at all on footprint order flow.

**Does it beat a blanket tighter stop? Yes, easily.** Every early-exit
variant tested beats blanket −0.5R (−0.53R EV) and −0.75R (−0.31R EV) by a
wide margin — confirms the brief's point that a blanket stop is not free
(here: −0.5R kills 41% of the book's runners to buy a smaller average loss
on junk, and the trade is a large net loser).

**Does it beat doing nothing? No — not distinguishably from zero.** The
best policy found (flag at minute 1, LR, threshold 0.45) improves book EV
by +0.008R/trade (+25R aggregate over 3,153 fights); its 95% day-block
bootstrap CI is [−0.020, +0.035] — contains zero. Every other
horizon/model/threshold combination in the full sweep is flat or negative,
with wider or equally-zero-straddling CIs. The reason is not model quality
(AUC is very high) but economics: cutting a real 3R+ runner among the false
positives costs 3.2–3.5R, roughly 5–8x what correctly cutting a junk trade
saves (0.45–0.61R), so even a strong classifier needs precision the book
doesn't currently support to turn a profit from intervening. One partial
exception worth flagging for follow-up rather than acting on: within **M3
alone**, the same pooled h=1 threshold clears its own day-block bootstrap
(ΔEV +0.055R, 95% CI [+0.013,+0.095]) — nominally significant, does not
survive a multiple-comparison correction for the 3 mechanisms checked, and
uses a threshold picked on the pooled book rather than for M3 specifically,
so it is a lead, not a result. **The
established pre-peak-heat asymmetry (runners dip −0.45R median, junk dips
−0.66R median, immediately) is real and detectable — but by the time it's
detectable with usable confidence, the cost of the false positives it drags
along is large enough to erase the benefit.** This is a clean null on the
*policy* question even though it is emphatically not a null on the
*predictability* question — both results are reported because both are
true.
