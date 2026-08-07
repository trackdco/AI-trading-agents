# Proposed adjustments for regime agent v0.4 — for Angus review, then Pat

Target metric: regime-read accuracy (scripts/score_regime_reads.py). Baseline v0.x on
March 2026: 43% reads, 17% read-quality capture, −$1,715 P&L (v0.3.0). Dominant miss:
event_risk over-call — 12 FLAT calls where the oracle wanted 8, seven misses on
tradeable days. At 60–70% reads the same architecture plausibly outperforms the
champion (rough March math: capture scales ~linearly with reads → ~45–55% capture ≈
+$5–6k vs champion's +$4.3k, and the insurance pays extra in red months).

## A. What the agent SEES (engine lane — buildable now)

A1. ANALOG BLOCK in the briefing. For today's regime vector: the K=15 nearest days from
    the 850-day library, each with its realized best action (rotation/momentum/flat) and
    both books' P&L. Regime reading becomes retrieval-plus-judgment instead of inference
    from one morning. THIS is "understanding the historical data" made literal.

A2. AMT FEATURE UPGRADE. The current day-type input is one overlap ratio. Add (all
    pre-open computable): overnight value position vs prior day's VA (above/inside/below
    — the 80%-rule setup), open-vs-value location, prior close location in prior VA,
    overnight inventory direction + size, overnight range vs 20d norm. These are the
    auction-theory reads that actually distinguish rotation from migration mornings.

A3. EVENT ANALOGS. Calendar says "CPI today"; it should also say: "last 6 CPI days:
    median morning range X, champion made money on 4, the release resolved directional
    by 09:15 in 5 of 6." Retrieval kills the boy-who-cried-wolf pattern behind 7 of the
    12 March misses.

## B. How VERDICTS work (Pat lane)

B1. 09:30 SECOND LOOK, release-only authority: may lift an 08:00 brake, never add one
    mid-session. Directly targets the 03-17 class (reasonable caution, disproven by the
    open, unrevisable all day).

B2. EVENT-RISK EXPIRES. Pre-release stand-down auto-expires once the release resolves
    (e.g. CPI 08:30 → verdict void at 09:00, agent re-reads the post-release tape).
    03-10/11/17 were post-release trend days lost to all-day event flats.

B3. SPLIT THE TAXONOMY. {balance, war, trap, event_risk} conflates tape-state with
    calendar-state. Two axes: tape ∈ {rotation, momentum, trap, unclear} × event-flag ∈
    {none, pre-release, post-shock}. Event becomes a timing MODIFIER, not a regime —
    an event morning can still be a momentum day after 09:00.

B4. HEALTH-CONDITIONED DEFAULT (Angus ruling, filed): unsure → follow baseline only
    where baseline's trailing expectancy is positive; else unsure → defend.

## C. How it LEARNS

C1. Scorecard feedback: each morning's briefing includes the agent's own running
    read-accuracy BY MISS CLASS ("your event_risk calls: 2/9 correct") from the ledger.
C2. Regret lines: every intervention's counterfactual cost (both arms run daily) goes
    into the playbook notes — the agent confronts the price of each brake it pulled.
