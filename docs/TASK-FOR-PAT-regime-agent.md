# TASK FOR PAT — Regime-Context Agent (Angus directive, 18 Jul 2026)

## ANGUS DIRECTIVE (18 Jul) — TWO-TIER TESTING PROTOCOL (speed without breaking the chain)

Angus's concern: 30s/verdict × one-day-at-a-time = the walk feels like "multiple
days." Real math: 890 sessions × 30s ≈ 7.4h — one arm of the full walk is ONE
overnight. But iteration must be much faster than exams. Protocol:

1. **Two tiers, already supported by your own driver modes.**
   - **Tier 1 — ITERATION (parallel mode, minutes/month):** prompt/briefing tweaks
     get graded on reads over one month in parallel mode (each day seeded from a
     compacted note snapshot). ~20 concurrent calls ≈ wall-clock of ONE verdict.
     Fail fast here; most candidate changes die here cheaply.
   - **Tier 2 — EXAMS (sequential mode, overnight):** only survivors of Tier 1 get
     a chained run (Q2 2025, the Long Walk). Chaining is the EXPERIMENT there —
     never approximate it in an exam.
2. **Within a day, everything runs concurrently.** Incumbent, fresh-eyes, HTF are
   mutually independent given the same briefing — a 3-agent panel costs the same
   30s as one agent. Serial-per-day ≠ serial-per-agent.
3. **Across arms, chains are independent** — every arm/variant runs concurrently.
   N arms cost one arm's wall-clock.
4. **Per-call latency diet:** (a) enable prompt caching — system prompt + standing
   rules + digest are byte-stable day to day; only the daily block changes;
   (b) briefing diet — trailing_sessions raw OHLC dumps can shrink to the derived
   stats + retrieval tables (A1/base-rates carry more signal in fewer tokens);
   (c) rationale caps stay (already fixed v0.3.0).
5. **Checkpoint/resume (gate G6) makes long runs restartable, and journaled
   verdicts are a cache** — a re-run after a non-agent change (scoring, harness)
   replays from the journal at zero agent cost.

## ANGUS DIRECTIVE (18 Jul, latest) — the C2 feedback contract is DOLLARS, not wins

Confirmed tonight by reading the briefing keys: the agent receives NO outcome
feedback in any currency — not dollars, not binary. It has never been told how a
verdict turned out. Meanwhile the edge is magnitude-skewed (top 10% of trading
days carry 35% of all oracle P&L; top 20% carry 52%; median green day $370 vs
biggest $4,480), so even binary win/loss feedback would mis-train it: at ~45% day
win rate with that skew, loss-dodging looks good in counts and is ruinous in
dollars. Measured bill, Mar–Jun (scripts/score_sizing.py, standing instrument):
cost $10,042 on shrunk winners vs $6,232 saved on shrunk losers; avg size 0.57 on
eventual winners vs 0.49 on eventual losers — a flat tax, not insurance.

**UPDATE (Angus go, 18 Jul): the draft code for all three wires is COMMITTED —
`src/desk/briefing_v05.py`** (opt-in module, nothing imports it by default; your
in-flight v0.4 run is untouched). `upgrade_briefing()` = W2, `feedback_block()` =
W1 (implements the contract below exactly — smoke-tested on real June days),
`V05_SIZE_NOTCHES` + `V05_PROMPT_ADDENDUM` = W3. Two calls in the driver + the
prompt splice and v0.5 is running. Publish on Angus's word once v0.4 results are
reviewed.

**Contract for the sequential driver — append to every morning briefing:**

```json
"yesterday_result": {
  "your_size": 0.5, "realized_usd": +410,
  "full_size_counterfactual_usd": +820, "oracle_usd": +1650,
  "sizing_regret_usd": -410,            // realized - full_size counterfactual
  "read_regret_usd": -1240              // realized - oracle (read + sizing)
},
"rolling_20d": {
  "your_cumulative_regret_usd": -3810,
  "your_arm_expectancy_usd": +85,       // B4 health input
  "champion_expectancy_usd": +170
}
```

