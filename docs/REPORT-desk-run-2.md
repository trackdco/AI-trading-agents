# Desk run 2 — phase 1 grading (fit span, 763 trades)

Written 2026-07-30, immediately on phase-1 completion. Graded against the
pre-registered protocol in `docs/PLAN-agents-capture-run.md` §6–§9. Phase 2
(the one-shot holdout chain) has NOT been launched — that look waits for an
explicit go.

> **POSTSCRIPT — ANGUS SHIP RULING (2026-07-31).** Shipped to live as-is: frozen v3
> spec, desk-live semantics, journal seeded (`runs/live/journal.jsonl`). Rationale is
> the funded criterion, with the shuffle result on the table: "remember its a fundd —
> it prevented lots more losses than where it didnt capture winners fully, and thats
> completely fine." The agent's advantage over the mechanical distillate is precisely
> the risk shape (maxDD $810 vs $2,476), which is what a funded account is graded on.
> The holdout look stays sealed and unspent. Arming detail: HANDOVER-pat-arming row M.

## Verdict in one paragraph

The desk-live agent beat the three-rule mechanical canon by **+100.1R over 763
trades (p = 0.003)**, with the delta positive in 12 of 13 months, both eras,
and surviving the drop-top-3 fragility test. It did it exactly the way the
thesis wanted: **average winner unchanged (+1.464R vs +1.462R), average loser
cut from −0.708R to −0.576R, and 27 mech losers converted into wins** (win
rate 59.2% vs 56.1%). Funded (lucid): **$95,194 vs $77,202 (+23%), with maxDD
cut from $1,268 to $810** and worst day −$479 vs −$670. However, two humbling
results temper the story: a one-line mechanical rule (lock1r_2r) captures
92% of the same delta, and the conviction-shuffle null FAILS — the agent's
per-trade timing choices are not distinguishable from random reassignment of
the same holding times. The edge is real but it is **policy shape, not
per-trade discrimination** — and policy shape is mechanizable.

## Headline numbers

| | mech (3-rule canon) | agent | lock1r_2r control |
|---|---|---|---|
| trade R (net) | +388.6R | **+488.7R** | +480.5R |
| win rate | 56.1% | **59.2%** | — |
| avg winner | +1.462R | +1.464R | — |
| avg loser | −0.708R | **−0.576R** | — |
| funded lucid net | $77,202 | $95,194 | **$96,433** |
| funded lucid maxDD | $1,268 | **$810** | $2,476 |
| funded lucid worst day | −$670 | **−$479** | −$650 |
| funded scaled600 net | $271,653 | $324,207 | **$346,049** |
| funded scaled600 maxDD | $4,892 | **$3,158** | $9,548 |
| months green (all arms) | 13/13 | 13/13 | 13/13 |

Decomposition: defense **+231.4R** across 335 mech losers (+0.69/loser);
offense **−131.3R** across 428 mech winners (−0.31/winner). The agent touched
its exit on 76% of trades. Oracle ceiling (hindsight-optimal exit, report-only):
+2,749R — agent captures 17.8% of it, mech 14.1%.

## Monthly ledger (delta R vs mech)

| 25-06 | 25-07 | 25-08 | 25-09 | 25-10 | 25-11 | 25-12 | 26-02 | 26-03 | 26-04 | 26-05 | 26-06 | 26-07 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| +2.1 | +2.8 | +3.2 | +9.9 | −4.3 | +10.5 | +14.7 | +2.6 | +5.5 | **+36.9** | +2.7 | +1.1 | +12.5 |

12 of 13 green. No month-on-month learning trend: offense-per-winner
oscillates (−0.09 to −0.70) with no drift toward zero; the delta's size
tracks the month's **round-trip frequency** (how often price runs past +1R
and comes all the way back — April 2026 being the extreme) rather than
either the book's quality or the agent's accumulated journal. The learning
hypothesis, as instrumented here, is **not supported**.

## Pre-registered kill criteria (PLAN §9)

