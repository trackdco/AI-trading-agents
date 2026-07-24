#!/usr/bin/env python3
"""Replay a captured Sierra day through the Route-B path (docs/BOX-HANDOFF.md step C).

Drives REAL Sierra `.scid` (+ optional `.depth`) files through `SierraFileFeed` ->
`CanonIngestor(book=DepthBook())` — the exact live wiring — and reports that real Sierra
bytes reconstruct sane bars, a populated MBP-10 book, and canon feature rows. This is the
end-to-end proof on real data that the offline tests can only simulate.

If the captured session-date ALSO exists in the repo's reference depth archive
(data/reference/depth_*/), pass --parity to run the true feed-parity check (arch §2.1):
reconstruct the book per reference-snapshot minute from `.depth` and diff (side, price, size)
against the frozen MBP-10 snapshot the backtest scored on. Capture an OVERLAPPING historical
day (one Sierra still has stored AND that is in data/reference) to get a real parity number;
a fresh live day has no reference and only the sanity replay applies.

    python scripts/sierra_parity_replay.py "C:\\SierraChart\\Data\\NQU26.scid"
    python scripts/sierra_parity_replay.py NQU26.scid NQU26.2026-02-10.depth --parity --day 2026-02-10
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.canon.book import DepthBook  # noqa: E402
from src.canon.features import depth_at, load_depth_day  # noqa: E402
from src.canon.ingestor import CanonIngestor  # noqa: E402
from src.canon.sierra_files import DepthReader, SierraFileFeed  # noqa: E402

NY = "America/New_York"


def sanity_replay(scid: Path, depth: Path | None) -> CanonIngestor:
    ing = CanonIngestor(book=DepthBook())
    feed = SierraFileFeed(scid, depth)
    n = feed.drive_batch(ing)
    bars = ing._bars
    print(f"  applied events        : {n}")
    print(f"  bars reconstructed    : {len(bars)}")
    if bars:
        print(f"  bar span (ts_event)   : {bars[0]['ts_event']}  ->  {bars[-1]['ts_event']}")
    bb, ba = ing.book.best_bid(), ing.book.best_ask()
    lf = ing.book.long_form()
    n_bid = sum(1 for r in lf if r["side"] == "bid")
    n_ask = sum(1 for r in lf if r["side"] == "ask")
    print(f"  book best bid/ask     : {bb} / {ba}"
          + (f"   spread {ba - bb:.2f}" if bb is not None and ba is not None else ""))
    print(f"  book depth (levels)   : {n_bid} bid / {n_ask} ask")
    if bars:
        fill = pd.Timestamp(bars[-1]["ts_event"])
        entry = float(bars[-1]["close"])
        row = ing.feature_row(fill, entry, "long")
        keys = sorted(row)
        print(f"  sample feature_row @ {fill} (entry {entry:.2f}, long): {len(keys)} features")
        for fam, sample in (("tape/CVD", "pm_sofar_cvd"), ("VWAP", "ent_vs_vwap_sd"),
                            ("depth", "dep_thick")):
            if sample in row:
                print(f"    {fam:9s}: {sample} = {row[sample]}")
    warn = []
    if not bars:
        warn.append("NO BARS — .scid empty or unreadable")
    if depth is not None and bb is None:
        warn.append("EMPTY BOOK — .depth produced no levels (is CME depth subscribed? "
                    "blank DOM is the expected 'data off' state pre-funding)")
    for w in warn:
        print(f"  ! {w}")
    return ing


def parity_check(depth: Path, day: str) -> int:
    ref = load_depth_day(day)
    if ref is None:
        print(f"  PARITY SKIPPED: no reference depth for {day} in data/reference/depth_* "
              f"(a fresh live day has none — capture an overlapping historical day).")
        return 0
    # reconstruct the book from .depth up to each reference-snapshot minute, diff level sets.
    events = list(DepthReader(depth).records())
    if not events:
        print("  PARITY FAIL: .depth produced no events.")
        return 1
    book = DepthBook()
    ei = 0
    snap_times = sorted(ref.ts.unique())
    matched = mism = 0
    examples: list[str] = []
    for ts in snap_times:
        ts = pd.Timestamp(ts)
        while ei < len(events) and events[ei].ts <= ts:
            book.apply({"action": events[ei].action, "price": events[ei].price,
                        "size": events[ei].size, "ct": events[ei].ct})
            ei += 1
        got = {(r["side"], round(r["price"], 2)): r["size"] for r in book.long_form()}
        want = {(r.side, round(r.price, 2)): int(r.size)
                for r in ref[ref.ts == ts].itertuples(index=False)}
        # compare the reference's levels (our long_form is top-10; reference may hold more)
        if all(got.get(k) == v for k, v in want.items() if k in got) and got:
            matched += 1
        else:
            mism += 1
            if len(examples) < 3:
                bad = {k: (got.get(k), v) for k, v in want.items() if got.get(k) != v}
                examples.append(f"    {ts}: got/want {dict(list(bad.items())[:4])}")
    total = matched + mism
    print(f"  PARITY ({day}): {matched}/{total} snapshot-minutes match the frozen MBP-10 "
          f"(got==want on the reference's overlapping levels)")
    for ex in examples:
        print(ex)
    return 0 if mism == 0 and total else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scid")
    ap.add_argument("depth", nargs="?", default=None)
    ap.add_argument("--parity", action="store_true", help="also diff .depth vs the reference day")
    ap.add_argument("--day", default=None, help="session date YYYY-MM-DD for --parity")
    a = ap.parse_args(argv[1:])
    scid = Path(a.scid)
    depth = Path(a.depth) if a.depth else None
    print(f"Route-B replay — scid={scid}  depth={depth}")
    sanity_replay(scid, depth)
    rc = 0
    if a.parity:
        if depth is None or not a.day:
            print("  --parity needs a .depth file AND --day YYYY-MM-DD")
            return 2
        print(f"\nFeed-parity vs reference (arch §2.1):")
        rc = parity_check(depth, a.day)
    print("\nDone. Engine placed nothing (data-ingest replay only).")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
