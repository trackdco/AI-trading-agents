# FINDINGS — THE OPEN-SPACE RESTATEMENT

Run against `DECLARATIONS-open-space.md`, **written and committed before
the run**. Fit-only, no holdout contact, report-only. New York untouched.

## THE THREE PREDICTIONS, SCORED

| # | prediction | outcome |
|---|---|---|
| 1 | the base rate replicates on the split-half | **CONFIRMS — and beats its own bar** |
| 2 | open-space-only loses SIM graduation to the bundled stream on frequency | **SPLIT: loses at 3m (meaninglessly), WINS at 5m** |
| 3 | if 2 happens, check whether LIVE dollars favour open-space anyway | **at 5m it wins BOTH; at 3m it loses both, narrowly** |

## 1 — THE CONFIRMATION

Frozen split, seed 20260807, defined over all 292 fit days so it does not
move with the population. 146 / 146.

| population | exit | Half 1 | Half 1 95% | Half 2 | Half 2 95% |
|---|---|---|---|---|---|
| open 3m | V1 | **+1.768** (n=39) | [+0.987,+2.456] | **+1.315** (n=48) | [+0.396,+2.247] |
| open 5m | V1 | **+1.533** (n=47) | [+1.001,+2.065] | **+1.237** (n=53) | [+0.485,+1.948] |
| open 3m | V2 | +1.522 | [+0.887,+2.064] | +1.156 | [+0.534,+1.773] |
| open 5m | V2 | +1.476 | [+1.049,+1.904] | +1.251 | [+0.589,+1.864] |

**All four cells confirm, and by more than the declared bar.** The bar was
sign agreement plus half the magnitude; what actually happened is that
**both halves' CIs clear zero independently**, on both timeframes and under
both exits, with Half 2 retaining 74–85% of Half 1's magnitude.

That is as strong as a fit-side confirmation gets. It is still fit-side —
see the closing section.

## 2 — THE EXIT: V2 IS WORSE HERE, and that refines BR-55

| population | V1 (15m trail) | V2 (trigger-TF trail) | delta |
|---|---|---|---|
| open 3m | **+1.518** | +1.320 | **−0.198** |
| open 5m | **+1.376** | +1.357 | −0.019 |

**This is the opposite of BR-55**, where re-anchoring the trail was a free
improvement on the bundled stream. The mechanism is coherent and worth
stating as a rule:

> **Re-anchor the trail when there is a level ahead. Keep the wide trail
> when there is not.** Open-space trades run a long way (median MFE 4.45R,
> P(≥3R) = 56.5%); a 3m trail cuts them off early. A 15m trail gives them
> room to run.

BR-55's "free improvement" was measured on the bundled stream, which is
74% level-ahead rows — so it netted positive there while being negative on
this quarter. **The trail timeframe should follow the obstacle structure,
not the trigger timeframe alone.**

## 3 — FULL BATTERY

**MFE-in-R** (bounded by the stop) — this population is in a different
regime from anything measured so far:

| population | /day | p25 | p50 | p75 | p90 | p95 | P(≥3R) |
|---|---|---|---|---|---|---|---|
| open 3m | 0.30 | 1.50 | **4.45** | 10.24 | 23.05 | 42.80 | **56.5%** |
| open 5m | 0.34 | 0.90 | **4.34** | 7.34 | 16.17 | 35.60 | **58.0%** |
| *(the full room-gated 3m book, for scale)* | 1.14 | 0.02 | 1.34 | 5.72 | 21.04 | 35.29 | 38.0% |

Median MFE is **3.3× the parent book's**, and P(≥3R) rises from 38% to 57%.

**Clustering-X:** +0.866 / **+1.518** / +1.990 / +1.070 at X = 0.25 / 0.5 /
1.0 / 2.0W (3m). Positive at every X, and **the declared 0.5W is not the
peak** — 1.0W is. Not tuned.

**Cost:** +1.518 → +1.452 → +1.386 across 0.5 / 1.0 / 1.5pt. Essentially
immune — the wins are large enough that round-trip cost is noise.

**Risk floor removed:** +1.518 → +1.356 (3m, 5 extra rows); 5m unchanged at
+1.377. The 2pt floor is **not** doing the work here.