Rules: DOLLARS everywhere (Angus: the agent cannot live in a world where shrunk
winners cost nothing); single-day numbers always paired with the rolling-20d
line so one loud day can't whipsaw the frame (the anti-overreaction damper);
regret is charged against the agent's own verdict, mechanically, no agent turn
spent computing it. The base-rates digest (output/base_rates.json,
scripts/build_base_rates.py --asof for replays) supplies the PRE-verdict
magnitude context; this block supplies the POST-verdict charge. Grade v0.4+ on
score_sizing.py discrimination (size_winners − size_losers) moving above +0.10
alongside the read metrics.

All replay metric readouts go to ANGUS for trading interpretation before
conclusions get drawn from them. Report raw numbers (reads, capture, arm deltas,
per-day tables) without narrative verdicts — Angus judges what the tape context
meant. He caught the June "worst month yet" framing being partly a scoring
artifact within minutes of seeing it; that review loop is now standing process.
See also docs/LONG-WALK-2023-2026.md — the full-history adaptive replay Angus has
queued, with launch gates G3–G6 in your lane.

## ANGUS DIRECTIVE (18 Jul, evening) — PARALLELIZE THE DESK + fresh-eyes panel

Angus, verbatim intent: why is ONE agent grinding these replays when eight are set
up? Sequential chaining is serial *within* a chain by design — but nothing else is:

1. **Independent arms are independent chains — run them concurrently.** Arm A vs
   arm B, prompt variants, the {0,0.25,0.5,0.75,1.0} sizing split-test: each is its
   own sealed chain with its own notes. One worker per arm, same wall-clock as one.
