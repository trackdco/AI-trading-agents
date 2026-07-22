#!/usr/bin/env python3
"""NQ Daily Bias via Session Daily Profiles (previous-session / London method).
Jul 2025 -> Jul 2026. No trading; grade the read vs the NY session.

Method: at 08:00 ET (London complete), read what London (03:00-08:00) did around the HTF
liquidity draws that existed before it, and map to ONE profile:
  A  London CONSOLIDATION (swept no HTF draw)          -> NY manipulation + reversal
  B  London MANIPULATION only (swept, not reversed)    -> NY reversal, away from swept side
  C  London MANIPULATION + REVERSAL (swept + displaced)-> NY continuation of the reversal
Direction rule: low-sweep + reversal -> BULLISH (target highs); high-sweep + reversal ->
BEARISH (target lows). Profile A (no sweep): the side we sit nearest / premium-discount picks
the expected manipulation, bias = the reversal away from it. News-gate + ambiguity -> NEUTRAL.

HTF draws (as of 08:00): PDH/PDL (prior day), Asia H/L (20:00-00:00), London H/L (03:00-08:00),
recent 1H swing highs/lows. Sweep = wick beyond a draw. Reversal = closed back through it with
displacement. No lookahead: classification uses only candles <= 08:00; graded on 09:30-16:00.
"""
import io
from datetime import time as dtime

import numpy as np
import pandas as pd

S = "/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad"
NY = "America/New_York"
START, END = "2025-07-01", "2026-07-15"
THR = 0.0010
NEWS_STAND_ASIDE = True     # default per spec; also reported both ways

bars = pd.read_parquet("/home/user/gs/data/reference/nq_1m_master.parquet")
bars["ts"] = pd.to_datetime(bars["ts_event"], utc=True).dt.tz_convert(NY)
bars["day"] = bars["ts"].dt.strftime("%Y-%m-%d")
bars["t"] = bars["ts"].dt.time
by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day")}
daylist = sorted(by_day)

# 1H swings for extra HTF draws
h1 = (bars.set_index("ts").resample("1h", closed="left", label="left")
      .agg(o=("open", "first"), h=("high", "max"), l=("low", "min"), c=("close", "last")).dropna().reset_index())
h1["day"] = h1["ts"].dt.strftime("%Y-%m-%d")

def swings_1h_asof(day):
    """Recent unswept 1H swing highs/lows before 08:00 on `day`."""
    cut = pd.Timestamp(f"{day} 08:00", tz=NY)
    fr = h1[h1["ts"] < cut].tail(48)
    if len(fr) < 5:
        return [], []
    H = fr.h.to_numpy(); L = fr.l.to_numpy(); n = len(fr)
    sh = [float(H[i]) for i in range(1, n - 1) if H[i] > H[i - 1] and H[i] > H[i + 1]]
    sl = [float(L[i]) for i in range(1, n - 1) if L[i] < L[i - 1] and L[i] < L[i + 1]]
    return sh[-4:], sl[-4:]

# red-folder calendar
fr = []
for f in ["/home/user/gs/config/news_calendar.csv", "/home/user/gs/config/news_calendar_hist.csv"]:
    fr.append(pd.read_csv(io.StringIO("".join(l for l in open(f) if not l.startswith("#")))))
Ncal = pd.concat(fr, ignore_index=True); Ncal = Ncal[Ncal.datetime_ET != "impact"]
Ncal["dt"] = pd.to_datetime(Ncal["datetime_ET"]); Ncal = Ncal[Ncal["impact"].astype(str).str.lower() == "high"]
Ncal["day"] = Ncal["dt"].dt.strftime("%Y-%m-%d")
Ncal = Ncal[(Ncal.dt.dt.time >= dtime(8, 0)) & (Ncal.dt.dt.time <= dtime(11, 0))]  # in/near the open window
news_day = set(Ncal.day.unique())
news_event = {d: ", ".join(sorted(set(g["dt"].dt.strftime("%H:%M") + " " + g.get("event", "").astype(str))))
              for d, g in Ncal.groupby("day")}

def win(g, t0, t1):
    w = g[(g.t >= t0) & (g.t < t1)]
    return w

