#!/usr/bin/env python3
"""Walk-forward regime-verdict harness (L3 runner — docs/REGIME-ADAPTATION-DESIGN.md).

Modes (transport is pluggable so the harness runs TODAY with zero new deps):

  emit    build briefings + deterministic prompts for a date range, write request
          blobs to output/desk_blobs/regime/<date>.request.txt (+ .briefing.json).
          A human, a Claude Code session, or a later API runner completes them.
              python -m scripts.run_regime_replay emit --start 2026-03-09 --end 2026-03-13

  ingest  validate completed responses (<date>.response.txt in the same dir),
          fail-closed; append journal rows + verdicts + engine gates.
              python -m scripts.run_regime_replay ingest

  api     (future) direct Anthropic-API transport for the full Feb->Jul replay.
          Requires the `anthropic` package + ANTHROPIC_API_KEY in .env — NEW
          DEPENDENCY, flagged per code-standards; not imported unless used.

Outputs (all under output/, gitignored by default; force-add what should persist):
  output/regime_verdicts.csv   one row per valid verdict
  output/regime_gates.csv      engine-consumable de-risk per day (RegimeGate)
  output/regime_journal.csv    append-only: every attempt incl. failures, blob shas
  output/desk_blobs/regime/    content blobs (briefing/prompt/response) — audit trail

Walk-forward notes: playbook_notes chain forward date->date (the agent's adaptation
memory). `emit` for a RANGE therefore uses the notes from the latest *ingested*
verdict before each date; for the strict day-by-day replay, emit/ingest one day at
a time (the replay driver will do exactly that).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backtest.engine import load_news_calendar  # noqa: E402
from src.desk.regime_agent import (  # noqa: E402
    RegimeVerdict,
    build_briefing,
    journal_row,
    parse_verdict,
    render_prompt,
    verdict_to_gate,
)

BLOB_DIR = Path("output/desk_blobs/regime")
VERDICTS = Path("output/regime_verdicts.csv")
GATES = Path("output/regime_gates.csv")
JOURNAL = Path("output/regime_journal.csv")
PARQUET = Path("data/reference/nq_1m_feb_jul2026.parquet")
VECTOR = Path("output/regime_vector.csv")
ANALOGS = Path("output/analog_days.csv")            # L2 hook (engine lane, optional)
NEWS = Path("data/reference/news_archive.csv")      # arm-C hook (Brake, optional)


def _load_inputs():
    df = pd.read_parquet(PARQUET)
    vec = pd.read_csv(VECTOR)
    cal = load_news_calendar()
    analogs = pd.read_csv(ANALOGS) if ANALOGS.exists() else None
    news = None
    if NEWS.exists():
        news = pd.read_csv(NEWS)
        news["published_ET"] = pd.to_datetime(news["published_ET"])
    return df, vec, cal, analogs, news


def _latest_notes() -> str:
    if not VERDICTS.exists():
        return ""
    v = pd.read_csv(VERDICTS)
    return "" if v.empty else str(v.sort_values("date").iloc[-1]["playbook_notes"])


def _append(path: Path, row: dict) -> None:
    df = pd.DataFrame([row])
    header = not path.exists()
    df.to_csv(path, mode="a", header=header, index=False)


def cmd_emit(args) -> int:
    df, vec, cal, analogs, news = _load_inputs()
    BLOB_DIR.mkdir(parents=True, exist_ok=True)
    days = [d for d in vec["day"] if args.start <= d <= args.end]
    notes = _latest_notes()
    for d in days:
        try:
            briefing = build_briefing(d, df, vec, cal, analogs, news, playbook_notes=notes)
        except ValueError as e:
            print(f"{d}: SKIP ({e})")
            continue
        prompt = render_prompt(briefing)
        (BLOB_DIR / f"{d}.briefing.json").write_text(
            pd.io.json.ujson_dumps(briefing) if hasattr(pd.io.json, "ujson_dumps")
            else __import__("json").dumps(briefing, default=str))
        (BLOB_DIR / f"{d}.request.txt").write_text(prompt)
        print(f"{d}: request emitted ({len(prompt)} chars)")
    print(f"\n{len(days)} requests in {BLOB_DIR}/ — complete each as "
          f"<date>.response.txt then run `ingest`.")
    return 0


def cmd_ingest(args) -> int:
    import json as _json
    df, vec, cal, analogs, news = _load_inputs()
    ok = failed = 0
    for resp_path in sorted(BLOB_DIR.glob("*.response.txt")):
        d = resp_path.name.split(".")[0]
        if VERDICTS.exists() and d in set(pd.read_csv(VERDICTS)["date"].astype(str)):
            continue  # idempotent: already ingested
        briefing = _json.loads((BLOB_DIR / f"{d}.briefing.json").read_text())
        prompt = (BLOB_DIR / f"{d}.request.txt").read_text()
        raw = resp_path.read_text()
        verdict: RegimeVerdict | None = None
        err = None
        try:
            verdict = parse_verdict(raw, expect_date=d)
        except Exception as e:  # fail-closed: journal the failure, no verdict row
            err = f"{type(e).__name__}: {e}"
        _append(JOURNAL, journal_row(briefing, prompt, raw, verdict, err))
        if verdict is None:
            failed += 1
            print(f"{d}: INVALID ({err}) — journaled, fail-closed")
            continue
        _append(VERDICTS, verdict.model_dump())
        _append(GATES, verdict_to_gate(verdict).model_dump())
        ok += 1
        print(f"{d}: {verdict.regime}/{verdict.directional_bias} "
              f"size={verdict.size_multiplier} stand_down={verdict.stand_down}")
    print(f"\ningested {ok} valid, {failed} failed (see {JOURNAL})")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("emit")
    e.add_argument("--start", required=True)
    e.add_argument("--end", required=True)
    sub.add_parser("ingest")
    args = p.parse_args()
    return cmd_emit(args) if args.cmd == "emit" else cmd_ingest(args)


if __name__ == "__main__":
    raise SystemExit(main())
