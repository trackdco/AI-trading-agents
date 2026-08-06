# PREREG — the displacement canon, full process, zero hindsight (2026-08-06)

**ANGUS: "lets enter off of displacement now, test things without hindsight...
lets go through the process again." This document is the contract for that
rebuild. Every run is declared here (or in a successor prereg) BEFORE it
executes. Fit only; the 2023/24 holdout stays sealed until one frozen book gets
one human-authorized look.**

## 0. What today already settled (not re-litigated)

- Entry: market at the open of the first 1m bar after the CLOSE-labeled signal
  bar. Label law source-corroborated. Stop: signal-candle adverse extreme ∓1
  tick — caps rejected monotonically in the discover era.
- The raw census is ~breakeven gross, slightly negative net in 2025 under naive
  exits. NAIVE-exit configurations are dead (2R-or-stop, EOD-hold, MAE cuts,
  retrace fork). The limit census looked the same before its engine existed —
  that is the room this program plays in, stated without promise.
- Era-stable raw material for management: losers resolve in 3m median, winners
  in 7m; open winners carry ~0.14R less MAE at every checkpoint (identical both
  eras); flow-confirmed closes hold more often but win smaller (all cells, both
  eras); struct_event broke/rejected separates hugely and is 100% post-T —
  entry-banned, exit-legal.

## 1. Fixed conventions (not tunable, ever)

1. Causality: entry features computable at T only (pre-T audit mandatory);
   in-trade rules may use only information from strictly after entry, minute by
   minute, plus the trade's own state. struct_event enters only via its own
   timestamp as an in-trade event.
2. Costs: 0/1/2-tick ladder + $5/RT; the 1-tick column decides. Netting in
   effective risk.
3. Population: risk ≥ 2pt; gap-through-stop = immediate −1R, never dropped.
4. Reporting: era × session, per-trade AND episode-mean AND day views; episode =
   same-day same-direction chain, gap ≤ 15m. Nominal-n confidence claims banned.
5. Era rule: a rule/check/arm survives only if it points the same way in 2025
   AND 2026 on the declared views. 2026-only findings are dead on arrival.
6. Multiplicity: every declared cell in a round is counted; survivors are
   reported as k-of-N against the round's cell count. No undeclared reruns.
7. Honesty note on hindsight-of-hypothesis: round hypotheses are informed by
   fit-era descriptive statistics — unavoidable; that is what discovery is. The
   controls are: declared-before-run, era rule, multiplicity ledger, and the
   sealed holdout as the only true exam.

## 2. ROUND 1 — the exit engine, declared arms

Baselines: uncut 2R-or-stop and EOD-hold (recorded in
`docs/L2-displacement-census.md`). An arm SURVIVES round 1 only if its net-1t
meanR beats the relevant baseline in BOTH eras on BOTH the per-trade and
episode-mean views. Families run separately; NO cross-products in round 1
(combinations are round 2, declared after round 1 reports).

- **A. Time-stop** (from the 3m/7m autopsy): exit at close of minute m if the
  trade has not reached +xR by then. m ∈ {3,5,7,10} × x ∈ {0.0, 0.25, 0.5}.
  12 cells.
- **B. Partial at +1R**: take p ∈ {25%, 50%, 75%} at +1R (fill assumed at the
  touch, 1-tick slip on that leg), remainder runs stop/EOD. 3 cells × both
  baselines' back-leg (stop-only, or 2R on the remainder) = 6 cells.
- **C. Breakeven after +1R**: stop → entry. 1 cell. Expectation on record: the
  limit canon's BE lesson was negative; declared here because the geometry is
  3× wider — if it fails again, BE is dead in both geometries and stays dead.
- **D. Trail**: after +1R, stop trails highest favorable close minus d ∈
  {0.5R, 1.0R}. 2 cells.
- **E. In-trade flow**: exit at bar close when cumulative post-entry delta
  (fp_minutes, minutes strictly after entry) opposes the position beyond its
  trailing-day q ∈ {0.8, 0.9} quantile. 2 cells. Uses only post-entry data —
  legal by law 1.
- **F. In-trade structure**: exit on a post-entry struct_event 'rejected'
  against the position (via struct_ts, only when struct_ts > entry minute).
  1 cell.

Round-1 total: **24 declared cells**. Kill line: fewer than the family-wise
noise expectation of survivors (≈1–2 of 24 by chance) means the round reports
NOTHING SURVIVES regardless of individual cell prettiness; survivors, if any,
proceed to round 2 (combinations + robustness: LODO, threshold-neighborhood,
riskband stratification) before anything is called an engine.

## 3. Rounds ahead (declared in outline, detailed per-round prereg before run)

- Round 2: combinations of round-1 survivors + robustness battery.
- Round 3: L3 check trial re-judged against the round-2 engine's managed
  outcomes (the canon's pipeline order); features admitted only with a pre-T
  audit attached. The sweep's verified corpus (WALLSZ-gold, bp5opp-gold, D,
  risk floor) re-enters here as declared candidates — nothing carries over as
  a default.
- Round 4: conviction/sizing tiers on surviving checks; session law; assembly;
  the era-rule gate on the full book.
- Round 5: freeze or kill. If freeze: the one holdout look, ANGUS-authorized.

## 4. Ledger

| round | declared | run | outcome |
|---|---|---|---|
| 1 | 2026-08-06 (this doc) | 2026-08-06, `scripts/l2_disp_engine_r1.py` (A–E, 23 cells; F deferred — no struct_ts exists for displacement entries) | **NOTHING SURVIVES — 0/23** beat baseline net-1t in both eras on both views, below the ~1–2 noise expectation. Kill line fires. |

## 5. CLOSURE (2026-08-06)

Round 2 is combinations of round-1 survivors; there are none, so rounds 2–5 are
empty by construction. **The displacement-entry canon process terminates with no
engine and no book.** This closure now rests on the full declared process, not
the quick sweep: entry conventions (settled), stop geometry (candle stop
validated, caps rejected), naive arms (dead), MAE cuts and retrace fork (dead),
and a pre-registered engine round across five management families (dead).

The structural finding, stated once for the record: **every management
intervention in this population trades 2025's losers against 2026's runners.**
Time-stops, breakeven, and in-trade opposing-flow exits all IMPROVE the discover
era (E-family: +0.053/+0.076 per-trade/episode net — the round's best 2025
cells) and all DAMAGE the confirm era, whose entire hold edge is carried by
runners that any early exit clips (partials −0.06..−0.19 in 2026; BE −0.085;
trails catastrophic in both eras). The two regimes want opposite management, and
a rule that flips sign with regime is exactly what the era rule exists to
refuse. The E-family observation (opposing-flow exits help in chop, hurt in
runner regimes) is recorded as a portfolio-level regime insight, NOT a freezable
rule.

The holdout was never touched by any of this. The prereg machine, conventions,
and harnesses carry forward unchanged to the next entry family
(`research/candidates/INTAKE-orderflow-2026-08-05.md`).
