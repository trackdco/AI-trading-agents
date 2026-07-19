#!/usr/bin/env python3
"""Stage-7 parity gate: the streaming Vault must reproduce the batch champion EXACTLY.

Runs the full champion BLEND (daily E3/E4 switch + book trigger filters) two ways over
the same real days and diffs every trade:

  batch  — score_replay_arms-style: simulate() per book over a LONG-history frame,
           per-day book chosen by the pre-open imbal switch (the frozen reference).
  stream — ReplayFeed -> Vault(session_policy=champion_policy), default warmup buffer,
           one closed bar at a time (what live paper trading will run).

Any mismatch in (trade_date, fill_ts, direction, round(points,2), round(dollars)) fails
the gate. Run before trusting paper trading, and after ANY change to the Vault, the
champion config, or the engine.

    python -m scripts.parity_check --start 2026-02-09 --end 2026-02-13
"""

from __future__ import annotations

import argparse
import ast
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backtest.engine import simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402
from src.live.champion import book_for_day, champion_books, e4_trigger_ok  # noqa: E402
from src.live.champion import champion_policy  # noqa: E402
from src.live.feed import ReplayFeed  # noqa: E402
from src.live.journal import LiveJournal  # noqa: E402
from src.live.vault import Vault  # noqa: E402

NY = "America/New_York"
PARQUET = "data/reference/nq_1m_feb_jul2026.parquet"
TRIGGER_CACHES = ["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]
VECTOR = "output/regime_vector.csv"
BATCH_LEADIN_DAYS = 30          # batch gets MORE history than the stream buffer on purpose


def load_triggers(lo, hi) -> list[Trigger]:
    out = []
    for path in TRIGGER_CACHES:
        if not Path(path).exists():
            continue
        for r in pd.read_csv(path).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"
            and lo <= pd.Timestamp(t.ts) <= hi]


def key(td, fts, direction, points, dollars, book=None, entry=None, exit_price=None,
        exit_reason=None, size=None):
    """Strict trade identity (Stage-7 review F1): every execution-relevant field.
    The pre-review key omitted book/entry/exit/size/reason — drift in an uncompared
    field would have passed the gate silently."""
    f = lambda x: None if x is None else round(float(x), 2)  # noqa: E731
    return (str(td), str(fts), direction, f(points), f(dollars), book,
            f(entry), f(exit_price), exit_reason, None if size is None else float(size))


def batch_key(bk, t):
    return key(t.trade_date, t.fill_ts, t.direction, t.points, t.dollars, book=bk,
               entry=t.entry, exit_price=t.exit_price, exit_reason=t.exit_reason,
               size=t.size)


def event_key(e):
    return key(e.trade_date, e.fill_ts, e.direction, e.points, e.dollars, book=e.book,
               entry=e.entry, exit_price=e.exit_price, exit_reason=e.exit_reason,
               size=e.size)


def journal_key(r):
    return key(r.trade_date, r.fill_ts, r.direction, r.points, r.dollars,
               book=r.playbook, entry=r.entry, exit_price=r.exit_price,
               exit_reason=r.exit_reason, size=r.size)


