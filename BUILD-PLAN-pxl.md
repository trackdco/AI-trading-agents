# PXL/PXH → armed bot: the complete build plan

Your five stages, with the two missing ones inserted and each stage given an exit condition. Nothing here needs new data.

Your pipeline as stated was: upload the channel → confirm the strategy → raw triggers → order flow → loser autopsy. The two gaps: **no fill-model stage** (PXL is a limit entry, so setups only become trades if price retraces — recording only filled ones is the row-existence defect you fixed on the break arm, and it can manufacture a phantom edge on its own), and **no holdout stage** (what killed the canon). Both are now stages 3 and 9.

Sessions in scope: NY AM first, London second. Asia is out — you ruled NQ out there on activity, and the spread arithmetic in stage 5 will confirm it independently.

---

## Stage 0 — Specification lock (your stage 2, promoted to first)

Your stage 1 was "upload the YT channel." It goes second, because the annotated chart you drew is worth more than the transcripts: it shows what you do rather than what someone says. The scrape is now a *supplement* to a spec you already own, not the source of it. And we established the PXL lecture may not even be on the public channel.

**Two ambiguities still open from your chart, and they gate everything downstream:**

1. **Which prior low becomes the PXL?** Most recent swing low on the timeframe? Nearest untested? A swing defined by how many bars either side? This is where the discretion hides, and without it the model isn't mechanical.
2. **Does the body close through the 0 (wick bottom, the prior low) or merely into the wick zone?** I read it as the 0. The two produce materially different populations and very different trigger counts.

Answer those two and the spec is executable. Everything else on the chart is already mechanical.

**Also lock, because they're unstated:** the swing-structure definition that establishes "lower high lower low" (how many pivots, what lookback); how long a PXL stays valid before it goes stale; and whether a PXL that's already been traded once can re-arm.

**Exit:** a spec document with no rule requiring a human to look at a chart. Then run the scrape as a supplement and grep the triage list — if the PXL lecture isn't there, you've lost nothing because the spec is already locked.

## Stage 1 — Build the P-TABLE

A new table, not an extension of the M-TABLE. PXL levels are swing wicks; M-TABLE levels are 15m BB MA fights. Different level family, different population. Reuse the M-TABLE's *infrastructure* — the schema conventions, the sealing mechanics, the gate scripts — but build a separate table.

One row per qualified PXL/PXH trigger, existing unconditionally. Columns:

- Keys: timestamp, direction, trigger timeframe, session, cluster id
- PXL geometry: wick top, wick bottom, **wick width in points**, the 50% level, the prior low being broken
- Trigger: displacement bar OHLC, body/range ratio, range ÷ ATR(14), whether the break was single-bar or accumulated (record the count)
- Context: swing structure state, HTF alignment, distance to VWAP and prior-day levels, the level-set snapshot
- **Fill: `filled` flag, fill bar, bars-to-fill, and — critically — the forward travel of UNFILLED setups**
- Outcomes: the full battery plus **MFE and MAE in R and in points**
- Flow features as-of the decision bar, on the covered months only

Run all three gates before merge: row existence under perturbation, entry-price perturbation, and a convention check against an overlap period. `scripts/htf_ma_entry_gate.py` already exists — point it at this table.

Seal the holdout span now, written unread, and commit the partition to the declarations file before anything is looked at.

**Exit:** three gates pass, exclusion criterion in writing and shown outcome-independent, holdout sealed and partition committed.

## Stage 2 — Base rates, zero conditioning

- Trigger frequency per session per day
- Raw win rate at the nearest-draw target
- **Stop-width distribution in points** — this is (half wick + 2pts) and you've never measured it for this setup
- **MFE/MAE in R: median, p75, p90, p95**, per arm and per session

The MFE table decides the exit design and it's the number most often skipped. Also compute the **wick-width distribution in points** — you need it for stage 4.

**Exit:** base rates and both distributions exist, whole population and per session.

## Stage 3 — Raw trigger book AND the fill model (your stage 3, doubled)

