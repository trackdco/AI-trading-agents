# SPEC — the adaptive journal (Angus, 27 Jul)

**The ask, verbatim intent:** journal *everything* — trades taken, trades NOT taken and what
they would have done, session summaries — so the agents can build a learning curve and
eventually earn discretion. His worked example: *"this trade is firing at 9:55, we have 4+
confluences but delta is a net negative from 9:40-10 whereas it's extremely profitable from
10:15, so maybe I will de-risk."*

That example is the acceptance test for this spec. Answering it needs three things the
journal does not currently hold together: the candidate that fired (taken or not), the flow
state of the *time bucket* it fired in, and what actually happened next.

**Standing ruling this does NOT touch:** `docs/RULING-mechanical-only.md` — no agent
discretion in the trade path while the engine is profitable. This spec builds the evidence
base for a later discretion project. It changes no trading behaviour.

---

## 1. What is already captured

### Live (production, per `src/live/journal.py` + `src/live/route_b.py`)

| sink | holds |
|---|---|
| `journal.jsonl` | one frozen `JournalRecord` per COMPLETED trade (51 fields, engine-parity) |
| `decisions.jsonl` | session picks, halts, rolls, guard trips, notes, stale-verdict skips |
| `rejects.jsonl` | every **execution-boundary** rejection, normalized (`RejectLedger`) — spine rules, spread guard, `dd_ramp_zero`, `feed_stale`, `book_crossed`, `duplicate` |
| `sizing.jsonl` | per-trade conviction / stop_pts / micros / available_dd (gate B5) |
| `spine.jsonl` | all-guards fired/not-fired report + shadow decision |
| `order_watch.jsonl`, `exit_exec.jsonl` | order lifecycle and exit resolution |

### Offline (backtest)

`output/canon_book.parquet` is far richer than the live trail: it holds the **whole candidate
universe**, not just fills — 713 rows over 252 days, 264 taken and 449 rejected — with every
check result (`W/F/Tp/G/C`, `D/Tc/X/AGE/PAQ`), every Q bit, ladder state, and the
counterfactual `dollars` each rejected candidate would have produced.

## 2. The gaps

**G1 — no rejection attribution.** *(CLOSED 27 Jul — `scripts/canon_attribution.py`)*
The book recorded that a candidate was skipped, never which layer skipped it. Now derived
post-hoc and self-validating: it re-walks the ladder and refuses to report if its re-derived
`size` disagrees with the committed book. First readout, fit window:

| layer | n | counterfactual $ (1-lot) | WR |
|---|---|---|---|
| `score_le_2` | 296 | −62,399 | 12% |
| `gold_Q_le_1` | 25 | −4,036 | 28% |
| `nth_needs_4` | 99 | −6,269 | 32% |
| `day_escalation` | 24 | −1,590 | 29% |
| `day_stop_400` | 5 | **+488** | 40% |
| taken | 264 | +49,277 | 46% |

Every layer is dollar-negative on what it skipped — i.e. earning its place — except the
−$400 day stop, which on 5 trades left money behind. n=5 is far too small to act on; it goes
on the holdout list, not into a change.

**G2 — the live path journals no candidate it did not take.** Production computes the same
universe and discards the rejects silently. A live day therefore cannot be compared with a
backtest day on anything except fills, and the learning substrate stops accumulating the
moment the bot goes live. **This is the single most important gap for Angus's ask.**

**G3 — no counterfactual resolution live.** Offline, `dollars` for a rejected candidate comes
from the simulator. Live, nothing replays what a skipped setup would have done.

