#!/usr/bin/env python3
"""RAW BASELINES — zxck-ifvg-50 and zxck-cisd, on ONE shared harness.

Both cards run through the same window, the same locked exit and the same feature code, so no
convention can drift between them. Gate counts are printed BEFORE any outcome is summarised.

Exit: research/zxcked/strategies/EXIT-CONVENTION-LOCKED.md — identical to ash-unicorn-sb.
Window/span: zxck-COMPONENTS.md F000 — 09:45-10:15 ET, 2025-06-01 -> 2026-07-15 [stated-by-user].

=================================== zxck-ifvg-50 ==========================================
[S]=stated  [I]=inferred  [U]=stated-by-user  [A]=our assumption  [LOCK]=locked exit

I1 GAP [S]      a 5-minute or 15-minute fair value gap.
                "15 minute or five minute inverse fair value gap" [lRgsHGWzO9E 07:44]
I2 INVERSION [S] price must CLOSE beyond the gap, not merely wick through it.
                "You see we closed below the fair value gap on the 545 candle" [BOuJLWIisMI 04:39]
                Consistent with every other state change he defines by a close. (Q13 resolved.)
I3 BIAS [U]     the inverted gap must align with the draw on liquidity.
                Brake: "the standalone version REQUIRES a directional bias / level... the 'you
                could literally make a model out of this alone' line is treated as him
                overselling the concept, not a literal every-gap rule."
                ⚠️ THIS GATE CAME FROM BRAKE, NOT FROM POWELL. Draw is taken from the PXH/PXL
                daily state machine (COMPONENTS A1), which IS his and IS fully stated.
I4 ENTRY [S]    limit at the 50% of the inverted gap, on the first return after I2.
I5 STOP [S]     5.0 points. "with a five-point stop" [lRgsHGWzO9E 07:44]
                => cost is 0.250R/trade at $25/round-turn. Enormous, and stated up front.
I6 TARGET [LOCK] 2R = 10 points.  I7 BE [LOCK] at 1R.  I8 no trailing.  I9 stop-first same bar.
I10 one trade per day [I].  I11 avoid FOMC / Fed-Chair-Powell [S].

==================================== zxck-cisd ============================================
C1 CISD [S]     a candle closes beyond the OPENING PRICE of the IMMEDIATELY ADJACENT opposing
                candle. "we want then the next candle after this one to close above the opening
                price of this down close candle" [0u1L00q77bw 02:16] (Q18 resolved: adjacent).
C2 TIMEFRAME [A] 1-HOUR. He names "daily CISD and then 4 hour and one hour CISDs are the most
                powerful and the most consistent" [rzfgAEYhxCg 00:47], and his worked example is
                the 09:00 ET candle into the open [55KRVFLqzwA 03:05]. Daily and 4H produce far
                too few levels inside a 30-minute window. OURS BY SELECTION among his three.
C3 ENTRY [S]    two ticks beyond the opening price, on the return to it.
                "we can put our entry two ticks above the opening price" [0u1L00q77bw 06:15]
C4 STOP [I]     beyond the CISD candle's own extreme. His only statement is a hedged
                recollection ("either a five or a three, I don't remember" [@ 06:38]); the
                corpus-wide rule is that the stop follows the PD array's size (COMPONENTS D1).
                Structural reading taken. Floor 5pt per [BOuJLWIisMI 03:28].
C5 INVALIDATION [S] lower probability if the target level is tapped BEFORE the entry fills
                [0u1L00q77bw 04:39]. Implemented as a hard skip.
C6-C10 exit, BE, trailing, same-bar, cap, one-per-day, FOMC: identical to zxck-ifvg-50.

--------------------------------- NOT IMPLEMENTED (both) ---------------------------------
N1 the FVG-inversion pairing on CISD — a BONUS, not a gate [0u1L00q77bw 10:11].
N2 SMT — needs ES; not held, purchase declined.
N3 the 15-second CISD scalp — needs sub-minute bars.
N4 order flow — COMPUTED for pooling, never applied.
==========================================================================================

    python -m scripts.zxck_remaining_baselines
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.f2_oos_test import flow_frame  # noqa: E402
from scripts.nya_sb01_feasibility import load_bars  # noqa: E402
from scripts.zxck_keyopen_baseline import FOMC, calendar  # noqa: E402

M0, M1 = 9 * 60 + 45, 10 * 60 + 15
LO, HI = "2025-06-01", "2026-07-15"
RTH_END = 16 * 60
COST_USD, PT, TICK = 25.0, 20.0, 0.25
IFVG_STOP = 5.0
OUT = ROOT / "research/zxcked/strategies"


# ----------------------------------------------------------------- his PXH/PXL draw (A1)
def daily_draw(bars: pd.DataFrame) -> dict:
    """COMPONENTS A1, stated and restated 10 months apart [jBS22-pX3dU 00:23; f0mYnZ9ISJY 01:36].
    Returns {day: +1 if the HIGH is the draw, -1 if the LOW is}. Uses only PRIOR days."""
    d = bars.set_index("ts").resample("1D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    draw, out = 0, {}
    days = d.index.strftime("%Y-%m-%d").tolist()
    for i in range(1, len(d)):
        prev, cur = d.iloc[i - 1], d.iloc[i]
        if cur.close > prev.high:
            draw = +1                      # closed above the prior high -> next high gets taken
        elif cur.close < prev.low:
            draw = -1                      # closed below the prior low  -> next low gets taken
        elif cur.high > prev.high and cur.close < prev.high:
            draw = -1                      # took the high, closed back within -> the low
        elif cur.low < prev.low and cur.close > prev.low:
            draw = +1                      # took the low, closed back within -> the high
        elif draw == 0:
            draw = +1 if cur.close > cur.open else -1        # bullish candle -> the high
        if i + 1 < len(days):
            out[days[i + 1]] = draw        # applies to the NEXT session only
    return out


def resample(g: pd.DataFrame, rule: str) -> pd.DataFrame:
    return g.set_index("ts").resample(rule, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()


def walk_exit(g, w, t, entry, stop, side, risk):
    """LOCKED convention. Includes the same-bar fill-and-stop check found on zxck-wick-ce."""
    target, half = entry + side * 2 * risk, entry + side * risk
    fb = w.iloc[t]
    if (fb.low <= stop) if side > 0 else (fb.high >= stop):
        return -1.0, stop, False
    tail = pd.concat([w.iloc[t + 1:], g[(g.mins > M1) & (g.mins <= RTH_END)]])
    cur, be = stop, False
    for _, b in tail.iterrows():
        if side > 0:
            if b.low <= cur:
                return (0.0 if be else -1.0), cur, be
            if b.high >= target:
                return 2.0, target, be
            if not be and b.high >= half:
                cur, be = entry, True
        else:
            if b.high >= cur:
                return (0.0 if be else -1.0), cur, be
            if b.low <= target:
                return 2.0, target, be
            if not be and b.low <= half:
                cur, be = entry, True
    last = float(tail.close.iloc[-1]) if len(tail) else entry
    return float(side * (last - entry) / risk), last, be


def features(g, w, t, side, entry, risk, day, atr, news, fp, t0):
    pre = g[g.mins < M0]
    h1 = float(pre.close.iloc[-1] - pre.close.iloc[-120]) if len(pre) > 120 else np.nan
    phi = float(pre.high.max()) if len(pre) else np.nan
    plo = float(pre.low.min()) if len(pre) else np.nan
    te = w.ts.iloc[t]
    disp = fp[(fp.index >= t0) & (fp.index <= t0)]
    ret = fp[(fp.index > t0) & (fp.index <= te)]
    sess = fp[(fp.index >= w.ts.iloc[0]) & (fp.index <= te)].vol
    med = float(sess.median()) if len(sess) else np.nan
    f1 = float(disp.delta.sum()) * side / med if (len(disp) and med) else np.nan
    dv, rv = float(disp.vol.sum()), float(ret.vol.sum())
    return {"dow": pd.Timestamp(day).day_name()[:3],
            "entry_min_into_window": int(w.mins.iloc[t] - M0),
            "atr_pct": float(atr.get(day, np.nan)),
            "htf_aligned": int((h1 > 0) == (side > 0)) if h1 == h1 else np.nan,
            "dist_to_level_R": (round(min(abs(entry - phi), abs(entry - plo)) / risk, 3)
                                if phi == phi else np.nan),
            "news_day": int(day in news), "risk_pts_v": round(risk, 2),
            "direction_long": int(side > 0),
            "F1_disp_delta": round(f1, 3) if f1 == f1 else np.nan,
            "F2_retrace_ratio": round(rv / dv, 3) if dv > 0 and len(ret) else np.nan}


def run_ifvg(bars, fp, draws):
    cal = calendar()
    fomc = set(cal[cal.event.str.contains("|".join(FOMC), case=False, na=False)]
               .dt.dt.strftime("%Y-%m-%d"))
    news = set(cal.dt.dt.strftime("%Y-%m-%d"))
    dly = bars.groupby("day").agg(high=("high", "max"), low=("low", "min"))
    atr = (dly.high - dly.low).rolling(14).mean().shift(1).rank(pct=True)
    rows, gate = [], {"sessions": 0, "gap": 0, "inverted": 0, "bias": 0, "entry": 0}
    for day, g in bars.groupby("day", sort=False):
        if day in fomc:
            continue
        g = g.reset_index(drop=True)
        w = g[(g.mins >= M0) & (g.mins <= M1)].reset_index(drop=True)
        if len(w) < 20:
            continue
        gate["sessions"] += 1
        drw = draws.get(day, 0)
        hit = False
        for rule in ("5min", "15min"):
            if hit:
                break
            r = resample(g[g.mins <= M1], rule)
            if len(r) < 4:
                continue
            for k in range(2, len(r)):
                a, c = r.iloc[k - 2], r.iloc[k]
                for gside, lo_, hi_ in ((-1, c.high, a.low), (+1, a.high, c.low)):
                    if not (hi_ > lo_):                                   # I1 an FVG exists
                        continue
                    gate["gap"] += 1
                    # I2 inversion: a LATER 1-min bar must CLOSE beyond the gap
                    gt = r.index[k]
                    post = w[w.ts > gt]
                    if not len(post):
                        continue
                    inv = (post.close > hi_) if gside < 0 else (post.close < lo_)
                    if not inv.any():
                        continue
                    gate["inverted"] += 1
                    side = +1 if gside < 0 else -1        # bearish gap inverted up -> LONG
                    if drw != side:                                        # I3 [U] bias gate
                        continue
                    gate["bias"] += 1
                    ii = int(inv.idxmax())
                    ce = (hi_ + lo_) / 2                                   # I4
                    fwd = w.loc[ii + 1:] if ii + 1 in w.index else w.iloc[0:0]
                    back = (fwd.low <= ce) if side > 0 else (fwd.high >= ce)
                    if not len(fwd) or not back.any():
                        continue
                    t = int(back.idxmax())
                    gate["entry"] += 1
                    entry = float(ce); stop = entry - side * IFVG_STOP     # I5
                    R, ex, be = walk_exit(g, w, t, entry, stop, side, IFVG_STOP)
                    rows.append({"card": "zxck-ifvg-50", "date": day,
                                 "time": f"{w.ts.iloc[t]:%H:%M}",
                                 "direction": "long" if side > 0 else "short",
                                 "entry": round(entry, 2), "stop": round(stop, 2),
                                 "target": round(entry + side * 2 * IFVG_STOP, 2),
                                 "exit": round(float(ex), 2), "risk_pts": IFVG_STOP,
                                 "R": round(R, 3),
                                 "outcome": "win" if R >= 2 else ("BE" if R == 0 else
                                            ("loss" if R <= -1 else "timeout")),
                                 "be_moved": be, "tf": rule,
                                 **features(g, w, t, side, entry, IFVG_STOP, day, atr, news,
                                            fp, w.ts.iloc[ii])})
                    hit = True
                    break
                if hit:
                    break
    return pd.DataFrame(rows), gate


def run_cisd(bars, fp):
    cal = calendar()
    fomc = set(cal[cal.event.str.contains("|".join(FOMC), case=False, na=False)]
               .dt.dt.strftime("%Y-%m-%d"))
    news = set(cal.dt.dt.strftime("%Y-%m-%d"))
    dly = bars.groupby("day").agg(high=("high", "max"), low=("low", "min"))
    atr = (dly.high - dly.low).rolling(14).mean().shift(1).rank(pct=True)
    rows, gate = [], {"sessions": 0, "cisd": 0, "entry": 0, "skip_draw_first": 0}
    for day, g in bars.groupby("day", sort=False):
        if day in fomc:
            continue
        g = g.reset_index(drop=True)
        w = g[(g.mins >= M0) & (g.mins <= M1)].reset_index(drop=True)
        if len(w) < 20:
            continue
        gate["sessions"] += 1
        h = resample(g[g.mins <= M0], "1h")                                # C2 1-hour
        if len(h) < 2:
            continue
        prev, cur = h.iloc[-2], h.iloc[-1]
        prev_up = prev.close > prev.open
        # C1 the latest 1H candle closes beyond the OPENING PRICE of the adjacent opposing one
        if prev_up and cur.close < prev.open:
            side, lvl, ext = -1, float(prev.open), float(cur.high)
        elif (not prev_up) and cur.close > prev.open:
            side, lvl, ext = +1, float(prev.open), float(cur.low)
        else:
            continue
        gate["cisd"] += 1
        entry = lvl + side * 2 * TICK                                      # C3 two ticks beyond
        stop = ext                                                          # C4 structural
        risk = abs(entry - stop)
        if risk < 5.0:                                                      # C4 floor
            risk = 5.0
            stop = entry - side * risk
        back = (w.low <= entry) if side > 0 else (w.high >= entry)
        if not back.any():
            continue
        t = int(back.idxmax())
        tgt = entry + side * 2 * risk
        pre_hit = (w.iloc[:t].high >= tgt).any() if side > 0 else (w.iloc[:t].low <= tgt).any()
        if pre_hit:                                                         # C5 draw taken first
            gate["skip_draw_first"] += 1
            continue
        gate["entry"] += 1
        R, ex, be = walk_exit(g, w, t, entry, stop, side, risk)
        rows.append({"card": "zxck-cisd", "date": day, "time": f"{w.ts.iloc[t]:%H:%M}",
                     "direction": "long" if side > 0 else "short",
                     "entry": round(entry, 2), "stop": round(stop, 2), "target": round(tgt, 2),
                     "exit": round(float(ex), 2), "risk_pts": round(risk, 2), "R": round(R, 3),
                     "outcome": "win" if R >= 2 else ("BE" if R == 0 else
                                ("loss" if R <= -1 else "timeout")),
                     "be_moved": be, "tf": "1h",
                     **features(g, w, t, side, entry, risk, day, atr, news, fp, w.ts.iloc[0])})
    return pd.DataFrame(rows), gate


def summarise(d, label):
    if not len(d):
        return {"card": label, "n": 0}
    eq = d.R.cumsum(); c = float((COST_USD / (d.risk_pts * PT)).mean())
    return {"card": label, "n": len(d), "win%": 100 * (d.R >= 2).mean(),
            "BE%": 100 * (d.R == 0).mean(), "loss%": 100 * (d.R <= -1).mean(),
            "avgR": d.R.mean(), "cost": c, "exp": d.R.mean() - c, "totR": d.R.sum(),
            "maxDD": float((eq.cummax() - eq).max())}


def main() -> None:
    bars = load_bars()
    bars = bars[(bars.day >= LO) & (bars.day <= HI)]
    fp = flow_frame()
    draws = daily_draw(load_bars())

    print("RAW BASELINES — zxck-ifvg-50 and zxck-cisd. Shared harness, locked exit.\n")
    print(f"NQ 1-min   window 09:45-10:15 ET [U]   span {LO} -> {HI}\n")

    di, gi = run_ifvg(bars, fp, draws)
    dc, gc = run_cisd(bars, fp)

    print("GATE COUNTS — before any outcome is summarised")
    print(f"  zxck-ifvg-50 : sessions {gi['sessions']}  ->  5m/15m FVGs {gi['gap']}"
          f"  ->  inverted by a close {gi['inverted']}"
          f"  ->  draw-aligned {gi['bias']}  ->  filled {gi['entry']}")
    print(f"  zxck-cisd    : sessions {gc['sessions']}  ->  1H CISD present {gc['cisd']}"
          f"  ->  filled {gc['entry']}   (skipped, draw taken first: {gc['skip_draw_first']})\n")

    rows = [summarise(di, "zxck-ifvg-50"), summarise(dc, "zxck-cisd")]
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:+.3f}"))
    for lab, d in (("zxck-ifvg-50", di), ("zxck-cisd", dc)):
        if len(d) >= 5:
            e = d.assign(era=np.where(d.date < "2026-01-01", "2025", "2026"))
            print(f"\n{lab} era split:")
            print(e.groupby("era").R.agg(n="size", win_rate=lambda x: (x >= 2).mean(),
                                         avg_R="mean", total="sum").to_string())
    both = pd.concat([di, dc], ignore_index=True)
    p = OUT / "zxck-remaining-raw-trades.csv"
    both.to_csv(p, index=False)
    print(f"\ntrades -> {p.relative_to(ROOT)}  ({len(both)} rows)")


if __name__ == "__main__":
    main()
