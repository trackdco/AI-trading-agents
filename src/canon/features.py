"""Shared canon feature library (LIVE-STACK punch-list #2 — feature-library parity).

The SAME feature definitions must serve the backtest matrix builders
(`scripts/trade_matrix.py`, and the London depth path) AND the live ingestor, so a live
feature can never silently drift from the value the frozen thresholds were fit against.
These functions are the single source of truth for those definitions; both sides import
them rather than each carrying its own copy.

Copied expression-for-expression from `scripts/trade_matrix.py` (the definitions the
+$106k book was scored on). Three families so far:
  * depth      — path_eff, crosses, load_depth_day, depth_at
  * tape / CVD — tape_features (pm/op-so-far CVD+eff, d5/d15/d30, pathpos, fill_delta)
  * VWAP geom  — vwap_geometry (entry vs VWAP band, ON-range position, London sweep)

Validation: `tests/test_canon_features_parity.py` reproduces the stored
`output/trade_matrix.parquet` DEPTH columns to the decimal from the raw depth CSVs
(922/922 trades). `tests/test_canon_features_unit.py` covers tape/VWAP with hand-computed
synthetic frames; their backtest-parity check activates once `output/fp_minutes.parquet`
is restored (it is currently absent from this machine — see the ingestor build notes).
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


# --------------------------------------------------------------------------- tape / CVD
# The minute tape ("footprint minutes") carries, per closed minute of a session day:
#   sday (session-date str), delta (signed volume = CVD increment), vol (total volume),
#   vwp (per-minute VWAP proxy for path features), hm (minute-of-day = hour*60+minute),
#   and the running cum / runmin / runmax of cumulative delta over the day (no lookahead).
# `tape_features` reads the slice STRICTLY BEFORE the fill (`upto`), so it can never see
# the fill minute or later — identical truncation to scripts/trade_matrix.py.

def tape_features(upto: pd.DataFrame, direction: str, fill_ts: pd.Timestamp,
                  day_med_vol: float) -> dict:
    """At-fill tape/CVD features from the minute tape truncated before the fill.

    `upto` = the day's minute rows with index < fill_ts (must carry columns delta, vol,
    vwp, hm, cum, runmin, runmax). `day_med_vol` = the session day's median minute volume
    (for `fill_vol_rel`). Copied expression-for-expression from trade_matrix.py so the
    live ingestor's numbers equal the backtest's."""
    f: dict = {}
    is_long = direction == "long"
    pm = upto[upto.hm >= 480]                     # 08:00+ ("pre-market so far")
    op = upto[upto.hm >= 570]                     # 09:30+ ("open so far")
    if len(pm):
        f["pm_sofar_cvd"] = pm.delta.sum()
        f["pm_sofar_abscvd"] = abs(f["pm_sofar_cvd"])
        f["pm_sofar_eff"] = f["pm_sofar_cvd"] / max(pm.vol.sum(), 1)
        f["pm_sofar_crosses"] = crosses(pm.vwp)
        f["pm_sofar_patheff"] = path_eff(pm.vwp)
        f["pm_sofar_conf"] = int((f["pm_sofar_cvd"] > 0) == is_long)
    if len(op):
        f["op_sofar_cvd"] = op.delta.sum()
        f["op_sofar_eff"] = f["op_sofar_cvd"] / max(op.vol.sum(), 1)
        f["op_sofar_conf"] = int((f["op_sofar_cvd"] > 0) == is_long)
    for k in (5, 15, 30):
        w = upto[upto.index >= fill_ts - pd.Timedelta(minutes=k)]
        f[f"d{k}"] = w.delta.sum() if len(w) else np.nan
        f[f"d{k}_conf"] = int((f[f"d{k}"] > 0) == is_long) if len(w) else np.nan
    if len(upto):
        last = upto.iloc[-1]
        rng = last.runmax - last.runmin
        f["pathpos"] = (last.cum - last.runmin) / rng if rng > 0 else np.nan
        f["fill_vol_rel"] = last.vol / max(day_med_vol, 1)
        f["fill_delta"] = last.delta
        f["fill_delta_conf"] = int((last.delta > 0) == is_long)
    return f


# --------------------------------------------------------------------------- VWAP geometry
# Bars carry per closed minute: mi (minute timestamp), hm, high, low, and daily-VWAP
# bands vw / up1 (lower_1 is symmetric). `vwap_geometry` reads only bars STRICTLY BEFORE
# the fill and measures entry position vs the VWAP band, vs the overnight range, and the
# London-sweep state — copied expression-for-expression from trade_matrix.py.

def vwap_geometry(pre: pd.DataFrame, entry: float, direction: str) -> dict:
    """At-fill geometry from the day's bars before the fill (`pre`, columns mi/hm/high/low/
    vw/up1). Returns {} if there is no prior bar or VWAP is not yet anchored (NaN)."""
    f: dict = {}
    if not len(pre):
        return f
    bar = pre.iloc[-1]
    if bar.vw != bar.vw:                          # VWAP NaN (pre-anchor) -> no geometry
        return f
    sgn = 1 if direction == "long" else -1
    bw = max(bar.up1 - bar.vw, 1e-9)              # one-sigma band width
    f["ent_vs_vwap_sd"] = (entry - bar.vw) / bw
    f["ent_vs_vwap_sd_dir"] = sgn * f["ent_vs_vwap_sd"]   # + = entering with-trend vs VWAP
    onr = pre[(pre.hm >= 1080) | (pre.hm < 480)]  # overnight: 18:00-24:00 or 00:00-08:00
    if len(onr):
        hi, lo = onr.high.max(), onr.low.min()
        f["ent_on_pos"] = (entry - lo) / max(hi - lo, 1e-9)
    lon = pre[(pre.hm >= 120) & (pre.hm < 480)]   # London 02:00-08:00 ET
    if len(lon):
        post = pre[pre.hm >= 480]
        if len(post):
            f["lon_hi_swept"] = int(post.high.max() > lon.high.max())
            f["lon_lo_swept"] = int(post.low.min() < lon.low.min())
        else:
            f["lon_hi_swept"] = 0
            f["lon_lo_swept"] = 0
    return f
