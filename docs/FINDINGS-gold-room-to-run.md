# FINDINGS — ROOM-TO-RUN ON GOLD

Run against `DECLARATIONS-gold-room-to-run.md`, written and committed before the run.
GC front month, 104,423 fights → **69,729 first-of-fight rows over 932 session-days** at
the 0.2-point risk floor, shipped exit, assumed 0.20-point round turn.

**Pipeline check first.** The same population reproduces `vah · break` at **+0.111R**
[+0.064, +0.158], H1 +0.092 / H2 +0.131, both eras — identical to
`FINDINGS-gold-level-census.md`. The room columns are bolted to a census that reproduces.

---

## THE FOUR PREDICTIONS, SCORED

| # | prediction | outcome |
|---|---|---|
| 1 | open space clears both eras, ≥3R does not | **SPLIT — direction right, but pooled open space fails the era bar under the declared cost** |
| 2 | if ≥3R shows an edge, its floor sweep is non-monotone | **antecedent false, and gold's sweep is MONOTONE — a different failure mode from NQ's** |
| 3 | the bundled BR-32/35 form lands between the arms | **CONFIRMED — it lands on exactly zero** |
| 4 | open space is rare (5.8–7.0% on NQ) | **REFUTED — 16.0% on gold, ~2.5×** |

## 1 — THE DECOMPOSITION

| cell | n | win% | EV | 95% | H1 | H2 | both eras |
|---|---|---|---|---|---|---|---|
| BASELINE (all, risk≥0.2) | 69,729 | 32.66 | **+0.000** | [−0.018, +0.019] | −0.081 | +0.088 | — |
| **A · OPEN SPACE** | 11,140 | 33.56 | **+0.088** | [+0.049, +0.126] | +0.001 | +0.200 | — |
| **B · ROOM ≥ 3R** | 3,688 | 26.84 | **−0.267** | [−0.327, −0.204] | −0.419 | −0.170 | — |
| **C · BUNDLED (BR-32/35 form)** | 14,828 | 31.89 | **−0.000** | [−0.034, +0.034] | −0.078 | +0.084 | — |
| **A · open space · break** | 5,374 | 34.28 | **+0.133** | [+0.089, +0.179] | +0.082 | +0.195 | **BOTH** |
| A · open space · reject | 5,766 | 32.88 | +0.047 | [−0.007, +0.101] | −0.070 | +0.206 | — |

**BR-53's decomposition holds on gold.** The two halves of the BR-32/35 gate point in
opposite directions — open space **+0.088**, room-≥3R **−0.267** — and bundling them
produces **−0.000 [−0.034, +0.034]**. Not "a weak edge": zero, to three decimals, on
14,828 rows. That is as clean a demonstration as the ledger contains that the gate was
two claims wearing one name, and it is why porting BR-32/35 unexamined would have
returned nothing and taught nothing.

**The only cell clearing the E1.4 both-era bar is `open space · break`, +0.133R.** Pooled
open space does not clear it: H1 is **+0.001**, indistinguishable from zero, against H2
+0.200. The whole pooled effect lives in the second half of the sample, which is exactly
the pattern E1.4 exists to catch.

**Dual currency agrees throughout** (Law 3). Open space lifts win rate 32.66 → 33.56% and
EV together; the ≥3R arm drops both (26.84%, −0.267). No inversion of the BR-20/46/48
kind anywhere in this table.

## 2 — MOST OF THE GRADIENT IS THE COST DENOMINATOR

**This is the finding that governs everything above.** `next_lvl_R` is a distance divided
by risk, so it is a risk-coupled feature and Law 2 requires it be flagged. On gold the
coupling is not a footnote — it manufactures the headline.

`spearman(next_lvl_R, risk) = **−0.202**`. A row qualifies for a high room floor partly by
having a *small stop*, and a small stop pays the fixed 0.20-point round turn as a **larger
fraction of R**:

| floor | n | median risk | cost burden |
|---|---|---|---|
| ≥1.0R | 16,489 | 1.400 pt | +0.143 R |
| ≥2.0R | 7,011 | 1.151 pt | +0.174 R |
| ≥3.0R | 3,688 | 1.000 pt | +0.200 R |
| ≥5.0R | 1,486 | 0.800 pt | +0.250 R |
| all rows | 69,729 | 1.961 pt | +0.102 R |
| **open space** | 11,140 | **2.300 pt** | **+0.087 R** |

Cost enters the census once, as `cost = COST_PTS / risk`, so it can be removed exactly.
Doing so collapses the sweep:

| floor | EV with cost | EV cost removed |
|---|---|---|
| ≥1.0R | −0.138 | **+0.059** |
| ≥1.5R | −0.162 | +0.054 |
| ≥2.0R | −0.203 | +0.029 |
| ≥3.0R | −0.267 | **−0.005** |
| ≥4.0R | −0.297 | −0.011 |
| ≥5.0R | −0.312 | −0.007 |

**A steep monotone decline spanning 0.174R becomes a nearly flat line spanning 0.070R
that is indistinguishable from zero past 3R.** The "more room is worse" gradient is
roughly 60% an artifact of dividing a fixed cost by a shrinking denominator.

