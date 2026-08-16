#!/usr/bin/env python3
"""T1/T2 FORENSIC RE-DERIVATION — finest available resolution.

The substrate is 1-minute bars plus per-minute footprint; there is no
tick stream in this repo, so "tick level" here means: every candle the
construction saw, every MA value it priced, every condition it tested,
printed raw — plus parity checks of our BB MA values against the exact
values visible on the trader's own TradingView screenshots.

T1 = 2026-06-01 (sess_day 2026-05-31), SHORT, fill ~30,445-455 @
~09:49-50 per screenshots.
T2 = 2026-06-02 (sess_day 2026-06-01), LONG, fill ~30,479.25 @
~09:44-47 per screenshots (called clean earlier, never re-verified).

    python -m scripts.trade_audit_t1t2
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.trigger_race_census import (MENU, TOLW, in_window,     # noqa: E402
                                         m1_episode_arrays)
from src.htf_ma.levels import (NY, bb_ma_asof, profile_at_minutes,  # noqa: E402
                               vwap_bands)

TRADES = [
    ("T1", "2026-05-31", "2026-06-01", -1, "09:40", "09:58", 30450.0,
     "SHORT; screenshots put the fill ~30,445-455 around 09:49-50"),
    ("T2", "2026-06-01", "2026-06-02", +1, "09:38", "09:52", 30479.25,
     "LONG; screenshots put the fill ~30,479.25 around 09:44-47"),
]
PARITY = [
    ("2026-05-31", 1, "2026-06-01 09:59", 30405.18,
     "Jun-1 1m chart, replay bar 09:59"),
    ("2026-05-31", 2, "2026-06-01 09:47", 30382.96,
     "Jun-1 2m chart, replay ~09:47-48"),
    ("2026-05-31", 2, "2026-06-01 09:49", 30382.96, "  (next minute)"),
    ("2026-06-01", 1, "2026-06-02 09:53", 30504.70,
     "Jun-2 1m chart, replay bar 09:53"),
]


def day_state(bars, sess_day):
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t1 = t0 + pd.Timedelta(hours=23)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                & (bars.index < t1)]
    seg = hist[(hist.index >= t0) & (hist.index < t1)]
    idx = seg.index
    ma15, w15 = bb_ma_asof(hist, 15)
    ma15_1m = ma15.reindex(idx).to_numpy()
    w15_1m = w15.reindex(idx).to_numpy()
    armed1, epi1 = m1_episode_arrays(seg.high.to_numpy(),
                                     seg.low.to_numpy(),
                                     seg.close.to_numpy(),
                                     ma15_1m, w15_1m)
    vw = vwap_bands(hist)
    prof = profile_at_minutes(hist, list(idx + pd.Timedelta(minutes=1)))
    S = {"poc": prof["poc"].to_numpy(), "val": prof["val"].to_numpy(),
         "vah": prof["vah"].to_numpy()}
    for b in ("vwap", "vwap_p1", "vwap_m1", "vwap_p2", "vwap_m2"):
        S[b] = vw[b].reindex(idx).to_numpy()
    dist = np.stack([np.abs(S[k] - ma15_1m) for k in MENU])
    aff = np.where(np.isfinite(w15_1m) & (w15_1m > 0),
                   np.nansum(dist <= TOLW * w15_1m, axis=0), 0).astype(int)

    f15 = hist.resample("15min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min",
         "close": "last"}).dropna()
    f15 = f15[(f15.index > t0) & (f15.index <= t1)]
    ma_at15 = ma15.reindex(f15.index - pd.Timedelta(minutes=1)).to_numpy()
    pos15 = np.searchsorted(idx.values, f15.index.values)
    N = len(idx)
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
    return dict(hist=hist, seg=seg, idx=idx, ma15=ma15_1m, w15=w15_1m,
                armed1=armed1, epi1=epi1, live2=live2, live3=live3,
                aff=aff)


def main():
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low",
                                              "close", "volume"]]
    C = pd.read_parquet(ROOT /
                        "output/htf_ma_census/race_fit_m1episode.parquet")
    C["t"] = pd.to_datetime(C.t)
    E = pd.read_parquet(ROOT /
                        "output/htf_ma_census/race_outcomes_epi.parquet")
    E["t"] = pd.to_datetime(E.t)

    states = {}

    print("=" * 100)
    print("MA PARITY vs THE TRADER'S OWN CHART VALUES (TradingView "
          "BB(20, close, 2) read off the screenshots)")
    print("=" * 100)
    for sd, tf, when, tv, note in PARITY:
        if sd not in states:
            states[sd] = day_state(bars, sd)
        st = states[sd]
        ma_tf, _ = bb_ma_asof(st["hist"], tf)
        t = pd.Timestamp(when, tz=NY)
        ours = float(ma_tf.reindex(st["idx"]).asof(t))
        print(f"  {note:40s} TV {tv:10.2f}  ours {ours:10.2f}  "
              f"diff {ours - tv:+7.2f}")

    for tid, sd, cal, d, lo_, hi_, fill, note in TRADES:
        st = states.setdefault(sd, day_state(bars, sd))
        idx, seg = st["idx"], st["seg"]
        w0 = pd.Timestamp(f"{cal} {lo_}", tz=NY)
        w1 = pd.Timestamp(f"{cal} {hi_}", tz=NY)
        print("\n" + "=" * 100)
        print(f"{tid}  {cal}  {'SHORT' if d < 0 else 'LONG'}  ({note})")
        print("=" * 100)

        m = (idx >= w0) & (idx <= w1)
        print("\n1m TRACE (close vs the 1m MA and the 15m MA; * = his "
              "approx fill price traded this minute):")
        ma1 = bb_ma_asof(st["hist"], 1)[0].reindex(idx).to_numpy()
        for j in np.where(m)[0]:
            row = seg.iloc[j]
            star = "*" if row.low <= fill <= row.high else " "
            print(f"   {idx[j].strftime('%H:%M')}{star} O{row.open:9.2f} "
                  f"H{row.high:9.2f} L{row.low:9.2f} C{row.close:9.2f}  "
                  f"1mMA {ma1[j]:9.2f} ({row.close - ma1[j]:+7.2f})  "
                  f"15mMA {st['ma15'][j]:9.2f} "
                  f"({row.close - st['ma15'][j]:+7.2f})")

        for tf in (1, 2, 3):
            ma_tf, _ = bb_ma_asof(st["hist"], tf)
            if tf == 1:
                ftf = seg.copy()
                ftf.index = ftf.index + pd.Timedelta(minutes=1)
            else:
                ftf = st["hist"].resample(f"{tf}min", label="right",
                                          closed="left").agg(
                    {"open": "first", "high": "max", "low": "min",
                     "close": "last"}).dropna()
            pos = np.clip(np.searchsorted(
                idx.values, (ftf.index - pd.Timedelta(minutes=1)).values),
                0, len(idx) - 1)
            matf = ma_tf.reindex(idx).to_numpy()[pos]
            print(f"\n{tf}m CANDLES in the envelope — every condition, "
                  f"pass/fail:")
            print(f"   {'end':5s} {'O':>9s} {'C':>9s} {'MA(tf)':>9s} "
                  f"{'openOK':>6s} {'thru':>5s} {'mech':>4s} {'aff':>3s} "
                  f"{'verdict'}")
            for bi, ts in enumerate(ftf.index):
                if not (w0 <= ts <= w1):
                    continue
                p = pos[bi]
                ma_ = matf[bi]
                fo, fc = ftf.open.iloc[bi], ftf.close.iloc[bi]
                open_ok = d * (fo - ma_) <= 0
                thru = d * (fc - ma_) > 0
                if st["armed1"][p] == d:
                    mech = "M1"
                elif st["live2"][p] == d:
                    mech = "M2"
                elif st["live3"][p] == d:
                    mech = "M3"
                else:
                    mech = "-"
                na = int(st["aff"][p])
                if not thru:
                    verdict = "no close through MA"
                elif not open_ok:
                    verdict = "NOT FRESH (open already through)"
                elif mech == "-":
                    verdict = "no thesis armed"
                elif mech != "M1" and na < 1:
                    verdict = "no affirmation"
                elif tf == 1 and na < 2:
                    verdict = "1m gate (aff<2)"
                else:
                    verdict = ">>> EMIT"
                print(f"   {ts.strftime('%H:%M')} {fo:9.2f} {fc:9.2f} "
                      f"{ma_:9.2f} {'Y' if open_ok else 'n':>6s} "
                      f"{'Y' if thru else 'n':>5s} {mech:>4s} {na:3d} "
                      f"{verdict}")

        dr = "short" if d < 0 else "long"
        rows = C[(C.sess_day == sd) & (C.dir == dr)
                 & (C.t >= w0) & (C.t <= w1 + pd.Timedelta(minutes=10))]
        print("\nCENSUS ROWS (episode) in/near the envelope:")
        for r in rows.itertuples():
            print(f"   {r.t.strftime('%H:%M')} {r.mech} tf_won={r.tf_won} "
                  f"n_aff={r.n_aff} close={r.close_px:.2f}")
        er = E[(E.sess_day == sd) & (E.dir == dr)
               & (E.t >= w0) & (E.t <= w1 + pd.Timedelta(minutes=10))]
        for r in er.itertuples():
            print(f"   OUTCOME ROW: t={r.t.strftime('%H:%M')} {r.mech} "
                  f"entry={r.entry:.2f} stop={r.stop:.2f} "
                  f"risk={r.risk:.2f}")
            adv = d * (r.entry - fill)   # + = HIS fill beats the construction
            print(f"   HIS FILL ~{fill:.2f} vs construction {r.entry:.2f}: "
                  f"his fill is {abs(adv):.2f}pt "
                  f"{'BETTER' if adv > 0 else 'worse'} "
                  f"({adv / r.risk:+.2f}R at this fight's risk)")


if __name__ == "__main__":
    main()
