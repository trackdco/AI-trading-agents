# Desk run — London, phase 1 grading (fit span, 161 candidates)

Written 2026-07-31, immediately on completion. Graded against the pre-registered
protocol in `docs/PLAN-agents-capture-london.md` §6-9. Port of the NY design
(`claude/agents-capture-handoff-26rnvp`) — see that plan for every place London's
execution semantics and terrain differ from NY's, discovered and resolved before this
run, not after.

## Verdict in one paragraph

**The agent loses to V1 on this book, and the pre-registered kill criteria confirm
it should stop here.** Paired stats (n=128, excluding 4 agent-only trades with no V1
baseline): agent +78.6R vs V1 +96.0R, **delta -17.4R** (mean -0.136R/trade, not
significant, sign-flip p=0.27). Era split does not flip sign (both eras negative:
2025 -4.8R, 2026 -12.6R) but that only means the underperformance is consistent, not
that it's acceptable. The conviction shuffle fails even more decisively than NY's did
(p=0.963 — random timing reassignment beats the agent's actual choices 96% of the
time). The one criterion the agent DOES pass — beating the lock1r_2r mechanical
control (+78.6R vs +28.0R) — is not much comfort: that control is a poor bar on this
book, since even V1 alone beats it by more than 3x. **Kill criterion 1 (mean deltaR
<= 0) trips on its own; this is not a marginal case.**

## The mechanism, in five trades

The worst 5 paired deltas alone sum to **-27.8R** — MORE negative than the entire net
delta. Every one is the identical failure mode:

| trade | agent | V1 (real) | delta | what happened |
|---|---|---|---|---|
| 2026-03-31 | +1.74R | +10.37R | -8.63R | tightened on one flow-flip read after a 2.67R giveback; V1 rode the fixed target |
| 2026-03-25 | +0.25R | +7.58R | -7.33R | "3 consecutive reads show flow flip... lock partial" — exited near breakeven |
| 2025-11-04 | +0.97R | +5.44R | -4.47R | short-term flow flip + nearby wall — locked early |
| 2026-03-02 | +4.46R | +8.15R | -3.70R | trailed to lock +4.5R "given exceptional run" — the run kept going |
| 2025-11-17 | +1.46R | +5.10R | -3.64R | "rare +3.7R peak decelerating" — locked partial, left the rest |

**This is not noise — it is the SAME finding this entire branch already established
by every other method tried today.** V9's giveback ratchet lost to V1 on both defense
and offense. Partial-take-profit-then-BE lost to V1 at every tested level (0.5R
through 2.5R). Moving the BE stop to anything other than exactly breakeven (tighter
or looser) lost to V1 at every tested level. Now a fully discretionary LLM agent,
reading real-time order flow and depth, loses to V1 the same way, for the same
reason: **London's edge lives in a small number of very large winners running
undisturbed to a real, distant structural target. Every form of "protect the gain"
tested against this book — mechanical or discretionary — gives up more than it
saves, because it is fundamentally impossible to distinguish "this run is done" from
"this run has 8 more R in it" from a flow read at the moment it happens.** V1's
answer — don't try, just hold the fixed target — keeps winning because it is the
only tested policy that never pays this tax.

## Headline numbers

| | V1 (real) | agent | lock1r_2r control |
|---|---|---|---|
| trade R (paired, n=128) | +96.01R | **+78.60R** | +28.03R |
| win rate | 28.9% | **47.7%** | — |
| funded (flat $250/trade, MNQ micros) net | **$+23,982** | $+19,722 | $+7,045 |
| funded maxDD | $931 | **$907** | $1,320 |
| funded worst day | **-$505** | -$509 | -$577 |

Same win-rate illusion as everywhere else in this session's work: the agent's 47.7%
WR looks far better than V1's 28.9% — and makes LESS money, because V1's structural
28.9% WR converts its rare wins into full-target runners while the agent converts
more trades into small, protected wins at the cost of the tail.

**Funded note:** agent still narrowly wins on maxDD ($907 vs $931) even while losing
on net — a faint echo of NY's genuine finding (agent's real edge was risk shape, not
net R). It is far too small a margin here (2.6%) to read as the same result; NY's
was $810 vs $2,476, a 3x difference. On this book the risk-shape argument does not
carry the day the way it did for NY.

## Pre-registered kill criteria (PLAN §9)

