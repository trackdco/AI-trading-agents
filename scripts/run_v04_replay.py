#!/usr/bin/env python3
"""v0.4 replay harness — one sealed CHAIN with a per-day FRESH-EYES panel (Angus
directive, 18 Jul). Concurrency is by chain: run many invocations of this script at
once (one arm/month each) and answer their verdicts in parallel; within a chain the
incumbent's notes are strictly sequential by design.

Each day emits TWO requests off the SAME briefing (facts + analog block):
  - <date>.chained.request.txt  — carries the incumbent's inherited playbook notes.
  - <date>.fresh.request.txt    — no inherited notes (the lock-in control).
Both are answered (by a Claude session / human / API runner) as <date>.*.response.txt.
Only the CHAINED verdict drives the gate and the notes carried to the next day; the
fresh verdict is scored beside it and their divergence is the daily frame-lock-in
signal. After each day, scorecard + regret grade both actions vs the realized oracle
(Angus rule: best-book <= 0 counts FLAT) — pure mechanics, no agent turn.

    python -m scripts.run_v04_replay --arm v04a --start 2026-06-01 --end 2026-06-30
    # resumable: already-ingested days are skipped. Seed a month from the prior
    # month's closing note with --seed-notes-file <path>.

Fail-closed: an invalid CHAINED verdict = no gate that day (champion) and notes do
NOT advance; an invalid FRESH verdict = divergence unmeasured that day. Both journaled.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_regime_replay import _append, _load_inputs  # noqa: E402
from src.desk.regime_agent import (  # noqa: E402
    build_briefing,
    journal_row,
    parse_verdict,
    render_prompt,
    verdict_to_gate,
)
from src.desk.v04 import (  # noqa: E402
    as_fresh_eyes,
    attach_analog_block,
    divergence_row,
    grade_day,
    load_analog_block,
    verdict_action,
)


def _paths(arm: str) -> dict:
    root = Path("output/v04")
    blobs = Path("output/desk_blobs/v04") / arm
    blobs.mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=True)
    return {
        "blobs": blobs,
        "verdicts": root / f"{arm}_verdicts.csv",       # chained (the incumbent)
        "gates": root / f"{arm}_gates.csv",
        "fresh": root / f"{arm}_fresh.csv",
        "journal": root / f"{arm}_journal.csv",
        "divergence": root / f"{arm}_divergence.csv",
        "ledger": root / f"{arm}_ledger.csv",
    }


def _done_days(p: dict) -> set[str]:
    if not p["verdicts"].exists():
        return set()
    return set(pd.read_csv(p["verdicts"])["date"].astype(str))


def _latest_notes(p: dict, seed: str) -> str:
    if not p["verdicts"].exists():
        return seed
    v = pd.read_csv(p["verdicts"])
    return seed if v.empty else str(v.sort_values("date").iloc[-1]["playbook_notes"])


def _wait(path: Path, after_mtime: float, poll_s: float, deadline: float) -> str | None:
    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_mtime >= after_mtime:
            return path.read_text()
        time.sleep(poll_s)
    return None


def run_day(day: str, inputs, notes: str, p: dict, poll_s: float,
            timeout_s: float) -> str:
    """Emit chained + fresh requests, wait, ingest, grade. Returns a status string;
    'timeout' means the caller should stop and resume later."""
    df, vec, cal, analogs, news = inputs
    try:
        base = build_briefing(day, df, vec, cal, None, news, playbook_notes=notes)
    except ValueError as e:
        print(f"{day}: SKIP ({e})")
        return "skip"
    block = load_analog_block(day)
    chained_b = attach_analog_block(base, block)
    fresh_b = attach_analog_block(as_fresh_eyes(base), block)

    (p["blobs"] / f"{day}.briefing.json").write_text(json.dumps(chained_b, default=str))
    reqs = {}
    for kind, brief in (("chained", chained_b), ("fresh", fresh_b)):
        rp = p["blobs"] / f"{day}.{kind}.request.txt"
        rp.write_text(render_prompt(brief))
        reqs[kind] = rp.stat().st_mtime
    print(f"{day}: emitted chained+fresh -> {p['blobs']} (awaiting both responses)",
          flush=True)

    deadline = time.monotonic() + timeout_s
    raws = {}
    for kind in ("chained", "fresh"):
        raws[kind] = _wait(p["blobs"] / f"{day}.{kind}.response.txt", reqs[kind],
                           poll_s, deadline)
        if raws[kind] is None:
            print(f"{day}: TIMEOUT waiting for {kind} — stop, rerun to resume")
            return "timeout"

    # parse both, fail-closed independently
    parsed = {}
    for kind in ("chained", "fresh"):
        try:
            parsed[kind] = parse_verdict(raws[kind], expect_date=day)
        except Exception as e:
            parsed[kind] = None
            _append(p["journal"], journal_row(chained_b, "", raws[kind], None,
                                              f"{kind}: {type(e).__name__}: {e}"))
            print(f"{day}: {kind} INVALID ({e}) — journaled, fail-closed")

    cv, fv = parsed["chained"], parsed["fresh"]
    if cv is not None:
        _append(p["verdicts"], cv.model_dump())
        _append(p["gates"], verdict_to_gate(cv).model_dump())
        _append(p["journal"], journal_row(chained_b, "chained", raws["chained"], cv))
    if fv is not None:
        _append(p["fresh"], fv.model_dump())

    # divergence + scorecard/regret (only when both verdicts are valid / P&L known)
    if cv is not None and fv is not None:
        drow = divergence_row(day, cv.model_dump(), fv.model_dump())
        _append(p["divergence"], drow)
        flag = "AGREE" if drow["agree"] else "*** DIVERGE ***"
        print(f"{day}: chained={drow['chained_action']} fresh={drow['fresh_action']} "
              f"{flag} (oracle={drow['oracle']})")
    for kind, v in (("chained", cv), ("fresh", fv)):
        if v is None:
            continue
        g = grade_day(day, verdict_action(v.regime, v.stand_down, v.size_multiplier, v.permitted_structures))
        if g is not None:
            _append(p["ledger"], {"arm": kind, **g})
    return "ok" if cv is not None else "failclosed"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True, help="chain id (blob/ledger namespace)")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--seed-notes-file", default=None,
                    help="seed the chain's opening notes from a file (e.g. prior month's close)")
    ap.add_argument("--poll-seconds", type=float, default=5.0)
    ap.add_argument("--timeout-minutes", type=float, default=45.0)
    args = ap.parse_args(argv)

    p = _paths(args.arm)
    inputs = _load_inputs()
    vec = inputs[1]
    days = [d for d in vec["day"] if args.start <= d <= args.end]
    if not days:
        print("no vector days in range")
        return 0
    seed = Path(args.seed_notes_file).read_text() if args.seed_notes_file else ""

    done = _done_days(p)
    ok = fc = skipped = 0
    for day in days:
        if day in done:
            skipped += 1
            continue
        status = run_day(day, inputs, _latest_notes(p, seed), p,
                         args.poll_seconds, args.timeout_minutes * 60)
        if status == "timeout":
            return 1
        ok += status == "ok"
        fc += status == "failclosed"

    print(f"\nv0.4 chain {args.arm} {args.start}..{args.end}: "
          f"{ok} ingested, {fc} fail-closed, {skipped} already done")
    if p["ledger"].exists():
        L = pd.read_csv(p["ledger"])
        for kind in ("chained", "fresh"):
            k = L[L.arm == kind]
            if len(k):
                print(f"  {kind}: reads {k.hit.sum()}/{len(k)} = {k.hit.mean()*100:.0f}%  "
                      f"capture ${k.agent_pl.sum():+,.0f}/${k.oracle_pl.sum():+,.0f}  "
                      f"regret ${k.regret.sum():+,.0f}")
        if p["divergence"].exists():
            D = pd.read_csv(p["divergence"])
            print(f"  frame-lock-in: chained & fresh diverged on {(~D.agree).sum()}/{len(D)} days")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
