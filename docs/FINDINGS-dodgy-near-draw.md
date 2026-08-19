# FINDINGS — the near draw set, E5 rule 4, and the equal-highs ladder, on 08:30–11:00

NQ, 1,251,240 one-minute bars, 2023-01 → 2026-07. **Restricted to 08:30–11:00 ET entries
per the operator's instruction: 9,802 of 85,277 signals (11.5%).** Every earlier result in
this stream carried 88.5% of its weight in hours he tells students to avoid, so this is the
first run measured on the population he actually trades. Corrected detector
(`require_revisit` enforced), 2-point risk floor, 240-bar max hold, 0.5-point round turn,
day-clustered intervals, both eras, win% and EV together, dollars beside R.

This closes the three items `FINDINGS-dodgy-structural-target.md` left open. Two of them
land against me: one is a bug in my own harness, the other demotes the rule I had ranked
as the lecture's most valuable new predicate.

---

## 0 — FIRST: a contamination in my own structural test

`signals()` sets `target 1` to the last confirmed swing, and **falls back to a manufactured
`close + 1R` when no confirmed swing survives ahead of price.** That is 31.2% of the book
and 28.0% in-window. `dodgy_structural_target.py` fed that column into the draw set as a
target candidate — so **24.4% of the published "structural" arm's targets were a synthetic
1R, not a level the market ever printed.**

Since the synthetic sits exactly 1R away it wins the nearest-level contest almost every
time it appears, which is precisely how it poisoned the median.

| full book | n | win % | EV | median RR | $/trade |
|---|---|---|---|---|---|
| fixed 2R (incumbent) | 81,038 | 32.80 | −0.128 | 2.00 | −$11.31 |
| structural, **as published** | 79,971 | **43.06** | −0.143 | **1.07** | −$13.50 |
| structural, **synthetics removed** | 78,761 | **33.25** | −0.141 | **2.14** | −$13.71 |

**The verdict survives and the explanation does not.** Structural is still worse than fixed
2R, in R and in dollars. But the published mechanism — *"the pool is nearer than two units
of risk… 43.1% at ~1.07R loses to 32.8% at 2R"* — was an artifact of the manufactured
target. The real nearest structural pool sits at **2.14R, slightly FURTHER than 2R**, and
the win rate is **33.25%, not 43.06%**. The headline +10.3pp win-rate gain does not exist.
See `FINDINGS-dodgy-structural-target.md` CORRECTION 1.

---

## 1 — The additive near draw set cannot move the result, and that is arithmetic

L1 equal highs and L9 intermediate-term were the stated bound on the structural result —
*"the only route by which a structural target could be argued to have been tested
unfairly."* Both are now built with as-of semantics: a k=3 pivot is unknown until `i+3`,
dead once swept (`next_greater` gives the sweep bar in O(n)), and an equal-highs cluster
dies when its **extreme** is taken, not its newest member. 135,756 pivot highs, 134,735
lows.

Added to the existing draw set, they changed **nothing** — identical EV to three decimals
across every tolerance (0.25 / 2 / 5 points) and every combination.

**That is not a null result, it is a proof.** Under a *nearest-level-ahead* rule the extra
columns are unreachable by construction:

- an **equal-highs level is the maximum of a pivot cluster**, so it is never nearer than
  the nearest member of that cluster;
- an **intermediate-term high *is* a pivot high**, so it is never nearer than the nearest
  pivot high.

The nearest raw swing dominates both, always. **My caveat in the structural doc — "the gap
is unlikely to be hiding a rescue" — was too weak: an additive near draw set is incapable
of changing a nearest-target test at all.** The only informative version is an *exclusive*
draw set, where the level type actually selects the target.

## 2 — Exclusive draw sets: EV rises monotonically with target distance

