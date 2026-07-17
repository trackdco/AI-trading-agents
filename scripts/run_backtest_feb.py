#!/usr/bin/env python3
"""Spec 1 Step 7/8 runner: backtest Feb 2-27 2026 with defaults W1/E1/V0.

Uses output/triggers_feb.csv when it is FRESHER than src/engine/triggers.py (the detector
is expensive); otherwise re-detects per day in the 07:45-11:00 morning band. Then replays
the whole month through src/backtest/engine.simulate and writes output/trades.csv,
output/verdicts.csv, output/equity.csv.

    python scripts/run_backtest_feb.py
"""
import ast
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.backtest.engine import load_backtest_config, simulate, write_outputs  # noqa: E402
from src.engine.triggers import Trigger, detect_triggers  # noqa: E402

NY = "America/New_York"
CSV = Path("output/triggers_feb.csv")
DETECTOR = Path("src/engine/triggers.py")


def load_or_detect(df: pd.DataFrame) -> list[Trigger]:
    if CSV.exists() and CSV.stat().st_mtime > DETECTOR.stat().st_mtime:
        print(f"using cached {CSV} (fresher than detector)")
        rows = pd.read_csv(CSV)
        recs = rows.to_dict("records")
        for r in recs:                       # CSV stores list columns as their repr; parse back
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
        return [Trigger(**r) for r in recs]
    print("detecting triggers per day (07:45-11:00 band) — this takes a while...")
    out: list[Trigger] = []
    for d in pd.date_range("2026-02-02", "2026-02-27", freq="D"):
        if d.weekday() >= 5:
            continue
        start = pd.Timestamp(f"{d:%Y-%m-%d} 07:45", tz=NY)
        end = pd.Timestamp(f"{d:%Y-%m-%d} 11:00", tz=NY)
        if df[(df["ts_event"] >= start) & (df["ts_event"] <= end)].empty:
            continue
        trigs = detect_triggers(df, start=start, end=end)
        out.extend(trigs)
        print(f"  {d:%Y-%m-%d}: {len(trigs)} triggers", flush=True)
    pd.DataFrame([t.model_dump() for t in out]).to_csv(CSV, index=False)
    return out


def main():
    # full dataset when present; else the committed Feb slice (data/reference/ is tracked so
    # Angus's chat can run calibration reruns without re-pulling Databento)
    full, ref = Path("data/nq_1m.parquet"), Path("data/reference/nq_1m_feb2026.parquet")
    src = full if full.exists() else ref
    print(f"data: {src}")
    df = pd.read_parquet(src)
    feb = df[(df["ts_event"] >= pd.Timestamp("2026-02-01 18:00", tz=NY)) &
             (df["ts_event"] <= pd.Timestamp("2026-02-27 17:00", tz=NY))].reset_index(drop=True)
    triggers = load_or_detect(feb)
    print(f"{len(triggers)} triggers considered")

    cfg = load_backtest_config()
    print(f"config: window {cfg.win_start}-{cfg.win_end}, entry {cfg.entry_variant}, "
          f"mgmt {cfg.mgmt_variant}")
    trades, verdicts, equity = simulate(feb, triggers, cfg)
    write_outputs(trades, verdicts, equity)

    from collections import Counter
    st = Counter(v.status for v in verdicts)
    wins = sum(1 for t in trades if t.r_multiple > 0)
    total_r = sum(t.r_multiple for t in trades)
    total_d = sum(t.dollars for t in trades)
    print(f"\n=== Feb 2-27 backtest (W1/{cfg.entry_variant}/{cfg.mgmt_variant}) ===")
    print(f"trades: {len(trades)}  wins: {wins}  losses: {sum(1 for t in trades if t.r_multiple < 0)}")
    print(f"total R: {total_r:+.2f}   total $ (1 NQ, net comm): {total_d:+,.0f}")
    print("verdicts:", dict(st.most_common()))
    print("\nper-day trades:")
    by_day = Counter(t.trade_date for t in trades)
    for d in sorted(by_day):
        day_r = sum(t.r_multiple for t in trades if t.trade_date == d)
        print(f"  {d}: {by_day[d]} trades  {day_r:+.2f}R")
    print("\nwrote output/trades.csv, output/verdicts.csv, output/equity.csv")

    # Step 9 diagnostics + Step 8 calibration report from this same run (spec-1 artifacts)
    from src.backtest.calibrate import main as calibrate_main  # noqa: E402
    from src.backtest.diagnostics import main as diagnostics_main  # noqa: E402
    print()
    diagnostics_main()
    calibrate_main()


if __name__ == "__main__":
    main()
