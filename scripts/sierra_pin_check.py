#!/usr/bin/env python3
"""PIN-ON-BOX check for the Route-B file-tail data path (docs/BOX-HANDOFF.md step B).

Opens a REAL Sierra `.scid` or `.depth` file and confirms the byte layout the parser in
`src/canon/sierra_files.py` assumes actually matches the installed Sierra build: header
magic, HeaderSize, RecordSize, Version, and — for `.depth` — that every record's Command
byte decodes to a known action. Prints the header and a sample of decoded records so a human
can eyeball prices/sizes/times against Sierra's own DOM + chart.

This is the one gate that CANNOT be closed offline (the offline tests only prove the parser
inverts its own synthetic writer). Run it on the VPS against a freshly-dumped NQU6 file.

    python scripts/sierra_pin_check.py "C:\\SierraChart\\Data\\NQU26.scid"
    python scripts/sierra_pin_check.py "C:\\SierraChart\\Data\\MarketDepthData\\NQU26.2026-07-27.depth"

Exit 0 = layout matches the pinned constants. Exit 1 = mismatch (the message names the exact
constant in src/canon/sierra_files.py to adjust, then re-run).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.canon.sierra_files import (  # noqa: E402
    DEPTH_HEADER, DEPTH_HEADER_SIZE, DEPTH_MAGIC, DEPTH_REC_SIZE,
    SCID_HEADER, SCID_HEADER_SIZE, SCID_MAGIC, SCID_REC_SIZE,
    DepthReader, ScidReader,
)


def _sample(seq, first: int = 5, last: int = 3) -> list:
    items = list(seq)
    if len(items) <= first + last:
        return items
    return items[:first] + ["  ... (%d more) ..." % (len(items) - first - last)] + items[-last:]


def check_scid(path: Path) -> bool:
    with path.open("rb") as f:
        head = f.read(SCID_HEADER_SIZE)
    magic, hsize, rsize, ver, _u, _utc, _res = SCID_HEADER.unpack(head)
    print(f"  file      : {path}  ({path.stat().st_size:,} bytes)")
    print(f"  magic     : {magic!r}   (pinned {SCID_MAGIC!r})")
    print(f"  HeaderSize: {hsize}     (pinned {SCID_HEADER_SIZE})")
    print(f"  RecordSize: {rsize}     (pinned {SCID_REC_SIZE})")
    print(f"  Version   : {ver}")
    recs = list(ScidReader(path).records())          # raises on layout mismatch
    print(f"  records   : {len(recs):,}  (full records only; a partial tail is ignored)")
    print("  sample (ts | O H L C | numTrades vol bidVol askVol):")
    for r in _sample(recs):
        if isinstance(r, str):
            print(r); continue
        print(f"    {r.ts}  {r.open:.2f} {r.high:.2f} {r.low:.2f} {r.close:.2f}  "
              f"{r.num_trades} {r.total_volume} {r.bid_volume} {r.ask_volume}")
    return True


def check_depth(path: Path) -> bool:
    with path.open("rb") as f:
        head = f.read(DEPTH_HEADER_SIZE)
    magic, hsize, rsize, ver, _u, _res = DEPTH_HEADER.unpack(head)
    print(f"  file      : {path}  ({path.stat().st_size:,} bytes)")
    print(f"  magic     : {magic!r}   (pinned {DEPTH_MAGIC!r})")
    print(f"  HeaderSize: {hsize}     (pinned {DEPTH_HEADER_SIZE})")
    print(f"  RecordSize: {rsize}     (pinned {DEPTH_REC_SIZE})")
    print(f"  Version   : {ver}")
    evs = list(DepthReader(path).records())          # raises on layout / Command enum mismatch
    print(f"  records   : {len(evs):,}  (every Command byte decoded to a known action)")
    print("  sample (ts | action | price | size | ct):")
    for e in _sample(evs):
        if isinstance(e, str):
            print(e); continue
        print(f"    {e.ts}  {e.action}  {e.price:.2f}  {e.size}  {e.ct}")
    return True


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"FAIL: no such file: {path}")
        return 1
    # dispatch by magic (robust to odd extensions), fall back to suffix
    with path.open("rb") as f:
        magic = f.read(4)
    kind = "scid" if magic == SCID_MAGIC else "depth" if magic == DEPTH_MAGIC else \
        ("scid" if path.suffix == ".scid" else "depth" if path.suffix == ".depth" else "?")
    print(f"PIN-ON-BOX check — detected {kind.upper()} file")
    try:
        ok = check_scid(path) if kind == "scid" else check_depth(path) if kind == "depth" else False
    except ValueError as e:
        print(f"\nFAIL (layout/enum mismatch): {e}")
        print("→ Adjust the corresponding PIN-ON-BOX constant in src/canon/sierra_files.py "
              "(header sizes at the top; the .depth Command enum in DCMD_*/_DCMD_ACTION), "
              "then re-run this check.")
        return 1
    if not ok:
        print("FAIL: could not identify the file as .scid or .depth (bad magic).")
        return 1
    print("\nPASS — byte layout matches the pinned constants. Eyeball the sample rows above "
          "against Sierra's chart/DOM before trusting the feed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
