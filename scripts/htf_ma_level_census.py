#!/usr/bin/env python3
"""E1 — LEVEL-FAMILY CENSUS (DECLARATIONS-level-family-census.md).

The M-TABLE indexes fights at ONE level (the 15m BB MA). This runs the
SAME fight grammar at each of the declared loci, so the trigger population
itself is the object of study rather than selection inside a fixed one.

Loci (declared, closed — a fifth needs its own declaration):
    bbma15   15m BB middle band          CONTROL / calibration
    poc      developing session POC       family 1
    val,vah  developing value area        family 2
    vwap     session VWAP                 family 3
    vwap_m1, vwap_p1   VWAP -1/+1 sd      family 4

Everything else is the incumbent, unchanged: decision at the 15m close,
entry at the next 1m open (reject) or the previous-1m as-of level (break
retest), stop at the trigger extreme, shipped exit (75% at 3R + 15m trail),
W = 15m BB width as the single scale ruler for every locus, per-1m as-of
levels. One pass per session day computes ALL loci.

    python -m scripts.htf_ma_level_census [--days N] [--locus NAME]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_mtable import flow_features                     # noqa: E402
from src.htf_ma.levels import (NY, bb_ma_asof, vwap_bands,          # noqa: E402
                               profile_at_minutes, session_tag)

TICK = 0.25
COST_PTS = 0.5
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
LOCI = ["bbma15", "poc", "val", "vah", "vwap", "vwap_m1", "vwap_p1"]
EXCL = {"no_next_open": 0, "gap_through_stop": 0, "level_nan": 0}


def level_series(hist: pd.DataFrame, seg_index: pd.DatetimeIndex,
                 ma15: pd.Series) -> dict[str, np.ndarray]:
    """Per-1m AS-OF value of every locus, aligned to seg_index.

    Row t is the level AT THE CLOSE of 1m bar t — usable for a decision at
    t+1m and never at t itself (the incumbent's convention, levels.py)."""
    out: dict[str, np.ndarray] = {}
    out["bbma15"] = ma15.reindex(seg_index).to_numpy()
    vw = vwap_bands(hist)
    for name, col in (("vwap", "vwap"), ("vwap_m1", "vwap_m1"),
                      ("vwap_p1", "vwap_p1")):
        out[name] = vw[col].reindex(seg_index).to_numpy()
    # developing profile: a bar stamped t is included for request minutes
    # STRICTLY GREATER than t, so a snapshot at t sees bars < t. Request at
    # t+1m to obtain the as-of-close-of-t value, matching the MA convention.
    req = list(seg_index + pd.Timedelta(minutes=1))
    prof = profile_at_minutes(hist, req)
    for name in ("poc", "vah", "val"):
        out[name] = prof[name].to_numpy()
    return out


def day_rows(bars: pd.DataFrame, sess_day: str,
             loci: list[str], fp: pd.DataFrame | None = None) -> list[dict]:
    """All fights at every requested locus for one 18:00-anchored session.

    fp (optional): per-minute footprint state. When supplied, the twelve
    flow features are attached to every row, computed as-of the DECISION
    BAR's close by the same `flow_features` the M-TABLE uses (imported, not
    reimplemented). The live recorder passes it; the base-rate census does
    not need it."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    if hist.empty:
        return []
    ma15, w15 = bb_ma_asof(hist, 15)
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return []
    idx = seg.index
    hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
    op = seg.open.to_numpy()
    w_1m = w15.reindex(idx).to_numpy()
    lv = level_series(hist, idx, ma15)

    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    if f15.empty:
        return []
    ma_f15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1))
    ma_f15.index = f15.index                      # trail reference (all loci)
    w_at15 = w15.reindex(f15.index - pd.Timedelta(minutes=1))
    w_at15.index = f15.index
    fpd = fp15 = None
    if fp is not None and len(fp):
        fpd = fp[(fp.index >= t0 - pd.Timedelta(hours=30)) & (fp.index < t1)]
        fp15 = fpd.resample("15min", label="right", closed="left").agg(
            {"vol": "sum", "delta": "sum"}).dropna() if len(fpd) else None

    def flow_at(tstamp, d, b_):
        if fpd is None:
            return {}
        return flow_features(fpd, tstamp - pd.Timedelta(minutes=15), tstamp,
                             d, fp15[fp15.index < tstamp]
                             if fp15 is not None else None,
                             bar_ohlc=b_, prior_ohlc=f15[f15.index < tstamp])

    def walk_exits(j0, d, entry, stop):
        """Shipped exit, identical machinery for every locus."""
        risk = abs(entry - stop)
        if risk <= 0 or j0 >= len(idx):
            return None
        cost = COST_PTS / risk
        stop_j, t3, mfe = None, None, 0.0
        for j in range(j0, len(idx)):
            if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                stop_j = j
                break
            fav = d * ((hi[j] if d > 0 else lo[j]) - entry) / risk
            mfe = max(mfe, fav)
            if t3 is None and fav >= 3.0:
                t3 = j
        eod = d * (cl[-1] - entry) / risk
        hold = -1.0 if stop_j is not None else eod
        tstop, trail, j_trail = stop, None, None
        fb2 = f15[f15.index > idx[j0]]
        fi, pos = list(fb2.index), 0
        for j in range(j0, len(idx)):
            if (lo[j] <= tstop) if d > 0 else (hi[j] >= tstop):
                trail = d * (tstop - entry) / risk
                j_trail = j
                break
            while pos < len(fi) and fi[pos] <= idx[j]:
                b_ = fb2.iloc[pos]
                m = ma_f15.get(fi[pos], np.nan)
                if np.isfinite(m) and d * (b_.close - m) > 0:
                    cand = (b_.low - TICK) if d > 0 else (b_.high + TICK)
                    if d * (cand - tstop) > 0:
                        tstop = cand
                pos += 1
        if trail is None:
            trail = eod
            j_trail = len(idx) - 1
        leg3 = (3.0 * risk - TICK) / risk if t3 is not None else None
        ship = (0.75 * leg3 + 0.25 * trail if leg3 is not None else trail) - cost
        # EXPOSURE TIMESTAMPS (item 3, risk spine): the position is open from
        # entry until the LAST leg leaves. Under the shipped exit the 75% leg
        # goes at 3R (t_3r) and the 25% remainder rides the trail to j_trail;
        # if the stop is hit before 3R the whole position leaves at stop_j.
        j_exit = stop_j if (stop_j is not None and t3 is None) else j_trail
        return {"risk": risk, "mfe_r": mfe, "out_ship": ship,
                "out_trail": trail - cost, "out_hold": hold - cost,
                "t_entry": idx[j0],
                "t_3r": idx[t3] if t3 is not None else pd.NaT,
                "t_exit": idx[j_exit] if j_exit is not None else idx[-1]}

    rows: list[dict] = []
    for locus in loci:
        l_1m = lv[locus]
        # the locus value as-of the decision bar's close
        pos15 = np.searchsorted(idx.values,
                                (f15.index - pd.Timedelta(minutes=1)).values)
        pos15 = np.clip(pos15, 0, len(idx) - 1)
        l_at15 = l_1m[pos15]
        for side_name in ("below", "above"):
            count, cluster = 0, 0
            for bi, tstamp in enumerate(f15.index):
                lvl_e, w_e = l_at15[bi], w_at15.iloc[bi]
                if not (np.isfinite(lvl_e) and np.isfinite(w_e) and w_e > 0):
                    EXCL["level_nan"] += 1
                    continue
                b_ = f15.iloc[bi]
                crossed = (b_.close > lvl_e) != (b_.open > lvl_e)
                fail = ((b_.close < lvl_e) and (b_.high >= lvl_e)
                        and (b_.open < lvl_e)) if side_name == "below" else \
                       ((b_.close > lvl_e) and (b_.low <= lvl_e)
                        and (b_.open > lvl_e))
                j0 = int(np.searchsorted(idx.values, tstamp.to_datetime64()))
                if crossed:
                    if count >= 1:
                        d = 1 if b_.close > lvl_e else -1
                        jt = None
                        for j in range(max(j0, 1), len(idx)):
                            tgt = l_1m[j - 1]      # as-of PREVIOUS 1m close
                            if np.isfinite(tgt) and lo[j] <= tgt <= hi[j]:
                                jt = j
                                break
                        entry = float(l_1m[jt - 1]) if jt is not None else np.nan
                        stop = (b_.low - TICK) if d > 0 else (b_.high + TICK)
                        w = walk_exits(jt, d, entry, stop) \
                            if jt is not None else None
                        if w is None:
                            w = {"risk": np.nan, "mfe_r": np.nan,
                                 "out_ship": np.nan, "out_trail": np.nan,
                                 "out_hold": np.nan, "t_entry": pd.NaT,
                                 "t_3r": pd.NaT, "t_exit": pd.NaT}
                        rows.append({"sess_day": sess_day, "t": tstamp,
                                     "locus": locus, "arm": "break",
                                     "side": side_name, "n_attempts": count,
                                     "direction": d,
                                     "session": session_tag(tstamp),
                                     "cluster_id": f"{sess_day}:{locus}:"
                                                   f"{side_name}:{cluster}",
                                     "entry": entry, "stop": stop,
                                     "w15": w_e, "lvl_px": lvl_e,
                                     "trig_high": b_.high, "trig_low": b_.low,
                                     "retested": jt is not None,
                                     "t_fill": idx[jt] if jt is not None
                                     else pd.NaT, **w,
                                     **flow_at(tstamp, d, b_)})
                    count = 0
                    cluster += 1
                    continue
                if not fail:
                    continue
                count += 1
                d = -1 if side_name == "below" else 1
                if j0 >= len(idx):
                    EXCL["no_next_open"] += 1
                    continue
                entry = float(op[j0])              # NEXT 1m open (entry law)
                stop = (b_.high + TICK) if d < 0 else (b_.low - TICK)
                if d * (entry - stop) <= 0:
                    EXCL["gap_through_stop"] += 1
                    continue
                w = walk_exits(j0, d, entry, stop)
                if w:
                    rows.append({"sess_day": sess_day, "t": tstamp,
                                 "locus": locus, "arm": "reject",
                                 "side": side_name, "n_attempts": count,
                                 "direction": d,
                                 "session": session_tag(tstamp),
                                 "cluster_id": f"{sess_day}:{locus}:"
                                               f"{side_name}:{cluster}",
                                 "entry": entry, "stop": stop, "w15": w_e,
                                 "lvl_px": lvl_e, "trig_high": b_.high,
                                 "trig_low": b_.low, "retested": None,
                                 "t_fill": pd.NaT, **w,
                                 **flow_at(tstamp, d, b_)})
    return rows


def main() -> None:
    n_days = None
    loci = LOCI
    if "--days" in sys.argv:
        n_days = int(sys.argv[sys.argv.index("--days") + 1])
    if "--locus" in sys.argv:
        loci = [sys.argv[sys.argv.index("--locus") + 1]]
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    if n_days:
        sess_days = sess_days[-n_days:]
    fit, sealed, gray = [], [], []
    for k, d in enumerate(sess_days):
        rows = day_rows(bars, d, loci)
        (fit if FIT_START <= d <= FIT_END else
         sealed if d < "2025-01-01" else gray).extend(rows)
        if k % 60 == 0:
            print(f"  {k}/{len(sess_days)}...", flush=True)
    out = ROOT / "output/htf_ma_census"
    out.mkdir(parents=True, exist_ok=True)
    (ROOT / "output/sealed").mkdir(parents=True, exist_ok=True)
    if fit:
        pd.DataFrame(fit).to_parquet(out / "levels_fit.parquet", index=False)
    if sealed:
        pd.DataFrame(sealed).to_parquet(
            ROOT / "output/sealed/levels_sealed.parquet", index=False)
    if gray:
        pd.DataFrame(gray).to_parquet(out / "levels_gray.parquet", index=False)
    print(f"LEVEL CENSUS: fit={len(fit):,} | sealed={len(sealed):,} "
          f"(written, NOT read) | gray={len(gray):,}")
    print(f"named exclusions: {EXCL}")
    if fit:
        F = pd.DataFrame(fit)
        print(F.groupby(["locus", "arm"]).size().to_string())


if __name__ == "__main__":
    main()
