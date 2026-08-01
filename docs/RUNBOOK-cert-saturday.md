# RUNBOOK — R13 certification (Pat, on the VPS, Saturday)

The execution wiring is BUILT (`src/live/ny_execution.py` + `scripts/ny_run.py`
integration): cancels, scratch-closes, rule J/K flattens and the canon V8 exit engine
all route to a Broker; a DryRunBroker simulates fills off real bars for rehearsal.
`--arm` stays refused until this certification passes and the gate comes off in the
certified commit.

**ATTEMPT 1 (2026-08-01 03:22–06:55): FAIL — and that failure is why the cert exists.**
Zero triggers all day, in the replay AND in Friday's live shadow. Three root causes,
all fixed + test-pinned in the follow-up commit:
  1. The box's Rithmic-named `NQU6.CME.scid` writes bar prices **100x** (2857526.00);
     the detector's point-based geometry goes blind at 100x (reproduced on reference
     days: 72/32/69 triggers at 1x -> 1/0/0 at 100x). Bars now normalize at the feed,
     evidence-anchored, refusing on ambiguity; journals a `price_scale` row.
  2. `session_day` on raw UTC stamps rolled the trading day at **1pm ET**, clearing
     position state mid-session (Friday's shadow "started 2026-08-01" on Friday
     afternoon). Boundary now converts to ET: rolls at 17:00 ET.
  3. Full-history frame rebuild per bar made the replay ~1 min/bar (3.5h). Frame now
     trimmed to 14 days — trigger-identical to deeper frames on 3 reference days
     (`python -m scripts.check_trim_parity`).

## 1. Pull + suite (expect ~800 passed, 2 known unrelated failures)

    cd C:\Users\Administrator\AI-trading-agents
    git pull origin claude/agents-capture-handoff-26rnvp
    python -m pytest -q

## 2. The practice day — replay Friday's session with simulated fills

Move attempt 1's journals aside first (they are committed; the rerun starts clean):

    Rename-Item output\live\ny ny_practice1_fail
    python -m scripts.ny_run --dryrun --replay-day 2026-07-31

Runs to the `feed STALLED — halting (fail closed)` + `ny_run STOP` pair on its own
(no Ctrl+C). Expected much faster than attempt 1. PASS = in `output\live\ny\`:
  - a `price_scale` row: `bars / 100` (and `depth / 100` once the day's depth loads)
  - `trigger_seen` rows during the 07:45–11:00 ET band (the detector actually firing)
  - `placed` rows with broker refs (orders actually reached the broker)
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
