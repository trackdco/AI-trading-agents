# FINDINGS — tomtrades CBR, loser autopsy

Population: the trigger-only book, **2,411 trades over 920 NY days**, GC front month,
2023-01-02 → 2026-08-11. Gates all off — the full stack had 42 trades in three and a
half years and cannot answer a separation question. "Trigger only" still includes the
W-shape (C6), the C7 nested gate and the stop-size cap, which are part of the shift's
definition rather than confluences. The daily cap is off; it is priced separately below.

Method: `src/research/tomtrades/autopsy.py`, run by `scripts/tomtrades_autopsy.py`.
Every feature is read at the bar whose close confirmed the shift, and
`test_autopsy_features_cannot_see_past_the_signal` pins that by truncating the series
after the fill and demanding identical values. Day-clustered bootstrap throughout
(BR-42). Every headline is calibrated against 200 outcome shuffles (BR-97). Post-entry
variables are anatomy only and are refused by the model (BR-41). Both currencies are
reported on every row (Law 3).

---

## The answer in one paragraph

**Winners and losers are separable, and the separation is worthless.** A model reaches
out-of-sample AUC **0.712** against a 0.495 null — and **0.507** once reward:risk is
genuinely held fixed, which is the null. Everything it "knows" is one thing: how far
away the target is. Near targets get hit and pay little; far targets miss and pay more,
and the two offset almost exactly. Sorting the book by out-of-sample expected value and
taking the best fifth returns **+0.004R per trade (p = 0.87)** — no findable subset
pays. The strategy does not lose because it picks bad trades. It loses because of where
it puts the target, and no entry-time filter reaches that.

---

## 1. Where the money goes

| | |
|---|---|
| win rate | 67.86% |
| mean win | +0.4395R |
| mean loss | −1.0000R (every loss is a stop; no gaps or costs modelled) |
| expectancy | **−0.0232R** per trade, −56.0R total |
| win rate needed to break even | 69.47% — short by 1.61 points |
| mean win needed to break even | 0.4737R — short by 0.034R |
| median reward:risk at entry | **0.40** |
| trades risking more than they can make | **82.7%** |

Because every loss is exactly −1R, expectancy is fully determined by two numbers:
`EV = p · E[RR|win] − (1 − p)`. Reward:risk is fixed the moment the order goes in, so
it is knowable at entry. That splits the autopsy in two — anything that predicts **p**,
and anything that predicts **RR** — and the second is not a finding, it is arithmetic.
The only question that matters is whether they are independent.

They are not.

## 2. Win rate and payoff cancel each other

| reward:risk at entry | n | win % | EV | 95% CI (day-clustered) |
|---|---|---|---|---|
| 0.08 | 483 | **89.9** | −0.0345 | [−0.064, −0.008] |
| 0.22 | 483 | 80.7 | −0.0140 | [−0.059, +0.028] |
| 0.40 | 481 | 71.5 | +0.0013 | [−0.056, +0.061] |
| 0.68 | 482 | 56.4 | −0.0542 | [−0.137, +0.024] |
| 1.51 | 482 | **40.7** | −0.0148 | [−0.128, +0.108] |

Spearman(reward:risk, win) = **−0.382**, null −0.000 ± 0.020, p = 0.005 (the floor at
200 shuffles). Win rate falls from 90% to 41% across the book, and **EV is flat and
negative the whole way**. Selecting high-payoff trades is not free; it costs exactly
what it pays.

This also explains his numbers. He claims 76–88% win rates. The top row here is 89.9% —
entirely reachable, and it is the row where you risk one dollar to make eight cents. A
win rate in that range is not evidence of an edge in this method; it is evidence of a
close target.

## 3. Twenty features, six distinct variables

