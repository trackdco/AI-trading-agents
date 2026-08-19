# FINDINGS — his exit is the wrong one: the structural target buys win rate and sells expectancy

NQ, 1,251,240 one-minute bars, 2023-01 → 2026-07. **85,277 inversion signals**, 88/day.
2-point risk floor, 240-bar max hold, 0.5-point round turn, day-clustered intervals, both
era halves, win% and EV on every row.

He does not target a fixed multiple. *"95% of my targets are always highs and lows"*
(`r43i9rRIjoQ @ 08:25:54`) and *"do you think the market sees your little riskreward
position tool on the screen? No"* (`@ 08:27:20`). The incumbent test
(`docs/FINDINGS-dodgy-ifvg.md`) targets a flat 2R, so the exit was a **specification
mismatch**, not a filter — which is why it was ranked the highest-information item in the
lecture catalogue.

**Correcting the mismatch makes the book worse.** The fixed-2R "error" was flattering him.

## The harness reproduces the published book first

| | published | here |
|---|---|---|
| trigger only, fixed 2R, after cost | **−0.135** [−0.145, −0.125] | **−0.135** [−0.146, −0.125] |

Same number to three decimals on 80,603 trades. Everything below is measured against a
baseline that reproduces.

## The result

| arm | n | /day | win % | EV | 95% CI | H1 | H2 | eras |
|---|---|---|---|---|---|---|---|---|
| fixed 2R *(incumbent)* | 81,038 | 88.2 | 32.80 | **−0.128** | [−0.138, −0.117] | −0.148 | −0.110 | — |
| **structural** | 79,971 | 87.0 | **43.06** | **−0.143** | [−0.153, −0.133] | −0.153 | −0.134 | — |
| **structural, rr ≥ 1** | 48,913 | 53.2 | 34.18 | **−0.142** | [−0.157, −0.127] | −0.149 | −0.135 | — |

**Win rate +10.3pp, expectancy −0.015R.** That is the dual-currency inversion Law 3 exists
to catch, and it is now the fourth instance on the record here after BR-20/46/48 and the
tomtrades 89.86%-win-rate cell. Every interval clears zero on the negative side; no arm
clears either era, let alone both.

**His own risk-reward floor does not rescue it.** *"Never take a trade below one R"* cuts
the book by 40% — 88 to 53 trades a day — and moves EV by +0.001R. It buys back the win
rate it lost (43.1% → 34.2%) and none of the expectancy.

## Why: the pool is nearer than two units of risk

| arm | median stop | cost in R | **median reward:risk** | $/trade | $/day |
|---|---|---|---|---|---|
| fixed 2R | 5.00 pt | 0.100 | **2.00** | −$11.31 | −$997 |
| structural | 5.00 pt | 0.100 | **1.07** | −$13.50 | −$1,175 |
| structural, rr ≥ 1 | 4.50 pt | 0.111 | 1.63 | −$12.49 | −$665 |

The nearest unswept liquidity sits at **1.07R**, not 2R. Targeting it pays you more often
and less, and the arithmetic does not close: 43.1% at ~1.07R loses to 32.8% at 2R.

**Law 2 discharged.** A structural target sets reward from the same geometry as risk, so R
is a moving denominator between arms and an EV-in-R comparison alone would be
untrustworthy. It is not the explanation here: **the ordering is identical in dollars**
(−$11.31 / −$13.50 / −$12.49) and median stop is unchanged at 5.00 points between the two
main arms. The structural exit is worse in R, worse per trade in dollars, and worse per day.

## Incidental — CORRECTION 2's blast radius is small

`require_revisit` was inert (`docs/FINDINGS-dodgy-ifvg.md` CORRECTION 2). Enforcing it
removes **70 of 85,347 signals (0.08%)** and moves EV **−0.135 → −0.128, about +0.007R**.

The bug was real and the fix is right, but it does not rescue anything and it does not
change a published verdict. Worth recording precisely because the natural assumption — that
a broken gate on the defining condition of the pattern must matter — is wrong here.

## The draw set, and what it is missing

Targets are the nearest unswept level ahead of entry from: the last confirmed swing high or
low, prior-day H/L, prior-week H/L, and completed same-day Asia and London H/L. All carry
no-lookahead semantics; the session boxes are invalid until their window closes.

**Not included, and this bounds the result:** L1 equal highs/lows and L9 intermediate-term
levels, both of which need swing clustering that does not exist in the repo, and L2 trend
lines, dropped as unfalsifiable (`RESEARCH-dodgysdd-lecture.md` C-5). He weights equal
highs heavily and gives them an explicit probability ladder, so **this is not the full draw
set he trades** — it is the subset with as-of implementations.

That said, the missing levels are *near* levels. Adding them moves the median reward:risk
further below 2R, which is the direction that made this book worse. **The gap is unlikely
to be hiding a rescue.**

## Two bugs of mine, both caught by an absurd number rather than by reading

Recorded because the detection route generalises:

1. **Asia levels were available on 0% of bars.** The window test used clock hour, and the
   session spans midnight, so "before Asia" (`hour < 20`) also matched the entire 00:00–18:00
   stretch *after* Asia and voided the level exactly where it is tradeable. Fixed with
   session-relative elapsed time.
2. **Median reward:risk came out at 16.7** on the first pass, because the draw set held only
   coarse levels and omitted the near pool. `signals()` already computes the last confirmed
   swing high and low.

Neither was visible on inspection. Both were obvious the moment a summary statistic was
printed, which is an argument for printing them before the EV.

## Standing conclusion

The iFVG model is negative on NQ under his own stated exit, on a detector whose known bug
is now fixed, with the population reproducing the published baseline. Correcting the exit
mismatch — the highest-information item in the lecture catalogue — moved the book **the
wrong way**, and his own reward-reward floor recovered none of it.

Next, in order:

1. **Build the near draw set** (L1 equal highs, L9 intermediate-term). It bounds this result
   and is the only route by which a structural target could be argued to have been tested
   unfairly.
2. **E5 rule 4, target-must-be-unswept, as a rejecting filter.** One line
   (`dodgy_ifvg_test.py:122-125` already computes the predicate and currently uses it
   backwards, keeping the trade with a synthetic target).
3. **F1, big overnight move ⇒ choppy NY AM.** No entry model needed, and untouched by any
   of this.
