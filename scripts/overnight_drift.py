#!/usr/bin/env python3
"""Overnight vs day session in index futures. Rules frozen in docs/PREREG-overnight-drift.md."""
import argparse, numpy as np, pandas as pd

def third_friday(y, m):
    d = pd.Timestamp(year=y, month=m, day=1)
    f = d + pd.Timedelta(days=(4 - d.dayofweek) % 7)
    return f + pd.Timedelta(days=14)

def roll_window(dates):
    """10 trading days ending on the third Friday of Mar/Jun/Sep/Dec."""
    td = pd.DatetimeIndex(sorted(set(dates)))
    bad = set()
    for y in range(td.min().year, td.max().year + 1):
        for m in (3, 6, 9, 12):
            tf = third_friday(y, m)
            past = td[td <= tf]
            if len(past): bad |= set(past[-10:])
    return bad

def sessions(path, cost=0.5):
    b = pd.read_parquet(path)
    t = pd.to_datetime(b.ts_event)
    t = t.dt.tz_convert("America/New_York") if t.dt.tz is not None else t.dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    b = b.set_index(t.dt.tz_localize(None))[["open","high","low","close"]].sort_index()
    b["date"] = b.index.normalize(); b["hm"] = b.index.hour * 100 + b.index.minute
    op = b[b.hm == 930].groupby("date").open.first()
    cl = b[b.hm == 1559].groupby("date").close.first()
    df = pd.concat([op.rename("open930"), cl.rename("close1600")], axis=1).dropna()
    df["prev_close"] = df.close1600.shift(1)
    df["overnight"] = df.open930 - df.prev_close - cost
    df["day"] = df.close1600 - df.open930 - cost
    df["hold24"] = df.close1600 - df.prev_close - cost
    return df.dropna()

def stats(x, label):
    x = x.dropna()
    if len(x) < 30: return None
    cum = x.cumsum(); dd = float((cum - cum.cummax()).min())
    sh = float(x.mean() / x.std() * np.sqrt(252)) if x.std() > 0 else 0.0
    se = x.std() / np.sqrt(len(x))
    return dict(leg=label, days=len(x), pts_day=float(x.mean()), t_stat=float(x.mean()/se),
                total=float(x.sum()), sharpe=sh, maxDD=dd, ret_dd=float(x.sum()/abs(dd)) if dd < 0 else np.nan,
                win=float((x > 0).mean()), worst=float(x.min()), best=float(x.max()))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--bars", required=True); ap.add_argument("--label", required=True)
    a = ap.parse_args()
    df = sessions(a.bars)
    bad = roll_window(df.index)
    for tag, d in (("roll days EXCLUDED (headline)", df[~df.index.isin(bad)]), ("all days", df)):
        rows = [r for r in (stats(d.overnight, "overnight"), stats(d.day, "day session"), stats(d.hold24, "buy & hold")) if r]
        R = pd.DataFrame(rows)
        print(f"\n{a.label} - {tag}  ({len(d):,} sessions)")
        print(R.to_string(index=False, formatters={"pts_day":"{:+.2f}".format, "t_stat":"{:+.2f}".format,
              "total":"{:+,.0f}".format, "sharpe":"{:+.2f}".format, "maxDD":"{:+,.0f}".format,
              "ret_dd":"{:.2f}".format, "win":"{:.1%}".format, "worst":"{:+,.0f}".format, "best":"{:+,.0f}".format}))
