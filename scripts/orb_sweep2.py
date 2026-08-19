#!/usr/bin/env python3
"""PHASE 3B — four single-axis sweeps on TRAIN ONLY (2023-01-02 -> 2025-08-31).

Bare ORB baseline re-run inside every axis so each cell is compared against the same
control. Costs are per side and include $3/round-turn commission (the value read off the
v3.1 export, which earlier runs omitted). Every cell reported, not just winners.

The holdout — 2025-09-01 onward — is not read by this script.

    python scripts/orb_sweep2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.orb.engine import Config, daily_context, load_gc, run

TRAIN = ("2023-01-02", "2025-08-31")
RNG = np.random.default_rng(20260819)


def boot(r: np.ndarray, n: int = 4000) -> tuple[float, float]:
    if len(r) < 20:
        return (np.nan, np.nan)
    m = RNG.choice(r, size=(n, len(r)), replace=True).mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def cutoff_for(anchor: str, mins: int = 150) -> str:
    h, m = (int(x) for x in anchor.split(":"))
    t = h * 60 + m + mins
    return f"{t//60:02d}:{t%60:02d}"


def bare(anchor="09:30", or_min=15, tf=15, **kw) -> dict:
    """The control: plain ORB, no cap, no gates, no management."""
    return dict(anchor=anchor, or_minutes=or_min, entry_tf=tf, target_r=1.5,
                cutoff=cutoff_for(anchor), flat_minutes=240, max_trades_per_day=1,
                commission_usd=3.0, **kw)


def cell(bars, ctx, label: str, cfg_kw: dict) -> list[dict]:
    out = []
    for slip in (1.0, 2.0):
        t = run(bars, Config(**cfg_kw, slip_ticks=slip), ctx)
        if t.empty:
            out.append({"cell": label, "slip": slip, "n": 0})
            continue
        r = t.r.to_numpy()
        lo, hi = boot(r)
        gl = -t[t.r <= 0].pnl_usd.sum()
        yr = t.groupby(t.cal.dt.year).r.mean()
        out.append({"cell": label, "slip": slip, "n": len(t),
                    "win%": 100 * (t.r > 0).mean(), "avgR": r.mean(), "lo": lo, "hi": hi,
                    "pts": t.pnl_pts.mean(), "usd": t.pnl_usd.sum(),
                    "PF": (t[t.r > 0].pnl_usd.sum() / gl) if gl > 0 else np.inf,
                    "medRisk": t.risk_pts.median(),
                    "y23": yr.get(2023, np.nan), "y24": yr.get(2024, np.nan),
                    "y25": yr.get(2025, np.nan)})
    return out


def show(rows: list[dict], title: str) -> None:
    d = pd.DataFrame(rows)
    print(f"\n{'='*126}\n{title}\n{'='*126}")
    for slip in (1.0, 2.0):
        s = d[d.slip == slip].drop(columns="slip")
        print(f"\n-- {slip:g} tick/side + $3 commission --")
        print(s.round(3).to_string(index=False))


def main() -> None:
    bars = load_gc(str(ROOT / "data/gc_1m.parquet"))
    ctx = daily_context(bars, 14)
    lo, hi = (pd.Timestamp(x, tz="America/New_York").normalize() for x in TRAIN)
    w = bars[(bars.cal >= lo) & (bars.cal <= hi)]
    print(f"TRAIN {TRAIN[0]} -> {TRAIN[1]}   {w.cal.nunique()} days")
    print("HOLDOUT 2025-09-01 -> 2026-08-11 not read.  2025-09-01 -> 2026-03-01 stays sealed.")
    print("2010-2021 unavailable: data begins 2023-01-02 and there is no Databento key.")
    all_rows = []

    # ---- A. ANCHOR ---------------------------------------------------------
    rows = []
    for a in ("09:30", "08:20", "03:00"):
        rows += cell(w, ctx, f"anchor {a}  (cutoff {cutoff_for(a)})", bare(anchor=a))
    show(rows, "A. ANCHOR — entry window held at 150 min after each anchor, so the "
               "comparison is fair")
    all_rows += [{**r, "axis": "A anchor"} for r in rows]

    # ---- B. CRABEL ---------------------------------------------------------
    rows = cell(w, ctx, "no contraction gate", bare())
    for g in ("nr4", "nr7", "inside", "idnr4"):
        rows += cell(w, ctx, f"prior day {g}", bare(crabel=g))
    show(rows, "B. CRABEL CONTRACTION — the original ORB precondition, never tested here")
    all_rows += [{**r, "axis": "B crabel"} for r in rows]

    # ---- C. PARTICIPATION --------------------------------------------------
    rows = cell(w, ctx, "no participation filter", bare())
    for k in (1.2, 1.5, 2.0):
        rows += cell(w, ctx, f"relvol >= {k} x slot-matched 14d", bare(min_relvol=k))
    for k in (0.5, 1.0, 1.5):
        rows += cell(w, ctx, f"breakout range >= {k} x ATR14(tf)", bare(min_bar_atr=k))
    show(rows, "C. PARTICIPATION — breakout-bar volume and range")
    all_rows += [{**r, "axis": "C participation"} for r in rows]

    # ---- D. OR WINDOW ------------------------------------------------------
    rows = []
    for m in (5, 15, 30, 60):
        rows += cell(w, ctx, f"OR {m}m (entry TF {m}m)", bare(or_min=m, tf=m))
    show(rows, "D. OR WINDOW — entry timeframe tracks the OR length")
    all_rows += [{**r, "axis": "D or_window"} for r in rows]

    pd.DataFrame(all_rows).to_csv(ROOT / "output/orb_sweep2_train.csv", index=False)
    print("\nwrote output/orb_sweep2_train.csv")


if __name__ == "__main__":
    pd.set_option("display.width", 260)
    main()
