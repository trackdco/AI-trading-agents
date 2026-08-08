#!/usr/bin/env python3
"""Measure the NQ quarterly roll spread from the calendar-spread instrument itself.

Corrects the Stage 0 audit's "~230-250 pt unadjusted gaps", which was a round number
that propagated into three documents and was wrong for seven of eight workbench rolls.

The deferred premium is read from the NQxx-NQyy spread instrument's own quotes on the
roll day, not inferred by differencing two outright prints, so it is the market's price
for the roll rather than an artefact of two contracts' last trades.

HOLDOUT GUARD: rolls dated after WORKBENCH_END are refused and named, not measured.
"""
import collections, csv, io, statistics, subprocess
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WORKBENCH_END = "2025-01-31"
ARCHIVE = "glbx-mdp3-20230101-20250301.ohlcv-1m.csv.zst"
ROLLS = ["2023-03-13", "2023-06-12", "2023-09-11", "2023-12-11",
         "2024-03-11", "2024-06-17", "2024-09-16", "2024-12-17",
         "2025-03-18", "2025-06-16", "2025-09-15", "2025-12-15"]


def main():
    use = [r for r in ROLLS if r <= WORKBENCH_END]
    refused = [r for r in ROLLS if r > WORKBENCH_END]
    print(f"measuring {len(use)} workbench rolls; REFUSING {len(refused)} holdout-dated: {refused}")
    want = set()
    for r in use:
        b = date(*map(int, r.split("-")))
        want |= {(b + timedelta(days=k)).isoformat() for k in (-1, 0)}

    acc = collections.defaultdict(list)
    p = subprocess.Popen(["zstd", "-dc", str(REPO / ARCHIVE)], stdout=subprocess.PIPE)
    for row in csv.DictReader(io.TextIOWrapper(p.stdout, encoding="utf-8")):
        d = row["ts_event"][:10]
        if d > WORKBENCH_END or d not in want or "-" not in row["symbol"]:
            continue
        acc[(d, row["symbol"])].append(float(row["close"]))
    p.wait()

    print(f"\n{'roll':<12} {'spread':<14} {'n':>6} {'median':>9} {'min':>9} {'max':>9}")
    meds = []
    for rd in use:
        cand = {k: v for k, v in acc.items() if k[0] == rd}
        if not cand:
            print(f"{rd:<12} (no spread rows)")
            continue
        k = max(cand, key=lambda kk: len(cand[kk]))
        v = cand[k]
        m = statistics.median(v)
        meds.append(m)
        print(f"{rd:<12} {k[1]:<14} {len(v):>6} {m:>9.2f} {min(v):>9.2f} {max(v):>9.2f}")
    print(f"\nmin {min(meds):.2f}  median {statistics.median(meds):.2f}  "
          f"max {max(meds):.2f}  mean {statistics.mean(meds):.2f}")
    print('The audit shorthand "~230-250" holds for one roll of eight.')


if __name__ == "__main__":
    main()
