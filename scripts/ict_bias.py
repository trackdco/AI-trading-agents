#!/usr/bin/env python3
"""ICT weekly-anchored daily bias — Jul 2025 -> Jul 2026. No trading; grade the read.

Framework (the user's, faithfully mechanized):
  1. WEEKLY BIAS first (top-down). A bullish week expands UP: low placed Mon/Tue, high Thu/Fri;
     both extremes form in HTF arrays. Bearish mirrors. Determined from completed WEEKLY candles
     only (structure + momentum), fixed for the whole week -> no lookahead.
  2. The ECONOMIC CALENDAR (red folder = high-impact) decides WHICH day places the low/high.
     Bullish week: the low prints on the early-week news day (turtle soup / judas), the high on
     the late-week news day. Quiet early days = accumulation. News is scheduled -> known Monday.
  3. NEVER counter-weekly. Daily bias is EITHER the weekly direction (on expansion days) or
     NEUTRAL. No shorts in a bullish week, ever. Most days are NEUTRAL -> don't trade every day.
  4. Conviction: expansion days Tue-Thu with the low already in = HIGH; the sweep/reversal day
     itself, or Mon/Fri expansion = MEDIUM; everything else NEUTRAL.

GRADING (user rule): CORRECT only if the NY SESSION (09:30->16:00) follows the bias — net move
beyond +/-0.10% of the open (BULLISH needs up, BEARISH down). NEUTRAL = stand-aside (not graded
as a directional hit; tracked as "correctly sat out" iff the session was flat OR the day was a
red-news day we intended to avoid). Secondary: did the DAILY candle close in the bias direction.
"""
import io
from datetime import time as dtime

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
NY = "America/New_York"
START, END = "2025-07-01", "2026-07-15"
THR = 0.0010            # 0.10% of open = flat band
DOW = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}

# ---------------- data ----------------
bars = pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")

# daily candle = ET calendar day (ICT midnight-open daily); NY session = 09:30-16:00
drows, srows = [], []
for day, g in bars.groupby("day"):
    drows.append(dict(day=day, o=float(g.open.iloc[0]), h=float(g.high.max()),
                      l=float(g.low.min()), c=float(g.close.iloc[-1])))
    ses = g[(g.ts.dt.time >= dtime(9, 30)) & (g.ts.dt.time < dtime(16, 0))]
    if len(ses) >= 100:
        i_hi = ses.high.idxmax(); i_lo = ses.low.idxmin()
        srows.append(dict(day=day, so=float(ses.open.iloc[0]), sc=float(ses.close.iloc[-1]),
                          sh=float(ses.high.max()), sl=float(ses.low.min()),
                          t_hi=ses.ts[i_hi].value, t_lo=ses.ts[i_lo].value))
DAY = pd.DataFrame(drows).set_index("day").sort_index()
DAY["dt"] = pd.to_datetime(DAY.index)
DAY["dow"] = DAY.dt.dt.dayofweek
DAY["iso"] = DAY.dt.dt.isocalendar().year * 100 + DAY.dt.dt.isocalendar().week
SES = pd.DataFrame(srows).set_index("day")

# weekly candles (Mon-anchored) from daily
wk = DAY[DAY.dow < 5].groupby("iso").agg(o=("o", "first"), h=("h", "max"), l=("l", "min"),
                                         c=("c", "last"), start=("dt", "first")).sort_index()
wk_list = list(wk.itertuples())          # ordered completed-week reference

# red-folder calendar: day -> has high-impact release in the trading day
fr = []
for f in ["/home/user/gs/config/news_calendar.csv", "/home/user/gs/config/news_calendar_hist.csv"]:
    rows = [l for l in open(f) if not l.startswith("#")]
    fr.append(pd.read_csv(io.StringIO("".join(rows))))
N = pd.concat(fr, ignore_index=True); N = N[N.datetime_ET != "impact"]
N["dt"] = pd.to_datetime(N["datetime_ET"]); N = N[N["impact"].astype(str).str.lower() == "high"]
N["day"] = N["dt"].dt.strftime("%Y-%m-%d")
N = N[(N.dt.dt.time >= dtime(8, 0)) & (N.dt.dt.time <= dtime(16, 0))]
news_day = set(N.day.unique())
news_event = {d: ", ".join(sorted(set(g["dt"].dt.strftime("%H:%M") + " " + g.get("event", "").astype(str))))
              for d, g in N.groupby("day")}

# ---------------- weekly bias (from COMPLETED weeks only) ----------------
def weekly_bias(iso):
    prior = [w for w in wk_list if w.Index < iso]
    if len(prior) < 4:
        return "NEUTRAL"
    c = [w.c for w in prior]; o = [w.o for w in prior]; h = [w.h for w in prior]; l = [w.l for w in prior]
    c1, c2, c3 = c[-1], c[-2], c[-3]
    rng = h[-1] - l[-1]
    upper_half = (c1 - l[-1]) / rng > 0.5 if rng > 0 else False
    ma4 = np.mean(c[-4:])
    bull = (c1 > c2) + (c1 > c3) + (c1 > o[-1] and upper_half) + (c1 > ma4)
    bear = (c1 < c2) + (c1 < c3) + (c1 < o[-1] and not upper_half) + (c1 < ma4)
    if bull >= 3 and bull > bear:
        return "BULLISH"
    if bear >= 3 and bear > bull:
        return "BEARISH"
    return "NEUTRAL"