| criterion | result |
|---|---|
| 1. mean deltaR <= 0, or positive only via <=3 trades | **FAIL (kills the arm)** — mean -0.136R; fragility check confirms it's not a top-heavy artifact: dropping the best 3 trades makes it WORSE (-26.29R), because the damage is in the tail of BIG NEGATIVE deltas, not propped up by a few big positive ones |
| 2. loses to the lock1r_2r mechanical control on fit | PASS (agent +78.6R > control +28.0R) — but the control is weak on this book (V1 alone beats it 3.4x), so this pass carries little weight |
| 3. era-split sign flip (2025 vs 2026) | PASS (no flip — both negative: -4.8R / -12.6R) |
| 4. conviction shuffle matches real verdicts | **FAIL** — null >= real p=0.963 (worse than NY's own 0.978 fail) |

Two of four criteria trip, including the primary one (mean delta). Per the
pre-commitment ("dies if ANY"), **the agent arm is dead on this book.**

## Bucket split (descriptive)

| bucket | n | delta | mean |
|---|---|---|---|
| 08:00-08:30 | 35 | **+5.69R** | +0.163 |
| 08:30-09:00 | 33 | -4.96R | -0.150 |
| 09:00-09:30 | 42 | **-18.01R** | **-0.429** |
| 09:30-09:45 | 18 | -0.13R | -0.007 |

All 5 of the catastrophic under-captures land in the 08:30-09:30 window (London
09:30-10:30 local, the heart of the session) — where London's biggest structural
runners apparently concentrate. The earliest bucket (08:00-08:30) is the only one
where the agent adds value, small samples nonwithstanding (n=35).

## Population note

161 pre-serialization candidates; 132 managed by the agent (29 skipped as still-open
under the agent's OWN timing — the dynamic one-at-a-time re-walk, PLAN §4b); 128 of
those paired against a V1 baseline (4 are agent-only: admitted by the agent's faster
exits where V1's own one-at-a-time walk would still have been in a position, no V1
R to compare against — reported separately: agent +6.35R, WR 50%, not part of the
paired delta above).

## Oracle ceiling (report-only, never a target)

Hindsight-optimal: +717.21R. Agent captures 11.0% of it, V1 captures 13.4% — both
tiny, as expected (the ceiling assumes perfect foresight of every peak). Consistent
with NY's own finding that the ceiling number is a report-only sanity check, not
something either arm was ever close to approaching.

## What this means

The capture question has an answer on London too, and it's a cleaner one than NY's:
**not "the edge is policy shape, not judgment" (NY's finding) — here there is no
edge to speak of, in either form.** NY's agent found a real, if mechanizable, +100R
edge. London's agent, given the same architecture, real-time order flow, and a
spec written honestly around London's own terrain (no borrowed press-state
assumption), still loses to the simplest possible policy: hold the fixed target,
change nothing. Combined with today's V9/partial/stop-lock results, this closes the
London exit-management question about as firmly as a single day's research can:
**V1 (BE at +1R, run to the real structural target, no discretion, no ratchet, no
partial) is not just the best MECHANICAL policy tested on this book — it beats a
frontier LLM reading live flow and depth, too.**

## Methods notes

- Baseline is V1 (`output/l2_outcomes_london_fit_v1.parquet`), the rev-3 canon
  management, not NY's V8/three-rule-canon.
- Population is the 161 PRE-serialization candidates (window 08:00-09:45 + floor
  9.5pt + score-0 veto), not the frozen 130-trade V1 book — one-at-a-time admission
  is re-derived per-arm from each arm's OWN realized exit times (PLAN §4b), so the
  agent and V1 columns can legitimately admit slightly different candidate sets on
  the same raw population.
- lock1r_2r control ported directly from NY's grader: at V1's own exit minute, if
  peak had already reached +2R, refuse the exit and lock stop at +1R instead;
  otherwise take V1's exit. Commission-netted.
- Shuffle strata: (era x V1-outcome-sign) — London has no session split (unlike NY's
  pre/gold), so era is the only other stable stratifier at this n.
- Funded: `scripts/london_funded_test.py`'s own convention (flat $250 risk/trade,
  MNQ micros), not NY's lucid/scaled600 profiles, which have no London equivalent.
- Journal: `runs/desk_london/journal.jsonl` (132 rows); grader:
  `scripts/grade_desk_run_london.py` (deterministic, seeded).
