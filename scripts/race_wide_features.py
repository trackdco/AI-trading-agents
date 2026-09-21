#!/usr/bin/env python3
"""WIDE FEATURE TABLE for the agent sweep — every decision-time variable
we can derive, on the corrected (episode-M1) race census.

CAUSALITY RULE, enforced by construction: every column is computed from
information available at the DECISION MINUTE p (the bar whose close is
at t; entry is the next 1m open). Nothing reads a bar at or after entry.
The one deliberate exception is the outcome block (out/hit/mfe), which
is the thing being predicted and is named as such.

Also emits the frozen split-half assignment (seed 20260807, day-level)
used by the declared survival rule.

    python -m scripts.race_wide_features [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.race_diagnose import cluster                           # noqa: E402
from scripts.trigger_race_census import (MENU, SESSIONS, TOLW,      # noqa: E402
                                         m1_episode_arrays)
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

OUTP = ROOT / "output/htf_ma_census/race_outcomes_epi.parquet"
CENP = ROOT / "output/htf_ma_census/race_fit_m1episode.parquet"
FLOWP = ROOT / "output/htf_ma_census/race_flow_feats_entry.parquet"
WIDE = ROOT / "output/htf_ma_census/race_wide.parquet"
SEED = 20260807


def day_features(bars, sess_day, rows):
    """Per-row decision-time context for one session day."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                & (bars.index < t1)]
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return {}
    idx = seg.index
    hi, lo, cl, op = (seg.high.to_numpy(), seg.low.to_numpy(),
                      seg.close.to_numpy(), seg.open.to_numpy())
    vol = seg.volume.to_numpy().astype(float)
    N = len(idx)
    ma15, w15 = bb_ma_asof(hist, 15)
    ma15_1m = ma15.reindex(idx).to_numpy()
    w15_1m = w15.reindex(idx).to_numpy()
    ma60, w60 = bb_ma_asof(hist, 60)
    ma60_1m = ma60.reindex(idx).to_numpy()
    w60_1m = w60.reindex(idx).to_numpy()
    armed1, epi1 = m1_episode_arrays(hi, lo, cl, ma15_1m, w15_1m)
    vw = vwap_bands(hist)
    prof = profile_at_minutes(hist, list(idx + pd.Timedelta(minutes=1)))
    S = {"poc": prof["poc"].to_numpy(), "val": prof["val"].to_numpy(),
         "vah": prof["vah"].to_numpy()}
    for b in ("vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2",
              "vwap_p3", "vwap_m3"):
        S[b] = vw[b].reindex(idx).to_numpy()
    sd_1m = vw["vwap_sd"].reindex(idx).to_numpy()

    # rolling / cumulative context, all causal (shift where needed)
    s = pd.Series(cl, index=idx)
    rng1 = pd.Series(hi - lo, index=idx)
    atr30 = rng1.rolling(30, min_periods=10).mean().to_numpy()
    rv30 = s.diff().rolling(30, min_periods=10).std().to_numpy()
    rv120 = s.diff().rolling(120, min_periods=30).std().to_numpy()
    volm30 = pd.Series(vol, index=idx).rolling(
        30, min_periods=10).mean().to_numpy()
    volm240 = pd.Series(vol, index=idx).rolling(
        240, min_periods=60).mean().to_numpy()
    cummax = pd.Series(hi, index=idx).cummax().to_numpy()
    cummin = pd.Series(lo, index=idx).cummin().to_numpy()
    # MA slopes in W units per 15 minutes
    sl15_5 = (ma15_1m - np.roll(ma15_1m, 5)) / np.where(w15_1m > 0,
                                                        w15_1m, np.nan)
    sl15_30 = (ma15_1m - np.roll(ma15_1m, 30)) / np.where(w15_1m > 0,
                                                          w15_1m, np.nan)
    sl60_30 = (ma60_1m - np.roll(ma60_1m, 30)) / np.where(w15_1m > 0,
                                                          w15_1m, np.nan)
    sl15_5[:5] = np.nan
    sl15_30[:30] = np.nan
    sl60_30[:30] = np.nan
    # overnight / prior-day context
    on = seg[seg.index < pd.Timestamp(f"{sess_day} 18:00",
                                      tz=NY) + pd.Timedelta(hours=9)]
    on_hi = float(on.high.max()) if len(on) else np.nan
    on_lo = float(on.low.min()) if len(on) else np.nan
    on_rng = on_hi - on_lo if np.isfinite(on_hi) else np.nan

    out = {}
    for r in rows:
        t = pd.Timestamp(r["t"])
        p = int(np.searchsorted(idx.values, t.to_datetime64())) - 1
        if p < 0 or p >= N:
            continue
        d = int(r["direction"])
        w = w15_1m[p]
        entry = float(r["entry"])
        risk = float(r["risk"])
        if not (np.isfinite(w) and w > 0):
            continue
        f = {}
        # --- trend / regime state
        f["ma15_slope5_w"] = sl15_5[p]
        f["ma15_slope30_w"] = sl15_30[p]
        f["ma60_slope30_w"] = sl60_30[p]
        f["slope_with_trade"] = sl15_30[p] * d
        f["ma15_vs_ma60_w"] = (ma15_1m[p] - ma60_1m[p]) / w
        f["px_vs_ma60_w"] = (cl[p] - ma60_1m[p]) / w
        f["trend_align"] = float(np.sign(ma15_1m[p] - ma60_1m[p]) == d)
        f["w15_pts"] = w
        f["w60_over_w15"] = w60_1m[p] / w if w > 0 else np.nan
        f["vwap_sd_over_w15"] = sd_1m[p] / w if w > 0 else np.nan
        # --- volatility / activity
        f["atr30_over_w"] = atr30[p] / w
        f["rv30_over_rv120"] = (rv30[p] / rv120[p]
                                if np.isfinite(rv120[p]) and rv120[p] > 0
                                else np.nan)
        f["vol30_over_vol240"] = (volm30[p] / volm240[p]
                                  if np.isfinite(volm240[p])
                                  and volm240[p] > 0 else np.nan)
        f["risk_over_w"] = risk / w
        f["risk_over_atr30"] = (risk / atr30[p]
                                if np.isfinite(atr30[p]) and atr30[p] > 0
                                else np.nan)
        # --- location within the day
        dr = cummax[p] - cummin[p]
        f["day_range_w"] = dr / w
        f["pos_in_day_range"] = ((cl[p] - cummin[p]) / dr
                                 if dr > 0 else np.nan)
        f["pos_in_range_dir"] = (((cl[p] - cummin[p]) / dr) if d > 0
                                 else ((cummax[p] - cl[p]) / dr)) \
            if dr > 0 else np.nan
        f["dist_day_high_w"] = (cummax[p] - cl[p]) / w
        f["dist_day_low_w"] = (cl[p] - cummin[p]) / w
        f["room_ahead_day_w"] = ((cummax[p] - cl[p]) if d > 0
                                 else (cl[p] - cummin[p])) / w
        f["on_range_w"] = on_rng / w if np.isfinite(on_rng) else np.nan
        f["px_vs_on_hi_w"] = (cl[p] - on_hi) / w if np.isfinite(on_hi) \
            else np.nan
        f["px_vs_on_lo_w"] = (cl[p] - on_lo) / w if np.isfinite(on_lo) \
            else np.nan
        # --- structure geometry ahead of the entry
        ahead, behind = [], []
        for k in MENU + ["vwap_p3", "vwap_m3"]:
            v = S[k][p]
            if not np.isfinite(v):
                continue
            gap = d * (v - entry)
            (ahead if gap > 0 else behind).append(abs(gap))
        f["n_struct_ahead"] = len(ahead)
        f["nearest_ahead_r"] = min(ahead) / risk if ahead else np.nan
        f["nearest_ahead_w"] = min(ahead) / w if ahead else np.nan
        f["open_space"] = float(not ahead)
        f["n_ahead_within_2r"] = sum(1 for x in ahead if x / risk <= 2)
        f["nearest_behind_r"] = min(behind) / risk if behind else np.nan
        f["struct_spread_w"] = ((max(ahead) - min(ahead)) / w
                                if len(ahead) >= 2 else np.nan)
        # --- confluence geometry, continuous (not the binary count)
        dists = [abs(S[k][p] - ma15_1m[p]) / w for k in MENU
                 if np.isfinite(S[k][p])]
        f["conf_tightness_w"] = min(dists) if dists else np.nan
        f["conf_mean_dist_w"] = float(np.mean(dists)) if dists else np.nan
        f["poc_dist_w"] = abs(S["poc"][p] - ma15_1m[p]) / w
        f["vwap_dist_w"] = abs(S["vwap"][p] - ma15_1m[p]) / w
        f["va_width_w"] = (S["vah"][p] - S["val"][p]) / w
        f["px_in_va"] = float(S["val"][p] <= cl[p] <= S["vah"][p])
        f["px_vs_poc_w"] = (cl[p] - S["poc"][p]) / w
        f["px_vs_vwap_w"] = (cl[p] - S["vwap"][p]) / w
        f["vwap_side_with_trade"] = float(
            np.sign(cl[p] - S["vwap"][p]) == d)
        # --- episode / displacement detail
        f["epi_max_w_r"] = epi1[p] if np.isfinite(epi1[p]) else np.nan
        f["px_vs_ma15_w"] = (cl[p] - ma15_1m[p]) / w
        f["abs_px_vs_ma15_w"] = abs(cl[p] - ma15_1m[p]) / w
        f["ma15_ahead_r"] = d * (ma15_1m[p] - entry) / risk
        # --- trigger candle micro-geometry (decision bar itself)
        rr = hi[p] - lo[p]
        f["bar_range_w"] = rr / w
        f["bar_body_frac"] = abs(cl[p] - op[p]) / rr if rr > 0 else np.nan
        f["bar_closeloc_dir"] = (((cl[p] - lo[p]) / rr) if d > 0
                                 else ((hi[p] - cl[p]) / rr)) \
            if rr > 0 else np.nan
        f["bar_vol_over_30"] = (vol[p] / volm30[p]
                                if np.isfinite(volm30[p]) and volm30[p] > 0
                                else np.nan)
        f["prev3_ret_w"] = (cl[p] - cl[p - 3]) / w if p >= 3 else np.nan
        f["prev3_ret_dir"] = ((cl[p] - cl[p - 3]) / w) * d if p >= 3 \
            else np.nan
        f["prev15_ret_dir"] = ((cl[p] - cl[p - 15]) / w) * d if p >= 15 \
            else np.nan
        f["n_bars_since_open"] = p
        out[r["scid"]] = f
    return out


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    E = pd.read_parquet(OUTP)
    E["t"] = pd.to_datetime(E.t)
    E["out"] = np.where(E.mech == "M1", E.m1_out, E.near_out)
    E["hit"] = np.where(E.mech == "M1", E.m1_hit, E.near_hit)
    B = cluster(E, bars)
    print(f"book: {len(B)} fights")

    C = pd.read_parquet(CENP)[["t", "mech", "dir", "aff_list", "disp_w",
                               "epi_max_w", "tie_tfs"]]
    C["t"] = pd.to_datetime(C.t)
    B = B.merge(C, on=["t", "mech", "dir"], how="left", validate="1:1")
    FL = pd.read_parquet(FLOWP)
    B = B.merge(FL, on="scid", how="left", validate="1:1")

    rows = B.to_dict("records")
    feats = {}
    days = sorted(B.sess_day.unique())
    for k, day in enumerate(days):
        dr = [r for r in rows if r["sess_day"] == day]
        feats.update(day_features(bars, day, dr))
        if k % 40 == 0:
            print(f"  {k}/{len(days)}...", flush=True)
    FT = pd.DataFrame.from_dict(feats, orient="index")
    FT.index.name = "scid"
    B = B.merge(FT.reset_index(), on="scid", how="left")

    # affirmation flags + counts
    for k in MENU:
        B[f"aff_{k}"] = B.aff_list.fillna("").str.split(",") \
            .apply(lambda xs, kk=k: kk in xs)
    B["n_tie"] = B.tie_tfs.fillna("").str.split(",") \
        .apply(lambda xs: sum(1 for x in xs if x))
    B["disp_abs_w"] = B.disp_w.abs()
    hm = B.t.dt.hour * 60 + B.t.dt.minute
    start = pd.Series(0, index=B.index)
    for nm, (a, b) in SESSIONS.items():
        start[B.session == nm] = a
    B["tmin"] = hm - start
    B["dow"] = B.t.dt.dayofweek
    B["month"] = B.t.dt.month
    B["is_long"] = (B.direction > 0).astype(int)

    # sequence / streak context (causal within day+session)
    B = B.sort_values("t").reset_index(drop=True)
    B["seq_day"] = B.groupby("sess_day").cumcount()
    B["seq_sess"] = B.groupby(["sess_day", "session"]).cumcount()
    B["prev_out_day"] = B.groupby("sess_day")["out"].shift(1)
    B["prev_out_sess"] = B.groupby(["sess_day", "session"])["out"].shift(1)
    B["day_out_so_far"] = (B.groupby("sess_day")["out"].cumsum()
                           - B["out"])
    # earlier-session result the same day (causal: LONDON informs NY)
    lon = B[B.session == "LONDON"].groupby("sess_day")["out"].sum()
    B["london_out_today"] = np.where(
        B.session == "LONDON", np.nan,
        B.sess_day.map(lon).fillna(0.0))

    # day-type join
    DT = pd.read_csv(ROOT / "output/amt_daytypes.csv")
    DT["day"] = DT["day"].astype(str)
    B["cal_day"] = B.t.dt.date.astype(str)
    B = B.merge(DT[["day", "type", "value_position", "open_vs_value",
                    "inventory_pts", "overlap"]],
                left_on="cal_day", right_on="day", how="left")
    B["daytype"] = B["type"].fillna("unknown")

    # frozen split-half, day level, seed 20260807
    rng = np.random.default_rng(SEED)
    dd = sorted(B.sess_day.unique())
    half = dict(zip(dd, rng.integers(0, 2, len(dd))))
    B["half"] = B.sess_day.map(half)

    drop = ["aff_list", "tie_tfs", "day", "type", "cal_day", "scid_y"]
    B = B.drop(columns=[c for c in drop if c in B.columns])
    B.to_parquet(WIDE, index=False)
    nfeat = sum(1 for c in B.columns if B[c].dtype.kind in "fbi")
    print(f"written: {WIDE.name}  {B.shape[0]} rows x {B.shape[1]} cols "
          f"({nfeat} numeric/bool)")
    print(f"half split: A={int((B.half == 0).sum())} "
          f"B={int((B.half == 1).sum())} over {len(dd)} days")
    print("\ncolumns:")
    print(", ".join(B.columns))


if __name__ == "__main__":
    main()
