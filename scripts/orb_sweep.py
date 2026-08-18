#!/usr/bin/env python3
"""PHASE 3 — measurement sweeps on TRAIN ONLY (2023-01-02 -> 2025-08-31).

One variable at a time off the v1-exact baseline, per D5. Every cell is reported in R
(leading) and points (alongside) per skill rule 1, at 1-tick AND 2-tick per-side slippage
per skill rule 4, with a per-year breakdown so a cell that lives in one regime is visible.

The holdout (2025-09-01 onward) is not read by this script.

    python scripts/orb_sweep.py
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
RNG = np.random.default_rng(20260818)


def boot(r: np.ndarray, n: int = 2000) -> tuple[float, float]:
    """Plain bootstrap. With max_trades_per_day=1 a trade IS a day, so day-clustering
    (BR-42) and the plain resample coincide — stated so the shortcut is visible."""
    if len(r) < 20:
        return (np.nan, np.nan)
    m = RNG.choice(r, size=(n, len(r)), replace=True).mean(axis=1)
    return (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def cell(t: pd.DataFrame, label: str, group: str) -> dict:
    if t is None or t.empty:
        return {"group": group, "config": label, "n": 0}
    r = t.r.to_numpy()
    w, l_ = t[t.r > 0], t[t.r <= 0]
    gl = -l_.pnl_usd.sum()
    lo, hi = boot(r)
    yrs = t.groupby(t.cal.dt.year).r.mean()
    return {"group": group, "config": label, "n": len(t),
            "per_day": np.nan, "win_pct": 100 * len(w) / len(t),
            "ev_r": r.mean(), "lo": lo, "hi": hi,
            "tot_r": r.sum(), "ev_pts": t.pnl_pts.mean(), "usd": t.pnl_usd.sum(),
            "pf": (w.pnl_usd.sum() / gl) if gl > 0 else np.inf,
            "med_risk": t.risk_pts.median(),
            "y2023": yrs.get(2023, np.nan), "y2024": yrs.get(2024, np.nan),
            "y2025": yrs.get(2025, np.nan),
            "tgt%": 100 * (t.reason == "target").mean(),
            "flat%": 100 * (t.reason == "flat").mean()}


def main() -> None:
    bars = load_gc(str(ROOT / "data/gc_1m.parquet"))
    ctx = daily_context(bars, 14)
    lo, hi = (pd.Timestamp(x, tz="America/New_York").normalize() for x in TRAIN)
    w = bars[(bars.cal >= lo) & (bars.cal <= hi)]
    print(f"TRAIN {TRAIN[0]} -> {TRAIN[1]}   {w.cal.nunique()} calendar days with bars")
    print("HOLDOUT 2025-09-01 -> 2026-08-11 is NOT read by this script\n")

    V1 = dict(cutoff="12:00")          # v1-exact + the calibrated 12:00 entry cutoff
    grid: list[tuple[str, str, dict]] = [
        ("baseline",   "v1-exact (09:30 · 1.5R)",        {}),
        ("anchor",     "anchor 08:20",                   dict(anchor="08:20")),
        ("anchor",     "anchor 03:00 (London)",          dict(anchor="03:00")),
        ("target",     "target 1.00R",                   dict(target_r=1.0)),
        ("target",     "target 1.25R",                   dict(target_r=1.25)),
        ("risk cap",   "cap 25pt",                       dict(risk_mode="cap", max_risk_pts=25)),
        ("risk cap",   "cap 30pt",                       dict(risk_mode="cap", max_risk_pts=30)),
        ("risk cap",   "cap 40pt",                       dict(risk_mode="cap", max_risk_pts=40)),
        ("risk cap",   "skip >25pt",                     dict(risk_mode="skip", max_risk_pts=25)),
        ("risk cap",   "skip >30pt",                     dict(risk_mode="skip", max_risk_pts=30)),
        ("risk cap",   "skip >40pt",                     dict(risk_mode="skip", max_risk_pts=40)),
        ("ratchet",    "ratchet 1.0R -> +0.25R",         dict(ratchet=True)),
        ("time stop",  "time stop 90min @0.5R",          dict(time_stop_min=90, time_stop_r=0.5)),
        ("time stop",  "time stop 60min @0.5R",          dict(time_stop_min=60, time_stop_r=0.5)),
        ("time stop",  "time stop 120min @0.5R",         dict(time_stop_min=120, time_stop_r=0.5)),
        ("time stop",  "time stop 90min @0.3R",          dict(time_stop_min=90, time_stop_r=0.3)),
        ("gate",       "session VWAP gate",              dict(vwap_gate=True)),
        ("gate",       "prior-day-close gate",           dict(pdc_gate=True)),
        ("gate",       "skip Monday",                    dict(skip_weekdays=(0,))),
        ("breaker",    "3-consec-loss halt (wk reset)",  dict(consec_loss_halt=3)),
        ("breaker",    "weekly -4R breaker",             dict(weekly_stop_r=-4.0)),
    ]

    rows = []
    for slip in (1.0, 2.0):
        for group, label, kw in grid:
            t = run(w, Config(**V1, slip_ticks=slip, **kw), ctx)
            c = cell(t, label, group)
            c["slip_ticks"] = slip
            c["per_day"] = c["n"] / w.cal.nunique() if c["n"] else 0
            rows.append(c)
        print(f"  slip {slip:g} tick done", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "output/orb_sweep_train.csv", index=False)
    pd.set_option("display.width", 260)
    cols = ["group", "config", "n", "win_pct", "ev_r", "lo", "hi", "ev_pts", "usd",
            "pf", "med_risk", "y2023", "y2024", "y2025", "tgt%", "flat%"]
    for slip in (1.0, 2.0):
        print(f"\n{'='*118}\n=== TRAIN sweep · {slip:g} tick per side "
              f"(${slip*10:.0f} round turn) · R leads, points alongside\n{'='*118}")
        print(out[out.slip_ticks == slip][cols].round(3).to_string(index=False))
    print(f"\nwrote output/orb_sweep_train.csv")


if __name__ == "__main__":
    main()
