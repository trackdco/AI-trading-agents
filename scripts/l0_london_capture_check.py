#!/usr/bin/env python3
"""Does the London L0 census contain the trades ANGUS ACTUALLY TOOK in London?

The detector-vs-trader check, London edition (handoff §4-L0 "bonus gate"). Parity proved the
regenerated census reproduces the detector's own history; this asks the different question —
whether the detector SEES what the trader saw.

THE EVIDENCE IS TWO TRADES. Neither hand log covers London: feb2026_hand_log.csv and
mar2026_hand_log.csv are both NY-morning only (entry times 09:25-10:52 ET). The only live
London executions in the repo are in data/reference/live_trades_catalog.md, both on
2026-04-10, read off TopstepX screenshots with Melbourne-clock conversion (post-Apr-5 rule:
AEST+10 vs EDT-4 = -14h). NY's equivalent gate ran 43/45; this one runs on n=2.

n=2 CANNOT VALIDATE THE DETECTOR. A HIT is weak positive evidence; a MISS on both is a real
finding worth naming before L3 fits anything to this census. Read it as a smoke test, not a
gate that can pass. Times are screenshot timestamps — the entry may precede the shot — so the
match window is deliberately generous and direction must agree.

    python -m scripts.l0_london_capture_check
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NY = "America/New_York"
CENSUS = ROOT / "output/l0_triggers_london_fit.parquet"
WINDOW_MIN = 20         # screenshot time is an upper bound on entry time, not the entry time

# data/reference/live_trades_catalog.md, "Apr 10 cluster" (IMG_3364/3366/3376/3378)
LIVE = [
    {"day": "2026-04-10", "et": "03:10", "direction": "long",  "stop_pts": 6.75,
     "note": "LONG 6 MNQM26 w/ 6.75pt stop"},
    {"day": "2026-04-10", "et": "04:24", "direction": "short", "stop_pts": 31.75,
     "note": "SHORT 6 MNQM26 w/ 31.75pt stop"},
]


def main() -> None:
    if not CENSUS.exists():
        raise SystemExit(f"{CENSUS.relative_to(ROOT)} not found — build the fit census first")
    T = pd.read_parquet(CENSUS)
    # trigger ts are ET ISO strings whose UTC offset flips across DST — parse via UTC
    T["ts_et"] = pd.to_datetime(T.ts, format="mixed", utc=True).dt.tz_convert(NY)
    T["day"] = T.ts_et.dt.strftime("%Y-%m-%d")
    T["stop_dist"] = (T.entry_ref - T.stop_ref).abs()

    hits = 0
    for ex in LIVE:
        target = pd.Timestamp(f"{ex['day']} {ex['et']}", tz=NY)
        day = T[T.day == ex["day"]]
        near = day[(day.ts_et - target).abs() <= pd.Timedelta(minutes=WINDOW_MIN)]
        same = near[near.direction == ex["direction"]]

        print(f"\n{ex['day']} {ex['et']} ET  {ex['direction'].upper():<5} "
              f"stop {ex['stop_pts']}pt — {ex['note']}")
        print(f"  census that day: {len(day)} triggers | "
              f"within +/-{WINDOW_MIN}min: {len(near)} | same direction: {len(same)}")
        if same.empty:
            print("  MISS — no same-direction trigger in the window")
            if not near.empty:
                print("    (opposite-direction triggers nearby: "
                      f"{sorted(near.ts_et.dt.strftime('%H:%M') + ' ' + near.direction)})")
            continue
        hits += 1
        best = same.assign(d=(same.ts_et - target).abs()).sort_values("d").iloc[0]
        print(f"  HIT  — nearest: {best.ts_et.strftime('%H:%M')} ET {best.tf} {best.kind} "
              f"pattern {best.pattern}")
        print(f"         entry {best.entry_ref:.2f} stop {best.stop_ref:.2f} "
              f"= {best.stop_dist:.2f}pt (live: {ex['stop_pts']}pt) | "
              f"confluence {best.confluence_count}")
        for _, r in same.sort_values("ts_et").iterrows():
            print(f"         all: {r.ts_et.strftime('%H:%M')} {r.tf:>5} {r.kind:<16} "
                  f"stop_dist {r.stop_dist:6.2f}pt")

    print(f"\ncapture: {hits}/{len(LIVE)} live London executions have a same-direction "
          f"trigger within +/-{WINDOW_MIN}min")
    print("n=2 — weak evidence either way. Not a pass/fail gate; a finding to report.")


if __name__ == "__main__":
    main()