# ---------------- per-week calendar -> expected low/high day ----------------
def week_days(iso):
    return [d for d in DAY.index if DAY.loc[d, "iso"] == iso and DAY.loc[d, "dow"] < 5]

def expansion_plan(iso, wb):
    """Return dict day-> (bias, conviction, reason) for a week, given weekly bias wb.
    Uses only info knowable at each day's premarket: the week's scheduled news (all known
    Monday) + prior days' completed candles this week."""
    days = week_days(iso)
    if not days or wb == "NEUTRAL":
        return {d: ("NEUTRAL", "NEUTRAL", "weekly bias neutral — stand aside") for d in days}
    dows = {d: DAY.loc[d, "dow"] for d in days}
    hasnews = {d: (d in news_day) for d in days}
    news_dows = sorted(dows[d] for d in days if hasnews[d])
    # expected low/high day-of-week (bullish framing; bearish is mirror in outcome, same day logic)
    early = [dw for dw in news_dows if dw <= 2]      # Mon-Wed news -> low placement
    late = [dw for dw in news_dows if dw >= 2]       # Wed-Fri news -> high placement
    low_dow = early[0] if early else 0               # default Monday
    high_dow = late[-1] if late else 4               # default Friday
    if high_dow <= low_dow:
        high_dow = 4

    out = {}
    for d in days:
        dw = dows[d]
        # is the weekly extreme (low for bullish) already in, from prior days THIS week?
        prior_days = [x for x in days if dows[x] < dw]
        low_in = high_in = False
        if prior_days:
            wl = min(DAY.loc[x, "l"] for x in prior_days); wh = max(DAY.loc[x, "h"] for x in prior_days)
            last = max(prior_days, key=lambda x: dows[x])
            lc = DAY.loc[last]
            near_high = (lc.c - lc.l) / (lc.h - lc.l) > 0.6 if lc.h > lc.l else False
            near_low = (lc.c - lc.l) / (lc.h - lc.l) < 0.4 if lc.h > lc.l else False
            # prior week extreme for sweep detection
            pw = [w for w in wk_list if w.Index < iso]
            if pw:
                if wl < pw[-1].l and near_high:     # swept prior-week low then closed strong -> low in
                    low_in = True
                if wh > pw[-1].h and near_low:
                    high_in = True
            if dw > low_dow:
                low_in = True
            if dw > high_dow:
                high_in = True

        if wb == "BULLISH":
            if dw < low_dow and not low_in:
                out[d] = ("NEUTRAL", "NEUTRAL", f"pre-low accumulation (low expected {inv(low_dow)})")
            elif dw == low_dow and not low_in:
                out[d] = ("BULLISH", "MEDIUM", "low-of-week / turtle-soup day — reversal long expected")
            elif low_in and dw <= high_dow:
                conv = "HIGH" if 1 <= dw <= 3 else "MEDIUM"
                out[d] = ("BULLISH", conv, f"expansion day, low in, high expected {inv(high_dow)}")
            elif dw > high_dow or high_in:
                out[d] = ("NEUTRAL", "NEUTRAL", "post-high distribution — stand aside")
            else:
                out[d] = ("BULLISH", "MEDIUM", "with-week expansion")
        else:  # BEARISH mirror (high early, low late)
            hi_dow, lo_dow = low_dow, high_dow      # bearish: high placed early, low late
            if dw < hi_dow and not high_in:
                out[d] = ("NEUTRAL", "NEUTRAL", f"pre-high accumulation (high expected {inv(hi_dow)})")
            elif dw == hi_dow and not high_in:
                out[d] = ("BEARISH", "MEDIUM", "high-of-week / turtle-soup day — reversal short expected")
            elif high_in and dw <= lo_dow:
                conv = "HIGH" if 1 <= dw <= 3 else "MEDIUM"
                out[d] = ("BEARISH", conv, f"expansion day, high in, low expected {inv(lo_dow)}")
            elif dw > lo_dow or low_in:
                out[d] = ("NEUTRAL", "NEUTRAL", "post-low distribution — stand aside")
            else:
                out[d] = ("BEARISH", "MEDIUM", "with-week expansion")
    return out