Run the spec exactly as written, costed. Then the part that decides whether PXL is validatable at all:

- Log every qualified setup at the **trigger**, tag filled vs unfilled
- **Report the fill rate** as a headline number
- **Measure the no-fill opportunity cost** — how far did unfilled setups travel? If the ones that never retrace are the bigger winners, your filled sample is adversely selected and the limit entry is costing more than it saves
- Require **trade-through, not touch**: fill only if price trades ≥1 tick (0.25pt) beyond the 50% level. Stress at 2 ticks with partial fills
- **Run a market-entry control** — same population, entry at next bar's open. If the market version is roughly break-even and the limit version is positive, your entire edge is fill price improvement, and the fill model becomes load-bearing rather than a detail

Costs: NQ RTH spread runs ~2.3–2.7 ticks (~0.6pt); budget ~1pt round trip in NY AM and more in London.

**Exit:** raw expectancy in R and points, fill rate and no-fill cost reported, entry-price perturbation passed. **Gate: if the edge doesn't survive trade-through plus costs, stop here and fix the entry before any parameter work.**

## Stage 4 — Geometry and exit

Two defects to fix before anything downstream is measured against them.

**The 2pt stop.** Fixed points across a span where band widths doubled 28.6 → 52.8. Replace with a fraction of a measured width plus a tick floor. Grid a few declared values — don't sweep.

**The wick-width trap.** Stop ≈ half wick + 2pts, target is a fixed price, so R is mechanically set by wick width and your "min 1R" is a covert filter excluding wide wicks — plausibly your most violent, best displacements. Three things to test as explicit hypotheses: re-include wide-wick setups and read their MFE; scale entry depth by wick width (33% or 25% on wide wicks) to cap R while keeping the level logic; decouple the target from geometry entirely.

Then test the exit against the stage-2 MFE table: fixed R at several levels, structural, hold-with-stop, partial-plus-trail. **Choose from a plateau interior, never the argmax, never a grid edge.**

**Exit:** stop scale-free, exit chosen from a plateau, both surviving monthly folds.

## Stage 5 — Session and time-of-day (your priority question)

The cheapest large effect available, and it answers what you actually asked.

- Expectancy in R by session and by 30-minute bucket
- **Spread ÷ R per session.** If median spread exceeds ~15% of median R, a 1–2R design can't survive there regardless of hit rate. This is what formally kills Asia
- Report, don't filter, unless the split was pre-declared
- The two macro windows: 09:45–10:15 straddles the 10:00 data slot; 13:45–14:15 has almost nothing scheduled. Test them as declared time cuts against matched control windows
- **Boundary placebo** for the 90-minute grid: 08:30, 10:00, 09:30, 11:00, 16:00 carry real scheduled flow; 04:00, 05:30, 14:30 carry nothing. If the effect lives only at event boundaries, replace the clock with the calendar
- Anchor London logic to **London local time**, not fixed ET — US and EU DST switch on different dates, so a fixed ET grid drifts an hour for two to three weeks twice a year

**Exit:** per-session expectancy in R and points, spread-over-R per session, boundary placebo result.

## Stage 6 — Bar-only cut study

Cuts, not weights. Bar-only first so findings land on the ~23-month holdout at ±4pp rather than the thin flow venue.

Candidates from the research, all pure OHLC: displacement quality (body/range, range÷ATR), single-bar vs accumulated break, HTF alignment, side-of-VWAP, distance to prior-day levels, wick-width bucket, bars-to-fill.

Discipline: pin every declaration before contact — variable, direction, bin structure, bar. **Seeded split-half**: derive on half one, try to kill on half two, and report the kill rate. Score survivors on monthly folds, day-level clustering, and max single-day contribution. **Score expectancy AND frequency** — a cut that halves trade count can reduce qualifying days.

Keep PXL and PXH separate from the start if the structure differs — but here they're mirror images of one mechanism, so pool unless the data says otherwise. That's the opposite call from your reject/break arms, which are genuinely different bets.

