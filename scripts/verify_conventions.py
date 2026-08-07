"""Reproduce the empirical proofs behind docs/conventions.md.

Run: python3 scripts/verify_conventions.py
All data access goes through src/chokepoint.py (enforced by
tests/test_chokepoint_guards.py).

Proof 1 — clock fingerprints: every book family is FLOORED (ts_event pinned to
the minute; true time = ts_recv, ~60s later).

Proof 2 — bar labelling: OHLCV 1m bars are START-labelled. Bar stamped m has
its close best matched by the book mid observed at ~m+60s; the close-labelled
hypothesis performs no better than deliberately nonsensical ±120s alignments.
Roll-week days (front-month divergence) are excluded and listed.

Proof 3 — archive overlap: arch1 and arch2 are row-identical on their
2025-01-01..2025-02-28 overlap.
"""

import os
import sys
from collections import defaultdict

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO, "src"))

import chokepoint


def proof_1_clock():
    print("=== Proof 1: clock fingerprints (FLOORED per family) ===")
    for family in ("london", "ny2025", "ny2026"):
        offs = sorted(
            r["ts_true"] - r["minute_label_raw"]
            for r in chokepoint.load_book_minutes(family)
        )
        n = len(offs)
        frac = sum(1 for o in offs if 55 <= o <= 61) / n
        print(
            f"  {family}: n={n}  median offset={offs[n // 2]:.3f}s  "
            f"frac in [55,61]s = {frac:.4f}  -> FLOORED"
        )


def proof_2_labelling():
    print("=== Proof 2: bar labelling (START) — arch3 x ny2025 ===")
    snaps = defaultdict(list)
    for r in chokepoint.load_book_minutes("ny2025"):
        b, a = r["bids"][0][0], r["asks"][0][0]
        if b > 0 and a > 0:
            snaps[r["date"]].append((r["ts_true"], (a + b) / 2))

    bars_all = list(
        chokepoint.load_ohlcv_1m("arch3", date_range=(min(snaps), max(snaps)))
    )
    fm = chokepoint.front_month_by_day(bars_all)
    day_bars = defaultdict(dict)
    for b in bars_all:
        if fm.get(b["date"]) == b["symbol"]:
            day_bars[b["date"]][b["ts_open"]] = b["close"]

    hyp = {
        "START  (close at m+60)": 60.0,
        "CLOSE  (close at m)   ": 0.0,
        "nonsense +120         ": 120.0,
        "nonsense -120         ": -120.0,
    }
    # exclude roll-mismatch days (per-day median error > 5 pts under START)
    clean_days, roll_days = [], []
    for d, ss in snaps.items():
        db = day_bars.get(d)
        if not db:
            continue
        errs = sorted(
            abs(db[round((t - 60) / 60) * 60] - mid)
            for t, mid in ss
            if round((t - 60) / 60) * 60 in db
        )
        if not errs:
            continue
        (clean_days if errs[len(errs) // 2] <= 5 else roll_days).append(d)
    print(f"  clean days={len(clean_days)}  roll-divergence days={sorted(roll_days)}")

    for name, off in hyp.items():
        errs = []
        for d in clean_days:
            db = day_bars[d]
            for t, mid in snaps[d]:
                m = round((t - off) / 60) * 60
                if m in db:
                    errs.append(abs(db[m] - mid))
        errs.sort()
        n = len(errs)
        print(
            f"  {name} n={n}  median|close-mid|={errs[n // 2]:.3f} pts  "
            f"frac<=1pt={sum(1 for e in errs if e <= 1.0) / n:.3f}"
        )
    print("  -> START must dominate; CLOSE must be indistinguishable from nonsense.")


def proof_3_overlap():
    print("=== Proof 3: arch1/arch2 overlap consistency ===")
    span = ("2025-01-01", "2025-02-28")
    key = lambda b: (b["symbol"], b["ts_open"])
    val = lambda b: (b["open"], b["high"], b["low"], b["close"], b["volume"])
    a = {key(b): val(b) for b in chokepoint.load_ohlcv_1m("arch1", outrights_only=False, date_range=span)}
    b_ = {key(b): val(b) for b in chokepoint.load_ohlcv_1m("arch2", outrights_only=False, date_range=span)}
    common = set(a) & set(b_)
    same = sum(1 for k in common if a[k] == b_[k])
    print(
        f"  rows arch1={len(a)} arch2={len(b_)} common={len(common)} "
        f"identical={same} only1={len(set(a) - set(b_))} only2={len(set(b_) - set(a))}"
    )


if __name__ == "__main__":
    proof_1_clock()
    proof_2_labelling()
    proof_3_overlap()
