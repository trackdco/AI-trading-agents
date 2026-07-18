#!/usr/bin/env python3
"""FreshEyes v0.5 calibration — the memory-quarantined agent (v0.4 analog prompt, NO
inherited notes) scored across a WHOLE horizon instead of one month (Pat directive,
18 Jul). Because fresh-eyes carries no notes, every day is INDEPENDENT — there is no
chain, so all requests can be emitted at once and answered fully in parallel. This is
the fast path for firing an entire year.

    python -m scripts.run_fresheyes_calibration emit   --start 2026-02-01 --end 2026-07-31
    python -m scripts.run_fresheyes_calibration ingest --start 2026-02-01 --end 2026-07-31

emit   writes output/desk_blobs/fe/<date>.request.txt for every gradeable day (fresh
       briefing + analog block). Answer each as <date>.response.txt (any order, parallel).
ingest validates every response (fail-closed), grades each against the realized oracle
       (Angus $0-best-book = FLAT), and prints the horizon scorecard: reads + capture +
       regret by month and overall, plus the confusion matrix and the worst leaks.

Grading uses realized book P&L (l2_analog_routing.csv / allyears_daily_books.csv). Days
without P&L are emitted but not graded. Nothing here chains, memoizes, or shares state
between days — that is the whole point of the fresh-eyes control.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_regime_replay import _load_inputs  # noqa: E402
from src.desk.regime_agent import (  # noqa: E402
    build_briefing,
    parse_verdict,
    render_prompt,
)
from src.desk.v04 import (  # noqa: E402
    _load_books,
    as_fresh_eyes,
    attach_analog_block,
    grade_day,
    load_analog_block,
    verdict_action,
)

BLOBS = Path("output/desk_blobs/fe")
OUT = Path("output/fe")
VERDICTS = OUT / "verdicts.csv"
LEDGER = OUT / "ledger.csv"


def _days(start: str, end: str) -> list[str]:
    # read the vector directly — ingest needs only the day list, and _load_inputs()
    # pulls the arm-C news loader which now collides with Brake's calendar file.
    vec = pd.read_csv("output/regime_vector.csv")
    return [d for d in vec["day"] if start <= d <= end]


def cmd_emit(args) -> int:
    BLOBS.mkdir(parents=True, exist_ok=True)
    df, vec, cal, _analogs, news = _load_inputs()
    emitted = skipped = 0
    for d in _days(args.start, args.end):
        try:
            base = build_briefing(d, df, vec, cal, None, news, playbook_notes="")
        except ValueError as e:
            print(f"{d}: SKIP ({e})")
            skipped += 1
            continue
        brief = attach_analog_block(as_fresh_eyes(base), load_analog_block(d))
        (BLOBS / f"{d}.briefing.json").write_text(json.dumps(brief, default=str))
        (BLOBS / f"{d}.request.txt").write_text(render_prompt(brief))
        emitted += 1
    print(f"emitted {emitted} fresh-eyes requests to {BLOBS}/ ({skipped} skipped). "
          f"Answer each as <date>.response.txt (parallel, any order), then `ingest`.")
    return 0


def _append(path: Path, rows: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def cmd_ingest(args) -> int:
    books = _load_books()
    verdicts, ledger, failed = [], [], 0
    for d in _days(args.start, args.end):
        resp = BLOBS / f"{d}.response.txt"
        if not resp.exists():
            continue
        try:
            v = parse_verdict(resp.read_text(), expect_date=d)
        except Exception as e:
            failed += 1
            print(f"{d}: INVALID ({type(e).__name__}: {e}) — fail-closed")
            continue
        verdicts.append(v.model_dump())
        act = verdict_action(v.regime, v.stand_down, v.size_multiplier)
        g = grade_day(d, act, books=books)
        if g is not None:
            ledger.append({"month": d[:7], "regime": v.regime, **g})
    if verdicts:
        _append(VERDICTS, verdicts)
    if not ledger:
        print(f"ingested {len(verdicts)} verdicts, {failed} failed; no gradeable days.")
        return 0
    _append(LEDGER, ledger)
    L = pd.DataFrame(ledger)

    print(f"\n=== FreshEyes v0.5 calibration — {len(L)} graded days "
          f"({args.start}..{args.end}), {failed} fail-closed ===\n")
    hdr = f"{'month':9} {'days':>5} {'reads':>10} {'capture':>18} {'regret':>10}"
    print(hdr)
    print("-" * len(hdr))
    for m, g in L.groupby("month"):
        cap = g.agent_pl.sum() / g.oracle_pl.sum() * 100 if g.oracle_pl.sum() else 0
        print(f"{m:9} {len(g):>5} {str(g.hit.sum())+'/'+str(len(g))+' '+str(round(g.hit.mean()*100))+'%':>10} "
              f"{'$'+format(int(g.agent_pl.sum()),',')+'/'+format(int(g.oracle_pl.sum()),','):>18} "
              f"{'$'+format(int(g.regret.sum()),','):>10}")
    cap = L.agent_pl.sum() / L.oracle_pl.sum() * 100 if L.oracle_pl.sum() else 0
    print("-" * len(hdr))
    print(f"{'ALL':9} {len(L):>5} {str(L.hit.sum())+'/'+str(len(L))+' '+str(round(L.hit.mean()*100))+'%':>10} "
          f"{'$'+format(int(L.agent_pl.sum()),',')+'/'+format(int(L.oracle_pl.sum()),','):>18} "
          f"{'$'+format(int(L.regret.sum()),','):>10}")
    print(f"\n(capture = follow-the-reads $ / oracle+SD $; overall = "
          f"{cap:.0f}% of the ${int(L.oracle_pl.sum()):,} ceiling)")

    print("\n=== confusion matrix (agent action vs realized oracle) ===")
    print(pd.crosstab(L.action, L.oracle).to_string())

    print("\n=== biggest leaks (top regret days) ===")
    for _, r in L.nlargest(8, "regret").iterrows():
        print(f"  {r.day}: agent {r.action} ({r.regime}) vs oracle {r.oracle} "
              f"| E3 {r.e3:+,} E4 {r.e4:+,} | regret ${int(r.regret):+,}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("emit", "ingest"):
        s = sub.add_parser(name)
        s.add_argument("--start", required=True)
        s.add_argument("--end", required=True)
    args = p.parse_args()
    return cmd_emit(args) if args.cmd == "emit" else cmd_ingest(args)


if __name__ == "__main__":
    raise SystemExit(main())
