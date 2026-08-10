#!/usr/bin/env python3
"""AGENT CONTEXT LAYER — the structure the trader actually reads that the
research build never computed.

Sourced from his two narrated days (2026-01-14 London and New York):

  weekly profile   "I have another volume profile anchored to the last
                   five trading days" — he targets weekly VAL and the
                   weekly lows, and judges rejections against them.
  NY-range fibs    "that high at 9:32 down to 10:00, so the first 30
                   minutes of the market open... we are heavily
                   rejecting off of the 0.618" — the basis of his 10:28
                   short.
  rebalance state  "I am probably not gonna take any trades until I see
                   price reach the 15-minute moving average" — a gate on
                   the whole session, not a feature of one candle.
  simultaneity     "we closed through the POC and the Bollinger Band in
                   the same candle, and that's what I look for. I look
                   for it to close through the same area at the same
                   time." Named twice, unprompted.

EVERYTHING IS AS-OF. Each series is valid for decisions at the minute it
is stamped on and never reads a later bar. The weekly profile uses only
COMPLETED prior session-days; the NY range is undefined until 10:00 NY.

Usable two ways: batch (attach to a census) and live (`context_at` for a
single minute, which is what the local TradingView agent will call).

    python -m scripts.agent_context [--build]     # attach to raw_triggers
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof, vwap_bands            # noqa: E402

RAW = ROOT / "output/htf_ma_census/raw_triggers.parquet"
OUT = ROOT / "output/htf_ma_census/agent_context.parquet"
FIBS = [0.382, 0.5, 0.618, 0.705, 0.786]     # the set on his charts
WEEK_DAYS = 5                                 # his weekly profile anchor
DISP_W = 0.5                                  # displacement, in W15
NY_RANGE = (570, 600)                         # 09:30-10:00 NY


def volume_profile(seg: pd.DataFrame, bin_w: float = 1.0,
                   value_frac: float = 0.70):
    """(poc, val, vah) by traded volume, TradingView-style.

    Two fixes over the original, both of which mattered (2026-08-10):

    1. Each bar's volume is SPREAD uniformly across its high-low range.
       The original dumped the whole bar at its HLC3, which for a 1m bar
       spanning 20 points is a bad approximation of where trade occurred.
    2. The value area EXPANDS OUTWARD FROM THE POC in pairs until it holds
       `value_frac` of total volume, so it is CONTIGUOUS. The original took
       the highest-volume bins anywhere in the profile and returned their
       min/max — over a week-long profile that returns something close to
       the full range. On 2026-06-22 it put the weekly VAH ~190pt above the
       trader's own reading; this version lands ~25-45pt away.

    A ~30pt residual remains and is NOT resolved: real profiles distribute
    volume by traded ticks, not uniformly, and his chart's row size is
    unknown. Read profile levels off the chart; use these for orientation.
    """
    if seg.empty or seg.volume.sum() <= 0:
        return (np.nan, np.nan, np.nan)
    lo = np.floor(seg.low.to_numpy() / bin_w).astype(np.int64)
    hi = np.floor(seg.high.to_numpy() / bin_w).astype(np.int64)
    vol = seg.volume.to_numpy(float)
    b0, b1 = int(lo.min()), int(hi.max())
    acc = np.zeros(b1 - b0 + 2, dtype=float)
    # spread each bar over its rows via a difference array (O(n) not O(n*rows))
    np.add.at(acc, lo - b0, vol / (hi - lo + 1))
    np.add.at(acc, hi - b0 + 1, -vol / (hi - lo + 1))
    rows = np.cumsum(acc)[:-1]
    if rows.sum() <= 0:
        return (np.nan, np.nan, np.nan)
    i = int(rows.argmax())
    total, lo_i, hi_i = rows.sum(), i, i
    cum = rows[i]
    while cum < value_frac * total and (lo_i > 0 or hi_i < len(rows) - 1):
        up = rows[hi_i + 1:hi_i + 3].sum() if hi_i < len(rows) - 1 else -1.0
        dn = rows[max(lo_i - 2, 0):lo_i].sum() if lo_i > 0 else -1.0
        if up >= dn and hi_i < len(rows) - 1:
            hi_i = min(hi_i + 2, len(rows) - 1)
        elif lo_i > 0:
            lo_i = max(lo_i - 2, 0)
        else:
            break
        cum = rows[lo_i:hi_i + 1].sum()
    return (float((b0 + i) * bin_w), float((b0 + lo_i) * bin_w),
            float((b0 + hi_i + 1) * bin_w))


def anchored_weekly_profile(bars: pd.DataFrame, sess_day: str,
                            upto: pd.Timestamp | None = None):
    """His actual weekly profile: anchored to the Asia open (18:00 NY) of the
    SAME WEEKDAY exactly one week earlier, and DEVELOPING to `upto`.

    Declared 2026-08-10: "If I'm trading Monday, I'm gonna anchor it to the
    Asia Open at the beginning of last week. If I'm trading Tuesday, I'm
    gonna anchor it to the Asia Open of Monday night... the last five trading
    days should be exactly a week before, the same day."

    Note this is NOT `weekly_levels` below, which is a fixed 5-completed-day
    profile. Both are kept: this one is his, that one is the research build's.
    """
    anchor = pd.Timestamp(f"{sess_day} 18:00", tz=NY) - pd.Timedelta(days=7)
    end = upto if upto is not None else (
        pd.Timestamp(f"{sess_day} 18:00", tz=NY) + pd.Timedelta(hours=23))
    seg = bars[(bars.index >= anchor) & (bars.index < end)]
    poc, val, vah = volume_profile(seg)
    return {"awPOC": poc, "awVAL": val, "awVAH": vah,
            "awHIGH": float(seg.high.max()) if len(seg) else np.nan,
            "awLOW": float(seg.low.min()) if len(seg) else np.nan,
            "anchor": anchor}


def session_day_of(t: pd.Timestamp) -> str:
    return str((t.normalize() if t.hour >= 18
                else t.normalize() - pd.Timedelta(days=1)).date())


def weekly_levels(bars: pd.DataFrame, sess_day: str, all_days: list):
    """Volume profile + extremes over the WEEK_DAYS completed session-days
    before `sess_day`. Fixed for the whole of `sess_day` — causal."""
    i = all_days.index(sess_day) if sess_day in all_days else -1
    prior = all_days[max(i - WEEK_DAYS, 0):i] if i > 0 else []
    if not prior:
        return {k: np.nan for k in ("wPOC", "wVAL", "wVAH",
                                    "wHIGH", "wLOW")}
    a = pd.Timestamp(f"{prior[0]} 18:00", tz=NY)
    b = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    seg = bars[(bars.index >= a) & (bars.index < b)]
    poc, val, vah = volume_profile(seg)
    return {"wPOC": poc, "wVAL": val, "wVAH": vah,
            "wHIGH": float(seg.high.max()) if len(seg) else np.nan,
            "wLOW": float(seg.low.min()) if len(seg) else np.nan}


def prev_day_levels(bars: pd.DataFrame, sess_day: str, all_days: list):
    i = all_days.index(sess_day) if sess_day in all_days else -1
    if i <= 0:
        return {k: np.nan for k in ("pPOC", "pVAL", "pVAH",
                                    "pHIGH", "pLOW")}
    p = all_days[i - 1]
    a = pd.Timestamp(f"{p} 18:00", tz=NY)
    b = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    seg = bars[(bars.index >= a) & (bars.index < b)]
    poc, val, vah = volume_profile(seg)
    return {"pPOC": poc, "pVAL": val, "pVAH": vah,
            "pHIGH": float(seg.high.max()) if len(seg) else np.nan,
            "pLOW": float(seg.low.min()) if len(seg) else np.nan}


def day_series(bars: pd.DataFrame, sess_day: str):
    """Per-1m series for one session-day: rebalance state, NY-range fibs,
    and the per-minute simultaneous-closure map. All as-of."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                & (bars.index < t1)]
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return None
    idx = seg.index
    hi, lo, cl = (seg.high.to_numpy(), seg.low.to_numpy(),
                  seg.close.to_numpy())
    N = len(idx)
    ma15, w15 = bb_ma_asof(hist, 15)
    m15 = ma15.reindex(idx).to_numpy()
    w = w15.reindex(idx).to_numpy()

    # ---- rebalance state: after price displaces >= DISP_W from the 15m
    # MA it is "awaiting rebalance" until a bar's range contains the MA.
    disp_side = np.zeros(N, dtype=int)      # side it displaced to
    awaiting = np.zeros(N, dtype=int)       # 1 = waiting for rebalance
    since_touch = np.full(N, -1)
    cur_side, cur_wait, last_touch = 0, 0, -1
    for j in range(N):
        if not (np.isfinite(m15[j]) and np.isfinite(w[j]) and w[j] > 0):
            disp_side[j], awaiting[j] = cur_side, cur_wait
            since_touch[j] = -1 if last_touch < 0 else j - last_touch
            continue
        touched = lo[j] <= m15[j] <= hi[j]
        if touched:
            last_touch = j
            cur_wait, cur_side = 0, 0
        else:
            e = (cl[j] - m15[j]) / w[j]
            if abs(e) >= DISP_W:
                cur_side = int(np.sign(e))
                cur_wait = 1
        disp_side[j], awaiting[j] = cur_side, cur_wait
        since_touch[j] = -1 if last_touch < 0 else j - last_touch

    # ---- NY range (09:30-10:00 NY) and its fibs; undefined before 10:00
    hm = np.array([t.hour * 60 + t.minute for t in idx])
    inr = (hm >= NY_RANGE[0]) & (hm < NY_RANGE[1])
    nyh = float(hi[inr].max()) if inr.any() else np.nan
    nyl = float(lo[inr].min()) if inr.any() else np.nan
    fib = {}
    if np.isfinite(nyh) and np.isfinite(nyl) and nyh > nyl:
        for f in FIBS:
            fib[f"fib_{f}"] = nyh - (nyh - nyl) * f
    valid_from = np.where(hm >= NY_RANGE[1], True, False)

    # ---- simultaneous closure map: for each minute, which TFs closed a
    # candle there, and did that candle close through its own BB MA in
    # the same direction? (2m closes on even minutes, 3m on /3, 15m /15
    # relative to the session grid.)
    ma_tf = {tf: bb_ma_asof(hist, tf)[0].reindex(idx).to_numpy()
             for tf in (2, 3, 15)}
    thru = {tf: np.zeros(N, dtype=int) for tf in (2, 3, 15)}
    for tf in (2, 3, 15):
        f = hist.resample(f"{tf}min", label="right", closed="left").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last"}).dropna()
        f = f[(f.index > t0) & (f.index <= t1)]
        for ts, b_ in f.iterrows():
            j = int(np.searchsorted(idx.values, ts.to_datetime64())) - 1
            if j < 0 or j >= N:
                continue
            m = ma_tf[tf][j]
            if not np.isfinite(m):
                continue
            for d in (+1, -1):
                if d * (b_.close - m) > 0 and d * (b_.open - m) <= 0:
                    thru[tf][j] = d
    return dict(idx=idx, m15=m15, w=w, disp_side=disp_side,
                awaiting=awaiting, since_touch=since_touch,
                ny_high=nyh, ny_low=nyl, fib=fib, fib_valid=valid_from,
                thru=thru, cl=cl)