C3. Confidence calibration tracked: if 'high' confidence doesn't outperform 'medium',
    confidence loses authority (ties into library-depth gating, finding #6).

## D. Process guard

D1. All of A+B+C land as ONE version bump (v0.4). Fair exam = months the agent was not
    iterated on: May 2026 + one 2025 quarter. Score reads first, P&L second. No further
    March retests count for anything.

Engine lane commits to A1–A3 (data plumbing) immediately on Angus's go.

## Engine-lane predictions (pass 34 — to be GRADED by the fair exam)

P1. Reads on March-class months: 43% -> 60-67% (B2/B3 convert 4-5 of the 7 event-flat
    misses; A2 catches 1-2 of the 3 trap-day misses; B3 half-fixes the war/rotation mix).
P2. March P&L: -$1,715 -> +$2,500-4,500, still likely UNDER the champion (+$4,276) —
    insurance premium never reaches zero in a green month; beating the champion on March
    would itself be a warning sign of March-overfit.
P3. Red months are the payoff: May 2026 agent arm +$800-1,500 (champion +$10); a 2025
    quarter's bleed cut 40-60%, ~50/50 odds one 2025 month flips green on flats alone.
    Acid test: agent beats champion on {Mar + May + 2025 quarter} COMBINED.
P4. Risk register: B1 whipsaw if release-only leaks; A1 confident-nonsense on
    novel regimes (library-depth gate is the guard); B2 walks into post-release traps of
    the Aug-2024 class (A3 event analogs must flag "day stayed hostile" shocks); bundled
    v0.4 muddies attribution -> reads scored before P&L, always.

## THE BAR (Angus, 18 Jul, 5am — pre-registered before any 2025 run)

Angus, verbatim intent: "The real tell is where the champion lost money in 2025.
If we run the agent in a span in 2025 and it maintains profitability, I actually
do agree with you on that."

Locked as the exam's pass condition so nobody can move the goalposts afterward,
in either direction:

- **Exam:** Q2 2025 (Apr–Jun), sequential driver, fresh-eyes panel if built,
  reads scored before P&L. Requires Brake's calendar file first.
- **Context:** champion is RED in every month of the span (E3 −$5,870,
  E4 −$2,772 across the quarter; oracle+SD ceiling +$18,132).
- **PASS:** agent arm finishes the quarter ≥ $0 while following its own verdicts
  at full discipline. That is "maintained profitability where the champion lost."
- **Distinction:** ≥ 30% oracle capture (≥ ~$5.4k) = the 55–60% story has a pulse.
- **FAIL:** agent arm red on the quarter → the insurance-premium critique stands
  everywhere, not just in green months, and the design pivots (fresh-eyes panel,
  briefing features, or deeper).

## THE INFORMATION BUMP (v0.5) — Angus-approved direction, 18 Jul (late)

Three measured defects, one root cause: the agent decides in an information
vacuum and is never billed. The bump is three wires, landed as ONE version
(D1 one-bump rule) so attribution stays clean, graded reads-first:

- **W1 (fixes: empty feedback loop).** Sequential driver appends the
  `yesterday_result` block (spec in TASK-FOR-PAT doc): realized / full-size
  counterfactual / oracle dollars + sizing_regret + rolling-20d cumulative
  regret and expectancies. Mechanical, no agent turn. — Pat
- **W2 (fixes: unpriced fear inputs).** Briefing joins the two retrieval tables:
  `analog_days` (A1 block, built — the "15 mornings like this and what paid")
  and the base-rates digest (built, --asof for replays). Every danger signal now
  arrives priced. — Pat wiring; engine tables done
- **W3 (fixes: magnitude blindness).** Prompt bump: reason and justify in
  expectancy DOLLARS, not event probabilities; sizing notches widened to
  {0, 0.25, 0.5, 0.75, 1.0}; verdict schema adds `expected_value_usd` (its own
  stated EV, so calibration becomes gradeable per C3). — Pat prompt/schema

Exam unchanged: May 2026 + Q2 2025 (post-calendar, base rates --asof
2025-04-01), reads before P&L, sizing graded on score_sizing.py discrimination.

## PREDICTIONS P5–P8 (filed before any v0.5 run — grade me)

- **P5 (reads).** 3-way reads on exam months: 50–58% (from ~40% avg). Hard
  floor: the agent must beat the mechanical analog-majority baseline (52% in
  2026, 44% in 2025). If the agent reads BELOW the majority-of-analogs it is
  subtracting judgment from retrieval — that would be a design-level fail, not
  a tuning miss.
- **P6 (sizing).** Discrimination (avg size winners − losers) from +0.09 to
  ≥ +0.20; cost-on-winners down 40–60% while saved-on-losers holds within
  ±25%; net sizing effect ≥ −$500/quarter (from −$3,810/4mo).
- **P7 (money).** Green-month capture 30–40% (from 17–27%). Q2 2025 exam: PASS
  per the pre-registered bar (≥ $0), central estimate +$2,500–5,500 vs the
  +$18,132 ceiling (14–30% capture) — vol-normalization gate G7 is the main
  drag risk on this one.
- **P8 (new failure mode this bump can CREATE).** Regret feedback can over-swing
  the agent aggressive (counterfactual-chasing: "yesterday's caution cost $800 →
  size 1.0 always"), and base-rate priors can make it lazy ("priors say flat,
  skip reading today's tape"). Detection is already built: under-FLAT cost line
  (E4 scorecard) rising month-over-month = over-aggression; verdicts citing
  priors without same-day tape evidence in cited_evidence = laziness; fresh-eyes
  divergence spiking = either. Named in advance so nobody discovers it in a
  crash-out.