| draw set | n | /day | win % | EV | 95% CI | H1 | H2 | median RR | $/trade |
|---|---|---|---|---|---|---|---|---|---|
| session boxes only (L3/L4/L6/L7) | 9,126 | 10.0 | 19.67 | **−0.089** | [−0.153, −0.019] | −0.062 | −0.116 | 6.95 | −$15.21 |
| L9 intermediate-term only | 9,236 | 10.1 | 23.20 | **−0.093** | [−0.146, −0.041] | −0.068 | −0.118 | 4.41 | −$14.18 |
| **his set**: boxes + L1 + L9, no raw swing | 9,436 | 10.3 | 29.22 | −0.104 | [−0.146, −0.058] | −0.095 | −0.113 | 2.94 | −$14.73 |
| **fixed 2R (incumbent control)** | 9,660 | 10.6 | 32.28 | **−0.109** | [−0.138, −0.080] | −0.129 | −0.089 | 2.00 | −$16.95 |
| swing only | 9,562 | 10.5 | 36.11 | −0.118 | [−0.157, −0.079] | −0.103 | −0.133 | 1.84 | −$18.09 |
| coarse + swing, synthetics removed | 9,572 | 10.5 | 38.92 | −0.123 | [−0.157, −0.090] | −0.120 | −0.127 | 1.56 | −$18.38 |
| structural as published (synthetics in) | 9,595 | 10.5 | 41.19 | −0.136 | [−0.167, −0.103] | −0.144 | −0.128 | 1.08 | −$17.55 |

*(L1-only rows omitted here and given in §3; tol=0.25 shown for his set, the tol sweep moves
it between −0.104 and −0.111.)*

**Sorted by EV, the table is sorted by median reward:risk.** Seven arms, monotone: 6.95 →
4.41 → 2.94 → 2.00 → 1.84 → 1.56 → 1.08 against −0.089 → −0.093 → −0.104 → −0.109 → −0.118
→ −0.123 → −0.136. Win rate runs monotonically the *other* way, 19.7% → 41.2%.

**The further the target, the better the expectancy — and every single arm is still
negative with its whole interval below zero.** This is the BR-46/48 dual-currency
inversion again, now traced across a continuum rather than two points: near targets buy hit
rate and sell expectancy, and no point on the curve reaches break-even. **The model does
not have a target problem. It has a trigger problem.** No arm clears both eras.

**Two arms beat the incumbent in both currencies at once** — session boxes (−0.089R,
−$15.21) and L9 (−0.093R, −$14.18) against fixed 2R's (−0.109R, −$16.95). That is a real
+0.016 to +0.020R and ~$2/trade, it is directionally his claim that targets should be
structure rather than a multiple, and **it is worth nothing operationally**: both remain
comfortably loss-making and neither clears E1.4.

## 3 — E5 rule 4 is inert, and it was my highest-ranked new predicate

*"The target must still be unswept… if you ever see like a Trump candle take out 50 million
highs or lows in the same candle do not enter, there's no more liquidity"*
(`WQycR82IOD4 @ 03:30:46` for the level vocabulary; rule text in
`RESEARCH-dodgysdd-lecture.md` §E5). I ranked it *"the most valuable new predicate in this
document — mechanical, unambiguous, cheap to code."* Tested as a **rejecting filter** with
the incumbent fixed-2R exit held constant, so it reads as trade selection and not as an
exit change:

| | n | /day | win % | EV | 95% CI |
|---|---|---|---|---|---|
| unfiltered | 9,660 | 10.6 | 32.28 | −0.109 | [−0.138, −0.080] |
| **E5r4 KEEP** (a level survives ahead) | 9,460 | 10.4 | 32.25 | **−0.110** | [−0.139, −0.082] |
| **E5r4 REJECT** (nothing left to take) | 200 | 1.5 | 33.50 | −0.068 | [−0.268, +0.129] |

**It rejects 2.0% of the book and moves EV by −0.001R.** Identical at all three tolerances,
because coverage is set by the session boxes and L9, neither of which depends on tol.

Worse for the rule than mere inertia: **the trades it throws away are not the bad ones.**
The rejected cell reads −0.068R against the kept cell's −0.110R — the wrong sign for the
rule, though on 200 trades the interval spans zero and this is not itself a finding.

**Status: refuted as stated.** It is unambiguous and cheap, as advertised; it simply almost
never fires, because on 1-minute NQ there is essentially always *some* unswept structure
ahead. A version that could bite would need the "obvious levels only" qualifier from E5
rule 2 — and rule 2 is already refuted (`FINDINGS-dodgy-ifvg.md`), so there is no
non-circular route to a stricter version from what he states.

