# RUNBOOK — R15 certification (Pat, on the VPS, Sunday)

The agent layer is PORTED (`src/live/agent_desk.py` — HANDOVER §7, behavior-for-behavior
from `scripts/capture_desk_run.py`; the spec `.claude/agents/trade-manager-v3.md` deploys
byte-identical). Entries stay mechanical (certified R13); at a committed fill the agent
owns the trade within driver-enforced guardrails. Mechanical laws override the agent
unconditionally: stop-first, 09:30 pre-flatten, 15:55 EOD, close-and-reverse, kill file.
Replay agent calls are SYNCHRONOUS (reference causality); live calls run on a worker
thread — the loop never waits (isolation law).

PREREQ (done 2026-08-02): Claude CLI 2.1.220 installed + authenticated on the box
(`claude -p --output-format json "..."` returns result JSON).

## 1. Pull + suite (expect ~814 passed, 2 known unrelated failures)

    cd C:\Users\Administrator\AI-trading-agents
    git pull origin claude/agents-capture-handoff-26rnvp
    python -m pytest -q

## 2. Practice day WITH AGENTS — replay Friday

    Rename-Item output\live\ny ny_r13_cert
    python -m scripts.ny_run --dryrun --replay-day 2026-07-31 --agents

Expect the usual waterfall + two agent day-reads (07:45 thesis, 09:40 re-read — each an
`agent_day_read` journal row). Friday's one genuine touch was gate-refused at the fill
minute, so the day may commit ZERO trades to manage — that is the day's honest content,
not a failure. Runs to the STALLED/STOP pair; agent calls add minutes, not hours.

## 3. A day with committed fills (if #2 managed zero trades)

    Rename-Item output\live\ny ny_r15_0731
    python -m scripts.ny_run --dryrun --replay-day 2026-07-29 --agents

07-29's depth file exists on the box. If this day commits fills, the desk manages them
with the real CLI — `agent_trade_open` / turns / `agent_trade_settled` rows, and
`output\live\ny\agent_journal.jsonl` grows past its 763-row seed copy (the REAL seed
`runs/live/journal.jsonl` is never touched by a replay, by construction).

## 4. Kill test (§7 row 8) — on whichever day managed a trade

    Rename-Item output\live\ny ny_r15_0729
    python -m scripts.ny_run --dryrun --replay-day <that day> --agents --agent-kill-test

From the second agent call on, the CLI process is KILLED ~1s after launch. PASS = the
run completes; every managed trade still exits mechanically (stop / flatten / flip);
zero dispatch_error rows; the dead calls journal as hold.

## 5. Push everything for the verdict

    git add -f output/live/ny output/live/ny_r15_0731 output/live/ny_r15_0729
    git commit -m "R15 practice days - agents on"
    git push

PASS criteria (read against the journals):
  - `agent_day_read` rows with parseable thesis/re-read JSON
  - every committed fill -> `agent_trade_open` -> turns in transcripts -> settle row
    in agent_journal.jsonl, schema-identical to the seed rows, `v8_R` present
  - guardrail evidence: no stop ever widened, no target below floor, partials in (0,1)
  - mechanical overrides intact: flatten/flip/stop rows unchanged from mech-only runs
  - kill-test run: trades complete mechanically, zero dispatch_error
  - the R13 mech invariants still hold (zero wrong-side stops, zero orphaned fills)

Then the certified commit + Pat's written confirmation naming the NEW SHA + Angus's
fresh arming.yaml (the current authorization dies with the agent code landing) + phrase.
