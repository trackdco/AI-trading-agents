#!/usr/bin/env python3
"""HOW HAS THE HIGHER TIMEFRAME TREATED THIS LEVEL SO FAR THIS SESSION?

    python -m scripts.htf_level_behavior 2026-06-23 03:40 \
        --level weekly_val=29693.61 --level vwap=29764.06
    python -m scripts.htf_level_behavior 2026-06-23 03:40 --level poc=29821 --json

Produced for the trigger briefing (`tv-trigger` 0.4.2 / T46). His ruling:

    "The higher time frame will also matter, because if the 2-minute can close
    below it but the 5-minute can't, that could just look like a massive bottom
    wick... The 2-minute candles are closing above and below that, but if we look
    at the higher time frame, like a 15-minute, it was just a big wick, and it
    couldn't close through."

So a 2m close through a level that reclaims is NOT a failed level if the 15m
shows a wick that could not close through — that shape is his HIGHEST conviction
rejection, and a stack reading only the 2m grades it C and passes his best
setups of the day.

**Why this is a script and not something the orchestrator works out.** It is the
input to a grade, so it must be identical every run, on every day, computed the
same way — and under the separation of powers (runbook §0c) the orchestrator
supplies mechanical facts, never judgements. An ad-hoc count is a judgement
wearing a number's clothes.

CAUSALITY, which is the whole game here: only candles whose CLOSE time is at or
before the decision minute are counted. A 15m candle that opened at 03:30 is not
complete at 03:40 and its close is not knowable — including it would leak the
future into the exact field the agent grades conviction from. The last completed
candle per timeframe is printed so the truncation can be checked by eye.
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

TFS = (2, 3, 5, 15)      # 2m/3m for contrast; 5m/15m are what T46 turns on


def _session_bounds(sess_day: str, minute: str):
    t0 = pd.Timestamp(f"{sess_day} 18:00", tz=NY)
    t = pd.Timestamp(f"{sess_day} {minute}", tz=NY)
    if t < t0:                       # 00:00-17:59 belongs to the NEXT calendar
        t += pd.Timedelta(days=1)    # date within this 18:00-anchored day
    if not (t0 <= t < t0 + pd.Timedelta(hours=23)):
        raise SystemExit(f"{minute} is outside session-day {sess_day}")
    return t0, t


def behavior_at(bars: pd.DataFrame, sess_day: str, minute: str,
                level: float, tfs=TFS, window_min: int = 60) -> dict:
    """Per timeframe, how price is treating `level` right now — and today.

    TWO WINDOWS, because they answer two different questions and conflating
    them makes both useless:

    - **the recent window** (default 60 min) is the CURRENT TEST. This is what
      grades the T46 shape: slowed, wicked, turned. Measured over the whole
      session it degenerates — price traverses hundreds of points in 9 hours,
      so every level reads "closed both sides" and nothing is distinguishable.
    - **the session** answers a different and also-real question: has this
      level already been sliced today? That is conviction rubric point 4 — "a
      level price already sliced earlier in the session" grades lower.

    Excursion stats are measured ONLY over candles that actually reached the
    level. A candle sitting entirely above it has not wicked past it; counting
    its high as a "wick above" measures distance, not rejection.
    """
    t0, t = _session_bounds(sess_day, minute)
    w0 = max(t0, t - pd.Timedelta(minutes=window_min))
    seg = bars[(bars.index >= t0) & (bars.index < t)]
    if seg.empty:
        raise SystemExit(f"no bars between {t0:%Y-%m-%d %H:%M} and {t:%H:%M}")

    out = {"level": float(level), "decision_minute": f"{t:%Y-%m-%d %H:%M}",
           "session_open": f"{t0:%Y-%m-%d %H:%M}",
           "window_from": f"{w0:%H:%M}", "window_min": window_min, "by_tf": {}}

    for tf in tfs:
        # label="right" => the index IS the candle's close time, so "complete
        # at the decision minute" is exactly index <= t. closed="left" matches
        # agent_context's convention throughout the repo.
        f = seg.resample(f"{tf}min", label="right", closed="left").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last"}).dropna()
        f = f[f.index <= t]
        if f.empty:
            out["by_tf"][f"{tf}m"] = {"candles": 0,
                                      "verdict": "no completed candles"}
            continue

        win = f[f.index > w0]
        if win.empty:                      # tf coarser than the window
            win = f.tail(1)

        reached = win[(win.low <= level) & (win.high >= level)]
        n_above = int((win.close > level).sum())
        n_below = int((win.close < level).sum())

        # Wick vs body, over TESTS ONLY — the shape his ruling turns on.
        if len(reached):
            wick_up = float((reached.high - level).max())
            wick_dn = float((level - reached.low).max())
            body_up = float((reached[["open", "close"]].max(axis=1) - level)
                            .clip(lower=0).max())
            body_dn = float((level - reached[["open", "close"]].min(axis=1))
                            .clip(lower=0).max())
        else:
            wick_up = wick_dn = body_up = body_dn = 0.0

        # Which side did price come from? The first completed candle in the
        # window settles it; ties fall back to the window's midpoint.
        first = win.iloc[0]
        if first.close != level:
            approach = "below" if first.close < level else "above"
        else:
            approach = "below" if (win.high.max() + win.low.min()) / 2 < level \
                else "above"

        out["by_tf"][f"{tf}m"] = {
            "candles": int(len(win)),
            "approach": approach,
            "last_complete": f"{f.index[-1]:%H:%M}",
            "tests": int(len(reached)),
            "closes_above": n_above,
            "closes_below": n_below,
            "max_wick_above": round(wick_up, 2),
            "max_body_above": round(body_up, 2),
            "max_wick_below": round(wick_dn, 2),
            "max_body_below": round(body_dn, 2),
            # session-wide: has the level already been sliced today?
            "session_closes_above": int((f.close > level).sum()),
            "session_closes_below": int((f.close < level).sum()),
            "verdict": _verdict(len(reached), n_above, n_below, wick_up,
                                wick_dn, body_up, body_dn, approach),
        }
    return out


def _verdict(tests: int, n_above: int, n_below: int, wick_up: float,
             wick_dn: float, body_up: float, body_dn: float,
             approach: str) -> str:
    """The T46 question in one phrase: did it close through, or only wick?

    `approach` is the side price came from, and it is what makes the counts
    mean anything. For a level at the top of the window's range every candle
    closes below it — that is not "closed through downward", it is "never got
    above it". Only movement AGAINST the approach side is a break.
    """
    if tests == 0:
        side = "above" if n_above else "below"
        return f"not tested in window (price {side} it throughout)"

    # Through = the far side from where price came. Body, not wick: a wick
    # beyond that closes back is the rejection, not the break.
    if approach == "below":
        through_body, through_n, far = body_up, n_above, "above"
        wick_far = wick_up
    else:
        through_body, through_n, far = body_dn, n_below, "below"
        wick_far = wick_dn

    if through_body <= 0:
        if wick_far > 0:
            return (f"HELD — {tests} test(s) from {approach}, wicked "
                    f"{wick_far:.1f}pt {far}, body never through")
        return (f"HELD — {tests} test(s) from {approach}, never traded "
                f"{far} it")
    if n_above and n_below:
        return (f"closed BOTH sides ({n_above} up / {n_below} down), "
                f"approached from {approach}")
    return (f"closed through {far} ({through_n}), body {through_body:.1f}pt "
            f"beyond")


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sess_day", help="session-day, 18:00 NY anchor")
    p.add_argument("minute", help="decision minute NY, HH:MM")
    p.add_argument("--level", action="append", required=True, metavar="NAME=PRICE",
                   help="a candidate rejection level; repeatable")
    p.add_argument("--json", action="store_true",
                   help="emit JSON for the briefing instead of a table")
    p.add_argument("--window-min", type=int, default=60,
                   help="minutes of recent tape that count as the CURRENT "
                        "test (default 60). The session-wide slice counts are "
                        "reported separately and are not affected.")
    a = p.parse_args()

    levels = []
    for spec in a.level:
        name, _, px = spec.partition("=")
        if not px:
            raise SystemExit(f"--level wants NAME=PRICE, got {spec!r}")
        levels.append((name, float(px)))

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close"]]

    results = {n: behavior_at(bars, a.sess_day, a.minute, px,
                              window_min=a.window_min)
               for n, px in levels}

    if a.json:
        print(json.dumps({n: r["by_tf"] for n, r in results.items()}, indent=2))
        return 0

    first = next(iter(results.values()))
    print(f"\nHTF LEVEL BEHAVIOUR — session-day {a.sess_day}, "
          f"as of {first['decision_minute']}")
    print(f"  current test = last {a.window_min} min "
          f"(from {first['window_from']}); only candles CLOSING at or before "
          f"the decision minute")
    for name, px in levels:
        r = results[name]
        print(f"\n  {name}  @ {px:.2f}")
        print(f"    {'tf':<5}{'last':>7}{'tests':>7}{'cl^':>5}{'clv':>5}"
              f"{'wick^':>7}{'body^':>7}{'wickv':>7}{'bodyv':>7}"
              f"{'today':>9}   verdict")
        for tf in TFS:
            d = r["by_tf"][f"{tf}m"]
            if not d.get("candles"):
                print(f"    {str(tf) + 'm':<5}   {d['verdict']}")
                continue
            today = f"{d['session_closes_above']}/{d['session_closes_below']}"
            print(f"    {str(tf) + 'm':<5}{d['last_complete']:>7}"
                  f"{d['tests']:>7}{d['closes_above']:>5}{d['closes_below']:>5}"
                  f"{d['max_wick_above']:>7.1f}{d['max_body_above']:>7.1f}"
                  f"{d['max_wick_below']:>7.1f}{d['max_body_below']:>7.1f}"
                  f"{today:>9}   {d['verdict']}")

    print("\n  'today' = session-wide closes above/below — has this level "
          "already been sliced")
    print("  (conviction rubric pt 4). The verdict grades the CURRENT test "
          "only.")
    print("  T46: a 2m closing both sides while the 15m only WICKS is his "
          "highest-conviction")
    print("  rejection, not chop. Grade on the 15m.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
