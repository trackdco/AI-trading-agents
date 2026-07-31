# PLAN — chained-agents capture test on London (pre-registered protocol)

Written 2026-07-31, BEFORE any agent verdict is generated. Companion/port of the NY
reference (`docs/PLAN-agents-capture-run.md`, `scripts/capture_desk_run.py`,
`.claude/agents/trade-manager-v3.md`, `scripts/grade_desk_run2.py`,
`docs/REPORT-desk-run-2.md`, all on `claude/agents-capture-handoff-26rnvp`). Ported
structure, not ported numbers or ported execution semantics — London's canon differs
from NY's in ways that change the design, recorded in §1-2 below rather than discovered
mid-run.

## 0. What NY proved, and why it's not assumed to transfer

NY's result: agent +100.1R over 763 trades (p=0.003), but the conviction-shuffle null
**failed** — the edge was policy shape (cut losers fast, refuse mechanical exits on
runners), not per-trade discrimination, and a one-line mechanical rule (lock1r_2r)
captured 92% of it at 3x the drawdown. Shipped anyway because the funded risk profile
(maxDD $810 vs $2,476) is what a funded account is graded on. This plan tests whether
the same shape holds on London — a different book, different management baseline,
different execution law — not whether NY's numbers repeat.

## 1. Execution semantics — resolved BEFORE launch (per instruction; this is the part
   that does NOT port directly)

**NY's problem:** the raw canon population allows overlapping/opposing entries; a
close-and-reverse overlay (`apply_close_reverse.py`) and a one-per-level dedupe were
needed to make the baseline match how the book would actually execute.

**London's problem is different, not absent.** The rev-3 book already enforces
one-position-at-a-time via `serial_walk` (`scripts/london_holdout_report.py`): a
candidate whose fill lands before the currently-open position's exit is never taken —
skipped, not reversed-into. That walk is frozen on **V1's own exit times**. The agent
test breaks that assumption the moment it lets a trade run past or exit before V1's
mechanical exit: a candidate V1's book excluded (because it overlapped V1's shorter
hold) may now be legitimately tradeable if the agent exits early; a candidate the frozen
book DID include may no longer be reachable if the agent holds longer. Reusing the
frozen 130-trade V1 book as "the population" would silently misstate both directions.

**Resolution:** the driver walks the **pre-serialization candidate population** (window
+ floor 9.5pt + score-0 veto, i.e. `build_book(..., "rev3")` with the `serial_walk` step
skipped — **161 candidates, 93 days, 39 days with >=2 same-day candidates, max 9/day**)
chronologically per day, and re-derives one-at-a-time admission LIVE from each
trade's REAL realized exit (agent-managed), not from V1's frozen exit. A candidate is
skipped iff its fill lands before the prior open position's actual exit, under
WHICHEVER arm is being graded (mechanical V1 walk for the baseline column, agent's
real exit for the agent column) — so the two arms can legitimately admit different
candidate sets on the same raw population, exactly as a live desk running either policy
would. There is no "flip/reversal" law for London (unlike NY): a skipped candidate
simply never existed for that arm, it does not close-and-reverse into anything.

