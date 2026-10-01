#!/usr/bin/env python3
"""ES false-breakdown reclaim (long only). Rules frozen in docs/PREREG-es-false-breakdown.md.
Exits scanned from the bar AFTER entry; a bar touching both stop and target counts STOP."""
import argparse, numpy as np, pandas as pd

TICK = 0.25
RTH_OPEN, RTH_CLOSE, LAST_ENTRY = 9*60+30, 16*60, 15*60
ON_START = 18*60          # overnight starts 18:00 ET prior evening
MHL_START = 5*60+30       # multi-hour window 05:30-09:29

def roll_days(idx):
    """2nd Thursday of Mar/Jun/Sep/Dec, plus the following day."""
    out = set()
    for y in range(idx.year.min(), idx.year.max()+1):
        for m in (3,6,9,12):
            d = pd.Timestamp(year=y, month=m, day=1)
            thurs = [d + pd.Timedelta(days=k) for k in range(31)
                     if (d + pd.Timedelta(days=k)).month == m
                     and (d + pd.Timedelta(days=k)).dayofweek == 3]
            r = thurs[1]
            out.add(r.date()); out.add((r + pd.Timedelta(days=1)).date())
    return out

def build(df):
    idx = df.index
    tmin = (idx.hour*60 + idx.minute).values
    cal = idx.normalize()
    # session date: evening bars (>=18:00) belong to the NEXT trading day
    sess = np.where(tmin >= ON_START, (cal + pd.Timedelta(days=1)).values, cal.values)
    df = df.copy()
    df["tmin"] = tmin; df["sess"] = sess; df["cal"] = cal.values
    return df

def levels(df):
    """Per session date: PDL (prev RTH low), ONL (overnight low), MHL (05:30-09:29 low)."""
    rth = df[(df.tmin >= RTH_OPEN) & (df.tmin < RTH_CLOSE)]
    rth_low = rth.groupby("cal")["low"].min()
    prev_low = rth_low.shift(1)                      # previous RTH session low
    pre = df[df.tmin < RTH_OPEN]                     # 18:00 prev evening -> 09:29
    onl = pre.groupby("sess")["low"].min()
    mh = df[(df.tmin >= MHL_START) & (df.tmin < RTH_OPEN)]
    mhl = mh.groupby("sess")["low"].min()
    lv = pd.DataFrame({"ONL": onl, "MHL": mhl})
    lv["PDL"] = prev_low.reindex(lv.index).values if False else np.nan
    # PDL keyed by calendar date of the session
    pdl = prev_low.copy(); pdl.index = pdl.index
    lv["PDL"] = pdl.reindex(lv.index).values
    return lv

def scan_session(bars, level, target, cost):
    """bars: RTH bars of one session, ascending. Returns a trade dict or None."""
    t = bars.tmin.values; h = bars.high.values; l = bars.low.values; c = bars.close.values
    n = len(c)
    broke = False; dip = np.inf; reclaim = -1
    for i in range(n):
        if t[i] >= LAST_ENTRY: return None
        if not broke:
            if l[i] < level: broke = True; dip = l[i]
            continue
        dip = min(dip, l[i])
        if reclaim < 0:
            if c[i] > level: reclaim = i
            continue
        # reclaim happened on a previous bar: this bar is the "hang" test
        if c[i] > level:
            E = c[i]; stop = dip - TICK; risk = E - stop
            if risk <= 0: return None
            tgt = E + target
            for k in range(i+1, n):
                if l[k] <= stop:
                    pnl = -risk; res = "STOP"; break
                if h[k] >= tgt:
                    pnl = target; res = "TARGET"; break
            else:
                pnl = c[n-1] - E; res = "FLAT"; k = n-1
            return dict(entry=float(E), stop=float(stop), risk=float(risk),
                        rr=target/risk, res=res, pnl=float(pnl),
                        r=(pnl - cost)/risk, bars_held=k-i, i_entry=i, n=n)
        else:
            reclaim = -1                 # failed to hang; wait for a fresh reclaim
            if l[i] < level: dip = min(dip, l[i])
    return None