| feature | ρ with win | p | ρ with EV | p | survives BH(10%) |
|---|---|---|---|---|---|
| retrace_frac | **+0.352** | 0.005 | **−0.113** | 0.005 | yes, wrong way |
| rr_at_entry `[Law 2]` | **−0.382** | 0.005 | +0.127 | 0.005 | yes |
| disp_atr | −0.119 | 0.005 | +0.060 | 0.005 | yes |
| run_displacement | −0.081 | 0.005 | +0.061 | 0.005 | yes |
| sweep_depth | +0.022 | 0.318 | **+0.069** | 0.010 | yes |
| sweep_depth_atr | +0.023 | 0.249 | +0.066 | 0.015 | yes |
| minute_of_hour | −0.102 | 0.005 | −0.001 | 0.995 | no |
| run_minutes | −0.102 | 0.005 | −0.001 | 0.975 | no |
| bars_since_arm | +0.063 | 0.005 | +0.015 | 0.428 | no |
| break_dist_atr | +0.060 | 0.015 | −0.007 | 0.726 | no |
| is_long | +0.059 | 0.010 | +0.002 | 0.930 | no |
| risk_atr `[Law 2]` | +0.065 | 0.010 | +0.033 | 0.124 | no |

(Full table with the remaining eight in `output/tomtrades_autopsy_univariate.csv`.)

Two things to read off it.

**The list is shorter than it looks.** `rr_at_entry` and `retrace_frac` correlate
**−0.93** — the same variable twice, since a deeper give-back before entry means a
nearer target. `run_minutes` and `minute_of_hour` correlate **1.000** exactly: the run
is measured from the hour open, so they are the same column. `run_displacement` and
`risk_pts` correlate 0.92. Twenty features are about six things.

**Five features move the win rate and are worth nothing.** `minute_of_hour`,
`run_minutes`, `bars_since_arm`, `break_dist_atr` and `is_long` all shift the hit rate
at p ≤ 0.015 and shift EV by ρ ≤ 0.015 at p ≥ 0.42. Under Law 3 that is a refutation,
not a finding — they are moving the target closer, not improving the trade. His clock
is the clearest case: **minute-of-hour is one of the strongest win-rate effects in the
book and its EV correlation is −0.0006 (p = 0.995).**

`retrace_frac` is the sharpest single result in the table: the largest win-rate effect
of any feature (+0.352) and a **negative** EV effect (−0.113). Waiting for more
give-back before entering buys a higher hit rate at a price greater than it is worth.

## 4. The model: 0.712, or 0.507

| statistic | value | null | p |
|---|---|---|---|
| OOS AUC, all actionable features | 0.7182 | — | — |
| OOS AUC, Law-2 features dropped | **0.7118** | 0.4947 ± 0.0179 | 0.005 |
| top-quintile realised EV | **+0.0039R** | −0.0226 ± 0.0307 | 0.871 |

Day-grouped 5-fold logistic regression; a day is never on both sides of a split, so the
model cannot score its own session. The AUC is real. It is also entirely geometry —
holding reward:risk fixed dissolves it:

| RR strata | AUC within | null | p |
|---|---|---|---|
| 5 | 0.5284 | 0.4920 ± 0.019 | 0.016 |
| 10 | 0.5114 | 0.4919 ± 0.019 | 0.197 |
| 20 | 0.5083 | 0.4918 ± 0.019 | 0.230 |
| 40 | **0.5073** | 0.4917 ± 0.019 | 0.246 |

Quintiles of reward:risk are wide enough that distance-to-target information survives
inside a stratum; tighten them and the separation decays to the null and stays there.
**0.712 → 0.507.** What looked like skill was the ruler.

And the decision that matters — rank by out-of-sample expected value, take the best
fifth:

| predicted EV bin | n | days | predicted EV | win % | **realised EV** | 95% CI |
|---|---|---|---|---|---|---|
| lowest | 483 | 361 | −0.175 | 66.3 | −0.0352 | [−0.106, +0.035] |
| | 482 | 383 | −0.083 | 77.0 | −0.0445 | [−0.096, +0.008] |
| | 482 | 370 | −0.033 | 71.8 | −0.0341 | [−0.094, +0.025] |
| | 482 | 385 | +0.031 | 68.1 | −0.0051 | [−0.073, +0.061] |
| highest | 482 | 357 | **+0.194** | 56.2 | **+0.0026** | [−0.081, +0.093] |

The model predicts the best fifth will make +0.194R and it makes +0.003R. Realised EV
spans 0.047R across the whole book and every interval contains zero. The ranking is
not just weak — its confidence is fiction.

## 5. The one survivor: how far the sweep ran

`sweep_depth` is the only feature that clears the family correction on EV without being
a distance-to-target proxy, and it has the shape Law 3 asks for — EV moves, win rate
does not.

