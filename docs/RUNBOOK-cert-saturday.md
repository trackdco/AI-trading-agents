# RUNBOOK — R13 certification (Pat, on the VPS, Saturday)

The execution wiring is BUILT (`src/live/ny_execution.py` + `scripts/ny_run.py`
integration): cancels, scratch-closes, rule J/K flattens and the canon V8 exit engine
all route to a Broker; a DryRunBroker simulates fills off real bars for rehearsal.
`--arm` stays refused until this certification passes and the gate comes off in the
certified commit.

## 1. Pull + suite (expect ~793 passed, 2 known unrelated failures)

    cd C:\Users\Administrator\AI-trading-agents
    git pull origin claude/agents-capture-handoff-26rnvp
    python -m pytest -q

## 2. The practice day — replay Friday's session with simulated fills

    python -m scripts.ny_run --dryrun --replay-day 2026-07-31

Let it run until it goes quiet past the replay day (it replays the box's own .scid),
then Ctrl+C. PASS = in `output\live\ny\`:
  - `placed` rows with broker refs in decisions.jsonl (orders actually reached the broker)
  - every `cancel` matched by a `cancelled` row (the resting rule executes)
  - any fill followed by `position_closed` or `closed_now` with a `pl` (exit engine ran)
  - any pre-window fill closed by `rule_k_flatten` on the 09:30 bar
  - zero `dispatch_error` / `place_failed` rows
Push the journals (`git add -f output/live/ny && git commit && git push`) for review.

## 3. Known items the cert must eyeball (from the build's own notes)

  - `_entry_working` (DTC fill detection) is a HEURISTIC pinned only against the
    DryRunBroker — the real-Sierra pin happens on the first armed session's read-backs,
    with the conservative default (treat-as-filled -> the runner's fill gate re-checks).
  - Stacked positions: LiveExitExecutor's stop-exit verification is account-level;
    fails toward flat. Journaled as `stacked_positions` whenever >1 position is open.

## 4. After PASS

Report the journals; the R13 gate comes off in a final commit, that SHA is what the
written confirmation names (PROMOTION-GATE), then Angus's token, then Monday's arm.
The agent layer (R15) certifies separately: dry-run day + kill-test per handover §7.
