#!/usr/bin/env python3
"""Deep per-trade CVD sweep (Angus 23-Jul autonomous deep-dive).

Every CVD angle computable AT the moment a trade fills, tested per setup (A/B/B2) on the
970-trade both-books/all-days universe, out-of-fit 2025 vs 2026. A signal survives only if
the on-vs-off direction agrees in BOTH years with a >=$60/t gap and n>=12 per cell.

Angles:
  conf_ON / conf_LON / conf_PM : session-window CVD sign agrees with trade direction
  conf_sess    : cumulative session delta at fill agrees with direction
  conf_last15/30 : delta of the last 15/30 minutes before fill agrees (tape momentum into entry)
  fade_last15  : last-15m delta OPPOSES direction (entering against the tape)
  path_hi / path_lo : session CVD path position at fill (top/bottom quartile of day's CVD range)
  div15        : last-15m price move disagrees with last-15m delta (divergence into entry)
  strength quartiles of |cvd_PM| among PM-confirmed trades (is bigger conviction better?)

    python -m scripts.trade_angles
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.dayflow_features import minute_table
NY = "America/New_York"


def main():
    cache = Path("output/fp_minutes.parquet")
    if cache.exists():
        M = pd.read_parquet(cache)
        M.index = pd.DatetimeIndex(M.index)
    else:
        M = minute_table()
        M.to_parquet(cache)
    M = M.sort_index()
    cum = M.groupby("sday").delta.cumsum()
    M["cum"] = cum
    day_min = M.groupby("sday").cum.transform("cummin")
    day_max = M.groupby("sday").cum.transform("cummax")
    M["pathpos"] = (M.cum - day_min) / (day_max - day_min).replace(0, np.nan)
    # price proxy per minute for divergence
    M["px"] = M.vwp

    D = pd.read_parquet("output/dayflow_features.parquet")[
        ["cvd_ON", "cvd_LON", "cvd_PM"]]
    S = pd.read_parquet("output/universal_orderflow.parquet")
    S["fillmi"] = pd.to_datetime(S.fill, utc=True, format="mixed").dt.tz_convert(NY).dt.floor("min")
    S = S.join(D, on="day")

    def sgn_conf(v, direction):
        return int((v > 0 and direction == "long") or (v < 0 and direction == "short"))

    rows = []
    for t in S.itertuples():
        try:
            upto = M.loc[:t.fillmi]
            w15 = upto[upto.index >= t.fillmi - pd.Timedelta(minutes=15)]
            w30 = upto[upto.index >= t.fillmi - pd.Timedelta(minutes=30)]
            at = upto.iloc[-1]
            if str(at.sday) != t.day:
                rows.append({}); continue
        except Exception:
            rows.append({}); continue
        d15, d30 = w15.delta.sum(), w30.delta.sum()
        px15 = (w15.px.iloc[-1] - w15.px.iloc[0]) if len(w15) > 1 else 0.0
        rows.append(dict(
            conf_ON=sgn_conf(t.cvd_ON, t.direction), conf_LON=sgn_conf(t.cvd_LON, t.direction),
            conf_PM=sgn_conf(t.cvd_PM, t.direction), conf_sess=sgn_conf(at.cum, t.direction),
            conf_last15=sgn_conf(d15, t.direction), conf_last30=sgn_conf(d30, t.direction),
            fade_last15=sgn_conf(-d15, t.direction),
            path_hi=int(at.pathpos >= 0.75) if at.pathpos == at.pathpos else np.nan,
            path_lo=int(at.pathpos <= 0.25) if at.pathpos == at.pathpos else np.nan,
            div15=int(np.sign(px15) != np.sign(d15) and abs(px15) > 3 and abs(d15) > 100)))
    X = pd.DataFrame(rows, index=S.index)
    S = pd.concat([S, X], axis=1).dropna(subset=["conf_sess"])
    S["win"] = S.dollars > 0
    S.to_parquet("output/trade_angles.parquet")
    sigs = ["conf_ON", "conf_LON", "conf_PM", "conf_sess", "conf_last15", "conf_last30",
            "fade_last15", "path_hi", "path_lo", "div15"]
    print(f"{len(S)} trades scored\n")
    print("SURVIVORS (both years same direction, >=$60/t gap, n>=12 both cells) + near-misses:")
    for setup in ["A", "B", "B2"]:
        d = S[S.pattern == setup]
        print(f"\n===== {setup}  n={len(d)}  base ${d.dollars.mean():+.0f}/t =====")
        for s in sigs:
            cells = {}
            ok = True
            for yr in (2025, 2026):
                dy = d[d.yr == yr]
                on, off = dy[dy[s] == 1], dy[dy[s] == 0]
                if len(on) < 12 or len(off) < 12:
                    ok = False; break
                cells[yr] = (on.dollars.mean(), off.dollars.mean(), len(on), len(off),
                             on.win.mean(), off.win.mean())
            if not ok:
                continue
            g25 = cells[2025][0] - cells[2025][1]; g26 = cells[2026][0] - cells[2026][1]
            tag = "SURVIVES" if (g25 * g26 > 0 and abs(g25) >= 60 and abs(g26) >= 60) else (
                  "  near  " if g25 * g26 > 0 and min(abs(g25), abs(g26)) >= 30 else None)
            if tag:
                c5, c6 = cells[2025], cells[2026]
                print(f"  [{tag}] {s:12s} 2025 on{c5[2]:3d} ${c5[0]:+5.0f} off{c5[3]:3d} ${c5[1]:+5.0f}   "
                      f"2026 on{c6[2]:3d} ${c6[0]:+5.0f} off{c6[3]:3d} ${c6[1]:+5.0f}")
    # strength: among PM-confirmed B2, quartiles of |cvd_PM|
    print("\n--- B2 & conf_PM==1: |cvd_PM| strength quartiles ---")
    b2 = S[(S.pattern == "B2") & (S.conf_PM == 1)].copy()
    for yr in (2025, 2026):
        d = b2[b2.yr == yr]
        q = pd.qcut(d.cvd_PM.abs(), 4, labels=False, duplicates="drop")
        tab = d.groupby(q).dollars.agg(["count", "mean"])
        print(f"  {yr}: " + " | ".join(f"Q{int(k)+1} n{int(r['count'])} ${r['mean']:+.0f}" for k, r in tab.iterrows()))


if __name__ == "__main__":
    main()