def context_at(bars, sess_day, t, all_days):
    """Full structured context at one minute — what the live agent asks
    for. `t` is the decision minute (the close of the trigger candle)."""
    S = day_series(bars, sess_day)
    if S is None:
        return {}
    j = int(np.searchsorted(S["idx"].values,
                            pd.Timestamp(t).to_datetime64())) - 1
    if j < 0 or j >= len(S["idx"]):
        return {}
    out = {}
    out.update(weekly_levels(bars, sess_day, all_days))
    out.update(prev_day_levels(bars, sess_day, all_days))
    out["ny_high"], out["ny_low"] = S["ny_high"], S["ny_low"]
    if S["fib_valid"][j]:
        out.update(S["fib"])
    out["awaiting_rebalance"] = int(S["awaiting"][j])
    out["displaced_side"] = int(S["disp_side"][j])
    out["mins_since_ma_touch"] = int(S["since_touch"][j])
    sim = [tf for tf in (2, 3, 15) if S["thru"][tf][j] != 0]
    out["closed_through_tfs"] = ",".join(str(x) for x in sim)
    out["n_tf_simultaneous"] = len(sim)
    out["sim_dir"] = int(S["thru"][2][j] or S["thru"][3][j] or 0)
    w = S["w"][j]
    if np.isfinite(w) and w > 0:
        px = S["cl"][j]
        for k, v in list(out.items()):
            if k[0] in "wp" and isinstance(v, float) and np.isfinite(v) \
                    and k not in ("w", "px"):
                out[f"dist_{k}_w"] = (px - v) / w
    return out


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    all_days = sorted({session_day_of(t) for t in bars.index})
    F = pd.read_parquet(RAW)
    F["t"] = pd.to_datetime(F.t)
    days = sorted(F.sess_day.unique())
    rows = []
    for k, day in enumerate(days):
        S = day_series(bars, day)
        if S is None:
            continue
        wk = weekly_levels(bars, day, all_days)
        pv = prev_day_levels(bars, day, all_days)
        g = F[F.sess_day == day]
        for r in g.itertuples():
            j = int(np.searchsorted(S["idx"].values,
                                    pd.Timestamp(r.t).to_datetime64())) - 1
            if j < 0 or j >= len(S["idx"]):
                continue
            w = S["w"][j]
            px = S["cl"][j]
            rec = {"sess_day": day, "t": r.t, "tf": r.tf, "dir": r.dir,
                   "awaiting_rebalance": int(S["awaiting"][j]),
                   "displaced_side": int(S["disp_side"][j]),
                   "mins_since_ma_touch": int(S["since_touch"][j]),
                   "n_tf_simultaneous": sum(
                       1 for tf in (2, 3, 15) if S["thru"][tf][j] != 0),
                   "closed_2m3m_together": int(
                       S["thru"][2][j] != 0 and S["thru"][3][j] != 0),
                   "closed_with_15m": int(S["thru"][15][j] != 0)}
            rec.update(wk)
            rec.update(pv)
            if S["fib_valid"][j] and S["fib"]:
                nearest = min(S["fib"], key=lambda f2: abs(px - S["fib"][f2]))
                rec["nearest_fib"] = nearest
                rec["dist_fib_w"] = ((px - S["fib"][nearest]) / w
                                     if w and w > 0 else np.nan)
                rec["at_fib"] = int(abs(rec["dist_fib_w"]) <= 0.15
                                    if np.isfinite(rec["dist_fib_w"])
                                    else 0)
            for nm, v in list(wk.items()) + list(pv.items()):
                rec[f"dist_{nm}_w"] = ((px - v) / w
                                       if np.isfinite(v) and w and w > 0
                                       else np.nan)
            rows.append(rec)
        if k % 50 == 0:
            print(f"  {k}/{len(days)}...", flush=True)
    C = pd.DataFrame(rows)
    C.to_parquet(OUT, index=False)
    print(f"written: {OUT.name} ({len(C):,} rows x {C.shape[1]} cols)")
    print(f"\n   awaiting-rebalance at trigger : "
          f"{C.awaiting_rebalance.mean()*100:.1f}% of triggers")
    print(f"   2m AND 3m closed together     : "
          f"{C.closed_2m3m_together.mean()*100:.1f}%")
    print(f"   15m closed in the same minute : "
          f"{C.closed_with_15m.mean()*100:.1f}%")
    if "at_fib" in C:
        print(f"   at a NY-range fib (<=0.15W)   : "
              f"{C.at_fib.mean()*100:.1f}% (of rows where fibs exist)")
    print(f"   weekly levels present         : "
          f"{C.wVAL.notna().mean()*100:.1f}%")


if __name__ == "__main__":
    main()
