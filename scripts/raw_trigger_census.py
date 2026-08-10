#!/usr/bin/env python3
"""RAW TRIGGER CENSUS — the trader's own reset, 2026-08-08.

His words: "every single time a 3-minute candle closes through a VWAP
band and through its Bollinger Band moving average, every single time
that happens, what is the raw amount of triggers we have there? We can
work back from there, calculating risk to reward, calculating outcomes,
and diagnosing winners from losers."

So: NO higher-timeframe thesis requirement, NO affirmation count, NO
mechanism classification. Just the candle condition, everything it
catches, and the honest outcome distribution. Discretion is explicitly
NOT modelled — the point is to get the raw substrate and then look for
what separates winners from losers inside it.

TRIGGER: a TF candle (2m and 3m, reported separately) whose OPEN is on
one side of BOTH (a) its own BB(20) MA and (b) some VWAP band, and whose
CLOSE is through both, in the same direction. The qualifying band is
recorded, never fixed.

Entry = next 1m open. Stop = the trigger candle's opposite extreme
+/- 1 tick. Outcomes are walked with NO target (stop or session end
only) so every R multiple can be priced afterwards.

    python -m scripts.raw_trigger_census [--build]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

OUT = ROOT / "output/htf_ma_census/raw_triggers.parquet"
TFS = [2, 3]
BANDS = ["vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2",
         "vwap_p3", "vwap_m3"]
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
TICK = 0.25
RS = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]


def day_rows(bars, sess_day):
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                & (bars.index < t1)]
    if hist.empty:
        return []
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if seg.empty:
        return []
    idx = seg.index
    hi, lo, cl, op = (seg.high.to_numpy(), seg.low.to_numpy(),
                      seg.close.to_numpy(), seg.open.to_numpy())
    N = len(idx)
    ma15, w15 = bb_ma_asof(hist, 15)
    ma15_1m = ma15.reindex(idx).to_numpy()
    w15_1m = w15.reindex(idx).to_numpy()
    ma60, _ = bb_ma_asof(hist, 60)
    ma60_1m = ma60.reindex(idx).to_numpy()
    vw = vwap_bands(hist)
    band_1m = {b: vw[b].reindex(idx).to_numpy() for b in BANDS}
    prof = profile_at_minutes(hist, list(idx + pd.Timedelta(minutes=1)))
    poc_1m = prof["poc"].to_numpy()
    val_1m = prof["val"].to_numpy()
    vah_1m = prof["vah"].to_numpy()

    def walk(j0, d, entry, stop):
        """No target — walk to the stop or the session end. Returns the
        full excursion so any R multiple can be priced later."""
        risk = abs(entry - stop)
        mfe = mae = 0.0
        stopped = False
        peak = j0
        for j in range(j0, N):
            adv = d * ((hi[j] if d > 0 else lo[j]) - entry) / risk
            adverse = d * ((lo[j] if d > 0 else hi[j]) - entry) / risk
            if adv > mfe:
                mfe, peak = adv, j
            mae = min(mae, adverse)
            if (lo[j] <= stop) if d > 0 else (hi[j] >= stop):
                stopped = True
                break
        end = j if stopped else N - 1
        return mfe, mae, stopped, int(end - j0), int(peak - j0), \
            d * (cl[end] - entry) / risk

    rows = []
    for tf in TFS:
        ma_tf, _ = bb_ma_asof(hist, tf)
        ftf = hist.resample(f"{tf}min", label="right", closed="left").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last"}).dropna()
        ftf = ftf[(ftf.index > t0) & (ftf.index <= t1)]
        pos = np.clip(np.searchsorted(
            idx.values, (ftf.index - pd.Timedelta(minutes=1)).values),
            0, N - 1)
        matf = ma_tf.reindex(idx).to_numpy()[pos]
        fo, fc = ftf.open.to_numpy(), ftf.close.to_numpy()
        fh, fl = ftf.high.to_numpy(), ftf.low.to_numpy()
        for bi, ts in enumerate(ftf.index):
            p = pos[bi]
            m_tf = matf[bi]
            if not np.isfinite(m_tf):
                continue
            for d in (+1, -1):
                # (a) closes through its OWN BB MA, fresh
                if not (d * (fc[bi] - m_tf) > 0 and d * (fo[bi] - m_tf) <= 0):
                    continue
                # (b) AND through some VWAP band, same candle, same way
                qual = None
                for b in BANDS:
                    bv = band_1m[b][p]
                    if not np.isfinite(bv):
                        continue
                    if d * (fc[bi] - bv) > 0 and d * (fo[bi] - bv) <= 0:
                        if qual is None or abs(bv - fc[bi]) < abs(qual[1]
                                                                 - fc[bi]):
                            qual = (b, bv)
                if qual is None:
                    continue
                j0 = int(np.searchsorted(idx.values, ts.to_datetime64()))
                if j0 >= N:
                    continue
                entry = float(op[j0])
                stop = (fl[bi] - TICK) if d > 0 else (fh[bi] + TICK)
                if d * (entry - stop) <= 0:
                    continue
                risk = abs(entry - stop)
                mfe, mae, stopped, held, peak, eod = walk(j0, d, entry, stop)
                w = w15_1m[p]
                rec = {"sess_day": sess_day, "t": ts, "tf": tf,
                       "dir": "long" if d > 0 else "short", "direction": d,
                       "hm": ts.hour * 60 + ts.minute,
                       "entry": entry, "stop": stop, "risk": risk,
                       "qual_band": qual[0],
                       "run_mfe_r": mfe, "run_mae_r": mae,
                       "stopped": stopped, "bars_held": held,
                       "mins_to_peak": peak, "eod_r": eod,
                       "w15": w,
                       "risk_over_w": risk / w if w and w > 0 else np.nan,
                       # context for the winner/loser diagnosis
                       "px_vs_ma15_w": (cl[p] - ma15_1m[p]) / w
                       if w and w > 0 else np.nan,
                       "px_vs_ma60_w": (cl[p] - ma60_1m[p]) / w
                       if w and w > 0 else np.nan,
                       "ma15_vs_ma60_w": (ma15_1m[p] - ma60_1m[p]) / w
                       if w and w > 0 else np.nan,
                       "with_15m_trend": float(
                           np.sign(ma15_1m[p] - ma60_1m[p]) == d),
                       "px_vs_poc_w": (cl[p] - poc_1m[p]) / w
                       if w and w > 0 else np.nan,
                       "in_value": float(val_1m[p] <= cl[p] <= vah_1m[p]),
                       "bar_range_w": (fh[bi] - fl[bi]) / w
                       if w and w > 0 else np.nan,
                       "bar_closeloc": (((fc[bi] - fl[bi]) /
                                         (fh[bi] - fl[bi])) if d > 0
                                        else ((fh[bi] - fc[bi]) /
                                              (fh[bi] - fl[bi])))
                       if fh[bi] > fl[bi] else np.nan}
                for R in RS:
                    rec[f"r{R}"] = bool(mfe >= R)
                rows.append(rec)
    return rows


def main() -> None:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    days = [d for d in sess_days if FIT_START <= d <= FIT_END]

    if "--build" in sys.argv or not OUT.exists():
        rows = []
        for k, d in enumerate(days):
            rows.extend(day_rows(bars, d))
            if k % 40 == 0:
                print(f"  {k}/{len(days)}...", flush=True)
        F = pd.DataFrame(rows)
        F["t"] = pd.to_datetime(F.t)
        F.to_parquet(OUT, index=False)
        print(f"written: {OUT.name} ({len(F):,} rows)")
    F = pd.read_parquet(OUT)
    F["t"] = pd.to_datetime(F.t)
    nd = len(days)

    print("\n" + "=" * 92)
    print("RAW TRIGGER COUNT — TF candle closes through its own BB MA *and* "
          "a VWAP band. No thesis filter.")
    print("=" * 92)
    for tf in TFS:
        g = F[F.tf == tf]
        print(f"   {tf}m: {len(g):,} triggers over {nd} days = "
              f"{len(g)/nd:.2f}/day   (long {(g.dir=='long').sum()}, "
              f"short {(g.dir=='short').sum()})")

    print("\nBY HOUR (NY) — where they actually occur, vs his 03:00-10:51 range")
    for tf in TFS:
        g = F[F.tf == tf]
        h = (g.hm // 60).value_counts().sort_index()
        print(f"   {tf}m: " + " ".join(f"{int(k):02d}h:{v}" for k, v in
                                       h.items() if 2 <= k <= 12))

    print("\n" + "=" * 92)
    print("OUTCOME DISTRIBUTION — P(reach R before stop), and the fixed-target "
          "EV that implies")
    print("=" * 92)
    print(f"   {'tf':>3s} {'n':>6s} " + " ".join(f"{('P('+str(R)+'R)'):>8s}"
                                                 for R in RS))
    for tf in TFS:
        g = F[F.tf == tf]
        print(f"   {tf:3d} {len(g):6d} " + " ".join(
            f"{g[f'r{R}'].mean()*100:7.1f}%" for R in RS))
    print(f"\n   fixed-target EV (=P*R-(1-P), cost ~0.04R):")
    print(f"   {'tf':>3s} " + " ".join(f"{(str(R)+'R'):>8s}" for R in RS))
    for tf in TFS:
        g = F[F.tf == tf]
        print(f"   {tf:3d} " + " ".join(
            f"{g[f'r{R}'].mean()*R-(1-g[f'r{R}'].mean())-0.04:+8.3f}"
            for R in RS))

    print(f"\n   stopped {F.stopped.mean()*100:.1f}%   median bars held "
          f"{F.bars_held.median():.0f}   median mins to peak "
          f"{F.mins_to_peak.median():.0f}")
    print(f"   median risk {F.risk.median():.1f}pt  "
          f"({F.risk_over_w.median():.2f} W15)")
    print(f"   qualifying band: " + "  ".join(
        f"{k}:{v}" for k, v in F.qual_band.value_counts().items()))


if __name__ == "__main__":
    main()
