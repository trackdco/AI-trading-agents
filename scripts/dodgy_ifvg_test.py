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


def signals(bars: pd.DataFrame, require_sweep: bool, max_age: int = 240,
            require_revisit: bool = True, cluster_bars: int = 15) -> pd.DataFrame:
    """Every iFVG inversion: a gap that formed EARLIER and is later closed through.

    THIS IS THE FIX. The first version tested the gap across (i-3, i-2, i-1) against
    bar i and nothing else, so every "inversion" was exactly one bar old — it measured
    "three-bar gap immediately reversed on bar four", which is not the model and is far
    noisier than it. An inversion fair value gap is a gap price LEFT, came BACK to, and
    then closed through, which can be minutes or hours later. Gaps are now carried
    forward in an active list until they invert, expire, or the session ends.

    ``require_revisit`` enforces the return leg: price must trade back INTO the gap
    before the close that breaks it. Without it a gap blown straight through by one
    continuation candle counts, and that is a momentum event, not an inversion.
    """
    o, h, l_, c = (bars[x].to_numpy() for x in ("open", "high", "low", "close"))
    idx = bars.index
    n = len(bars)

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
    active: list[dict] = []          # gaps still live: {born, kind, lo, hi, touched}
    for i in range(3, n - 1):
        if sday[i] != sday[i - 1]:
            active.clear()           # a gap does not survive the session break

        # --- age out, then test every live gap for an inversion ------------------
        still = []
        for g in active:
            if i - g["born"] > max_age:
                continue
            # revisit: price traded back into the zone on some EARLIER bar. Snapshot
            # before updating -- reading the flag after setting it from bar i made the
            # gate inert, because any candle that closes through has already spanned the
            # zone and set its own flag. See FINDINGS-dodgy-ifvg CORRECTION 2.
            was_touched = g["touched"]
            if l_[i] <= g["hi"] and h[i] >= g["lo"]:
                g["touched"] = True
            broke = (c[i] < g["lo"]) if g["kind"] == "bull" else (c[i] > g["hi"])
            if broke and (was_touched or not require_revisit):
                direction = -1 if g["kind"] == "bull" else 1
                stop = (g["hi"] + TICK) if direction < 0 else (g["lo"] - TICK)
                risk = abs(stop - c[i])
                if risk >= 2.0:
                    ok = True
                    if require_sweep:
                        ok = (not np.isnan(last_lo[i]) and l_[max(0, i - 10):i + 1].min()
                              < last_lo[i]) if direction > 0 else \
                             (not np.isnan(last_hi[i]) and h[max(0, i - 10):i + 1].max()
                              > last_hi[i])
                    if ok:
                        t1 = last_hi[i] if direction > 0 else last_lo[i]
                        # t1_synth marks the fallback: no confirmed swing survives ahead
                        # of price, so the "target" is a manufactured 1R and not a level
                        # at all. E5 rule 4 says these are no-trades; the incumbent book
                        # keeps them. Flagged rather than dropped so the published
                        # population is unchanged and downstream can decide.
                        t1_synth = bool(np.isnan(t1) or (direction > 0 and t1 <= c[i]) or
                                        (direction < 0 and t1 >= c[i]))
                        if t1_synth:
                            t1 = c[i] + direction * risk
                        rows.append({"i": i, "ts": idx[i], "sess_day": sday[i],
                                     "direction": direction, "stop": stop, "risk": risk,
                                     "t1": t1, "t1_synth": t1_synth, "age": i - g["born"]})
                continue             # gap is spent either way
            still.append(g)
        active = still

        # --- register the gap completed by bar i ---------------------------------
        if l_[i] > h[i - 2]:
            active.append({"born": i, "kind": "bull", "lo": h[i - 2], "hi": l_[i],
                           "touched": False})
        elif h[i] < l_[i - 2]:
            active.append({"born": i, "kind": "bear", "lo": h[i], "hi": l_[i - 2],
                           "touched": False})
    sig = pd.DataFrame(rows)
    if sig.empty:
        return sig
    # ONE SIGNAL PER FIGHT (BR-9/BR-10). A single momentum candle can close through
    # several stale gaps at once, so the raw list counts one move many times — that is
    # what 207 signals/day was. Keep the OLDEST gap on each bar (the most respected
    # level), then impose a cooldown so the same push cannot re-fire every few bars.
    sig = (sig.sort_values(["i", "age"], ascending=[True, False])
              .drop_duplicates(["i", "direction"], keep="first"))
    keep, last = [], {}
    for r in sig.itertuples(index=False):
        if r.i - last.get(r.direction, -10**9) >= cluster_bars:
            keep.append(r.Index if hasattr(r, "Index") else True)
            last[r.direction] = r.i
        else:
            keep.append(False)
    sig = sig[[bool(k) for k in keep]].reset_index(drop=True)
    sig["sid"] = np.arange(len(sig))
    return sig


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
        out.append({"sid": int(r.sid), "i": int(r.i), "sess_day": r.sess_day, "direction": d, "risk": risk,
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
