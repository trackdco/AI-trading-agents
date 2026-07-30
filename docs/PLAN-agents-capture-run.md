# PLAN — chained-agents capture test on the rebuilt canon (pre-registered protocol)

Written 2026-07-30, BEFORE any agent verdict was generated, so the holdout protocol in §8 is
a declaration, not a rationalisation. Companion to `docs/HANDOFF-agents-capture.md` (the
mission + rules); this doc is the concrete run design. ANGUS is still ruling on mechanical
exit variables (25% partial unshipped; fixed-R family grid in flight) — the agent layer sits
above whatever mechanical baseline ships, and is measured against V8 as canon law today.

## 1. What is already built and proven

- **Settlement harness** `scripts/capture_replay.py`: causal minute walk over each canon
  fill (decision at minute t sees bars ≤ t only; stop checked BEFORE the decision; stops
  only tighten; P&L anchored on the book's own realised `dollars_1lot`, only deviations
  simulated). `check` reconciles **956/956 fit and 637/637 holdout trades to the cent**.
- **Capture ceiling** `scripts/capture_mfe.py` → `output/capture_mfe_{span}.parquet`:
  per-trade MFE/MAE (bar data only — holdout-computable). Fit: realized +0.53R vs in-trade
  MFE 2.32R. Holdout: +0.52R vs 2.06R. The 2026·pre fit cell is the outlier hunting ground
  (realized +1.16R vs EOD ceiling 9.73R).
- **Mechanical controls** (fit only, holdout NOT graded — ledger discipline): canon
  $148,766 · be1r $135,449 (worse, BE kills runners — old lesson still true) · trail_1r
  $144,462 (flat) · **lock1r_2r $177,484 (+19%)** — "once +2R prints, refuse the canon exit,
  hold with stop locked at +1R". The capture gap is real and mechanically reachable on fit;
  the agent arm must beat the best MECHANICAL control, not just canon, to justify existing.

## 2. Population

All 956 fit canon trades (funded_book.load_book — wall cut applied), managed per-trade on
identical fills and stops. Segmentation reported (never averaged away): sess × era × tier ×
elite × struct_event, plus the press-signal state (+0.5R by t+3–5) from
`output/time_segments2_fit.parquet`.

## 3. Decision points (per trade, MAX 4)

1. `reached_+1R` — first minute +1R trades (before the canon exit).
2. `canon_would_exit_here` — the canon exit minute; taking it is the default.
3. `recheck_while_extended` — every 30 min after refusing the exit.

The +0.5R-by-t+3–5 press signal is IN the briefing (it is triple-era, bar-derived), so the
agent can act on the strongest known state without us hard-coding a rule.

## 4. Input tiers — the fp_minutes constraint, planned for from day one

- **Tier BAR (both spans):** bars, excursion state, geometry (VWAP SD, session range,
  path efficiency, clock), level stack, MBP-10 depth block (129 holdout day-files exist),
  journal digest. A policy learned on these is holdout-confirmable.
- **Tier FLOW (fit only):** fp_minutes CVD/delta/volume windows. Evidence from these can
  NEVER be holdout-confirmed at minute granularity.

Two agent arms run on fit: `agent_full` (BAR+FLOW) and `agent_bar` (BAR only). The gap
between them measures what flow is worth; only `agent_bar` (or a frozen mechanical distillate
expressible in BAR terms) is eligible for the holdout shot. If `agent_full` wins on fit and
`agent_bar` does not, the finding ships with the stated fit-only caveat and does NOT change
the book.

## 5. Chained structure

The deterministic briefing builder is the "reader" (bounded context by construction: it
truncates every frame at the decision minute). The trade-manager agent is the "manager" —
briefing JSON in, one verdict JSON out, no tools. Verdicts are fail-closed: missing or
malformed → the trade falls back to canon, never to a guess. Rounds expand the frontier
(`reachable_points`): decision N+1 exists only under the verdicts at decisions ≤ N.
Lookahead firewall: briefings judged in one call never share a session day.

The agent spec (`.claude/agents/trade-manager.md`) quotes OLD-canon numbers (2.14R/7.28R,
"78% of winners", old journal claims). It gets a v2 rewritten to THIS terrain before any
verdict is collected; the old text is void along with the rest of the old canon.

## 6. Metrics (per §3 rule 2)

Per-trade, same fills: capture ratio (realized R / in-trade MFE R), mean ΔR vs V8, WR, and
the funded-sizing delta (`funded_book.run`, lucid + scaled600: net, worst day, maxDD,
months green). Book totals alone are inadmissible. Every deviation from V8 carries the
verdict's rationale in the journal (rule 7: every kill attributable).

## 7. Nulls and ceilings

- **Permutation null**: any mined sub-population or threshold ("agents help on X") is
  re-scored against shuffled-outcome nulls; the best apparent lift on noise is reported
  beside the real lift.
- **Conviction shuffle**: the agent arm re-graded with verdicts randomly reassigned within
  (sess, decision-reason) strata — if the real assignment does not beat the shuffle, the
  agent is a coin with commentary.
- **Oracle ceiling** (hindsight-optimal exit per trade) is reported as CEILING only, never a
  target (rule 5).

## 8. Holdout protocol (the ledger)

Looks spent so far: 2 (time-segment state confirmation; the 25%-partial referendum), both
declared before looking. This test earns AT MOST one more: a single frozen policy —
mechanical distillate or agent_bar with frozen prompt/spec/journal — runs the 637 holdout
trades ONCE, after fit results, segment stability, and nulls are all written down. If the
fixed-R family (thread B) freezes a joint mechanical candidate first, the agent policy is
measured ON TOP of that candidate on fit before the look is spent, so holdout is never
charged twice for the same question.

## 9. Kill criteria (pre-committed)

The agent arm dies, and the capture question closes with it, if ANY of:
- fit mean ΔR vs V8 ≤ 0, or positive only via ≤3 trades (fragility test: drop top-3),
- it loses to the best mechanical control arm on fit (then the mechanical arm is the
  candidate and agents were an expensive detour),
- era-split flips sign across fit-2025 vs fit-2026,
- the conviction shuffle matches the real verdicts.

"Agents don't beat V8" is a valid, valuable outcome — it closes the capture question with
the same finality the rebuild closed the entry question (§8 of the handoff).
