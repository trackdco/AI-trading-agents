#!/usr/bin/env python3
"""LONDON day-of-week character — what Monday and Friday actually do differently.

THE ASK (Brake, 2026-07-30): "is there something price action does differently on
monday and friday?" (the stack's best days: Mon 73%/+0.880, Fri 75%/+0.847).

Three separable explanations, each measured on ALL fit session days (not just traded
days — using traded days only would bake the outcome into the cause):
  MARKET    per-day window stats from the 1m bars, by weekday: window range,
            efficiency (|net move| / path length — low = chop, the fade-friendly
            regime), open dislocation (window open vs prior session's window close —
            Monday carries the weekend), volume.
  BOOK      what the strategy TAKES by weekday: candidates/day, wall-pass rate,
            trade composition (B2 share, both-wall share, A+ share, conv score,
            stop size, room).
  RESIDUAL  if market and composition look the same but outcomes differ, the Mon/Fri
            edge is unexplained at this n — i.e. plausibly noise.

DESCRIPTIVE THROUGHOUT — 15-30 trades and ~55 sessions per weekday cell; nothing here
is charged, nothing becomes a rule. FIT ONLY, sealed untouched.

    python -m scripts.london_dow_character
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import write
from scripts.london_conviction import CUT_MIN, lonmins
from scripts.london_holdout_report import load_pop
from scripts.london_tf_conviction import serial_walk
from scripts.london_veto_scan import build_book

LON = "Europe/London"
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri"]


def day_stats() -> pd.DataFrame:
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    t = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(LON)
    bars = bars.assign(lday=t.dt.date.astype(str), lmin=t.dt.hour * 60 + t.dt.minute)
    P = load_pop("fit")
    fit_days = sorted(set(P.day.astype(str).str[:10]))
    w = bars[(bars.lmin >= 480) & (bars.lmin < CUT_MIN) & bars.lday.isin(fit_days)]
    rows = []
    prev_close = {}
    for day, g in w.groupby("lday"):
        g = g.sort_values("lmin")
        path = g.close.diff().abs().sum()
        rows.append({
            "day": day, "dow": pd.Timestamp(day).day_name()[:3],
            "range": float(g.high.max() - g.low.min()),
            "eff": float(abs(g.close.iloc[-1] - g.open.iloc[0]) / path) if path else np.nan,
            "vol": float(g.volume.sum()),
            "open": float(g.open.iloc[0]), "close": float(g.close.iloc[-1]),
        })
    D = pd.DataFrame(rows).sort_values("day").reset_index(drop=True)
    D["disloc"] = (D.open - D.close.shift(1)).abs()
    D.loc[0, "disloc"] = np.nan
    return D


def main() -> None:
    D = day_stats()
    base = build_book()
    b = serial_walk(base[base.conv > 0]).reset_index(drop=True)
    b["dow"] = pd.to_datetime(b.day).dt.day_name().str[:3]
    b["aplus"] = ((b.pattern == "B2") & (b.W == 1) & (b.FAR == 1)).values
    b["both"] = ((b.W == 1) & (b.FAR == 1)).values
    P = load_pop("fit")
    P["mins"] = lonmins(P.fill)
    Pc = P[(P.mins < CUT_MIN) & (P.risk >= 9.5)].copy()
    Pc["dow"] = pd.to_datetime(Pc.day).dt.day_name().str[:3]

    L = ["# What Mondays and Fridays do differently — market vs book vs residual\n",
         "\n**FIT ONLY. Descriptive — nothing charged, nothing becomes a rule. All "
         "fit session days (~284), not just traded days.**\n"]

    L.append("\n## 1. MARKET — the window itself, by weekday (all sessions)\n\n"
             "| day | sessions | median range (pt) | median efficiency | median "
             "dislocation vs prior close (pt) | median volume |\n"
             "|---|---|---|---|---|---|\n")
    for d in DOW:
        g = D[D.dow == d]
        L.append(f"| {d} | {len(g)} | {g['range'].median():.0f} | "
                 f"{g.eff.median():.3f} | {g.disloc.median():.1f} | "
                 f"{g.vol.median():,.0f} |\n")
    L.append("\n(Efficiency = |net move| / path length over 08:00-09:30. Low = choppy "
             "mean-reversion tape — the regime a fade strategy wants. Dislocation = "
             "|window open - prior session window close|; Monday carries the "
             "weekend.)\n")

    L.append("\n## 2. BOOK — what the strategy finds and takes, by weekday\n\n"
             "| day | candidates/session | wall-pass rate | trades (stack) | B2 share "
             "| both-wall share | A+ share | mean conv | median stop (pt) |\n"
             "|---|---|---|---|---|---|---|---|---|\n")
    for d in DOW:
        pc = Pc[Pc.dow == d]
        g = b[b.dow == d]
        sess = D[D.dow == d].day.nunique()
        L.append(f"| {d} | {len(pc) / max(sess, 1):.1f} | "
                 f"{pc.wall.mean() * 100:.0f}% | {len(g)} | "
                 f"{g.b2.mean() * 100:.0f}% | {g.both.mean() * 100:.0f}% | "
                 f"{g.aplus.mean() * 100:.0f}% | {g.conv.mean():.2f} | "
                 f"{(g.risk / 20).median():.1f} |\n")

    L.append("\n## 3. RESIDUAL — outcomes on comparable trades\n\n"
             "| day | trades | WR | mean R | A+ trades WR/R | non-A+ WR/R |\n"
             "|---|---|---|---|---|---|\n")
    for d in DOW:
        g = b[b.dow == d]
        ga, gn = g[g.aplus], g[~g.aplus]
        fa = (f"{(ga.R > 0).mean() * 100:.0f}%/{ga.R.mean():+.2f}" if len(ga) else "—")
        fn = (f"{(gn.R > 0).mean() * 100:.0f}%/{gn.R.mean():+.2f}" if len(gn) else "—")
        L.append(f"| {d} | {len(g)} | {(g.R > 0).mean() * 100:.0f}% | "
                 f"{g.R.mean():+.3f} | {fa} | {fn} |\n")
    write("LONDON-DOW-CHARACTER.md", "".join(L))


if __name__ == "__main__":
    main()