| sweep past the swing (pts) | n | win % | EV | 95% CI |
|---|---|---|---|---|
| 0.31 | 514 | 64.6 | **−0.0969** | [−0.159, −0.032] |
| 0.86 | 461 | 68.8 | −0.0432 | [−0.110, +0.018] |
| 1.76 | 488 | 68.4 | −0.0062 | [−0.081, +0.074] |
| 3.58 | 466 | 70.0 | +0.0081 | [−0.063, +0.075] |
| 11.98 | 482 | 67.8 | +0.0268 | [−0.043, +0.098] |

Read it as an **exclusion**, not a selection: only the shallow bucket has an interval
clear of zero, and it is negative. The top bucket's interval contains zero.

Three checks, because it correlates 0.50 with stop size and 0.52 with run displacement:

- **Risk-adjusted.** Partial ρ(sweep_depth, EV | risk) = **+0.0595**, null +0.002 ±
  0.021, p = 0.020. It survives.
- **Within risk terciles.** ρ with EV = +0.092 / +0.075 / +0.045 (tight / mid / wide
  stops). Present in all three, so it is not a stop-size proxy wearing a disguise.
- **Tie-break artifact?** Tight stops are what the pessimistic same-bar rule punishes,
  so the shallow bucket could be an artifact of the simulator. It is not: same-bar
  stop-outs run 0.9–1.9% across every bucket and the worst-performing bucket is at
  1.75%, in the middle of that range.

What it is worth: dropping the shallowest fifth lifts the book from −0.0232R to
**−0.0033R** (n = 1,897, CI [−0.038, +0.034], halves −0.0002 / −0.0053). The largest
single lever found — and it buys breakeven, not profit, and dies at −0.0515R against
one tick of cost.

## 6. Ten rule variants, priced

| variant | n | win % | EV | 1st half | 2nd half |
|---|---|---|---|---|---|
| baseline (uncapped) | 2411 | 67.86 | −0.0232 | −0.035 | −0.015 |
| **his max 3 trades/day** | 1964 | 67.57 | **−0.0314** | −0.037 | −0.027 |
| breakeven stop at +0.15R | 2411 | 48.65 | **+0.0154** | +0.022 | +0.011 |
| breakeven stop at +0.25R | 2411 | 54.62 | −0.0064 | +0.001 | −0.011 |
| breakeven stop at +0.40R | 2411 | 60.76 | −0.0157 | −0.017 | −0.015 |
| breakeven stop at +0.60R | 2411 | 64.91 | −0.0157 | −0.019 | −0.013 |
| fixed 0.5R target | 2411 | 65.37 | −0.0195 | −0.025 | −0.015 |
| fixed 1.0R target | 2411 | 48.86 | −0.0231 | −0.016 | −0.028 |
| fixed 1.5R target | 2411 | 37.62 | −0.0615 | −0.049 | −0.070 |
| fixed 2.0R target | 2411 | 32.02 | −0.0476 | −0.020 | −0.068 |

Every variant runs on the same signal book, so these are ten exits on one set of trades
rather than ten different strategies.

- **His daily cap costs money here.** Capping at three trades takes EV from −0.0232 to
  −0.0314. Keeping the first three trades of a day is a time-of-day selection, and the
  early trades are not the better ones.
- **Bigger targets are strictly worse.** 0.5R → 1.0R → 1.5R → 2.0R is monotone down.
  The fade is shallow; asking it for more does not work. This closes off the obvious
  repair to §1.
- **One positive cell in ten, and it is not credible on this data.** The +0.15R
  breakeven stop is the only variant above zero and it holds in both halves — but
  +0.15R on a median 2.3-point stop is **0.35 points, three and a half ticks**. Whether
  that level was touched before the stop is a path question, and 1-minute OHLC cannot
  answer path questions at three-tick resolution. Treat it as the single best reason to
  buy sub-minute data, not as a result.

The "just take the trades that pay" filter fails the same way:

| min reward:risk | n | win % | mean win | EV | 95% CI |
|---|---|---|---|---|---|
| none | 2411 | 67.9 | 0.44 | −0.0232 | [−0.056, +0.009] |
| ≥ 0.4 | 1203 | 52.5 | 0.85 | −0.0282 | [−0.088, +0.034] |
| ≥ 0.6 | 840 | 45.8 | 1.08 | −0.0455 | [−0.130, +0.038] |
| ≥ 0.8 | 561 | 42.4 | 1.32 | −0.0152 | [−0.123, +0.094] |
| ≥ 1.0 | 418 | 40.7 | 1.50 | +0.0151 | [−0.124, +0.146] |
| ≥ 1.5 | 173 | 34.1 | 2.08 | +0.0507 | [−0.191, +0.308] |

