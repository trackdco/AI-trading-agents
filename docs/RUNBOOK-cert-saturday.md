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

**ATTEMPT 2 (2026-08-01 07:55–08:35): FAIL — wiring clean, data path caught again.**
Detector fired (45 triggers), 75 placements each matched by a cancel, gate cancels
named, both price scales journaled, zero errors, 32-minute runtime. But 30/75 verdicts
were LONG brackets with stops ABOVE their limits. Forensics (`scripts/dump_box_bars.py`):
6519/6784 practice-window bars had **open = 0.0** — the box's `NQU6.CME.scid` is a TICK
file (record Open is a flag; High/Low are ask/bid quotes; Close is the trade), and the
minute aggregator trusted the zero open. A zero open reads as "displacement through
every level below the close" → phantom longs, stops at the candle low above the entry.
Fixed: per-record tick semantics in `MinuteAggregator` (OHLC from TRADE prices;
quote extremes never contaminate bars), priceless records skipped, test-pinned. The
bar dump now also writes a 2026-07-14 window for bar-level parity against the repo's
Databento-built reference parquet.

**ATTEMPT 3 (2026-08-01 09:28–09:58): geometry clean, one wiring bug caught + fixed.**
33 triggers, 26 verdicts, ZERO wrong-side stops, zero errors — bars certified against
the reference (2026-07-14: high/low 100% identical over 600 session minutes, triggers
72=72, sub-tick level noise only). One genuine find: `ny:2026-07-31:20` (short 28193.75)
was TOUCHED at 10:21 and gate-cancelled the same minute — the cancel popped the order
record, orphaning the queued fill: naked, stopless, unjournaled broker position. Fixed
two ways, both test-pinned: (1) dispatch processes fills BEFORE the runner's per-bar
cancels/resizes, so a bar-quantized cancel can never race a fill; (2) NYExecution keeps
a cancelled-order graveyard so a racing fill (armed path: broker fills between our poll
and our cancel) still attributes, routes to the runner, and the refusal scratches it
flat. Practice day 4 = the certification run.

**ATTEMPT 4 (2026-08-01 10:26–10:55): PASS — R13 CERTIFIED.**
Deterministic replay, byte-identical to attempt 3 except exactly the race fix's rows:
ny:2026-07-31:20's same-minute touch now runs fill -> fill-minute gate refusal ->
`scratch` -> `scratched` (flattened, stop down first) instead of a blind cancel that
orphaned the fill. Zero errors, zero wrong-side stops, both price scales journaled,
every placement/cancel matched. The `--arm` R13 refusal comes off in the certified
commit; the two-party gate (config/arming.yaml + token, `verify_for_arming`) remains
fail-closed and is what stands between this commit and money.

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
