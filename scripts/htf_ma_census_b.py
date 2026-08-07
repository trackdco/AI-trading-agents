#!/usr/bin/env python3
"""CENSUS B — the M2 rejection/continuation base rate (SPEC §4). 15m reference.

Attempt: a completed 15m bar that REACHES its own BB MA intrabar (approaching
from one side) but whose CLOSE fails to cross. Consecutive count n_attempts
(1..4, each N fires once per cycle); reset on a 15m close that crosses — the
reset emits a BREAK-ARM counterfactual row. Continuation direction = AWAY from
the MA (the side price already occupies). Events stamped at the failing bar's
15m close; outcomes forward on 1m bars to the 17:00 session close, distances
measured against the MOVING as-of MA in the EVENT's W units; stop-first on
ambiguous bars.

ANGUS ruling 2026-08-07 (recorded verbatim in intent): conditioning variables
are COLUMNS, never filters — confluence count, mtf_reject_count, admissibility
snapshot, profile maturity all recorded so the later selection study reads ONE
shared feature table for both mechanisms and pays its trial count once.

Fit rows -> output/htf_ma_census/censusB_fit.parquet; 2023/24 ->
output/sealed/censusB_sealed.parquet (written, never read); 2025-01..05 ->
censusB_gray.parquet (not analysed). Same physical guard as Census A.

    python -m scripts.htf_ma_census_b [--days N]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import (NY, bb_ma_asof, vwap_bands,          # noqa: E402
                               profile_at_minutes, session_tag)

TICK = 0.25
T_SWEEP = [0.5, 1.0, 1.5, 2.0]                 # travel targets, event-W units
S_SWEEP = [10, 20, 30, 40, 60, 80]             # ticks through the MA (stop side)
MTF_TFS = [2, 3, 5, 15]
CONFL_TOL_W = 0.25
FIT_START, FIT_END = "2025-06-01", "2026-07-31"


def attempt_flags(f15: pd.DataFrame, ma_at: pd.Series):
    """Per completed 15m bar: (+1 below-approach fail, -1 above, 0 none/cross).
    below-approach: open&close below MA, high >= MA, close fails to cross."""
    ma = ma_at.reindex(f15.index).to_numpy()
    o, h, l, c = (f15[k].to_numpy() for k in ("open", "high", "low", "close"))
    below_fail = (c < ma) & (h >= ma) & (o < ma)
    above_fail = (c > ma) & (l <= ma) & (o > ma)
    cross_up = (c > ma) & (o <= ma)
    cross_dn = (c < ma) & (o >= ma)
    return below_fail, above_fail, cross_up | cross_dn


def census_day(bars: pd.DataFrame, sess_day: str) -> list[dict]:
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    if hist.empty:
        return []
    ma15, w15 = bb_ma_asof(hist, 15)
    tf_ma = {tf: bb_ma_asof(hist, tf)[0] for tf in MTF_TFS}
    ma5, _ = bb_ma_asof(hist, 5)
    ma60, _ = bb_ma_asof(hist, 60)
    vw = vwap_bands(hist)
    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    tr = np.maximum(f15.high - f15.low,
                    np.maximum((f15.high - f15.close.shift()).abs(),
                               (f15.low - f15.close.shift()).abs()))
    atr15 = tr.rolling(14).mean()
    # ma value AT each 15m close = as-of 1m row at that stamp minus 1m
    ma_at15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1))
    ma_at15.index = f15.index
    w_at15 = w15.reindex(f15.index - pd.Timedelta(minutes=1))
    w_at15.index = f15.index
    below_fail, above_fail, crossed = attempt_flags(f15, ma_at15)

    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    idx = seg.index
    hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
    ma_1m = ma15.loc[idx].to_numpy()

    # per-tf failed-state at 15m closes (last completed tf bar failed, same side)
    tf_fail: dict[int, tuple] = {}
    for tf in MTF_TFS:
        ftf = hist.resample(f"{tf}min", label="right", closed="left").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        matf = tf_ma[tf].reindex(ftf.index - pd.Timedelta(minutes=1))
        matf.index = ftf.index
        bf, af, _ = attempt_flags(ftf, matf)
        tf_fail[tf] = (ftf.index.values, bf, af)

    rows: list[dict] = []
    events_min: list[pd.Timestamp] = []
    for side_name, fail_vec, sgn in (("below", below_fail, 1), ("above", above_fail, -1)):
        # sgn=+1: approach from below fails -> continuation DOWN? NO:
        # price lives BELOW the MA; continuation (away) = DOWN = -1 direction.
        away = -1 if side_name == "below" else 1
        count, cluster = 0, 0
        for bi, tstamp in enumerate(f15.index):
            ma_e, w_e = ma_at15.iloc[bi], w_at15.iloc[bi]
            if not (np.isfinite(ma_e) and np.isfinite(w_e) and w_e > 0):
                continue
            if crossed[bi]:
                if count >= 1:
                    # BREAK ARM: the failure chain resolves by crossing
                    j0 = int(np.searchsorted(idx.values, tstamp.to_datetime64()))
                    retraced, reached_break = False, False
                    brk = 1 if f15.close.iloc[bi] > ma_e else -1
                    for j in range(j0, len(idx)):
                        m = ma_1m[j]
                        if not retraced and np.isfinite(m) and lo[j] <= m <= hi[j]:
                            retraced = True
                        if brk * (cl[j] - ma_e) / w_e >= 1.0:
                            reached_break = True
                            break
                    rows.append({"sess_day": sess_day, "t": tstamp, "kind": "break",
                                 "side": side_name, "n_attempts": count,
                                 "break_dir": "up" if brk > 0 else "down",
                                 "retraced_ma": retraced,
                                 "reached_1W_break": reached_break,
                                 "session": session_tag(tstamp),
                                 "cluster_id": f"{sess_day}:{side_name}:{cluster}"})
                count = 0
                cluster += 1
                continue
            if not fail_vec[bi]:
                continue                      # chain persists; reset only on cross
            count += 1
            if count > 4:
                continue
            # ---- rejection event at this 15m close ----
            j0 = int(np.searchsorted(idx.values, tstamp.to_datetime64()))
            trav_max = 0.0
            reached: dict[float, float] = {}
            t1w_first: dict[int, bool] = {}
            crossed_S = {S: False for S in S_SWEEP}
            t_first_cross = np.nan
            for j in range(j0, len(idx)):
                m = ma_1m[j] if np.isfinite(ma_1m[j]) else ma_e
                # stop side FIRST within the bar (conservative), then travel
                for S in S_SWEEP:
                    if not crossed_S[S]:
                        thru = (-away) * ((hi[j] if away < 0 else lo[j]) - m) / TICK
                        if thru >= S:
                            crossed_S[S] = True
                d_away = max(away * ((lo[j] if away < 0 else hi[j]) - m) / w_e, 0.0)
                trav_max = max(trav_max, d_away)
                for T in T_SWEEP:
                    if T not in reached and trav_max >= T:
                        reached[T] = (idx[j] - tstamp) / pd.Timedelta(minutes=1)
                        if T == 1.0:          # the race snapshot, per S
                            for S in S_SWEEP:
                                t1w_first[S] = not crossed_S[S]
                if not np.isfinite(t_first_cross):
                    # 1m close across the moving MA (first cross marker)
                    if (-away) * (cl[j] - m) > 0:
                        t_first_cross = (idx[j] - tstamp) / pd.Timedelta(minutes=1)
            bar = f15.iloc[bi]
            pen = (bar.high - ma_e) if side_name == "below" else (ma_e - bar.low)
            a_e = atr15.iloc[bi]
            # conditioning columns (recorded, NEVER filtered) --------------
            mtf = 0
            for tf in MTF_TFS:
                tix, bf, af = tf_fail[tf]
                k = int(np.searchsorted(tix, tstamp.to_datetime64(), side="right")) - 1
                if k >= 0 and (bf[k] if side_name == "below" else af[k]):
                    mtf += 1
            events_min.append(tstamp)
            rows.append({
                "sess_day": sess_day, "t": tstamp, "kind": "reject",
                "side": side_name, "n_attempts": count,
                "session": session_tag(tstamp),
                "cluster_id": f"{sess_day}:{side_name}:{cluster}",
                "w15": w_e, "ma_px": ma_e, "event_px": bar.close,
                "body_atr": abs(bar.close - bar.open) / a_e
                            if np.isfinite(a_e) and a_e > 0 else np.nan,
                "close_dist_bw": abs(ma_e - bar.close) / w_e,
                "pen_bw": max(pen, 0.0) / w_e,
                "wick_frac": (pen / (bar.high - bar.low))
                             if bar.high > bar.low and pen > 0 else 0.0,
                "travel_max_W": trav_max,
                **{f"reached_{T}": T in reached for T in T_SWEEP},
                **{f"t_reached_{T}": reached.get(T, np.nan) for T in T_SWEEP},
                **{f"travel1W_before_cross_{S}": t1w_first.get(S, False)
                   for S in S_SWEEP},
                "t_first_cross": t_first_cross,
                "mtf_reject_count": mtf,
                "profile_min": (tstamp - t0) / pd.Timedelta(minutes=1)})
    # confluence + admissibility snapshot + next-level columns (batch) -----
    if events_min:
        prof = profile_at_minutes(hist, sorted({m - pd.Timedelta(minutes=1)
                                                for m in events_min}))
        for r in rows:
            if r["kind"] != "reject":
                continue
            pm = r["t"] - pd.Timedelta(minutes=1)
            p = prof.loc[pm]
            vrow = vw.loc[pm] if pm in vw.index else None
            lvls = {"poc": p.poc, "vah": p.vah, "val": p.val}
            if vrow is not None:
                lvls.update({"vwap": vrow.vwap, "vwap_p1": vrow.vwap_p1,
                             "vwap_m1": vrow.vwap_m1, "vwap_p2": vrow.vwap_p2,
                             "vwap_m2": vrow.vwap_m2})
            tol = CONFL_TOL_W * r["w15"]
            r["confluence_count"] = sum(1 for v in lvls.values()
                                        if np.isfinite(v) and abs(v - r["ma_px"]) <= tol)
            away = -1 if r["side"] == "below" else 1
            ahead = [(k, v) for k, v in lvls.items() if np.isfinite(v)
                     and away * (v - r["event_px"]) > 0]
            if ahead:
                k, v = min(ahead, key=lambda kv: abs(kv[1] - r["event_px"]))
                r["next_level"], r["next_level_dist_W"] = k, abs(v - r["event_px"]) / r["w15"]
                m5 = ma5.reindex([pm]).iloc[0]
                m60 = ma60.reindex([pm]).iloc[0]
                ceil_tf, ceil_px = None, None
                for tfn, mv in (("5m", m5), ("60m", m60)):
                    if np.isfinite(mv) and min(r["event_px"], v) < mv < max(r["event_px"], v):
                        if ceil_px is None or abs(mv - r["event_px"]) < abs(ceil_px - r["event_px"]):
                            ceil_tf, ceil_px = tfn, mv
                r["ceiling_tf"] = ceil_tf or "none"
                r["admissible_snapshot"] = ceil_tf is None
            else:
                r["next_level"] = "none"
                r["next_level_dist_W"] = np.nan
                r["ceiling_tf"] = "none"
                r["admissible_snapshot"] = True
    return rows


def main() -> None:
    n_days = None
    if "--days" in sys.argv:
        n_days = int(sys.argv[sys.argv.index("--days") + 1])
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close", "volume"]]
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    if n_days:
        sess_days = sess_days[-n_days:]
    fit, sealed, gray = [], [], []
    for k, d in enumerate(sess_days):
        rows = census_day(bars, d)
        (fit if FIT_START <= d <= FIT_END else
         sealed if d < "2025-01-01" else gray).extend(rows)
        if k % 50 == 0:
            print(f"  {k}/{len(sess_days)} days...", flush=True)
    out = ROOT / "output/htf_ma_census"
    out.mkdir(parents=True, exist_ok=True)
    (ROOT / "output/sealed").mkdir(parents=True, exist_ok=True)
    if fit:
        pd.DataFrame(fit).to_parquet(out / "censusB_fit.parquet", index=False)
    if sealed:
        pd.DataFrame(sealed).to_parquet(ROOT / "output/sealed/censusB_sealed.parquet",
                                        index=False)
    if gray:
        pd.DataFrame(gray).to_parquet(out / "censusB_gray.parquet", index=False)
    print(f"censusB: fit={len(fit):,} | sealed={len(sealed):,} (written, NOT read) "
          f"| gray={len(gray):,} (not analysed)")


if __name__ == "__main__":
    main()
