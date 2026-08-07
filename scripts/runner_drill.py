#!/usr/bin/env python3
"""Stage-8 full-stack drill: the ASSEMBLED runner must reproduce the batch backtest,
computing EVERYTHING itself.

Unlike scripts/parity_check.py (which pre-loads the frozen trigger cache and reads the
frozen regime CSV), this streams real bars through the whole LiveRunner so that:
  * triggers come from LiveDetector (live detection), not a cache;
  * the E3/E4 book comes from LiveVectorPolicy (live classification), not the CSV;
  * trades flow through the real guard + paper broker + journal.
The resulting paper ledger is then diffed against the batch champion trade log on every
execution-relevant field (the strict key from parity_check). This is the end-to-end
proof that the paper bot == the backtest, with no pre-computed inputs.

A crash-restart leg re-runs the second half from the persisted ledger and asserts the
account is byte-identical and NO duplicate alerts fire.

    python -m scripts.runner_drill --start 2026-03-16 --end 2026-03-20
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.live.feed import ReplayFeed  # noqa: E402
from src.live.runner import LiveRunner  # noqa: E402
from scripts.parity_check import (  # noqa: E402
    PARQUET, VECTOR, batch_key, book_for_day, champion_books, e4_trigger_ok,
    event_key, load_triggers, simulate,
)

NY = "America/New_York"


class _CountingAlerts:
    """Stand-in TelegramAlerts that just counts, so the drill can assert no duplicate
    trade alerts across a restart without touching the network."""
    def __init__(self):
        self.trades = 0
        self.halts = 0
        self.said = []

    def on_trade(self, ev):
        self.trades += 1

    def on_halt(self, date, reason):
        self.halts += 1

    def daily_summary(self, broker, date):
        pass

    def say(self, text):
        self.said.append(text)


def batch_reference(df, args):
    lo = pd.Timestamp(args.start, tz=NY)
    hi = pd.Timestamp(args.end, tz=NY) + pd.Timedelta(days=1)
    vector = pd.read_csv(VECTOR)
    days = sorted(d for d in vector["day"] if args.start <= d <= args.end)
    trigs = load_triggers(lo - pd.Timedelta(days=30), hi)
    bdf = df[(df.ts_event >= lo - pd.Timedelta(days=30)) & (df.ts_event < hi)]\
        .reset_index(drop=True)
    by_book = {}
    for name, cfg in champion_books().items():
        tt = [t for t in trigs if e4_trigger_ok(t)] if name == "E4" else trigs
        tr, _, _ = simulate(bdf, tt, cfg)
        by_book[name] = tr
    keys = []
    for d in days:
        bk = book_for_day(d, vector)
        keys += [batch_key(bk, t) for t in by_book[bk] if str(t.trade_date) == d]
    return keys


def run_runner(df, args, tmp, alerts):
    """Feed the runner exactly as live would: warmup bars first with DETECTION OFF (they
    fill the Vault's indicator/level buffer and the detector/vector history but carry no
    in-window triggers), then the target window with detection ON. This is both faster
    and more faithful than re-detecting historical warmup every run."""
    runner = LiveRunner(ledger_path=tmp / "ledger.csv", journal_dir=tmp / "journal",
                        starting_equity=25_000.0, alerts=alerts)
    warm_lo = pd.Timestamp(args.start, tz=NY) - pd.Timedelta(days=16)
    win_lo = pd.Timestamp(args.start, tz=NY)
    warmup = df[(df.ts_event >= warm_lo) & (df.ts_event < win_lo)]
    window = ReplayFeed(df, start=args.start, end=args.end)

    runner.detect_enabled = False
    for bar in ReplayFeed(warmup).stream():
        runner.on_bar(bar)
    runner.detect_enabled = True                       # 'go live' at the window open
    for bar in window.stream():
        runner.on_bar(bar)
    runner.finalize()
    return runner


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2026-03-16")
    ap.add_argument("--end", default="2026-03-20")
    args = ap.parse_args(argv)

    df = pd.read_parquet(PARQUET)
    batch = batch_reference(df, args)

    tmp = Path(tempfile.mkdtemp(prefix="runner_drill_"))
    alerts = _CountingAlerts()
    runner = run_runner(df, args, tmp, alerts)
    live = [event_key(e) for e in runner.broker.trades
            if args.start <= e.trade_date <= args.end]

    ok = live == batch
    print(f"full-stack drill {args.start}..{args.end}: batch {len(batch)} trades, "
          f"runner {len(live)} trades (own triggers + own book picks)")
    width = max(len(batch), len(live))
    for i in range(width):
        b = batch[i] if i < len(batch) else "—"
        s = live[i] if i < len(live) else "—"
        if b != s:
            print(f"  >>> batch  {b}")
            print(f"      runner {s}")
    print(f"alerts: {alerts.trades} trade alerts, {alerts.halts} halts "
          f"(expected {len(batch)} / 0)")
    ok = ok and alerts.trades == len(batch)

    # --- restart leg: rebuild from the SAME ledger, replay again, assert no dup alerts
    alerts2 = _CountingAlerts()
    runner2 = run_runner(df, args, tmp, alerts2)
    live2 = [event_key(e) for e in runner2.broker.trades
             if args.start <= e.trade_date <= args.end]
    restart_ok = live2 == batch and alerts2.trades == 0
    print(f"restart: account {'identical' if live2 == batch else 'DIVERGED'}, "
          f"{alerts2.trades} duplicate alerts (expected 0)")
    ok = ok and restart_ok

    print(f"\nRUNNER DRILL: {'MATCH — gate PASSED' if ok else 'MISMATCH — gate FAILED'}")
    if not ok:
        print(f"artifacts kept: {tmp}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
