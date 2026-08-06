#!/usr/bin/env python3
"""FVT — JJ Simon's Fair Value Theory on NQ. A NEW model, built from a published rule set.

ANGUS 2026-08-06 linked the FX Replay backtest of this strategy. Rules taken from the
published PDF (fxreplay.com/strategies/jj-simons-fair-value-theory-nq-strategy), not from a
video summary, so every threshold below is the AUTHOR'S number and none of them is mine.

WHY THIS ONE, AND NOT THE OTHER CANDIDATE. Trader Kane's "Lab Model" from the same channel
requires SMT divergence between NQ and ES. Angus has already ruled on that -- *"nah fuck ES.
smt divergences have been proven to have no delta"* -- and we do not hold ES data. FVT needs
NQ alone.

WHY IT IS WORTH THE COMPUTE: it inverts the exact thing we proved kills our own book today.

  |               | FVT                          | our canon                                |
  |---------------|------------------------------|------------------------------------------|
  | reference     | the 09:30 OPEN PRICE, one    | VWAP bands + BB basis + POC clusters     |
  |               | fixed number for the session |                                          |
  | stop          | FIXED POINTS by ATR tier     | structural, below the candle             |
  | target        | FIXED 1.5R, no management,   | 2R floor + walkout + V8 partials, which  |
  |               | no partials                  | produced a 2.9% target-hit rate          |
  | time          | continuation first ~15m,     | none                                     |
  |               | mean reversion after         |                                          |

`research/findings/the-geometry-frontier.md` showed our variables are all proxies for target
distance, so nothing we filter escapes a fixed win-rate/win-size trade-off. A fixed-point stop
with a fixed 1.5R target is a different geometry entirely -- the target distance stops being a
function of the setup.

THE PREMISE: "If there is no new information for the market to price in, it is most likely
going to revert back to fair value." JJ uses the 09:30 open and the 14:00 price as fair value.

DECLARED INTERPRETATIONS -- the source is ambiguous in exactly two places, and both are
recorded here rather than quietly chosen:

  1. DISPLACEMENT. The PDF says counter-wick "less than 20% of the distance from the candle's
     open to counter wick h/l", which is circular as written (for a bullish candle that
     distance IS the lower wick). The defensible mechanical reading, and the one used:
     counter-wick <= 20% of the candle's FULL range.
  2. ATR PERIOD/TIMEFRAME. Unspecified. The tiers (<7, 7-20, >20) with 16.5/25/50 point stops
     imply an intraday ATR of single-to-low-double-digit points, so 1-minute and 5-minute
     ATR(14) are BOTH run as declared arms and both reported.

ERAS: 2025 discovers, 2026 validates, and the 2023/24 holdout stays sealed. Nothing here is
fitted -- every threshold is the author's -- so the era split is a robustness read, not a
selection.

    python -m scripts.fvt_model [--atr-tf 1|5] [--full-span]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
BARS = ("data/reference/nq_1m_master.parquet", "data/reference/nq_1m_feb_jul2026.parquet")
FRICTION = 2.0

# JJ's published NY windows, plus the sessions his channel says he actually trades. The FX
# Replay PDF hints at them ("Could also test first 90m after Asia & London market opens";
# "If trading Asia session, only trade it if it provides a surge in volume/volatility") and
# his video "How I Trade the 6PM & 8PM Session (Fair Price Theory on Funded Accounts)" makes
# them explicit. Fair value for each window is that window's OPENING PRICE -- the same rule
# as 09:30, applied to the session that is actually opening.
WINDOW_SETS = {
    "ny": [("AM", 9 * 60 + 30, 11 * 60), ("PM", 14 * 60, 15 * 60)],
    "evening": [("E18", 18 * 60, 19 * 60 + 30), ("E20", 20 * 60, 21 * 60 + 30)],
    "london": [("LDN", 3 * 60, 4 * 60 + 30)],
    "all": [("AM", 9 * 60 + 30, 11 * 60), ("PM", 14 * 60, 15 * 60),
            ("E18", 18 * 60, 19 * 60 + 30), ("E20", 20 * 60, 21 * 60 + 30),
            ("LDN", 3 * 60, 4 * 60 + 30)],
}
WINDOWS = WINDOW_SETS["ny"]
SKIP_FIRST_MIN = 3          # "may be best to avoid the first 3m after 9:30 market open"
CONT_MIN = 15               # continuation phase length; JJ says "the first ~10-15m"
WICK_MAX = 0.20             # displacement quality
# Bars either side of the pivot: 1 = the 3-bar fractal JJ describes ("close past wick H/L of
# recent price leg"). NOTE the semantic: this is the HALF-width, not the total. It was briefly
# 3 here after the fractal was generalised, which silently meant a 7-bar fractal and moved the
# baseline from +0.19 to -1.37 pt/trade. The sweep in the commit log shows 1 is also the best
# value, monotonically -- stricter structure is strictly worse on this model.
SWING_N = 1
RR = 1.5                    # "1.5R take profit, no trade management"
TIERS = [(20.0, 50.0), (7.0, 25.0), (0.0, 16.5)]   # (atr_above, stop_points)


def load() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in BARS], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    t = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b["day"] = t.dt.strftime("%Y-%m-%d")
    b["hm"] = t.dt.hour * 60 + t.dt.minute
    return b


def atr_series(b: pd.DataFrame, tf: int) -> pd.Series:
    """ATR(14) on `tf`-minute bars, mapped back to every 1-minute row. Strictly causal: the
    value on a 1m bar comes from the last COMPLETED tf-bar before it."""
    x = b.set_index(pd.to_datetime(b.ts_event, utc=True))
    o = x.resample(f"{tf}min", label="right", closed="right").agg(
        high=("high", "max"), low=("low", "min"), close=("close", "last")).dropna()
    pc = o.close.shift(1)
    tr = pd.concat([o.high - o.low, (o.high - pc).abs(), (o.low - pc).abs()], axis=1).max(axis=1)
    a = tr.rolling(14).mean().shift(1)          # shift: only completed bars
    return a.reindex(x.index, method="ffill").to_numpy()


def stop_for(atr: float) -> float:
    for lo, sl in TIERS:
        if atr > lo:
            return sl
    return TIERS[-1][1]


def run(b: pd.DataFrame, atr_tf: int, swing_n: int = SWING_N) -> pd.DataFrame:
    b = b.copy()
    b["atr"] = atr_series(b, atr_tf)
    rng = (b.high - b.low).to_numpy()
    up_wick = (b.high - np.maximum(b.open, b.close)).to_numpy()
    dn_wick = (np.minimum(b.open, b.close) - b.low).to_numpy()
    bull = (b.close > b.open).to_numpy()
    bear = (b.close < b.open).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        disp_up = bull & (np.where(rng > 0, dn_wick / rng, 1.0) <= WICK_MAX)
        disp_dn = bear & (np.where(rng > 0, up_wick / rng, 1.0) <= WICK_MAX)
    b["disp_up"], b["disp_dn"] = disp_up, disp_dn

    trades = []
    for day, g in b.groupby("day"):
        g = g.reset_index(drop=True)
        # Fair value for a window is THAT WINDOW'S opening price. JJ states it for 09:30 and
        # 14:00; the same rule generalises to whichever session is actually opening, which is
        # what makes the evening and London windows testable at all.
        fv_by_win = {}
        for wname, wlo, _ in WINDOWS:
            seg = g[g.hm >= wlo]
            fv_by_win[wname] = float(seg.open.iloc[0]) if len(seg) else np.nan

        hi = g.high.to_numpy(float)
        lo = g.low.to_numpy(float)
        cl = g.close.to_numpy(float)
        hm = g.hm.to_numpy()
        atr = g.atr.to_numpy(float)

        # 3-bar fractal swings, confirmed one bar late so nothing is known early
        # k bars either side of the pivot. k=1 is a 3-bar fractal, which on 1-minute NQ marks
        # a new "swing" every few bars and turns "close past the recent price leg" into "close
        # past a wiggle". Larger k means a real leg, which is what the source intends.
        k = max(1, swing_n)
        sw_hi = np.full(len(g), np.nan)
        sw_lo = np.full(len(g), np.nan)
        lh = ll = np.nan
        for i in range(len(g)):
            j = i - k                                  # pivot candidate, confirmed at i
            if j - k >= 0:
                if hi[j] == hi[j - k:j + k + 1].max() and (hi[j - k:j] < hi[j]).all():
                    lh = hi[j]
                if lo[j] == lo[j - k:j + k + 1].min() and (lo[j - k:j] > lo[j]).all():
                    ll = lo[j]
            sw_hi[i], sw_lo[i] = lh, ll

        for wname, wlo, whi in WINDOWS:
            fv = fv_by_win.get(wname, np.nan)
            if not np.isfinite(fv):
                continue
            start = wlo + (SKIP_FIRST_MIN if wname == "AM" else 0)
            idx = np.flatnonzero((hm >= start) & (hm < whi))
            if len(idx) < 5:
                continue
            open_trade = None
            for i in idx:
                if open_trade is not None:
                    e, d_, stop, tgt, t0, ph = open_trade
                    hit_s = (lo[i] <= stop) if d_ == 1 else (hi[i] >= stop)
                    hit_t = (hi[i] >= tgt) if d_ == 1 else (lo[i] <= tgt)
                    ex = None
                    if hit_s and hit_t:
                        ex, why = stop, "both->stop"      # conservative on same-bar ambiguity
                    elif hit_s:
                        ex, why = stop, "stop"
                    elif hit_t:
                        ex, why = tgt, "target"
                    if ex is not None:
                        trades.append({"day": day, "win": wname, "phase": ph, "dir": d_,
                                       "entry": e, "exit": ex, "why": why,
                                       "pts": (ex - e) * d_ - FRICTION,
                                       "risk": abs(e - stop), "hm": t0})
                        open_trade = None
                    continue

                if not np.isfinite(atr[i]):
                    continue
                phase = "cont" if hm[i] < wlo + CONT_MIN else "rev"
                above = cl[i] > fv
                d_ = 0
                # CONTINUATION phase: trade AWAY from fair value, needs a BOS in that direction
                if phase == "cont":
                    if b_up := (bool(np.isfinite(sw_hi[i])) and cl[i] > sw_hi[i] and disp_up[i]):
                        d_ = 1 if above else 0
                    if (not b_up) and np.isfinite(sw_lo[i]) and cl[i] < sw_lo[i] and disp_dn[i]:
                        d_ = -1 if not above else 0
                # REVERSION phase: trade BACK toward fair value, needs an MSB toward it
                else:
                    if above and np.isfinite(sw_lo[i]) and cl[i] < sw_lo[i] and disp_dn[i]:
                        d_ = -1
                    elif (not above) and np.isfinite(sw_hi[i]) and cl[i] > sw_hi[i] and disp_up[i]:
                        d_ = 1
                if d_ == 0:
                    continue
                sl = stop_for(float(atr[i]))
                e = cl[i]
                stop = e - d_ * sl
                tgt = e + d_ * sl * RR
                open_trade = (e, d_, stop, tgt, int(hm[i]), phase)

            if open_trade is not None:      # flat at window end
                e, d_, stop, tgt, t0, ph = open_trade
                last = idx[-1]
                trades.append({"day": day, "win": wname, "phase": ph, "dir": d_, "entry": e,
                               "exit": cl[last], "why": "window_end",
                               "pts": (cl[last] - e) * d_ - FRICTION,
                               "risk": abs(e - stop), "hm": t0})
    T = pd.DataFrame(trades)
    if not T.empty:
        T["era"] = T.day.str[:4]
        T["R"] = T.pts / T.risk
    return T


def score(T: pd.DataFrame, days: int) -> dict:
    if len(T) < 30:
        return {}
    d = T.groupby("day").pts.sum()
    return {"n": len(T), "per_day": len(T) / max(days, 1), "net": T.pts.mean(),
            "total": T.pts.sum(), "wr": (T.pts > 0).mean(),
            "green": (d > 0).mean(), "sessions": len(d),
            "sharpe": d.mean() / d.std() * np.sqrt(252) if d.std() > 0 else np.nan,
            "worst10": d.rolling(10).sum().min(), "tgt": (T.why == "target").mean()}


def row(nm: str, s: dict) -> str:
    if not s:
        return f"| {nm} | — | — | — | — | — | — | — | — |"
    return (f"| {nm} | {s['n']:,} | {s['per_day']:.2f} | **{s['net']:+.2f}** | "
            f"{s['total']:+,.0f} | {s['wr']:.1%} | {s['tgt']:.1%} | {s['green']:.0%} | "
            f"{s['sharpe']:.2f} |")


HDR = ("| book | trades | /day | net pt | total | win% | target% | green days | Sharpe |\n"
       "|---|---:|---:|---:|---:|---:|---:|---:|---:|")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full-span", action="store_true",
                    help="include the sealed 2023/24 holdout — do NOT use while iterating")
    a = ap.parse_args()
    b = load()
    if not a.full_span:
        b = b[b.day >= "2025-01-01"]

    L = ["# FVT — JJ Simon's Fair Value Theory, NQ", "",
         "Rules from the published PDF; every threshold is the author's, none is fitted here.",
         "Fair value = the 09:30 open price. Fixed-point stops by ATR tier, fixed 1.5R target,",
         "**no trade management and no partials** — the inverse of the exit regime we proved",
         "kills our own book (2.9% target-hit under a 2R floor with walkout).", "",
         f"Friction {FRICTION:g} pt/round trip. 2023/24 holdout "
         f"{'INCLUDED — this run is no longer a clean test' if a.full_span else 'SEALED'}.", ""]

    for tf in (1, 5):
        T = run(b, tf)
        if T.empty:
            L += [f"## ATR on {tf}-minute bars", "", "No trades.", ""]
            continue
        nd = b.day.nunique()
        L += [f"## ATR({tf}m) arm", "", HDR]
        L.append(row("ALL", score(T, nd)))
        for e in sorted(T.era.unique()):
            X = T[T.era == e]
            L.append(row(f"  {e}", score(X, b[b.day.str[:4] == e].day.nunique())))
        for w in ("AM", "PM"):
            L.append(row(f"  window {w}", score(T[T.win == w], nd)))
        for p in ("cont", "rev"):
            L.append(row(f"  phase {p}", score(T[T.phase == p], nd)))
        L += ["", f"exit mix: {T.why.value_counts().to_dict()}",
              f"median risk {T.risk.median():.1f} pt", ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/fvt_model.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
