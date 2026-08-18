#!/usr/bin/env python3
"""PHASE 2 (redo) — literal trade-for-trade diff against the v3.1 TradingView export.

The v1 116-trade export was never supplied; this 75-trade v3.1 export was, and it carries
what the gate actually needs: per-trade direction, entry and exit timestamps, fill prices,
exit signal and P&L. This is the diff the task asked for.

Config is read off the export's own Properties sheet, not guessed.

    python scripts/orb_parity_v31.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research.orb.engine import Config, daily_context, load_gc, run

# exactly the Properties sheet of Gold_ORB v3.1, COMEX:GC1!, 15m, 2026-03-03 -> 2026-08-18
V31 = dict(
    anchor="09:30", or_minutes=15, entry_tf=15, target_r=1.0,
    cutoff="12:00",                      # 150 min after the anchor
    flat_minutes=240, flat_from_anchor=True,     # "Force flat (min after anchor)"
    max_trades_per_day=1,
    slip_ticks=1.0, commission_usd=3.0,          # 1 tick/side, $1.50/contract/side
    risk_mode="cap", max_risk_pts=30.0,
    ratchet=True, ratchet_trigger_r=1.0, ratchet_lock_r=0.25,
    time_stop_min=90, time_stop_r=0.5,
    vwap_gate=True, skip_weekdays=(0,),
    daily_stop_r=-2.0, weekly_stop_r=-4.0, consec_loss_halt=3,
)

REASON = {"target": "XL/XS win", "stop": "XL/XS loss", "ratchet": "XL/XS loss",
          "time_stop": "scratch", "flat": "flat"}


def tv_reason(r) -> str:
    if r.signal == "scratch":
        return "time_stop"
    if r.signal == "flat":
        return "flat"
    return "target" if r.pnl > 0 else "stop"


def main() -> None:
    tv = pd.read_csv(ROOT / "output/tv_v31_trades.csv", parse_dates=["entry_ts", "exit_ts"])
    tv["cal"] = tv.entry_ts.dt.normalize().dt.tz_localize("America/New_York")
    tv["reason"] = tv.apply(tv_reason, axis=1)

    bars = load_gc(str(ROOT / "data/gc_1m.parquet"))
    ctx = daily_context(bars, 14)
    lo = pd.Timestamp("2026-03-01", tz="America/New_York").normalize()
    w = bars[bars.cal >= lo]
    print(f"TV window   {tv.entry_ts.min().date()} -> {tv.entry_ts.max().date()}  n={len(tv)}")
    print(f"our data    ends {w.cal.max().date()}")
    overlap = tv[tv.cal <= w.cal.max()]
    print(f"comparable  n={len(overlap)}  ({len(tv)-len(overlap)} TV trades past our data)\n")

    best = None
    for tf, skip_first in ((1, False), (15, False)):
        t = run(w, Config(**V31, exit_tf=tf), ctx)
        t = t[t.cal <= w.cal.max()]
        m = overlap.merge(t, on="cal", how="outer", suffixes=("_tv", "_us"), indicator=True)
        both = m[m._merge == "both"]
        agree_dir = (both["dir_tv"] == both["dir_us"]).sum()
        agree_rsn = (both.reason_tv == both.reason_us).sum()
        entry_ok = (np.abs(both.entry_px - both.entry) <= 0.55).sum()
        row = dict(exit_tf=tf, ours=len(t), tv=len(overlap),
                   matched_days=len(both), tv_only=int((m._merge == "left_only").sum()),
                   us_only=int((m._merge == "right_only").sum()),
                   dir_agree=agree_dir, reason_agree=agree_rsn, entry_within_5tk=entry_ok,
                   pnl_us=t.pnl_usd.sum(), pnl_tv=overlap.pnl.sum())
        print(f"exit walk {tf:>2}m : days matched {len(both):3d}/{len(overlap)}   "
              f"direction {agree_dir:3d}   reason {agree_rsn:3d}   entry px {entry_ok:3d}   "
              f"our ${t.pnl_usd.sum():>9,.0f} vs TV ${overlap.pnl.sum():>9,.0f}")
        if best is None or agree_rsn > best[1]:
            best = (tf, agree_rsn, t, m, both)

    tf, _, t, m, both = best
    print(f"\n{'='*100}\nBEST PARITY: exit walk {tf}m\n{'='*100}")
    pct = 100 * len(both) / len(overlap)
    print(f"day-level match      {len(both)}/{len(overlap)} = {pct:.1f}%")
    for k, col in (("direction", "dir"), ):
        print(f"{k:<20} {(both[col+'_tv']==both[col+'_us']).sum()}/{len(both)}"
              f" = {100*(both[col+'_tv']==both[col+'_us']).mean():.1f}%")
    same_t = (both.entry_ts.dt.hour*60+both.entry_ts.dt.minute == both.entry_min)
    print(f"{'entry timestamp':<20} {same_t.sum()}/{len(both)} = {100*same_t.mean():.1f}%")
    dpx = (both.entry_px - both.entry).abs()
    print(f"{'entry price':<20} median |diff| {dpx.median():.2f} pt "
          f"({(dpx<=0.55).sum()}/{len(both)} within 5 ticks)")
    print(f"{'exit reason':<20} {(both.reason_tv==both.reason_us).sum()}/{len(both)}"
          f" = {100*(both.reason_tv==both.reason_us).mean():.1f}%")
    dp = (both.pnl - both.pnl_usd)
    print(f"{'per-trade $':<20} median |diff| ${dp.abs().median():,.0f}   "
          f"within $200: {(dp.abs()<=200).sum()}/{len(both)}")

    print("\n--- exit-reason confusion (rows = TV, cols = engine) ---")
    print(pd.crosstab(both.reason_tv, both.reason_us).to_string())

    print("\n--- days TV traded and the engine did not ---")
    lo_ = m[m._merge == "left_only"]
    for r in lo_.head(12).itertuples():
        print(f"  {str(r.cal)[:10]}  TV {'long ' if r.dir_tv>0 else 'short'} "
              f"@{r.entry_px:.1f} {r.reason_tv:<10} ${r.pnl:>8,.0f}")
    print(f"  ({len(lo_)} total)")
    print("\n--- days the engine traded and TV did not ---")
    ro = m[m._merge == "right_only"]
    for r in ro.head(12).itertuples():
        print(f"  {str(r.cal)[:10]}  us {'long ' if r.dir_us>0 else 'short'} "
              f"@{r.entry:.1f} {r.reason_us:<10} ${r.pnl_usd:>8,.0f}")
    print(f"  ({len(ro)} total)")
    m.to_csv(ROOT / "output/orb_parity_v31.csv", index=False)


if __name__ == "__main__":
    main()
