#!/usr/bin/env python3
"""LONDON trade substrate: triggers -> fills/exits, both books, DST-correct windows.

Mirrors the morning universe build: every London-window trigger is run through the
backtest engine under BOTH books (E3 = rotation/V8 mgmt, E4 = momentum entry), no book
choosing. Days are grouped by their ET window (03:00-05:00 normal / 04:00-06:00 during
UK-US DST misalignment) and simulated with matching win_start/win_end configs.

Writes output/london_substrate.parquet (one row per fill, chronological).

`--span holdout` runs the identical code over the sealed 2023/24 days instead, reading the
triggers `scripts.holdout_london_triggers` detected and writing
output/london_substrate_holdout.parquet. Same engine, same DST grouping, same cap.

The engine's `min_stop_points` floor is forced to 0 in both spans. It has to be: the shipped
london_substrate.parquet contains 134 sub-7pt fills, so it predates that ruling, and Layer 0
of the London canon does its own gating at >=9.5pt anyway. Leaving today's floor on would
veto candidates at fill time, and since `max_trades_per_day` is enforced there, each veto
hands the day's cap slot to a trade the rulebook never saw.

    python -m scripts.london_substrate
    python -m scripts.london_substrate --span holdout
"""
import argparse
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load  # noqa: E402
from scripts.run_triggers_london import london_window_et  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402

NY = "America/New_York"

SPANS = {
    "fit": {
        "trigs": ["output/triggers_london.csv"],
        "bars": [("data/reference/nq_1m_master.parquet", "2025-05-20"),
                 ("data/reference/nq_1m_feb_jul2026.parquet", None)],
        "out": "output/london_substrate.parquet",
        "years": (2025, 2026),
    },
    "holdout": {
        "trigs": ["output/triggers_london_holdout.csv"],
        "bars": [("data/reference/nq_1m_master.parquet", "2023-05-01")],
        "out": "output/london_substrate_holdout.parquet",
        "years": (2023, 2024),
    },
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--span", choices=sorted(SPANS), default="fit")
    a = ap.parse_args()
    spec = SPANS[a.span]

    trigs = load(spec["trigs"])
    print(f"loaded {len(trigs)} London triggers ({a.span})")

    frames = []
    for path, since in spec["bars"]:
        b = pd.read_parquet(path).drop(columns=["roll"], errors="ignore")
        if since:
            b = b[b.ts_event >= pd.Timestamp(since, tz=NY)]
        frames.append(b)
    df = (pd.concat(frames, ignore_index=True)
          .drop_duplicates("ts_event").sort_values("ts_event").reset_index(drop=True))

    # group trigger days by their ET window
    days = sorted({t.ts[:10] for t in trigs})
    shifted = {d for d in days if london_window_et(d)[0].hour != 3}
    groups = [("LDN", dtime(3, 0), dtime(5, 0), [t for t in trigs if t.ts[:10] not in shifted]),
              ("LDN_DST", dtime(4, 0), dtime(6, 0), [t for t in trigs if t.ts[:10] in shifted])]
    print(f"  {len(days)} days, {len(shifted)} DST-shifted (04:00-06:00 ET)")

    base = load_backtest_config().model_copy(update={"max_trades_per_day": 2,
                                                     "min_stop_points": 0.0})
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
    out.to_parquet(spec["out"])
    w = out.dollars > 0
    print(f"\nwrote {spec['out']}: {len(out)} fills "
          f"({out.day.nunique()} days; WR {w.mean()*100:.0f}%, raw ${out.dollars.sum():+,.0f})")
    for yr in spec["years"]:
        d = out[out.yr == yr]
        print(f"  {yr}: {len(d)} fills, WR {(d.dollars>0).mean()*100:.0f}%, raw ${d.dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
