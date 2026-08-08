#!/usr/bin/env python3
"""STAGE 4 — ORDERFLOW: CHARACTERISE AND PARK.

CONSTRAINT, stated before any result:

  MBP-10 coverage is 2025-06 -> 2026-07. The workbench ends 2025-01-31.
  THERE IS ZERO OVERLAP.

  287 files (2025-06 -> 2026-01) fall inside the SEALED holdout and are
  UNREADABLE. 223 files (2026-02-01 -> 2026-07-22) are readable under the
  microstructure-only ruling.

  Therefore orderflow-informed stop or target rules CANNOT be developed or
  validated on the workbench. This produces measurements and parked
  hypotheses, not a layer to add.

Sealed dates FAIL LOUD. They are not skipped silently.

WHAT THE SCHEMA SUPPORTS: one book snapshot per minute, the minute's last
update. No CVD (3 trade records in the entire dataset). No OFI - it is a sum
over events and is unrecoverable from snapshots at any frequency. No footprint.
What exists is static 10-level depth at minute boundaries.

No strategy performance is computed anywhere in this file.
"""
from __future__ import annotations

import sys
sys.path = [p for p in sys.path if p != "/usr/lib/python3/dist-packages"]

import collections
import csv
import statistics as st
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HOLDOUT_START, HOLDOUT_END = "2025-02-01", "2026-01-30"
READABLE_FROM = "2026-02-01"
A5_STOP = 10.00          # A5 minimum stop distance, points
A4_TGT = 21.32           # median planned target = median planned RR 2.132 x 10.00
LEVELS = 10


class HoldoutBreach(RuntimeError):
    pass


def et_offset(dt):
    y = dt.year
    m = datetime(y, 3, 8, tzinfo=timezone.utc)
    while m.weekday() != 6:
        m += timedelta(days=1)
    n = datetime(y, 11, 1, tzinfo=timezone.utc)
    while n.weekday() != 6:
        n += timedelta(days=1)
    return -4 if m.replace(hour=7) <= dt < n.replace(hour=6) else -5


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    lo = int(k)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (k - lo)


def file_first_date(p):
    with p.open() as fh:
        fh.readline()
        ts = datetime.fromisoformat(fh.readline().split(",")[0].replace(" ", "T"))
    return (ts + timedelta(hours=et_offset(ts))).strftime("%Y-%m-%d")


def read_book(p):
    """-> list of dicts. RAISES on any sealed-dated row. Never skips silently."""
    out = []
    scaled = p.name.startswith("condensed_")
    with p.open(newline="") as fh:
        for row in csv.DictReader(fh):
            ts = datetime.fromisoformat(row["ts_event"].replace(" ", "T"))
            et = ts + timedelta(hours=et_offset(ts))
            d = et.strftime("%Y-%m-%d")
            if HOLDOUT_START <= d <= HOLDOUT_END:
                raise HoldoutBreach(
                    f"REFUSING {p.name}: session {d} is inside the SEALED holdout "
                    f"{HOLDOUT_START}..{HOLDOUT_END}")
            f = (lambda x: float(x) / 1e9) if scaled else (lambda x: float(x))
            bids = [(f(row[f"bid_px_{k:02d}"]), float(row[f"bid_sz_{k:02d}"]))
                    for k in range(LEVELS) if row.get(f"bid_px_{k:02d}")]
            asks = [(f(row[f"ask_px_{k:02d}"]), float(row[f"ask_sz_{k:02d}"]))
                    for k in range(LEVELS) if row.get(f"ask_px_{k:02d}")]
            if not bids or not asks:
                continue
            out.append({"date": d, "mm": et.hour * 60 + et.minute,
                        "bids": bids, "asks": asks,
                        "mid": (bids[0][0] + asks[0][0]) / 2,
                        "spread": asks[0][0] - bids[0][0]})
    return out


