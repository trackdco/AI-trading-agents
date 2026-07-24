"""Shared canon feature library (LIVE-STACK punch-list #2 — feature-library parity).

The SAME feature definitions must serve the backtest matrix builders
(`scripts/trade_matrix.py`, and the London depth path) AND the live ingestor, so a live
feature can never silently drift from the value the frozen thresholds were fit against.
These functions are the single source of truth for those definitions; both sides import
them rather than each carrying its own copy.

Extracted verbatim from `scripts/trade_matrix.py` (the definitions the +$106k book was
scored on). `tests/test_canon_features_parity.py` proves they reproduce the stored
`output/trade_matrix.parquet` depth columns to the decimal from the raw depth CSVs.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

NY = "America/New_York"


def path_eff(p: pd.Series) -> float:
    """Path efficiency of a price/VWAP series: |net move| / sum(|per-step move|).
    NaN until at least 5 non-null points (matches the backtest's min-length guard)."""
    p = p.dropna()
    if len(p) < 5:
        return np.nan
    return float(abs(p.iloc[-1] - p.iloc[0]) / max(p.diff().abs().sum(), 1e-9))


def crosses(p: pd.Series) -> float:
    """Number of mean-crossings of a series (chop proxy). NaN until >= 5 points."""
    p = p.dropna()
    if len(p) < 5:
        return np.nan
    s = np.sign(p - p.mean())
    return float((s.diff().abs() > 0).sum())


def load_depth_day(day: str) -> pd.DataFrame | None:
    """Load one NY session's long-form book snapshots (bid/ask levels per timestamp) from
    the reference depth archives, ts converted to America/New_York. None if absent."""
    for folder in ("depth_2025", "depth_2026", "depth_apr2026"):
        p = Path(f"data/reference/{folder}/nq_depth_{day}_ny.csv")
        if p.exists():
            d = pd.read_csv(p)
            d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY)
            return d
    return None


def depth_at(dep: pd.DataFrame, minute: pd.Timestamp, entry: float,
             direction: str) -> dict:
    """Order-book features as of the last snapshot at/before `minute`: thickness,
    imbalance, spread, direction-aware support/resist, nearest wall above/below
    (distance + size), and the 5-minute thickness delta. Empty dict if no snapshot.

    This is the definition the canon's depth signals (`WALLSZ`, `dep_wall_*`, thickness,
    imbalance) were validated on — the live ingestor MUST call this exact function."""
    sub = dep[dep.ts <= minute]
    if sub.empty:
        return {}
    b = sub[sub.ts == sub.ts.max()]
    bid, ask = b[b.side == "bid"], b[b.side == "ask"]
    if bid.empty or ask.empty:
        return {}
    tb, ta = bid["size"].sum(), ask["size"].sum()
    f = {"dep_thick": tb + ta, "dep_imb": (tb - ta) / max(tb + ta, 1),
         "dep_spread": ask.price.min() - bid.price.max(),
         "dep_support": tb if direction == "long" else ta,
         "dep_resist": ta if direction == "long" else tb}
    f["dep_sup_m_res"] = f["dep_support"] - f["dep_resist"]
    above, below = b[b.price > entry], b[b.price < entry]
    if len(above):
        w = above.loc[above["size"].idxmax()]
        f["dep_wall_above_d"] = float(w.price - entry)
        f["dep_wall_above_sz"] = float(w["size"])
    if len(below):
        w = below.loc[below["size"].idxmax()]
        f["dep_wall_below_d"] = float(entry - w.price)
        f["dep_wall_below_sz"] = float(w["size"])
    b5 = dep[dep.ts <= minute - pd.Timedelta(minutes=5)]
    if not b5.empty:
        f["dep_thick_d5m"] = f["dep_thick"] - b5[b5.ts == b5.ts.max()]["size"].sum()
    return f
