#!/usr/bin/env python3
"""LONDON trade substrate: triggers -> fills/exits, both books, DST-correct windows.

Mirrors the morning universe build: every London-window trigger is run through the
backtest engine under BOTH books (E3 = rotation/V8 mgmt, E4 = momentum entry), no book
choosing. Days are grouped by their ET window (03:00-05:00 normal / 04:00-06:00 during
UK-US DST misalignment) and simulated with matching win_start/win_end configs.

Writes output/london_substrate.parquet (one row per fill, chronological).

    python -m scripts.london_substrate
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load  # noqa: E402
from scripts.run_triggers_london import london_window_et  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402

NY = "America/New_York"


def main():
    trigs = load(["output/triggers_london.csv"])
    print(f"loaded {len(trigs)} London triggers")

    mb = pd.read_parquet("data/reference/nq_1m_master.parquet")
    mb = mb[mb.ts_event >= pd.Timestamp("2025-05-20", tz=NY)]
    fb = pd.read_parquet("data/reference/nq_1m_feb_jul2026.parquet")
    df = (pd.concat([mb, fb], ignore_index=True)
          .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))

    # group trigger days by their ET window
    days = sorted({t.ts[:10] for t in trigs})
    shifted = {d for d in days if london_window_et(d)[0].hour != 3}
    groups = [("LDN", dtime(3, 0), dtime(5, 0), [t for t in trigs if t.ts[:10] not in shifted]),
              ("LDN_DST", dtime(4, 0), dtime(6, 0), [t for t in trigs if t.ts[:10] in shifted])]

    base = load_backtest_config().model_copy(update={"max_trades_per_day": 2})
    rows = []
    for tag, ws, we, tt in groups:
        if not tt:
            continue
        cfg = base.model_copy(update={"win_start": ws, "win_end": we})
        cfg_e3, cfg_e4 = books(cfg)
        for book, bc in (("E3", cfg_e3), ("E4", cfg_e4)):
            tr, _, _ = simulate(df, tt, bc)
            for r in tr:
                rows.append(dict(day=r.trade_date, book=book, fill=str(r.fill_ts),
                                 exit=str(r.exit_ts), direction=r.direction,
                                 entry=r.entry, stop=r.stop_initial,
                                 exit_price=r.exit_price, exit_reason=r.exit_reason,
                                 dollars=r.dollars, pattern=r.pattern,
                                 tf=getattr(r, "tf", ""), wgroup=tag))
            print(f"  {tag}/{book}: {sum(1 for x in rows if x['wgroup']==tag and x['book']==book)} fills")

    out = pd.DataFrame(rows).sort_values("fill").reset_index(drop=True)
    out["yr"] = out.day.str[:4].astype(int)
    out["risk"] = (out.entry - out.stop).abs()
    out.to_parquet("output/london_substrate.parquet")
    w = out.dollars > 0
    print(f"\nwrote output/london_substrate.parquet: {len(out)} fills "
          f"({out.day.nunique()} days; WR {w.mean()*100:.0f}%, raw ${out.dollars.sum():+,.0f})")
    for yr in (2025, 2026):
        d = out[out.yr == yr]
        print(f"  {yr}: {len(d)} fills, WR {(d.dollars>0).mean()*100:.0f}%, raw ${d.dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
