#!/usr/bin/env python3
"""RESEARCH ONLY (claude/agent-exit-london-r1). L2 V9 grid — one pass, 5 new cells.

Declared BEFORE running (Stage 1, S1.2 of the agent-exit-london plan):
  v9_arm_r     in {4.5, 6.0}            (default 6.0)
  v9_lock_frac in {0.4, 0.5, 0.7}       (default 0.5)
  v9_floor_r   fixed at engine default 3.0 (NOT swept — keeps the grid small; a
               declared limitation, not an oversight)
  v9_max_risk_pts fixed at engine default None (NOT swept)
6 cells total; (6.0, 0.5) is the default cell already built by the standard
`build_l2_outcomes_london --mgmt V9` run and is EXCLUDED here to avoid recomputing it.

NO REIMPLEMENTATION: reuses window_et, load_backtest_config, simulate, Trigger from the
frozen modules exactly as scripts/build_l2_outcomes_london.py does — this file adds a
per-cell v9_arm_r/v9_lock_frac override to l2_cfg and nothing else. One bar-segment load
per day serves all 5 cells (amortizes the load; simulate() cost itself is irreducible
per cell, since a different management config walks a genuinely different exit path).

FIT SPAN ONLY. Holdout guard: src/research/holdout_guard.py is applied to every bar
load in this file.

    python -m scripts.research.build_l2_v9_grid --procs 3
"""
from __future__ import annotations

import argparse
import sys
from datetime import time as dtime
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import scripts.build_l0_triggers_london as L0M  # noqa: E402
from scripts.build_l0_triggers_london import window_et  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402
from src.engine.triggers import Trigger  # noqa: E402
from src.research.holdout_guard import assert_fit_only  # noqa: E402

NY = "America/New_York"
LOOKBACK_DAYS = 7
MASTER = "data/reference/nq_1m_master.parquet"

CELLS = [(4.5, 0.4), (4.5, 0.5), (4.5, 0.7), (6.0, 0.4), (6.0, 0.7)]  # (6.0,0.5) excluded

_BARS: pd.DataFrame | None = None


def l2_cfg(day: str, arm_r: float, lock_frac: float):
    start, end = window_et(day)
    return load_backtest_config().model_copy(update={
        "win_start": dtime(start.hour, start.minute),
        "win_end": dtime(end.hour, end.minute),
        "max_trades_per_day": 99,
        "min_stop_points": 0.0, "post_open_min_stop": 0.0, "max_stop_points": None,
        "no_trade_start": None, "no_trade_end": None, "t_cancel": 100000.0,
        "mgmt_variant": "V9",
        "v9_arm_r": arm_r, "v9_lock_frac": lock_frac,
        "v8_be_at_open": False})


def load_bars() -> pd.DataFrame:
    df = (pd.read_parquet(ROOT / MASTER).drop(columns=["roll"], errors="ignore")
          .sort_values("ts_event").reset_index(drop=True))
    assert_fit_only(df, "ts_event", str(MASTER))
    return df


def day_outcomes(args) -> list[dict]:
    day, recs, lookback = args
    global _BARS
    if _BARS is None:
        _BARS = load_bars()
    seg = _BARS[(_BARS.ts_event >= pd.Timestamp(f"{day} 00:00", tz=NY)
                 - pd.Timedelta(days=lookback))
                & (_BARS.ts_event <= pd.Timestamp(f"{day} 16:10", tz=NY))].reset_index(drop=True)
    _, win_end = window_et(day)
    out = []
    for arm_r, lock_frac in CELLS:
        cfg = l2_cfg(day, arm_r, lock_frac)
        for rec in recs:
            t = Trigger(**{k: v for k, v in rec.items() if k in Trigger.model_fields})
            trades, verdicts, _ = simulate(seg, [t], cfg)
            row = {"day": day, "ts": t.ts, "tf": t.tf, "direction": t.direction,
                   "arm_r": arm_r, "lock_frac": lock_frac}
            if trades:
                r = trades[0]
                risk = round(abs(float(r.limit_price) - float(r.stop_initial)), 4)
                row |= {"status": "outcome", "fill_ts": str(r.fill_ts),
                        "entry": float(r.entry), "stop": float(r.stop_initial),
                        "risk": risk, "exit_ts": str(r.exit_ts),
                        "exit_price": float(r.exit_price),
                        "exit_reason": str(r.exit_reason),
                        "R": float(r.r_multiple), "size_engine": float(r.size),
                        "dollars_1lot": float(r.dollars)}
            else:
                v = verdicts[0] if verdicts else None
                row |= {"status": v.status if v else "no_verdict", "fill_ts": "",
                       "R": float("nan")}
            out.append(row)
    return out


def run(trigs: pd.DataFrame, procs: int, lookback: int = LOOKBACK_DAYS) -> pd.DataFrame:
    ts = pd.to_datetime(trigs.ts, format="mixed", utc=True).dt.tz_convert(NY)
    trigs = trigs.assign(day=ts.dt.strftime("%Y-%m-%d"))
    jobs = [(day, g.drop(columns=["day"]).to_dict("records"), lookback)
            for day, g in trigs.groupby("day", sort=True)]
    rows = []
    with Pool(procs) as p:
        for i, day_rows in enumerate(p.imap(day_outcomes, jobs)):
            rows.extend(day_rows)
            if day_rows and i % 20 == 0:
                print(f"  {day_rows[0]['day']}: {len(day_rows)} rows "
                      f"({len(CELLS)} cells x triggers)", flush=True)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=3)
    a = ap.parse_args()
    L0M.WINDOW = ("08:00", "10:00")     # census window; rev-3 09:45 cut applied downstream
    trigs = pd.read_parquet(ROOT / "output/l0_triggers_london_fit.parquet")
    F = run(trigs, procs=a.procs)
    out = ROOT / "output/research/l2_outcomes_london_fit_v9grid.parquet"
    out.parent.mkdir(exist_ok=True)
    F.to_parquet(out, index=False)
    oc = F[F.status == "outcome"]
    print(f"\nwrote {out.relative_to(ROOT)} — {len(F)} rows, {len(oc)} outcomes "
          f"across {len(CELLS)} cells: {CELLS}")


if __name__ == "__main__":
    main()