This is BR-32's own warning arriving with its sign reversed. On NQ the note reads
"confound runs AGAINST it — small stops inflate the ratio AND predict bad outcomes". On
gold, with a 0.20-point cost against a 1.0-point median stop in the gated cell, the
confound does not merely run against the gate: it *creates* the negative result.

### What survives the correction

| | with cost | cost removed |
|---|---|---|
| open space lift vs baseline | **+0.088** [+0.054, +0.122] | **+0.062** [+0.031, +0.096] |
| ≥3R lift vs baseline | −0.267 [−0.329, −0.205] | **−0.154** [−0.214, −0.094] |
| open space · break lift | **+0.133** [+0.095, +0.170] | **+0.095** [+0.058, +0.133] |

Both real effects survive, smaller. Open space is worth **+0.062R** as a market fact
rather than the +0.088R the cost-laden book shows — about 30% of its apparent lift was
also the denominator, in its favour this time, because open-space rows carry *wider* stops
(2.300 vs 1.961 median) and so pay less cost in R.

And the ≥3R arm's *absolute* loss is entirely cost: **−0.005 [−0.063, +0.057]**, spanning
zero, once the round turn is removed. What remains real is its **relative** shortfall,
−0.154R against the baseline. A distant level ahead genuinely predicts underperformance.
It does not predict a losing trade.

**Cost-sensitivity warning.** Every figure here inherits an *assumed* 0.20-point round
turn that queue item 1 has still not measured, and `ohlcv-1m` cannot measure. The ≥3R
result is the **most** cost-sensitive number in this document precisely because that cell
has the smallest stops: at a 0.10-point true round turn it gains ~+0.10R and the refutation
softens to a shortfall. Open space, with the widest stops in the book, is the least
sensitive. **The ranking of these arms is robust to the cost assumption; their signs are
not.**

## 3 — IS IT JUST `vah · break`?

Gold's one prior survivor is `vah · break`. Open space is **not** a relabelling of it —
vah is 31.0% of the open-space break cell, and the remaining 69% spreads across val
(23.8%), vwap_m1 (21.9%) and vwap_p1 (20.1%).

| cell | n | EV | 95% | H1 | H2 | both eras |
|---|---|---|---|---|---|---|
| `vah · break`, all (the incumbent) | 3,838 | +0.111 | [+0.064, +0.158] | +0.092 | +0.131 | **BOTH** |
| `vah · break` **and open** | 1,667 | **+0.146** | [+0.070, +0.220] | +0.160 | +0.132 | **BOTH** |
| `vah · break`, level ahead | 2,171 | +0.083 | [+0.022, +0.146] | +0.045 | +0.130 | — |
| open · break **excluding vah** | 3,707 | +0.127 | [+0.077, +0.182] | +0.050 | +0.227 | — |

**Open space carries information the incumbent does not.** It splits `vah · break` into
+0.146 and +0.083, and the level-ahead half stops clearing both eras. That is a genuine
+0.035R increment on gold's only established candidate, from a variable that costs nothing
to compute and is pure bar geometry.

But the both-era robustness is **anchored on vah**. The non-vah 69% reads +0.127 pooled
with H1 +0.050 against H2 +0.227 — era-unstable, and not something to build on yet.

## 4 — WHAT THIS DOES AND DOES NOT ESTABLISH

**Does:** the BR-53 decomposition transfers to gold. The bundled BR-32/35 gate is worth
exactly zero here, the ≥3R arm underperforms, and open space is a real incremental
variable worth +0.062R on the market-fact basis and +0.035R stacked on `vah · break`.

**Does not:** confirm anything. §5 of the declaration said this in advance and it stands —
the whole GC sample was already spent on the level census, so every number here is
fit-side. It also does not license a magnitude comparison against NQ's +1.518R: that was
measured on the LTF trigger recensus at 3m/5m, a population gold does not have, and gold's
open-space share is 16.0% against NQ's 5.8–7.0%, so the two "open space" populations are
not the same object.

**One cross-instrument difference worth recording.** BR-35 found that on NQ "the BREAK arm
does not carry it (3m +0.051) — refuting the declared prediction that room would favour
breaks". On gold the break arm is the *only* thing that carries it: +0.133 both eras,
against reject's +0.047 clearing nothing. Gold's edge has now landed on the break arm
twice, independently — `vah · break` and now open space. Whatever that is, it is a
property of gold and not of the method.

## 5 — WHAT TO DO NEXT

1. **Measure the round turn.** It was queue item 1 before this run and this run raises it:
   two of the three headline signs here are decided by a number nobody has measured.
2. **Do not adopt anything.** Fit-side, and a real confirmation needs GC data the analysis
   has not touched — a later-dated export, not a re-split of this one.
3. **`vah · break ∩ open space` is the candidate worth carrying** at +0.146R, both eras,
   1,667 rows — **1.79/day across all 932 session-days, but it appears on only 650 of them
   (70%), at 2.56/day when it appears.** State it the second way: a book that is absent
   three days in ten is a different operational proposition from one that trades daily, and
   BR-37/39 are on the record that frequency is not a nuisance parameter. It is not a new
   locus; it is the incumbent with a free filter.
