# FINDINGS — FLOW CONCORDANCE, DEPTH, IN-TRADE (one run, 2026-08-07)

Prereg: `PREREG-flow-depth-intrade.md`, committed 6531deae before any
number below existed. One table walk, one frame
(`output/htf_ma_census/bc_frame.parquet`, 3,336 rows × 60 cols), every
candidate scored off it. Bonferroni ×10. Fit-only; **no sealed row
touched**; parallel to holdout look #1.

**Headline: the wall-quality cut reproduced its win-rate claim almost
exactly — 37.5–41.5% against the canon's 37–41% — and its EV goes the
other way. The canon selected on hit rate and paid for it in R.**

---

# A — THREE AUDIT QUERIES

## A1 — the 18 candidates by data family, with survival

| family | candidates | H1 survivors | H2 confirmed |
|---|---|---|---|
| trade-based flow (footprint delta / CVD) | **8** — flowconf, thru_delta_conf, d5/d15/d30_conf, bp5opp, delta_z, cvd_slope30 | 5 | **1** (S1) |
| volume / efficiency | **2** — volx, eff_result | 2 | 0 |
| bar geometry | **3** — closeloc, rangex, pen_bw | 2 | 0 |
| level structure | **4** — cnt_ahead_1w, cnt_beyond_3r, confluence_count, admissible_snapshot | 1 | 0 |
| session / operational | **1** — ny_pm | 1 | 0 |
| **book-based depth** | **0** | — | — |
| **dedicated volatility** | **0** (rangex is bar geometry) | — | — |
| total | **18** | 10 | 1 |

**Answers.** Flow was *not* barely represented — it was the single
largest family, 8 of 18, and its 10 members (with volume) are 10 of 18.
The one confirmed survivor in programme history is a flow feature. **Depth
was not in the list at all — zero of eighteen.** Neither was any dedicated
volatility measure. So the "flow was undertested" hypothesis is wrong as
stated; the true gap is that flow was tested **one feature at a time**
(the object B1 addresses) and that **the book was never tested at all**
(the gap B2/B3 addresses).

## A2 — what the twelve flow features actually are

All twelve are **trade-tape (footprint) derived. None is book-derived.**
Resolutions span 1–30 minutes; every one is as-of the decision bar.

| feature | family | resolution |
|---|---|---|
| flowconf | trade flow, directional | the 15m decision bar |
| thru_delta_conf | trade flow, directional | final 1 minute |
| d5_conf / d15_conf / d30_conf | trade flow, directional | 5 / 15 / 30 min pre-bar |
| cvd_slope30 | trade flow, directional | 30-min OLS slope |
| delta_z | trade flow, directional | bar delta z-scored vs prior 20 bars |
| bp5opp | trade flow, opposing | last 5 minutes |
| volx | volume magnitude | bar vs prior-20 median |
| eff_result | volume / range efficiency | the 15m bar |
| closeloc | bar geometry | the 15m bar |
| rangex | bar geometry | bar vs prior-20 median |

**All twelve appeared among the 18** — they are candidates 1–12; the other
six are the four level-structure variables, pen_bw and ny_pm.

## A3 — MBP-10 reach, now a standing constraint

Written to `docs/CONSTRAINT-mbp10-reach.md`, **measured not asserted**:

| side | median L0→L9 span | p90 | max |
|---|---|---|---|
| bid | **2.25 pt** | 2.50 | 3.25 |
| ask | **2.25 pt** | 2.50 | 3.00 |

"Is there a wall right here?" (within ~2.25 pt / 9 ticks) is answerable.
"Is there a magnet 30 points away?" is **~13× beyond the deepest published
level** and is not. Any feature referencing distances beyond ~2.5 pt
measures the absence of data, will look stable because it is mostly
constant or NaN, and means nothing. Deep-book magnet ideas need MBO/
full-book and are out of scope on MBP-10.

**Coverage is a second, separate limit** — NY 08:00–10:29 (381 files),
London 02:00–05:58 (22), MBP-10 raw 03:00–04:59 (423): **799 of 3,336
composite fights = 24.0%**, and the eligible subpopulation is
better-than-average (EV **+0.287** vs +0.186). Declared in the prereg as a
confound, not discovered as one.

---

# B — RESULTS

## B1 — FLOW CONCORDANCE COUNT: real signal, MISSES its gate bar

CONCORD = unweighted count of the twelve features agreeing with trade
direction, 0–12. Zero free parameters, no weights, no combo search. **One
candidate, not twelve.**

