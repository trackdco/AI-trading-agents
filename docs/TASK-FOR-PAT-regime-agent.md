# TASK FOR PAT — Regime-Context Agent (Angus directive, 18 Jul 2026)

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
