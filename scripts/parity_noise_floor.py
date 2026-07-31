#!/usr/bin/env python3
"""NOISE FLOOR for the depth parity gate — how much does the VENDOR disagree with ITSELF?

Context (2026-07-31): the first real-capture parity run (box Rithmic/Sierra vs Databento
archive, day 2026-07-29) scored 93.06% gate agreement — a FAIL against the 100% bar.
Diagnosis showed the two books are the same book (77% of matched levels byte-identical,
zero systematic size bias, correct minute alignment); the disagreements concentrate where
the wall feature's argmax flips on one-instant, one-level differences (e.g. a far 7-lot
entering one snapshot's visible top-10 and not the other's — 08:38, wall moved 73pt).

That raises the question this script answers: is 93% the live feed being wrong, or the
NOISE FLOOR of sampling ANY two views of this book a split second apart? Method: build two
archive-format snapshot sets from the SAME Databento raw file — one at each minute close,
one 500ms earlier — and run the exact parity probes between them.

  * noise floor ~= the live capture's score  ->  the box's feed matches Databento as well
    as Databento matches itself; the gap is sampling jitter, not feed error. The gate's
    100% bar is then unachievable BY CONSTRUCTION against a different clock, and re-specing
    it (e.g. "within the measured noise floor") is an evidence-backed ANGUS ruling.
  * noise floor ~= 100%  ->  the live feed genuinely differs beyond timing noise; deeper
    diagnosis before anything arms.

Run on the machine holding the raw file (needs: pip install pandas pyarrow databento):

    python3 scripts/parity_noise_floor.py ~/Downloads/glbx-mdp3-20260729.mbp-10.dbn \
        --day 2026-07-29

Self-check of the probe mechanics (no raw file needed; must print 100%):

    python3 scripts/parity_noise_floor.py --selfcheck --day 2026-07-29
"""
from __future__ import annotations

import argparse
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.depth_parity import FEATS, gates, load_archive          # noqa: E402
from src.canon.features import depth_at                              # noqa: E402

NY = "America/New_York"
WINDOW = (dtime(8, 0), dtime(11, 0))


def snapshots_from_dbn(path: Path, day: str, offset_ms: int) -> pd.DataFrame:
    """Per-minute 10+10 level snapshots sampled at (minute close - offset_ms).

    Every MBP-10 record carries the full 10-level book, so the snapshot at instant T is
    simply the last record at/before T, unpacked — same convention as condense_depth."""
    import databento as db
    df = db.DBNStore.from_file(str(path)).to_df().reset_index()
    tcol = "ts_event" if "ts_event" in df.columns else "ts_recv"
    df["ts"] = pd.to_datetime(df[tcol], utc=True).dt.tz_convert(NY)
    df = df[df["ts"].dt.strftime("%Y-%m-%d") == day]
    if "instrument_id" in df.columns and df["instrument_id"].nunique() > 1:
        df = df[df["instrument_id"] == df["instrument_id"].value_counts().idxmax()]
    df = df.sort_values("ts")
    lo = pd.Timestamp(f"{day} {WINDOW[0]}", tz=NY)
    hi = pd.Timestamp(f"{day} {WINDOW[1]}", tz=NY)
    out = []
    for minute in pd.date_range(lo, hi, freq="1min"):
        cutoff = minute + pd.Timedelta(minutes=1) - pd.Timedelta(milliseconds=offset_ms)
        sub = df[df.ts < cutoff]
        if sub.empty:
            continue
        r = sub.iloc[-1]
        for i in range(10):
            for side, px, sz in (("bid", f"bid_px_{i:02d}", f"bid_sz_{i:02d}"),
                                 ("ask", f"ask_px_{i:02d}", f"ask_sz_{i:02d}")):
                p, s = r.get(px), r.get(sz)
                if p is None or pd.isna(p) or not np.isfinite(float(p)) or not s:
                    continue
                out.append({"ts": minute, "side": side,
                            "price": float(p), "size": int(s)})
    return pd.DataFrame(out)


def probe_agreement(A: pd.DataFrame, B: pd.DataFrame, label: str) -> float:
    """The exact parity probe loop over two archive-format frames."""
    minutes = sorted(set(A.ts.unique()) & set(B.ts.unique()))
    rows = []
    for m in minutes:
        a, b = A[A.ts == m], B[B.ts == m]
        mid = float(np.mean([a[a.side.str.startswith("b")].price.max(),
                             a[a.side.str.startswith("a")].price.min()]))
        if not np.isfinite(mid):
            continue
        for direction in ("long", "short"):
            fa = depth_at(a.assign(ts=m), pd.Timestamp(m), mid, direction)
            fb = depth_at(b.assign(ts=m), pd.Timestamp(m), mid, direction)
            ga, gb = gates(fa, direction), gates(fb, direction)
            rows.append({
                "agree": all((pd.isna(ga[k]) and pd.isna(gb[k])) or ga[k] == gb[k]
                             for k in ga),
                **{f"d_{k}": abs(float(fa.get(k, np.nan)) - float(fb.get(k, np.nan)))
                   for k in FEATS}})
    R = pd.DataFrame(rows)
    pct = R.agree.mean() * 100
    print(f"\n== {label} ==")
    print(f"  probes {len(R)} | GATE AGREEMENT: {pct:.2f}%")
    for k in FEATS:
        c = R[f"d_{k}"].dropna()
        if len(c):
            print(f"  {k:<20} max|Δ| {c.max():9.4f}  median {c.median():8.4f}")
    return pct


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dbn", nargs="?", type=Path, help="raw Databento MBP-10 .dbn(.zst)")
    ap.add_argument("--day", required=True)
    ap.add_argument("--offset-ms", type=int, default=500)
    ap.add_argument("--selfcheck", action="store_true",
                    help="probe the committed archive CSV against itself (must be 100%%)")
    a = ap.parse_args()

    if a.selfcheck:
        arc = load_archive(a.day)
        pct = probe_agreement(arc, arc, "SELFCHECK archive vs itself (must be 100%)")
        raise SystemExit(0 if pct == 100.0 else 1)

    if not a.dbn:
        raise SystemExit("pass the raw .dbn path (or --selfcheck)")
    print(f"sampling at minute close and close-{a.offset_ms}ms (streaming {a.dbn.name})...")
    base = snapshots_from_dbn(a.dbn, a.day, offset_ms=0)
    early = snapshots_from_dbn(a.dbn, a.day, offset_ms=a.offset_ms)
    print(f"  snapshots: {base.ts.nunique()} minutes (base) / {early.ts.nunique()} (early)")
    pct = probe_agreement(
        base, early,
        f"NOISE FLOOR vendor-vs-itself, {a.offset_ms}ms sampling skew")
    print(f"\nReference: the box capture scored 93.06% on {a.day}. If the noise floor is "
          f"in that neighbourhood, the live feed matches the vendor as well as the vendor "
          f"matches itself; if the floor is ~100%, the live feed differs beyond timing "
          f"noise. Either way this number goes to ANGUS with the parity report — the "
          f"gate's bar is his to re-spec, not ours to quietly relax.")


if __name__ == "__main__":
    main()
