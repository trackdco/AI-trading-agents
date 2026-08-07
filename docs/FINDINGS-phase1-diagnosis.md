# FINDINGS — PHASE 1 (the diagnosis) and PHASE 2 (precondition)

Overnight run, 2026-08-07. **Report-only.** Nothing armed, nothing adopted,
no holdout contact.

## PHASE 2 IN ONE LINE, because it gates everything

**The precondition FAILS.** Of 17 entry-usable candidates, exactly one
passes all four ladder tests — `closeloc` — and it is **Law-2 mechanical**
(`risk ≈ closeloc × range`). **Zero non-mechanical variables** show real
tier-to-tier differentiation across 3+ tiers. **Phase 2 stops there.** No
sizing ladder is forced onto binary or mechanically-coupled signal.

---

## PHASE 1 — SCHEMA, stated before anything ran

Five mismatches were reported in Phase 0. Two bind here:

- **The depth six exist only on the incumbent.** The LTF population has no
  depth columns at all, so `dep_*` is diagnosed on the incumbent only. Not
  papered over; the LTF depth build was not done.
- **`next_lvl_R` and the ceilings existed only on the LTF frame.** Built
  for the incumbent using the *same* code path so the column means the same
  thing in both books (84.6% coverage — the remainder is "no level ahead",
  a category, not missing data).

**Coverage flagging.** Any column present on <90% of a book's rows is
flagged `PARTIAL-COVERAGE` and is treated as a *sub-population* finding,
never a book-level one. This caught a real defect: on the combined books
the in-trade and depth columns exist only on the incumbent rows (67–68%
coverage), so an unflagged run would have reported the incumbent's numbers
as if they were the combined book's.

## THE LAW-2 SCREEN, widened mid-run

The declared screen was for mechanical coupling to stop width or the R
denominator. Running it exposed a **second** category the screen did not
cover, and it dominated the raw ranking:

> **POST-ENTRY variables are not knowable at the decision bar.** The
> in-trade family (`it1_*` … `it10_*`) is measured 1–10 minutes *into* the
> trade, so it is partly the outcome itself. `it10_cum` split the incumbent
> book by **+1.125R** — the largest separation in the entire table — and it
> is worth nothing for entry selection or conviction sizing at entry.
> Usable for exit/management rules only (BR-22).

**24 of 124 rows** were flagged post-entry. Without that flag the top of
the ranking would have been eight in-trade variables, and the whole
diagnosis would have read as a discovery.

## THE ENTRY-USABLE SURVIVORS

Day-clustered significant, knowable at the decision bar, full coverage:
**17 rows.** Ranked by |ΔEV|, with the Law-2 verdict:

| book | column | ΔEV | clustered 95% | Δwin | w/o worst-5 | Law 2 |
|---|---|---|---|---|---|---|
| ROOM 3m | risk_w | +0.936 | [+0.406,+1.473] | +21.0 | +0.883 | **mechanical** |
| ROOM 5m | closeloc | +0.911 | [+0.365,+1.463] | +25.3 | +1.030 | **mechanical** |
| ROOM 5m | risk_w | +0.847 | [+0.321,+1.382] | +22.7 | +1.055 | **mechanical** |
| ROOM 5m | rangex | +0.770 | [+0.302,+1.234] | +13.6 | +0.809 | **mechanical** |
| ROOM 5m | **ceil5_between** | **−0.764** | [−1.385,−0.124] | −24.7 | −0.767 | clean |
| ROOM 3m | **volx** | **+0.627** | [+0.109,+1.121] | +16.6 | +0.649 | clean |
| ROOM 5m | w15 | −0.607 | [−1.162,−0.045] | −18.8 | −0.745 | mechanical |
| ROOM 5m | risk | +0.583 | [+0.063,+1.102] | +14.9 | +0.535 | mechanical |
| ROOM 5m | **volx** | **+0.536** | [+0.037,+1.045] | +12.3 | +0.649 | clean |
| COMBINED 5m | risk / closeloc / risk_w | +0.42/+0.40/+0.40 | all clear | +14..16 | stable | mechanical |
| COMBINED 3m | **d15_conf** | **+0.341** | [+0.070,+0.614] | +7.5 | +0.323 | clean |
| INCUMBENT | risk_w | +0.353 | [+0.072,+0.624] | +15.1 | +0.341 | mechanical |
| COMBINED 3m | risk / risk_w | +0.30/+0.30 | clear | +12.8/+13.4 | stable | mechanical |
| INCUMBENT | **d15_conf** | **+0.296** | [+0.008,+0.547] | +8.0 | +0.297 | clean |

**Only three distinct non-mechanical variables survive:** `volx`,
`ceil5_between`, `d15_conf`.

