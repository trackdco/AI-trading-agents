# PRE-REGISTRATION — CHOP AS A REGIME GATE

**Declared by him, 2026-08-16, BEFORE any measurement.** Registered here
before a single number is computed, per the repo's standing discipline
(`docs/PREREG-displacement-canon.md`, `docs/HOLDOUT-2023-24-PREREGISTRATION.md`).

**Standing conditions, his words:** *"Counts and base rates only in stages
1–3; report-only throughout; fit-only."* and *"Nothing adopted from this
pass."* No threshold is selected, no gate is shipped, no contract changes,
regardless of what any stage shows. FIT SPAN ONLY — the holdout partition
(`docs/DECLARATIONS-holdout-partition.md`) is not touched.

---

## §0 — The hypothesis, stated before anything is measured

His words, verbatim:

> My trigger is one candle closing through two levels, one being its own BB
> MA. In a trending market the levels are dispersed, so crossing two in one
> candle requires real displacement. In chop, VWAP, POC, the MA and the bands
> compress into the same few points — so a nothing candle crosses two of them
> trivially. **The trigger's difficulty is not constant; it is inversely
> proportional to the separation between the two levels crossed.** Chop does
> not generate false triggers because it is choppy. It generates them because
> my trigger becomes structurally easier exactly when it should be getting
> harder.
>
> If that is right, the primary fix is a separation requirement, not a regime
> detector — and the detectors below are secondary.

**Why this is a strong hypothesis and not a hunch:** it is mechanistic, it
names the direction of the effect in advance, it makes a falsifiable
quantitative prediction (§2), and it predicts that the cheap fix
(separation) dominates the expensive one (regime detection). It can fail
cleanly — if separation shows no monotone relationship with outcome, §0 is
dead regardless of what the detectors do.

## §1 — Day-clustering diagnosis. RUN FIRST.

Per window (**LONDON 03:00–04:59 / NY_PRE 08:00–09:29 / NY_AM 09:35–11:00,
never pooled**), decompose the loss distribution into within-day and
between-day variance.

**Decision this stage settles, in advance:** if chop damage concentrates in a
small number of sessions, this is not a per-trade leak — it is a handful of
days that should have been no-trade days, and a **session-level** gate is far
cheaper than a trigger-level one. Report which it is before building anything
further.

## §2 — The mechanism test

For every trigger, record the distance between the two levels crossed, **in
points AND in W15**. Score outcome against that separation, **in both R and
points** — stop width varies with structure, so anything correlated with it
will look correlated with performance in R alone. Report deciles.

**Prediction, registered in advance:** separation below roughly **0.10·W15**
is one level being crossed twice, not two levels, and should underperform
badly.

## §3 — Detectors, all reported as base rates, nothing selected on

**Denominate everything in W15, not points** — a fixed point threshold
silently changes meaning as band width moves across the fit span.

| detector | definition | his note |
|---|---|---|
| **MA closure count** | closes through the trigger's own BB MA in the last N bars; sweep N | *"measured in the exact object that generates my signal, so I expect it to beat the general-purpose measures"* |
| **15m BB MA slope** | in W15 per bar | a flat 15m MA kills both mechanisms at once — rebalance is meaningless when price already oscillates across it, continuation meaningless with no direction to continue into |
| **Efficiency ratio** | net displacement ÷ sum of absolute bar-to-bar moves over N | |
| **Inside developing VA** | price within the developing value area | trading inside the VA is trading in balance by definition |
| **Variance ratio** | validation reference ONLY, never a gate | rigorous but noisy at intraday samples |

**Explicitly excluded: band width alone.** *"Wide chop is the dangerous kind
for me — it prints big convincing displacement candles. Narrow chop I already
skip by eye."*

## §4 — The state machine, in his language

**Do not build a continuous chop score.** *"I already have a graded conviction
ladder and a second score will fight it."* Build a STATE:

> Range detected → mark the range edges → the only permitted trades are from
> an edge, targeting the opposite side. **The middle is dead.** No rebalance
> trades, no continuation trades, nothing from the middle toward the far side.

*"This is my existing range doctrine — I am not adding a rule, I am
instrumenting one I already trade by."* (Consistent with T64, already in
`tv-trigger` 0.4.7 as a thesis-layer location doctrine.)

## §5 — Scoring

**Net of frequency.** The question is whether the book improves after those
trades are removed, not whether chop correlates with losses. Report per
window, **both R and points**, **day-clustered CIs**, and report the
**frequency cost explicitly alongside any EV gain**. Nothing adopted from
this pass.

---

## SUBSTRATE — decided before measuring, recorded here

**His trigger census, not the canon's.** `output/l0_triggers_*.parquet` and
`l2_outcomes_*.parquet` (19,137 rows, 270 days) are the MECHANICAL CANON's
substrate — `rejection_block` / `displacement` patterns over order blocks and
confluence clusters. They do **not** encode his trigger and must not be used
to test §0.

The correct substrate is `scripts/raw_trigger_census.py` — his own 2026-08-08
reset: *"every single time a 3-minute candle closes through a VWAP band and
through its Bollinger Band moving average... what is the raw amount of
triggers we have there?"* — 2m and 3m, open on one side of both its own
BB(20) MA and a VWAP band, close through both, same direction. It already
computes `run_mfe_r` and carries W15, and it is the substrate the
selection-effect result rests on, so §1–§3 inherit a measurement lineage he
has already reviewed.

**Two substrate limits, stated now rather than discovered later:**

1. **The census's second leg is a VWAP band only.** Current doctrine also
   licenses POC/VAH/VAL and weekly-profile edges as the second level. So the
   census is a SUBSET of his trigger. This is acceptable for §0 — the
   compression hypothesis is *about* the VWAP/MA cluster, which is the census's
   exact population — but any separation threshold derived here would not
   generalise to profile-leg triggers without re-measurement. Recorded as a
   scope limit on the finding, not a defect.
2. **Outcome is `run_mfe_r`,** a no-target walk to the stop or session end.
   That is the right outcome for a diagnostic (it prices any R multiple later
   and does not bake in a target rule), and it is NOT a backtest of his book.
   §5's "does the book improve" question therefore needs the agent run logs,
   which at the time of registration hold ~6 days — insufficient. **§5 is
   deferred until the June walk-forward completes**, and that is declared here
   rather than fudged with a small sample.

## POWER, declared in advance

The fit span carries ~270 session-days. §1 and §2 have adequate n at the
trigger level. §3's detector sweeps multiply comparisons, which is exactly
why he restricted them to **base rates with nothing selected on** — the
multiplicity is uncontrolled by design, and any detector that looks good here
must survive pre-registered re-measurement on the holdout before it can ever
gate anything.

## STAGE STATUS

| stage | status |
|---|---|
| §0 hypothesis | registered 2026-08-16, unmeasured |
| §1 day-clustering | not yet run |
| §2 mechanism test | not yet run |
| §3 detector base rates | not yet run |
| §4 state machine | design only, not built |
| §5 net-of-frequency scoring | **DEFERRED** — needs the June walk-forward book |
