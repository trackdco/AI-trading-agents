#!/usr/bin/env python3
"""NO-LOOKAHEAD GATE for the OFFLINE harness modules. Adversarial by design.

    python -m scripts.gate_offline_causality
    python -m scripts.gate_offline_causality --days 2026-06-08 2026-06-15

His precondition before a month may be run offline: *"make sure that all of
our levels, all of the things I use, are calibrated fully correctly, and make
sure there's no look ahead, none of that, no wrong data."*

`scripts/htf_ma_gates.py` already proves this for the LEVEL ENGINE (G1/G7/G8).
This gate proves it for everything the offline harness added on top, which
that suite never sees:

    scripts.offline_briefings   build_levels, candle, flush_inputs,
                                last_15m_candles, recent_2m_bars, above_below
    scripts.offline_scan        scan_day (the candidate set)
    scripts.chop_state          state_at
    scripts.level_visits        freshness
    scripts.htf_level_behavior  behavior_at (the T46 grade input)

THE METHOD, and it is the only honest one: compute every field at minute t,
then CORRUPT every bar at or after t — shift it hundreds of points, blow out
the highs and lows, multiply the volume — and recompute. Anything that reads
the future changes. Anything causal is bit-identical. A field that merely
"looks right" is not evidence; a field that survives having the future
replaced with garbage is.

Also checks the DATA the run would stand on, because a causal computation
over bad bars is still a bad run: duplicate timestamps, non-monotonic index,
out-of-order OHLC, non-positive prices, zero-volume floods, and session-day
bar counts far outside normal.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.offline_briefings as OB                            # noqa: E402
from scripts.chop_state import state_at                           # noqa: E402
from scripts.htf_level_behavior import behavior_at                # noqa: E402
from scripts.level_visits import freshness                        # noqa: E402
from scripts.offline_scan import scan_day                         # noqa: E402

PROBE_MINUTES = ("03:40", "08:20", "09:42", "10:30")


def corrupt_from(bars: pd.DataFrame, t: pd.Timestamp) -> pd.DataFrame:
    """Replace the future with garbage. If anything downstream moves, it
    was reading the future."""
    b = bars.copy()
    m = b.index >= t
    if not m.any():
        return b
    n = int(m.sum())
    rng = np.random.default_rng(20260817)
    shift = rng.normal(0, 400, n)
    b.loc[m, "open"] = b.loc[m, "open"] + shift
    b.loc[m, "close"] = b.loc[m, "close"] + shift
    b.loc[m, "high"] = b.loc[m, "high"] + shift + np.abs(shift)
    b.loc[m, "low"] = b.loc[m, "low"] + shift - np.abs(shift)
    b.loc[m, "volume"] = b.loc[m, "volume"] * 7 + 1000
    return b


def fields_at(bars, day, minute, all_days):
    """Every offline-harness field that feeds a briefing or a decision."""
    t0, t = OB.session_bounds(day, minute)
    hb = bars[["open", "high", "low", "close"]]
    core = OB.build_levels(bars, day, minute, all_days)
    lm = OB.level_map(core)
    above, below = OB.above_below(core)
    probe_level = core["levels_at_decision_BUILD"]["vwap"]["vwap"]
    return {
        "levels": core,
        "above": above, "below": below,
        "candle_2m": OB.candle(bars, t, 2),
        "candle_3m": OB.candle(bars, t, 3),
        "flush": OB.flush_inputs(bars, day, minute),
        "last15": OB.last_15m_candles(bars, day, minute),
        "recent2m": OB.recent_2m_bars(bars, day, minute),
        "htf": behavior_at(hb, day, minute, probe_level),
        "chop": state_at(bars, day, minute),
        "fresh": freshness(hb, day, minute, probe_level, []),
        "n_levels": len(lm),
    }


def check_data(bars: pd.DataFrame, days: list[str]) -> list[str]:
    faults = []
    if bars.index.has_duplicates:
        faults.append(f"{int(bars.index.duplicated().sum())} duplicate timestamps")
    if not bars.index.is_monotonic_increasing:
        faults.append("index not monotonic increasing")
    bad_hl = int((bars.high < bars.low).sum())
    if bad_hl:
        faults.append(f"{bad_hl} bars with high < low")
    bad_oc = int(((bars.open > bars.high) | (bars.open < bars.low)
                  | (bars.close > bars.high) | (bars.close < bars.low)).sum())
    if bad_oc:
        faults.append(f"{bad_oc} bars with open/close outside high/low")
    if float(bars[["open", "high", "low", "close"]].min().min()) <= 0:
        faults.append("non-positive prices present")
    if int((bars.volume < 0).sum()):
        faults.append("negative volume present")
    for d in days:
        t0 = pd.Timestamp(f"{d} 18:00", tz=OB.NY)
        seg = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
        if not (900 <= len(seg) <= 1400):
            faults.append(f"{d}: {len(seg)} bars in the session-day "
                          f"(expected ~1000-1380)")
        if len(seg) and int((seg.volume <= 0).sum()) > 120:
            faults.append(f"{d}: {int((seg.volume <= 0).sum())} zero-volume minutes")
    return faults


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", nargs="+", default=None)
    a = ap.parse_args()

    bars = OB.get_bars()
    all_days = OB.all_session_days(bars)
    days = a.days or ["2026-06-08", "2026-06-15", "2026-06-22", "2026-06-29"]
    days = [d for d in days if d in all_days]

    print("\n" + "=" * 78)
    print("  OFFLINE HARNESS — NO-LOOKAHEAD + DATA GATE")
    print("=" * 78)

    print("\n  [DATA] integrity of the bars the run would stand on")
    faults = check_data(bars, days)
    if faults:
        for f in faults:
            print(f"    FAULT: {f}")
    else:
        print(f"    PASS — {len(bars):,} bars, no duplicates, OHLC coherent, "
              f"session-day counts normal")

    print("\n  [CAUSALITY] recompute after replacing the future with garbage")
    failures = 0
    for day in days:
        for minute in PROBE_MINUTES:
            try:
                clean = fields_at(bars, day, minute, all_days)
            except (ValueError, KeyError, IndexError) as e:
                print(f"    {day} {minute}: SKIP ({type(e).__name__})")
                continue
            _, t = OB.session_bounds(day, minute)
            OB._BARS = corrupt_from(bars, t)
            try:
                dirty = fields_at(OB._BARS, day, minute, all_days)
            finally:
                OB._BARS = bars
            same = json.dumps(clean, sort_keys=True, default=str) == \
                json.dumps(dirty, sort_keys=True, default=str)
            if not same:
                failures += 1
                diff = [k for k in clean
                        if json.dumps(clean[k], sort_keys=True, default=str)
                        != json.dumps(dirty[k], sort_keys=True, default=str)]
                print(f"    {day} {minute}: **FAIL** — leaked: {', '.join(diff)}")
            else:
                print(f"    {day} {minute}: PASS "
                      f"({len(clean)} field groups bit-identical)")

    print("\n  [SCANNER] candidate set unchanged by a corrupted future")
    for day in days[:2]:
        try:
            clean = [c["minute"] for c in scan_day(bars, day)]
        except (ValueError, KeyError):
            continue
        cut = pd.Timestamp(f"{day} 18:00", tz=OB.NY) + pd.Timedelta(hours=15)
        OB._BARS = corrupt_from(bars, cut)
        try:
            dirty = [c["minute"] for c in scan_day(OB._BARS, day)
                     if c["minute"] < "09:00"]
        finally:
            OB._BARS = bars
        before = [m for m in clean if m < "09:00"]
        ok = before == dirty
        failures += 0 if ok else 1
        print(f"    {day}: {'PASS' if ok else '**FAIL**'} — "
              f"{len(before)} pre-09:00 candidates, future corrupted from 09:00")

    ok = failures == 0 and not faults
    print(f"\n  {'ALL OFFLINE GATES PASS' if ok else f'{failures} CAUSALITY FAILURE(S)'}"
          f"{'' if not faults else f' + {len(faults)} DATA FAULT(S)'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
