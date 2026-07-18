# Trade-Journal Schema Freeze — PROPOSAL

**Status: PROPOSED — awaiting engine-lane + Angus ratification.** Once ratified,
`src/desk/journal.py` `SCHEMA_VERSION` drops the `-proposed` suffix and changes go
through the normal gate. This is Pat's lane (Hermes reporting duty, pass-24
directive `docs/TASK-FOR-PAT-trade-journal-agent.md`) and closes the
`docs/REGIME-ADAPTATION-DESIGN.md` prerequisite #2 ("journal schema freeze —
mid-replay schema churn poisons the experiment").

## Why this is a freeze, not a preference

The journal is the shared contract of three consumers: the backtester's per-trade
output, the walk-forward replay's memory, and (later) the live execution feed.
Today **two emitters have already drifted:**

- the engine's `TradeRecord` (`src/backtest/engine.py`) — 24 fields, full price detail
- the condensed `output/journal_champion.csv` — abbreviated names, extra features
  (`align_votes`, `pre930`, `risk_pts`, `hold_min`, `win`) that `TradeRecord` lacks

`JournalRecord` (`src/desk/journal.py`, 51 fields, `extra='forbid'`) is the union
the task doc demands ("extend, don't trim"), organized into the task's sections:
identity · setup · execution · path · outcome · desk-context · review. It
**extends** `TradeRecord` via `from_trade_record()`, it does not replace it.

## What the engine lane must ADD (from `coverage_report()`)

Run `coverage_report(list(TradeRecord.model_fields))` — the current gaps:

| Section | Missing fields the freeze requires |
|---|---|
| identity | `config_hash` (reproducibility stamp — already in the Hermes design) |
| setup | `cluster_types`, `cluster_center`, `vwap_touched`, `day_type`, `session`, `news_context` |
| execution | `rr_at_entry` |
| path | `mfe_r`, `mae_r`, `time_to_mfe_min`, `partial_fills`, `trail_moves`, `be_armed` |
| review | `angus_verdict`, `would_angus_take` (Angus-filled / capture-matcher-prefilled) |

Note: `mfe_r`/`mae_r`/`hold_min`/`align_votes` already exist in the champion
journal and in diag22 — they just need to flow into the unified writer.

## Name reconciliation the freeze locks (champion journal → frozen)

The condensed journal's abbreviations map to the frozen names as follows — this
map is the freeze's other half (so `branch` and `entry_variant` can never be
mistaken for two different things again):

| champion CSV | frozen field |
|---|---|
| `month` + `day` | `trade_date` (derive) |
| `branch` | `entry_variant` |
| `dir` | `direction` |
| `conf` | `confluence_count` |
| `htf` | `htf_flag` |
| `vwap_touch` | `vwap_touched` |
| `pre930` | `pre_930` |
| `fill` | `fill_ts` |
| `exit` | `exit_price` |

## Desk context is part of the record (new, from the agents)

Now that the regime + HTF agents gate the engine, the journal must capture WHY a
trade was allowed — the adaptation experiment's memory needs it:
`regime_verdict`, `htf_verdict`, `gates_applied`, `size_multiplier_applied`.
These are OPTIONAL: a pre-agent backtest row leaves them null; an agent-gated
replay row fills them. This is what lets the three-arm replay attribute a P&L
delta to a specific gate.

## Ratification checklist (who signs what)

- [x] **Engine lane:** confirm the ADD list above is emittable from the
      backtester + diag22, and adopt `from_trade_record()` as the writer path
      (extend `TradeRecord`, don't fork it). **SIGNED — see verification below.**
- [x] **Engine lane:** adopt the name-reconciliation map for the condensed
      journal. **SIGNED** (map adopted; retire-vs-keep of the abbreviated CSV is
      deferred to when the frozen writer is wired — the CSV's producer is not
      engine-lane's file to delete).
- [ ] **Angus:** confirm the review fields (`angus_verdict`, `would_angus_take`)
      are the slots he wants for "give me the data and I'll say where to improve."
- [ ] On sign-off: drop `-proposed` from `SCHEMA_VERSION`; every journal row
      thereafter stamps it, and the replay may start (churn now = a gated change).

## Engine-lane verification (2026-07-18, Brake's lane — per-field emittability)

Checked against `src/backtest/engine.py` (TradeRecord/_Pos/simulate),
`src/engine/triggers.py` (Trigger), and existing scripts. `coverage_report()`
re-run this date: 25/55 emitted, gap list identical to the ADD table above.

| Field | Emittable? | Source of truth |
|---|---|---|
| `config_hash` | YES (trivial) | sha256 of `config/strategy.yaml` at `load_backtest_config()`; VALUE becomes stable when the champion freeze (prereq #1) lands — field emittable today with whatever config ran |
| `cluster_types` | YES (copy-through) | already on `Trigger` (triggers.py:86); order holds the Trigger → copy into TradeRecord at close |
| `cluster_center` | YES (copy-through) | `Trigger.cluster_center` (triggers.py:84) |
| `vwap_touched` | YES (copy-through) | `Trigger.vwap_touched` (triggers.py:89) |
| `day_type` | YES (writer join) | not computed inside `simulate()` — joined per `trade_date` from `scripts/build_regime_vector.py` output (pre-open classification, no lookahead). Emitted by the `from_trade_record()` writer path, not the simulator |
| `session` | YES (derive) | from `fill_ts` vs §2 session boxes (pure function of an emitted field) |
| `news_context` | YES (calendar join) | nearest release ± window from the news calendar at `fill_ts`; **quality caveat:** rides on the Feb-only calendar until the Feb–Jul `news_archive.csv` (Brake task #5) lands |
| `rr_at_entry` | YES (record-at-place) | engine already computes `reward / risk` for the §6.5 floor veto at order placement — record instead of discarding |
| `mfe_r` / `mae_r` / `time_to_mfe_min` | YES (path pass) | computable from 1m bars between `fill_ts` and `exit_ts` (precedent: the MFE giveback study + diag22); writer post-pass, or an in-`simulate` tracker later — same numbers either way on 1m granularity |
| `partial_fills` | YES (trivial) | `len(_Pos.legs) - 1` (engine.py:226) |
| `trail_moves` | YES (small addition) | count `pending_stop` reassignments in V8/V9 management — needs a per-position counter (a few lines), no design change |
| `be_armed` | YES (trivial) | `_Pos.be_done` (engine.py:224) |
| `angus_verdict` / `would_angus_take` | YES as NULLABLE | engine emits null; filled by Angus / the capture-matcher — schema must keep them Optional |

**Name note:** TradeRecord's `confluence` maps to frozen `confluence_count`
(`coverage_report` shows zero `unknown_emitted`, so `from_trade_record()`
already reconciles it) — flagged only so nobody "fixes" the difference twice.

**Net verdict: every ADD-list field is emittable; none requires a rule change or
schema redesign. The one true engine addition is the `trail_moves` counter.**
Awaiting Angus's review-slot confirmation to drop `-proposed`.

## What is NOT decided here

The champion CONFIG itself (Blend v1.1) and its hash are the engine lane +
Angus's to freeze (Stage-1 prerequisite #1/#3) — this schema just reserves
`config_hash` to hold whatever they freeze. Deliverables #2 (`journal build`
entrypoint) and #3 (summary-view generator) from the task doc follow once the
schema is ratified.