def classify(day):
    """Return a dict describing the London session profile + bias, as of 08:00 (no lookahead)."""
    g = by_day[day]
    prevdays = [d for d in daylist if d < day]
    if not prevdays:
        return None
    pg = by_day[prevdays[-1]]
    pdh, pdl = float(pg.high.max()), float(pg.low.min())
    asia = win(pg, dtime(20, 0), dtime(23, 59))
    asia_h = float(asia.high.max()) if len(asia) else np.nan
    asia_l = float(asia.low.min()) if len(asia) else np.nan
    lon = win(g, dtime(3, 0), dtime(8, 0))
    if len(lon) < 30 or np.isnan(asia_h):
        return None
    lon_h, lon_l = float(lon.high.max()), float(lon.low.min())
    lon_open = float(lon.open.iloc[0]); lon_close = float(lon.close.iloc[-1])
    price08 = lon_close
    sh1, sl1 = swings_1h_asof(day)

    # HTF draws that existed into London (levels London could sweep)
    resist = [x for x in [pdh, asia_h] + list(sh1) if not np.isnan(x) and x > lon_open]
    support = [x for x in [pdl, asia_l] + list(sl1) if not np.isnan(x) and x < lon_open]
    swept_high = any(lon_h > r for r in resist)
    swept_low = any(lon_l < s for s in support)
    # which specific level was taken (nearest to lon_open on the swept side)
    hi_lvl = min((r for r in resist if lon_h > r), key=lambda r: abs(r - lon_open)) if swept_high else None
    lo_lvl = max((s for s in support if lon_l < s), key=lambda s: abs(s - lon_open)) if swept_low else None
    # reversal = London closed back on the correct side of the swept level, with displacement
    rev_up = swept_low and (lon_close > lo_lvl) and ((lon_close - lon_l) / (lon_h - lon_l + 1e-9) > 0.55)
    rev_dn = swept_high and (lon_close < hi_lvl) and ((lon_h - lon_close) / (lon_h - lon_l + 1e-9) > 0.55)

    # ---- profile + bias ----
    prof = bias = conv = "NEUTRAL"; swept = "none"; rev = "no"; reason = ""
    if not swept_high and not swept_low:
        prof = "A"; swept = "none (consolidation)"
        # nearest unswept draw to the 08:00 price picks the manipulation side; reverse away.
        ups = [x for x in [pdh, asia_h] + list(sh1) if not np.isnan(x) and x > price08]
        dns = [x for x in [pdl, asia_l] + list(sl1) if not np.isnan(x) and x < price08]
        d_up = min((x - price08 for x in ups), default=1e9)
        d_dn = min((price08 - x for x in dns), default=1e9)
        # premium/discount of the Asia+PD reference range as tie context
        lo_r = min([v for v in [pdl, asia_l] if not np.isnan(v)] + [lon_l])
        hi_r = max([v for v in [pdh, asia_h] if not np.isnan(v)] + [lon_h])
        pos = (price08 - lo_r) / (hi_r - lo_r) if hi_r > lo_r else 0.5
        if d_up < d_dn * 0.8 or pos > 0.62:      # nearest liquidity above / in premium -> sweep high, reverse down
            bias = "BEARISH"; conv = "MEDIUM"; reason = "consol->expect NY sweep of the buyside then reverse down"
        elif d_dn < d_up * 0.8 or pos < 0.38:    # nearest below / discount -> sweep low, reverse up
            bias = "BULLISH"; conv = "MEDIUM"; reason = "consol->expect NY sweep of the sellside then reverse up"
        else:
            bias = "NEUTRAL"; reason = "consol but price mid-range — no clean manipulation side (stand aside)"
    elif swept_low and rev_up and not (swept_high and rev_dn):
        prof = "C"; swept = f"sellside {lo_lvl:.0f}"; rev = "yes (closed back above, displaced up)"
        bias = "BULLISH"; conv = "HIGH"; reason = "London swept lows + reversed up -> NY continuation up (wait LTF sweep)"
    elif swept_high and rev_dn and not (swept_low and rev_up):
        prof = "C"; swept = f"buyside {hi_lvl:.0f}"; rev = "yes (closed back below, displaced down)"
        bias = "BEARISH"; conv = "HIGH"; reason = "London swept highs + reversed down -> NY continuation down (wait LTF sweep)"
    elif swept_low and not rev_up and not swept_high:
        prof = "B"; swept = f"sellside {lo_lvl:.0f}"; rev = "no (still below / no displacement)"
        bias = "BULLISH"; conv = "MEDIUM"; reason = "London swept lows, no reversal yet -> NY delivers reversal up"
    elif swept_high and not rev_dn and not swept_low:
        prof = "B"; swept = f"buyside {hi_lvl:.0f}"; rev = "no"
        bias = "BEARISH"; conv = "MEDIUM"; reason = "London swept highs, no reversal yet -> NY delivers reversal down"
    else:
        # swept both sides -> use London close position to resolve; else neutral
        prof = "B/ambiguous"; swept = "both sides"
        if cpos_close(lon_close, lon_l, lon_h) > 0.6:
            bias = "BULLISH"; conv = "MEDIUM"; prof = "B"; rev = "closed strong"; reason = "swept both, closed strong -> up"
        elif cpos_close(lon_close, lon_l, lon_h) < 0.4:
            bias = "BEARISH"; conv = "MEDIUM"; prof = "B"; rev = "closed weak"; reason = "swept both, closed weak -> down"
        else:
            bias = "NEUTRAL"; reason = "London swept both sides, closed mid — ambiguous (stand aside)"

    return dict(profile=prof, bias=bias, conv=conv, swept=swept, rev=rev, reason=reason,
                pdh=pdh, pdl=pdl, asia_h=asia_h, asia_l=asia_l, lon_h=lon_h, lon_l=lon_l, price08=price08)


def cpos_close(c, l, h):
    return (c - l) / (h - l) if h > l else 0.5



