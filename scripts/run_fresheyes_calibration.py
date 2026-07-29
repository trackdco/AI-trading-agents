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

from src.backtest.engine import load_news_calendar  # noqa: E402
from src.desk.regime_agent import (  # noqa: E402
    build_briefing,
    parse_verdict,
    render_prompt,
)
from src.desk.briefing_v05 import build_v062_briefing  # noqa: E402
from src.desk.v04 import (  # noqa: E402
    _load_books,
    as_fresh_eyes,
    attach_analog_block,
    grade_day,
    load_analog_block,
    verdict_action,
)

MASTER_PARQUET = "data/reference/nq_1m_master.parquet"   # covers 2023-01 .. 2026-07


def _paths(tag: str):
    """Namespace blobs + ledgers by run tag so v0.5 and v0.6 don't overwrite."""
    blobs = Path(f"output/desk_blobs/{tag}")
    out = Path(f"output/{tag}")
    return blobs, out, out / "verdicts.csv", out / "ledger.csv"


def _days(start: str, end: str) -> list[str]:
    vec = pd.read_csv("output/regime_vector.csv")
    return [d for d in vec["day"] if start <= d <= end]


def _inputs(parquet: str):
    # year-agnostic loader: master parquet (all years) + vector + the now-backfilled
    # calendar. No arm-C news (avoids the collision; these runs are arm B).
    df = pd.read_parquet(parquet)
    vec = pd.read_csv("output/regime_vector.csv")
    cal = load_news_calendar()
    return df, vec, cal


def cmd_emit(args) -> int:
    BLOBS, _OUT, _V, _L = _paths(args.tag)
    BLOBS.mkdir(parents=True, exist_ok=True)
    df, vec, cal = _inputs(args.parquet)
    news = None
    agent_file = Path(args.agent_file) if args.agent_file else None
    v062_books = v062_ledger = None
    if args.v062:
        # R1/R2-floored books = "what paid under the floor the engine enforces"
        v062_books = pd.read_csv(args.books).rename(
            columns={"E3": "pl_e3", "E4": "pl_e4"}).set_index("day")
        if args.feedback_ledger:
            fl = pd.read_csv(args.feedback_ledger)
            v062_ledger = fl[["day", "action", "agent_pl", "oracle_pl"]].copy()
    emitted = skipped = 0
    for d in _days(args.start, args.end):
        try:
            base = build_briefing(d, df, vec, cal, None, news, playbook_notes="")
        except ValueError as e:
            print(f"{d}: SKIP ({e})")
            skipped += 1
            continue
        brief = attach_analog_block(as_fresh_eyes(base), load_analog_block(d))
        if args.v062:
            brief = build_v062_briefing(brief, d, cal, v062_books, v062_ledger,
                                        asof=args.asof)
        (BLOBS / f"{d}.briefing.json").write_text(json.dumps(brief, default=str))
        (BLOBS / f"{d}.request.txt").write_text(
            render_prompt(brief, agent_file=agent_file) if agent_file
            else render_prompt(brief))
        emitted += 1
    print(f"emitted {emitted} fresh-eyes requests to {BLOBS}/ ({skipped} skipped). "
          f"Answer each as <date>.response.txt (parallel, any order), then `ingest`.")
    return 0


def _append(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def cmd_ingest(args) -> int:
    BLOBS, _OUT, VERDICTS, LEDGER = _paths(args.tag)
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
        act = verdict_action(v.regime, v.stand_down, v.size_multiplier, v.permitted_structures)
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
    L["year"] = L.month.str[:4]

    print(f"\n=== FreshEyes calibration [{args.tag}] — {len(L)} graded days "
          f"({args.start}..{args.end}), {failed} fail-closed ===\n")
    hdr = f"{'period':9} {'days':>5} {'reads':>10} {'capture':>18} {'regret':>10}"
    print(hdr)
    print("-" * len(hdr))
    for y, g in L.groupby("year"):                       # by-year rollup (multi-year runs)
        print(f"{y:9} {len(g):>5} {str(g.hit.sum())+'/'+str(len(g))+' '+str(round(g.hit.mean()*100))+'%':>10} "
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
        s.add_argument("--tag", default="fe", help="run namespace (e.g. fe_v06)")
        if name == "emit":
            s.add_argument("--parquet", default=MASTER_PARQUET)
            s.add_argument("--v062", action="store_true",
                           help="attach base_rates + event_family_analogs + C2 bill")
            s.add_argument("--agent-file", default=None,
                           help="override agent definition (e.g. regime-context-v062.md)")
            s.add_argument("--books", default="output/allyears_daily_books_r1r2.csv",
                           help="v062: floored books for event analogs + feedback")
            s.add_argument("--feedback-ledger", default=None,
                           help="v062: graded ledger of the predecessor lineage (C2 source)")
            s.add_argument("--asof", default=None,
                           help="v062: base-rates cutoff for replay safety")
    args = p.parse_args()
    return cmd_emit(args) if args.cmd == "emit" else cmd_ingest(args)


if __name__ == "__main__":
    raise SystemExit(main())