## 4 — The L1 probability ladder: the levels are hit far more than he claims, and the wick count carries no information

His ladder (`WQycR82IOD4 @ 03:30:46`): *"If we only have two wicks right next to each other,
it's like 50% probability being hit. Two wicks several candles apart, 70–80%. Three plus
wicks stacked…"* — 89%, and 4+ far apart to the tick, 90–95%.

Measured as a pure base rate, no entry model. The **control is the single unclustered
pivot**, because his claim is comparative in wick count. Tested at three pivot scales,
because scale *is* the claim — he draws equal highs on swings visible from ten feet away,
and a 3-bar fractal on 1-minute data is a 4-point wiggle.

**Hit rate within one session-day (1,380 bars), highs:**

| pivot scale | 1 wick *(control)* | 2 | 3 | 4+ | his claim |
|---|---|---|---|---|---|
| k=3 (≈1m noise) | 96.5% | 97.5% | 97.8% | 97.8% | 50 → 89 → 90-95 |
| k=15 (≈5m swings) | 92.8% | 94.7% | 96.2% | 97.5% | ” |
| k=30 (≈15m swings, "obvious") | 89.5% | 91.9% | 94.4% | 95.1% | ” |

*(tol = 0.25 pt, "to the tick". The tol=2 and tol=5 sweeps are in
`output/dodgy_l1_ladder.csv` and flatten the ladder further.)*

**His floor is far too low and his ceiling is about right.** Two adjacent wicks are not a
coin flip — they are taken 92–98% of the time within a day depending on scale. A **single**
wick, which he does not treat as a level at all, is taken 89–97%.

**And the ladder's shape does not survive the distance control.** More wicks means a
*nearer* level — median distance falls 18.0 → 11.8 → 8.5 → 5.8 points from 1 to 4+ wicks at
k=30 — and nearer levels are hit more for reasons that have nothing to do with liquidity.
Stratifying on distance (highs, k=30, tol=0.25, one-day horizon):

| distance tertile | 1 wick | 2 | 3 | 4+ |
|---|---|---|---|---|
| near | 96.2% | 97.1% | 96.4% | 96.4% |
| mid | 91.8% | 90.5% | 91.1% | 88.2% |
| far | 81.2% | 80.7% | 91.3% | 100.0% *(n=81)* |

**Within a distance band the ladder is flat.** Near: 96.2 → 96.4 across four buckets. Mid:
91.8 → 88.2, if anything declining. The far tertile rises but carries 81 observations in
the top bucket and is the only cell in the study that supports him.

**The raw ladder's apparent rise is the distance confound, not the wick count.** Same
structure as the Law 2 problem that governs the session split — a variable that looks like
a quality signal is a proxy for a geometric one.

**Two honest qualifications.** (a) *Hit* here means price trades through the level within
the horizon, measured from the moment the cluster completes; he never states a horizon, so
three are reported and all three tell the same story. (b) He may intend the ladder as a
draw-side probability on a higher timeframe chart with an opposite-side race — a stricter
target-before-stop reading would lower every number in the table, but it lowers the control
by the same mechanism, and it is the *comparison across wick counts* that fails here.

---

## What this leaves

**The near draw set is built and it does not rescue the structural target.** Additively it
provably cannot; exclusively it moves EV by at most +0.020R against the incumbent and
leaves every arm loss-making. The bound named in `FINDINGS-dodgy-structural-target.md` is
now closed rather than outstanding.

Two of the lecture's three highest-ranked untested items are now refuted on the population
he actually trades: **E5 rule 4 (inert, 2% of the book, wrong-signed)** and **the L1
probability ladder (floor far too low, shape gone under a distance control)**. The third,
F1 — big overnight move ⇒ choppy NY AM — is untouched and needs no entry model.

The single most useful thing in this run is not about him. It is the **monotone
distance/EV curve in §2**: across seven independent target specifications spanning 1.08R to
6.95R, expectancy improves with distance and win rate deteriorates with it, and the curve
never crosses zero. That is a property of the *trigger*, and it says no exit rule reachable
from this signal set will produce a positive book.