# ---------------- NY session outcomes ----------------
def ny_session(day):
    g = by_day[day]
    ses = g[(g.t >= dtime(9, 30)) & (g.t < dtime(16, 0))]
    if len(ses) < 100:
        return None
    return dict(so=float(ses.open.iloc[0]), sc=float(ses.close.iloc[-1]),
                sh=float(ses.high.max()), sl=float(ses.low.min()),
                t_hi=ses.ts[ses.high.idxmax()].value, t_lo=ses.ts[ses.low.idxmin()].value)


def grade(bias, net, thr):
    if bias == "BULLISH":
        return "CORRECT" if net > thr else ("WRONG" if net < -thr else "FLAT")
    if bias == "BEARISH":
        return "CORRECT" if net < -thr else ("WRONG" if net > thr else "FLAT")
    return "STOOD ASIDE"


# ICT-weekly read for the cross-check (optional)
try:
    ICT = pd.read_csv(f"{S}/ict_bias_v2_days.csv", dtype={"day": str}).set_index("day")["bias"].to_dict()
except Exception:
    ICT = {}

rows = []
for day in daylist:
    if day < START or day > END:
        continue
    c = classify(day)
    ny = ny_session(day)
    if c is None or ny is None:
        continue
    thr = THR * ny["so"]; net = ny["sc"] - ny["so"]
    bias = c["bias"]
    newsd = day in news_day
    graded_bias = "NEUTRAL" if (newsd and NEWS_STAND_ASIDE) else bias
    v = grade(graded_bias, net, thr)
    if graded_bias == "BULLISH":
        exp_ok = (ny["t_lo"] < ny["t_hi"]) and (ny["sh"] - ny["so"] >= thr)
    elif graded_bias == "BEARISH":
        exp_ok = (ny["t_hi"] < ny["t_lo"]) and (ny["so"] - ny["sl"] >= thr)
    else:
        exp_ok = abs(net) <= thr
    dirword = "up" if net > thr else ("down" if net < -thr else "flat")
    ict = ICT.get(day, "n/a")
    agree = (ict == bias) and bias in ("BULLISH", "BEARISH")
    note = f"{c['profile']} · London swept {c['swept']}, rev {c['rev']} · NY {net:+.0f}pt ({dirword}) · {c['reason']}"
    if newsd and NEWS_STAND_ASIDE and bias != "NEUTRAL":
        note += f" · NEWS -> stood aside ({news_event.get(day,'')[:40]})"
    rows.append(dict(day=day, weekday=pd.Timestamp(day).day_name()[:3], profile=c["profile"],
                     raw_bias=bias, bias=graded_bias, conviction=c["conv"], net=round(net, 1),
                     verdict=v, expansion_ok=bool(exp_ok), newsday=newsd,
                     ict_weekly=ict, agree=bool(agree), reason=c["reason"], note=note))

J = pd.DataFrame(rows)
J.to_csv(f"{S}/session_profile_days.csv", index=False)

D = J[J.bias != "NEUTRAL"]
acc = lambda x: round(100 * (x.verdict == "CORRECT").mean(), 1) if len(x) else 0.0
expf = lambda x: round(100 * x.expansion_ok.mean(), 1) if len(x) else 0.0
print("=== SESSION-PROFILE BIAS (London method) ===")
print(f"days {len(J)} | directional {len(D)} | stood aside {len(J)-len(D)}  (news-gated: {J[(J.newsday)&(J.raw_bias!='NEUTRAL')].shape[0]})")
print(f"profile mix (raw, incl news): {J.profile.value_counts().to_dict()}")
print(f"\nDIRECTIONAL: strict {acc(D)}%  expansion {expf(D)}%")
print("by profile:")
for p in ["A", "B", "C"]:
    x = D[D.profile == p]
    if len(x):
        print(f"  {p} {len(x):3d}d  strict {acc(x)}%  expansion {expf(x)}%")
print("by conviction:")
for cv in ["HIGH", "MEDIUM"]:
    x = D[D.conviction == cv]
    if len(x):
        print(f"  {cv:6s} {len(x):3d}d  strict {acc(x)}%  expansion {expf(x)}%")
print("by bias:", {b: (len(D[D.bias == b]), acc(D[D.bias == b])) for b in ["BULLISH", "BEARISH"]})
# cross-check with ICT-weekly
both = J[(J.bias != "NEUTRAL") & (J.ict_weekly.isin(["BULLISH", "BEARISH"]))]
agr = both[both.agree]
print(f"\nCROSS-CHECK vs ICT-weekly: both directional {len(both)}d")
print(f"  AGREE {len(agr)}d  strict {acc(agr)}%  expansion {expf(agr)}%")
print(f"  disagree {len(both)-len(agr)}d  strict {acc(both[~both.agree])}%")
print("\nmonthly (directional):")
J["mo"] = J.day.str.slice(0, 7)
for mo, gg in J[J.bias != "NEUTRAL"].groupby("mo"):
    print(f"  {mo}  {len(gg):2d}d  {acc(gg):5.1f}%")
print("saved session_profile_days.csv")