**G4 — no session summary artifact.** `output/regime_vector.csv` holds pre-open features;
nothing records how the session actually *went* (realized range, volume, CVD trajectory,
delta by time bucket, where the day's extremes formed). Angus's 09:40-10:00 vs 10:15 question
is a **time-bucketed flow** question and cannot be answered from per-trade rows alone.

**G5 — no per-trade linkage to the flow bucket it fired in.** Even with G4, a trade needs to
carry a key into its bucket for the join to be trivial.

## 3. Proposed shape

### Tier 1 — `candidates.jsonl` (closes G2)

One row per trigger that reaches the scorer, taken **or not**, written live at decision time.
Superset of the verdict row:

- identity: `day`, `session`, `window` (pre/gold/london), `fill_ts`, `fillhm`, `direction`,
  `pattern`, `setup_id`
- every check individually, not just the total: `W/F/Tp/G/C` or `D/Tc/X/AGE/PAQ`, `score`
- every Q bit: `WALLSZ/BIGFD/T2/TRIG/VWAPD/LONSLOPE`, `Q`
- ladder trace: `size_after_ladder`, `size_after_Q`, `size_final`, and **`rejected_by`**
- economics: `conviction`, `risk_pts`, `micros`, `available_dd`
- the full feature vector at decision time (the `trade_matrix` columns), so a later question
  about a feature nobody thought to keep is answerable without a re-pull
- `bucket_key` (G5) — `day` + 15-min bucket of the fill

Discipline: **write-only, fail-soft, never read back into a decision.** Same contract as
`journal.jsonl` — a full disk cannot raise into the trading loop.

### Tier 2 — EOD counterfactual resolver (closes G3)

After the session, replay every non-taken candidate against the day's bars under the canon's
own managed-exit rules and record what it *would* have done: `cf_mfe_r`, `cf_mae_r`,
`cf_exit_reason`, `cf_dollars`. Runs **out of the trade path**, on stored bars, never live.
Emits `counterfactuals.jsonl` keyed to the candidate row.

This is what converts a reject log into a learning signal. Without it a rejected candidate is
an opinion; with it, it is a scored prediction.

### Tier 3 — `sessions.jsonl` (closes G4)

One row per session per day. Per Angus's example the flow fields must be **bucketed**, not
daily aggregates:

- character: realized range, volume, VWAP path, value area, open type, gap
- flow: CVD trajectory and **signed delta per 15-min bucket** across 08:00-11:00 and the
  London window; absorption/exhaustion counts
- structure: overnight high/low and when they were taken, session extremes and their times
- context: news events with times and impact, contract roll state, DST flag
- canon activity: triggers fired, candidates scored, taken, rejected by reason, P&L

### Tier 4 — agent decision provenance (later, gated on discretion)

When agents eventually act: the verdict, the evidence cited, the counterfactual grade, and
whether a standing rule was formed / paid / retired. Deliberately last — worthless until
Tiers 1-3 have accumulated.

## 4. Sequencing — and why nothing ships into the live path today

`docs/PROMOTION-GATE.md` §E: any change to canon / sizer / spine / relay is stop-and-review
plus full re-certification. The arming check refuses if HEAD differs from the certified
commit by anything except `config/arming.yaml`. **A journaling change inside the live loop is
a live-path change**, however write-only it is.

So:

| # | what | where | when |
|---|---|---|---|
| 1 | rejection attribution | offline only | **DONE** — `scripts/canon_attribution.py` |
| 2 | apply attribution to the 2023/24 holdout | offline | with the holdout scoring |
| 3 | `sessions.jsonl` builder from stored bars/tape | offline | any time — no live path |
| 4 | `candidates.jsonl` in the live loop | **live** | **after arming**, own certification |
| 5 | EOD counterfactual resolver | offline, reads live logs | after 4 |
| 6 | agent provenance | desk | after discretion is ruled on |

Items 1-3 and 5 never touch the trade path. Only item 4 does, and it waits.

## 5. Open decisions for Angus

1. ~~**The C1/C2 contract.**~~ **RULED 2026-07-27 — see `docs/RULING-agent-outcome-visibility.md`.**
   Agents may SEE outcomes, P&L and counterfactuals, for learning only; they may not ACT on
   them until Angus judges they beat the mechanical baseline. Tier 2 is authorized. One
   engineering condition attaches: every outcome record carries a `resolved_ts` and the
   briefing builder filters on it, so an agent reasoning about day D can never see an
   outcome resolved at or after its own decision time. Learning from the past is the point;
   reading your own answers is the failure mode, and in a walk-forward run it would look
   like brilliance.
2. **Retention.** The full feature vector per candidate is ~95 columns × ~3 candidates/day.
   Trivial for years. Confirm we keep everything rather than a curated subset — the whole
   point is that the question nobody anticipated is answerable later.
3. **Does a rejected candidate consume a slot?** Today Layer 2b counts only taken trades as
   `nth`. If discretion later un-rejects something, that ordering changes. Worth pinning the
   semantics now, while it is free.
