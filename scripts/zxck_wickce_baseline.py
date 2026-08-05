#!/usr/bin/env python3
"""RAW BASELINE — zxck-wick-ce, exactly as carded. No enhancements, no filters.

Card: research/zxcked/strategies/zxck-wick-ce.md (PARTIAL — Q3 unresolved by instruction)
Gate: scripts/zxck_wick_gate.py  -> 38 events (17 in 2025, 21 in 2026)
Exit: research/zxcked/strategies/EXIT-CONVENTION-LOCKED.md — identical to ash-unicorn-sb.

=========================== MECHANIZED RULESET, WITH PROVENANCE ==========================
[S]=stated by him  [I]=inferred  [U]=stated-by-user  [A]=our assumption  [LOCK]=locked exit

W0  WINDOW [U]   09:45-10:15 ET, 2025-06-01 -> 2026-07-15. Brake's macro rule + the flow span.
                 NEITHER trader states a window for this card. COMPONENTS F000.
W1  WICK [A]     a 1-minute bar with a >=10.0pt wick on one side.
                 He gives NO size threshold for a rejection wick. The only quantified wick
                 guidance in his corpus is the key-open MANIPULATION floor [5pL41Pl7GM4].
                 Reused here. OURS BY EXTENSION. It barely binds (249 of 266 sessions pass).
W2  CLOSE [S]    the bar must close AGAINST its own wick — down-close for an upper wick.
                 "it's not a rejection block until this candle closes" [AGmRZ9Te9NY 02:47].
                 Explicitly NOT the ICT definition, by his own insistence [@ 03:11].
W3  SWEEP [S]    the wick must exceed a 15m swing extreme formed before the window opened.
                 "We swept liquidity and we had a bearish candle close. You can say that that's
                 good enough." [a3LzCUZU5ko 02:24] — sweep + close is his stated MINIMUM.
W4  ENGINEERED LIQUIDITY [S/I]  a prior extreme resting >2.0pt beyond the CE, inside the wick.
                 "if it's like two points or less away from the CE, I'll just not take it"
                 [xae9AiV5Ps4 02:16].
                 ⚠️ Q3 UNRESOLVED BY INSTRUCTION. [wS-dBenAIlY 01:11] and [xae9AiV5Ps4 02:40]
                 put this on OPPOSITE sides. The inside-the-wick reading rides as [inferred].
                 Every number below carries that assumption.
W5  ENTRY [S]    limit at the CE (the wick's 50%), filled on the first return after the wick bar.
                 "If the risk is too much, then put it at the CE" [6opmiyFvJBA 08:40].
                 [A] no edge tolerance -> our fill rate is a LOWER BOUND on his.
W6  STOP [S]     at the wick's extreme, no buffer (most literal reading of "stop below the wick").
                 => risk = half the wick length, so the 10pt wick floor implies a >=5pt stop,
                 which coincides with his stated 5pt minimum [BOuJLWIisMI 03:28]. Not tuned.
W7  TARGET [LOCK] entry +/- 2 x risk.   W8 BREAK-EVEN [LOCK] at 1R.   W9 NO TRAILING [LOCK].
W10 same-bar stop+target -> STOP first [LOCK].   W11 cap 16:00 ET [LOCK].
W12 ONE TRADE PER DAY [I]. W13 AVOID FOMC / Fed-Chair-Powell sessions [S] [xae9AiV5Ps4 01:31].

--------------------------------- NOT IMPLEMENTED ---------------------------------
N1 PD-array coincidence and the fib — BONUSES [tNyT7tHOmGI 16:19].
N2 Displacement validation — a TELL for WHERE to enter, not a take/skip gate [pMv3USznFdU 07:24].
N3 SMT — needs ES. Not held, and Brake has declined to buy it.
N4 The far-edge entry — UNTESTABLE at n=12, see zxck-gap-fill-edge.md.
N5 Order flow — COMPUTED for pooling, never applied.
==========================================================================================

    python -m scripts.zxck_wickce_baseline
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.f2_oos_test import flow_frame  # noqa: E402  (local frame, includes January)
from scripts.nya_sb01_feasibility import find_fvg, load_bars, swing_levels  # noqa: E402
from scripts.zxck_keyopen_baseline import FOMC, calendar  # noqa: E402
from scripts.zxck_wick_gate import EL_MIN, HI, LO, M0, M1, WICK_PTS  # noqa: E402

RTH_END = 16 * 60
COST_USD, PT = 25.0, 20.0
OUT = ROOT / "research/zxcked/strategies"


def run(bars: pd.DataFrame, fp: pd.DataFrame) -> pd.DataFrame:
    cal = calendar()
    fomc = set(cal[cal.event.str.contains("|".join(FOMC), case=False, na=False)]
               .dt.dt.strftime("%Y-%m-%d"))
    news = set(cal.dt.dt.strftime("%Y-%m-%d"))
    dly = bars.groupby("day").agg(high=("high", "max"), low=("low", "min"))
    atr = (dly.high - dly.low).rolling(14).mean().shift(1).rank(pct=True)
    rows = []
    for day, g in bars.groupby("day", sort=False):
        if day in fomc:
            continue
        g = g.reset_index(drop=True)
        w = g[(g.mins >= M0) & (g.mins <= M1)].reset_index(drop=True)
        if len(w) < 20:
            continue
        hs, ls = swing_levels(g, M0)
        pre = g[g.mins < M0]
        done = False
        for i in range(len(w) - 1):
            if done:
                break
            bar = w.iloc[i]
            bh, bl = max(bar.open, bar.close), min(bar.open, bar.close)
            for side, wl, tip, lvls in ((-1, bar.high - bh, bar.high, hs),
                                        (+1, bl - bar.low, bar.low, ls)):
                if wl < WICK_PTS:                                              # W1
                    continue
                if (side < 0) != (bar.close < bar.open):                       # W2
                    continue
                swept = ([x for x in lvls if bh < x < tip] if side < 0
                         else [x for x in lvls if tip < x < bl])               # W3
                if not swept:
                    continue
                ce = (tip + bh) / 2 if side < 0 else (tip + bl) / 2
                el = [x for x in lvls if (side < 0 and ce + EL_MIN < x <= tip)
                      or (side > 0 and tip <= x < ce - EL_MIN)]                # W4
                if not el:
                    continue
                fwd = w.iloc[i + 1:]
                back = (fwd.high >= ce) if side < 0 else (fwd.low <= ce)       # W5
                if not len(fwd) or not back.any():
                    continue
                t = int(back.idxmax())
                entry, stop = float(ce), float(tip)                            # W6
                risk = abs(entry - stop)
                if risk <= 0:
                    continue
                target = entry + side * 2 * risk                               # W7
                half = entry + side * risk                                     # W8
                # R10/W10 SAME-BAR: the entry bar itself can carry price through the stop.
                # Entry is the wick's MIDpoint and the stop its TIP, so the fill bar frequently
                # continues into the stop within the same minute. Scanning from t+1 would miss
                # that and make the result OPTIMISTIC. Fixed 2026-08-07 after a bar-by-bar
                # replay of 2025-06-05 showed exactly this (fill 10:14, that bar's low already
                # through the stop). Stop assumed first, per the locked convention.
                fb = w.iloc[t]
                same_bar_stop = (fb.low <= stop) if side > 0 else (fb.high >= stop)
                tail = pd.concat([w.iloc[t + 1:], g[(g.mins > M1) & (g.mins <= RTH_END)]])
                cur, be, out, ex = stop, False, None, None
                if same_bar_stop:
                    out, ex = -1.0, stop
                for _, b2 in (tail.iterrows() if out is None else iter([])):
                    if side > 0:
                        if b2.low <= cur:
                            out, ex = (0.0 if be else -1.0), cur; break
                        if b2.high >= target:
                            out, ex = 2.0, target; break
                        if not be and b2.high >= half:
                            cur, be = entry, True
                    else:
                        if b2.high >= cur:
                            out, ex = (0.0 if be else -1.0), cur; break
                        if b2.low <= target:
                            out, ex = 2.0, target; break
                        if not be and b2.low <= half:
                            cur, be = entry, True
                if out is None:                                                # W11
                    last = float(tail.close.iloc[-1]) if len(tail) else entry
                    out, ex = float(side * (last - entry) / risk), last

                # ---- flow, same definitions as ash-unicorn-sb, minutes <= entry only ----
                t0, te = w.ts.iloc[i], w.ts.iloc[t]
                disp = fp[(fp.index >= t0) & (fp.index <= t0)]
                ret = fp[(fp.index > t0) & (fp.index <= te)]
                sess = fp[(fp.index >= w.ts.iloc[0]) & (fp.index <= te)].vol
                assert not len(ret) or ret.index.max() <= te
                med = float(sess.median()) if len(sess) else np.nan
                f1 = float(disp.delta.sum()) * side / med if (len(disp) and med) else np.nan
                dv, rv = float(disp.vol.sum()), float(ret.vol.sum())
                f2 = rv / dv if dv > 0 and len(ret) else np.nan

                h1 = float(pre.close.iloc[-1] - pre.close.iloc[-120]) if len(pre) > 120 else np.nan
                phi = float(pre.high.max()) if len(pre) else np.nan
                plo = float(pre.low.min()) if len(pre) else np.nan
                rows.append({
                    "date": day, "time": f"{te:%H:%M}", "session": "NY",
                    "window": "09:45-10:15", "direction": "long" if side > 0 else "short",
                    "entry": round(entry, 2), "stop": round(stop, 2),
                    "target": round(target, 2), "exit": round(float(ex), 2),
                    "risk_pts": round(risk, 2), "wick_pts": round(wl, 2), "R": round(out, 3),
                    "outcome": "win" if out >= 2 else ("BE" if out == 0 else
                               ("loss" if out <= -1 else "timeout")),
                    "be_moved": be, "has_fvg": find_fvg(w, i, side) is not None,
                    "dow": pd.Timestamp(day).day_name()[:3],
                    "entry_min_into_window": int(w.mins.iloc[t] - M0),
                    "atr_pct": float(atr.get(day, np.nan)),
                    "htf_aligned": int((h1 > 0) == (side > 0)) if h1 == h1 else np.nan,
                    "dist_to_level_R": (round(min(abs(entry - phi), abs(entry - plo)) / risk, 3)
                                        if phi == phi else np.nan),
                    "news_day": int(day in news), "risk_pts_v": round(risk, 2),
                    "direction_long": int(side > 0),
                    "F1_disp_delta": round(f1, 3) if f1 == f1 else np.nan,
                    "F2_retrace_ratio": round(f2, 3) if f2 == f2 else np.nan})
                done = True
                break
    return pd.DataFrame(rows)


def main() -> None:
    bars = load_bars()
    bars = bars[(bars.day >= LO) & (bars.day <= HI)]
    d = run(bars, flow_frame())
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "zxck-wick-ce-raw-trades.csv"
    d.to_csv(p, index=False)

    print("RAW BASELINE — zxck-wick-ce, exactly as carded. No filters.\n")
    print(f"NQ 1-min   window 09:45-10:15 ET   span {LO} -> {HI}")
    print(f"wick floor {WICK_PTS:.0f}pt [OURS]   engineered liquidity >{EL_MIN:.0f}pt [his]")
    print("⚠️ Q3 unresolved: the inside-the-wick liquidity reading rides as an assumption.\n")
    if not len(d):
        print("no trades"); return
    eq = d.R.cumsum(); cost = float((COST_USD / (d.risk_pts * PT)).mean())
    print("=" * 70)
    print(f"  n {len(d)}   win {int((d.R>=2).sum())}  loss {int((d.R<=-1).sum())}  "
          f"BE {int((d.R==0).sum())}  timeout {int(((d.R>-1)&(d.R<2)&(d.R!=0)).sum())}")
    print(f"  win rate     {100*(d.R>=2).mean():.1f}%")
    print(f"  avg R        {d.R.mean():+.3f}")
    print(f"  cost         {cost:.3f}R/trade   (median stop {d.risk_pts.median():.1f}pt)")
    print(f"  expectancy   {d.R.mean()-cost:+.3f}R net")
    print(f"  total        {d.R.sum():+.1f}R gross / {d.R.sum()-cost*len(d):+.1f}R net")
    print(f"  max drawdown {float((eq.cummax()-eq).max()):.1f}R")
    print(f"  direction    {int((d.direction=='long').sum())} long / "
          f"{int((d.direction=='short').sum())} short")
    print("=" * 70)
    e = d.assign(era=np.where(d.date < "2026-01-01", "2025", "2026"))
    print("\nera split:")
    print(e.groupby("era").R.agg(n="size", win_rate=lambda x: (x >= 2).mean(),
                                avg_R="mean", total="sum").to_string())
    print(f"\nwick size: median {d.wick_pts.median():.1f}pt   stop: median "
          f"{d.risk_pts.median():.1f}pt (= half the wick, by construction)")
    print(f"of these events, {int(d.has_fvg.sum())} also had an FVG "
          f"(the gap-fill-edge subset, n=12 at its own entry)")
    print(f"\nflow computed on {int(d[['F1_disp_delta','F2_retrace_ratio']].notna().all(axis=1).sum())}"
          f"/{len(d)} — NOT applied.")
    print(f"\ntrades -> {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