*Monotone first (Law 8), EV by CONCORD bin:*

| CONCORD | break n | break EV | reject n | reject EV |
|---|---|---|---|---|
| 0–4 | 224 | **+0.038** | 509 | **+0.049** |
| 5 | 195 | +0.228 | 252 | +0.260 |
| 6 | 227 | +0.369 | 261 | +0.100 |
| 7 | 241 | +0.220 | 268 | +0.168 |
| 8 | 251 | +0.176 | 192 | +0.235 |
| 9–12 | 368 | +0.305 | 348 | +0.192 |
| **Spearman ρ** | 1,506 | **+0.093** | 1,830 | **+0.129** |

The relationship is real and positive on **both arms** — and it is a
*bottom-bin* effect, not a ladder: CONCORD ≤ 4 runs +0.038/+0.049 against
a book of +0.186, and above 5 the bins are noisy with no ordering.

*Gate second (Law 7), whole-book:*

| cut CONCORD < | q | μ_cut | book lift | half-1 lift | half-2 lift |
|---|---|---|---|---|---|
| 4 | 12.3% | −0.039 | +0.032 | +0.028 | +0.035 |
| 5 | 22.0% | +0.045 | +0.039 | +0.054 | +0.023 |
| 6 | 35.4% | +0.121 | +0.035 | +0.056 | +0.012 |
| 7 | 50.0% | +0.152 | +0.034 | +0.053 | +0.014 |
| 8 | 65.3% | +0.161 | +0.046 | +0.090 | **−0.004** |

**VERDICT: MISS on the declared bar.** No threshold reaches +0.05R on the
full book (max +0.046), and every threshold that looks like a half-1
survivor (+0.053…+0.090) collapses on half 2 (+0.023…−0.004). The
split-half did exactly its job.

**Why it misses, and it is Law 7 not bad luck:** the worst bin is still
*profitable*. At CONCORD < 5 the removed trades average +0.045R. You
cannot gate your way to +0.05R by removing trades that make money. The
concordance count is a genuine *ranking* variable with no *gate* value on
this book.

Per Law 8 and the A-2 precedent, a sizing weight was **not** run: the
arithmetic does not support it — a ladder over a ρ of 0.09–0.13 is
precisely the configuration that bled 0.12 ρ to 0.01R in A-2.

## B2 — WALL-QUALITY CUT: the win-rate claim reproduces, the EV inverts

`dep_wall_below_d < 2.75 OR WALLSZ == 0`, as-of the decision bar,
entry-price gate enforced, on the window-bounded depth-eligible set
(793 fights).

| arm | n | cut % | μ_cut | kept EV | **cut win%** | kept win% | eligible lift | book lift |
|---|---|---|---|---|---|---|---|---|
| break | 327 | 12.5% | +0.360 | +0.305 | **41.5%** | 36.0% | −0.007 | −0.002 |
| reject | 466 | 70.4% | +0.319 | +0.154 | **37.5%** | 32.6% | −0.116 | −0.015 |
| both | 793 | 46.5% | +0.324 | +0.256 | **37.9%** | 34.9% | −0.032 | −0.017 |

**The canon's number reproduces almost exactly.** It claimed 37–41% win
rate on the cut set across three eras; measured clean, on a different
book, with a different entry model: **37.5% and 41.5%.** That is a real,
replicable property of the wall condition and the canon was not imagining
it.

**And it is the wrong currency.** The cut set's EV is **+0.324R against
the kept set's +0.256R** — the trades the rule removes are *better* in R,
because they win less often and win bigger. Every lift is negative;
cutting them costs money on both arms.

This is Law 3 (dual currency) in its purest recorded form: hit rate and R
have **opposite signs** on this variable. The canon selected on win rate
and paid in expectancy. **The wall-quality cut is refuted as an EV gate —
for the first time, on an uncontaminated measurement.** It was never
refuted before because it was never measurable before.

## B3 — REMAINING DEPTH FEATURES: all dead

Bottom-quartile cuts on the eligible set:

| feature | cut % | μ_cut | eligible lift | book lift |
|---|---|---|---|---|
| support_wall_dist | 16.4% | +0.183 | +0.020 | +0.000 |
| dep_thickness_vs_day | 25.0% | +0.296 | −0.003 | −0.007 |
| support_wall_size | 16.6% | +0.348 | −0.012 | −0.007 |
| dep_imbalance | 24.8% | +0.364 | −0.025 | −0.011 |
| dep_thickness_delta_5m | 24.0% | +0.362 | −0.024 | −0.011 |
| support_minus_resist | 23.5% | +0.411 | −0.038 | −0.013 |