def random_match(bars, risk, target, cost, rng):
    """Same session, same risk and target, entry at a uniformly random RTH bar."""
    t = bars.tmin.values; h = bars.high.values; l = bars.low.values; c = bars.close.values
    ok = np.where(t < LAST_ENTRY)[0]
    if len(ok) < 2: return None
    i = int(rng.choice(ok[:-1])); n = len(c)
    E = c[i]; stop = E - risk; tgt = E + target
    for k in range(i+1, n):
        if l[k] <= stop: pnl = -risk; break
        if h[k] >= tgt:  pnl = target; break
    else:
        pnl = c[n-1] - E
    return (pnl - cost)/risk

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost", type=float, default=0.50)
    ap.add_argument("--targets", default="10,12,15")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--maxrisk", type=float, default=0.0, help="skip setups whose stop is wider than this (0=off)")
    a = ap.parse_args()

    df = build(pd.read_parquet("data/reference/algotrader_3min/ES_3min.parquet"))
    bad = roll_days(df.index)
    lv = levels(df)
    rth = df[(df.tmin >= RTH_OPEN) & (df.tmin < RTH_CLOSE)]
    groups = {k: v for k, v in rth.groupby("cal")}
    sess_dates = sorted(d for d in groups
                        if pd.Timestamp(d).date() not in bad and d in lv.index)
    rng = np.random.default_rng(a.seed)
    span_weeks = (pd.Timestamp(sess_dates[-1]) - pd.Timestamp(sess_dates[0])).days / 7.0

    rows = []; per_trade = []
    for tgt in [float(x) for x in a.targets.split(",")]:
        for lvname in ("PDL", "ONL", "MHL"):
            trades = []; ctrl = []
            for d in sess_dates:
                level = lv.at[d, lvname]
                if not np.isfinite(level): continue
                b = groups[d]
                tr = scan_session(b, level, tgt, a.cost)
                if tr is None: continue
                if a.maxrisk and tr["risk"] > a.maxrisk: continue
                tr.update(day=str(pd.Timestamp(d).date()), level=lvname, target=tgt)
                trades.append(tr)
                r = random_match(b, tr["risk"], tgt, a.cost, rng)
                if r is not None: ctrl.append(r)
            if not trades: continue
            t = pd.DataFrame(trades); per_trade.append(t)
            r = t.r.values
            half = len(sess_dates)//2
            cut = str(pd.Timestamp(sess_dates[half]).date())
            h1 = t[t.day < cut].r; h2 = t[t.day >= cut].r
            rows.append(dict(
                target=tgt, level=lvname, n=len(t), per_wk=len(t)/span_weeks,
                R=r.mean(), netR=r.sum(),
                win=(t.res == "TARGET").mean(),
                medRR=t.rr.median(), medRisk=t.risk.median(),
                t_stat=r.mean()/(r.std(ddof=1)/np.sqrt(len(r))) if len(r) > 2 else np.nan,
                H1=h1.mean() if len(h1) else np.nan, H2=h2.mean() if len(h2) else np.nan,
                rand=np.mean(ctrl) if ctrl else np.nan,
                edge=r.mean() - (np.mean(ctrl) if ctrl else np.nan),
                flat=(t.res == "FLAT").mean()))
    res = pd.DataFrame(rows)
    pd.set_option("display.width", 200, "display.max_columns", 50)
    print(f"ES 3-min | {len(sess_dates)} sessions | {span_weeks:.0f} weeks | "
          f"{pd.Timestamp(sess_dates[0]).date()} to {pd.Timestamp(sess_dates[-1]).date()} | "
          f"cost {a.cost} pt\n")
    print(res.to_string(index=False, float_format=lambda x: f"{x:+.4f}" if abs(x) < 10 else f"{x:,.1f}"))
    all_t = pd.concat(per_trade)
    all_t.to_csv(f"data/debug/es_false_breakdown_trades_mr{int(a.maxrisk)}.csv", index=False)
    print("\nrisk (stop distance, pts) distribution across all trades:")
    print(all_t.risk.describe(percentiles=[.1,.25,.5,.75,.9]).to_string())
    print("\noutcome mix by level (target 12):")
    sub = all_t[all_t.target == 12]
    if len(sub): print(pd.crosstab(sub.level.values, sub.res.values, normalize="index").to_string(float_format=lambda x: f"{x:.1%}"))

if __name__ == "__main__":
    main()
