# FINDINGS — PHASE C: the live flow recorder (2026-08-07)

## Status: SHIPPED, replay-certified, ready for VPS wiring

`scripts/htf_flow_recorder.py` — log-only, Stage-3 shadow artifact. It has
no order path, no DTC code, no position logic: it cannot act even by bug,
because there is nothing in the file that could place an order.

Why it exists and why today: S1's win-rate lift is +4.0pp; the sealed flow
holdout resolves ±10pp on ~6 months, so per the standing declaration the
flow look stays unspent and CANNOT validate S1. Forward-recorded flow is
S1's only real validation route, and every session that passes without the
recorder is uncontaminated forward data lost permanently.

**Parity by construction:** the recorder imports the SAME `day_rows`
function the M-TABLE builder uses — the twelve features and the trigger
grammar cannot drift from research, because there is one implementation.

**Certification (2026-08-07):** `--replay` mode reproduced the research
table bit-for-bit on two sessions — 2026-06-02 (26/26 triggers) and
2026-03-10 (18/18): entry, stop, risk, and all twelve flow features
identical.

**Startup self-gates** (it refuses to log rather than log garbage):
- G-DELTA: corr(delta, 1m vwp change) on the trailing tape must exceed
  +0.2 — catches a sign-inverted or dead delta feed at startup.
- G-CLOCK: newest bar within 3 minutes of wall clock.
- G-DEPTH: ≥30h bars, ≥20 completed 15m bars.
It survives restarts (re-reads its own journal, never double-logs) and
never dies on a data error (logs, retries next quarter-hour).

**Journal row:** keys + geometry + all twelve features + `s1_keep` (the S1
verdict as the live system would have read it) + `logged_at`. Outcomes are
NOT logged live (not knowable at decision time); they get joined later by
the same walk research uses.

## ⚠ Convention defect found during wiring — separate from the recorder

The M-TABLE's delta convention was verified empirically before shipping:
fp delta correlates **+0.46** with same-minute price change (top-decile
delta minutes +8.5 pts, bottom-decile −8.6) — so research delta =
buys − sells, standard, and **S1 reads as flow-CONFIRMATION** (keep fights
where the trigger bar's aggressive flow agrees with the trade).

But `scripts/build_cvd_minute.py` documents side 'A' = buy aggressor and
computes delta = A − B. The footprint files' empirical semantics are the
opposite (side 'B' is the buy side). Its output
(`output/cvd_minute_apr2026.csv`) and anything downstream that consumed it
likely carries an **inverted delta**. This is the same disease class the
convention gate caught once before (fp delta sign inversion, caught
2026-08). The recorder does not depend on that file; audit it before its
next use.

## Wiring instructions

Full runbook: `docs/RUNBOOK-flow-recorder.md`. Config template:
`config/flow_recorder.json.example` — point `bars_path`/`fp_path` at the
intraday reader's rolling state files (fp_minutes schema, delta =
side'B' − side'A'), `journal` at the append-only output. Market data stays
on the Sierra box; the recorder runs there under the existing
watchdog/Task-Scheduler pattern.

## One next action

Run the replay certification ON THE VPS against yesterday's session
(`python -m scripts.htf_flow_recorder --replay <sess_day>` → must print
PARITY PASS), then schedule `--live` under the watchdog. Nothing else
until the journal shows its first clean week.
