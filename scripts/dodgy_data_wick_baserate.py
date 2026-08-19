#!/usr/bin/env python3
"""Does an abnormal news wick get traded back to the same session? (DodgysDD claim)

The load-bearing claim under his 2023 flagship setup, and the only one in the audit
that is both second-hand and cheap to settle:

    "my friend back tested it… besides one day in the last couple five months, out of
     every single data high or low made, there's only one day where they weren't hit
     in the same day"

This measures it on NQ. No entry model, no exit, no cost — a pure base rate, in the
same shape as BR-1.

TWO THINGS DECIDE WHETHER THE NUMBER MEANS ANYTHING, and both are built in:

1. "Abnormal size" is never defined in the corpus. It is therefore a SWEEP, not a
   constant: the wick must be >= k x the median wick of the prior hour, for k across
   a ladder, and every rung is published. Picking the k that reads best would be
   inventing his rule for him.

2. The claim is about NEWS wicks specifically. So the control is an equally abnormal
   wick at a NON-news minute, same session, same threshold. If ordinary abnormal
   wicks come back at the same rate, then "data" is decoration and the news timing
   contributes nothing — which is the whole substance of the setup.

Confirmability: he requires the wick to also be a 1-minute swing point, and a swing
needs k bars on both sides, so the setup is not knowable until k bars after the
candle. The return scan therefore starts at pivot-confirmation, not at the wick.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.tomtrades import autopsy as AU

NY = "America/New_York"
NEWS_MINUTES = {(8, 30), (10, 0), (14, 0)}            # ET; FOMC lands on 14:00
PIVOT_K = 2


def load_nq() -> pd.DataFrame:
    parts = [pd.read_parquet(ROOT / f).drop(columns=["roll"], errors="ignore")
             for f in ("data/reference/nq_1m_master.parquet",
                       "data/reference/nq_1m_feb_jul2026.parquet")]
    b = (pd.concat(parts, ignore_index=True).drop_duplicates("ts_event")
           .sort_values("ts_event").reset_index(drop=True))
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    return b.set_index("mi")[["open", "high", "low", "close"]]


def episodes(bars: pd.DataFrame, k_mult: float) -> pd.DataFrame:
    o, h, l_, c = (bars[x].to_numpy() for x in ("open", "high", "low", "close"))
    idx = bars.index
    up_w = h - np.maximum(o, c)
    dn_w = np.minimum(o, c) - l_

    # baseline: median wick over the prior 60 completed minutes (shifted, no self-view)
    med = (pd.Series(np.maximum(up_w, dn_w)).rolling(60, min_periods=20)
             .median().shift().to_numpy())

    shifted = idx - pd.Timedelta(hours=18)
    sday = shifted.date
    hh, mm = idx.hour.to_numpy(), idx.minute.to_numpy()
    is_news = np.array([(a, b) in NEWS_MINUTES for a, b in zip(hh, mm)])

    rows = []
    start = 0
    for end in np.flatnonzero(np.r_[sday[1:] != sday[:-1], True]) + 1:
        sl = slice(start, end)
        start = end
        N = end - sl.start
        if N < 120:
            continue
        H, L = h[sl], l_[sl]
        UW, DW, M = up_w[sl], dn_w[sl], med[sl]
        NEWS, D, IX = is_news[sl], sday[sl], idx[sl]
        for j in range(PIVOT_K, N - PIVOT_K - 1):
            if np.isnan(M[j]) or M[j] <= 0:
                continue
            for side, wick, ext in ((-1, DW[j], L[j]), (1, UW[j], H[j])):
                if wick < k_mult * M[j]:
                    continue
                # must also be a 1-minute swing point, per his stated condition
                lo_i, hi_i = j - PIVOT_K, j + PIVOT_K + 1
                if side < 0 and L[j] > L[lo_i:hi_i].min():
                    continue
                if side > 0 and H[j] < H[lo_i:hi_i].max():
                    continue
                # knowable only once the pivot confirms: scan from j+K+1
                s = j + PIVOT_K + 1
                if s >= N:
                    continue
                hit = bool(np.any((L[s:] <= ext) & (H[s:] >= ext)))
                first = int(np.argmax((L[s:] <= ext) & (H[s:] >= ext))) if hit else -1
                rows.append({
                    "ts": IX[j], "sess_day": D[j], "side": side,
                    "is_news": bool(NEWS[j]), "wick": float(wick),
                    "wick_mult": float(wick / M[j]), "ext": float(ext),
                    "out": int(hit), "mins_to_hit": first if hit else np.nan,
                    "mins_left": int(N - s),
                })
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ladder", default="2,3,5,8")
    a = ap.parse_args()

    bars = load_nq()
    print(f"NQ {len(bars):,} bars  {bars.index.min().date()} -> {bars.index.max().date()}",
          flush=True)

    rows = []
    for k in [float(x) for x in a.ladder.split(",")]:
        ep = episodes(bars, k)
        if ep.empty:
            continue
        for label, sub in (("NEWS", ep[ep.is_news]), ("control (non-news)", ep[~ep.is_news])):
            if len(sub) < 30:
                rows.append({"k": k, "cell": label, "n": len(sub)})
                continue
            lo, hi = AU.dboot_mean(sub, "out")
            rows.append({"k": k, "cell": label, "n": len(sub),
                         "days": sub.sess_day.nunique(),
                         "per_day": len(sub) / sub.sess_day.nunique(),
                         "hit_pct": 100 * sub["out"].mean(),
                         "ci_lo": 100 * lo, "ci_hi": 100 * hi,
                         "median_mins": float(sub.mins_to_hit.median())})
        n_, c_ = ep[ep.is_news], ep[~ep.is_news]
        if len(n_) >= 30 and len(c_) >= 30:
            rows[-1]["news_minus_control_pp"] = 100 * (n_["out"].mean() - c_["out"].mean())
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print("\n=== same-session return to an abnormal wick ===")
    print(t.round(2).to_string(index=False), flush=True)
    t.to_csv(ROOT / "output/dodgy_data_wick_baserate.csv", index=False)


if __name__ == "__main__":
    main()
