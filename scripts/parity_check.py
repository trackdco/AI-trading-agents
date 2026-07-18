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
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.backtest.engine import simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402
from src.live.champion import book_for_day, champion_books, e4_trigger_ok  # noqa: E402
from src.live.champion import champion_policy  # noqa: E402
from src.live.feed import ReplayFeed  # noqa: E402
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


def key(td, fts, direction, points, dollars):
    return (str(td), str(fts), direction, round(float(points), 2), round(float(dollars)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2026-02-09")
    ap.add_argument("--end", default="2026-02-13")
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
    batch_keys = [key(t.trade_date, t.fill_ts, t.direction, t.points, t.dollars)
                  for _, t in batch]

    # ---- streaming: the Vault exactly as paper trading will run it
    feed = ReplayFeed(df, start=args.start, end=args.end, warmup_days=16)
    vault = Vault(session_policy=champion_policy(vector), triggers=trigs)
    emitted = []
    vault.add_sink(emitted.append)
    for bar in feed.stream():
        vault.on_bar(bar)
    stream = [e for e in emitted if args.start <= e.trade_date <= args.end]
    stream_keys = [key(e.trade_date, e.fill_ts, e.direction, e.points, e.dollars)
                   for e in stream]

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
    print(f"\nPARITY: {'MATCH — gate PASSED' if ok else 'MISMATCH — gate FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