def selftest(batch_keys) -> bool:
    """Prove the alarm rings (review F3): each single-field mutation of a real result
    must be detected by the comparison the gate actually uses."""
    mutations = {
        "dropped trade": batch_keys[:-1],
        "dollars off by $1": [k if i else (*k[:4], k[4] + 1.0, *k[5:])
                              for i, k in enumerate(batch_keys)],
        "wrong book": [k if i else (*k[:5], "E4" if k[5] == "E3" else "E3", *k[6:])
                       for i, k in enumerate(batch_keys)],
        "wrong exit reason": [k if i else
                              (*k[:8], "stop" if k[8] != "stop" else "target", k[9])
                              for i, k in enumerate(batch_keys)],
    }
    ok = True
    for name, mutated in mutations.items():
        caught = mutated != batch_keys
        ok &= caught
        print(f"  selftest [{name}]: {'CAUGHT' if caught else 'MISSED — comparator blind!'}")
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2026-02-09")
    ap.add_argument("--end", default="2026-02-13")
    ap.add_argument("--selftest", action="store_true",
                    help="also prove the comparator catches mutated results")
    args = ap.parse_args(argv)

    lo_day = pd.Timestamp(args.start, tz=NY)
    hi = pd.Timestamp(args.end, tz=NY) + pd.Timedelta(days=1)
    df = pd.read_parquet(PARQUET)
    vector = pd.read_csv(VECTOR)
    days = sorted(d for d in vector["day"] if args.start <= d <= args.end)
    trigs = load_triggers(lo_day, hi)

    # ---- batch reference: per-book sims over LONG history, day book by the switch
    batch_lo = lo_day - pd.Timedelta(days=BATCH_LEADIN_DAYS)
    bdf = df[(df.ts_event >= batch_lo) & (df.ts_event < hi)].reset_index(drop=True)
    books = champion_books()
    by_book = {}
    for name, cfg in books.items():
        tt = [t for t in trigs if e4_trigger_ok(t)] if name == "E4" else trigs
        tr, _, _ = simulate(bdf, tt, cfg)
        by_book[name] = tr
    batch = []
    for d in days:
        bk = book_for_day(d, vector)
        batch += [(bk, t) for t in by_book[bk] if str(t.trade_date) == d]
    batch_keys = [batch_key(bk, t) for bk, t in batch]

    if not days:                                       # review F2: no vacuous passes
        print(f"GATE FAILED: no reference days in {args.start}..{args.end}")
        return 1

    # ---- streaming: the Vault exactly as paper trading will run it, journal attached
    feed = ReplayFeed(df, start=args.start, end=args.end, warmup_days=16)
    journal = LiveJournal(Path(tempfile.mkdtemp(prefix="parity_journal_")))
    vault = Vault(session_policy=journal.wrap_policy(champion_policy(vector)),
                  triggers=trigs)
    emitted = []
    vault.add_sink(emitted.append)
    vault.add_record_sink(journal.on_record)
    for bar in feed.stream():
        vault.on_bar(bar)
    stream = [e for e in emitted if args.start <= e.trade_date <= args.end]
    stream_keys = [event_key(e) for e in stream]

    # ---- diff
    print(f"parity {args.start}..{args.end} — batch {len(batch_keys)} trades, "
          f"stream {len(stream_keys)} trades")
    width = max(len(batch_keys), len(stream_keys))
    ok = batch_keys == stream_keys
    for i in range(width):
        b = batch_keys[i] if i < len(batch_keys) else "—"
        s = stream_keys[i] if i < len(stream_keys) else "—"
        mark = "OK " if b == s else ">>>"
        print(f"  {mark} batch {b}")
        if b != s:
            print(f"      stream {s}")
    # ---- Stage-6 gate: the journal must match the batch trade log row-for-row.
    # journal rows come from full TradeRecords; keep only the scored window (warmup
    # days can complete trades too, exactly like the raw stream above).
    in_window = [r for r in journal.trades() if args.start <= r.trade_date <= args.end]
    jkeys = [journal_key(r) for r in in_window]
    jok = jkeys == batch_keys
    picks = {d["date"]: d["book"] for d in journal.decisions()
             if d["type"] == "session"}
    # review F4: session picks must MATCH the reference switch, not just be counted
    bad_picks = [(d, picks.get(d), book_for_day(d, vector)) for d in days
                 if picks.get(d) != book_for_day(d, vector)]
    pok = not bad_picks
    print(f"\nJOURNAL: {len(jkeys)} trade rows, {len(picks)} session picks logged — "
          f"{'row-for-row MATCH' if jok else 'MISMATCH vs batch trade log'}; picks "
          f"{'all match the switch' if pok else 'DIVERGE from the switch'}")
    if not jok:
        print(f"  missing={[k for k in batch_keys if k not in jkeys]}\n"
              f"  unexpected={[k for k in jkeys if k not in batch_keys]}")
    for d, got, want in bad_picks:
        print(f"  >>> pick {d}: journal {got} vs reference {want}")

    ok = ok and jok and pok
    if ok and not batch_keys:                          # review F2: no vacuous passes
        print("GATE FAILED: zero trades on both sides — window proves nothing; "
              "pick a window with reference trades")
        ok = False
    if args.selftest and batch_keys:
        print("\nSELFTEST (mutated copies of the real result must be caught):")
        ok = selftest(batch_keys) and ok
    print(f"\nPARITY: {'MATCH — gate PASSED' if ok else 'MISMATCH — gate FAILED'}")
    if ok:
        shutil.rmtree(journal.dir, ignore_errors=True)
    else:
        print(f"journal kept for forensics: {journal.dir}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
