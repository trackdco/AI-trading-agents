# Stage-2 review — Vault hardening before Stage 3 (Pat directive, 18 Jul)

Pat: "truly address any and all issues… it must be as close to perfect as we can get it."
Adversarial re-review of the Stage-1/2 build. Findings, each verified against engine
source, with resolutions. All fixes tested; the multi-day full-blend parity gate is the
acceptance criterion.

## Findings and resolutions

**F1 — CRITICAL: the champion's daily blend switch was missing.**
The frozen champion picks a book EVERY session (pre-open `imbal_share_20 >= 0.5` → E4
war book with ≤15-pt-stop triggers only; else E3/V8 balance book). The first Vault ran
one static config — not the champion. → Built `src/live/champion.py` (books mirroring
score_replay_arms `_books` byte-for-byte, the switch, the E4 trigger filter) and gave the
Vault a per-session `session_policy` that sets (book, cfg, trigger filter) at each roll.
Flagged: computing the vector pre-open from live bars is a Stage-8 deliverable; replay and
paper use the precomputed vector.

**F2 — CRITICAL: warmup too small → wrong targets.**
The target menu includes prior-WEEK high/low (src/engine/snapshot.py); a 2-session buffer
would compute different levels than the batch backtest → different targets/exits. The
1-day parity test had masked it by feeding both sides the same short window. → Default
warmup raised to 10 sessions; the parity gate now gives the batch side a 30-day lead-in
ON PURPOSE so any buffer-dependence fails loudly.

**F3 — phantom-trade risk on config change.**
Re-simulating past sessions under a NEW day's config could mint "new" (never-emitted)
variants of old trades. → Triggers are now SESSION-SCOPED: each re-sim sees only the
current session's triggers; warmup bars feed indicators only. Unit-tested.

**F4 — a crashing sink killed the loop.**
One Telegram exception would have halted trading. → Sink calls isolated; errors routed to
`on_sink_error`; later sinks still served. Unit-tested.

**F5 — duplicate trigger delivery.**
Live detector overlap/restart would double triggers. → Identity-keyed dedup in
`add_triggers`; re-delivery is a no-op. Unit-tested.

**F6 — performance: naive re-sim was unusable (found by running, not reading).**
Full-buffer re-sim every bar ≈ 10 s × all-day bars → hours per replay day. Three fixes:
 (a) sim runs on the CURRENT SESSION frame only (18:00 → now; every champion trade sits
     ≥ 14 h after session open) while the target resolver is built over the FULL buffer —
     multi-week levels stay exact, sim cost drops ~10×;
 (b) trim moved to session rolls (was per-bar full-buffer work);
 (c) disposal latch: after win_end, once every causal trigger is TERMINALLY disposed
     (trade, or vetoed/cancelled/skipped verdict), stop simming for the session; after
     eod_flatten always stop. **Sub-bug caught here: "taken" is a verdict status — an
     open position's trigger looked "disposed", which would have stopped simming with a
     position open and silently never emitted its exit. Excluded "taken" from terminal
     statuses; open positions keep the loop simming until they close.**

**F7 — known limitation (deferred, documented): no entry-time event.**
TradeEvents surface when a trade COMPLETES (entry+exit together) — P&L-correct for paper
parity, but a live entry alert can't fire at fill time. Needs a small engine kwarg to
expose the open position; deferred to Stage 5 (Telegram) and noted in the build plan.
The Vault's per-bar cadence already supports it once the engine exposes the state.

## Acceptance
- 17 unit tests green (loop semantics incl. every finding above), full suite green.
- 1-day full-blend parity: MATCH (E3 book day, trades/fills/dollars identical to batch).
- 5-day full-blend parity gate (both books, batch 30-day lead-in vs stream default
  buffer): run via `python -m scripts.parity_check` — the standing Stage-7 gate; must be
  re-run after ANY change to the Vault, champion config, or engine.