**Two-session law does not apply.** NY flattens pre-market positions hard at 09:30
(a house rule specific to NY's pre/gold split). London has one continuous window
(08:00-09:45 London entries) with a single universal flatten:
`config/strategy.yaml` `session.eod_flatten: 15:55` ET, same mechanism the engine
already uses for every London trade. No pre-flatten override needed or added.

**One-per-level dedupe:** subsumed by one-at-a-time (two positions can never be open
regardless of direction or level), so no separate rule is needed.

## 2. Data resolved (verify-before-promising, per instruction)

- **Flow tape**: `output/fp_minutes.parquet` already spans 2025-06-01 18:00 ET through
  2026-07-19, in NY tz, columns `delta`/`vol` — the SAME file used for NY, not
  session-specific. Covers the London window (03:00-06:00 ET DST-dependent) directly;
  no separate build needed for fit.
- **Depth**: `data/reference/depth_london/` (295 day-files, fit) and
  `data/reference/depth_london_2023_24/` (128 day-files, holdout — sealed, not used
  yet). Same condensed MBP-10 wide format `scripts/london_depth.py` already parses
  (`load_day`/`depth_at`) for the L3 features used all session — reused verbatim for
  the live book-line rather than re-derived.
- **Working target**: `output/l2_outcomes_london_fit_v1.parquet` carries
  `working_target` (the real structural price V1 exits at) — this is the mechanical
  plan the agent inherits at fill, same role as NY's `working_target` column.

## 3. Population and baseline

161 pre-serialization candidates (§1), NOT the frozen 130-trade V1 book. Baseline =
**V1** (BE at +1R, run to real structural target) — London's canon management
(`docs/LONDON-MGMT-TOURNAMENT.md`), replacing NY's V8. Same fills/stops/targets for
both arms; only management differs, exactly as the mgmt tournament's own convention.

Segmentation reported (never averaged away): era (2025/2026), fill time-bucket
(08:00-08:30/08:30-09:00/09:00-09:30/09:30-09:45, matching the rev-3 report's own
buckets), pattern (B2/displacement), both-wall vs one.

## 4. Decision points (per trade)

Event-driven, same shape as NY (`manage_trade`, ported): position opened, press check
at fill+3m, each whole-R touch, giveback >=0.75R off a >=1R peak, flow-against-a-green
position (5m CVD via `fp_minutes`), the V1 mechanical-exit minute (take or refuse),
10-min rechecks while extended, 30-min-to-flatten warning. MAX_TURNS 10/trade,
CLI_TIMEOUT 240s, next-bar-open execution +/-1 tick slip, stop-first, EOD flatten
absolute.

**Day thesis: single read, no re-read (design choice, differs from NY).** NY reads a
07:45 pre-market thesis plus a 09:40 cash-open re-read because it has two distinct
sessions (pre, then a separate cash-open regime). London has one continuous window; there
is no analogous mid-window regime change to re-read at. One thesis read per day, timed
at that day's own DST-resolved window start minus 15 minutes (`window_et(day)`, already
used by the L0 builder) — not a fixed ET clock time, since the window itself is
London-local and shifts with DST.

## 4b. Dynamic one-at-a-time admission (the concrete mechanism for §1's resolution)

