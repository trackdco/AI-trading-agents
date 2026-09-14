#!/usr/bin/env python3
"""BRIEFING EXTRAS — NWOG, swept extremes, defended levels (T67/T68, cat-3 gaps).

    python -m scripts.context_extras 2026-06-25 09:42
    python -m scripts.context_extras 2026-06-25 09:42 --json

Three objects HIS reasoning uses that no briefing carried, each named in the
wk1 comparison as a category-3 gap and each mechanically computable:

  nwog             "a ~400pt NWOG from last week's open is unfilled and he
                   expects it to fill" — a whole day's destination logic.
                   Both edges are reported raw (prior Friday 17:00 close,
                   Sunday 18:00 open); his convention decides which matters.
  swept lows/highs "we've taken out that low... massive wick" as the licence
                   to act. Absent from every agent account of the week.
  defended levels  the T67 licence's first condition: a level with MEMORY —
                   a prior session's defended extreme or a multi-day floor —
                   stated with its tests and closes-beyond so "tested and
                   FAILED to break" is a readable fact, not a judgement.

Causality: everything is computed from bars strictly before the decision
minute, same convention as agent_context.context_at.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

SWING_W = 5          # bars each side for a 2m swing extreme
NEAR_PTS = 120.0     # defended levels reported only within reach of price
MEMORY_TOL = 6.0     # pts: prior-session extremes this close = one level


def _bounds(sess_day: str, minute: str):
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t = pd.Timestamp(f"{sess_day} {minute}", tz=NY)
    if t < t0:
        t += pd.Timedelta(days=1)
    return t0, t


def nwog(bars: pd.DataFrame, sess_day: str, minute: str) -> dict:
    """Prior Friday 17:00 close and this week's Sunday 18:00 open, plus fill state."""
    t0, t = _bounds(sess_day, minute)
    # this week's Sunday 18:00 anchor: walk back from session open to Sunday
    anchor = t0
    while anchor.weekday() != 6:                       # 6 = Sunday
        anchor -= pd.Timedelta(days=1)
    pre = bars[bars.index < anchor]
    post = bars[(bars.index >= anchor) & (bars.index < t)]
    if pre.empty or post.empty:
        return {"available": False}
    fri_close = float(pre.close.iloc[-1])
    week_open = float(post.open.iloc[0])
    lo, hi = sorted((fri_close, week_open))
    seg = bars[(bars.index >= anchor) & (bars.index < t)]
    touched_lo = bool((seg.low <= lo).any())
    touched_hi = bool((seg.high >= hi).any())
    return {"available": True,
            "prior_friday_close": round(fri_close, 2),
            "week_open": round(week_open, 2),
            "gap_pts": round(week_open - fri_close, 2),
            "filled": bool(touched_lo and touched_hi),
            "edges_touched_since_open": {"lower": touched_lo, "upper": touched_hi}}


