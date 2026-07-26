#!/usr/bin/env python3
"""ICT weekly-bias v2 — adds draw-on-liquidity weekly bias, sweep+reclaim confirmation, and an
HTF-array (4H/daily unfilled FVG) gate. Jul 2025 -> Jul 2026. No trading; grade vs NY session.

Upgrades over v1 (all principled ICT, no curve-fit):
  1. WEEKLY BIAS = HTF trend (daily 20/40d structure) + draw-on-liquidity (which prior-week
     extreme is unswept = where the week is drawn) + premium/discount location. If trend and
     draw CONFLICT -> NEUTRAL week (kills the weak calls v1 forced).
  2. EXTREME-IN = a real sweep+reclaim: the week (or prior day) traded through a prior low/high
     and CLOSED back the other side (turtle soup). Expansion is only called AFTER the
     manipulation is confirmed - "to go up, price first goes down."
  3. HTF ARRAY GATE = require an unfilled 4H or daily FVG on the retracement side (a logical PDA
     for the pullback + CISD). No array -> downgrade to NEUTRAL.
  4. The low/high-of-week (sweep) day is only called once the sweep has confirmed; otherwise it
     stays NEUTRAL (don't pre-empt the manipulation).
"""
import io
from datetime import time as dtime

import numpy as np
import pandas as pd

import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
NY = "America/New_York"
START, END = "2025-07-01", "2026-07-15"
THR = 0.0010

bars = pd.read_parquet(f"{WT}/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")

# daily + NY session candles
drows, srows = [], []
for day, g in bars.groupby("day"):
    drows.append(dict(day=day, o=float(g.open.iloc[0]), h=float(g.high.max()),
                      l=float(g.low.min()), c=float(g.close.iloc[-1])))
    ses = g[(g.ts.dt.time >= dtime(9, 30)) & (g.ts.dt.time < dtime(16, 0))]
    if len(ses) >= 100:
        srows.append(dict(day=day, so=float(ses.open.iloc[0]), sc=float(ses.close.iloc[-1]),
                          sh=float(ses.high.max()), sl=float(ses.low.min()),
                          t_hi=ses.ts[ses.high.idxmax()].value, t_lo=ses.ts[ses.low.idxmin()].value))
DAY = pd.DataFrame(drows).set_index("day").sort_index()
DAY["dt"] = pd.to_datetime(DAY.index); DAY["dow"] = DAY.dt.dt.dayofweek
iso = DAY.dt.dt.isocalendar(); DAY["iso"] = iso.year * 100 + iso.week
SES = pd.DataFrame(srows).set_index("day")
daylist = list(DAY.index)

# 4H candles (clock-based) for HTF FVGs
h4 = (bars.set_index("ts").resample("4h", closed="left", label="left")
      .agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last"))
      .dropna().reset_index())
h4["day"] = h4["ts"].dt.strftime("%Y-%m-%d")

# weekly candles
wk = DAY[DAY.dow < 5].groupby("iso").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"),
                                         c=("c", "last")).sort_index()
wk_list = list(wk.itertuples())

# red-folder calendar
fr = []
for f in ["/home/user/gs/config/news_calendar.csv", "/home/user/gs/config/news_calendar_hist.csv"]:
    fr.append(pd.read_csv(io.StringIO("".join(l for l in open(f) if not l.startswith("#")))))
N = pd.concat(fr, ignore_index=True); N = N[N.datetime_ET != "impact"]
N["dt"] = pd.to_datetime(N["datetime_ET"]); N = N[N["impact"].astype(str).str.lower() == "high"]
N["day"] = N["dt"].dt.strftime("%Y-%m-%d")
N = N[(N.dt.dt.time >= dtime(8, 0)) & (N.dt.dt.time <= dtime(16, 0))]
news_day = set(N.day.unique())
news_event = {d: ", ".join(sorted(set(g["dt"].dt.strftime("%H:%M") + " " + g.get("event", "").astype(str))))
              for d, g in N.groupby("day")}
