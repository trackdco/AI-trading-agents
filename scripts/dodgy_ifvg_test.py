#!/usr/bin/env python3
"""Does the iFVG trigger work on NQ, and do his two headline rules add anything?

Tests the DodgysDD model's core, not its decoration. Three questions, in the order
that decides whether the later ones are worth asking:

  1. the trigger alone — a fair value gap that price CLOSES through, entered at that
     close. If this is not positive there is nothing to filter.
  2. the liquidity sweep — he states it as required: "we always want the market to
     sweep some sort of higher low". Tested as a gate, on and off.
  3. the breakeven rule — "once you hit that first target stop ALWAYS goes to break
     even". This is the most-repeated mechanic in the whole channel (1,958 mentions
     across 472 transcripts, more than "fair value gap" itself), and it is a rule
     variant rather than a filter, which makes it the interesting one.

The repo has already found this family of exit rule to be a trap once. BR-46/48: fixed
targets bought 15-16pp of hit rate and sold 80-100% of expectancy — a dual-currency
inversion. A breakeven rule does the same thing in miniature, converting losses into
scratches and winners into scratches, so it MUST be read in both currencies or it will
look like an improvement while costing money.

Definitions, stated because the corpus does not fix them:
  FVG        three-candle gap: candle1.high < candle3.low (bullish) or the mirror.
  inversion  a later candle CLOSES beyond the far edge of that gap.
  entry      the close of the inverting candle, filled at the next open.
  stop       the opposite extreme of the FVG, plus one tick.
  target 1   the nearest prior swing in the trade's direction ("internal liquidity").
  final      2R, a stand-in for "hold to the draw" which he never quantifies.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.tomtrades import autopsy as AU

NY = "America/New_York"
TICK = 0.25
COST_PTS = 0.5          # NQ round turn, the incumbent census's assumption
PIVOT_K = 3
MAX_HOLD = 240


def load_nq() -> pd.DataFrame:
    parts = [pd.read_parquet(ROOT / f).drop(columns=["roll"], errors="ignore")
             for f in ("data/reference/nq_1m_master.parquet",
                       "data/reference/nq_1m_feb_jul2026.parquet")]
    b = (pd.concat(parts, ignore_index=True).drop_duplicates("ts_event")
           .sort_values("ts_event").reset_index(drop=True))
    b["mi"] = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    # volume is carried for vwap_bands/profile_at_minutes in the context test;
    # the trigger itself never reads it
    return b.set_index("mi")[["open", "high", "low", "close", "volume"]]


def signals(bars: pd.DataFrame, require_sweep: bool) -> pd.DataFrame:
    """Every iFVG inversion, with the swing context needed for stops and targets."""
    o, h, l_, c = (bars[x].to_numpy() for x in ("open", "high", "low", "close"))
    idx = bars.index
    n = len(bars)

    # confirmed swings, placed at the bar they become knowable (i+K)
    last_hi = np.full(n, np.nan)
    last_lo = np.full(n, np.nan)
    ch = cl = np.nan
    for i in range(PIVOT_K, n - PIVOT_K):
        w = slice(i - PIVOT_K, i + PIVOT_K + 1)
        if h[i] >= h[w].max():
            ch = h[i]
        if l_[i] <= l_[w].min():
            cl = l_[i]
        last_hi[i + PIVOT_K] = ch
        last_lo[i + PIVOT_K] = cl

    sday = (idx - pd.Timedelta(hours=18)).date
    rows = []
    for i in range(PIVOT_K + 3, n - 1):
        # bullish FVG across (i-3, i-2, i-1): gap between high[i-3] and low[i-1]
        for d, lo_edge, hi_edge in (
                (1, h[i - 3], l_[i - 1]),      # bullish gap -> inversion DOWN = short
                (-1, h[i - 1], l_[i - 3])):    # bearish gap -> inversion UP  = long
            if not (lo_edge < hi_edge):
                continue
            # inversion: close beyond the FAR edge, against the gap's own direction
            if d > 0 and not c[i] < lo_edge:
                continue
            if d < 0 and not c[i] > hi_edge:
                continue
            direction = -d                      # trade the way the inversion broke
            stop = (hi_edge + TICK) if direction < 0 else (lo_edge - TICK)
            entry_ref = c[i]
            risk = abs(stop - entry_ref)
            if risk < 2.0:                      # BR-29: sub-2pt stops are not a risk unit
                continue
            if require_sweep:
                # "we always want the market to sweep some sort of higher low"
                sw = (not np.isnan(last_lo[i]) and l_[i - 3:i + 1].min() < last_lo[i]) \
                    if direction > 0 else \
                    (not np.isnan(last_hi[i]) and h[i - 3:i + 1].max() > last_hi[i])
                if not sw:
                    continue
            t1 = last_hi[i] if direction > 0 else last_lo[i]
            if np.isnan(t1) or (direction > 0 and t1 <= entry_ref) or \
               (direction < 0 and t1 >= entry_ref):
                t1 = entry_ref + direction * risk      # fall back to 1R
            rows.append({"i": i, "ts": idx[i], "sess_day": sday[i], "direction": direction,
                         "stop": stop, "risk": risk, "t1": t1})
    return pd.DataFrame(rows)


def simulate(bars: pd.DataFrame, sig: pd.DataFrame, be_at_t1: bool) -> pd.DataFrame:
    o, h, l_, c = (bars[x].to_numpy() for x in ("open", "high", "low", "close"))
    n = len(bars)
    out = []
    for r in sig.itertuples(index=False):
        i0 = int(r.i) + 1
        if i0 >= n:
            continue
        entry = o[i0]
        d = int(r.direction)
        stop, risk = float(r.stop), abs(o[i0] - float(r.stop))
        if risk < 2.0:
            continue
        final = entry + d * 2.0 * risk
        live_stop, hit_t1 = stop, False
        px, why = np.nan, "timeout"
        for j in range(i0, min(i0 + MAX_HOLD, n)):
            if (h[j] >= live_stop) if d < 0 else (l_[j] <= live_stop):
                px, why = live_stop, ("be" if live_stop != stop else "stop")
                break
            if (l_[j] <= final) if d < 0 else (h[j] >= final):
                px, why = final, "target"
                break
            if not hit_t1 and ((l_[j] <= r.t1) if d < 0 else (h[j] >= r.t1)):
                hit_t1 = True
                if be_at_t1:
                    live_stop = entry           # armed for SUBSEQUENT bars only
        else:
            j = min(i0 + MAX_HOLD, n) - 1
            px = c[j]
        out.append({"i": int(r.i), "sess_day": r.sess_day, "direction": d, "risk": risk,
                    "out": d * (px - entry) / risk - COST_PTS / risk,
                    "reason": why, "hit_t1": int(hit_t1)})
    t = pd.DataFrame(out)
    if not t.empty:
        t["win"] = (t["out"] > 0).astype(float)
    return t


def report(t: pd.DataFrame, label: str) -> dict:
    if len(t) < 30:
        return {"variant": label, "n": len(t)}
    lo, hi = AU.dboot_mean(t, "out")
    days = np.array(sorted(t.sess_day.unique()))
    mid = days[len(days) // 2]
    h1, h2 = t[t.sess_day < mid], t[t.sess_day >= mid]
    return {"variant": label, "n": len(t), "per_day": len(t) / t.sess_day.nunique(),
            "win_pct": 100 * t["win"].mean(), "ev": t["out"].mean(),
            "lo": lo, "hi": hi, "h1": h1["out"].mean(), "h2": h2["out"].mean(),
            "both": bool(AU.dboot_mean(h1, "out")[0] > 0 and AU.dboot_mean(h2, "out")[0] > 0),
            "scratch_pct": 100 * (t.reason == "be").mean()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.parse_args()
    bars = load_nq()
    print(f"NQ {len(bars):,} bars  {bars.index.min().date()} -> {bars.index.max().date()}",
          flush=True)

    rows = []
    for sweep in (False, True):
        sig = signals(bars, require_sweep=sweep)
        tag = "sweep required" if sweep else "trigger only"
        print(f"  {tag}: {len(sig):,} signals", flush=True)
        for be in (False, True):
            t = simulate(bars, sig, be_at_t1=be)
            rows.append(report(t, f"{tag} · {'BE at T1' if be else 'no BE'}"))
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    print("\n=== iFVG on NQ, cost 0.5pt, day-clustered ===")
    print(out.round(3).to_string(index=False), flush=True)
    out.to_csv(ROOT / "output/dodgy_ifvg_test.csv", index=False)


if __name__ == "__main__":
    main()