Per day, candidates sorted by fill time. Two independent "open_until" trackers, one per
arm (mechanical-V1, agent):
- A candidate is skipped for an arm iff its fill lands before that arm's own running
  open_until (its previous trade's own real exit, under that arm).
- If skipped for the **agent** arm: the agent never sees it (no CLI call, no cost) —
  logged as `skipped_by_agent_timing`, no agent_R.
- If skipped for the **V1** arm but NOT the agent arm (the agent exited its prior trade
  earlier than V1 would have, opening a door V1's book never had): the agent manages it
  as a real trade, but there is no V1 baseline for it — logged as `agent_only`, v1_R is
  null. This is symmetric with the reverse case above; neither is forced into an
  artificial equivalence, matching how this session's own V0-vs-V1/V9-vs-V1 comparisons
  already disclose "only-in-one-arm" trades rather than paper over them.
- Both eligible: agent manages it, and V1's own walk is computed independently
  (bar-mechanics only, no agent call) for the paired agent_R-vs-v1_R comparison.

Grading reports the mechanical book total, the agent book total, AND the paired
intersection delta — all three, not one blended number.

## 5. The terrain — measured on London's own V1-managed book, NOT NY's numbers

(n=130 real-V1-managed trades; walk validated against the engine: median per-trade
|R difference| 0.018, net $22,890 vs engine $22,665 — the same walk used for the
lock-level sweep earlier this session.)

- Reach ladder (touched before the real exit): +0.5R 91%, +1R 72%, +1.5R 54%,
  +2R 33%, +3R 13%.
- Winners (n=38, hit the real target): median MAE ~0.00R, median peak timing 10 min,
  mean peak +2.82R. Losers/scratches (n=92): median MAE +0.08R, median peak timing
  3 min, mean peak +1.43R.
- Post-peak giveback (trades whose peak reached >=0.5R, n=118): median +1.48R,
  mean +1.21R.

**Structural finding that changes the spec, not just its numbers:** NY's "press
state" (touched +0.5R by minute 3-5, still green, near peak) predicts a 79-88% win
rate there — a genuine persistence signal. **London shows no such thing**: trades
touching +0.5R by minute 3 (82% of the book) win at 32%, statistically indistinguishable
from the 29% book base rate, in both eras (31%/32%). Early, shallow excursion is
close to universal here and carries no information.

What DOES carry information is **depth of excursion reached at any point**, not speed:
reached +1R eventually -> 35% win rate; +1.5R -> 47%; +2R -> 60% (vs 29% baseline) —
monotone and real in both eras. This is close to tautological (a trade needs to pass
through +2R to reach its ~+3.4R average target) but it is the honest signal available,
and it is a DEPTH gate, not a SPEED gate. **The spec below is written around this
signal, not a copy of NY's press-state lockout**, which has no empirical basis on
this book.

## 6. Metrics (mirrors NY PLAN §6)

Per-trade, same fills: agent_R vs v1_R delta, WR, funded-sizing delta
(`funded_book.run`, lucid profile — London does not yet have a scaled-tier profile;
report lucid only, flag if that changes). Book totals alone are inadmissible. Every
deviation from V1 carries the verdict's rationale in the journal.

## 7. Nulls and ceilings (mirrors NY PLAN §7)

- **Conviction shuffle**: agent verdicts (realized hold-times) reassigned within
  (era x V1-outcome-sign) strata — NY used (sess x mech-sign); London has no session
  split, era replaces it as the only other stable stratifier at this n. If the real
  assignment does not beat the shuffle, the agent is a coin with commentary, same as
  NY's finding.
- **Mechanical control** (the bar the agent must beat, not just V1): **lock1r_2r**,
  ported directly — at V1's own exit minute, if peak had already reached +2R, refuse
  the exit and lock stop at +1R instead; otherwise take V1's exit. Same one-line
  control NY used, same rationale (agents must beat the best mechanical idea, not just
  the shipped one, to justify existing).
- **Oracle ceiling** (hindsight-optimal exit per trade): report-only, never a target.

## 8. Holdout protocol

**SEALED. Fit only.** The 128-day 2023/24 span is not touched by this test. Depth
(`depth_london_2023_24/`) exists and flow-tape-at-minute-granularity coverage for the
holdout has NOT been verified here (out of scope until a holdout look is authorized) —
recorded as an open item, not assumed. One look, spent only on Angus's explicit go,
with a frozen policy, exactly as the prereg discipline elsewhere in this repo already
requires for this same sealed span.

## 9. Kill criteria (pre-committed, identical structure to NY PLAN §9)

The agent arm dies, and the capture question closes with it, if ANY of:
- fit mean deltaR vs V1 <= 0, or positive only via <=3 trades (drop-top-3 fragility),
- it loses to the lock1r_2r mechanical control on fit,
- era-split flips sign across fit-2025 vs fit-2026,
- the conviction shuffle matches the real verdicts (null >= real, p >= 0.05).

"Agents don't beat V1" is a valid, valuable outcome on this book too — every mechanical
enhancement tried on London today (V9, partial-take-then-BE at 6 levels, stop-lock at
6 levels) lost to plain V1; a discretionary agent losing as well would close the
management-improvement question with the same finality, on different grounds
(policy-shape vs no-shape at all).

## 10. Run size and cost (why no subsample, unlike NY's initial 3-month sample)

161 candidates over 93 days vs NY's 763 over ~13 months — proportionally
~1.5-2 hours of wall-clock at NY's observed rate (~8-10h/763 trades), well within a
single validate-then-launch cycle. Runs the ENTIRE fit span in one pass; no smaller
initial subsample is pre-registered, matching where NY's OWN protocol ended up
("Phase 1: the ENTIRE fit span, chronological" — comment in `capture_desk_run.py`
reflecting Angus's later "im happy to run a bigger chained run" ruling) rather than
NY's original 3-month starting point.

**Validation gate before the full run** (per instruction, non-negotiable): one day,
end-to-end, transcript shown, before the chain launches on the full 93 days.

## 11. Checkpointing

`runs/desk_london/journal.jsonl` (append-only), `runs/desk_london/state.json`
(resumable), `runs/desk_london/transcripts/<trade_id>.json`. Commit on a cadence
during the full run (this session's containers can die mid-run, same risk NY
disclosed twice).