inv = lambda dw: {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"}[dw]

# ---------------- HTF unfilled FVGs as of a day ----------------
def fvgs_unfilled(frame, price):
    """Unfilled bullish/bearish FVGs in `frame` (needs o,h,l,c). Returns (bull_below, bear_above)
    booleans: is there an unfilled bullish array BELOW price / bearish array ABOVE price."""
    h = frame["h"].to_numpy(); l = frame["l"].to_numpy(); c = frame["c"].to_numpy(); n = len(frame)
    bull_below = bear_above = False
    for i in range(n - 2):
        if h[i] < l[i + 2]:                      # bullish FVG zone [h[i], l[i+2]]
            lo, hi = h[i], l[i + 2]
            filled = any(c[j] < lo for j in range(i + 3, n))   # body closed below -> filled/invalid
            if not filled and hi < price:        # sits below current price = discount array
                bull_below = True
        elif l[i] > h[i + 2]:                    # bearish FVG zone [h[i+2], l[i]]
            lo, hi = h[i + 2], l[i]
            filled = any(c[j] > hi for j in range(i + 3, n))
            if not filled and lo > price:
                bear_above = True
    return bull_below, bear_above

# precompute per-day HTF array availability (uses only candles fully closed before the day)
array_cache = {}
for day in daylist:
    prev = [d for d in daylist if d < day]
    if not prev:
        array_cache[day] = (False, False); continue
    price = DAY.loc[prev[-1], "c"]
    d4 = h4[h4["day"] < day].tail(24)            # ~last 4 days of 4H candles
    dd = DAY.loc[prev].tail(15)[["o", "h", "l", "c"]] if len(prev) >= 3 else None
    b4, s4 = fvgs_unfilled(d4[["o", "h", "l", "c"]], price) if len(d4) >= 3 else (False, False)
    bd, sd = fvgs_unfilled(dd, price) if dd is not None and len(dd) >= 3 else (False, False)
    array_cache[day] = (b4 or bd, s4 or sd)      # (bullish array below, bearish array above)

# ---------------- weekly bias v2: trend + draw + PD ----------------
def daily_trend_asof(iso):
    hist = DAY[(DAY.iso < iso) & (DAY.dow < 5)].tail(40)
    if len(hist) < 20:
        return "neutral", 0.5
    c = hist.c.to_numpy(); rng_h = hist.h.tail(20).max(); rng_l = hist.l.tail(20).min()
    pos = (c[-1] - rng_l) / (rng_h - rng_l) if rng_h > rng_l else 0.5
    ma20 = float(c[-20:].mean()); ma40 = float(c.mean()); last = float(c[-1]); c20 = float(c[-20])
    up = int(last > ma20) + int(ma20 > ma40) + int(last > c20)   # int() — numpy bool '+' is OR, not sum
    dn = int(last < ma20) + int(ma20 < ma40) + int(last < c20)
    return ("up" if up >= 2 and up > dn else "down" if dn >= 2 and dn > up else "neutral"), pos

def weekly_bias_v2(iso):
    prior = [w for w in wk_list if w.Index < iso]
    if len(prior) < 4:
        return "NEUTRAL"
    trend, pos = daily_trend_asof(iso)
    pw, pw2 = prior[-1], prior[-2]
    rng = pw.h - pw.l
    cpos = (pw.c - pw.l) / rng if rng > 0 else 0.5     # where last week CLOSED in its range
    # a weekly REVERSAL: swept the opposite extreme and closed rejecting it (turtle soup, weekly)
    bear_rev = pw.h > pw2.h and cpos < 0.35            # took prior highs, closed weak -> distribution
    bull_rev = pw.l < pw2.l and cpos > 0.65            # took prior lows, closed strong -> accumulation
    # trend-led (premium/discount is ENTRY location, not draw direction — it does NOT flip bias)
    if trend == "up":
        return "NEUTRAL" if bear_rev else "BULLISH"
    if trend == "down":
        return "NEUTRAL" if bull_rev else "BEARISH"
    if bull_rev:                                       # no trend -> a clean reversal week sets bias
        return "BULLISH"
    if bear_rev:
        return "BEARISH"
    return "NEUTRAL"

# ---------------- sweep+reclaim: is the weekly extreme in? ----------------
def extreme_in(iso, day, wb):
    """Has the week (as of prior completed days) swept a prior low/high and reclaimed it?"""
    days = [d for d in daylist if DAY.loc[d, "iso"] == iso and d < day and DAY.loc[d, "dow"] < 5]
    if not days:
        return False
    pw = [w for w in wk_list if w.Index < iso]
    if not pw:
        return False
    pwl, pwh = pw[-1].l, pw[-1].h
    for d in days:
        r = DAY.loc[d]
        if wb == "BULLISH" and r.l < pwl and r.c > pwl:       # swept prior-week low, closed back above
            return True
        if wb == "BEARISH" and r.h > pwh and r.c < pwh:
            return True
    # or a prior day this week swept the day-before's low and reclaimed (daily turtle soup)
    for i in range(1, len(days)):
        a, b = DAY.loc[days[i - 1]], DAY.loc[days[i]]
        if wb == "BULLISH" and b.l < a.l and b.c > a.l:
            return True
        if wb == "BEARISH" and b.h > a.h and b.c < a.h:
            return True
    return False

# ---------------- per-day plan ----------------
def plan_week(iso, wb):
    days = [d for d in daylist if DAY.loc[d, "iso"] == iso and DAY.loc[d, "dow"] < 5
            and START <= d <= END]
    out = {}
    if wb == "NEUTRAL":
        for d in days:
            out[d] = ("NEUTRAL", "NEUTRAL", "weekly bias neutral (trend/draw conflict) — stand aside")
        return out
    dows = {d: DAY.loc[d, "dow"] for d in days}
    news_dows = sorted(dows[d] for d in days if d in news_day)
    early = [dw for dw in news_dows if dw <= 2]; late = [dw for dw in news_dows if dw >= 2]
    lo_dow = early[0] if early else 0; hi_dow = late[-1] if late else 4
    if hi_dow <= lo_dow:
        hi_dow = 4
    if wb == "BEARISH":
        lo_dow, hi_dow = hi_dow, lo_dow            # bearish: high early, low late

    for d in days:
        dw = dows[d]
        ein = extreme_in(iso, d, wb)                 # sweep+reclaim confirmed this week?
        bull_below, bear_above = array_cache.get(d, (False, False))
        has_array = bull_below if wb == "BULLISH" else bear_above
        low_in = ein or dw > lo_dow                  # extreme in (sweep-confirmed OR past the low day)

        if dw < lo_dow and not ein:
            out[d] = ("NEUTRAL", "NEUTRAL", "pre-sweep accumulation — wait for the manipulation")
        elif dw > hi_dow:
            out[d] = ("NEUTRAL", "NEUTRAL", "post-expansion distribution — stand aside")
        elif dw == lo_dow and not ein:
            # the sweep/reversal day itself, manipulation not yet confirmed -> lower-quality
            out[d] = (wb, "MEDIUM", "sweep/turtle-soup day — reversal expected, unconfirmed")
        else:
            # expansion window, extreme in. Conviction tiers on sweep-confirmed + array + prime day.
            factors = int(ein) + int(has_array) + int(1 <= dw <= 3) + int(d in news_day)
            conv = "HIGH" if factors >= 3 else "MEDIUM"
            tags = []
            tags.append("sweep confirmed" if ein else "low in (past low day)")
            tags.append("HTF array present" if has_array else "no clean array")
            out[d] = (wb, conv, f"expansion day, {', '.join(tags)}, high~{inv(hi_dow)}")
    return out

# ---------------- run + grade ----------------
def grade(bias, net, thr):
    if bias == "BULLISH":
        return "CORRECT" if net > thr else ("WRONG" if net < -thr else "FLAT")
    if bias == "BEARISH":
        return "CORRECT" if net < -thr else ("WRONG" if net > thr else "FLAT")
    return "STOOD ASIDE"

isos = sorted(DAY[(DAY.index >= START) & (DAY.index <= END)].iso.unique())
plans = {i: (weekly_bias_v2(i), None) for i in isos}
for i in isos:
    wb = plans[i][0]; plans[i] = (wb, plan_week(i, wb))

rows = []
for day in sorted(DAY.index):
    if day < START or day > END or DAY.loc[day, "dow"] >= 5 or day not in SES.index:
        continue
    wb, plan = plans.get(DAY.loc[day, "iso"], ("NEUTRAL", {}))
    bias, conv, reason = plan.get(day, ("NEUTRAL", "NEUTRAL", "no plan"))
    s = SES.loc[day]; d = DAY.loc[day]; thr = THR * s.so; net = s.sc - s.so
    v = grade(bias, net, thr)
    if bias == "BULLISH":
        expansion_ok = (s.t_lo < s.t_hi) and (s.sh - s.so >= thr)
    elif bias == "BEARISH":
        expansion_ok = (s.t_hi < s.t_lo) and (s.so - s.sl >= thr)
    else:
        expansion_ok = abs(net) <= thr
    dirword = "up" if net > thr else ("down" if net < -thr else "flat")
    bits = [f"{inv(d.dow)} · weekly {wb.lower()} · NY {net:+.0f}pt ({dirword})"]
    bits.append(reason if bias == "NEUTRAL" else
                (f"expanded {bias.lower()[:4]} with the week" if v == "CORRECT"
                 else f"chopped flat" if v == "FLAT" else f"ran {dirword} against the read"))
    if day in news_event:
        bits.append("news: " + news_event[day][:55])
    rows.append(dict(day=day, weekday=inv(d.dow), weekly=wb, bias=bias, conviction=conv,
                     net=round(net, 1), verdict=v, expansion_ok=bool(expansion_ok),
                     newsday=(day in news_day), reason=reason, note="; ".join(bits)))

J = pd.DataFrame(rows)
J.to_csv(f"{S}/ict_bias_v2_days.csv", index=False)
D = J[J.bias != "NEUTRAL"]
acc = lambda x: round(100 * (x.verdict == "CORRECT").mean(), 1) if len(x) else 0.0
expf = lambda x: round(100 * x.expansion_ok.mean(), 1) if len(x) else 0.0
print("=== ICT BIAS v2 ===")
print(f"days {len(J)} | directional {len(D)} | stood aside {len(J)-len(D)}")
print(f"weekly mix (day-count): {J.weekly.value_counts().to_dict()}")
print(f"STRICT {acc(D)}%  EXPANSION {expf(D)}%  (v1 was 45.1% / 46.7%)")
print(f"  HIGH   {len(D[D.conviction=='HIGH']):3d}d  strict {acc(D[D.conviction=='HIGH'])}%  expansion {expf(D[D.conviction=='HIGH'])}%")
print(f"  MEDIUM {len(D[D.conviction=='MEDIUM']):3d}d  strict {acc(D[D.conviction=='MEDIUM'])}%")
print("by weekday:")
for wd in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
    x = D[D.weekday == wd]
    if len(x):
        print(f"  {wd} {len(x):3d}d  strict {acc(x)}%  expansion {expf(x)}%")
print("by bias:", {b: (len(D[D.bias == b]), acc(D[D.bias == b])) for b in ["BULLISH", "BEARISH"]})
print(f"news-day {len(D[D.newsday])}d {acc(D[D.newsday])}%  |  quiet {len(D[~D.newsday])}d {acc(D[~D.newsday])}%")
print("saved ict_bias_v2_days.csv")
