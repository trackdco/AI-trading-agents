# PRE-REGISTRATION — NYA-LVL-01 stage 3 — the discriminant: 16.6/day down to 1–3

**Committed BEFORE any of it runs.** Authorised by Angus 2026-08-05 off the stage-2
result. Fit span only. **Sealed 2023/24 not touched, holdout look: NO.**

---

## PLAIN LANGUAGE — the job

Stage 2 established two things.

**Good news:** fixing the exit arithmetic turns a losing raw set into a profitable one.
The declared default (20-point stop, 30-point target) alone took PF 0.43 → 1.07, and
tighter stops with a trail did far better.

**Sobering news:** the placebo null came back **p = 0.24**. Six random lines drawn from
the same day's price range produce the same best result as the six real ones. **The six
levels are not the edge — the exit geometry is.** They are a fine way to pick entry
times, and that is all they are on the evidence so far.

**So stage 3 is the bridge Angus asked for:** what separates the winning pool from the
losing pool, so 16.6 tags a day becomes **1–3 of the best ones**. That is roughly an
85–90% cut, and this family is the only one in the programme with enough raw events to
afford it — 1–3/day still leaves ~290–860 trades.

---

## Standing constraints recorded

- **ANGUS RULE: anything trading before the official NY open must be flat by 09:30.**
  Verified against the current build: **zero entries before 09:30** (earliest 09:45,
  latest 15:45), so the rule does not bind on this family as constructed. It **does**
  constrain the declared substrate extension — any pre-market level touches added later
  must flatten by 09:30, and that is now on the record before those are built.
- **We already skip the opening 15-minute candle** as a side effect of a 15m bar being
  unable to close before 09:45. That is MrZincx's most emphatic filter and his
  "45% of losses" claim cannot be tested on this build without deliberately adding that
  bar back. Not doing so; recorded so nobody later mistakes compliance for a result.
- **The entry is a guideline, not a target** (Angus): his six levels source the events.
  Trade management and selection are ours to find.

---

## Stage 3a — the regime diagnostic (runs FIRST, and it is decisive)

"Cut at 10, trail, hold" is the classic trend-capture profile — 43% win rate, ~4:1
payoff. It prints when the instrument trends and bleeds when it chops. Our whole fit span
is one 13-month stretch.

**The question: is stage 2's result an edge, or a bet that NQ trended?**

Measured, all declared now:

1. Correlation of **daily strategy P&L** with the day's **absolute RTH move** (|close −
   open|) and with the day's **range**.
2. Daily P&L split by **directional-efficiency terciles** (|net move| ÷ total path).
   A trend-capture model should earn almost everything in the top tercile.
3. **Long-side vs short-side P&L split.** A model that only earns on one side over a
   directional 13 months is a beta bet wearing a strategy label.
4. Monthly P&L vs NQ's own monthly return.

**No pass/fail bar** — this is a diagnosis, not a gate. But its answer determines how the
rest of stage 3 is read, and it goes on the card in plain language either way.

## Stage 3b — the winner/loser discriminant

**Declared variable list, frozen here — it may not grow:**

| variable | recorded at | frozen split |
|---|---|---|
| `level_type` | birth | the 6 categories |
| `tap_15m` | birth | 1st tap / 2nd / 3rd+ (his three-tap rule) |
| `minute_of_rth` | birth | hourly buckets |
| `dist_from_open` ÷ `atr15` | birth | terciles |
| `level_age_min` | birth | terciles (PM levels only) |
| `gap_context` ÷ `atr15` | birth | terciles |
| `atr15` | birth | terciles (the volatility regime) |
| `side` | birth | long / short |
| `t+5` sign | birth | green / not green at 5 minutes |
| `t+15` sign | birth | green / not green at 15 minutes |

**Protocol — §5.12.2, literally:**
- Every variable evaluated **ALONE** at its frozen split. No combinations in this pass.
- **NaN stands down** — excluded from both arms, never counted as a fail.
- **Fewer than 30 events a side in an era = `thin`, no verdict** (§2.2).
- **Survival requires the same direction in BOTH eras**, and the **inverse era pass**
  (discover-2026/validate-2025) must agree (§2.1).
- Reported at **both cost levels**; base-only is not a pass.

## Stage 3b-control — the placebo classification, and this is the point

The stage-2 null already told us the levels are not special in aggregate. So for every
discriminant that survives, we run **the identical split on placebo levels** and classify
it:

- **LEVEL-BORNE** — works on the real six, not on random lines. This is a genuine
  level-interaction edge.
- **CONTEXT-BORNE** — works equally on random lines. Still a real edge (time of day and
  volatility regime do not care where the line is), but it belongs to a *price-context*
  strategy, not a level one.

**Neither is a failure.** The point is to know which we own, because a context-borne edge
generalises differently, needs different holdout conditions, and overlaps different
cousins in the book. Conflating them is how a strategy dies at the holdout for reasons
nobody understood in advance.

## Stage 3c — the selective rule, targeting 1–3/day

Only survivors from 3b are eligible. Combined with an **explicitly declared** rule:
stack surviving gates in descending order of their single-variable lift until the event
rate falls into **1–3 filled trades per session**, then stop.

- The stack order is fixed by 3b's measured lift, not chosen by trying combinations.
- **Stop size is re-fitted per surviving cohort**, since stage 2 showed geometry is where
  the money is — the stop grid (10/15/20/25/30/40) is re-run *inside* the selected pool.
- **Permutation null on the final stack, family-wise across everything stage 3 tested**,
  200 permutations, placebo levels, bar **p ≤ 0.01**. Budgeted from the start, not bolted
  on.

## What stage 3 may not do

- **May not promote.** §6.0.1 stands; anything found here is a candidate spec requiring
  PBO and a holdout look it has not earned.
- **May not touch 2023/24.** Every gate here is fitted on the fit span by definition,
  which is exactly why the holdout must stay sealed.
- **May not add variables.** The list above is closed. Anything new needs a new prereg.

## Artifacts

`scripts/nya_lvl_regime.py` · `scripts/nya_lvl_discriminant.py` ·
`output/nya_lvl_regime.md` · `output/nya_lvl_discriminant.md` · trials to
`output/trial_ledger.parquet` · card refreshed in `research/FUNNEL.md`.