def inv(dw):
    return {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri"}[dw]

# ---------------- grade ----------------
def grade(bias, net, thr):
    if bias == "BULLISH":
        return "CORRECT" if net > thr else ("WRONG" if net < -thr else "FLAT")
    if bias == "BEARISH":
        return "CORRECT" if net < -thr else ("WRONG" if net > thr else "FLAT")
    return "STOOD ASIDE"

rows = []
isos = sorted(DAY[(DAY.index >= START) & (DAY.index <= END)].iso.unique())
plans = {}
for iso in isos:
    wb = weekly_bias(iso)
    plans[iso] = (wb, expansion_plan(iso, wb))

for day in sorted(DAY.index):
    if day < START or day > END or DAY.loc[day, "dow"] >= 5 or day not in SES.index:
        continue
    iso = DAY.loc[day, "iso"]
    wb, plan = plans.get(iso, ("NEUTRAL", {}))
    bias, conv, reason = plan.get(day, ("NEUTRAL", "NEUTRAL", "no plan"))
    s = SES.loc[day]; d = DAY.loc[day]
    thr = THR * s.so
    net = s.sc - s.so
    dc = d.c - d.o           # daily candle direction
    v = grade(bias, net, thr)
    daily_ok = (dc > 0) if bias == "BULLISH" else (dc < 0) if bias == "BEARISH" else (abs(net) <= thr)
    dirword = "up" if net > thr else ("down" if net < -thr else "flat")
    # ICT expansion (PO3/judas): did NY sweep against, THEN expand with the bias?
    # bullish -> session LOW printed before session HIGH and the high cleared the open by >= thr.
    if bias == "BULLISH":
        expansion_ok = (s.t_lo < s.t_hi) and (s.sh - s.so >= thr)
    elif bias == "BEARISH":
        expansion_ok = (s.t_hi < s.t_lo) and (s.so - s.sl >= thr)
    else:
        expansion_ok = abs(net) <= thr

    bits = [f"{inv(d.dow)} · weekly {wb.lower()} · NY {net:+.0f}pt ({dirword})"]
    if bias == "NEUTRAL":
        bits.append(reason)
        if day in news_day:
            bits.append("red-folder day")
    elif v == "CORRECT":
        bits.append(f"session expanded {bias.lower()[:4]} with the week — {reason}")
    elif v == "FLAT":
        bits.append(f"right direction bias but session chopped flat — {reason}")
    else:
        bits.append(f"session ran {dirword} AGAINST the {bias.lower()} read — {reason}")
    if day in news_event:
        bits.append("news: " + news_event[day][:60])

    rows.append(dict(day=day, weekday=inv(d.dow), weekly=wb, bias=bias, conviction=conv,
                     net=round(net, 1), net_pct=round(100 * net / s.so, 2),
                     daily_dir=("up" if dc > 0 else "down"), verdict=v,
                     daily_ok=bool(daily_ok), expansion_ok=bool(expansion_ok),
                     newsday=(day in news_day), reason=reason, note="; ".join(bits)))

J = pd.DataFrame(rows)
J.to_csv(f"{S}/ict_bias_days.csv", index=False)

# ---------------- summary ----------------
D = J[J.bias != "NEUTRAL"]
def acc(x):
    return round(100 * (x.verdict == "CORRECT").mean(), 1) if len(x) else 0.0
print(f"days: {len(J)}  |  directional (traded) days: {len(D)}  |  NEUTRAL/stand-aside: {len(J)-len(D)}")
print(f"weekly-bias weeks: {J.groupby('weekly').day.nunique() if False else J.weekly.value_counts().to_dict()}")
print(f"\nSTRICT net-close accuracy (NY closes in bias dir): {acc(D)}%  (n={len(D)})")
print(f"  of directional: correct {(D.verdict=='CORRECT').sum()}, wrong {(D.verdict=='WRONG').sum()}, flat {(D.verdict=='FLAT').sum()}")
print(f"ICT EXPANSION accuracy (sweep-then-expand, the tradeable measure): {round(100*D.expansion_ok.mean(),1)}%")
print(f"daily-candle agreement (secondary): {round(100*D.daily_ok.mean(),1)}%")
print(f"  HIGH-conviction expansion: {round(100*D[D.conviction=='HIGH'].expansion_ok.mean(),1)}%")
print("\nby bias:")
for b in ["BULLISH", "BEARISH"]:
    x = D[D.bias == b]
    if len(x):
        print(f"  {b:8s} {len(x):3d}d  correct {acc(x)}%  wrong {(x.verdict=='WRONG').mean()*100:.0f}%")
print("\nby conviction:")
for c in ["HIGH", "MEDIUM"]:
    x = D[D.conviction == c]
    if len(x):
        print(f"  {c:7s} {len(x):3d}d  correct {acc(x)}%")
print("\nby weekday (validate the Tue-Wed-Thu thesis):")
for wd in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
    x = D[D.weekday == wd]
    if len(x):
        print(f"  {wd} {len(x):3d}d  correct {acc(x)}%")
print("\nNEWS-DAY vs quiet-day (directional):")
print(f"  news days   {len(D[D.newsday]):3d}d  correct {acc(D[D.newsday])}%")
print(f"  quiet days  {len(D[~D.newsday]):3d}d  correct {acc(D[~D.newsday])}%")
print("\nmonthly directional accuracy:")
J["mo"] = J.day.str.slice(0, 7); D2 = J[J.bias != "NEUTRAL"]
for mo, g in D2.groupby("mo"):
    print(f"  {mo}  {len(g):2d}d  {acc(g):5.1f}%")
print("saved ict_bias_days.csv")
