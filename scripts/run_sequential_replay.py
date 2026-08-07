#!/usr/bin/env python3
"""Sequential day-by-day replay driver (Pat lane — v0.4 addendum E3, Angus-authorized).

The parallel month runs broke the agent's memory: every verdict was a "first
entry" because all briefings were emitted at once with the same playbook notes.
This driver runs the replay the way the design intended (regime blueprint §
walk-forward notes): ONE day at a time —

    emit day N  ->  wait for the verdict  ->  ingest  ->  emit day N+1

so day N+1's briefing carries day N's playbook notes. That chaining is the
substrate Angus's v0.4 learning mechanisms (C1 scorecard feedback, C2 regret
ledger) will run on; without it they cannot even be tested.

Transport stays pluggable (desk contract: no new deps, no LLM import in this
repo). The driver writes <date>.request.txt and BLOCKS until a fresh
<date>.response.txt appears — completed by a Claude Code session, a human, or
a future API runner. A response file is accepted only if it was written AFTER
the request (stale responses from earlier parallel runs are ignored), because
the briefing — and therefore the valid answer — changes with the chained notes.

    python -m scripts.run_sequential_replay --start 2026-06-01 --end 2026-06-30
    # resumable: already-ingested days are skipped; re-run to continue.

Fail-closed per the desk contract: an invalid response is journaled as a
failure and the driver MOVES ON (that day trades as the champion) — matching
what the live desk would do at 08:00 with a broken verdict.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_regime_replay import (  # noqa: E402
    BLOB_DIR,
    GATES,
    JOURNAL,
    VERDICTS,
    _append,
    _latest_notes,
    _load_inputs,
)
from src.desk.regime_agent import (  # noqa: E402
    build_briefing,
    journal_row,
    parse_verdict,
    render_prompt,
    verdict_to_gate,
)


def ingested_days() -> set[str]:
    if not VERDICTS.exists():
        return set()
    return set(pd.read_csv(VERDICTS)["date"].astype(str))


def emit_day(day: str, inputs, notes: str) -> tuple[dict, str, float] | None:
    """Write the day's briefing + request blobs; return (briefing, prompt,
    request_mtime) or None when the vector can't brief the day."""
    df, vec, cal, analogs, news = inputs
    try:
        briefing = build_briefing(day, df, vec, cal, analogs, news, playbook_notes=notes)
    except ValueError as e:
        print(f"{day}: SKIP ({e})")
        return None
    prompt = render_prompt(briefing)
    import json as _json
    (BLOB_DIR / f"{day}.briefing.json").write_text(_json.dumps(briefing, default=str))
    req = BLOB_DIR / f"{day}.request.txt"
    req.write_text(prompt)
    return briefing, prompt, req.stat().st_mtime


def wait_for_response(day: str, request_mtime: float, poll_s: float,
                      timeout_s: float) -> str | None:
    """Block until a response file FRESHER than the request appears (stale
    responses from earlier parallel runs are ignored). None on timeout."""
    resp = BLOB_DIR / f"{day}.response.txt"
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if resp.exists() and resp.stat().st_mtime >= request_mtime:
            return resp.read_text()
        time.sleep(poll_s)
    return None


def ingest_day(day: str, briefing: dict, prompt: str, raw: str) -> bool:
    """Validate + append (verdict/gate/journal); False = fail-closed."""
    verdict, err = None, None
    try:
        verdict = parse_verdict(raw, expect_date=day)
    except Exception as e:  # fail-closed: journaled failure, day trades as champion
        err = f"{type(e).__name__}: {e}"
    _append(JOURNAL, journal_row(briefing, prompt, raw, verdict, err))
    if verdict is None:
        print(f"{day}: INVALID ({err}) — journaled, fail-closed, moving on")
        return False
    _append(VERDICTS, verdict.model_dump())
    _append(GATES, verdict_to_gate(verdict).model_dump())
    print(f"{day}: {verdict.regime}/{verdict.directional_bias} "
          f"size={verdict.size_multiplier} stand_down={verdict.stand_down}")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--poll-seconds", type=float, default=5.0)
    ap.add_argument("--timeout-minutes", type=float, default=30.0,
                    help="max wait per day for a response before the driver exits "
                         "(resumable — rerun to continue where it stopped)")
    args = ap.parse_args(argv)

    inputs = _load_inputs()
    BLOB_DIR.mkdir(parents=True, exist_ok=True)
    vec = inputs[1]
    days = [d for d in vec["day"] if args.start <= d <= args.end]
    if not days:
        print("no vector days in range")
        return 0

    done = ingested_days()
    ok = failed = skipped = 0
    for day in days:
        if day in done:
            skipped += 1
            continue
        emitted = emit_day(day, inputs, _latest_notes())   # notes re-read EVERY day
        if emitted is None:
            continue
        briefing, prompt, req_mtime = emitted
        print(f"{day}: request emitted -> {BLOB_DIR / f'{day}.request.txt'} "
              f"(waiting for fresh {day}.response.txt)", flush=True)
        raw = wait_for_response(day, req_mtime, args.poll_seconds,
                                args.timeout_minutes * 60)
        if raw is None:
            print(f"{day}: TIMEOUT after {args.timeout_minutes:g} min — stopping "
                  f"(rerun to resume from this day)")
            return 1
        if ingest_day(day, briefing, prompt, raw):
            ok += 1
        else:
            failed += 1

    print(f"\nsequential replay {args.start}..{args.end}: "
          f"{ok} ingested, {failed} fail-closed, {skipped} already done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
