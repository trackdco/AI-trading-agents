#!/usr/bin/env python3
"""Record LDN-WIN-01 into the machine trial ledger.

§6.0.2 (BRAKE 2026-08-05): "Trials recorded in prose only do not exist for
deflation purposes — record both, at trial time." LDN-WIN-01 was run and written
up before that ruling landed, so it exists only in prose
(`research/findings/london-window-LDN-WIN-01.md`). This puts it on the record.

The study reported medians per 30-min bucket, which is not a t-testable
statistic. So rather than back-fit a number to the prose, this recomputes the
declared H1 comparison as a proper paired test — per day, mean realised range in
02:00-05:00 ET minus mean realised range in 05:00-06:00 ET — and records that.

Recording it even though it is a structural measurement rather than a P&L trial:
over-recording is safe, under-recording is precisely the failure §6.0.2 exists to
prevent. Whether a descriptive window study belongs in the DSR denominator is
Brake's call against his graders; it cannot be his call if the row isn't there.

    python -m scripts.london_window_ledger [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger

BARS = ROOT / "data/reference/nq_1m_master.parquet"
PREREG = "docs/PREREG-london-window-study.md"
FAMILY = "LDN-WIN-01"


def per_day_difference() -> pd.DataFrame:
    """Per day: mean 30-min realised range in 02:00-05:00 ET minus 05:00-06:00 ET."""
    bars = pd.read_parquet(BARS)
    bars["ts_event"] = pd.to_datetime(bars["ts_event"])
    bars["day"] = bars["ts_event"].dt.strftime("%Y-%m-%d")
    bars["minute"] = bars["ts_event"].dt.hour * 60 + bars["ts_event"].dt.minute
    window = bars[(bars["minute"] >= 120) & (bars["minute"] < 360)].copy()
    window["bucket"] = (window["minute"] // 30) * 30

    agg = window.groupby(["day", "bucket"]).agg(hi=("high", "max"), lo=("low", "min"))
    agg["rng"] = agg["hi"] - agg["lo"]
    agg = agg.reset_index()

    his = agg[agg["bucket"] < 300].groupby("day")["rng"].mean()      # 02:00-05:00
    tail = agg[agg["bucket"] >= 300].groupby("day")["rng"].mean()    # 05:00-06:00
    out = pd.DataFrame({"his": his, "tail": tail}).dropna()
    out["diff"] = out["his"] - out["tail"]
    out["era"] = out.index.str[:4]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    frame = per_day_difference()
    rows = []
    for era in ("2025", "2026"):
        sel = frame[frame["era"] == era]["diff"]
        n = len(sel)
        if n < 2:
            continue
        mean = float(sel.mean())
        se = float(sel.std(ddof=1)) / math.sqrt(n)
        t = mean / se if se else 0.0
        rows.append({
            "family": FAMILY,
            "trial": "H1 range 0200-0500 minus 0500-0600",
            "era": era,
            "prereg": PREREG,
            "stat_type": "mean",
            "estimate": round(mean, 3),
            "n": n,
            "t_stat": round(t, 4),
            "effect": round(trial_ledger.effect_from_t(t, n), 6),
            "verdict": (
                "structural measurement, not a P&L trial; H1 supported both eras "
                "(2026 margin negligible), H2 failed — event-anchoring lost to the "
                "wall clock because euro_open_det is noise "
                "(docs/FINDING-euro-open-det-is-noise.md)"
            ),
        })

    for r in rows:
        print(f"  {r['era']}  n={r['n']:>4}  mean={r['estimate']:+7.2f} pts  "
              f"t={r['t_stat']:+7.3f}  effect={r['effect']:+.4f}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    existing = trial_ledger.load()
    if not existing.empty and (existing["family"] == FAMILY).any():
        print(f"\n{FAMILY} already in the ledger — append-only, not re-recording.")
        return 0

    trial_ledger.record(rows)
    print(f"\nrecorded {len(rows)} trials\n")
    print(trial_ledger.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
