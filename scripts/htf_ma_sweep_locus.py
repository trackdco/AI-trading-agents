#!/usr/bin/env python3
"""ITEM 6 — SWEEP-RECLAIM AS A LOCUS (DECLARATIONS-sweep-locus.md).

Two cells, both censused like VAL/VWAP-1 and NOT bolted onto an existing
book:

  (a) STANDALONE  one 15m bar sweeps the 8-bar swing low by >=4 ticks and
                  CLOSES BACK ABOVE it. No prior attempt required.
  (b) OWN-STOP    a prior attempt (any of the seven loci) was stopped; a
                  later bar trades >=4 ticks beyond THAT ATTEMPT'S OWN STOP
                  and a bar closes back inside within 3 bars.

Shared machinery is the E1 machinery: entry next 1m open, stop at the
trigger candle extreme, shipped exit, W = 15m BB width, 15m trigger TF.

    python -m scripts.htf_ma_sweep_locus [--days N]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof, session_tag           # noqa: E402

TICK = 0.25
COST_PTS = 0.5
FIT_START, FIT_END = "2025-06-01", "2026-07-31"
LOOKBACK, PEN_TICKS, RECLAIM_A, RECLAIM_B = 8, 4, 1, 3
EXCL = {"no_next_open": 0, "gap_through_stop": 0}


def day_rows(bars: pd.DataFrame, sess_day: str,
             prior_stops: list[dict] | None = None) -> list[dict]:
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
    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    if len(f15) < LOOKBACK + 2:
        return []
    ma_f15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1))
    ma_f15.index = f15.index
    w_at15 = w15.reindex(f15.index - pd.Timedelta(minutes=1))
    w_at15.index = f15.index
    fl, fh, fc = f15.low.to_numpy(), f15.high.to_numpy(), f15.close.to_numpy()
    pen = PEN_TICKS * TICK

    def walk_exits(j0, d, entry, stop):
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
            trail, j_trail = eod, len(idx) - 1
        leg3 = (3.0 * risk - TICK) / risk if t3 is not None else None
        ship = (0.75 * leg3 + 0.25 * trail if leg3 is not None else trail) - cost
        j_exit = stop_j if (stop_j is not None and t3 is None) else j_trail
        return {"risk": risk, "mfe_r": mfe, "out_ship": ship,
                "out_trail": trail - cost, "out_hold": hold - cost,
                "t_entry": idx[j0], "t_exit": idx[j_exit]}

    def emit(cell, bi, d, side):
        b_ = f15.iloc[bi]
        w_e = w_at15.iloc[bi]
        if not (np.isfinite(w_e) and w_e > 0):
            return None
        j0 = int(np.searchsorted(idx.values, f15.index[bi].to_datetime64()))
        if j0 >= len(idx):
            EXCL["no_next_open"] += 1
            return None
        entry = float(op[j0])
        stop = (b_.low - TICK) if d > 0 else (b_.high + TICK)
        if d * (entry - stop) <= 0:
            EXCL["gap_through_stop"] += 1
            return None
        w = walk_exits(j0, d, entry, stop)
        if not w:
            return None
        return {"sess_day": sess_day, "t": f15.index[bi], "cell": cell,
                "side": side, "direction": d, "n_attempts": 0,
                "session": session_tag(f15.index[bi]), "w15": w_e,
                "entry": entry, "stop": stop, "trig_high": b_.high,
                "trig_low": b_.low, "arm": "sweep", "locus": cell, **w}

    rows = []
    # ---- cell (a): standalone one-bar sweep-and-reclaim -------------------
    for bi in range(LOOKBACK, len(f15)):
        ref_lo = fl[bi - LOOKBACK:bi].min()
        ref_hi = fh[bi - LOOKBACK:bi].max()
        if fl[bi] <= ref_lo - pen and fc[bi] > ref_lo:
            r = emit("sweep_a", bi, 1, "below")
            if r:
                rows.append(r)
        if fh[bi] >= ref_hi + pen and fc[bi] < ref_hi:
            r = emit("sweep_a", bi, -1, "above")
            if r:
                rows.append(r)

    # ---- cell (b): sweep of a PRIOR STOPPED ATTEMPT'S OWN STOP -----------
    for ps in (prior_stops or []):
        t_st, sp, d = pd.Timestamp(ps["t"]), float(ps["stop"]), int(ps["dir"])
        after = np.searchsorted(f15.index.values, t_st.to_datetime64(),
                                side="right")
        for k in range(after, len(f15)):
            beyond = (fl[k] <= sp - pen) if d > 0 else (fh[k] >= sp + pen)
            if not beyond:
                continue
            for m in range(k, min(k + RECLAIM_B + 1, len(f15))):
                inside = (fc[m] > sp) if d > 0 else (fc[m] < sp)
                if inside:
                    r = emit("sweep_b", m, d,
                             "below" if d > 0 else "above")
                    if r:
                        r["prior_t"] = t_st
                        rows.append(r)
                    break
            break                      # first penetration only
    # DEDUP: one reclaim bar can sweep the stops of SEVERAL prior attempts.
    # That is one trigger, not many — key on (bar, direction) and keep the
    # earliest prior attempt as the attributed cause.
    seen = {}
    out_rows = []
    for r in rows:
        if r["cell"] != "sweep_b":
            out_rows.append(r)
            continue
        k = (r["t"], r["direction"])
        if k in seen:
            if r.get("prior_t") is not None and \
                    r["prior_t"] < seen[k]["prior_t"]:
                seen[k]["prior_t"] = r["prior_t"]
            continue
        seen[k] = r
        out_rows.append(r)
    return out_rows


def main() -> None:
    n_days = None
    if "--days" in sys.argv:
        n_days = int(sys.argv[sys.argv.index("--days") + 1])
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    # prior stopped attempts, from the seven-locus census (fit rows only)
    L = pd.read_parquet(ROOT / "output/htf_ma_census/levels_fit_v1.parquet")
    L = L[L.out_ship.notna() & (L.risk > 0)]
    L["stopped"] = (L.out_hold <= -1.0) & (L.mfe_r < 3.0)
    S = L[L.stopped]
    stops_by_day: dict[str, list[dict]] = {}
    for r in S.itertuples():
        stops_by_day.setdefault(r.sess_day, []).append(
            {"t": r.t, "stop": r.stop, "dir": int(r.direction)})
    print(f"prior stopped attempts available: {len(S):,} over "
          f"{len(stops_by_day)} days")

    sess_days = sorted({str((t.normalize() if t.hour >= 18
                             else t.normalize() - pd.Timedelta(days=1)).date())
                        for t in bars.index})
    if n_days:
        sess_days = sess_days[-n_days:]
    fit, sealed, gray = [], [], []
    for k, d in enumerate(sess_days):
        rows = day_rows(bars, d, stops_by_day.get(d))
        (fit if FIT_START <= d <= FIT_END else
         sealed if d < "2025-01-01" else gray).extend(rows)
        if k % 80 == 0:
            print(f"  {k}/{len(sess_days)}...", flush=True)
    out = ROOT / "output/htf_ma_census"
    if fit:
        F = pd.DataFrame(fit)
        F.to_parquet(out / "sweep_fit.parquet", index=False)
        print(F.groupby(["cell", "side"]).size().to_string())
    if sealed:
        pd.DataFrame(sealed).to_parquet(
            ROOT / "output/sealed/sweep_sealed.parquet", index=False)
    print(f"SWEEP LOCUS: fit={len(fit):,} | sealed={len(sealed):,} "
          f"(written, NOT read) | gray={len(gray):,} | excl={EXCL}")


if __name__ == "__main__":
    main()
