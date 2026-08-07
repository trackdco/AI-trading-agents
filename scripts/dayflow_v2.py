#!/usr/bin/env python3
"""Expanded day-flow substrate v2 (Angus 23-Jul round 2).

Adds the variable families round 1 skipped, and WINDOW-SPLIT labels: pre-market (fills
< 09:30) vs golden (fills >= 09:30) per-book P&L from the both-books universe, so
stand-down can be learned PER WINDOW, not per day.

New feature families:
  chop/efficiency : px path efficiency ON/PM, PM mean-crosses, ON extreme age
  delta structure : PM early-vs-late delta flip, big-print share, |z| of cvd vs 20d
  relative regime : on_range / 20d, vol_ON / 20d
  prior-day       : yesterday red, red streak, yesterday oracle_sd, gap-vs-yday agreement
  calendar/news   : day-of-week, red_folder_today, named_high_today, streak_imbal
Outputs: output/dayflow_v2.parquet (day features+labels), output/window_labels.parquet.

    python -m scripts.dayflow_v2
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
NY = "America/New_York"


def main():
    M = pd.read_parquet("output/fp_minutes.parquet")
    M.index = pd.DatetimeIndex(M.index)
    M = M.sort_index()
    hm = M.hm

    pm = M[(hm >= 480) & (hm < 570)]
    on = M[(hm >= 1080) | (hm < 480)]
    op = M[(hm >= 570) & (hm < 590)]

    F = pd.DataFrame(index=sorted(M.sday.unique()))
    F.index.name = "day"

    # --- delta structure ---
    e = pm[pm.hm < 525].groupby("sday").delta.sum()
    l = pm[pm.hm >= 525].groupby("sday").delta.sum()
    F["pm_early_delta"] = e; F["pm_late_delta"] = l
    F["pm_flip"] = (np.sign(e) != np.sign(l)).astype(float)
    v90 = pm.groupby("sday").vol.quantile(0.9).rename("v90")
    j = pm.join(v90, on="sday")
    F["big_print_share_PM"] = j[j.vol >= j.v90].groupby("sday").vol.sum() / pm.groupby("sday").vol.sum()

    # --- chop / efficiency ---
    def path_eff(g):
        p = g.vwp.dropna()
        if len(p) < 10:
            return np.nan
        return float(abs(p.iloc[-1] - p.iloc[0]) / max(p.diff().abs().sum(), 1e-9))
    F["pm_eff_path"] = pm.groupby("sday").apply(path_eff, include_groups=False)
    F["on_eff_path"] = on.groupby("sday").apply(path_eff, include_groups=False)
    F["op_eff_path"] = op.groupby("sday").apply(path_eff, include_groups=False)

    def crosses(g):
        p = g.vwp.dropna()
        if len(p) < 10:
            return np.nan
        s = np.sign(p - p.mean())
        return float((s.diff().abs() > 0).sum())
    F["pm_crosses"] = pm.groupby("sday").apply(crosses, include_groups=False)

    def extreme_age(g):
        p = g.vwp.dropna()
        if len(p) < 30:
            return np.nan
        n = len(p)
        return float(min(n - 1 - int(np.argmax(p.values)), n - 1 - int(np.argmin(p.values))))
    F["on_extreme_age"] = on.groupby("sday").apply(extreme_age, include_groups=False)

    # --- carry over v1 features + labels, add relative/z/prior-day/calendar ---
    D1 = pd.read_parquet("output/dayflow_features.parquet")
    F = D1.join(F, how="left")
    for c in ("cvd_ON", "cvd_PM"):
        F[f"z_{c}"] = F[c] / F[c].rolling(20, min_periods=10).std().shift(1)
        F[f"absz_{c}"] = F[f"z_{c}"].abs()
    F["rel_range"] = F.on_range / F.on_range.rolling(20, min_periods=10).median().shift(1)
    F["rel_vol"] = F.vol_ON / F.vol_ON.rolling(20, min_periods=10).median().shift(1)

    B = pd.read_csv("output/allyears_daily_books_r1r2.csv").set_index("day")
    allred = ((B[["E3", "E4"]].max(axis=1) <= 0).astype(int)).rename("red")
    F["yday_red"] = allred.shift(1).reindex(F.index)
    st = []
    run = 0
    for d in B.index:
        st.append(run)
        run = run + 1 if allred.loc[d] else 0
    F["red_streak"] = pd.Series(st, index=B.index).reindex(F.index)
    F["yday_orc"] = B.oracle_sd.shift(1).reindex(F.index)
    F["dow"] = pd.to_datetime(F.index).dayofweek

    V = pd.read_csv("output/regime_vector.csv").set_index("day")
    for c in ("red_folder_today", "named_high_today", "streak_imbal", "gap_vs_value"):
        if c in V:
            F[c] = pd.to_numeric(V[c], errors="coerce").reindex(F.index)

    # --- WINDOW-SPLIT labels from the both-books trade universe ---
    T = pd.read_parquet("output/trade_angles.parquet")
    T["t"] = T.fillmi.dt.hour * 60 + T.fillmi.dt.minute
    T["win_"] = np.where(T.t < 570, "pre", "gold")
    W = T.groupby(["day", "win_", "book"]).dollars.sum().unstack(["win_", "book"]).fillna(0.0)
    W.columns = [f"{w}_{b}" for w, b in W.columns]
    for w in ("pre", "gold"):
        cols = [c for c in (f"{w}_E3", f"{w}_E4") if c in W]
        has = T[T.win_ == w].groupby("day").size().reindex(W.index).fillna(0) > 0
        W[f"{w}_red"] = np.where(has, (W[cols].max(axis=1) <= 0).astype(float), np.nan)
    W.to_parquet("output/window_labels.parquet")
    F = F.join(W, how="left")
    F.to_parquet("output/dayflow_v2.parquet")
    n_new = F.shape[1] - D1.shape[1]
    print(f"wrote output/dayflow_v2.parquet: {len(F)} days x {F.shape[1]} cols (+{n_new} new)")
    print(f"window labels: pre_red rate {F.pre_red.mean():.2f} (n={int(F.pre_red.notna().sum())}), "
          f"gold_red rate {F.gold_red.mean():.2f} (n={int(F.gold_red.notna().sum())})")
    print(f"pre vs gold red agreement: {(F.pre_red == F.gold_red).mean():.2f}")


if __name__ == "__main__":
    main()
