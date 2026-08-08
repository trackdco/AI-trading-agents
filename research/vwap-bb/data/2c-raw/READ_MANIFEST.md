# READ MANIFEST

Append one line per file read.

Complete and honest record of every file this session read, searched, listed or opened,
in order. Nothing outside the working directory
`/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/blind_build/`
was read, with the single permitted exception noted at the bottom.

## Read (working directory)

- `SPEC.md`  — read in full, in two passes (lines 1–400, then 400–728)
- `TASK.md`  — read in full
- `bars_api.py` — read in full
- `READ_MANIFEST.md` — read (this file, before appending)

## Directory listings (working directory only)

- `ls -la` of the working directory itself, once, at the start. No other directory was
  listed anywhere on the machine.

## Written / created by me (working directory)

- `blind_impl.py`
- `blind_trades.json`
- `sensitivity.py`
- `AMBIGUITIES.md`
- `NOTES.md`
- `READ_MANIFEST.md` (this file)

## Scratch files I created and read back (outside the project, inside my own scratch area)

- `/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/scratchpad/prev.json`
  — a copy of my own `blind_trades.json`, made by me, read back only to verify that a rerun
  is byte-identical. Contains nothing but my own output.
- `/tmp/claude-0/-home-user-AI-trading-agents/90c7bfeb-e680-5848-8a9b-2088af4f6416/tasks/bmoex1ox5.output`
  — the captured stdout of my own backgrounded `sensitivity.py` run. My own output.

## The one permitted read outside the working directory

- `/home/user/AI-trading-agents/research/star-trading/tools/_nq_frontmonth.pkl`
  — loaded **indirectly and only** by `bars_api._build()` when `bars_api.sessions()` is called.
  I never opened, inspected, listed or unpickled it myself. This is the exception TASK.md
  explicitly grants.

## Explicit negative statement

I did **not** read, grep, glob, list or open any `.py` file, or any other file, under
`/home/user/AI-trading-agents/` — including anything under
`/home/user/AI-trading-agents/research/star-trading/tools/`. I did not list that directory or
any parent of it. No file named in SPEC.md as a cross-reference
(`research/STATE.md`, `research/vwap-bb/preflight.md`, `research/vwap-bb/PARITY-P2-RESULT.md`,
`research/vwap-bb/target-stop-reconciliation.md`, `data/reference/hand_log_scope.md`,
`vwapbb_a7_selector.py`, `loc_gate_measure.py`, `spec_current.py`,
`workbench_results_SEALED.parquet`) was opened or searched for; every reference to their
contents in my notes is quoted from SPEC.md itself.

No session with `session_end_date > 2025-01-31` was processed; the filter is applied before any
session is touched and is re-asserted inside `process_session()`.

**No accidental reads occurred. This manifest is complete and honest.**
