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

from src.canon.book import DepthBook  # noqa: E402
from src.canon.sierra_files import (  # noqa: E402
    DEPTH_HEADER, DEPTH_HEADER_SIZE, DEPTH_MAGIC, DEPTH_REC_SIZE,
    SCID_HEADER, SCID_HEADER_SIZE, SCID_MAGIC, SCID_REC_SIZE,
    DepthReader, ScidReader,
)

REQUIRED_DEPTH_LEVELS = 10          # "Number of Depth Levels to Subscribe" pinned to 10 on box


class OrderFlowFail(Exception):
    """A layout-valid file that nonetheless can't feed the canon: the order-flow families
    (CVD/tape) or the depth ladder are blind. Distinct from a byte-layout mismatch — the fix
    is a Sierra subscription/recording setting, not a constant in sierra_files.py."""


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

    # --- Angus check #1: order-flow must not be blind -----------------------------------
    # Bid/Ask volume is the ONLY source of aggressor side. If it's all-zero, Sierra recorded
    # bars/ticks WITHOUT the at-bid/at-ask split, and CVD (delta = askVol − bidVol) plus the
    # whole tape/order-flow family (cvd_*, fill_delta, absorption, delta_div, stacked_imb,
    # d5/d15/d30) degenerate to zero — silently. Fail loudly instead. (Supersedes the earlier
    # all-zero-both-sides check: this also catches a single blind side.)
    tot_bid = sum(r.bid_volume for r in recs)
    tot_ask = sum(r.ask_volume for r in recs)
    tot_vol = sum(r.total_volume for r in recs)
    print(f"  order flow: Σ bidVol={tot_bid:,}  Σ askVol={tot_ask:,}  (Σ vol={tot_vol:,})")
    if recs and (tot_bid == 0 or tot_ask == 0):
        blind = ("both sides" if tot_bid == 0 and tot_ask == 0 else
                 "bid (sell-aggressor)" if tot_bid == 0 else "ask (buy-aggressor)")
        raise OrderFlowFail(
            f"ANGUS CHECK #1 FAILED — .scid order-flow volume is all-zero on {blind}.\n"
            f"    CVD (delta = askVol − bidVol) and the ENTIRE tape/order-flow family are "
            f"BLIND: every delta collapses to zero.\n"
            f"    Cause: Sierra is storing trade volume without the at-bid/at-ask split. "
            f"REMEDIATION: ensure the intraday data source records bid/ask volume per record "
            f"(a real trade feed does; a 1-Tick .scid from the Rithmic/Denali feed carries it) "
            f"— re-record a sample and re-run this check before trusting any CVD number.")
    nz = sum(1 for r in recs if r.bid_volume or r.ask_volume)
    print(f"  order flow: {nz:,}/{len(recs):,} records carry BidVolume/AskVolume (CVD source OK)")
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

    # --- Angus check #2: the ladder must be 10 deep per side, not 5 ----------------------
    # Replay every event and track the DEEPEST book reached on each side. Our wall checks
    # (WALLSZ, dep_wall_above/below, wall-behind) read the full MBP-10 ladder; a 5-deep feed
    # silently truncates them. "Number of Depth Levels to Subscribe" was pinned to 10 on box;
    # if the feed only delivers 5, Denali depth isn't fully subscribed.
    book = DepthBook()
    max_bid = max_ask = 0
    for e in evs:
        book.apply({"action": e.action, "price": e.price, "size": e.size, "ct": e.ct})
        lf = book.long_form()
        max_bid = max(max_bid, sum(1 for r in lf if r["side"] == "bid"))
        max_ask = max(max_ask, sum(1 for r in lf if r["side"] == "ask"))
    print(f"  ladder    : deepest {max_bid} bid / {max_ask} ask levels reached "
          f"(need {REQUIRED_DEPTH_LEVELS} per side)")
    if min(max_bid, max_ask) < REQUIRED_DEPTH_LEVELS:
        if max_bid == 0 and max_ask == 0:
            cause = ("the book never populated — CME depth is not subscribed at all "
                     "(a blank DOM; expected pre-funding, but NOT acceptable for the gate)")
        else:
            cause = (f"the ladder tops out at {min(max_bid, max_ask)} per side. Likely cause: "
                     f"'Number of Depth Levels to Subscribe' on the NQ?#.CME symbol pattern is "
                     f"below {REQUIRED_DEPTH_LEVELS}, or the Lucid Market Depth add-on is "
                     f"delivering only top-{min(max_bid, max_ask)} depth on the Rithmic feed "
                     f"(NOT Denali — Denali was deactivated 2026-07-26; depth comes from the "
                     f"Lucid add-on, see docs/FOR-ANGUS-golive-questions.md Q2)")
        raise OrderFlowFail(
            f"ANGUS CHECK #2 FAILED — .depth yields fewer than {REQUIRED_DEPTH_LEVELS} ladder "
            f"levels per side ({max_bid} bid / {max_ask} ask).\n"
            f"    {cause}.\n"
            f"    The depth family (WALLSZ, dep_wall_above/below, wall-behind — a top-2 signal "
            f"in every window) reads the full MBP-10 ladder and is truncated/blind below 10.\n"
            f"    REMEDIATION: confirm the DENALI CME depth feed provides 10-level MBP, set "
            f"'Number of Depth Levels to Subscribe = 10' on the NQ?#.CME symbol pattern "
            f"(0 means defer-to-global, NOT unlimited), re-record, and re-run this check.")
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
    except OrderFlowFail as e:
        # Layout is fine; the feed itself can't drive the canon. This is a Sierra
        # subscription/recording setting, NOT a constant to edit — do not point at the .py.
        print(f"\nFAIL (order-flow / depth blind): {e}")
        return 1
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