It turns positive at ≥1.0R — on +6.3R total across 338 days, with an interval nine
times wider than the estimate, and a non-monotone path to get there. That is not a
filter, it is a smaller sample.

## 7. Costs finish it

| round-turn cost | mean cost in R | EV | win % |
|---|---|---|---|
| 0 ticks | 0 | −0.0232 | 67.9 |
| **1 tick** | 0.0546 | **−0.0778** | 61.3 |
| 2 ticks | 0.1091 | −0.1323 | 54.5 |
| 3 ticks | 0.1637 | −0.1869 | 49.0 |

A single tick of round-turn friction is 5.5% of average risk, because the stops are
tiny — median 2.3 points. It more than triples the loss. Nothing found in this autopsy
survives one tick.

## 8. Anatomy, for the record

Post-entry and therefore never offered to any model (BR-41), but it describes the thing:

| exit | n | share | mean R | median hold |
|---|---|---|---|---|
| target | 1633 | 67.7% | +0.4385 | **2 min** |
| stop | 775 | 32.1% | −1.0000 | 6 min |
| timeout (240 min) | 3 | 0.1% | +0.9702 | 240 min |

This is a two-minute scalp, not a reversal trade. Of the losers, 65.9% went at least
+0.1R into profit first, 49.9% reached +0.2R, and 21.0% reached +0.5R — which is why
§6's tight breakeven stop moves the number, and why the resolution question in §6 is
the binding one.

By year: 2023 +0.006, 2024 −0.068, 2025 −0.016, 2026 −0.010. Never meaningfully
positive; 2024 is the only interval clear of zero, and it is negative.

By session — the one stratum the permutation null cannot test, since outcomes are
shuffled within it, so read as intervals:

| session | n | win % | EV | 95% CI |
|---|---|---|---|---|
| **asia** | 788 | 66.0 | **−0.0585** | [−0.113, −0.004] |
| london | 542 | 69.6 | −0.0258 | [−0.086, +0.035] |
| ny | 994 | 68.4 | +0.0040 | [−0.046, +0.056] |

Asia is the session he trades and says he trades every day, and it is the only one whose
interval is clear of zero — barely, with an upper bound of −0.004, on one of four cells.
Note the direction of that.

On his clock, uncapped and with C2 off, win rate declines monotonically from 75.1% in
the first quintile to 62.2% in the last, and EV shows no pattern at all (−0.019, −0.015,
−0.010, −0.055, −0.014). The ablation report found the same decline and an empty 0–9
bucket; the bucket is populated here because C2's 20-minute requirement is off in this
population.

---

## What this establishes, and what it does not

**Does.** On GC, at these parameters, with no costs: the method's losses are not a
selection problem. Nothing observable at entry separates winners from losers once the
payoff is held fixed, the best out-of-sample fifth of the book is flat, his clock and
his daily cap are worth nothing or less, larger targets are strictly worse, and one tick
of cost triples the loss. The failure is in the geometry — a target at 50% of the
impulse with a stop beyond the pattern extreme — and it is not reachable by filtering.

**Does not.** Falsify the method. This is a futures proxy for his instrument, at
1-minute resolution when he trades a 5-second chart, at one parameter point rather than
the sweep the confluence table specifies. Two results now point at the same missing
thing: 6,073 signals skipped because the target was gone before the fill, and a
breakeven variant that turns on a three-tick path question. **Sub-minute data is the
binding constraint on every open question here**, ahead of any further parameter work.

Next, in order of expected information: (1) re-run on 5-second GC — both open questions
need it; (2) test the target/stop geometry directly, which §2 and §6 both identify as
where the arithmetic fails; (3) re-test sweep depth on that data before treating it as
anything more than a candidate.

Per the repo's non-negotiables, these divergences are reported, not fixed. No parameter
was adjusted to improve any number above, and the variant menus in §6 are reported whole
so the best cell can be read against the size of the menu it came from.
