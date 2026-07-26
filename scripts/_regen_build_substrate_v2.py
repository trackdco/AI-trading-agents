#!/usr/bin/env python3
"""Build the correctly-tagged trade substrate (Angus 22 Jul). Simulates both books (E3/E4) with
the RECLASSIFIED v2 triggers (A = daily-VWAP ±2 touch reversal, B = with-trend continuation,
B2 = rejection) over the footprint-covered span, collecting EVERY trade with entry detail + the
correct A/B/B2 tag. This is the substrate the per-setup order-flow analysis runs on.

  2025 H2 (Jun-Dec, footprint): triggers_hist2326_ob_v2
  2026    (Feb-Jul):            triggers_feb_ob_v2 + triggers_marjul_ob_v2

    python -m scripts.build_substrate_v2
"""
import os
import sys
from datetime import time as dtime
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load
from src.backtest.engine import load_backtest_config, simulate
NY = "America/New_York"
# 0 = full history (ground truth). >0 caps the per-month segment to that many days of lookback
# (all management indicators are intraday/daily-anchored, so a generous cap is result-identical).
LOOKBACK_DAYS = int(os.environ.get("SUBSTRATE_LOOKBACK_DAYS", "0"))


def run(months, trig_src, df, base, sel):
    """sel: day -> chosen book ('E3'/'E4') or None (FLAT = stand down, take nothing). This is the
    AGENT SELECTION (walk_v07 book-per-day) — only the chosen book's trades are kept, so the
    substrate is the actual traded set, not every trigger."""
    cfg_e3, cfg_e4 = books(base)
    rows = []
    for m in months:
        trigs = [t for t in trig_src if t.ts[:7] == m]
        if not trigs:
            continue
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        if LOOKBACK_DAYS:
            start = pd.Timestamp(m + "-01", tz=NY) - pd.Timedelta(days=LOOKBACK_DAYS)
            seg = df[(df.ts_event >= start) & (df.ts_event <= end)].reset_index(drop=True)
        else:
            seg = df[df.ts_event <= end].reset_index(drop=True)
        for book, cfg in (("E3", cfg_e3), ("E4", cfg_e4)):
            tr, _, _ = simulate(seg, trigs, cfg)
            for r in tr:
                if sel.get(r.trade_date) != book:        # keep only the agent's chosen book that day
                    continue
                rows.append(dict(day=r.trade_date, book=book, fill=str(r.fill_ts), exit=str(r.exit_ts),
                                 direction=r.direction, entry=r.entry, stop=r.stop_initial,
                                 exit_price=r.exit_price, dollars=r.dollars, pattern=r.pattern,
                                 tf=getattr(r, "tf", "")))
    return pd.DataFrame(rows)


def main():
    base = load_backtest_config().model_copy(update={"win_start": dtime(8, 0),
                                                     "win_end": dtime(10, 15), "max_trades_per_day": 2})
    master = pd.read_parquet("data/reference/nq_1m_master.parquet")
    d25 = master[master.ts_event >= pd.Timestamp("2025-03-01", tz=NY)].reset_index(drop=True)
    d26 = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    t25 = load(["output/triggers_hist2326_ob_v2.csv"])
    t26 = load(["output/triggers_feb_ob_v2.csv", "output/triggers_marjul_ob_v2.csv"])
    # AGENT SELECTION: walk_v07 book-per-day (MOMENTUM->E4, ROTATION->E3, FLAT->stand down)
    led = pd.read_csv("output/v07/walk_v07/ledger.csv")
    sel = {d: {"MOMENTUM": "E4", "ROTATION": "E3"}.get(a) for d, a in zip(led.day, led.act)}
    M25 = [f"2025-{mm:02d}" for mm in range(6, 13)]
    M26 = [f"2026-{mm:02d}" for mm in range(2, 8)]
    print("simulating 2025 H2 (agent-selected) ...", flush=True)
    S25 = run(M25, t25, d25, base, sel)
    print(f"  2025 trades: {len(S25)}  {S25.pattern.value_counts().to_dict()}", flush=True)
    print("simulating 2026 (agent-selected) ...", flush=True)
    S26 = run(M26, t26, d26, base, sel)
    print(f"  2026 trades: {len(S26)}  {S26.pattern.value_counts().to_dict()}", flush=True)
    S = pd.concat([S25, S26], ignore_index=True)
    S["yr"] = S.day.str[:4].astype(int)
    out = os.environ.get("SUBSTRATE_OUT", "output/substrate_v2.parquet")
    S.to_parquet(out)
    print(f"\nwrote {out}  {len(S)} trades")
    print("by year x pattern:")
    print(pd.crosstab(S.yr, S.pattern))
    print(f"\nby year x book: \n{pd.crosstab(S.yr, S.book)}")
    print(f"total P&L 2025 ${S[S.yr==2025].dollars.sum():+,.0f}  2026 ${S[S.yr==2026].dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
