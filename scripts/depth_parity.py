#!/usr/bin/env python3
"""DEPTH PARITY GATE — the live book must produce the canon's wall features.

WHY THIS IS A GATE AND NOT A NICETY. `W` (pre-market) and `D` (gold) are the ONLY entry
gates in the rebuilt canon, plus the wall-quality cut, and all three are pure depth features
(`dep_thick`, `dep_wall_{above,below}_{d,sz}`). The canon measured them from the batch depth
archive. Live they come from a book built off Sierra's feed. If the two disagree — different
aggregation, a price convention, a lag, a units mismatch on `size` — the live book quietly
becomes a different book, and it fails SILENTLY: a wrong wall distance still yields a
perfectly plausible verdict, so nothing alerts and the P&L just drifts.

ANGUS 2026-07-30: Sierra carries MBO, which is strictly richer than the archive's per-minute
MBP snapshots. Richer input does not settle this. The question is not resolution, it is
whether the DERIVED numbers land in the same place — MBO aggregated to price levels must sum
to the same contracts-per-level the archive recorded, and `size >= 7` (the WALLSZ bit) is an
absolute threshold in those units. That is exactly what this script measures.

Book choice: `OrderBook` for an order-by-order (MBO) feed, `DepthBook` for Sierra's
per-level `.depth` file. Both expose the same read interface, so `depth_at` consumes either.

    # Pat: point it at one captured session and read the gate line
    python -m scripts.depth_parity --day 2026-04-20 --events capture.jsonl --book mbo

    # No capture yet? Prove the harness + read path are self-consistent first:
    python -m scripts.depth_parity --day 2026-04-20 --self-test

`--self-test` rebuilds the book by replaying the ARCHIVE back through the book's own `apply`
and re-derives the features. It cannot validate the live FEED — only that the harness, the
book's read path and `depth_at` agree with the archive when handed identical level data. A
green self-test with a red capture means the feed differs; a red self-test means this script
or the book's read path is wrong and no capture result can be trusted.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.score_canon_span import depth_file                    # noqa: E402
from src.canon.book import DepthBook, OrderBook                    # noqa: E402
from src.canon.features import depth_at                            # noqa: E402
from src.canon.scorer_ny import Q_WALLSZ_MIN, WALL_D_MIN           # noqa: E402

NY = "America/New_York"
DEPTH_DIRS = ["data/reference/depth_2025", "data/reference/depth_2026",
              "data/reference/depth_apr2026", "data/reference/depth_2023_24"]
#: the derived quantities that actually decide trades
FEATS = ["dep_thick", "dep_wall_above_d", "dep_wall_below_d",
         "dep_wall_above_sz", "dep_wall_below_sz"]


def load_archive(day: str) -> pd.DataFrame:
    p = depth_file([ROOT / d for d in DEPTH_DIRS], day)
    if p is None:
        raise SystemExit(f"no archive depth for {day} — cannot form a parity baseline")
    d = pd.read_csv(p)
    d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
    return d


def gates(f: dict, direction: str) -> dict:
    """The BOOLEANS the canon actually gates on. Feature deviation only matters where it
    flips one of these, so they are reported separately and weigh more."""
    long = direction == "long"
    thick = f.get("dep_thick", np.nan)
    behind = f.get("dep_wall_below_d" if long else "dep_wall_above_d", np.nan)
    ahead = f.get("dep_wall_above_d" if long else "dep_wall_below_d", np.nan)
    ahead_sz = f.get("dep_wall_above_sz" if long else "dep_wall_below_sz", np.nan)
    below_d = f.get("dep_wall_below_d", np.nan)
    W = np.nan if pd.isna(thick) else float(pd.isna(behind))
    D = np.nan if pd.isna(thick) else float(not pd.isna(ahead))
    wallsz = float(D == 1 and not pd.isna(ahead_sz) and ahead_sz >= Q_WALLSZ_MIN)
    quality_cut = ((not pd.isna(below_d) and below_d < WALL_D_MIN) or wallsz == 0)
    return {"W": W, "D": D, "WALLSZ": wallsz, "gold_cut": float(quality_cut)}


def events_from_archive(snap: pd.DataFrame) -> list[dict]:
    """One minute's archive snapshot expressed as book events (clear, then set each level)."""
    evs = [{"action": "R", "price": 0.0, "size": 0, "ct": 0}]
    for r in snap.itertuples():
        evs.append({"action": "B" if str(r.side).startswith("b") else "A",
                    "price": float(r.price), "size": int(r.size),
                    "ct": int(getattr(r, "ct", 1) or 1)})
    return evs


