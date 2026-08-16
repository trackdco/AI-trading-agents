#!/usr/bin/env python3
"""IN-TRADE EARLY-EXIT FEATURES — can junk be spotted in the first N minutes
AFTER ENTRY, using only information available at that moment?

Builds, for every fight in race_wide.parquet and every horizon
N in HORIZONS (minutes elapsed since entry), a snapshot of what a trader
watching the tape would know at exactly entry+N: excursion so far
(favourable/adverse), whether it has gone green, whether it has come back
through entry, bar-range and volume activity vs the pre-entry baseline,
cumulative footprint delta oriented to the trade, and distance/drift of the
15m trigger MA. Also carries whether the fight's OWN ORIGINAL STOP has
already fired by minute N (a trader watching would know this too).

NO-LOOKAHEAD DISCIPLINE (see docs/intrade-exit.md for the full argument):
  * The walk starts at j0 = the entry bar (same convention as
    scripts/race_runs.py's day_runs — the established idiom for this
    family) and advances one 1m bar at a time.
  * At each bar the ORIGINAL stop is checked FIRST. Once hit, the walk
    FREEZES: every later horizon for that fight reuses the frozen
    snapshot (the position is closed — there is nothing more to know).
    This is the fix that keeps "has it gone green" from being outcome-ish
    for short horizons: a fight that spikes green post-stop-touch does NOT
    get credit for it, because by then the trader watching would already
    be flat.
  * Nothing at position j0+k (k>N) is ever read to build the N-snapshot —
    the per-bar loop only ever advances to j0+N and returns.
  * The pre-entry baseline (volume, bar range) uses ONLY bars strictly
    before j0. The 15m MA is `bb_ma_asof`, which levels.py documents as
    as-of-bar-close and gates for lookahead elsewhere in this repo.

    python -m scripts.intrade_exit_features
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402

OUT = ROOT / "output/htf_ma_census/race_intrade_features.parquet"
WIDE = ROOT / "output/htf_ma_census/race_wide.parquet"
FP = ROOT / "output/fp_minutes_full.parquet"
HORIZONS = [1, 2, 3, 5, 10]
BASE_WINDOW = 30          # minutes of pre-entry history for the baseline


def day_features(bars: pd.DataFrame, fpd: pd.DataFrame | None, sess_day: str,
                  rows: list[dict]) -> list[dict]:
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return []
    idx = seg.index
    hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
    vol = seg.volume.to_numpy()
    N = len(idx)

    ma15, _ = bb_ma_asof(hist, 15)          # causal as-of-bar-close (levels.py)
    ma15_1m = ma15.reindex(idx).to_numpy()

    if fpd is not None and len(fpd):
        delta_1m = fpd["delta"].reindex(idx).to_numpy()
    else:
        delta_1m = np.full(N, np.nan)
    delta_ok = np.isfinite(delta_1m)
    delta_1m = np.where(delta_ok, delta_1m, 0.0)

    max_h = max(HORIZONS)
    hset = set(HORIZONS)
    out = []
    for r in rows:
        t = pd.Timestamp(r["t"])
        j0 = int(np.searchsorted(idx.values, t.to_datetime64()))
        if j0 >= N:
            continue
        d = int(r["direction"])
        entry, stop = float(r["entry"]), float(r["stop"])
        risk = abs(entry - stop)
        if risk <= 0:
            continue

        # ---- pre-entry baseline, bars strictly before j0 only
        a0 = max(j0 - BASE_WINDOW, 0)
        if j0 > a0:
            base_vol = float(np.mean(vol[a0:j0]))
            base_range_r = float(np.mean((hi[a0:j0] - lo[a0:j0]) / risk))
            base_fp_ok = float(np.mean(delta_ok[a0:j0])) if fpd is not None else 0.0
        else:
            base_vol = base_range_r = np.nan
            base_fp_ok = 0.0

        rec = {"scid": r["scid"], "sess_day": sess_day, "mech": r["mech"],
               "session": r["session"], "direction": d,
               "base_vol": base_vol, "base_range_r": base_range_r,
               "fp_coverage_pre": base_fp_ok}

        mfe = mae = 0.0
        close_r = 0.0
        cum_delta = 0.0
        sum_rng = 0.0
        sum_vol = 0.0
        red_bars = 0
        n_bars = 0
        stop_j = None
        snap = {}

        jend = min(j0 + max_h, N - 1)
        for j in range(j0, jend + 1):
            k = j - j0                          # minutes elapsed at this bar's close
            adv = d * ((hi[j] if d > 0 else lo[j]) - entry) / risk
            adverse = d * ((lo[j] if d > 0 else hi[j]) - entry) / risk
            mfe = max(mfe, adv)
            mae = min(mae, adverse)
            close_r = d * (cl[j] - entry) / risk
            if close_r < 0:
                red_bars += 1
            sum_rng += (hi[j] - lo[j]) / risk
            sum_vol += vol[j]
            cum_delta += delta_1m[j] * d
            n_bars += 1
            # same-bar convention (matches race_realexit/race_runs): the
            # ORIGINAL stop is checked for THIS bar before the snapshot is
            # written, so a stop firing exactly on the bar that closes a
            # horizon window is correctly reflected as "already stopped"
            # at that same horizon (not one bar later).
            stopped_now = (lo[j] <= stop) if d > 0 else (hi[j] >= stop)
            if stopped_now:
                stop_j = j

            if k in hset:
                snap[k] = dict(
                    exc_fav=mfe, exc_adv=mae, close_r=close_r,
                    frac_red=red_bars / n_bars, mean_rng=sum_rng / n_bars,
                    sum_vol=sum_vol, n_bars=n_bars, cum_delta=cum_delta,
                    dist_ma15=d * (cl[j] - ma15_1m[j]) / risk
                    if np.isfinite(ma15_1m[j]) else np.nan,
                    ma15_move=d * (ma15_1m[j] - ma15_1m[j0]) / risk
                    if np.isfinite(ma15_1m[j]) and np.isfinite(ma15_1m[j0]) else np.nan,
                    stopped=stopped_now, resolved_early=stopped_now)

            if stopped_now:
                for h in HORIZONS:
                    if h not in snap:
                        snap[h] = dict(
                            exc_fav=mfe, exc_adv=mae, close_r=close_r,
                            frac_red=red_bars / n_bars, mean_rng=sum_rng / n_bars,
                            sum_vol=sum_vol, n_bars=n_bars, cum_delta=cum_delta,
                            dist_ma15=d * (cl[j] - ma15_1m[j]) / risk
                            if np.isfinite(ma15_1m[j]) else np.nan,
                            ma15_move=d * (ma15_1m[j] - ma15_1m[j0]) / risk
                            if np.isfinite(ma15_1m[j]) and np.isfinite(ma15_1m[j0]) else np.nan,
                            stopped=True, resolved_early=True)
                break
            if j == N - 1:
                for h in HORIZONS:
                    if h not in snap:
                        snap[h] = dict(
                            exc_fav=mfe, exc_adv=mae, close_r=close_r,
                            frac_red=red_bars / n_bars, mean_rng=sum_rng / n_bars,
                            sum_vol=sum_vol, n_bars=n_bars, cum_delta=cum_delta,
                            dist_ma15=d * (cl[j] - ma15_1m[j]) / risk
                            if np.isfinite(ma15_1m[j]) else np.nan,
                            ma15_move=d * (ma15_1m[j] - ma15_1m[j0]) / risk
                            if np.isfinite(ma15_1m[j]) and np.isfinite(ma15_1m[j0]) else np.nan,
                            stopped=False, resolved_early=True)
                break

        for h in HORIZONS:
            s = snap.get(h)
            pfx = f"h{h}_"
            if s is None:            # should not happen, defensive
                for kk in ("exc_fav", "exc_adv", "close_r", "frac_red",
                           "mean_rng", "sum_vol", "n_bars", "cum_delta",
                           "dist_ma15", "ma15_move"):
                    rec[pfx + kk] = np.nan
                rec[pfx + "stopped"] = np.nan
                rec[pfx + "resolved_early"] = np.nan
                continue
            rec[pfx + "exc_fav_r"] = s["exc_fav"]
            rec[pfx + "exc_adv_r"] = s["exc_adv"]
            rec[pfx + "close_r"] = s["close_r"]
            rec[pfx + "green_ever"] = bool(s["exc_fav"] > 0)
            rec[pfx + "green_now"] = bool(s["close_r"] > 0)
            rec[pfx + "back_thru_entry"] = bool(s["exc_fav"] > 0 and s["close_r"] <= 0)
            rec[pfx + "frac_red_bars"] = s["frac_red"]
            rec[pfx + "mean_bar_range_r"] = s["mean_rng"]
            rec[pfx + "range_vs_base"] = (s["mean_rng"] / base_range_r
                                          if np.isfinite(base_range_r) and base_range_r > 0
                                          else np.nan)
            rec[pfx + "vol_ratio"] = ((s["sum_vol"] / s["n_bars"]) / base_vol
                                      if np.isfinite(base_vol) and base_vol > 0
                                      else np.nan)
            rec[pfx + "delta_share"] = (s["cum_delta"] / s["sum_vol"]
                                        if s["sum_vol"] > 0 else np.nan)
            rec[pfx + "dist_ma15_r"] = s["dist_ma15"]
            rec[pfx + "ma15_move_r"] = s["ma15_move"]
            rec[pfx + "already_stopped"] = bool(s["stopped"])
            rec[pfx + "resolved_early"] = bool(s["resolved_early"])
            rec[pfx + "n_bars"] = int(s["n_bars"])
        out.append(rec)
    return out


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    B = pd.read_parquet(WIDE)
    B["t"] = pd.to_datetime(B.t)
    fp = pd.read_parquet(FP).sort_index()

    rows = B[["scid", "sess_day", "t", "direction", "entry", "stop",
              "mech", "session"]].to_dict("records")
    days = sorted(B.sess_day.unique())
    res = []
    for k, day in enumerate(days):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        fpd = fp[(fp.index >= t0) & (fp.index < t0 + pd.Timedelta(hours=23))]
        dr = [r for r in rows if r["sess_day"] == day]
        res.extend(day_features(bars, fpd if len(fpd) else None, day, dr))
        if k % 40 == 0:
            print(f"  {k}/{len(days)}...", flush=True)
    F = pd.DataFrame(res)
    F.to_parquet(OUT, index=False)
    print(f"written: {OUT.name} ({len(F):,} rows, {F.shape[1]} cols)")

    print(f"\nfights with fp coverage pre-entry >0: "
          f"{(F.fp_coverage_pre > 0).mean()*100:.1f}%")
    for h in HORIZONS:
        print(f"  h={h:2d}: green_ever {F[f'h{h}_green_ever'].mean()*100:5.1f}%  "
              f"already_stopped {F[f'h{h}_already_stopped'].mean()*100:5.1f}%  "
              f"back_thru_entry {F[f'h{h}_back_thru_entry'].mean()*100:5.1f}%")


if __name__ == "__main__":
    main()
