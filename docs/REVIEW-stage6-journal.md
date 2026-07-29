# Stage-6 review — live journal (Pat directive, 19 Jul)

Same adversarial treatment as the Stage-2 and Stage-3/4 reviews: probe the failure
scenarios, fix what breaks, regression-test every finding. Two real bugs (one proven
live by probe), one audit-noise defect, one latent loop-killer in the guard, one
hygiene item.

## Findings and resolutions

**F1 — REAL BUG (critical): a torn journal line crashed the restart.**
JSONL was chosen because "a crash mid-write can cost at most the final line" — but the
reader didn't honor that: `LiveJournal()` re-parses its file on construction to arm
dedup, and a torn final line (exactly what a crash mid-write leaves) raised
JSONDecodeError, so the bot could not START after the very crash the format is meant to
tolerate. Probe confirmed the crash. → Tolerant reads everywhere: a torn line or a
schema-drifted row (valid JSON, bad fields) is skipped, counted
(`corrupt_journal_lines` / `corrupt_decision_lines`), warned to stderr, and left on
disk for forensics. A trade whose own line was the torn one self-heals: its key isn't
in dedup, so the next emission re-journals it. Regression tests: torn journal line,
torn decisions line, drifted row.

**F2 — REAL BUG (proven live): id()-keyed config-hash cache stamped a stale hash.**
`cfg_hash` was cached by `id(cfg)`. CPython reuses freed addresses: the probe deleted a
config, created a different one, got the SAME id, and the journal stamped the wrong
`config_hash` on the next trade — silent corruption of the reproducibility stamp, the
one field that exists to prove which strategy version made a trade. → Cache deleted;
the hash is computed fresh per trade (sha256 of a small JSON, ~2 calls/day — caching
bought nothing). Regression test forces the del-then-recreate sequence.

**F3 — audit noise: session picks re-logged on every restart.**
The Vault re-rolls its warmup sessions after a restart, so `wrap_policy` appended the
same daily picks again each time — a crash-looping bot would fill the decisions trail
with phantom "re-decisions". → (date, book) pairs are logged once, deduped in memory
and re-armed from disk on construction (same discipline as trade dedup). A *different*
pick for the same date is still logged — that IS news. Regression test covers re-roll,
restart, and changed-pick.

**F4 — latent loop-killer: RiskGuard.gate() called the halt hook unprotected.**
`gate()` runs INSIDE the engine's day_gate path; `on_halt` was invoked bare, so any
raising alert hook would have propagated into `simulate()` and killed the trading loop
from inside the risk guard. Both current hooks (Telegram, journal) happen to be
fail-soft internally, but the guard trusted that by accident, and Stage-8 wiring will
combine hooks. → try/except at the call site, and a `fanout(*hooks)` combiner in
src/live/risk.py (each hook isolated) — which also fixes the journal docstring that
referenced a `multi()` helper that never existed. Regression tests: raising hook still
returns the stand-down; fanout isolates and still calls the rest.

**F5 — hygiene: parity_check leaked its scratch journal dir.**
`mkdtemp` was never cleaned. → removed on a PASSED gate; deliberately KEPT and printed
on a FAILED gate (that journal is the forensic evidence).

## Re-verification after fixes
- Both critical probes re-run against the fixed code: torn-line restart SURVIVES
  (1 intact trade kept, 1 line skipped); id-reuse probe stamps the CORRECT hash.
- 268 tests green (7 new regression tests), ruff clean.
- Both standing parity windows re-passed with the journal gate: Feb 9–13 (7 trades,
  row-for-row) and Mar 16–20 (8 trades, row-for-row).
