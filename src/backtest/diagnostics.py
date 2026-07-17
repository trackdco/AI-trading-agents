"""Spec 1 Step 9 — per-slice expectancy diagnostics (§12.5).

Reads output/trades.csv (the Step 7/8 W1/E1/V0 run) and emits output/diagnostics.csv: for each
diagnostic DIMENSION, a per-value expectancy table so leaks are locatable —
    pattern × TF × confluence count × HTF flag × time bucket × news flag
plus roll-day and gap-day flags. Each dimension is a complete partition of the trade set, so its
rows sum back to the headline totals (verified by tests/test_diagnostics.py).

Output is LONG format — one row per (dimension, value):
    dimension, value, n_trades, wins, losses, win_rate, sum_r, avg_r, sum_dollars
avg_r is the per-trade expectancy of that slice. The full 6-way cross-tab is intentionally NOT
emitted at February's 20-trade scale (every cell would be n≈1 and read as noise); it becomes
meaningful only on the Jan→present sample and is deferred with this note (no silent cap).

    python -m src.backtest.diagnostics      # (run scripts/run_backtest_feb.py first)
"""
from __future__ import annotations

import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

from src.engine.sessions import load_news_calendar

NY = "America/New_York"
ROOT = Path(__file__).resolve().parents[2]
TRADES = ROOT / "output/trades.csv"
PARQUET = ROOT / "data/nq_1m.parquet"
OUT = ROOT / "output/diagnostics.csv"

GAP_THRESHOLD_PTS = 15.0        # diagnostic-only heuristic (NOT a rule): 09:30 open vs prior
                                # 16:00 close beyond this = "gap day". Surfaced, never traded on.

DIMENSIONS = ["pattern", "tf", "confluence", "htf_flag",
              "time_bucket", "news_day", "roll_day", "gap_day"]


def _time_bucket(t: dtime) -> str:
    """Fill-time bucket (Angus: fill time governs). 09:45–10:15 is peak AM-macro (§9)."""
    if t < dtime(9, 30):
        return "premarket"
    if t < dtime(9, 45):
        return "open_0930_0945"
    if t < dtime(10, 15):
        return "prime_0945_1015"
    if t < dtime(10, 30):
        return "mid_1015_1030"
    return "late_after_1030"


def _day_flags(dates: set) -> dict:
    """Per session-date: news_day (high-impact release), roll_day, gap_day."""
    cal = load_news_calendar()
    hi_days = set(cal[cal["impact"] == "high"]["datetime_ET"].dt.date)

    df = pd.read_parquet(PARQUET)
    df["date"] = df["ts_event"].dt.date
    roll_days = set(df[df["roll"]]["date"]) if "roll" in df.columns else set()

    flags = {}
    for d in dates:
        # gap: 09:30 cash open vs prior day's 16:00 cash close
        day = df[df["date"] == d]
        open_bar = day[day["ts_event"].dt.time == dtime(9, 30)]
        prior = df[(df["date"] < d) & (df["ts_event"].dt.time == dtime(15, 59))]
        gap = False
        if not open_bar.empty and not prior.empty:
            o = float(open_bar.iloc[0]["open"])
            pc = float(prior.iloc[-1]["close"])
            gap = abs(o - pc) > GAP_THRESHOLD_PTS
        flags[d] = {"news_day": d in hi_days, "roll_day": d in roll_days, "gap_day": gap}
    return flags


def _slice_rows(trades: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dim in DIMENSIONS:
        for val, g in trades.groupby(dim, dropna=False):
            n = len(g)
            wins = int((g["r_multiple"] > 0).sum())
            losses = int((g["r_multiple"] < 0).sum())
            rows.append({
                "dimension": dim, "value": val, "n_trades": n,
                "wins": wins, "losses": losses,
                "win_rate": round(wins / n, 4) if n else 0.0,
                "sum_r": round(float(g["r_multiple"].sum()), 4),
                "avg_r": round(float(g["r_multiple"].mean()), 4) if n else 0.0,
                "sum_dollars": round(float(g["dollars"].sum()), 2),
            })
    return pd.DataFrame(rows)


def build_diagnostics() -> pd.DataFrame:
    if not TRADES.exists():
        sys.exit(f"missing {TRADES} — run scripts/run_backtest_feb.py first")
    t = pd.read_csv(TRADES)
    if t.empty:
        return pd.DataFrame(columns=["dimension", "value", "n_trades", "wins", "losses",
                                     "win_rate", "sum_r", "avg_r", "sum_dollars"])
    t["fill_ts"] = pd.to_datetime(t["fill_ts"])
    t["time_bucket"] = t["fill_ts"].dt.time.map(_time_bucket)
    dates = set(t["trade_date"])
    t["_d"] = t["trade_date"].map(lambda s: pd.Timestamp(s).date())
    flags = _day_flags({pd.Timestamp(d).date() for d in dates})
    t["news_day"] = t["_d"].map(lambda d: flags[d]["news_day"])
    t["roll_day"] = t["_d"].map(lambda d: flags[d]["roll_day"])
    t["gap_day"] = t["_d"].map(lambda d: flags[d]["gap_day"])
    return _slice_rows(t)


def main() -> None:
    diag = build_diagnostics()
    OUT.parent.mkdir(exist_ok=True)
    diag.to_csv(OUT, index=False)
    if not diag.empty:
        tot_n = int(diag[diag["dimension"] == "pattern"]["n_trades"].sum())
        tot_r = round(float(diag[diag["dimension"] == "pattern"]["sum_r"].sum()), 2)
        print(f"{len(diag)} slice rows over {len(DIMENSIONS)} dimensions | "
              f"headline {tot_n} trades {tot_r:+.2f}R")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