| criterion | result |
|---|---|
| 1. mean ΔR ≤ 0, or positive only via ≤3 trades | **PASS** — mean +0.131R, t = 2.94, sign-flip p = 0.00325; without top-3 still +81.2R |
| 2. loses to best mechanical control on fit | **NARROW PASS on R** (+8.2R over lock1r_2r, commission-netted, same law horizons); on raw funded net the control wins (lucid $96.4k vs $95.2k) but at **3× the drawdown** ($2,476 vs $810) |
| 3. era-split sign flip (2025 vs 2026) | **PASS** — fit-2025 +38.8R, fit-2026 +61.4R, both positive |
| 4. conviction shuffle matches real verdicts | **FAIL** — null ≥ real with p = 0.978 (see below) |

Criterion 4 trips. Under the pre-commitment ("the agent arm dies if ANY"),
the agent arm **as a per-trade discretionary discriminator is dead**. What
survives is the policy it converged on.

## The conviction shuffle, plainly

Within (session × mech-outcome) strata, the agent's holding times were
randomly reassigned across trades and replayed through the same law walk
(stop-first, flip law, session flatten), 1,000 draws. The agent's own timing
replays to +550.2R; the null averages **+602.5R** (σ 25.9). Random
reassignment of the *same time budget* does better than the agent's specific
choices of which trade to cut when.

Read precisely: the shuffle preserves the agent's hold-time *distribution* —
that distribution IS the policy (cut losers fast, sit on winners past canon
exits). The test only asks whether the agent picked *which* trades got which
treatment better than chance. It did not. All of the +100R delta is carried
by the shape; the per-trade "reads" of tape/depth added nothing measurable
on top, and cost a little.

Session split says the same thing from another angle: the entire delta is
gold (+101.3R on 536); pre is flat (−1.1R on 227) — pre's 09:30 hard flatten
leaves no room for the shape to express, and without the shape the agent has
no edge.

## What this means (for the morning)

1. **The capture question has an answer**: the ceiling above V8 is real
   (+100R fit) and reachable, but the mechanism is a policy, not a per-trade
   judgment. A mechanical distillate — defense (giveback/flow cut on losers)
   + lock1r_2r-style refusal on runners — is now the natural candidate.
2. **The agent's genuine advantage over lock1r_2r is risk shape**, not net:
   maxDD $810 vs $2,476 on lucid. If that survives distillation, the
   distillate keeps it; if it doesn't, that's evidence some discretionary
   defense component matters after all. Testable on fit before any look.
3. **The holdout look (one shot, NOT spent)**: per PLAN §8 only a frozen
   policy earns it. Given the shuffle result, spending it on the agent chain
   as-is is hard to justify; the distillate (or distillate + frozen agent
   ablation) is the better candidate. Decision is Angus's.

## Methods notes

- Baseline is the three-rule canon (CR overlay): suppressed rows dropped,
  flip/pre-flatten exits substituted. Same fills, stops, and law horizons for
  every arm.
- lock1r_2r control re-implemented on THESE horizons (the old +19% figure was
  old-canon): at the canon exit minute, if +2R had printed (bar extremes),
  refuse the exit and hold with stop locked at +1R until stop/flip/flatten;
  stop-first, next-bar-open flatten, slip as the driver. Commission-netted
  (the raw walk is gross; mech/agent dollars are net — netting moved the
  control from +495.1R to +480.5R, which is what makes criterion 2 a narrow
  pass instead of a kill; flagged for honesty).
- Shuffle strata deviate from PLAN §7's "(sess, decision-reason)": the desk
  design has no discrete verdicts, so (sess × mech-sign) is the closest
  stable stratification. Replay executes single full exits at next-bar-open;
  partials/targets are not replayed (both sides of the comparison use the
  same executor, so the p-value is internally consistent).
- Funded runs use `funded_book.run` on the full 13-month span, static
  sizing, both profiles; maxDD is peak-to-trough on the cumulative daily
  curve.
- Journal: `runs/desk2/journal.jsonl` (763 rows); grader:
  `scripts/grade_desk_run2.py` (deterministic, seeded).
