#!/usr/bin/env python3
"""Tier-A free feature discovery (Angus overnight, 20 Jul): compute candidate pre-open
features from the 1m master + AMT levels, and MEASURE each one's book-choice / stand-down
discrimination against the floored oracle books. Keep only what beats noise — the same
measure-before-believe discipline that killed AMT-in-the-analog-metric.

Candidates:
  on_compression   overnight (18:00->08:00) range / trailing-20d median overnight range
  on_nr_rank       overnight range percentile vs trailing 20 sessions (low = coiled)
  open_loc_on      where 08:00 opens within the overnight range (0=low,1=high)
  gap_vs_value     08:00 vs prior day's value area: into_value / above / below
  pdc_loc          prior day's close location within its own range (0..1)
  pdc_out_value    prior close outside prior value area? (+1 above / -1 below / 0 in)
  vol_bandwidth    20d Bollinger bandwidth of daily closes (contraction<->expansion)

    python -m scripts.measure_candidate_features   -> output/candidate_features.csv + report
"""
import sys
from datetime import time as dtime
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.engine.data import _session_date  # noqa: E402

NY = "America/New_York"


def main():
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    df = df.assign(_sd=_session_date(df["ts_event"], dtime(18, 0)))
    amt = pd.read_csv("output/amt_daytypes.csv")
    B = pd.read_csv("output/allyears_daily_books_r1r2.csv")[["day", "E3", "E4"]]

    # per-session overnight (18:00 prior -> 08:00) and prior-day RTH stats
    on = df[df["ts_event"].dt.time < dtime(8, 0)]
    g = on.groupby("_sd")
    onr = (g.high.max() - g.low.min())
    onlo, onhi = g.low.min(), g.high.max()
    op = df[(df["ts_event"].dt.time >= dtime(8, 0))].groupby("_sd").first()["open"]
    # prior full-session (RTH-ish) range/close from all bars that session
    daily = df.groupby("_sd").agg(hi=("high", "max"), lo=("low", "min"),
                                  close=("close", "last"))
    rows = []
    sds = sorted(df["_sd"].unique())
    for i, sd in enumerate(sds):
        d = str(sd)
        prior = sds[:i]
        rec = {"day": d}
        # overnight compression
        if sd in onr.index and onr.loc[sd] > 0:
            r = onr.loc[sd]
            hist = [onr.loc[s] for s in prior[-20:] if s in onr.index]
            if len(hist) >= 10:
                rec["on_compression"] = round(r / np.median(hist), 3)
                rec["on_nr_rank"] = round((np.array(hist) < r).mean(), 3)
        # opening location within overnight range
        if sd in op.index and sd in onhi.index and (onhi.loc[sd] - onlo.loc[sd]) > 0:
            rec["open_loc_on"] = round((op.loc[sd] - onlo.loc[sd]) /
                                       (onhi.loc[sd] - onlo.loc[sd]), 3)
        # prior-day close location + outside-value
        if i > 0 and sds[i-1] in daily.index:
            pd_ = daily.loc[sds[i-1]]
            if pd_.hi > pd_.lo:
                rec["pdc_loc"] = round((pd_.close - pd_.lo) / (pd_.hi - pd_.lo), 3)
        # vol bandwidth (20d BB of daily closes)
        cl = [daily.loc[s].close for s in prior[-20:] if s in daily.index]
        if len(cl) >= 15:
            m, sd_ = np.mean(cl), np.std(cl)
            rec["vol_bandwidth"] = round(4 * sd_ / m * 100, 3) if m else None
        rows.append(rec)
    feat = pd.DataFrame(rows)
    # gap vs prior value + prior-close-vs-value from amt levels
    a = amt[["day", "prior_vah", "prior_val", "prior_poc", "on_vah", "on_val"]].copy()
    feat = feat.merge(a, on="day", how="left")
    op_map = op.copy(); op_map.index = op_map.index.astype(str)
    feat["open800"] = feat.day.map(op_map)
    def gap_v(r):
        if pd.isna(r.open800) or pd.isna(r.prior_vah): return None
        if r.open800 > r.prior_vah: return "above"
        if r.open800 < r.prior_val: return "below"
        return "into_value"
    feat["gap_vs_value"] = feat.apply(gap_v, axis=1)
    feat.to_csv("output/candidate_features.csv", index=False)

    # ---- MEASURE discrimination vs floored oracle (book choice + flat) ----
    m = feat.merge(B, on="day").copy()
    m = m[m.day.str[:4].isin(["2023","2024","2025","2026"])]
    m["act"] = np.where(m[["E3","E4"]].max(axis=1) <= 0, "FLAT",
                        np.where(m.E3 >= m.E4, "ROTATION", "MOMENTUM"))
    def report(col, bins=None, labels=None, cat=False):
        d = m.dropna(subset=[col]).copy()
        if len(d) < 40: 
            print(f"\n[{col}] insufficient data ({len(d)})"); return
        d["bucket"] = d[col] if cat else pd.cut(d[col], bins, labels=labels)
        t = d.groupby("bucket", observed=True).apply(lambda x: pd.Series({
            "n": len(x),
            "flat%": round((x.act=="FLAT").mean()*100),
            "rot%": round((x.act=="ROTATION").mean()*100),
            "mom%": round((x.act=="MOMENTUM").mean()*100)}), include_groups=False)
        mom_spread = t["mom%"].max() - t["mom%"].min()
        flat_spread = t["flat%"].max() - t["flat%"].min()
        print(f"\n[{col}]  book-lean swing {mom_spread:.0f}pts | flat swing {flat_spread:.0f}pts")
        print(t.to_string())
    print("="*70)
    print("CANDIDATE FEATURE DISCRIMINATION (full history, floored books)")
    print("book-lean swing = how much the momentum-best-rate moves across buckets")
    print("="*70)
    report("on_compression", [0,.7,1.0,1.4,99], ["coiled<.7",".7-1",".1-1.4",">1.4"])
    report("on_nr_rank", [-.01,.25,.75,1.01], ["low(coiled)","mid","high"])
    report("open_loc_on", [-.01,.25,.75,1.01], ["low","mid","high"])
    report("pdc_loc", [-.01,.33,.67,1.01], ["closed-low","mid","closed-high"])
    report("vol_bandwidth", bins=[0,2,4,6,99], labels=["tight<2","2-4","4-6",">6"])
    report("gap_vs_value", cat=True)


if __name__ == "__main__":
    main()
