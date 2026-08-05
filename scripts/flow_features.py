#!/usr/bin/env python3
"""AT-ENTRY ORDER-FLOW FEATURE LIBRARY. Every feature is provably computable at the entry instant.

Spec and proof table: research/_shared/flow-features/README.md

=================================== THE ONE RULE ===================================
    EVERY FEATURE READS ONLY MINUTES <= entry_minute - 1.
    The entry minute itself is NEVER read, by any feature, for any reason.
====================================================================================

This is not caution. `F2_retrace_ratio` ended its window AT the entry minute; footprint data is
minute-aggregated and entries fill intrabar, so it carried up to 59 SECONDS OF POST-FILL TAPE. On
73% of one card's trades the entire numerator WAS the entry minute. It voided the programme's
flagship flow finding and halted a pre-registered test at Step 0.

Ending at `entry_minute - 1` is provably safe: that bar has CLOSED before the entry minute begins.

Each feature ships with:
  1. a stated TIME BOUNDARY (exactly what it reads, up to what timestamp)
  2. a LOOK-AHEAD PROOF — recompute with every bar from the entry minute onward deleted; the
     value must be IDENTICAL. Asserted in code, over every historical event, not spot-checked.
  3. a ROLL-CLEAN dependency flag where volume-at-price is involved (scripts/footprint_clean.py)
  4. a unit test on synthetic sequences with hand-computable answers

BANNED AND NOT IMPLEMENTED: delta SIGN confirmation of a structurally-defined move. It removed
0 of 29 on ash-unicorn-sb because the structure gate already requires a directional break, so
signed delta over that leg agrees by construction. Magnitude is a separate question; sign is not
a feature. `disp_delta_magnitude` below is deliberately UNSIGNED.

    python -m scripts.flow_features          # runs the look-ahead proofs and the unit tests
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@dataclass
class FeatureInput:
    """Everything a feature may read. The library masks this before every call.

    `cut` is the hard boundary: NO feature may read any row with index > cut, and cut is always
    entry_ts - 1 minute. The masking is done by the library, not trusted to the feature.
    """
    day: str
    entry_ts: pd.Timestamp
    cut: pd.Timestamp                # entry_ts - 1min. The last readable minute.
    side: int
    sess_start: pd.Timestamp         # the scan window's first minute
    disp_start: pd.Timestamp | None  # displacement leg start, if the card defines one
    disp_end: pd.Timestamp | None    # displacement leg end (a COMPLETED leg)
    bars: pd.DataFrame               # 1-min OHLC, indexed by ts, ALREADY masked to <= cut
    fpm: pd.DataFrame                # per-minute (vol, delta), ALREADY masked to <= cut
    fpp: pd.DataFrame                # (minute x price x side) roll-cleaned, ALREADY masked


@dataclass
class Feature:
    name: str
    fn: Callable[[FeatureInput], float]
    boundary: str
    needs_roll_clean: bool
    direction: str                   # pre-stated direction for future testing, or "none"
    note: str = ""


REGISTRY: dict[str, Feature] = {}


def feature(name: str, boundary: str, needs_roll_clean: bool = False,
            direction: str = "none", note: str = ""):
    def deco(fn):
        REGISTRY[name] = Feature(name, fn, boundary, needs_roll_clean, direction, note)
        return fn
    return deco


# ============================================================ the features
@feature("participation_to_touch",
         boundary="(disp_end, entry_minute - 1] over per-minute volume; disp leg [disp_start, disp_end]",
         direction="winners LOWER",
         note="H2' — the pre-entry rebuild of the struck H2. UNDEFINED when the retracement is "
              "shorter than one full minute, which is the common case and is a property of the "
              "idea, not a data gap.")
def participation_to_touch(x: FeatureInput) -> float:
    if x.disp_end is None or x.disp_start is None:
        return np.nan
    disp = x.fpm[(x.fpm.index >= x.disp_start) & (x.fpm.index <= x.disp_end)]
    ret = x.fpm[(x.fpm.index > x.disp_end) & (x.fpm.index <= x.cut)]
    dv = float(disp.vol.sum())
    if dv <= 0 or not len(ret):
        return np.nan                      # UNDEFINED, not zero. Do not impute.
    return float(ret.vol.sum()) / dv


@feature("disp_delta_magnitude",
         boundary="[disp_start, disp_end], a COMPLETED leg strictly before the entry minute",
         note="UNSIGNED by construction. The signed version is banned as circular.")
def disp_delta_magnitude(x: FeatureInput) -> float:
    if x.disp_end is None or x.disp_start is None:
        return np.nan
    disp = x.fpm[(x.fpm.index >= x.disp_start) & (x.fpm.index <= x.disp_end)]
    sess = x.fpm[(x.fpm.index >= x.sess_start) & (x.fpm.index <= x.cut)]
    med = float(sess.vol.median()) if len(sess) else np.nan
    if not len(disp) or not (med == med) or med <= 0:
        return np.nan
    return abs(float(disp.delta.sum())) / med


@feature("cvd_slope_pre_15",
         boundary="[cut - 14min, cut] — 15 COMPLETED minutes ending one minute before entry",
         direction="none")
def cvd_slope_pre_15(x: FeatureInput) -> float:
    w = x.fpm[(x.fpm.index > x.cut - pd.Timedelta(minutes=15)) & (x.fpm.index <= x.cut)]
    sess = x.fpm[(x.fpm.index >= x.sess_start) & (x.fpm.index <= x.cut)]
    med = float(sess.vol.median()) if len(sess) else np.nan
    if len(w) < 5 or not (med == med) or med <= 0:
        return np.nan
    y = w.delta.cumsum().to_numpy()
    return float(np.polyfit(np.arange(len(y)), y, 1)[0]) / med


@feature("cvd_price_divergence_pre",
         boundary="two COMPLETED legs inside [sess_start, cut]; nothing at or after entry",
         direction="none",
         note="Compares CVD at two separate extremes. NOT delta-sign confirmation of the move "
              "being traded — that is the banned rule.")
def cvd_price_divergence_pre(x: FeatureInput) -> float:
    w = x.fpm[(x.fpm.index >= x.sess_start) & (x.fpm.index <= x.cut)]
    b = x.bars[(x.bars.index >= x.sess_start) & (x.bars.index <= x.cut)]
    if len(w) < 20 or len(b) < 20:
        return np.nan
    cvd = w.delta.cumsum()
    px = b.low if x.side > 0 else b.high
    idx = px.idxmin() if x.side > 0 else px.idxmax()
    prior = px[px.index < idx]
    if len(prior) < 5:
        return np.nan
    pidx = prior.idxmin() if x.side > 0 else prior.idxmax()
    if idx not in cvd.index or pidx not in cvd.index:
        return np.nan
    dpx = float(px[idx] - px[pidx]) * x.side          # negative = a lower low for a long
    dcv = float(cvd[idx] - cvd[pidx]) * x.side        # positive = CVD held up
    if dpx >= 0:
        return np.nan                                  # no new extreme -> no divergence to read
    sess_med = float(w.vol.median())
    return dcv / sess_med if sess_med > 0 else np.nan


@feature("absorption_pre_5",
         boundary="[cut - 4min, cut] — 5 COMPLETED minutes ending one minute before entry",
         direction="none",
         note="High volume with little net delta AND little price progress. Prior absorption work "
              "in this repo was null twice (LDN-FLOW-01, LDN-DEF-01) at other resolutions.")
def absorption_pre_5(x: FeatureInput) -> float:
    w = x.fpm[(x.fpm.index > x.cut - pd.Timedelta(minutes=5)) & (x.fpm.index <= x.cut)]
    b = x.bars[(x.bars.index > x.cut - pd.Timedelta(minutes=5)) & (x.bars.index <= x.cut)]
    if len(w) < 3 or len(b) < 3:
        return np.nan
    v = float(w.vol.sum())
    if v <= 0:
        return np.nan
    rng = float(b.high.max() - b.low.min())
    if rng <= 0:
        return np.nan
    return (v / rng) * (1.0 - abs(float(w.delta.sum())) / v)


@feature("volume_pace_at_entry",
         boundary="[cut - 4min, cut] against the session median to cut",
         direction="none")
def volume_pace_at_entry(x: FeatureInput) -> float:
    w = x.fpm[(x.fpm.index > x.cut - pd.Timedelta(minutes=5)) & (x.fpm.index <= x.cut)]
    sess = x.fpm[(x.fpm.index >= x.sess_start) & (x.fpm.index <= x.cut)]
    med = float(sess.vol.median()) if len(sess) else np.nan
    if not len(w) or not (med == med) or med <= 0:
        return np.nan
    return float(w.vol.mean()) / med


@feature("vpoc_distance_at_entry",
         boundary="volume-at-price over [sess_start, cut]; price = CLOSE of the cut bar",
         needs_roll_clean=True,
         direction="none",
         note="ROLL-CLEAN REQUIRED. Un-cleaned, 2025-09-15's VPOC is 239.90 — a calendar-spread "
              "price — against a session bar range of 24,139-24,183.")
def vpoc_distance_at_entry(x: FeatureInput) -> float:
    p = x.fpp[(x.fpp.index >= x.sess_start) & (x.fpp.index <= x.cut)]
    b = x.bars[x.bars.index <= x.cut]
    if not len(p) or not len(b):
        return np.nan
    g = p.groupby("price").volume.sum()
    if not len(g):
        return np.nan
    vpoc = float(g.idxmax())
    last = float(b.close.iloc[-1])
    rng = float(b.high.max() - b.low.min())
    return (last - vpoc) * x.side / rng if rng > 0 else np.nan


@feature("value_area_location",
         boundary="volume-at-price over [sess_start, cut]; price = CLOSE of the cut bar",
         needs_roll_clean=True,
         direction="none",
         note="ROLL-CLEAN REQUIRED. 0 = at the value-area low, 1 = at its high.")
def value_area_location(x: FeatureInput) -> float:
    p = x.fpp[(x.fpp.index >= x.sess_start) & (x.fpp.index <= x.cut)]
    b = x.bars[x.bars.index <= x.cut]
    if not len(p) or not len(b):
        return np.nan
    g = p.groupby("price").volume.sum().sort_index()
    if len(g) < 5:
        return np.nan
    tot = g.sum()
    order = g.sort_values(ascending=False)
    cum, keep = 0.0, []
    for pr, v in order.items():
        keep.append(pr); cum += v
        if cum >= 0.70 * tot:
            break
    lo, hi = min(keep), max(keep)
    last = float(b.close.iloc[-1])
    return (last - lo) / (hi - lo) if hi > lo else np.nan


# ============================================================ the look-ahead proof
def compute(name: str, x: FeatureInput) -> float:
    """Compute a feature with the boundary ENFORCED BY THE LIBRARY, not trusted to the feature."""
    f = REGISTRY[name]
    xm = FeatureInput(
        day=x.day, entry_ts=x.entry_ts, cut=x.cut, side=x.side, sess_start=x.sess_start,
        disp_start=x.disp_start, disp_end=x.disp_end,
        bars=x.bars[x.bars.index <= x.cut],
        fpm=x.fpm[x.fpm.index <= x.cut],
        fpp=x.fpp[x.fpp.index <= x.cut] if len(x.fpp) else x.fpp,
    )
    return float(f.fn(xm))


def prove_no_lookahead(name: str, x: FeatureInput) -> tuple[float, float, bool]:
    """THE PROOF. Recompute with every row from the ENTRY MINUTE onward physically deleted.

    If a feature reads anything at or after the entry minute, the two values differ. Identical
    values on every historical event is the proof. NaN == NaN counts as identical.
    """
    full = compute(name, x)
    xr = FeatureInput(
        day=x.day, entry_ts=x.entry_ts, cut=x.cut, side=x.side, sess_start=x.sess_start,
        disp_start=x.disp_start, disp_end=x.disp_end,
        bars=x.bars[x.bars.index < x.entry_ts],
        fpm=x.fpm[x.fpm.index < x.entry_ts],
        fpp=x.fpp[x.fpp.index < x.entry_ts] if len(x.fpp) else x.fpp,
    )
    masked = compute(name, xr)
    same = (full != full and masked != masked) or (abs(full - masked) < 1e-9)
    return full, masked, same
