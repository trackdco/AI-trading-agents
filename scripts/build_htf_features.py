#!/usr/bin/env python3
"""HTF bias features — the three variables that are not geometry.

Rules extracted in research/findings/htf-bias-rules-extracted.md.
Motivation in research/findings/the-geometry-frontier.md.

THE PROBLEM THESE EXIST TO SOLVE. A 33-variable scan of the limit book found 1 of 93 buckets
above zero mean R, and that one was +0.003. The reason is structural: every variable we record
is a proxy for how far the target sits from the stop, so `corr(win rate, average win size) =
-0.855` and filters slide the same trade along a fixed frontier instead of lifting it off.
Escaping needs information that is NOT a restatement of where the levels are.

ANGUS: *"the big problem with raw data is its every trigger, and that includes shorting when a
trigger fires on heavy bullish days, and longing when a trigger fires on heavy bearish days."*

  pd_position       where the trigger sits inside the PRIOR DAY's range, 0 = prior low,
                    1 = prior high. A statement about location in the auction.
  vs_midnight_open  trigger price against the 00:00 ET open, signed to trade direction.
                    Positive = the trade is FADING the day's move so far; negative = chasing.
                    JadeCap's power-of-three delineation, and he is explicit that midnight is
                    the reference: "I always use midnight as my delineation."
  already_moved     has the prior day's high (for a long) or low (for a short) ALREADY been
                    taken today, before this trigger? This is the one worth betting on -- the
                    only variable in the project that encodes whether the day's expected move
                    has been SPENT. "If I have a bullish bias and we're trading above the
                    previous day's high at 9:00 a.m., that is not a good sign to go long."

CAUSALITY. Every field uses only bars STRICTLY BEFORE the trigger bar's close, plus completed
prior sessions. The trigger bar itself contributes its close (the order is placed after that
bar closes) and nothing later. No fill-time information anywhere -- that defect has cost this
project two separate false findings already.

SESSION BOUNDARY. The "day" for prior-day high/low is the RTH session (09:30-16:00 ET), not
the CME 18:00 boundary, because the levels being referenced are the ones traders watch. The
midnight open is 00:00 ET on the calendar date of the trigger.

    python -m scripts.build_htf_features [--book output/l2_outcomes_fit.parquet]
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
RTH = (9 * 60 + 30, 16 * 60)
BARS = ("data/reference/nq_1m_master.parquet", "data/reference/nq_1m_feb_jul2026.parquet")
OUT = ROOT / "output/htf_features.parquet"


def load_bars() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(ROOT / p).drop(columns=["roll"], errors="ignore")
                   for p in BARS], ignore_index=True)
    b = b.drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True)
    t = pd.to_datetime(b.ts_event, utc=True).dt.tz_convert(NY)
    b["mi"] = t.dt.floor("min")
    b["day"] = t.dt.strftime("%Y-%m-%d")
    b["hm"] = t.dt.hour * 60 + t.dt.minute
    return b


def build(trig: pd.DataFrame) -> pd.DataFrame:
    """trig needs columns: ts (trigger time), day, direction. Returns one row per ts."""
    b = load_bars()
    rth = b[(b.hm >= RTH[0]) & (b.hm < RTH[1])]

    # prior RTH session high/low, by calendar day of the session that PRECEDES each day
    sess = rth.groupby("day").agg(hi=("high", "max"), lo=("low", "min"))
    days = sorted(sess.index)
    prev = {d: days[i - 1] for i, d in enumerate(days) if i}
    prev_hi = {d: float(sess.hi[prev[d]]) for d in prev}
    prev_lo = {d: float(sess.lo[prev[d]]) for d in prev}

    # midnight open: first bar at or after 00:00 ET on the trigger's calendar day
    mid = b[b.hm == 0].groupby("day").open.first().to_dict()

    # running intraday extremes BEFORE each minute, within the calendar day (from 00:00 ET,
    # so the overnight counts -- a prior-day high taken at 04:00 has still been taken)
    b = b.sort_values("mi").reset_index(drop=True)
    b["run_hi"] = b.groupby("day").high.cummax().shift(1)
    b["run_lo"] = b.groupby("day").low.cummin().shift(1)
    # shift(1) crosses the day boundary; repair the first bar of each day
    first = b.groupby("day").head(1).index
    b.loc[first, ["run_hi", "run_lo"]] = np.nan
    prior = b.set_index("mi")[["close", "run_hi", "run_lo"]]

    T = trig.copy()
    T["mi"] = pd.to_datetime(T.ts, utc=True, format="mixed").dt.tz_convert(NY).dt.floor("min")
    T = T.join(prior, on="mi")
    T["dir"] = np.where(T.direction.astype(str).str.lower().str.startswith(("l", "b")), 1, -1)
    T["prev_hi"] = T.day.map(prev_hi)
    T["prev_lo"] = T.day.map(prev_lo)
    T["mid_open"] = T.day.map(mid)

    rng = (T.prev_hi - T.prev_lo).replace(0, np.nan)
    T["pd_position"] = (T.close - T.prev_lo) / rng
    # signed so that POSITIVE always means "the trade is on the correct side of the auction"
    # under the premium/discount rule: a short in premium, a long in discount.
    T["pd_edge"] = np.where(T["dir"] == 1, 0.5 - T.pd_position, T.pd_position - 0.5)

    # positive = trade fades the day's move from the midnight open (short above / long below)
    T["vs_midnight_open"] = (T.mid_open - T.close) * T["dir"] * -1
    T["vs_mid_norm"] = T.vs_midnight_open / rng
    T["fades_open"] = T.vs_midnight_open > 0

    # has the level this trade is heading toward already been taken today, before now?
    took_hi = T.run_hi > T.prev_hi
    took_lo = T.run_lo < T.prev_lo
    T["already_moved"] = np.where(T["dir"] == 1, took_hi, took_lo)
    T["opposite_taken"] = np.where(T["dir"] == 1, took_lo, took_hi)   # the manipulation leg
    T["both_taken"] = took_hi & took_lo

    keep = ["ts", "pd_position", "pd_edge", "vs_midnight_open", "vs_mid_norm", "fades_open",
            "already_moved", "opposite_taken", "both_taken", "prev_hi", "prev_lo", "mid_open"]
    return T[keep]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default="output/l2_outcomes_fit.parquet")
    a = ap.parse_args()
    O = pd.read_parquet(ROOT / a.book)
    F = build(O[["ts", "day", "direction"]].drop_duplicates("ts"))
    F.to_parquet(OUT, index=False)
    n = len(F)
    print(f"wrote {OUT.relative_to(ROOT)} — {n:,} triggers")
    print(f"  pd_position       median {F.pd_position.median():.3f}  "
          f"[{F.pd_position.quantile(.1):.2f}, {F.pd_position.quantile(.9):.2f}]")
    print(f"  fades_open        {F.fades_open.mean():.1%} of triggers fade the midnight open")
    print(f"  already_moved     {F.already_moved.mean():.1%} fire AFTER their target-side "
          f"prior-day level was already taken")
    print(f"  opposite_taken    {F.opposite_taken.mean():.1%} fire after the OPPOSITE side "
          f"was taken (the manipulation leg)")
    print(f"  both_taken        {F.both_taken.mean():.1%}")
    print(f"  nulls: pd {F.pd_position.isna().mean():.1%}  "
          f"mid {F.mid_open.isna().mean():.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