## 4 — REDUNDANCY AND CONCURRENCY, measured fresh

| stream | n | redundant | concurrent |
|---|---|---|---|
| open-space 3m | 87 | 6.9% | **37.9%** |
| open-space 5m | 100 | 11.0% | **40.0%** |
| *(bundled, for comparison)* | 334 | 6.6% | 22.2% |

Redundancy carries over. **Concurrency does not** — it is 1.6–1.7× the
bundled figure, because open-space trades stay open far longer. Checking it
fresh was the right call.

Yet worst-day R does **not** degrade (below). That is BR-25 restated:
overlapping positions are not the binding constraint; daily total R is.

## 5 — THE ACCOUNT LAB, three-way

| book | /day | EV | R/day | worst | max size | SIM grad | LIVE $/yr |
|---|---|---|---|---|---|---|---|
| 1. incumbent alone | 2.27 | +0.357 | 0.813 | −5.41 | $350 | 98.5% | $28,501 |
| 2. inc + bundled 3m | 3.42 | +0.420 | **1.437** | −6.88 | $250 | 100.0% | **$35,599** |
| 3. inc + open-space 3m | 2.57 | +0.492 | 1.265 | **−5.41** | **$350** | 99.9% | $34,922 |
| 2. inc + bundled 5m | 3.33 | +0.375 | 1.247 | −6.74 | $250 | 99.7% | $32,691 |
| **3. inc + open-space 5m** | 2.62 | **+0.491** | **1.284** | **−5.41** | **$350** | **100.0%** | **$37,820** |

Deltas against the incumbent alone:

| addition | /day | R/day | worst | max size | GRAD | LIVE |
|---|---|---|---|---|---|---|
| bundled 3m | +1.14 | +0.624 | **−1.47** | **−$100** | +1.5pp | +$7,098 |
| open-space 3m | +0.30 | +0.452 | **+0.00** | **+$0** | +1.5pp | +$6,421 |
| bundled 5m | +1.05 | +0.434 | **−1.33** | **−$100** | +1.2pp | +$4,190 |
| **open-space 5m** | +0.34 | **+0.471** | **+0.00** | **+$0** | +1.5pp | **+$9,320** |

**The structural point, which matters more than which one wins:**
open-space adds **72% of the bundled stream's R/day at 26% of its trade
count — and costs nothing in worst-day R or position size.** The bundled
stream pays for its extra R/day with a $100 reduction in carryable size;
open-space does not.

At **5m, open-space-only is strictly better than the bundled combination on
every axis measured**: more R/day (+0.471 vs +0.434), better worst day
(−5.41 vs −6.74), larger size ($350 vs $250), higher graduation (100.0% vs
99.7%), and **+16% live dollars** ($37,820 vs $32,691).

**Prediction 2 was wrong at 5m, and that is the headline** — as declared it
would be. It was right at 3m only in a degenerate sense: 99.9% vs 100.0% is
**saturation, not a difference**. The SIM-stage graduation metric has no
resolution left at the top of this range, and comparisons there should not
be read as rankings.

## 6 — WHAT THIS DOES AND DOES NOT ESTABLISH

**Establishes, on fit:** the open-space restatement replicates on a frozen
split-half with both halves clearing zero independently; it is robust to
clustering width, cost, and the risk floor; it adds R/day without costing
worst-day R or size; and at 5m it dominates the bundled gate it replaces.

**Does not establish:** anything out of sample. A split-half on the same
fit data is a **stability check, not a confirmation** — and the population
was found by decomposing a published gate, which is the provenance the
programme distrusts most. n is 87 and 100.

**The real test is the bar-only holdout venue.** `next_lvl_R` is pure bar
geometry, so open-space belongs on the 23-month bar-only venue (Blocks A
and B, both must pass) and joins holdout look #1's claim list — replacing
the bundled room gate on that list rather than adding to it.

**Consequence for the existing record:** BR-32 and BR-35 are superseded by
this restatement, not merely qualified. The bundled `≥3R OR open` gate
should not be carried forward as a candidate — its threshold arm was shown
non-monotone and non-replicating (BR-54), and its open arm is this.

Nothing is adopted. New York remains untouched.