2. **Different exam months/quarters fan out the same way** (chains don't cross
   month-boundary in the current design beyond inherited notes — seed each from the
   prior month's closing note snapshot and run all months at once per arm).
3. **PER-DAY FRESH-EYES PANEL — this is also the frame lock-in fix.** Your June
   finding (early war framing entrenched through a rotation-rich stretch; chaining
   strengthened while accuracy fell) has the same cure as Angus's parallelism
   demand: each day, alongside the incumbent chained agent, a SECOND agent with NO
   inherited notes (briefing only) renders an independent verdict. Agreement =
   proceed; disagreement = flag in the journal and score both. The chained mind
   gets memory, the fresh mind is immune to folklore — divergence between them IS
   the lock-in detector, measured daily instead of discovered post-month.
4. **Scorecard + regret lines (C1/C2) compute mechanically after each day** — no
   agent turn needed; don't spend one on it.

## SCORING RULE CHANGE (Angus ruling, 18 Jul): $0 best-book days are FLAT

A day where the best book made $0 on no trades now counts oracle=FLAT
(score_regime_reads.py + analog table updated; an agent sitting out a nothing-day
is not a miss). Restated under the new rule: Mar 48%, Apr 38%, May 45%, **Jun 38%
(not 24%)** — and June's binary trade/no-trade is **71%, the best month on record**
(TRADE precision 85%). June's true failure is 3-way book confusion
(momentum-called-rotation), not the on/off switch. Update your ledger lines
accordingly before quoting June as "worst month yet."

**Assigned by Angus** (pass 14, out-of-sample review). Read this first, then
`context/progress-tracker.md` passes 11–14, then `docs/agent-blueprint.md` (your Phase-3
design — this agent slots into that framework).

## Why this exists (the March evidence)

Champion v2 (the best NY-morning config: +$11,442 in Feb, 36.4% win, 8.4× P&L/DD) lost
**−$4,430 in March at an 8% win rate**. The forensics (tracker pass 14) show:

- Entries were locally CORRECT — the median March loser ran **+1.33R in profit** before
  dying; 22 of 33 losers reached +1R. The tape then resumed the war trend and steamrolled
  the reversion.
- **No exit policy fixes it** (V1/V7 variants measured: best case still −$3.2k). The few
  big winners fund everything; capping them pays for the loser conversions almost exactly.
- Vol inside the trading window was NEAR-NORMAL (median 1m range 16.8 vs Feb 13.8) — a
  pure price-based vol filter would NOT have caught this. The difference was the REGIME:
  a shooting war (US strikes on Iran), relentless directional tape, headline shocks
  (Mar 23 ceasefire tweet: +408pts in one minute — see the shock scanner, pass 14).

Angus: *"If you had two brain cells you'd know it was going to dump the entire month…
we were looking to fade a war. There was no world where we should have traded how we did."*

## The mandate

Build the **regime-context agent**: an agent that reads MACRO/NARRATIVE CONTEXT (not
price alone) and emits a daily (and intraday-updatable) REGIME VERDICT that gates the
mechanical engine. Target output contract (strawman — refine against your blueprint):

```json
{
  "date": "2026-03-23",
  "regime": "war_risk_off",        // e.g. normal_rotation | trending_macro | war_risk_off | event_paralysis
  "directional_bias": "short",      // long | short | neutral
  "permitted_structures": ["continuation"],   // continuation | reversion | none
  "size_multiplier": 0.5,           // 0 = stand down entirely
  "rationale": "US-Iran open hostilities; indices in persistent risk-off trend; ceasefire headline risk extreme",
  "sources": ["..."]
}
```

Engine integration (coordinate with the engine lane): the Vault consumes this like the
existing condition-based de-risks (day/time). E.g. `war_risk_off` ⇒ no counter-trend
entries, no fades against the bias, half-or-zero size. March replayed under this gate is
the acceptance test: the agent (using ONLY information available each morning) should have
kept the engine flat-to-short-continuation through March.

## Inputs available in-repo

- `config/news_calendar.csv` — scheduled releases + speeches (Trump/Powell rows tagged).
- The shock-bar scanner (pass 14, tracker) — unscheduled headline detection from price.
- `data/reference/nq_1m_feb_jul2026.parquet` — full Feb–Jul data for backtesting the verdicts.
- Whatever news/context sources you wire for Phase 3 (this agent is the natural first
  consumer; hermes/atlas lanes in your blueprint are the fit — your call).

## Hard constraints (non-negotiable, per ai-workflow-rules)

1. **The agent NEVER sees engine P&L or trade outcomes** — context in, verdict out.
   (System proposes, human disposes; no outcome-feedback loops.)
2. Verdicts must be reproducible from timestamped inputs (no hindsight: the Mar 23 verdict
   may only use information published before Mar 23's session).
3. Rule changes stemming from this go through Angus + out-of-sample, as always.
4. Shadow mode first (Phase-5 ledger design in your blueprint) before it gates real sims.

## Acceptance criteria

- [ ] Daily regime verdicts for Feb 2 – Jul 15 2026, generated no-hindsight.
- [ ] March replay: engine gated by the verdicts turns March's −$4,430 into ≥ flat
      WITHOUT degrading February by more than ~10% (no regime-fitting to March alone).
- [ ] April–July verdicts produced BEFORE looking at April–July engine results (they are
      the true out-of-sample for the agent itself — coordinate with the engine lane).
- [ ] Documented in the blueprint structure + tests per code-standards.

— Claude Code (engine lane), on Angus's direction. Questions → Angus's chat or the tracker.

---

# ASSIGNMENT #2 — HTF-Structure Agent (Angus + Brake directive, same session)

**Insight (Angus/Brake):** his LTF "reversals" are usually HTF continuations — reversal
entries are only taken when the 4H/daily structure supports the direction. The engine has
NO 4H/daily view (only the 15m flag) — it happily fades entire trends.

**Measured evidence (pass 15, no-hindsight structure reads on champion trades):**

| entry vs 4H swing leg | FEB (daily = RANGE) | MAR (daily = war TREND) |
|---|---|---|
| AGAINST the 4H leg | **64% win, +$7,455** (74% of the month) | 10% win, −$1,692 |
| WITH the 4H leg | 17% win, −$382 | 6% win, −$1,485 |

**The signal is conditional, not absolute:** fading the 4H leg is the money trade when the
leg is a ROTATION inside a contained daily range (Feb), and fatal when the leg is a segment
of a genuine higher trend (Mar). Mechanical k=2 swing detection got the daily call wrong in
March (whipsaw) — the nesting judgment is the agent's job.

**Mandate:** per day (intraday-updatable), classify the nested structure and emit:
```json
{"date": "...", "daily_context": "range|trend_up|trend_down|unknown",
 "h4_leg": "up|down|range", "fade_permitted": true, "continuation_only": false,
 "rationale": "...", "sources": ["price structure 4H/daily; regime agent verdict"]}
```
Interlocks with Assignment #1 (war regime ⇒ legs are trend segments ⇒ fades off).

**Acceptance:** no-hindsight daily calls Feb 2 → Jul 15 that (a) preserve ≥90% of Feb's
AGAINST-4H profit, (b) block/de-risk March's fades, (c) hold up on Apr–Jul which the agent
must NOT have seen while being designed. Beat the mechanical baseline above or explain why.

**Data note:** structure reads are starving — dataset starts Feb 1 (no January or earlier).
The long-pending Jan-1 re-pull (P4.9, Brake) materially improves daily/weekly structure
quality; older history better still.

---

## GREENLIGHT UPDATE (Angus, 18 Jul 2026, pass 29) — BUILD, don't just scaffold

Angus ruling: agents move from scaffold-only to ACTIVE BUILD, targeting the walk-forward
replay experiment (not live trading — live stays gated behind validation):

1. **Regime-context agent** (this doc) — priority #1. Tonight's data made its mandate
   precise: regime resolution is the single biggest P&L lever. Mechanical index (trailing
   imbalanced-day share, committed in output/amt_daytypes.csv) is the baseline it must beat.
   Its output decides: reversal-set vs continuation-set vs stand-down, per day.
2. **Historical-analog module ("how good is this setup, historically?")** — Angus spec via
   his Malaysia contact's bot: given a candidate trade's feature vector (pattern, regime,
   day-type, alignment votes, risk geometry, hour — the journal schema), look up the K most
   similar historical setups and return the empirical win-rate / R-distribution → confidence
   + sizing input. NOTE: the CORE of this is mechanical (k-NN over the journal — engine lane
   can build the lookup); the AGENT wraps judgment around it (why this analog set does/doesn't
   apply today). Data need: multi-year 1m NQ history to deepen the analog library (cheap;
   Angus approved buying data as needed).
3. **Walk-forward adaptive replay** (the "Monte Carlo with adapting agents" Angus wants):
   replay Feb→Jul day by day; agents receive the journal-so-far; they may adjust their OWN
   playbook notes (adaptation journaled per Hermes mandate) — no human sign-off DURING the
   sim (Angus ruling); the STATIC champion runs as control. Deliverable: adaptive-vs-static
   P&L + a log of every adaptation and whether it paid. Cost note: thousands of LLM calls,
   fine as a one-off. 2026 data is past model cutoffs (no memorized-headline cheating).

Engine lane provides: journal schema + champion configs (output/journal_champion.csv is the
live example), trigger caches, simulate() as the fill engine. Ping when scaffolds are up.

## Design note for the FULL replay (engine lane, pass 33): playbook-note compaction

The 3-day pilot's playbook notes are excellent — and at ~750 replay days they will outgrow
any context window by month 4. Before the full run, give the notes a rolling structure:
- last N days of notes verbatim (recent memory),
- older notes DISTILLED into standing rules (each rule carries: born-date, evidence count,
  last-confirmed date),
- standing rules are themselves reviewable/retirable by the agent (retirements journaled
  like any adaptation — the unlearning is data too).
Every distillation pass is journaled so the adaptation ledger can still trace any rule back
to the raw notes that spawned it.