Not one clears; five of six are negative. Every removed bin is
comfortably profitable — the same Law-7 wall B1 hit. **The book, as
visible through MBP-10 at the decision bar, carries no EV gate for this
book.** Note this is a statement about a 2.25-pt-deep book on 24% of the
population, not about market depth in general.

---

# C — IN-TRADE CENSUS

## C1 — does in-trade flow separate recoverers? Weakly, and the count loses

Trades underwater at t+N, P(recover) = P(out_ship > 0):

| N (min) | underwater | base P(recover) | flag cum>0: fires | **precision** | recall | CONCORD≥3: fires | precision | recall |
|---|---|---|---|---|---|---|---|---|
| 1 | 1,612 | 23.4% | 17.8% | **31.0%** | 23.6% | 10.8% | 28.2% | 13.0% |
| 2 | 1,592 | 22.0% | 17.5% | **31.7%** | 25.1% | 13.1% | 27.8% | 16.5% |
| 3 | 1,598 | 19.4% | 17.4% | 27.0% | 24.2% | 14.3% | 24.5% | 18.1% |
| 5 | 1,617 | 17.3% | 19.0% | 21.8% | 24.0% | 16.3% | 19.7% | 18.6% |
| 10 | 1,640 | 12.4% | 18.2% | 17.4% | 25.6% | 16.3% | 17.2% | 22.7% |

**Yes, weakly.** The cumulative-delta sign lifts precision from a 23.4%
base to 31.0% at t+1 (+7.6pp) and from 12.4% to 17.4% at t+10 (+5.0pp).
But **recall is only ~24–26%** — it catches a quarter of the recoveries,
so it cannot be a "hold" rule; at best a "the odds just improved" tag.

**The declared question is answered NO: the in-trade concordance count
does not beat the best single feature.** CONCORD≥3 gives 28.2% precision
against the single flag's 31.0% at t+1, and is worse or equal at every
horizon. Unlike at the trigger — where counting solved the multiplicity
problem — in-trade the count *dilutes*: it mixes four signals that are
largely the same information at different smoothings.

EV of underwater trades by IN-CONCORD at t+5 is non-monotone at the top
(0: −0.481 · 1: −0.417 · 2: −0.229 · 3: −0.225 · **4: −0.349**), which
confirms the dilution rather than a ladder.

## C2 — the +2R-then-stopped tell: the prior was right, and the test is confounded

| group | n | it5_cum | it10_cum | it10_concord |
|---|---|---|---|---|
| mfe ≥ 2R, finished positive | 909 | +92.0 | +147.8 | 2.69 |
| mfe ≥ 2R, finished negative | 155 | +9.0 | −10.0 | 2.04 |

There is a difference, and **it should not be read as a tell.** In-trade
flow at t+5/t+10 is measured over the same minutes whose price action
determines the outcome, so winners having better in-trade flow is close to
tautological. This is a **confound, declared here rather than sold as a
finding**: to be a usable tell the measurement would have to be taken at
the +2R peak and predict what happens *after* it, and the table does not
record the peak minute. n=155 on the negative side is thin regardless.

**Recorded as: prior upheld, no actionable tell, and the test as
constructed cannot establish one.** A proper version needs peak-time
instrumentation in the builder — queued, not run.

---

# What this round settles

1. **Depth is refuted as an EV gate on this book** — and the canon's
   wall-quality finding is explained rather than merely dismissed: it was
   a true win-rate effect with the opposite R sign. Two voided canon
   findings are now measured; one (wall) is refuted, one (graded flow
   confluence) is reduced to a real-but-ungateable ranking signal.
2. **Counting agreements was the right idea and the right multiplicity
   fix** — one candidate, zero free parameters, positive ρ on both arms —
   **but the book's worst flow bin is still profitable**, so there is
   nothing to gate. That is a Law 7 outcome, not a measurement failure.
3. **In-trade flow is weak-but-real for recovery, and the count does not
   help in-trade.** Precision +5–8pp at ~25% recall.
4. Nothing here survives to a holdout. Per R0, no selection layer goes to
   the sealed venue; anything that had survived would ship on fit +
   forward validation via the seven-locus recorder.

## Base-rate library

BR-19 (concordance count), BR-20 (wall-quality dual-currency inversion),
BR-21 (depth features null), BR-22 (in-trade recovery precision/recall)
added to `BASE-RATES.md`.