def read_events(path: Path) -> dict[pd.Timestamp, list[dict]]:
    """A capture as JSONL, one event per line, grouped into the minute it belongs to (the book
    is snapshotted at each minute close, exactly as the archive was built).

    The event body must match the book being used — the two schemas are NOT interchangeable:

      --book depth  (Sierra .depth, per price level)
        {"ts": iso, "action": "R"|"B"|"A"|"b"|"a", "price": f, "size": i, "ct": i}
      --book mbo    (order-by-order)
        {"ts": iso, "action": "R"|"A"|"C"|"M", "order_id": i, "side": "B"|"A",
         "price": f, "size": i}

    Normalising the raw Sierra/DTC stream into one of these is the capture step's job; doing
    it wrong shows up here as a gate disagreement rather than a crash, which is the whole
    reason this gate exists."""
    by_min: dict[pd.Timestamp, list[dict]] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        ts = pd.Timestamp(e.pop("ts"))
        ts = ts.tz_convert(NY) if ts.tzinfo else ts.tz_localize(NY)
        by_min.setdefault(ts.floor("1min"), []).append(e)
    return by_min


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", required=True)
    ap.add_argument("--events", type=Path, default=None, help="captured depth events (JSONL)")
    ap.add_argument("--book", default="depth", choices=["depth", "mbo"],
                    help="depth = Sierra per-level (.depth); mbo = order-by-order")
    ap.add_argument("--self-test", action="store_true",
                    help="replay the ARCHIVE through the book instead of a live capture")
    ap.add_argument("--tick", type=float, default=0.25)
    a = ap.parse_args()
    if not a.events and not a.self_test:
        raise SystemExit("pass --events <capture.jsonl> or --self-test")
    if a.self_test and a.book == "mbo":
        raise SystemExit(
            "--self-test cannot drive the MBO book: the archive is per-PRICE-LEVEL "
            "(actions B/A/b/a) while OrderBook is order-by-order (actions A/C/M + order_id), "
            "so there are no order ids to replay. Self-test the per-level book "
            "(--book depth) to validate this harness, then run the MBO book against a real "
            "capture with --events.")

    arc = load_archive(a.day)
    minutes = sorted(arc.ts.unique())
    live_by_min = read_events(a.events) if a.events else None

    rows = []
    for m in minutes:
        snap = arc[arc.ts == m]
        mid = float(np.mean([snap[snap.side.str.startswith("b")].price.max(),
                             snap[snap.side.str.startswith("a")].price.min()]))
        if not np.isfinite(mid):
            continue
        evs = events_from_archive(snap) if a.self_test else live_by_min.get(pd.Timestamp(m))
        if not evs:
            rows.append({"ts": m, "missing": True})
            continue
        book = OrderBook() if a.book == "mbo" else DepthBook()
        for e in evs:
            book.apply(e)
        lf = pd.DataFrame(book.long_form())
        if lf.empty:
            rows.append({"ts": m, "missing": True})
            continue
        lf["ts"] = m
        # probe both directions at the mid: the gates are direction-relative, so a
        # one-sided check can pass while the side that matters is wrong.
        for direction in ("long", "short"):
            fa = depth_at(snap.assign(ts=m), pd.Timestamp(m), mid, direction)
            fl = depth_at(lf, pd.Timestamp(m), mid, direction)
            row = {"ts": m, "direction": direction, "missing": False}
            for k in FEATS:
                va, vl = fa.get(k, np.nan), fl.get(k, np.nan)
                row[f"d_{k}"] = (np.nan if (pd.isna(va) and pd.isna(vl))
                                 else (np.inf if (pd.isna(va) != pd.isna(vl))
                                       else abs(float(va) - float(vl))))
            ga, gl = gates(fa, direction), gates(fl, direction)
            row["gates_agree"] = all(
                (pd.isna(ga[k]) and pd.isna(gl[k])) or ga[k] == gl[k] for k in ga)
            rows.append(row)

    R = pd.DataFrame(rows)
    ok = R[~R.missing.fillna(False)] if "missing" in R else R
    print(f"DEPTH PARITY [{a.day}] source={'archive-selftest' if a.self_test else a.events} "
          f"book={a.book}")
    print(f"  archive minutes {len(minutes)} | compared {len(ok)} probes | "
          f"missing-from-live {int(R.missing.fillna(False).sum())}")
    if ok.empty:
        raise SystemExit("  nothing comparable — FAIL")
    for k in FEATS:
        c = ok[f"d_{k}"]
        finite = c.replace([np.inf], np.nan).dropna()
        n_nanmismatch = int(np.isinf(c).sum())
        print(f"  {k:<20} max|Δ| {(finite.max() if len(finite) else 0.0):>8.4f}  "
              f"median {(finite.median() if len(finite) else 0.0):>8.4f}  "
              f"present/absent mismatches {n_nanmismatch}")
    agree = float(ok.gates_agree.mean())
    worst = max((ok[f'd_{k}'].replace([np.inf], np.nan).dropna().max()
                 if ok[f'd_{k}'].replace([np.inf], np.nan).notna().any() else 0.0)
                for k in ("dep_wall_above_d", "dep_wall_below_d"))
    nan_mm = int(sum(np.isinf(ok[f"d_{k}"]).sum() for k in FEATS))
    verdict = (agree == 1.0 and nan_mm == 0 and worst <= a.tick)
    print(f"\n  GATE AGREEMENT (W / D / WALLSZ / wall-quality cut): {agree * 100:.2f}%")
    print(f"  {'PASS' if verdict else 'FAIL'} — "
          + ("live book reproduces every canon depth gate" if verdict else
             "the live book does NOT reproduce the canon's depth gates; DO NOT ARM"))
    if not verdict:
        bad = ok[~ok.gates_agree].head(5)
        if len(bad):
            print("\n  first disagreements:")
            print(bad[["ts", "direction"] + [f"d_{k}" for k in FEATS]].to_string(index=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
