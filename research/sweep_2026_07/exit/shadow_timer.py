#!/usr/bin/env python3
"""PART 4 — SHADOW-TRACKING HARNESS for the N-minute timer.

PURE PARALLEL LOGGING. This places no orders, changes no canon file, and touches nothing on the
live path. For every pre-market trade in a session it records, side by side, what the canon
actually did and what an N-minute timer WOULD have done. Append-only.

WHY IT EXISTS. The timer was found post-hoc, was rejected by the pre-registered selection, lost
in-sample and gained everything out-of-sample. It cannot be confirmed on the existing book — the
regime boundary is in the wrong place and there is only one of them. A FORWARD log is the only
mechanism that can ever settle it, because every session it records is genuinely out-of-sample
with respect to the hypothesis.

WHAT IT NEEDS PER SESSION: the day's pre-market fills (day, fill timestamp, direction, entry,
stop, micros) and 1-minute bars covering the session. Both already exist in the research book
format; for live use, point --book at the arming book.

    # backfill the whole existing book (idempotent, safe to re-run)
    python3 shadow_timer.py --backfill

    # one session, the daily call
    python3 shadow_timer.py --day 2026-07-13

    # read the accumulated evidence, including the forward-only slice
    python3 shadow_timer.py --report

APPEND-ONLY CONTRACT: one line per (day, fill, direction, risk, horizon). Re-running a day
replaces nothing — duplicates are detected on read by (key, horizon) and the FIRST occurrence
wins, so an accidental double-run cannot inflate the record.
"""
import argparse
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

REPO = "/home/user/AI-trading-agents"
OUT = f"{REPO}/research/sweep_2026_07/exit"
LOG = f"{OUT}/shadow_timer_log.jsonl"
COMM_RT, SLIP_MKT = 1.24, 0.50
HORIZONS = (30, 45, 60, 90)
CUTOVER = "2026-07-10"          # end of the book the hypothesis was formed on


def load_bars():
    b = pd.read_parquet(f"{REPO}/data/reference/nq_1m_master.parquet",
                        columns=["ts_event", "high", "low", "close"])
    b["ts"] = pd.to_datetime(b.ts_event, utc=True)
    return b.drop_duplicates("ts").set_index("ts").sort_index()


def load_book(path=None):
    p = path or f"{OUT}/part1_frame.csv"
    F = pd.read_csv(p)
    F["ft"] = pd.to_datetime(F.ft, utc=True)
    return F


def simulate(r, bars, h):
    """What the timer would have done. Returns (R, dollars, exit_reason, exit_ts)."""
    BI, BH, BL, BC = bars.index, bars.high.values, bars.low.values, bars.close.values
    d = 1 if r["direction"] == "long" else -1
    k0 = int(BI.searchsorted(pd.Timestamp(r["ft"]).floor("min"), side="right")) - 1
    if k0 < 0 or k0 >= len(BI) - 1:
        return None
    et = pd.Timestamp(r["ft"]).tz_convert("America/New_York")
    ce = et.replace(hour=15, minute=55, second=0, microsecond=0)
    kend = min(int(BI.searchsorted(ce.tz_convert("UTC"), side="right")), len(BI) - 1)
    kh = min(k0 + h, kend, len(BI) - 1)
    entry, risk = float(r["entry"]), float(r["risk_pts"])
    lo = ((BL[k0:kh + 1] - entry) if d > 0 else (entry - BH[k0:kh + 1])) / risk
    hit = np.nonzero(lo <= -1.0)[0]
    if len(hit):
        R_, why, kx = -1.0, "stop", k0 + int(hit[0])
    else:
        R_ = float(((BC[kh] - entry) if d > 0 else (entry - BC[kh])) / risk)
        why, kx = "timer", kh
    dollars = float(r["micros"]) * (R_ * risk * 2.0 - COMM_RT - SLIP_MKT)
    return R_, dollars, why, str(BI[kx])


def key_of(r):
    return f"{r['day']}|{r['ft']}|{r['direction']}|{round(float(r['risk_pts']), 4)}"