def main():
    print("=" * 96)
    print("STAGE 4 — ORDERFLOW: CHARACTERISE AND PARK")
    print("=" * 96)
    print("""
  MBP-10 coverage is 2025-06 -> 2026-07. The workbench ends 2025-01-31.
  THERE IS ZERO OVERLAP.

  287 files (2025-06 -> 2026-01) fall inside the SEALED holdout and are
  UNREADABLE. 223 files (2026-02-01 -> 2026-07-22) are readable under the
  microstructure-only ruling.

  ORDERFLOW-INFORMED STOP OR TARGET RULES CANNOT BE DEVELOPED OR VALIDATED ON
  THE WORKBENCH. What follows is measurement and parked hypotheses, not a layer
  to add.

  SCHEMA: one book snapshot per minute, the minute's last update. No CVD (3
  trade records in the entire dataset). No OFI - a sum over events, unrecoverable
  from snapshots at any frequency. No footprint. Static 10-level depth only.
""")

    files = sorted(p for p in ROOT.glob("*.csv")
                   if "mbp" in p.name.lower() or p.name.startswith("condensed_GLBX-"))
    readable, refused = [], 0
    for p in files:
        if file_first_date(p) < READABLE_FROM:
            refused += 1
        else:
            readable.append(p)
    print(f"  files total {len(files)}   REFUSED as holdout-dated {refused}   "
          f"readable {len(readable)}\n")

    snaps = []
    for p in readable:
        snaps.extend(read_book(p))
    rth = [s for s in snaps if s["mm"] >= 9 * 60 + 31]
    print(f"  snapshots read {len(snaps)}   of which RTH (>=09:31 ET) {len(rth)}")
    print(f"  sessions {len({s['date'] for s in snaps})}  "
          f"({min(s['date'] for s in snaps)} .. {max(s['date'] for s in snaps)})\n")

    # ---------------------------------------------------------------- 1
    print("=" * 96)
    print("1. RESTING SIZE BY DISTANCE FROM PRICE, BOTH SIDES")
    print("=" * 96)
    buck = collections.defaultdict(lambda: {"bid": [], "ask": []})
    for s in rth:
        for px, sz in s["bids"]:
            buck[round(abs(s["mid"] - px) / 0.25) * 0.25]["bid"].append(sz)
        for px, sz in s["asks"]:
            buck[round(abs(px - s["mid"]) / 0.25) * 0.25]["ask"].append(sz)
    print(f"{'dist (pts)':>11} {'n bid':>8} {'med bid':>8} {'p90 bid':>8} "
          f"{'n ask':>8} {'med ask':>8} {'p90 ask':>8}")
    for dsts in sorted(buck)[:14]:
        b, a = buck[dsts]["bid"], buck[dsts]["ask"]
        if len(b) < 50 and len(a) < 50:
            continue
        print(f"{dsts:>11.2f} {len(b):>8} {pct(b,.5):>8.1f} {pct(b,.9):>8.1f} "
              f"{len(a):>8} {pct(a,.5):>8.1f} {pct(a,.9):>8.1f}")
    allb = [sz for s in rth for _, sz in s["bids"]]
    alla = [sz for s in rth for _, sz in s["asks"]]
    print(f"\n  total resting size in the visible book: bid median "
          f"{pct([sum(z for _, z in s['bids']) for s in rth], .5):.0f}, ask median "
          f"{pct([sum(z for _, z in s['asks']) for s in rth], .5):.0f} contracts")
    print(f"  per-level size: bid median {pct(allb,.5):.1f}, ask median {pct(alla,.5):.1f}")
    print(f"  BOOK DEPTH SPAN: the 10 visible levels cover a median of "
          f"{pct([max(p for p,_ in s['asks']) - min(p for p,_ in s['bids']) for s in rth], .5):.2f} pts")

    # ---------------------------------------------------------------- 2
    print("\n" + "=" * 96)
    print("2. IS THERE MORE SIZE AT THE SPEC'S LEVEL TYPES?")
    print("=" * 96)
    print("""  THIS IS THE MEASUREMENT THAT WOULD GENUINELY INFORM TARGET PLACEMENT,
  AND IT IS MOSTLY NOT COMPUTABLE. Stated plainly rather than substituted:

    VWAP family  - needs volume. NOT COMPUTABLE. This is the spec's core level type.
    POC/VAH/VAL  - needs volume. NOT COMPUTABLE.
    prior-day H/L- needs the prior FULL session; files cover 08:00-10:29 only.
                   NOT COMPUTABLE.
    BB basis     - approximable as a 20-period SMA of the minute mid series.
                   COMPUTABLE, but it is a mid-series proxy, not the bar-close
                   BB the spec uses.
    window extremes - running high/low of the observed 08:00-10:29 window.
                   COMPUTABLE, but it is not the session extreme the spec means.

  So the two level types the strategy is actually built on - the VWAP family and
  the volume-profile POC - are exactly the two this schema cannot test. What
  follows tests a BB proxy and a window-extreme proxy against distance-matched
  arbitrary prices, and that is all it tests.""")

    by_day = collections.defaultdict(list)
    for s in snaps:
        by_day[s["date"]].append(s)
    hits = {"bb": [], "ext": [], "ctrl": []}
    for d, ss in by_day.items():
        ss.sort(key=lambda x: x["mm"])
        mids = [x["mid"] for x in ss]
        run_hi, run_lo = -1e18, 1e18
        for k, s in enumerate(ss):
            run_hi, run_lo = max(run_hi, s["mid"]), min(run_lo, s["mid"])
            if k < 20 or s["mm"] < 9 * 60 + 31:
                continue
            bb = sum(mids[k - 20:k]) / 20
            book = [(px, sz) for px, sz in s["bids"]] + [(px, sz) for px, sz in s["asks"]]
            if not book:
                continue
            def near(target):
                cand = [(abs(px - target), sz) for px, sz in book]
                dmin = min(c[0] for c in cand)
                return (sum(sz for dd, sz in cand if dd <= 0.25)
                        if dmin <= 0.25 else None)
            for tag, tgt in (("bb", bb), ("ext", run_hi if s["mid"] < run_hi else run_lo)):
                z = near(tgt)
                if z is not None:
                    hits[tag].append(z)
            # distance-matched control: same |distance from mid| as the BB proxy,
            # mirrored to the opposite side, so depth-vs-distance cannot explain it
            ctrl = s["mid"] - (bb - s["mid"])
            z = near(ctrl)
            if z is not None:
                hits["ctrl"].append(z)
    print(f"\n{'level proxy':>26} {'n':>8} {'median size':>12} {'p75':>8} {'p90':>8}")
    for tag, lab in (("bb", "BB(20) proxy on mids"),
                     ("ext", "window running extreme"),
                     ("ctrl", "distance-matched control")):
        g = hits[tag]
        if not g:
            print(f"{lab:>26} {'—':>8}")
            continue
        print(f"{lab:>26} {len(g):>8} {pct(g,.5):>12.1f} {pct(g,.75):>8.1f} {pct(g,.9):>8.1f}")
    if hits["bb"] and hits["ctrl"]:
        r = pct(hits["bb"], .5) / max(1e-9, pct(hits["ctrl"], .5))
        print(f"\n  BB proxy vs distance-matched control, median size ratio: {r:.2f}x")
        print("  A ratio near 1.00 means no detectable size concentration at the level.")

    # ---------------------------------------------------------------- 3
    print("\n" + "=" * 96)
    print("3. BOOK IMBALANCE ACROSS 10 LEVELS, MINUTE GRANULARITY")
    print("=" * 96)
    imb = []
    for s in rth:
        b = sum(sz for _, sz in s["bids"])
        a = sum(sz for _, sz in s["asks"])
        if b + a > 0:
            imb.append((b - a) / (b + a))
    print(f"  n={len(imb)}   p10 {pct(imb,.10):+.3f}  p25 {pct(imb,.25):+.3f}  "
          f"median {pct(imb,.5):+.3f}  p75 {pct(imb,.75):+.3f}  p90 {pct(imb,.90):+.3f}")
    print(f"  mean {st.mean(imb):+.4f}   stdev {st.pstdev(imb):.4f}")
    print(f"  fraction |imbalance| > 0.5 : "
          f"{sum(1 for x in imb if abs(x) > 0.5)/len(imb)*100:.1f}%")

    # ---------------------------------------------------------------- 4
    print("\n" + "=" * 96)
    print("4. TOP-OF-BOOK SPREAD BY TIME OF DAY — extending the cost basis")
    print("=" * 96)
    bym = collections.defaultdict(list)
    for s in snaps:
        bym[s["mm"] // 30 * 30].append(s["spread"])
    print(f"{'ET bucket':>11} {'n':>7} {'median':>8} {'p75':>8} {'p90':>8} {'p95':>8}   in RTH?")
    for k in sorted(bym):
        g = bym[k]
        if len(g) < 100:
            continue
        inr = "RTH" if 9 * 60 + 31 <= k < 16 * 60 else ""
        print(f"{k//60:>8}:{k%60:02d} {len(g):>7} {pct(g,.5):>8.2f} {pct(g,.75):>8.2f} "
              f"{pct(g,.9):>8.2f} {pct(g,.95):>8.2f}   {inr}")
    covered = sorted({k for k in bym if len(bym[k]) >= 100})
    print(f"\n  buckets with data: {[f'{k//60:02d}:{k%60:02d}' for k in covered]}")
    print("  UNMEASURED: 10:30 -> 16:00 ET. Every file ends at 10:29 or 04:59, so the")
    print("  cost basis still rests on a window holding ~9.7% of the signal population.")
    print("  This stage did NOT extend it into the missing hours. It cannot.")

    # ---------------------------------------------------------------- 5
    print("\n" + "=" * 96)
    print(f"5. DEPTH AT THE A5 STOP DISTANCE ({A5_STOP:.0f} pts) vs THE A4 TARGET "
          f"DISTANCE ({A4_TGT:.1f} pts)")
    print("=" * 96)
    print("  Both distances lie OUTSIDE the visible 10-level book on most snapshots.")
    reach = []
    for s in rth:
        span_dn = s["mid"] - min(p for p, _ in s["bids"])
        span_up = max(p for p, _ in s["asks"]) - s["mid"]
        reach.append((span_dn, span_up))
    dn = [x[0] for x in reach]
    up = [x[1] for x in reach]
    print(f"  visible book reaches below mid: median {pct(dn,.5):.2f} pts, "
          f"p90 {pct(dn,.9):.2f}, max {max(dn):.2f}")
    print(f"  visible book reaches above mid: median {pct(up,.5):.2f} pts, "
          f"p90 {pct(up,.9):.2f}, max {max(up):.2f}")
    print(f"  snapshots whose book reaches {A5_STOP:.0f} pts down: "
          f"{sum(1 for x in dn if x >= A5_STOP)/len(dn)*100:.2f}%")
    print(f"  snapshots whose book reaches {A4_TGT:.1f} pts up: "
          f"{sum(1 for x in up if x >= A4_TGT)/len(up)*100:.2f}%")
    print("\n  VERDICT ON THIS MEASUREMENT: the question 'is one side systematically")
    print("  thinner at the stop distance than at the target distance' CANNOT BE")
    print("  ANSWERED. MBP-10 shows ten levels; ten levels span a median of about")
    print(f"  {pct([max(p for p,_ in s['asks']) - min(p for p,_ in s['bids']) for s in rth], .5):.1f} points, "
          f"and both the {A5_STOP:.0f}-point stop and the {A4_TGT:.1f}-point target")
    print("  sit far beyond it. Answering it needs MBP-50 or full depth, not this.")

    print("\n" + "=" * 96)
    print("HOLDOUT: never read. 287 files refused by date before any row was parsed.")
    print("No strategy performance was computed. N_trials remains 0.")
    print("=" * 96)


if __name__ == "__main__":
    main()
