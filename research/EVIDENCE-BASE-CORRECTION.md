# CORRECTION — what the hand log actually is, and what it can support

**Recorded 2026-08-08.** Angus: *"ngl i never traded with this strategy im just relying on you to
research and backtest and find areas it can improve."*

The specification always said it. Line 4: *"Source of truth: **28 hand-backtested trades**
(Feb 2–27 2026, NQ, NY morning) + journals + charts + Q&A."* **I read past it and have written
"realised" throughout** — a word that means executed. That is an overclaim and it runs through
several documents.

---

## What changes

### 1. The hand log is a hand-marked backtest, not a track record

28 setups marked up on historical charts. Not 28 executed trades.

**The difference is not pedantic.** Marking a chart after the fact means the outcome was
visible — usually not deliberately, but scrolling a chart *is* seeing what happened next. A
68.4% win rate at 2.25R mean per trade would be an exceptional live edge. As a hand-marked
figure it is the number that a person who already knew the answer produced, and it should be
treated as such.

**No accusation is intended and none is needed.** Hindsight contamination in hand-backtesting is
structural, not a lapse. It is why the discipline exists.

### 2. What the hand log can and cannot support

| can | cannot |
|---|---|
| Define **what kind of setup** the strategy is about | Establish a win rate |
| Show the **scale** Angus works at — 35-point stops, ~30-minute holds, ~1 trade a session | Show the strategy is profitable |
| Anchor the **breakeven comparison** as a sanity check | Clear breakeven as *evidence* |
| Reveal criteria the spec is missing, as it did today | Serve as an out-of-sample result |

### 3. Figures that were resting on it, and where they now stand

| figure | status |
|---|---|
| **68.4% in-scope win rate**, Wilson [46.0%, 84.6%] | **Hand-marked.** Not a measured win rate. Every comparison against breakeven is now a sanity check, not evidence |
| **Gate 3 PASS** | **Unaffected in its arithmetic.** Breakeven of 43.90% is a property of geometry and costs, computed independently. What weakens is the supporting claim that the required rate is demonstrably attainable — that rested on the hand log |
| **Mean +3.678R on winners, median stop 35.00 pts** | Still the best available description of *intent and scale*. No longer described as "realised" |
| **Gate 1 SIZING PASS** | **Unaffected.** Rests on stop distances and contract counts, which describe intent regardless of execution |
| **The A5 10-point floor** | **Unaffected in its justification.** A5 was argued from measured spread and fill realism; the hand-log stop range was a supporting check, not the basis |
| **Gate 6, the tripwire, the axis table** | **Unaffected.** All computed from the detector's own frequency and the cost model |

### 4. The sealed workbench result is now worth *more*

`workbench_results_SEALED.parquet` — 1,423 trades, 501 sessions, unread — is **the first
mechanical, hindsight-free measurement this strategy will ever have had.** The hand log is
hindsight-contaminated by construction; the sealed run is not. That raises its value, and it
raises the cost of reading it carelessly.

### 5. Language corrected

"Realised" implies execution and appears in `preflight.md`, `opportunity-set.md` and
`PREREGISTRATION.md`. Corrected to **"hand-marked"** or **"recorded"**. The underlying numbers do
not change; the claim attached to them does.

---

## What does NOT change

- **Angus's judgement is still the right reference for what the spec should say.** He is the
  author. Today's exercise — asking why he would skip a setup — found two missing entry criteria
  and that finding stands entirely. Specifying a strategy and validating one are different jobs,
  and his judgement is authoritative for the first.
- **Every gate, audit and amendment stands.** The point-in-time audit, the nine engine defects,
  A1–A7, the cost measurement, the orderflow work — none of it depended on the hand log being a
  track record.
- **The spec is a better-specified document than it was a week ago**, and that was the actual job.

---

## The tension worth naming

Angus's ask is *"research and backtest and find areas it can improve."* The pre-registration
discipline says: set the pass marks, read the result once, do not iterate.

**These are not in conflict, but they must be sequenced, and the counter is what keeps them
honest.**

- **The workbench exists to be iterated on.** 539 sessions, already contaminated by development,
  and that is what they are for. Finding improvements there is the correct use of them.
- **Every improvement chosen by comparing outcomes increments N_trials.** That is not a penalty
  and not a budget to protect — it is the record of how many things were tried, and it is what
  makes the final confidence interval honest.
- **N_trials is 0 today** only because nothing has yet been chosen by looking at a result. The
  moment the improvement work starts, it climbs. **That is expected and allowed.** What is not
  allowed is losing count.
- **The holdout is the one measurement that survives all of it** — 257 sessions, sealed,
  answering once at the end, with the alpha deflated by whatever N_trials has reached.

So: iterate freely on the workbench, count every trial, and spend the holdout once. **The
sequence is what makes the last number mean anything.**

---

**N_trials: 0. Holdout sealed. Sealed workbench result unread.**