def swept(bars: pd.DataFrame, sess_day: str, minute: str) -> dict:
    """Swing extremes taken out THIS session, with reclaim state.

    Swings may have been SET in a prior session OR earlier in this one — his
    Friday licence ran off "this low from Asia" (set after 18:00 the same
    session-day) being dumped through at the open and reclaimed immediately.
    A swing only exists once its confirming bar has closed (SWING_W bars
    later), and only sweeps AFTER that confirmation, inside this session,
    count — so nothing here peeks forward.
    """
    t0, t = _bounds(sess_day, minute)
    hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30)) & (bars.index < t)]
    two = hist.resample("2min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    # drop the final PARTIAL bucket: with 1m bars truncated strictly before t, a
    # right-labeled bucket > t is a 2m bar that had not closed at the decision
    # minute - presenting it as closed is the unclosed-bar defect the candidate
    # clusterer already fixed, and it surfaced here as swept_at 08:04 in an
    # 08:03 briefing (caught by a trigger agent on 2026-05-31 P1).
    two = two[two.index <= t]
    out = {"lows": [], "highs": []}
    if len(two) < 2 * SWING_W + 2:
        return out
    lows, highs, idx = two.low.to_numpy(), two.high.to_numpy(), two.index
    for i in range(SWING_W, len(two) - SWING_W):
        confirmed = idx[i + SWING_W]           # swing exists only after this bar
        if lows[i] == lows[i - SWING_W:i + SWING_W + 1].min():
            lvl = float(lows[i])
            ses = two[(two.index > max(confirmed, t0))]
            hit = ses[ses.low < lvl]
            if len(hit):
                first = hit.index[0]
                after = ses[ses.index >= first]
                out["lows"].append({"level": round(lvl, 2),
                                    "set": f"{idx[i]:%a %H:%M}",
                                    "swept_at": f"{first:%H:%M}",
                                    "closed_beyond": bool((after.close < lvl).any()),
                                    "reclaimed": bool((after.close > lvl).any())})
        if highs[i] == highs[i - SWING_W:i + SWING_W + 1].max():
            lvl = float(highs[i])
            ses = two[(two.index > max(confirmed, t0))]
            hit = ses[ses.high > lvl]
            if len(hit):
                first = hit.index[0]
                after = ses[ses.index >= first]
                out["highs"].append({"level": round(lvl, 2),
                                     "set": f"{idx[i]:%a %H:%M}",
                                     "swept_at": f"{first:%H:%M}",
                                     "closed_beyond": bool((after.close > lvl).any()),
                                     "reclaimed": bool((after.close < lvl).any())})
    # dedup near-identical levels, keep the nearest few; a wall of sweeps is noise
    px = float(two.close.iloc[-1])
    for k in out:
        seen, kept = [], []
        for s in sorted(out[k], key=lambda d: abs(d["level"] - px)):
            if any(abs(s["level"] - x) <= MEMORY_TOL for x in seen):
                continue
            seen.append(s["level"]); kept.append(s)
        out[k] = kept[:4]
    return out


def defended(bars: pd.DataFrame, sess_day: str, minute: str, days_back: int = 4) -> dict:
    """Prior-session extremes with MEMORY, near price, with this session's tests."""
    t0, t = _bounds(sess_day, minute)
    ses = bars[(bars.index >= t0) & (bars.index < t)]
    if ses.empty:
        return {"floors": [], "ceilings": []}
    two = ses.resample("2min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    two = two[two.index <= t]          # same partial-bucket rule as swept()
    px = float(ses.close.iloc[-1])
    days = []
    for d in range(1, days_back + 1):
        a = t0 - pd.Timedelta(days=d)
        seg = bars[(bars.index >= a) & (bars.index < a + pd.Timedelta(hours=23))]
        if len(seg):
            # label by the CASH day (anchor+1), the day he'd name it by
            days.append((f"{a + pd.Timedelta(days=1):%a}",
                         float(seg.low.min()), float(seg.high.max())))
    out = {"floors": [], "ceilings": []}
    used_f, used_c = [], []
    for name, lo, hi in days:
        if abs(lo - px) <= NEAR_PTS and not any(abs(lo - u) <= MEMORY_TOL for u in used_f):
            sessions = [n for n, l, _ in days if abs(l - lo) <= MEMORY_TOL]
            tests = two[(two.low <= lo + MEMORY_TOL) & (two.low >= lo - NEAR_PTS)]
            out["floors"].append({
                "level": round(lo, 2), "defended_by": sessions,
                "memory": len(sessions),
                "tests_this_session": int(len(tests)),
                "closes_below": int((two.close < lo).sum()),
                "held": bool((two.close < lo).sum() == 0 and len(tests) > 0)})
            used_f.append(lo)
        if abs(hi - px) <= NEAR_PTS and not any(abs(hi - u) <= MEMORY_TOL for u in used_c):
            sessions = [n for n, _, h in days if abs(h - hi) <= MEMORY_TOL]
            tests = two[(two.high >= hi - MEMORY_TOL) & (two.high <= hi + NEAR_PTS)]
            out["ceilings"].append({
                "level": round(hi, 2), "defended_by": sessions,
                "memory": len(sessions),
                "tests_this_session": int(len(tests)),
                "closes_above": int((two.close > hi).sum()),
                "held": bool((two.close > hi).sum() == 0 and len(tests) > 0)})
            used_c.append(hi)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sess_day")
    ap.add_argument("minute")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close"]]

    res = {"nwog": nwog(bars, a.sess_day, a.minute),
           "swept": swept(bars, a.sess_day, a.minute),
           "defended_levels": defended(bars, a.sess_day, a.minute)}
    if a.json:
        print(json.dumps(res, indent=1))
        return 0
    print(f"\nCONTEXT EXTRAS — {a.sess_day} as of {a.minute} NY")
    n = res["nwog"]
    if n.get("available"):
        print(f"  NWOG  Fri close {n['prior_friday_close']}  week open "
              f"{n['week_open']}  gap {n['gap_pts']:+.2f}  "
              f"filled={n['filled']}")
    for side in ("lows", "highs"):
        for s in res["swept"][side]:
            print(f"  SWEPT {side[:-1]} {s['level']} (set {s['set']}) at "
                  f"{s['swept_at']}  closed_beyond={s['closed_beyond']} "
                  f"reclaimed={s['reclaimed']}")
    for kind in ("floors", "ceilings"):
        for f in res["defended_levels"][kind]:
            print(f"  DEFENDED {kind[:-1]} {f['level']}  memory={f['memory']} "
                  f"({'/'.join(f['defended_by'])})  tests={f['tests_this_session']} "
                  f"closes_beyond={f.get('closes_below', f.get('closes_above'))} "
                  f"held={f['held']}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
