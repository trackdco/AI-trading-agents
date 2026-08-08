#!/usr/bin/env python3
"""THE TRADE CHECK — the trader's real executed trades (2026-06-01..03
screenshots, chart timezone verified = NY by exact bar match) audited
against the redeclared race grammar. Report-only.

For each trade: was it CAUGHT by the census (race_fit, declared 0.10W),
and if MISSED, the exact stage it died at — window, thesis, affirmation,
or entry race. Windows are reported as a stage here, never used to hide a
row.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.trigger_race_census import (MENU, SESSIONS, TOLW,      # noqa: E402
                                         DISP, in_window)
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

TRADES = [
    ("T1", "2026-06-01", "short", "09:42", "09:58", 30445.0,
     "short off the pullback after the morning collapse"),
    ("T2", "2026-06-02", "long", "09:38", "09:54", 30479.0,
     "long off VWAP on the morning reversal"),
    ("T3", "2026-06-03", "long", "08:58", "09:16", 30723.5,
     "premarket long, rejoin of the overnight rally"),
    ("T4", "2026-06-03", "short", "10:38", "10:52", 30701.0,
     "the multi-TF short: 15m break + pullback, 1m closure at 10:45"),
]


def build_state(bars, sess_day):
    """Recompute the race-census day state (same conventions)."""
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                & (bars.index < t1)]
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    idx = seg.index
    N = len(idx)
    ma15, w15 = bb_ma_asof(hist, 15)
    ma15_1m = ma15.reindex(idx).to_numpy()
    w15_1m = w15.reindex(idx).to_numpy()
    vw = vwap_bands(hist)
    prof = profile_at_minutes(hist, list(idx + pd.Timedelta(minutes=1)))
    S = {"poc": prof["poc"].to_numpy(), "val": prof["val"].to_numpy(),
         "vah": prof["vah"].to_numpy()}
    for b in ("vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2"):
        S[b] = vw[b].reindex(idx).to_numpy()
    dist = np.stack([np.abs(S[k] - ma15_1m) for k in MENU])
    aff = np.where(np.isfinite(w15_1m) & (w15_1m > 0),
                   np.nansum(dist <= TOLW * w15_1m, axis=0), 0).astype(int)
    which = dist <= TOLW * w15_1m

    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min",
         "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    ma_at15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1)).to_numpy()
    pos15 = np.searchsorted(idx.values, f15.index.values)
    live2 = np.zeros(N, dtype=int)
    live3 = np.zeros(N, dtype=int)
    cur2 = cur3 = 0
    for bi in range(len(f15)):
        m = ma_at15[bi]
        b_ = f15.iloc[bi]
        if not np.isfinite(m):
            continue
        if (b_.close > m) != (b_.open > m):
            cur2, cur3 = 0, (1 if b_.close > m else -1)
        elif (b_.close < m) and (b_.high >= m) and (b_.open < m):
            cur2 = -1
        elif (b_.close > m) and (b_.low <= m) and (b_.open > m):
            cur2 = +1
        a = min(pos15[bi], N)
        b2 = min(pos15[bi + 1], N) if bi + 1 < len(f15) else N
        live2[a:b2] = cur2
        live3[a:b2] = cur3

    # per-TF fresh crosses through own MA, keyed by candle END timestamp
    crosses = {}
    for tf in (1, 2, 3):
        ma_tf, _ = bb_ma_asof(hist, tf)
        if tf == 1:
            ftf = seg.copy()
            ftf.index = ftf.index + pd.Timedelta(minutes=1)
        else:
            ftf = hist.resample(f"{tf}min", label="right",
                                closed="left").agg(
                {"open": "first", "high": "max", "low": "min",
                 "close": "last"}).dropna()
            ftf = ftf[(ftf.index > t0) & (ftf.index <= t1)]
        pos = np.clip(np.searchsorted(
            idx.values, (ftf.index - pd.Timedelta(minutes=1)).values),
            0, N - 1)
        matf = ma_tf.reindex(idx).to_numpy()[pos]
        for bi, ts in enumerate(ftf.index):
            p = pos[bi]
            fo, fc = ftf.open.iloc[bi], ftf.close.iloc[bi]
            for d in (+1, -1):
                if d * (fc - matf[bi]) > 0 and d * (fo - matf[bi]) <= 0:
                    crosses.setdefault(ts, []).append(
                        (tf, d, p, (fo - ma15_1m[p]) / w15_1m[p]
                         if w15_1m[p] > 0 else np.nan))
    return dict(idx=idx, ma15=ma15_1m, w15=w15_1m, aff=aff, which=which,
                live2=live2, live3=live3, crosses=crosses, S=S,
                cl=seg.close.to_numpy())


def main():
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    F = pd.read_parquet(ROOT / "output/htf_ma_census/race_fit.parquet")
    F["t"] = pd.to_datetime(F.t)
    F = F[F.tol == TOLW]

    states = {}
    for tid, day, dr, lo, hi_, px, note in TRADES:
        w0 = pd.Timestamp(f"{day} {lo}", tz=NY)
        w1 = pd.Timestamp(f"{day} {hi_}", tz=NY)
        # session-day convention: sessions anchor at 18:00 the PRIOR
        # evening, so a morning trade on calendar day D belongs to
        # sess_day D-1.
        sd = str((w0.normalize() - pd.Timedelta(days=1)).date()) \
            if w0.hour < 18 else day
        if sd not in states:
            states[sd] = build_state(bars, sd)
        st = states[sd]
        d = 1 if dr == "long" else -1
        idx = st["idx"]

        print("=" * 100)
        print(f"{tid}  {day}  {dr.upper()} ~{px}  ({note})")
        print("=" * 100)

        rows = F[(F.dir == dr)
                 & (F.t >= w0 - pd.Timedelta(minutes=20))
                 & (F.t <= w1 + pd.Timedelta(minutes=20))]
        if len(rows):
            print("  CENSUS ROWS in +/-20min of the trade envelope:")
            for r in rows.itertuples():
                print(f"    {r.t.strftime('%H:%M')}  {r.mech}  "
                      f"tf_won={r.tf_won} (ties {r.tie_tfs})  "
                      f"n_aff={r.n_aff} [{r.aff_list}]  "
                      f"close={r.close_px:.2f}  session={r.session}")
        else:
            print("  CENSUS ROWS in +/-20min: NONE")

        print(f"  STAGE DUMP, every minute {lo}-{hi_} (window as a stage, "
              f"not a filter):")
        print(f"    {'t':5s} {'win':6s} {'M1':>5s} {'M2':>3s} {'M3':>3s} "
              f"{'aff':>3s}  crosses(tf,dir)")
        m = (idx >= w0 - pd.Timedelta(minutes=1)) & (idx <= w1)
        for j in np.where(m)[0]:
            t_end = idx[j] + pd.Timedelta(minutes=1)
            hm = t_end.hour * 60 + t_end.minute
            win = in_window(hm) or "--"
            disp = ((st["cl"][j] - st["ma15"][j])
                    / st["w15"][j]) if st["w15"][j] > 0 else np.nan
            m1s = "-"
            if np.isfinite(disp) and (-disp if d > 0 else disp) >= DISP:
                m1s = "ARM"
            cx = st["crosses"].get(t_end, [])
            cxs = " ".join(f"{tf}m{'+' if dd > 0 else '-'}"
                           f"(aff{st['aff'][p]})" for tf, dd, p, _ in cx)
            print(f"    {t_end.strftime('%H:%M')} {win:6s} "
                  f"{m1s:>5s} "
                  f"{'ARM' if st['live2'][j] == d else '-':>3s} "
                  f"{'ARM' if st['live3'][j] == d else '-':>3s} "
                  f"{st['aff'][j]:3d}  {cxs}")

        # verdict: find qualifying construction entries inside the envelope
        print("  VERDICT:")
        got = []
        for t_end in sorted(st["crosses"]):
            if not (w0 <= t_end <= w1):
                continue
            for tf, dd, p, disp_o in st["crosses"][t_end]:
                if dd != d:
                    continue
                na = int(st["aff"][p])
                if np.isfinite(disp_o) and \
                        (-disp_o if d > 0 else disp_o) >= DISP:
                    mech = "M1"
                elif st["live2"][p] == d:
                    mech = "M2"
                elif st["live3"][p] == d:
                    mech = "M3"
                else:
                    continue
                if mech != "M1" and na < 1:
                    continue
                if tf == 1 and na < 2:
                    continue
                win = in_window(t_end.hour * 60 + t_end.minute)
                got.append((t_end, tf, mech, na, win))
        if not got:
            print("    -> no construction entry fires in the envelope; "
                  "see stage dump for the kill stage")
        for t_end, tf, mech, na, win in got:
            tag = "CAUGHT" if win else \
                "FIRES ON EVERY STAGE BUT DIES AT WINDOW"
            print(f"    -> {tag}: {t_end.strftime('%H:%M')} {mech} via "
                  f"{tf}m closure, n_aff={na}, window={win or 'OUTSIDE'}")
        print()


if __name__ == "__main__":
    main()
