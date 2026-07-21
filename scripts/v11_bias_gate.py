#!/usr/bin/env python3
"""Champion v1.1 gated by the NEW HTF bias engine (htf_bias.py v2), Feb-Jul 2026.

For each trading day: build the intraday bias timeline (INITIAL 08:00 -> event updates ->
mandatory 09:30 checkpoint -> later updates). Each v1.1 trade is judged by the bias IN FORCE
at its fill minute (the latest read at/before fill — no hindsight).

Gates reported (against the exact frozen v1.1 base = journal + 3 cuts, 100t/+$17,814):
  A HARD: long only if BULLISH, short only if BEARISH; NOTHING while NEUTRAL.
  B SOFT: block only trades OPPOSING a directional bias; NEUTRAL passes everything.
  (+ conviction splits for information.)

HONESTY: this FILTERS the frozen v1.1 trades; it does not re-run the engine, so a blocked
trade does not free its 2/day slot for a later setup. Bias timelines use bars sliced to a
60-day lookback before each day (all indicator lookbacks fit well inside; verified same
reads as full history on spot-checks).
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, "/home/user/AI-trading-agents")
import htf_bias as HB  # noqa: E402

NY = "America/New_York"
OUT = Path("/tmp/claude-0/-home-user-AI-trading-agents/69c9097f-44f3-585b-817f-a315126d0dbb/scratchpad")

# ---- the exact frozen v1.1 trade set (journal + 3 cuts; verified +$17,814) ----
J = pd.read_csv("/home/user/gs/output/journal_champion.csv")
fh = J.fill.str.slice(0, 2).astype(int)
V11 = J[(J.risk_pts >= 5.0) & ~((J.pattern == "B") & (fh == 9))
        & ~((J.branch == "E3bal") & (J.htf == "with_trend"))].copy()
print(f"v1.1 base: {len(V11)}t  ${V11.dollars.sum():+,.0f}  win {V11.win.mean()*100:.1f}%")

bars = HB.load_bars()
news = HB.load_news()
days = sorted(V11.day.unique())
print(f"building bias timelines for {len(days)} trade days ...", flush=True)

timelines = {}
for i, dstr in enumerate(days):
    D = pd.Timestamp(dstr, tz=NY)
    sl = bars[(bars.ts >= D - pd.Timedelta(days=60)) & (bars.ts < D + pd.Timedelta(days=1))].reset_index(drop=True)
    _, digest = None, None
    # replicate monitor_day but capture (time, bias, tier, score) transitions
    T0 = pd.Timestamp.combine(D.date(), dtime(8, 0)).tz_localize(NY)
    blk, st = HB.read_at(sl, news, D, T0, "INITIAL premarket")
    if st is None:
        timelines[dstr] = [("08:00", "NEUTRAL", "NEUTRAL", 0)]
        continue
    tl = [("08:00", st["bias"], st["tier"], st["score"])]
    fired = set()
    t = T0 + pd.Timedelta(minutes=15)
    end = pd.Timestamp.combine(D.date(), HB.WIN_END).tz_localize(NY)
    while t <= end:
        candle = sl[(sl.ts >= t - pd.Timedelta(minutes=15)) & (sl.ts < t)]
        if t.time() == dtime(9, 30):
            _, ns = HB.read_at(sl, news, D, t, "UPDATE @ 09:30 ET — mandatory open checkpoint",
                               prev_bias=st["bias"], trigger="0930")
            st = ns; fired = set()
            tl.append(("09:30", st["bias"], st["tier"], st["score"]))
        elif len(candle):
            hi = float(candle.high.max()); lo = float(candle.low.min()); cl = float(candle.close.iloc[-1])
            reasons = []
            d = st["direction"]
            if d in ("bullish", "bearish"):
                ip = st["inval_px"]
                if ip is not None and "inval" not in fired and ((d == "bullish" and cl < ip) or (d == "bearish" and cl > ip)):
                    reasons.append("inval"); fired.add("inval")
                dp = st["draw_px"]
                if dp is not None and "draw" not in fired and ((d == "bullish" and hi >= dp) or (d == "bearish" and lo <= dp)):
                    reasons.append("draw"); fired.add("draw")
                if "cisd" not in fired:
                    f15 = HB.frames_asof(sl, t, D)["15m"]
                    against = "bearish" if d == "bullish" else "bullish"
                    if HB.cisd_last(f15.tail(30), against):
                        reasons.append("cisd"); fired.add("cisd")
            else:
                if "flip" not in fired:
                    if st["pdh"] is not None and cl > st["pdh"]:
                        reasons.append("flip"); fired.add("flip")
                    elif st["pdl"] is not None and cl < st["pdl"]:
                        reasons.append("flip"); fired.add("flip")
            if reasons:
                _, ns = HB.read_at(sl, news, D, t, f"UPDATE @ {t.strftime('%H:%M')} ET", prev_bias=st["bias"],
                                   trigger=";".join(reasons))
                st = ns
                tl.append((t.strftime("%H:%M"), st["bias"], st["tier"], st["score"]))
        t += pd.Timedelta(minutes=15)
    timelines[dstr] = tl
    if (i + 1) % 20 == 0:
        print(f"  {i+1}/{len(days)} days", flush=True)

# save timelines
rows = [dict(day=d, time=e[0], bias=e[1], tier=e[2], score=e[3]) for d, tle in timelines.items() for e in tle]
pd.DataFrame(rows).to_csv(OUT / "bias_timelines.csv", index=False)

def bias_at(dstr, fill):
    tl = timelines.get(dstr, [("08:00", "NEUTRAL", "NEUTRAL", 0)])
    cur = tl[0]
    for e in tl:
        if e[0] <= fill:
            cur = e
        else:
            break
    return cur  # (time, bias, tier, score)

V11["bias"] = [bias_at(r.day, r.fill)[1] for r in V11.itertuples()]
V11["bias_tier"] = [bias_at(r.day, r.fill)[2] for r in V11.itertuples()]
V11["aligned"] = ((V11.bias == "BULLISH") & (V11.dir == "long")) | ((V11.bias == "BEARISH") & (V11.dir == "short"))
V11["opposed"] = ((V11.bias == "BULLISH") & (V11.dir == "short")) | ((V11.bias == "BEARISH") & (V11.dir == "long"))


def rep(x, label):
    if not len(x):
        print(f"  {label:42s} 0t"); return
    m = x.groupby("month").dollars.sum()
    print(f"  {label:42s} {len(x):3d}t  win {x.win.mean()*100:4.1f}%  ${x.dollars.sum():+8,.0f}  "
          f"green {int((m>0).sum())}/{m.size}")

print("\n=== CHAMPION v1.1 x NEW HTF BIAS ENGINE (bias in force at each fill) ===")
rep(V11, "v1.1 base (no bias gate)")
rep(V11[~V11.opposed], "GATE B soft: drop bias-OPPOSED trades")
rep(V11[V11.aligned], "GATE A hard: aligned only (no NEUTRAL)")
print()
print("  what the bias said at fill:")
for b in ["BULLISH", "BEARISH", "NEUTRAL"]:
    sub = V11[V11.bias == b]
    rep(sub, f"    bias={b}")
print()
print("  informational splits:")
rep(V11[V11.opposed], "    OPPOSED trades (what B drops)")
rep(V11[V11.aligned & V11.bias_tier.isin(["HIGH", "MEDIUM"])], "    aligned + HIGH/MEDIUM conviction")
rep(V11[V11.aligned & (V11.dir == "long")], "    aligned longs")
rep(V11[V11.aligned & (V11.dir == "short")], "    aligned shorts")
print("\n  monthly, GATE B:")
gb = V11[~V11.opposed].groupby("month").dollars.sum().round(0)
print(gb.to_string())
V11.to_csv(OUT / "v11_bias_gated.csv", index=False)
print("\nsaved v11_bias_gated.csv, bias_timelines.csv")