- **`volx`** is the strongest and it **replicates across both trigger
  timeframes** (3m +0.627, 5m +0.536) — the only variable in the run that
  does. Its mechanical coupling, if any, runs *against* it: a
  high-volume bar tends to be a wide-range bar, which means a bigger stop
  and therefore a *smaller* R multiple for the same move.
- **`ceil5_between`** is negative and coherent with the room thesis: a 5m
  BB MA ceiling sitting between entry and the next level costs −0.764R.
- **`d15_conf`** is small but present in two books.

## THE CHECKS THAT DID THEIR JOB

**Day-clustering.** **9 of 124** rows were significant naively and dead
once session-days were resampled instead of trades — day properties wearing
a trade's clothes. Between-day variance shares run 24–56%, so pseudo-
replication was a live risk throughout, not a formality.

**Dual currency.** **Zero** clustered-significant rows show a
hit-rate/expectancy inversion. The BR-20 failure mode does not appear
anywhere in this family — every survivor wins more often *and* pays more.

**Own-worst-days.** Each book's worst 5 days were found fresh rather than
inherited. The incumbent's are 2026-01-08, 2025-10-27, 2025-12-03,
2026-05-03, 2025-10-30 — **only one of which (2025-10-30) is on the
previously identified sequential-grind list**, so inheriting that list
would have been the wrong control. Those 5 days are −22.7R of a +237.3R
book over 233 days. **No survivor's signal is carried by them**: every
non-mechanical survivor's ΔEV is unchanged or larger with the worst days
removed (`volx` +0.627 → +0.649).

## A FINDING THAT WAS NOT ASKED FOR: the 2pt risk floor is too low

`risk_w` separates strongly in every book **even though the room-gated
books already have the 2pt floor applied**. Its bottom quintile still
underperforms badly (ROOM 5m: Q1 +0.069 vs Q5 +1.438, monotone).

That is BR-29 restating itself past the fix. The floor removed the worst of
the degenerate-stop population but not enough of it. **The floor level
itself deserves a declared sweep** — it was fixed at 2.0pt by argument, not
by measurement.

---

## PHASE 2 — THE PRECONDITION, with the numbers

Declared before reading: **T1** arity ≥3 tiers · **T2** top−bottom spread,
day-clustered CI clear · **T3** ≥2 positive adjacent steps **and** the
middle tiers separate (Q4−Q2 CI clear) · **T4** non-top spread ≥30% of
total. T3 is what distinguishes a ladder from a top-vs-rest step.

**17 candidates tested. 1 passes. It is mechanical. 0 non-mechanical pass.**

The two closest calls, both `volx`:

| | Q1 | Q2 | Q3 | Q4 | Q5 | verdict |
|---|---|---|---|---|---|---|
| **ROOM 3m** EV | +0.018 | +0.508 | +0.603 | +0.849 | +0.752 | T2 **FAIL** [−0.022,+1.487] |
| win | 26.9% | 34.3% | 40.9% | 50.7% | 46.3% | |
| **ROOM 5m** EV | −0.069 | +0.091 | +0.702 | +0.623 | +0.718 | T2 pass, T3 **FAIL** |
| win | 25.8% | 30.6% | 47.5% | 37.7% | 48.4% | |

`volx` looks like a ladder and is not one. At 3m the top-to-bottom spread
is +0.734R but its day-clustered interval includes zero by 0.022. At 5m the
spread clears, but the **middle tiers do not separate** — Q4−Q2 is
[−0.274,+1.387] — and 3 of 4 steps positive with one large negative is not
tier-to-tier differentiation. Both books have ~61–66 rows per tier, which
is the real constraint.

`ceil5_between` and `d15_conf` fail T1 outright: **binary, so a ladder is
impossible by construction**. That is the "don't force a sizing test onto
binary signal" case, arriving exactly as anticipated.

**PHASE 2 STOPS.** No Law 7 arithmetic, no ladder, no split-half, no
account scoring. Forcing a three-tier ladder onto a variable whose middle
tiers do not separate would be building on noise.

## WHAT WOULD CHANGE THE ANSWER

Stated so the morning has a decision rather than a dead end:

1. **More rows.** `volx` fails on interval width at ~65 rows/tier. The
   London room-gated books are 1.1–1.4 trades/day. Three tiers instead of
   five would roughly double the rows per tier — but tier count is exactly
   what the precondition is testing, so that is a *different* declared
   test, not a rescue of this one.
2. **A risk-floor sweep first.** If a higher floor removes the degenerate
   population that `risk_w` keeps flagging, the remaining variables get a
   cleaner substrate to be measured on.
3. **`volx` as a binary gate, not a ladder.** It survives day-clustering in
   both timeframes with dual currency agreeing. That is a *gate* question
   under Law 7, and it needs its own declaration — it is not this pass.

None of these are done. None are recommended without a declaration first.
