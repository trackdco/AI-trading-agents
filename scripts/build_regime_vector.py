#!/usr/bin/env python3
"""Pass-30: daily REGIME VECTOR — the mechanical layer of the regime-adaptation design
(docs/REGIME-ADAPTATION-DESIGN.md). One row per session day, every feature computed
strictly PRE-OPEN (08:00 ET) with zero lookahead. This is the input the regime agent
receives, the baseline it must beat, and the key for the historical-analog lookup.

    python -m scripts.build_regime_vector     -> output/regime_vector.csv

Features (all trailing / as-of 08:00):
  imbal_share_20   trailing-20-day imbalanced-day share (the champion's switch)
  imbal_share_10   trailing-10-day variant
  day_type         today's pre-open overnight-vs-prior-value classification
  trap_rate_10     share of last 10 days whose 08:00-10:15 tape printed a >=1R-and-reverse
                   signature (proxy: morning range retrace >70% after first-hour extreme —
                   May's trap character, computable from bars alone)
  range_pctl_20    yesterday's morning range percentile vs trailing 20 days
  gap_open_pts     |today 08:00 price - yesterday 16:00 close|
  streak_imbal     consecutive imbalanced days entering today
  red_folder_today count of named-high-impact calendar events today (FF calendar)
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import _is_named_high, load_news_calendar  # noqa: E402

NY = "America/New_York"
NAMED = ["CPI", "PPI", "non.?farm|payroll|NFP|employment change", "JOLTS",
         "rate decision|FOMC|federal funds"]


def main():
    data = Path("data/reference/nq_1m_master.parquet")
    if not data.exists():                              # pre-pass-31 fallback
        data = Path("data/reference/nq_1m_feb_jul2026.parquet")
    df = pd.read_parquet(data)
    dt = pd.read_csv("output/amt_daytypes.csv")
    cal = load_news_calendar()                         # NOTE: covers 2026 only —
    # red_folder_today is 0 for 2023-25 until a historical FF calendar lands (flagged)

    # morning tape stats per day (for trailing features only — each day's row uses
    # PRIOR days' stats, so today's morning never leaks into today's vector)
    morn = df[(df.ts_event.dt.time >= dtime(8, 0)) & (df.ts_event.dt.time <= dtime(10, 15))]
    g = morn.groupby(morn.ts_event.dt.strftime("%Y-%m-%d"))
    stats = pd.DataFrame({
        "rng": g.apply(lambda x: x.high.max() - x.low.min(), include_groups=False),
        "open": g.apply(lambda x: x.iloc[0].open, include_groups=False),
        "close": g.apply(lambda x: x.iloc[-1].close, include_groups=False),
        "hi": g.high.max(), "lo": g.low.min(),
    })
    # trap signature: first-hour extreme then >70% retrace of the morning range
    fh = morn[morn.ts_event.dt.time <= dtime(9, 0)]
    gfh = fh.groupby(fh.ts_event.dt.strftime("%Y-%m-%d"))
    stats["fh_hi"] = gfh.high.max()
    stats["fh_lo"] = gfh.low.min()
    up_ext = (stats.fh_hi - stats.open) > (stats.open - stats.fh_lo)
    retr_up = (stats.fh_hi - stats.close) / (stats.rng.replace(0, pd.NA))
    retr_dn = (stats.close - stats.fh_lo) / (stats.rng.replace(0, pd.NA))
    stats["trap"] = ((up_ext & (retr_up > 0.7)) | (~up_ext & (retr_dn > 0.7))).astype(float)

    prev_close = df.assign(d=df.ts_event.dt.strftime("%Y-%m-%d")) \
        .groupby("d").close.last()
    open_800 = stats["open"]

    dt = dt[dt.type != "unknown"].reset_index(drop=True)
    dt["imbal"] = dt.type.eq("imbalanced").astype(float)
    dt["imbal_share_20"] = dt.imbal.rolling(20, min_periods=5).mean()
    dt["imbal_share_10"] = dt.imbal.rolling(10, min_periods=5).mean()
    # E1 fix: streak entering day i = consecutive imbalanced days ending at i-1
    streak, run = [], 0
    for v in dt.imbal:
        streak.append(run)
        run = run + 1 if v == 1 else 0
    dt["streak_imbal"] = streak

    rows = []
    days = list(dt.day)
    for i, d in enumerate(days):
        prior = [x for x in days[:i] if x in stats.index]
        trail10 = prior[-10:]
        trail20 = prior[-20:]
        trap10 = stats.loc[trail10, "trap"].mean() if len(trail10) >= 5 else None
        if trail20 and days[i - 1] in stats.index and len(trail20) >= 5:
            yrng = stats.loc[days[i - 1], "rng"]
            pctl = (stats.loc[trail20, "rng"] < yrng).mean()
        else:
            pctl = None
        pc = prev_close.get(days[i - 1]) if i > 0 else None
        op = open_800.get(d)
        gap = (op - pc) if pc is not None and op is not None else None  # SIGNED (E1 fix)
        evs = cal[cal["datetime_ET"].dt.strftime("%Y-%m-%d") == d]
        red = sum(1 for _, e in evs.iterrows()
                  if str(e.get("impact", "")).lower() == "high")          # E1: ALL high
        named = sum(1 for _, e in evs.iterrows()
                    if str(e.get("impact", "")).lower() == "high"
                    and _is_named_high(str(e.get("event", "")), NAMED))
        r = dt.iloc[i]
        rows.append(dict(day=d, day_type=r.type,
                         imbal_share_20=round(r.imbal_share_20, 3) if pd.notna(r.imbal_share_20) else None,
                         imbal_share_10=round(r.imbal_share_10, 3) if pd.notna(r.imbal_share_10) else None,
                         trap_rate_10=round(trap10, 3) if trap10 is not None else None,
                         range_pctl_20=round(pctl, 3) if pctl is not None else None,
                         gap_open_pts=round(gap, 2) if gap is not None else None,
                         streak_imbal=int(r.streak_imbal),
                         red_folder_today=red,
                         named_high_today=named,
                         # AMT auction features (v0.7): built in build_daytypes, wired here so
                         # the agent SEES today's value context and the analog metric can match on it
                         value_position=r.get("value_position"),
                         open_vs_value=r.get("open_vs_value"),
                         inventory_pts=round(r.inventory_pts, 2) if pd.notna(r.get("inventory_pts")) else None))
    out = pd.DataFrame(rows)
    out.to_csv("output/regime_vector.csv", index=False)
    print(f"wrote output/regime_vector.csv ({len(out)} days)")
    print(out.groupby(out.day.str[:7])[["imbal_share_20", "trap_rate_10"]].mean().round(2).to_string())


if __name__ == "__main__":
    main()
