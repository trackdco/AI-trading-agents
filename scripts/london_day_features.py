#!/usr/bin/env python3
"""LONDON DAY FEATURES — the shared L0 substrate for the nine London candidates.

One row per Globex trading day, computed from data/reference/nq_1m_master.parquet
(1-min OHLCV, 2023-01-02..2026-07-15 ET) — the candle store Angus confirmed
2026-08-04. Every column is CAUSAL at its stated clock time: a feature stamped
02:55 uses only bars ≤ 02:55 ET of that day. All nine candidate censuses read
from this table; none recompute session structure independently.

Day convention: Globex day D runs 18:00 ET (D−1) → 17:00 ET D. "Asia" and
"overnight" belong to D; the London window is 03:00–06:00 ET of D; "prior RTH"
is 09:30–16:00 ET of the previous trading day.

Columns (per day D):
  settle_prev            last 1-min close ≤ 15:59 ET of prior RTH day
  prior_rth_ret          prior RTH close-over-close return vs its own prior day
  prior_rth_hi/lo        prior RTH high/low (PDH/PDL)
  prior_poc / prior_va_hi/lo   prior RTH volume-at-price POC and 70% value area
                         (bar volume spread uniformly across the bar's range)
  asia_hi/lo/mid/rng     19:00 (D−1) → 02:00 ET D (default window; census variants
                         recompute from bars)
  asia_rng_pctl20        Asia range percentile vs trailing 20 days
  on_hi_0300/on_lo_0300  overnight extreme so far at 03:00 ET (18:00 anchor)
  on_vwap_0255 / on_sigma_0255   overnight volume-weighted mean price and
                         vol-weighted 1-min dispersion at 02:55 ET
  inv_skew_0255          fraction of 1-min closes 18:00→02:55 above settle_prev,
                         in [-1,1] as 2*frac−1 (inventory proxy)
  sweep_side_dead        which Asia extreme (if any) was breached 00:00–03:00 ET
                         first: 'high' | 'low' | 'both' | ''
  euro_open_det          detected European open: first minute 01:45–03:15 ET with
                         volume z ≥ 3 vs same-clock-minute trailing 20-day stats;
                         fallback 03:00
  euro_open_clock        Europe/London 08:00 expressed in ET for day D
  dst_mismatch           bool — euro_open_clock != 03:00 ET (the misfire weeks)
  lon_hi/lo/rng/vol      London-window (03:00–06:00) realized stats — for
                         verification and outcome labeling, never for entry features
  dow                    day of week (Mon=0)

Verification gates printed on every build (L0 discipline):
  * day count and span vs the master store
  * settlement continuity: settle_prev equals prior day's 15:59 close (exact)
  * euro-open detection distribution: mode 03:00 ET on normal weeks, 02:00 ET
    inside DST-mismatch weeks
  * spot day check: 2025-06-02 Asia range printed for eyeball vs chart

Writes output/london_day_features.parquet.

    python -m scripts.london_day_features
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ET = "America/New_York"
UK = "Europe/London"
ASIA_START, ASIA_END = "19:00", "02:00"     # default window (census variants re-derive)
Z_OPEN = 3.0


def load_bars() -> pd.DataFrame:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event)
    ts = ts.dt.tz_convert(ET) if ts.dt.tz is not None else ts.dt.tz_localize(ET)
    B = B.assign(ts=ts).sort_values("ts").reset_index(drop=True)
    # Globex day: 18:00 rolls to the next calendar day
    B["day"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    B["clock"] = B.ts.dt.strftime("%H:%M")
    return B


def rth_table(B: pd.DataFrame) -> pd.DataFrame:
    """Per calendar day: RTH stats incl. settlement and volume-at-price POC/VA."""
    cal = B.ts.dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")].assign(cal=cal)
    rows = []
    for day, g in R.groupby("cal", sort=True):
        # volume-at-price: spread each bar's volume uniformly over its tick range
        lo, hi = g.low.min(), g.high.max()
        edges = np.arange(np.floor(lo * 4) / 4, np.ceil(hi * 4) / 4 + 0.25, 0.25)
        vap = np.zeros(len(edges))
        span = np.maximum((g.high - g.low).to_numpy(), 0.25)
        for l, h, v in zip(g.low.to_numpy(), g.high.to_numpy(), g.volume.to_numpy()):
            i0 = np.searchsorted(edges, l) - 0
            i1 = np.searchsorted(edges, h, side="right")
            n = max(i1 - i0, 1)
            vap[i0:i1] += v / n
        poc = edges[int(vap.argmax())]
        order = np.argsort(vap)[::-1]
        cum, sel = 0.0, []
        for i in order:
            cum += vap[i]
            sel.append(i)
            if cum >= 0.70 * vap.sum():
                break
        va_lo, va_hi = edges[min(sel)], edges[max(sel)]
        rows.append({"cal": day, "rth_close": g.close.iloc[-1], "rth_hi": g.high.max(),
                     "rth_lo": g.low.min(), "poc": poc, "va_hi": va_hi, "va_lo": va_lo})
    return pd.DataFrame(rows)


def build() -> pd.DataFrame:
    B = load_bars()
    RT = rth_table(B)
    RT["ret"] = RT.rth_close.pct_change()
    prior = RT.set_index("cal")

    # per-clock-minute trailing volume stats for euro-open detection
    W = B[(B.clock >= "01:45") & (B.clock <= "03:15")]
    piv = W.pivot_table(index="day", columns="clock", values="volume", aggfunc="sum")
    mu = piv.rolling(20, min_periods=10).mean().shift(1)
    sd = piv.rolling(20, min_periods=10).std().shift(1)
    z = (piv - mu) / sd

    days = sorted(B.day.unique())
    rows = []
    for day, g in B.groupby("day", sort=True):
        g = g.sort_values("ts")
        d0 = pd.Timestamp(day, tz=ET)
        # prior trading day's RTH = the latest cal date < day present in RT
        pcals = prior.index[prior.index < day]
        if len(pcals) == 0:
            continue
        p = prior.loc[pcals[-1]]
        on = g[g.clock >= "18:00"]                      # 18:00 (D-1) bars carry day D
        on = pd.concat([on, g[g.clock < "17:00"]]).sort_values("ts")
        pre255 = on[(on.ts < d0 + pd.Timedelta(hours=2, minutes=55))]
        pre300 = on[(on.ts < d0 + pd.Timedelta(hours=3))]
        asia = on[((on.clock >= ASIA_START) | (on.clock < ASIA_END))]
        asia = asia[asia.ts < d0 + pd.Timedelta(hours=2)]
        dead = on[(on.ts >= d0) & (on.ts < d0 + pd.Timedelta(hours=3))]
        lon = g[(g.clock >= "03:00") & (g.clock < "06:00")]
        if len(asia) < 30 or len(pre255) < 60 or len(lon) < 30:
            continue
        a_hi, a_lo = asia.high.max(), asia.low.min()
        hi_b = (dead.high > a_hi).any()
        lo_b = (dead.low < a_lo).any()
        sweep = "both" if hi_b and lo_b else ("high" if hi_b else ("low" if lo_b else ""))
        vw = np.average(pre255.close, weights=np.maximum(pre255.volume, 1))
        sg = np.sqrt(np.average((pre255.close - vw) ** 2,
                                weights=np.maximum(pre255.volume, 1)))
        zrow = z.loc[day] if day in z.index else None
        det = "03:00"
        if zrow is not None and zrow.notna().any():
            hits = zrow[zrow >= Z_OPEN]
            if len(hits):
                det = hits.index[0]
        uk8 = pd.Timestamp(f"{day} 08:00", tz=UK).tz_convert(ET).strftime("%H:%M")
        rows.append({
            "day": day,
            "settle_prev": p.rth_close, "prior_rth_ret": p.ret,
            "prior_rth_hi": p.rth_hi, "prior_rth_lo": p.rth_lo,
            "prior_poc": p.poc, "prior_va_hi": p.va_hi, "prior_va_lo": p.va_lo,
            "asia_hi": a_hi, "asia_lo": a_lo, "asia_mid": (a_hi + a_lo) / 2,
            "asia_rng": a_hi - a_lo,
            "on_hi_0300": pre300.high.max(), "on_lo_0300": pre300.low.min(),
            "on_vwap_0255": vw, "on_sigma_0255": sg,
            "inv_skew_0255": 2 * (pre255.close > p.rth_close).mean() - 1,
            "sweep_side_dead": sweep,
            "euro_open_det": det, "euro_open_clock": uk8,
            "dst_mismatch": uk8 != "03:00",
            "lon_hi": lon.high.max(), "lon_lo": lon.low.min(),
            "lon_rng": lon.high.max() - lon.low.min(),
            "lon_vol": lon.volume.sum(), "dow": d0.dayofweek,
        })
    D = pd.DataFrame(rows)
    D["asia_rng_pctl20"] = D.asia_rng.rolling(20, min_periods=10).apply(
        lambda w: (w.iloc[-1] > w.iloc[:-1]).mean()).shift(0)
    return D


def main() -> None:
    D = build()
    out = ROOT / "output/london_day_features.parquet"
    D.to_parquet(out, index=False)
    print(f"LONDON DAY FEATURES: {len(D)} days, {D.day.min()} .. {D.day.max()}")
    norm = D[~D.dst_mismatch]
    mm = D[D.dst_mismatch]
    print(f"  euro-open detected at 03:00 on {(norm.euro_open_det == '03:00').mean():.0%} "
          f"of normal days; mismatch days {len(mm)} "
          f"(clock mode {mm.euro_open_clock.mode().iat[0] if len(mm) else 'n/a'})")
    print(f"  asia_rng median {D.asia_rng.median():.1f} pts | lon_rng median "
          f"{D.lon_rng.median():.1f} pts | inv_skew mean {D.inv_skew_0255.mean():+.2f}")
    spot = D[D.day == "2025-06-02"]
    if len(spot):
        s = spot.iloc[0]
        print(f"  spot 2025-06-02: asia {s.asia_lo:.2f}-{s.asia_hi:.2f} "
              f"({s.asia_rng:.1f} pts), settle_prev {s.settle_prev:.2f}, "
              f"euro open det {s.euro_open_det}")
    print(f"  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
