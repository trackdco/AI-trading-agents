# Ambient trade-instrumentation — interpretation choices (for Angus to veto)

**Context.** The 24 Jul CANON ruling (`docs/FOR-ANGUS-desk-spec-questions.md` §RULING)
froze engine/detector behavior and made three things additive-only:

1. journal **sweep state** (Q-30 veto DROPPED),
2. journal **spread-at-fill** + add a mechanical **order-time spread guard** (Q-31),
3. journal **news-calendar state** (Q-33 buffer DROPPED).

The ruling said WHAT to record, not HOW to compute each value. This file lists every place
the text left something open and the choice I made. **Nothing here gates or resizes a
trade** except the spread guard (C-8..C-11), which the ruling explicitly moved to Python at
order time. Everything is additive; frozen behavior is untouched. Veto any line and it is a
localized change — the field definitions live in `src/live/ambient.py`, the guard in
`src/live/spread_guard.py`, the schema in `src/desk/journal.py`.

Code: `src/live/ambient.py`, `src/live/spread_guard.py`. Tests: `tests/test_ambient.py`,
`tests/test_spread_guard.py`, plus guard-trip integration in `tests/test_live_vault.py`.

---

## A. Where the fields live (schema + wiring)

- **C-0 — additive, optional, null by default.** The three fields are added to the *frozen*
  `JournalRecord` as `str|None` / `float|None`, defaulting to `None`. Pre-ruling rows still
  validate; the Stage-7 reconcile keys (date, fill, direction, points, dollars) are
  untouched, so parity is unaffected. *Alternative: a new v1.1 schema bump — rejected as
  heavier than the ruling needs.*
- **C-1 — journal on by default, guard off by default (in the runner).** Ambient context is
  computed and journaled for **every** live trade (the ruling's "journal EVERYTHING"). The
  order-time spread **guard is opt-in** (`LiveRunner(spread_guard=…)`, default `None`),
  because a guard trip drops an order and would make live diverge from the validated
  backtest — arming it is an operator decision. **Veto candidate:** if you want the guard
  armed in paper trading by default, say so and I flip the default (and pick a `mult`).

---

## B. news_calendar_state (Q-33)

- **C-2 — only `impact == high` counts as "news."** Medium/low/holiday rows are ignored.
  Rationale: the retired `lumen.NO_IMMINENT_NEWS` rule and Helios check 7 were both
  high-impact-only. *Veto: include `medium`.*
- **C-3 — encoding = `"{event}:T{±min}"`, signed minutes to the NEAREST high-impact
  release.** `T-15` = 15 min BEFORE the release (upcoming), `T+8` = 8 min AFTER. "Nearest"
  = smallest absolute distance, so the field can point forward or backward. `"none"` when no
  high-impact event exists / no calendar. Rationale: keeps the raw signed distance for later
  analysis rather than pre-bucketing (e.g. "within 60 min"), which would itself need a
  ruling. *Veto: bucket instead, or report only forward-looking distance.*
- **C-4 — tz-naive timestamps are assumed ET,** matching the engine's native tz and
  `load_news_calendar` (which localizes `datetime_ET` to ET). No UTC guessing.

## C. spread_at_fill + the guard (Q-31)

- **C-5 — the live `Bar` feed is OHLCV-only, so the default spread proxy is the fill bar's
  `high - low` range, in points.** There is no bid/ask in the minute bars the champion runs
  on. **This is a volatility/range proxy, not a true top-of-book spread.** The code takes a
  pluggable `spread_fn`, so the moment a quote feed is wired (the MBP-10 `condensed_*.csv`
  already carry `bid_px_00`/`ask_px_00`), a real spread overrides the proxy with no other
  change. **Biggest veto candidate** — flagged loudly: if you'd rather journal `None` until
  a real quote source exists than record a range proxy, say so.
- **C-6 — the fill bar is the exact `ts_event` match, else the last bar at-or-before the
  fill timestamp.** Fills land on bar closes in this engine, so exact match is the norm; the
  fallback covers timestamp-label edge cases.
- **C-7 — the guard's baseline window is the ≤30 bars STRICTLY BEFORE the fill, same session
  only.** No look-ahead past the fill; prior-session bars excluded so a session roll can't
  contaminate the baseline. *Veto: different window length or cross-session baseline.*
- **C-8 — the guard threshold is RELATIVE: `mult × median(recent spreads)`, default
  `mult = 3.0`.** Median (not mean) so one wide bar can't inflate its own baseline. This is
  the ruling's explicit "relative, never a frozen absolute" (London 2026 regime shift).
  **`mult = 3.0` is a guess** — no calibration exists for it yet. *Veto / set the number.*
- **C-9 — the guard fails OPEN.** Fewer than `min_obs = 5` baseline bars, or an unmeasurable
  fill spread → the order is PLACED (reason `insufficient_history` / `no_spread_data`). An
  untested block is exactly what the ruling warns degrades a validated book, so the guard
  only ever trips against a real, sufficiently-sampled local baseline. *Veto: fail closed.*
- **C-10 — trip test is STRICTLY greater-than** (`spread > threshold`); exactly-at-threshold
  passes.
- **C-11 — a guard trip = no order placed, journaled as a `guard_trip` DECISION line**
  (`decisions.jsonl`), never a trade row in `journal.jsonl`. A tripped order is not a taken
  trade, so keeping it out of the trade journal is what preserves the reconcile. The
  decision line carries the spread, baseline, threshold, reason, and the sweep/news context.

## D. sweep_state (Q-30)

- **C-12 — proxy for the retired `hydra.POOL_SWEPT` + `ENTRY_AFTER_GRAB` pair.** The engine
  does not stamp a `swept` flag (that was I-9, never built), so this is computed from the
  bar buffer, not read from a first-class engine signal. *Veto: wait for a real engine-
  stamped sweep flag instead of a proxy.*
- **C-13 — the "pool" = the IMMEDIATELY-PRIOR session's extreme** relevant to the trade
  direction: prior-session **low** for longs (sell-side liquidity), prior-session **high**
  for shorts (buy-side). Rationale: prior-day liquidity is the classic stop-run pool and is
  self-contained (no dependency on the engine's level menu). *Veto: use a different pool —
  session/premarket extreme, a specific level-menu entry, etc.*
- **C-14 — states: `swept_before_entry` / `swept_after_entry` / `no_sweep` / `unknown`.**
  "Swept" = a wick pierced the pool (`low < pool` for longs, `high > pool` for shorts).
  `before`/`after` are relative to the fill bar — `swept_before_entry` is the sequence
  hydra required to PASS. `unknown` = no prior session in the buffer or insufficient data.
  *Veto: require a reclaim (close back through) rather than just a wick piercing.*

## E. Fail-soft (engineering, not strategy)

- **C-15 — all instrumentation is fail-soft.** Any error computing a field yields
  `None`/`"unknown"` for that field alone and never raises into the trading loop — same
  discipline as the existing journal/sink isolation. Not a strategy choice; noted for
  completeness.
