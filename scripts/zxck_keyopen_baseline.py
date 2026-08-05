#!/usr/bin/env python3
"""RAW BASELINE — zxck-10am-keyopen, exactly as carded. No enhancements, no filters.

Card: research/zxcked/strategies/zxck-10am-keyopen.md (rev b, CONFIRMED)
Exit: research/zxcked/strategies/EXIT-CONVENTION-LOCKED.md — identical to ash-unicorn-sb.

=========================== MECHANIZED RULESET, WITH PROVENANCE ==========================
Every rule below is decidable from price data alone. Tags: [S]=stated by him,
[I]=inferred from his words, [U]=stated-by-user (Brake), [LOCK]=locked exit convention,
[A]=our assumption where his words leave a genuine but minor choice. NOTHING is optimised.

R1  THE LEVEL [S]  P = the OPEN of the 10:00:00 ET one-minute bar.
    10:00 ET is the 4-hour candle open on an 18:00-ET (CME session) grid:
    18/22/02/06/10/14. [Y-oqSZmNo4U 00:49] "the 10:00 a.m. is the 4hour candle open"

R2  THE WINDOW [U]  10:00 -> 10:15 ET. He never names an expiry.
    CORRECTED 2026-08-07: rev-a used 10:00->14:00 (the 4H candle). That was MY assumption and it
    violated Brake's standing instruction -- "from here onwards we only will stick to 9:45-10:15
    macro" -- and broke like-for-like comparison with ash-unicorn-sb, which is scored on a
    30-minute window with a hard 10:15 cutoff. 10:00-10:15 is the honest intersection of his
    level and that macro. The error was mine and it was caught by Brake, not by me.

R3  MANIPULATION [S/I]  the first excursion of >= 10.0 points beyond P, either side.
    Four labelled examples: 2pt "No" [5pL41Pl7GM4 01:58]; 8pt "gray area" [09:26];
    10pt "you can clearly see that's a wick" [10:10]; 15pt "Yes" [05:50].
    [U] Brake ratified the FIXED point value. The ATR-scaled variant (COMPONENTS F0.1) is OURS,
    unimplemented, and MUST NOT be substituted even if the sample is thin.
    If both sides breach 10pt inside the SAME minute bar the side is undecidable -> SKIPPED and
    logged, never guessed.

R4  DIRECTION [S]  opposite the manipulation. Manipulated DOWN -> LONG.
    [tNyT7tHOmGI 15:08] "10:00 a.m. opens lower, goes wicks down by 20 points... All we want
    with 10 a.m. is a lower wick, so that we can distribute to the upside."

R5  DISTRIBUTION [S]  a 1-minute bar must CLOSE beyond P in the trade direction, after R3.
    [38YtF6xFX4o 03:45] "you want to see a strong candle close above that level"

R6  ENTRY [S]  a limit at P exactly. Fills on the first touch of P after R5.
    [Y-oqSZmNo4U 05:12] "I want to have a short limit at this 10 a.m. key open"
    [A] No edge tolerance. He allows ~1pt of slack resolved by a lower-timeframe trigger
    [y7KMT9CIVMo 03:32], but that is a different entry mechanism. Fill-on-touch makes our fill
    rate a LOWER BOUND on his.

R7  STOP [S]  a static 15 points. Stated twice as his own choice for this exact setup:
    [Y-oqSZmNo4U 07:52] "for me, I would probably have like a 15 point stop... let price breathe
    a little bit because we do have like the most volatile session"
    [tNyT7tHOmGI 17:05] "Then I had a 15-point stop just to cover the midpoint"
    NOTE: this makes risk_pts CONSTANT, so stop_size is a degenerate autopsy feature and
    dist_to_level_R is just distance/15.

R8  TARGET [LOCK]  entry +/- 2 x risk = 30 points. NOT his 1:4-1:6 band.

R9  BREAK-EVEN [LOCK]  at 1R (15 points), the stop moves to entry.

R10 NO TRAILING [LOCK]. R11 same-bar stop+target -> STOP fills first. R12 cap 16:00 ET.

R13 ONE TRADE PER DAY [I] — there is one 10:00 open per day.

R14 AVOID: FOMC / Fed-Chair-Powell sessions [S] [xae9AiV5Ps4 01:31].
    Implemented from config/news_calendar*.csv on: FOMC Statement / Press Conference /
    Meeting Minutes / Economic Projections, Federal Funds Rate, Fed Chair Powell Testifies.

--------------------------------- DELIBERATELY NOT IMPLEMENTED ---------------------------
N1  PD-array coincidence, and the fib. BOTH ARE BONUSES, not requirements. Same quote that
    resolved Q8: [tNyT7tHOmGI 16:19] "0.79 on the fib... That's a bonus. We have a one- and a
    five-minute rejection block... That's a bonus. And the 10:00 a.m. framework is following
    our idea, our plan." A rejection block IS a PD array, so the card's rev-a setup condition 3
    is downgraded to a bonus by an ALREADY-RESOLVED question.
N2  "manipulates BOTH sides -> no read" [S] has no mechanical form in his words. Under R3
    (first excursion wins) it can only fire on a same-bar tie, which IS implemented. Any
    stronger version would be our tie-break, so none was invented.
N3  Mondays / holiday weeks. On the card as [inferred] and explicitly "never stated as a rule".
    NOT implemented.
N4  PXH/PXL daily-bias agreement. R4 is the card's own direction rule; requiring the daily bias
    to agree as well would be a stricter reading he never states for THIS setup. NOT applied.
    (Its effect would be roughly halving the sample.)
N5  The "first 5-minute trigger after 10:00" entry [WEeXKMzaJjY 14:21]. A second, different
    entry mechanism from a different video; the key-open video itself says limit. NOT run.
N6  Any order-flow filter. Flow columns are COMPUTED, never applied.
==========================================================================================

    python -m scripts.zxck_keyopen_baseline
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_sb01_feasibility import load_bars  # noqa: E402

NY = "America/New_York"
OPEN_MIN = 10 * 60           # 10:00 ET — the 4H candle open
WIN_END = 10 * 60 + 15       # R2 — AM1 OVERLAP 10:00-10:15 ET (Brake standing rule)
RTH_END = 16 * 60            # R12
MANIP_PTS = 10.0             # R3 — FIXED, ratified. Never ATR-scaled.
STOP_PTS = 15.0              # R7 — static
TARGET_R = 2.0               # R8 — LOCKED
COST_USD, PT = 25.0, 20.0    # scoring, identical to ash-unicorn-sb
OUT = ROOT / "research/zxcked/strategies"

FOMC = ("FOMC", "Federal Funds Rate", "Fed Chair Powell Testifies")


def calendar() -> pd.DataFrame:
    c = pd.concat([pd.read_csv(ROOT / f, comment="#")
                   for f in ("config/news_calendar_hist.csv", "config/news_calendar.csv")])
    c["dt"] = pd.to_datetime(c.datetime_ET, errors="coerce")
    return c.dropna(subset=["dt"])


def run(bars: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    fomc_days = set(cal[cal.event.str.contains("|".join(FOMC), case=False, na=False)]
                    .dt.dt.strftime("%Y-%m-%d"))
    news_days = set(cal.dt.dt.strftime("%Y-%m-%d"))
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    dly = bars.groupby("day").agg(high=("high", "max"), low=("low", "min"))
    atr_pct = (dly.high - dly.low).rolling(14).mean().shift(1).rank(pct=True)

    rows = []
    for day, g in by_day.items():
        rec = {"date": day, "session": "NY", "window": "10:00-10:15",
               "news_day": int(day in news_days)}
        if day in fomc_days:                                    # R14
            rows.append({**rec, "taken": "n", "skip_reason": "FOMC/Powell session"})
            continue
        o = g[g.mins == OPEN_MIN]
        if o.empty:
            rows.append({**rec, "taken": "n", "skip_reason": "no 10:00 bar"})
            continue
        P = float(o.open.iloc[0])
        w = g[(g.mins >= OPEN_MIN) & (g.mins <= WIN_END)].reset_index(drop=True)  # R2
        if len(w) < 5:
            rows.append({**rec, "taken": "n", "skip_reason": "short window"})
            continue

        # ---- R3 manipulation: first >=10pt excursion beyond P, either side ----
        up = w.high >= P + MANIP_PTS
        dn = w.low <= P - MANIP_PTS
        if not up.any() and not dn.any():
            rows.append({**rec, "taken": "n", "skip_reason": "no 10pt manipulation"})
            continue
        iu = int(up.idxmax()) if up.any() else 10 ** 9
        idn = int(dn.idxmax()) if dn.any() else 10 ** 9
        if iu == idn:                                           # undecidable, never guessed
            rows.append({**rec, "taken": "n", "skip_reason": "both sides same bar"})
            continue
        m = min(iu, idn)
        side = +1 if idn < iu else -1                           # R4 manip down -> LONG
        manip_pts = float(P - w.low.iloc[:m + 1].min()) if side > 0 \
            else float(w.high.iloc[:m + 1].max() - P)

        # ---- R5 distribution: a bar CLOSES beyond P in the trade direction ----
        post = w.iloc[m + 1:]
        clo = (post.close > P) if side > 0 else (post.close < P)
        if not len(post) or not clo.any():
            rows.append({**rec, "taken": "n", "skip_reason": "no close through the level",
                         "manip_pts": round(manip_pts, 2),
                         "direction": "long" if side > 0 else "short"})
            continue
        c_i = int(clo.idxmax())

        # ---- R6 entry: limit at P, fill on first touch after the distribution close ----
        fwd = w.iloc[c_i + 1:]
        hit = (fwd.low <= P) if side > 0 else (fwd.high >= P)
        if not len(fwd) or not hit.any():
            rows.append({**rec, "taken": "n", "skip_reason": "limit never filled",
                         "manip_pts": round(manip_pts, 2),
                         "direction": "long" if side > 0 else "short"})
            continue
        t = int(hit.idxmax())

        entry = P
        stop = entry - side * STOP_PTS                          # R7
        target = entry + side * TARGET_R * STOP_PTS             # R8
        half = entry + side * STOP_PTS                          # R9 break-even at 1R

        tail = pd.concat([w.iloc[t + 1:], g[(g.mins > WIN_END) & (g.mins <= RTH_END)]])
        cur, be, out, ex_px, ex_ts = stop, False, None, None, None
        for _, bar in tail.iterrows():
            if side > 0:
                if bar.low <= cur:                              # R11 stop first
                    out, ex_px, ex_ts = (0.0 if be else -1.0), cur, bar.ts; break
                if bar.high >= target:
                    out, ex_px, ex_ts = 2.0, target, bar.ts; break
                if not be and bar.high >= half:
                    cur, be = entry, True
            else:
                if bar.high >= cur:
                    out, ex_px, ex_ts = (0.0 if be else -1.0), cur, bar.ts; break
                if bar.low <= target:
                    out, ex_px, ex_ts = 2.0, target, bar.ts; break
                if not be and bar.low <= half:
                    cur, be = entry, True
        if out is None:                                         # R12 cap
            last = float(tail.close.iloc[-1]) if len(tail) else entry
            out = float(side * (last - entry) / STOP_PTS)
            ex_px, ex_ts = last, (tail.ts.iloc[-1] if len(tail) else w.ts.iloc[t])

        pre = g[g.mins < OPEN_MIN]
        h1 = float(pre.close.iloc[-1] - pre.close.iloc[-120]) if len(pre) > 120 else np.nan
        prev_hi = float(pre.high.max()) if len(pre) else np.nan
        prev_lo = float(pre.low.min()) if len(pre) else np.nan
        rows.append({**rec, "taken": "y",
                     "time": f"{w.ts.iloc[t]:%H:%M}",
                     "direction": "long" if side > 0 else "short",
                     "entry": round(entry, 2), "stop": round(stop, 2),
                     "target": round(target, 2), "exit": round(float(ex_px), 2),
                     "exit_time": f"{ex_ts:%H:%M}", "risk_pts": STOP_PTS,
                     "R": round(out, 3),
                     "outcome": "win" if out >= 2 else ("BE" if out == 0 else
                                ("loss" if out <= -1 else "timeout")),
                     "be_moved": be, "manip_pts": round(manip_pts, 2),
                     "manip_idx": m, "dist_idx": c_i, "entry_idx": t,
                     "dow": pd.Timestamp(day).day_name()[:3],
                     "entry_min_into_window": int(w.mins.iloc[t] - OPEN_MIN),
                     "atr_pct": float(atr_pct.get(day, np.nan)),
                     "htf_aligned": (int((h1 > 0) == (side > 0)) if h1 == h1 else np.nan),
                     "dist_to_level_R": (round(min(abs(entry - prev_hi),
                                                   abs(entry - prev_lo)) / STOP_PTS, 3)
                                         if prev_hi == prev_hi else np.nan),
                     "risk_pts_v": STOP_PTS,
                     "direction_long": int(side > 0)})
    return pd.DataFrame(rows)


def add_flow(d: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """Same definitions as ash-unicorn-sb. COMPUTED, NEVER APPLIED in this pass."""
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")
    fp.index = pd.to_datetime(fp.index)
    fp = fp[["vol", "delta"]].sort_index()
    lo, hi = fp.index.min(), fp.index.max()
    by_day = {k: g.reset_index(drop=True) for k, g in bars.groupby("day", sort=False)}
    f1, f2, cov = [], [], []
    for r in d.itertuples():
        if getattr(r, "taken", "n") != "y" or r.manip_idx != r.manip_idx:
            f1.append(np.nan); f2.append(np.nan); cov.append(0); continue
        g = by_day[r.date]
        w = g[(g.mins >= OPEN_MIN) & (g.mins <= WIN_END)].reset_index(drop=True)
        t0, t1 = w.ts.iloc[int(r.manip_idx)], w.ts.iloc[int(r.dist_idx)]
        te = w.ts.iloc[int(r.entry_idx)]
        if not (lo <= t0 <= hi and lo <= te <= hi):
            f1.append(np.nan); f2.append(np.nan); cov.append(0); continue
        side = 1 if r.direction == "long" else -1
        disp = fp[(fp.index >= t0) & (fp.index <= t1)]       # displacement = distribution leg
        ret = fp[(fp.index > t1) & (fp.index <= te)]         # retracement = leg into the fill
        sess = fp[(fp.index >= w.ts.iloc[0]) & (fp.index <= te)].vol
        assert not len(disp) or disp.index.max() <= te
        assert not len(ret) or ret.index.max() <= te
        med = float(sess.median()) if len(sess) else np.nan
        f1.append(float(disp.delta.sum()) * side / med if (len(disp) and med) else np.nan)
        dv, rv = float(disp.vol.sum()), float(ret.vol.sum())
        f2.append(rv / dv if dv > 0 and len(ret) else np.nan)
        cov.append(1)
    d = d.copy()
    d["F1_disp_delta"] = np.round(f1, 3)
    d["F2_retrace_ratio"] = np.round(f2, 3)
    d["flow_covered"] = cov
    return d


def main() -> None:
    bars = load_bars()
    d = add_flow(run(bars, calendar()), bars)
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "zxck-10am-keyopen-raw-trades.csv"
    d.to_csv(p, index=False)

    print("RAW BASELINE — zxck-10am-keyopen. Exactly as carded, no filters.\n")
    print(f"instrument NQ 1-min   range {bars.day.min()} -> {bars.day.max()}"
          f"   sessions {bars.day.nunique()}")
    print(f"window 10:00-10:15 ET   manipulation floor {MANIP_PTS:.0f}pt (FIXED)"
          f"   stop {STOP_PTS:.0f}pt   target 2R = {2*STOP_PTS:.0f}pt\n")

    print("GATE FUNNEL — every qualifying event logged, taken or not")
    print(f"  sessions evaluated              {len(d)}")
    for reason, n in d[d.taken == "n"].skip_reason.value_counts().items():
        print(f"    - {reason:<32} {n}")
    t = d[d.taken == "y"]
    print(f"  TRADES TAKEN                    {len(t)}\n")
    if not len(t):
        print("no trades"); return

    eq = t.R.cumsum()
    cost = float((COST_USD / (t.risk_pts * PT)).mean())
    print("=" * 66)
    print(f"  n {len(t)}   win {int((t.R>=2).sum())}  loss {int((t.R<=-1).sum())}  "
          f"BE {int((t.R==0).sum())}  timeout {int(((t.R>-1)&(t.R<2)&(t.R!=0)).sum())}")
    print(f"  win rate     {100*(t.R>=2).mean():.1f}%")
    print(f"  avg R        {t.R.mean():+.3f}")
    print(f"  cost         {cost:.3f}R/trade  ({STOP_PTS:.0f}pt stop)")
    print(f"  expectancy   {t.R.mean()-cost:+.3f}R net")
    print(f"  total        {t.R.sum():+.1f}R gross / {t.R.sum()-cost*len(t):+.1f}R net")
    print(f"  max drawdown {float((eq.cummax()-eq).max()):.1f}R")
    print(f"  direction    {int((t.direction=='long').sum())} long / "
          f"{int((t.direction=='short').sum())} short")
    print("=" * 66)
    t2 = t.assign(era=np.where(t.date < "2026-01-01", "2025", "2026"))
    print("\nera split:")
    print(t2.groupby("era").R.agg(n="size", win_rate=lambda x: (x >= 2).mean(),
                                 avg_R="mean", total="sum").to_string())
    print(f"\nmanip size: median {t.manip_pts.median():.1f}pt  "
          f"min {t.manip_pts.min():.1f}  max {t.manip_pts.max():.1f}")
    print(f"entry minute into window: median {t.entry_min_into_window.median():.0f}  "
          f"max {t.entry_min_into_window.max():.0f}")
    print(f"\nFLOW COVERAGE  {int(t.flow_covered.sum())}/{len(t)} trades "
          f"(flow span 2025-06-01 -> 2026-07-19). NOT applied — computed only.")
    print(f"\ntrades -> {p.relative_to(ROOT)}  ({len(d)} rows, {len(t)} taken)")


if __name__ == "__main__":
    main()
