#!/usr/bin/env python3
"""CENSUS A — the M1 rebalance base rate (SPEC §3). 15m primary reference.

Event: close displaced from the 15m BB MA by more than D (D swept in W_15m
units) for the FIRST time since price last touched the MA (per-D re-arm on MA
touch). Sides never pooled. Outcomes forward to the 17:00 session close:
touch of the (moving, as-of) MA, time to touch, further extension before touch
(the entry-free payoff-shape device: ma_before_stop_S over S ticks and
ma_before_ext_E over E in W units), levels between event and MA, 1h agreement.

Span: full 2023->2026. FIT (2025-06..2026-07) rows go to
output/htf_ma_census/censusA_fit.parquet and are analysed by the verdict
script. Rows outside fit go to output/sealed/censusA_sealed.parquet and
output/htf_ma_census/censusA_gray.parquet (2025-01..05) and are NEVER read,
printed, or aggregated here (SPEC §6.8; incident §8a made this guard physical).

    python -m scripts.htf_ma_census_a [--days N]      # N most recent per bucket, for smoke
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
D_SWEEP = [0.5, 0.75, 1.0, 1.5, 2.0]          # in W_15m units
E_SWEEP = [0.5, 1.0, 1.5, 2.0, 3.0]           # further extension, W_15m units
S_SWEEP = [10, 20, 30, 40, 60, 80]            # ticks beyond event extreme
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
CLUSTER_GAP_MIN = 30


def census_day(bars: pd.DataFrame, sess_day: str) -> list[dict]:
    """All census-A rows for one 18:00-anchored session."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)                      # 17:00 next day
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t1)]
    if hist.empty:
        return []
    ma15, w15 = bb_ma_asof(hist, 15)
    ma60, _ = bb_ma_asof(hist, 60)
    # ATR(14) on completed 15m bars, as-of (stamped at bar end)
    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"high": "max", "low": "min", "close": "last"}).dropna()
    tr = np.maximum(f15.high - f15.low,
                    np.maximum((f15.high - f15.close.shift()).abs(),
                               (f15.low - f15.close.shift()).abs()))
    atr15 = tr.rolling(14).mean()
    vw = vwap_bands(hist)

    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    if len(seg) < 30:
        return []
    idx = seg.index
    hi, lo, cl = seg.high.to_numpy(), seg.low.to_numpy(), seg.close.to_numpy()
    ma = ma15.loc[idx].to_numpy()
    w = w15.loc[idx].to_numpy()
    m60 = ma60.loc[idx].to_numpy()
    a15 = atr15.reindex(idx, method="ffill").to_numpy()
    touched_now = (lo <= ma) & (ma <= hi)

    rows = []
    for side, sgn in (("above", 1), ("below", -1)):       # sides never pooled
        armed = {D: False for D in D_SWEEP}
        for i in range(len(idx)):
            if not np.isfinite(ma[i]) or not np.isfinite(w[i]) or w[i] <= 0:
                continue
            if touched_now[i]:
                for D in D_SWEEP:
                    armed[D] = True
                continue
            disp = sgn * (cl[i] - ma[i])                  # >0 = displaced to `side`
            if disp <= 0:
                continue
            d_bw = disp / w[i]
            for D in D_SWEEP:
                if not armed[D] or d_bw <= D:
                    continue
                armed[D] = False                          # fires once per re-arm
                # forward outcomes to session close, against the MOVING as-of MA
                ext_ref = cl[i]                           # event price
                run_ext = 0.0                             # points beyond event price
                touched_at = None
                ext_first: dict[float, bool] = {}
                # touch-bar convention: the touch bar's own further extension
                # counts BEFORE the touch (stop-first, conservative)
                for j in range(i + 1, len(idx)):
                    adv = (hi[j] - ext_ref) if sgn > 0 else (ext_ref - lo[j])
                    if adv > run_ext:
                        run_ext = adv
                    for E in E_SWEEP:
                        if E not in ext_first and run_ext >= E * w[i]:
                            ext_first[E] = True           # extension reached pre-touch
                    if np.isfinite(ma[j]) and lo[j] <= ma[j] <= hi[j]:
                        touched_at = j
                        break
                r = {"sess_day": sess_day, "t": idx[i], "side": side, "D": D,
                     "session": session_tag(idx[i]),
                     "d_pts": disp, "d_bw": d_bw,
                     "d_atr": disp / a15[i] if np.isfinite(a15[i]) and a15[i] > 0 else np.nan,
                     "d_vwapdev": disp / vw.vwap_sd.loc[idx[i]]
                                  if np.isfinite(vw.vwap_sd.loc[idx[i]])
                                  and vw.vwap_sd.loc[idx[i]] > 0 else np.nan,
                     "w15": w[i], "event_px": cl[i], "ma_px": ma[i],
                     "touched_ma": touched_at is not None,
                     "t_touched_ma": (touched_at - i) if touched_at is not None else np.nan,
                     "closed_through_ma": False,          # filled below
                     "max_adverse_pts": run_ext,
                     "max_adverse_bw": run_ext / w[i],
                     # implied trade is TOWARD the 15m MA (direction -sgn); the
                     # 1h agrees when its close sits on that side of its own MA
                     "htf_agree_1h": bool(sgn * (cl[i] - m60[i]) < 0)
                                     if np.isfinite(m60[i]) else None}
                # closed_through: any 15m close on far side before touch/close
                # (evaluated on completed 15m bars after the event)
                after15 = f15[(f15.index > idx[i]) &
                              (f15.index <= (idx[touched_at] if touched_at is not None
                                             else idx[-1]))]
                r["closed_through_ma"] = bool((sgn * (after15.close.to_numpy()
                                       - ma15.reindex(after15.index, method="ffill")
                                       .to_numpy()) < 0).any()) if len(after15) else False
                for E in E_SWEEP:
                    r[f"ma_before_ext_{E}"] = (touched_at is not None
                                               and E not in ext_first)
                for S in S_SWEEP:
                    r[f"ma_before_stop_{S}"] = (touched_at is not None
                                                and run_ext < S * TICK)
                rows.append(r)
    # cluster ids: same side, events within CLUSTER_GAP_MIN minutes
    rows.sort(key=lambda r: (r["side"], r["t"]))
    cid, last_t, last_side = 0, None, None
    for r in rows:
        if last_side != r["side"] or last_t is None or \
                (r["t"] - last_t) > pd.Timedelta(minutes=CLUSTER_GAP_MIN):
            cid += 1
        r["cluster_id"] = f"{sess_day}:{r['side']}:{cid}"
        last_t, last_side = r["t"], r["side"]
    # levels between event and MA (profile + vwap family) — batch per day
    ev_min = [r["t"] for r in rows]
    if ev_min:
        prof = profile_at_minutes(hist, sorted(set(ev_min)))
        for r in rows:
            p = prof.loc[r["t"]]
            lvls = {"poc": p.poc, "vah": p.vah, "val": p.val,
                    "vwap": vw.vwap.loc[r["t"]],
                    "vwap_p1": vw.vwap_p1.loc[r["t"]],
                    "vwap_m1": vw.vwap_m1.loc[r["t"]]}
            a, b = sorted((r["event_px"], r["ma_px"]))
            r["levels_crossed"] = ",".join(k for k, v in lvls.items()
                                           if np.isfinite(v) and a < v < b)
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
        # bucket by the RTH date (session day + 1 for outcomes) — use sess_day
        if FIT_START <= d <= FIT_END:
            fit.extend(rows)
        elif d < "2025-01-01":
            sealed.extend(rows)
        elif d < FIT_START:
            gray.extend(rows)
        else:
            gray.extend(rows)
        if k % 50 == 0:
            print(f"  {k}/{len(sess_days)} days...", flush=True)
    out = ROOT / "output/htf_ma_census"
    out.mkdir(parents=True, exist_ok=True)
    (ROOT / "output/sealed").mkdir(parents=True, exist_ok=True)
    if fit:
        pd.DataFrame(fit).to_parquet(out / "censusA_fit.parquet", index=False)
    if sealed:
        pd.DataFrame(sealed).to_parquet(ROOT / "output/sealed/censusA_sealed.parquet",
                                        index=False)
    if gray:
        pd.DataFrame(gray).to_parquet(out / "censusA_gray.parquet", index=False)
    print(f"censusA: fit={len(fit):,} rows | sealed={len(sealed):,} (written, NOT read) "
          f"| gray={len(gray):,} (not analysed)")
    print("Sealed and gray are never aggregated by this script. SPEC §6.8.")


if __name__ == "__main__":
    main()
