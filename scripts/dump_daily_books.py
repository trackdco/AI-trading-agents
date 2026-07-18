#!/usr/bin/env python3
"""Regenerate output/allyears_daily_books.csv — per-day P&L of BOTH books over the
master history, under the CURRENT engine rules (news-aware since the 2023-25
calendar backfill). This is the ground truth for oracle labels, base rates, the
analog table, and the Q2 2025 exam; regenerate whenever an engine rule or its
input data changes.

    python -m scripts.dump_daily_books --years 2023,2024,2025,2026
"""
import argparse
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.year_suite import _init, run_task  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2023,2024,2025,2026")
    ap.add_argument("--daydir", default="output/triggers_hist2326_days")
    ap.add_argument("--out", default="output/allyears_daily_books.csv")
    a = ap.parse_args()

    daily = {}                                       # day -> {"E3": $, "E4": $}
    for year in a.years.split(","):
        months = sorted({p.name[:7] for p in Path(a.daydir).glob(f"{year}-*.csv")
                         if p.stat().st_size > 0})
        tasks = [(arm, m) for m in months for arm in ("e3book", "e4book")]
        with ProcessPoolExecutor(max_workers=4, initializer=_init,
                                 initargs=(year, a.daydir, "none")) as ex:
            for arm, mo, _, per_day in ex.map(run_task, tasks):
                key = "E3" if arm == "e3book" else "E4"
                for d, v in per_day.items():
                    daily.setdefault(d, {"E3": 0.0, "E4": 0.0})[key] += v
        print(f"  {year}: {len(months)} months done", flush=True)

    rows = []
    for d in sorted(daily):
        e3, e4 = daily[d]["E3"], daily[d]["E4"]
        best = max(e3, e4)
        rows.append(dict(day=d, E3=round(e3, 2), E4=round(e4, 2),
                         best=round(best, 2), oracle_sd=round(max(best, 0.0), 2),
                         pick="E3" if e3 >= e4 else "E4",
                         month=d[:7], year=d[:4]))
    out = pd.DataFrame(rows)
    out.to_csv(a.out, index=False)
    print(f"wrote {a.out}: {len(out)} days")
    print(out.groupby("year")[["E3", "E4", "oracle_sd"]].sum().round(0).to_string())


if __name__ == "__main__":
    main()
