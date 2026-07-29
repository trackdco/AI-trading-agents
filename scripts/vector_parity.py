#!/usr/bin/env python3
"""Stage-8 vector gate: the live E3/E4 switch must reproduce the frozen reference.

For every session day in the window, hand LiveVectorPolicy exactly the bars a live
runner would have at the decision moment (history through the first bar at/after
08:00 ET) and compare its pick to `book_for_day` on the frozen
output/regime_vector.csv. Any differing pick fails the gate.

    python -m scripts.vector_parity --start 2026-02-09 --end 2026-07-15
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.live.champion import book_for_day  # noqa: E402
from src.live.vector import LiveVectorPolicy  # noqa: E402
from src.live.vault import PENDING  # noqa: E402
from scripts.parity_check import PARQUET, VECTOR  # noqa: E402

NY = "America/New_York"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", default="2026-02-09")
    ap.add_argument("--end", default="2026-07-15")
    args = ap.parse_args(argv)

    df = pd.read_parquet(PARQUET)
    vector = pd.read_csv(VECTOR)
    days = sorted(d for d in vector["day"] if args.start <= d <= args.end)

    mismatches, pending = [], []
    for day in days:
        # the live runner's frame at decision time: everything through 08:00 that day
        cut = pd.Timestamp(f"{day} 08:00", tz=NY)
        frame = df[df.ts_event <= cut].reset_index(drop=True)
        policy = LiveVectorPolicy(lambda f=frame: f)
        pick = policy(day)
        if pick == PENDING:
            pending.append(day)
            continue
        live_book = pick[0]
        ref_book = book_for_day(day, vector)
        if live_book != ref_book:
            mismatches.append((day, live_book, ref_book,
                               policy.shares.get(day),
                               vector[vector.day == day].imbal_share_20.iloc[0]))

    print(f"vector parity {args.start}..{args.end}: {len(days)} days, "
          f"{len(mismatches)} mismatches, {len(pending)} undecidable")
    for day, live, ref, ls, rs in mismatches:
        print(f"  >>> {day}: live {live} (share {ls}) vs reference {ref} (share {rs})")
    for day in pending:
        print(f"  PENDING (no 08:00 bar?): {day}")
    ok = not mismatches and not pending
    print(f"\nVECTOR: {'MATCH — gate PASSED' if ok else 'MISMATCH — gate FAILED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
