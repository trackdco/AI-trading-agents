#!/usr/bin/env python3
"""RAW BASELINE — ash10hazard `ash-unicorn-sb`, exactly as taught. No enhancements.

No order flow, no added filters, no optimisation. Every discretionary choice is resolved to
the MOST LITERAL reading of his own words and recorded in ASSUMPTIONS below.

TWO SESSION VARIANTS of one card:
  NY     09:45-10:15, 10:45-11:15, 11:45-12:15, 13:45-14:15 ET  (12:45-13:15 skipped by him)
  LONDON 02:45-03:15, 03:45-04:15 ET

=============================== ASSUMPTIONS (recorded, not optimised) ==================
A1 ORDER BLOCK — he NEVER defines identification in 8 transcripts. Most literal reading of
   his usage: the last candle opposing the displacement, immediately before the leg that
   broke structure. THIS IS OUR RECONSTRUCTION, NOT HIS STATED RULE.
A2 STOP — "I'd run my stop at the most recent short-term low" [qngA8aIfV0M 08:01], taken as
   the ORDER BLOCK EDGE (its high for shorts, low for longs). Corroborated externally: this
   gives median 19.2pt/mean 25.5pt risk against his stated 27/28/51/53pt stops. The two
   rejected readings gave 58pt and 3.75pt.
A3 TARGET — 2R. "Usually, a 1 to 2 or 1 to 3 is perfect" [qngA8aIfV0M 08:35]; 1:2 is the one
   he names first and uses in most examples.
A4 BREAK-EVEN — stop to entry once price reaches 50% of entry->target. Stated in THREE
   videos [1cMWnAxElA0 06:53, pD5l_gEje9I 03:50, UBIHB1oB784 03:12].
A5 NO TRAILING — he states an R-multiple ladder then explicitly disowns it ("I don't like to
   be so systematic anymore... I look at the scenario" [1cMWnAxElA0 03:19]) and says his own
   trailing would have lost the demonstrated trade [UBIHB1oB784 07:40]. Discretionary by his
   own account, so it is NOT mechanised. BE (A4) is kept because it is stated consistently.
A6 BIAS — per-timeframe state machine IS stated: out of a bullish gap -> bullish, into a
   bearish gap -> bearish, swing taken -> neutral [qngA8aIfV0M 04:39-06:43]. Aggregation is
   NOT stated. Most literal: in his one worked example the DAILY is the decider, so the
   daily bias must agree with the trade direction.
A7 EXIT HORIZON — not specified. His targets exceed some macro windows' entire range, so
   trades cannot resolve inside 30 min. Held to stop/target, capped at 16:00 ET.
A8 SAME-BAR stop+target -> STOP assumed first (against the trade).
A9 ONE trade per macro window; day ends after 2 losses [qngA8aIfV0M 00:52].

*** NOT IMPLEMENTABLE: the ES LEADING TRIGGER. He enters when ES taps its FVG, before NQ
*** taps its own [qngA8aIfV0M 08:01]. WE HOLD NO ES DATA. This is a declared entry
*** component of the model and its absence is a limit on every number below.
=======================================================================================

    python -m scripts.ash_raw_baseline
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_sb01_feasibility import (  # noqa: E402
    MSS_LOOKBACK, find_fvg, load_bars, order_block, session_extremes, swing_levels,
)

NY = "America/New_York"
RTH_END = 16 * 60
# NARROWED 2026-08-06 (Brake): AM1 ONLY from here on.
# Legitimacy note — this is NOT rank-and-promote. He names AM1 as highest-probability
# BEFORE any test, with a stated mechanism: "that's because it's 15 minutes after the New
# York open... it injects high liquidity and therefore makes it high probability"
# [qngA8aIfV0M 01:46]. §6.0 permits a mechanism-prior default spec; it forbids picking the
# in-sample winner. AM1 was his pick first and ours second.
SESSIONS = {
    "NY": [("AM1", 585, 615)],
}


def daily_bias(bars: pd.DataFrame, day: str) -> int:
    """A6: daily FVG state machine, using only days STRICTLY BEFORE `day`."""
    d = bars[bars.day < day]
    if len(d) < 3 * 1440:
        return 0
    # ⚠️ SUNDAY-STUB DEFECT FIXED 2026-08-08 (adversarial retro-audit; confirmed by two
    # independent lenses and neither refuter could break it).
    # resample("1D") on NY-LOCAL timestamps keys on the NY CALENDAR day. Globex opens 18:00 ET
    # on SUNDAY, so every Sunday became its own "daily bar" holding only that 6-hour block:
    # 80 such stubs over the span, median range 184.5pt against 393.5pt for a real weekday.
    # Those stubs are fed to the FVG bias state machine as if they were sessions. Measured:
    # they participate in 54 of 117 bias-SET events, and the resulting daily bias differs from
    # the correct one on 84 of 480 days.
    # FIX: key on the CME session (18:00 ET -> 18:00 ET) and use COMPLETED sessions only.
    # Verified equivalent to simply dropping the Sunday stubs — byte-identical trade set.
    # The cut point is NOT a tunable parameter: hour 17 ET holds ZERO bars (CME maintenance
    # break), so every boundary in [17:00, 18:00) produces the same frame.
    g = (d.set_index(d.ts + pd.Timedelta(hours=6)).resample("1D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna())
    if len(g) > 1:
        g = g.iloc[:-1]          # drop the trailing INCOMPLETE session (a 6-hour stub itself)
    if len(g) < 5:
        return 0
    hi, lo = g.high.to_numpy(), g.low.to_numpy()
    # CORRECTION: he says a SWING low resets bias, not the previous bar's low. A swing
    # low is a fractal (lower than the bar either side). Using the prior bar made 59% of
    # days neutral, which is an artifact of my wording, not his rule.
    swing_lo = [i for i in range(1, len(g) - 1) if lo[i] < lo[i - 1] and lo[i] < lo[i + 1]]
    swing_hi = [i for i in range(1, len(g) - 1) if hi[i] > hi[i - 1] and hi[i] > hi[i + 1]]
    bias = 0
    for i in range(2, len(g)):
        a, c = g.iloc[i - 2], g.iloc[i]
        if a.low > c.high:
            bias = -1
        elif a.high < c.low:
            bias = +1
        prior_sl = [j for j in swing_lo if j < i]
        prior_sh = [j for j in swing_hi if j < i]
        if bias > 0 and prior_sl and c.low < lo[prior_sl[-1]]:
            bias = 0
        elif bias < 0 and prior_sh and c.high > hi[prior_sh[-1]]:
            bias = 0
    return bias


def run(session: str, bars: pd.DataFrame) -> pd.DataFrame:
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    days = sorted(by_day)
    trades = []
    for k, day in enumerate(days):
        g, prev = by_day[day], by_day[days[k - 1]] if k else None
        if prev is None:
            continue
        bias = daily_bias(bars, day)
        losses = 0
        for name, m0, m1 in SESSIONS[session]:
            if losses >= 2:
                break
            w = g[(g.mins >= m0) & (g.mins <= m1)].reset_index(drop=True)
            if len(w) < 20:
                continue
            hs, ls = swing_levels(g, m0)
            ext = session_extremes(g, prev)
            cands = ([(x, -1) for x in hs + [ext.get("asia_hi"), ext.get("lon_hi")] if x]
                     + [(x, +1) for x in ls + [ext.get("asia_lo"), ext.get("lon_lo")] if x])
            for lv, side in cands:
                if bias != side:                       # A6 daily bias must agree
                    continue
                # ⚠️ DEFECT FIXED 2026-08-07 (found by adversarial audit, confirmed
                # independently). The old test was `w.high > lv` / `w.low < lv`, which asks
                # WHERE PRICE IS, not WHETHER IT CROSSED. If price was already beyond the level
                # when the macro opened, hit was True on bar 0 -> s=0 -> the MSS lookback
                # `seg = w.iloc[max(0,s-20):s+1]` collapsed to a SINGLE bar, so `ref` became that
                # bar's own extreme and any small move past it scored as a structure shift.
                # Measured on the shipped 37 rows: s==0 on 30 of 37, and on 25 of 37 price was
                # already beyond the level BEFORE 09:45. Card conditions #2 (liquidity sweep) and
                # #3 (market structure shift) did not bind on the majority of the sample.
                # A sweep requires price to START the window on the unswept side and then take
                # the level. This is a fix to match the card, not a spec change.
                o0 = float(w.open.iloc[0])
                if (o0 > lv) if side < 0 else (o0 < lv):
                    continue                       # already swept before the macro -> not a sweep
                hit = (w.high > lv) if side < 0 else (w.low < lv)
                if not hit.any():
                    continue
                s = int(hit.idxmax())
                seg, post = w.iloc[max(0, s - MSS_LOOKBACK):s + 1], w.iloc[s + 1:]
                if not len(seg) or not len(post):
                    continue
                ref = float(seg.low.min()) if side < 0 else float(seg.high.max())
                brk = (post.close < ref) if side < 0 else (post.close > ref)
                if not brk.any():
                    continue
                m = int(brk.idxmax())
                fv = find_fvg(w, m, side)
                if fv is None:
                    continue
                edge, _far, fstart = fv
                ob, _ = order_block(w, fstart, side)
                if ob is None:
                    continue
                fwd = w.iloc[m + 1:]
                fill = (fwd.high >= edge) if side < 0 else (fwd.low <= edge)
                if not len(fwd) or not fill.any():
                    continue
                t = int(fill.idxmax())
                entry, stop = float(edge), float(ob)
                risk = abs(entry - stop)
                if risk <= 0:
                    continue
                target = entry - 2 * risk if side < 0 else entry + 2 * risk
                half = entry - risk if side < 0 else entry + risk   # A4 50% to target
                # ⚠️ SAME-BAR FILL-AND-STOP, fixed 2026-08-07. The walk used to start at t+1,
                # so a bar that filled the entry AND ran through the stop within the same
                # minute was scored as if the trade were still open at the next bar's open.
                # A8 already says stop-first on a same-bar conflict; this makes the code obey
                # it. Identical to walk_exit() in zxck_remaining_baselines.py, so both books
                # stay poolable.
                fb = w.iloc[t]
                same_bar_stop = (fb.high >= stop) if side < 0 else (fb.low <= stop)
                tail = pd.concat([w.iloc[t + 1:],
                                  g[(g.mins > m1) & (g.mins <= RTH_END)]])
                cur_stop, be, out, ex_px, ex_ts = stop, False, None, None, None
                if same_bar_stop:
                    out, ex_px, ex_ts = -1.0, stop, fb.ts
                for _, bar in (tail.iterrows() if out is None else iter([])):
                    if side < 0:
                        if bar.high >= cur_stop:
                            out, ex_px, ex_ts = (0.0 if be else -1.0), cur_stop, bar.ts; break
                        if bar.low <= target:
                            out, ex_px, ex_ts = 2.0, target, bar.ts; break
                        if not be and bar.low <= half:
                            cur_stop, be = entry, True
                    else:
                        if bar.low <= cur_stop:
                            out, ex_px, ex_ts = (0.0 if be else -1.0), cur_stop, bar.ts; break
                        if bar.high >= target:
                            out, ex_px, ex_ts = 2.0, target, bar.ts; break
                        if not be and bar.high >= half:
                            cur_stop, be = entry, True
                if out is None:                                   # A7 cap at RTH close
                    last = float(tail.close.iloc[-1]) if len(tail) else entry
                    out = float(((entry - last) if side < 0 else (last - entry)) / risk)
                    ex_px, ex_ts = last, (tail.ts.iloc[-1] if len(tail) else w.ts.iloc[t])
                trades.append({
                    "date": day, "time": f"{w.ts.iloc[t]:%H:%M}", "session": session,
                    "window": name, "direction": "short" if side < 0 else "long",
                    "entry": round(entry, 2), "stop": round(stop, 2),
                    "target": round(target, 2), "exit": round(float(ex_px), 2),
                    "exit_time": f"{ex_ts:%H:%M}" if ex_ts is not None else "",
                    "risk_pts": round(risk, 2), "R": round(out, 3),
                    "outcome": "win" if out >= 2 else ("BE" if out == 0 else
                               ("loss" if out <= -1 else "timeout")),
                    "be_moved": be})
                if out <= -1:
                    losses += 1
                break
    return pd.DataFrame(trades)


def stats(d: pd.DataFrame) -> dict:
    if d.empty:
        return {}
    eq = d.R.cumsum()
    return {"n": len(d), "win_rate": (d.R >= 2).mean(), "avg_R": d.R.mean(),
            "expectancy": d.R.mean(), "total_R": d.R.sum(),
            "max_dd_R": float((eq.cummax() - eq).max()),
            "wins": int((d.R >= 2).sum()), "losses": int((d.R <= -1).sum()),
            "be": int((d.R == 0).sum()), "timeouts": int(((d.R > -1) & (d.R < 2) &
                                                          (d.R != 0)).sum())}


def main() -> None:
    bars = load_bars()
    print("RAW BASELINE — ash-unicorn-sb, exactly as taught. No enhancements.\n")
    print(f"instrument: NQ 1-min   range: {bars.day.min()} -> {bars.day.max()}"
          f"   days: {bars.day.nunique()}")
    print("*** ES leading trigger NOT implemented — no ES data held. See docstring. ***\n")
    out_dir = ROOT / "research/ash10hazard/strategies"
    out_dir.mkdir(parents=True, exist_ok=True)
    allt = []
    for sess in SESSIONS:
        d = run(sess, bars)
        allt.append(d)
        s = stats(d)
        print("=" * 74)
        print(f"{sess}  windows: {', '.join(n for n, _, _ in SESSIONS[sess])}")
        print("=" * 74)
        if not s:
            print("  no trades")
            continue
        print(f"  n {s['n']}   win {s['wins']}  loss {s['losses']}  BE {s['be']}  "
              f"timeout {s['timeouts']}")
        print(f"  win rate {100*s['win_rate']:.1f}%   avg R {s['avg_R']:+.3f}   "
              f"total {s['total_R']:+.1f}R   maxDD {s['max_dd_R']:.1f}R")
        print(f"  median stop {d.risk_pts.median():.1f} pts")
        print("  by window: " + ", ".join(
            f"{w} n={len(x)} WR={100*(x.R>=2).mean():.0f}% R={x.R.mean():+.2f}"
            for w, x in d.groupby("window")))
    full = pd.concat(allt, ignore_index=True)
    p = out_dir / "ash-unicorn-sb-raw-trades.csv"
    full.to_csv(p, index=False)
    print(f"\ntrades written -> {p}  ({len(full)} rows)")


if __name__ == "__main__":
    main()
