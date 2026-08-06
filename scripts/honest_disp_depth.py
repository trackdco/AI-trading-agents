#!/usr/bin/env python3
"""HONEST at-close depth on displacement entries, FIT ONLY — the §7 harness.

Promoted from the sweep scratchpad per the versioned-builders convention
(docs/FINDING-displacement-sweep.md §5). Per fit trigger: signal TF bar ends at
boundary T (ts is the CLOSE label). Entry = open of first 1m bar at/after T.
Depth snapshot = archive row labeled minute T-1 — the last book state completed
BEFORE the boundary, i.e. the book at the close (causality independently verified
250/250 against the raw CSVs). Features vs the displacement entry price;
W/D/WALLSZ built exactly as l3_check_trial. Outcomes from
audit_displacement_entry.walk (2R-or-stop, EOD-hold).

KNOWN CORRECTION (verified): WALLSZ is never NaN by construction, so tables built
from it must mask depth-NaN rows explicitly — `WALLSZ.where(dep_thick.notna())` —
or 621 depth-NaN rows zero-fill into the off side. build() stores the UNMASKED
bit plus dep_thick so downstream callers can (and must) mask.

    python -m scripts.honest_disp_depth
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_displacement_entry import (  # noqa: E402
    TFMIN, TICK, NY, tf_bar, resolve_label_convention, walk)
from scripts.audit_depth_lookahead import load_depth  # noqa: E402
from scripts.build_l2_outcomes import load_bars  # noqa: E402
from src.canon.features import depth_at  # noqa: E402

PRE = (480, 570)
GOLD = (580, 630)
CACHE = ROOT / "output/honest_disp_depth.parquet"


def build(cache: bool = True) -> pd.DataFrame:
    """The full walked + honestly-depth-scored displacement frame (fit span)."""
    if cache and CACHE.exists():
        return pd.read_parquet(CACHE)
    L = pd.read_parquet(ROOT / "output/l2_outcomes_fit.parquet").copy()
    L["ts_ny"] = pd.to_datetime(L.ts, utc=True).dt.tz_convert(NY)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.sort_values("mi")
    bars_by_day = {d: g for d, g in bars.groupby(bars.mi.dt.strftime("%Y-%m-%d"))}

    conv = resolve_label_convention(L, bars_by_day)
    label = "start" if conv["start"] >= conv["close"] else "close"
    print(f"label convention: {conv} -> {label.upper()}")

    rows = []
    for day, g in L.groupby("day", sort=True):
        db = bars_by_day.get(day)
        if db is None:
            continue
        dep = load_depth("fit", day)
        for r in g.itertuples():
            m = TFMIN[r.tf]
            start = r.ts_ny if label == "start" else r.ts_ny - pd.Timedelta(minutes=m)
            b = tf_bar(db, start, m)
            if b is None:
                continue
            sgn = 1 if r.direction == "long" else -1
            stop = (b["low"] - TICK) if sgn > 0 else (b["high"] + TICK)
            nxt = db[db.mi >= b["end"]]
            if nxt.empty:
                continue
            entry_t, entry = nxt.iloc[0].mi, float(nxt.iloc[0].open)
            w = walk(db, entry_t, entry, stop, sgn, day)
            if w is None:
                continue
            hm = entry_t.hour * 60 + entry_t.minute
            sess = "pre" if PRE[0] <= hm < PRE[1] else (
                "gold" if GOLD[0] <= hm < GOLD[1] else "other")
            f = depth_at(dep, b["end"] - pd.Timedelta(minutes=1), entry,
                         r.direction) if dep is not None else {}
            rows.append({
                "day": day, "ts": r.ts, "tf": r.tf, "kind": r.kind, "status": r.status,
                "direction": r.direction, "sess": sess,
                "era": "2025" if day[:4] == "2025" else "2026",
                "T": b["end"], "entry": entry,
                "dep_thick": f.get("dep_thick", np.nan),
                "dep_wall_below_d": f.get("dep_wall_below_d", np.nan),
                "dep_wall_above_d": f.get("dep_wall_above_d", np.nan),
                "dep_wall_below_sz": f.get("dep_wall_below_sz", np.nan),
                "dep_wall_above_sz": f.get("dep_wall_above_sz", np.nan),
                **w})
    A = pd.DataFrame(rows)

    long = A.direction == "long"
    A["W"] = np.where(long, A.dep_wall_below_d.isna(), A.dep_wall_above_d.isna()).astype(float)
    A["W"] = A["W"].where(A.dep_thick.notna())
    A["D"] = pd.Series(np.where(long, A.dep_wall_above_d.notna(), A.dep_wall_below_d.notna()),
                       index=A.index).astype(float).where(A.dep_thick.notna())
    ahead_sz = np.where(long, A.dep_wall_above_sz, A.dep_wall_below_sz)
    A["ahead_sz"] = ahead_sz
    A["WALLSZ"] = ((A.D == 1) & (pd.Series(ahead_sz, index=A.index) >= 7)).astype(float)
    if cache:
        A.to_parquet(CACHE, index=False)
    return A


def main() -> None:
    A = build()
    P = A[A.risk >= 2.0].copy()
    print(f"walked {len(A):,}; population risk>=2pt {len(P):,}; "
          f"depth-evaluable {P.dep_thick.notna().sum():,}")
    for chk, sess in [("W", "pre"), ("D", "gold"), ("WALLSZ", "gold")]:
        col = P[chk].where(P.dep_thick.notna())          # the zero-fill mask, always
        for era in ("2025", "2026"):
            d = P[(P.sess == sess) & (P.era == era) & col.notna()]
            on, off = d[col.loc[d.index] == 1], d[col.loc[d.index] == 0]
            if len(on) == 0 or len(off) == 0:
                continue
            for rcol, nm in (("r_2r", "2R"), ("r_hold", "hold")):
                print(f"  {chk:<7}{sess:<5}{era}  {nm:<5} n {len(on):>5}/{len(off):>5} "
                      f"lift {on[rcol].mean() - off[rcol].mean():+.3f}")


if __name__ == "__main__":
    main()
