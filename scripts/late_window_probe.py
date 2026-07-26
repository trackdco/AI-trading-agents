#!/usr/bin/env python3
"""Is 10:15-11:00 worth trading? A first-pass probe, deliberately unfiltered.

ANGUS 2026-07-26: *"i just wanted to see if the 10:15-11:00 window could be made profitable
since we had all the order flow data now."*

Mirrors scripts/window_expanded.py exactly — same engine, same trigger caches, same E3/E4
book split, same no-cap stop treatment — and adds the late window alongside the two we
already trade. Apples to apples by construction: the ONLY thing that changes between rows
is the window bounds.

This is a RAW-OPPORTUNITY probe, not a proposal. No window-specific filters, no tuning.
The question it answers is the cheap one that has to come first: **is there anything in
that window at all before we start filtering?** If the unfiltered window is flat or
negative, anything that makes it look good afterwards is a fit, not an edge.

    python -m scripts.late_window_probe
"""
from __future__ import annotations

import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.grade_window_cap import books, load                      # noqa: E402
from src.backtest.engine import load_backtest_config, simulate        # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
WINDOWS = {
    "pre     08:00-09:30": (dtime(8, 0), dtime(9, 30)),
    "golden  09:40-10:15": (dtime(9, 40), dtime(10, 15)),
    "LATE    10:15-11:00": (dtime(10, 15), dtime(11, 0)),
    "late-a  10:15-10:30": (dtime(10, 15), dtime(10, 30)),   # the part depth still covers
    "late-b  10:30-11:00": (dtime(10, 30), dtime(11, 0)),    # flow only, no heatmap
}


def main() -> None:
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows()
           if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)

    rows = []
    for wname, (ws, we) in WINDOWS.items():
        base = load_backtest_config().model_copy(update={
            "no_trade_start": None, "no_trade_end": None, "win_start": ws, "win_end": we,
            "max_trades_per_day": 2, "post_open_min_stop": 0.0})
        cfg_e3, cfg_e4 = books(base)
        for m in MONTHS:
            trigs = [t for t in allt if t.ts[:7] == m]
            end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                               .tz_localize(None), tz=NY)
            seg = df[df.ts_event <= end].reset_index(drop=True)
            for tt, cfg in (([t for t in trigs if t.ts[:10] not in war], cfg_e3),
                            ([t for t in trigs if t.ts[:10] in war], cfg_e4)):
                tr, _, _ = simulate(seg, tt, cfg)
                for r in tr:
                    ft = pd.Timestamp(r.fill_ts).time()
                    if not (ws <= ft < we):
                        continue
                    rows.append(dict(window=wname, day=r.trade_date, month=m,
                                     fill_ts=str(r.fill_ts), direction=r.direction,
                                     risk_pts=abs(r.entry - r.stop_initial),
                                     dollars=r.dollars, win=r.dollars > 0,
                                     exit_reason=r.exit_reason, r_multiple=r.r_multiple))

    J = (pd.DataFrame(rows).drop_duplicates(subset=["window", "fill_ts", "direction"])
         .sort_values("fill_ts"))
    J.to_csv("output/late_window_probe.csv", index=False)

    print(f"2026-02 -> 2026-07, champion engine, E3/E4 split, no stop cap. "
          f"UNFILTERED — no window-specific rules.\n")
    print(f"{'window':<22}{'trades':>7}{'$':>10}{'win%':>7}{'avg $':>8}{'med R':>7}"
          f"{'med stop':>9}{'months green':>14}")
    for w in WINDOWS:
        s = J[J.window == w]
        if not len(s):
            print(f"{w:<22}{'(none)':>7}")
            continue
        mo = s.groupby("month").dollars.sum()
        print(f"{w:<22}{len(s):>7}{s.dollars.sum():>+10,.0f}{s.win.mean()*100:>6.0f}%"
              f"{s.dollars.mean():>+8,.0f}{s.r_multiple.median():>7.2f}"
              f"{s.risk_pts.median():>8.0f}pt{int((mo>0).sum()):>9}/{len(mo)}")

    print("\nmonth by month:")
    piv = J.pivot_table(index="month", columns="window", values="dollars", aggfunc="sum")
    print(piv.reindex(columns=[w for w in WINDOWS if w in piv.columns])
          .to_string(float_format=lambda x: f"{x:+,.0f}"))

    print("\nexit reasons in the late window:")
    late = J[J.window == "LATE    10:15-11:00"]
    if len(late):
        print(late.exit_reason.value_counts().to_string())
    print("\nwrote output/late_window_probe.csv")


if __name__ == "__main__":
    main()