**Exit:** survivors pass the declared bar on half two, folds, and clustering — or go in the base-rate library dead.

## Stage 7 — Order flow (your stage 4)

Flow goes here, not earlier, because it has the narrowest coverage and therefore the weakest holdout.

**Before running anything, compute confirmability.** Six months of NY-AM flow is ~±10pp, so only effects around +20pp or larger are confirmable. Pre-commit in writing that a sub-threshold finding is recorded as interesting-but-unconfirmable, isn't fought over, and doesn't spend the look.

Your listed families, with what each actually needs:

- **CVD / delta divergence** — needs trade prints with aggressor side. Test as a cut: does decision-bar delta agree with trade direction? This is the S1 hypothesis transplanted, and it's the cheapest flow test you have
- **Absorption** — needs BOTH prints and book state. Verify feasibility before specifying; a book-only feed cannot produce it
- **Depth / heatmap walls** — needs MBP-10. This is the one flow family that speaks to **room to run** rather than arrival, which makes it unusually valuable given how scarce tail predictors are. Censored at 10 levels, so state that limit
- **Footprint imbalance stacking** — collinear with delta and with displacement quality on the same bar. Don't count it as independent alongside those

**Hunt a bar-only proxy for anything that survives.** `closeloc` is a natural proxy for aggressive-side dominance and is pure OHLC — if it captures most of a delta finding's effect, the idea becomes confirmable on the wide holdout instead of the thin one.

**Start the live flow recorder now**, whatever else is happening. Forward flow is the only uncontaminated venue that grows, and it's the fallback for everything unconfirmable on six months.

**Exit:** flow findings confirmable and confirmed, or explicitly logged as forward-validation candidates.

## Stage 8 — Loser autopsy (your stage 5)

Where the largest effects usually live, and where one specific error waits.

The threat is **not** multiplicity. A property in 90% of a thousand losers versus 30% of winners is enormous — far beyond any correction. The threat is **pseudo-replication**: at ~3 trades a day over a few hundred days, a day-level property masquerades as a trade-level one. 90% of losers could be 90% of twenty bad days. **Run the within-day vs between-day variance decomposition before believing anything.**

Then: the autopsy is exploratory, so it can't be priced by corrections needing an enumerable trial count. Its output is **hypotheses, not findings.** Everything it surfaces re-enters at stage 6 as a pre-declared cut with its own bar, on data the autopsy didn't touch.

**Exit:** hypotheses written down and queued as declared cuts, pseudo-replication check done.

## Stage 9 — Holdout confirmation

One look, declared first.

- **Aggregation rule committed before opening anything** — pooled with one interval, or sign agreement across all folds, or a stated minimum fraction
- **Two blocks, both must pass.** Stricter than one pooled look, catches internal regime flips automatically, and converts one bit into two so a marginal first result isn't terminal
- **Venue exclusivity:** the six flow-covered NY-AM months go exclusively to the flow test, the remaining ~23 exclusively to bar-only. Otherwise whichever family looks first contaminates the other
- Flow gets **one look, not two blocks** — three months per block is ~±14pp, too thin to mean anything

**Exit:** declared bar met on declared venue, or recorded dead. A failed holdout is a permanent finding.

## Stage 10 — Arming

Score on **P(required qualifying days AND profit target BEFORE an EOD breach)**, day-block bootstrap, not per-trade R.

Then: the dollar arithmetic at each risk tier (a book clearing the floor at $300 may not at $150 — the binding constraint is size, not win rate), joint (target, size) optimisation, paper forward with live recording, live-vs-replay comparison to measure the execution gap, and only then scale.

---

## Order of operations if you want the shortest path to a real answer

Stages 0 → 3 are the whole game. If the fill model shows unfilled setups outrunning filled ones, PXL's entry is wrong and stages 4–10 are wasted work on a bad entry. That's one query against a table you don't have yet — so stage 1 is the real first job, and it's a spec file for Adrian.

Two questions to answer before I write it: which prior low becomes the PXL, and does the body close through the 0 or into the wick.