def append(rows):
    seen = set()
    if os.path.exists(LOG):
        for line in open(LOG):
            try:
                d = json.loads(line)
                seen.add((d["key"], d["horizon"]))
            except Exception:
                pass
    n = 0
    with open(LOG, "a", buffering=1) as fh:
        for row in rows:
            if (row["key"], row["horizon"]) in seen:
                continue
            fh.write(json.dumps(row, default=str) + "\n")
            seen.add((row["key"], row["horizon"]))
            n += 1
    return n


def run(days, book_path=None):
    bars, F = load_bars(), load_book(book_path)
    F["day"] = F.day.astype(str)
    sel = F[F.day.isin(days)] if days else F
    rows = []
    stamped = datetime.now(timezone.utc).isoformat()
    for _, r in sel.iterrows():
        for h in HORIZONS:
            s = simulate(r, bars, h)
            if s is None:
                continue
            R_, dollars, why, xts = s
            rows.append(dict(key=key_of(r), day=r["day"], ft=str(r["ft"]),
                             direction=r["direction"], horizon=h,
                             canon_R=float(r["R"]), canon_pl=float(r["pl"]),
                             timer_R=R_, timer_pl=dollars, exit_reason=why, timer_exit=xts,
                             delta_pl=dollars - float(r["pl"]),
                             forward_only=bool(str(r["day"]) > CUTOVER),
                             logged_at=stamped))
    n = append(rows)
    print(f"shadow log: {len(sel)} trades x {len(HORIZONS)} horizons -> {n} new records "
          f"({len(rows) - n} already present)")
    return n


def report():
    if not os.path.exists(LOG):
        print("no shadow log yet — run --backfill first")
        return
    seen, recs = set(), []
    for line in open(LOG):
        d = json.loads(line)
        k = (d["key"], d["horizon"])
        if k in seen:              # first occurrence wins
            continue
        seen.add(k)
        recs.append(d)
    L = pd.DataFrame(recs)
    print(f"SHADOW TIMER LOG — {L.key.nunique()} trades, {len(L)} records, "
          f"{L.day.min()} .. {L.day.max()}")
    print(f"\n{'horizon':9s} {'n':>5} {'canon':>11} {'timer':>11} {'delta':>11} {'stop%':>7}")
    for h, g in L.groupby("horizon"):
        print(f"{str(h)+'m':9s} {len(g):>5} {g.canon_pl.sum():>+11,.0f} "
              f"{g.timer_pl.sum():>+11,.0f} {g.delta_pl.sum():>+11,.0f} "
              f"{(g.exit_reason=='stop').mean()*100:>6.0f}%")
    fw = L[L.forward_only]
    print(f"\nFORWARD-ONLY SLICE (sessions after {CUTOVER} — the only genuinely out-of-sample")
    print(f"evidence for this hypothesis):")
    if not len(fw):
        print(f"  none yet. Every record so far is backfill over the book the hypothesis was")
        print(f"  formed on, and therefore proves nothing about it.")
    else:
        print(f"  {fw.key.nunique()} trades over {fw.day.nunique()} sessions")
        for h, g in fw.groupby("horizon"):
            print(f"    {h}m: canon ${g.canon_pl.sum():+,.0f} vs timer ${g.timer_pl.sum():+,.0f} "
                  f"= ${g.delta_pl.sum():+,.0f} on {len(g)} trades"
                  + ("   INSUFFICIENT" if len(g) < 10 else ""))
        need = 28
        print(f"\n  Registered target before this can be called: ~{need} +1R-reaching trades in "
              f"the late segment\n  (Part 3), roughly 80 further trading days at the observed rate.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backfill", action="store_true")
    ap.add_argument("--day", action="append", default=[])
    ap.add_argument("--book", default=None)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.report:
        report()
    elif a.backfill:
        run(None, a.book)
    elif a.day:
        run(set(a.day), a.book)
    else:
        ap.error("one of --backfill / --day / --report required")
