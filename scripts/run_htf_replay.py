#!/usr/bin/env python3
"""HTF-structure verdict harness (assignment #2) — mirrors scripts/run_regime_replay.py.

  emit    python -m scripts.run_htf_replay emit --start 2026-03-09 --end 2026-03-13
  ingest  python -m scripts.run_htf_replay ingest

Blobs in output/desk_blobs/htf/; verdicts/gates/journal in output/htf_*.csv.
The same day's regime verdict (output/regime_verdicts.csv) is included in the
briefing when present — the task-doc sanctioned interlock (war => fades off).
Walk-forward note-chaining follows the regime runner's convention.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.desk.htf_agent import (  # noqa: E402
    AGENT_FILE,
    HTFStructureVerdict,
    build_structure_briefing,
    parse_verdict,
    verdict_to_gate,
)
from src.desk.regime_agent import journal_row, render_prompt  # noqa: E402

BLOB_DIR = Path("output/desk_blobs/htf")
VERDICTS = Path("output/htf_verdicts.csv")
GATES = Path("output/htf_gates.csv")
JOURNAL = Path("output/htf_journal.csv")
PARQUET = Path("data/reference/nq_1m_feb_jul2026.parquet")
REGIME_VERDICTS = Path("output/regime_verdicts.csv")


def _regime_verdicts() -> pd.DataFrame | None:
    return pd.read_csv(REGIME_VERDICTS) if REGIME_VERDICTS.exists() else None


def _latest_notes() -> str:
    if not VERDICTS.exists():
        return ""
    v = pd.read_csv(VERDICTS)
    return "" if v.empty else str(v.sort_values("date").iloc[-1]["playbook_notes"])


def _append(path: Path, row: dict) -> None:
    pd.DataFrame([row]).to_csv(path, mode="a", header=not path.exists(), index=False)


def _session_days(df: pd.DataFrame, start: str, end: str) -> list[str]:
    sd = (df["ts_event"].dt.tz_convert("America/New_York") + pd.Timedelta(hours=6)).dt.date
    return sorted({str(d) for d in set(sd) if start <= str(d) <= end})


def cmd_emit(args) -> int:
    df = pd.read_parquet(PARQUET)
    BLOB_DIR.mkdir(parents=True, exist_ok=True)
    notes = _latest_notes()
    rv = _regime_verdicts()
    n = 0
    for d in _session_days(df, args.start, args.end):
        try:
            briefing = build_structure_briefing(d, df, rv, playbook_notes=notes)
        except ValueError as e:
            print(f"{d}: SKIP ({e})")
            continue
        prompt = render_prompt(briefing, agent_file=AGENT_FILE)
        (BLOB_DIR / f"{d}.briefing.json").write_text(json.dumps(briefing, default=str))
        (BLOB_DIR / f"{d}.request.txt").write_text(prompt)
        print(f"{d}: request emitted ({len(prompt)} chars)")
        n += 1
    print(f"\n{n} requests in {BLOB_DIR}/ — complete each as <date>.response.txt, then `ingest`.")
    return 0


def cmd_ingest(args) -> int:
    ok = failed = 0
    for resp_path in sorted(BLOB_DIR.glob("*.response.txt")):
        d = resp_path.name.split(".")[0]
        if VERDICTS.exists() and d in set(pd.read_csv(VERDICTS)["date"].astype(str)):
            continue
        briefing = json.loads((BLOB_DIR / f"{d}.briefing.json").read_text())
        prompt = (BLOB_DIR / f"{d}.request.txt").read_text()
        raw = resp_path.read_text()
        verdict: HTFStructureVerdict | None = None
        err = None
        try:
            verdict = parse_verdict(raw, expect_date=d)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
        _append(JOURNAL, journal_row(briefing, prompt, raw, verdict, err, agent_file=AGENT_FILE))
        if verdict is None:
            failed += 1
            print(f"{d}: INVALID ({err}) — journaled, fail-closed (fades off)")
            continue
        _append(VERDICTS, verdict.model_dump())
        _append(GATES, verdict_to_gate(verdict).model_dump())
        ok += 1
        print(f"{d}: {verdict.daily_context}/{verdict.h4_leg} nested={verdict.h4_leg_nested_as} "
              f"fade={verdict.fade_permitted} cont_only={verdict.continuation_only}")
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
