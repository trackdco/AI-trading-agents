# DECLARATION — THE AGENT SWEEP (winner/loser separation, all variables)

2026-08-08, written and committed BEFORE any agent reads an outcome.
Fit-only, no holdout, report-only, nothing adopted.

## WHY A DECLARED FILTER IS NON-OPTIONAL HERE

The sweep is deliberately broad: **111 numeric columns × 9 (session ×
mechanism) cells × 2 directions ≈ 2,000 candidate splits**, plus
interactions. At a 95% interval that manufactures **~100 spurious
"clears" by construction**. Every previous pass on this family cleared
at or near its false-positive budget (BR-91: 9/110; BR-94: 9/160). A
broad sweep without a pre-committed survival rule would produce a long
list of nothing. The rule below is the deliverable's spine.

## THE SURVIVAL RULE (all five, no exceptions, declared now)

A finding is reported as SURVIVING only if:

1. **Full-cell day-clustered CI clears zero.** Mean-difference between
   the two arms of the split, day-clustered bootstrap on the
   DIFFERENCE, seed 20260807, 2000 draws, 95%.
2. **Both halves agree.** The frozen day-level split-half (seed
   20260807, written into `race_wide.parquet` as `half`) must show the
   SAME SIGN in both halves, each at least **one third** the magnitude
   of the full-cell effect. This is the anti-noise filter: a real
   separator survives a coin-flip partition of the days; a lucky one
   does not.
3. **The points-based control agrees in sign.** Every R-denominated
   effect must reproduce in `out × risk` (points). An effect that dies
   in points is the R denominator, not the market (Law 2, BR-43).
4. **Not mechanically coupled**: |ρ(variable, risk)| < 0.4, else the
   finding is reported under a LAW-2 flag and is not a survivor.
   `risk`, `w15`, `w15_pts`, `risk_over_w`, `tf_won`, `closeloc`,
   `rangex` are mechanical BY DECLARATION.
5. **Minimum power**: ≥40 fights in the cell, ≥10 per arm, ≥3 days per
   arm.

Anything clearing (1) but failing (2)–(5) is reported as **"clears but
does not survive"**, with the failing test named. Nulls are published.

## SESSION DISCIPLINE

**Sessions are NEVER pooled** — LONDON, NY_PRE, NY_AM are reported
separately at every level, per the trader's standing instruction.
Mechanisms (M1/M2/M3) are never pooled with each other. Directions may
be pooled WITHIN a cell for power, and that pooling is stated wherever
used.

## OUTCOME DEFINITION

`out` = the declared outcome of the corrected census: M1 → first-passage
to the 15m MA; M2/M3 → first-passage to the nearest menu structure
beyond entry. `hit`, `mfe_r` available. Realized-R quintiles as well as
winner/loser means, per the trader's instruction that scoring not
collapse to win/lose.

## WHAT THE AGENTS MAY AND MAY NOT DO

MAY: any split, any threshold, any interaction, any subgroup, on the
111 columns; derive further columns from those present; report
quintile structure and monotonicity as supporting evidence.

MAY NOT: touch holdout data (none exists for this family); change the
census; re-score outcomes; or report a survivor without all five tests.
Thresholds found by search are declared as SEARCHED (a threshold picked
on the same data it is tested on is a fit artifact even when it
survives split-half; it is reported with that label).

## THE PRIOR

Every selection layer tested on this family so far has failed
(BR-91 price-state: nothing positive-clears; BR-94 flow/depth: at the
false-positive budget, at both evaluation timestamps). The population
nets zero (BR-86/90) and the timing lever was accounting (BR-96). The
honest expectation is that **most or all of this sweep returns
nothing**, and that outcome is a result, not a failed run. If something
does survive all five tests in a session, it is the first thing on this
family that has.

Standing: fit-only, no holdout, report-only, nothing adopted.
