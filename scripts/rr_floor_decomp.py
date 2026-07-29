#!/usr/bin/env python3
"""rr_floor deep-dive (ANGUS 2026-07-26: "rr floor should be looked at deeper").

The ablation's -33R headline is CONTAMINATED by mechanics: rr_floor is not a veto —
`walk_menu` picks the FIRST target level clearing the floor, so changing the floor changes
the TARGET GEOMETRY of trades that trade at every setting, on top of admitting/vetoing
marginal ones. This decomposes the three effects separately, otherwise-canon config:

  A. SHARED fills (same fill_ts+direction at both floors): how do R and target change?
     -> the exit-geometry effect.
  B. RESCUED fills (trade at the lower floor, absent at 2.0): n, R, W/L, per-year.
     -> the true admission/frequency effect.
  C. Net book per floor, both years, months green.

    python -m scripts.rr_floor_decomp
"""
from __future__ import annotations

import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.grade_window_cap import books, load                      # noqa: E402
from scripts.late_window_probe import MONTHS, TRIGGERS, WARMUP_DAYS   # noqa: E402
from src.backtest.engine import load_backtest_config, simulate        # noqa: E402

NY = "America/New_York"
FLOORS = [2.0, 1.5, 1.0]


def run(floor: float) -> pd.DataFrame:
    allt = load(TRIGGERS)
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows()
           if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    base = load_backtest_config().model_copy(update={
        "no_trade_start": None, "no_trade_end": None,
        "win_start": dtime(9, 40), "win_end": dtime(10, 15),
        "max_trades_per_day": 2, "rr_floor": floor})
    cfg_e3, cfg_e4 = books(base)
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1))
                           .tz_localize(None), tz=NY)
        start = pd.Timestamp((pd.Timestamp(m + "-01")
                              - pd.Timedelta(days=WARMUP_DAYS)).strftime("%Y-%m-%d"), tz=NY)
        seg = df[(df.ts_event >= start) & (df.ts_event <= end)].reset_index(drop=True)
        for tt, cfg in (([t for t in trigs if t.ts[:10] not in war], cfg_e3),
                        ([t for t in trigs if t.ts[:10] in war], cfg_e4)):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                if not (dtime(9, 40) <= ft < dtime(10, 15)):
                    continue
                rows.append(dict(month=m, fill_ts=str(r.fill_ts), direction=r.direction,
                                 kind=r.kind, risk_pts=abs(r.entry - r.stop_initial),
                                 target_name=r.target_name, working_target=r.working_target,
                                 dollars=r.dollars, r_multiple=r.r_multiple,
                                 exit_reason=r.exit_reason))
        print(f"  rr={floor} {m} done", flush=True)
    J = (pd.DataFrame(rows).drop_duplicates(subset=["fill_ts", "direction"])
         .sort_values("fill_ts").reset_index(drop=True))
    J["key"] = J.fill_ts + "|" + J.direction
    J["yr"] = J.month.str[:4]
    return J


def main() -> None:
    res = {}
    for f in FLOORS:
        res[f] = run(f)
        J = res[f]
        mo = J.groupby("month").dollars.sum()
        print(f"rr_floor={f}: {len(J)}t  {J.r_multiple.sum():+.1f}R  "
              f"(${J.r_multiple.sum()*200:+,.0f} @floor)  win {(J.dollars>0).mean()*100:.0f}%  "
              f"green {int((mo>0).sum())}/{len(mo)}", flush=True)
        J.to_csv(f"output/rr_floor_{str(f).replace('.','_')}.csv", index=False)

    base = res[2.0].set_index("key")
    for f in [1.5, 1.0]:
        J = res[f].set_index("key")
        shared = base.index.intersection(J.index)
        resc = J.index.difference(base.index)
        lost = base.index.difference(J.index)
        b, j = base.loc[shared], J.loc[shared]
        moved = (b.r_multiple.round(4) != j.r_multiple.round(4))
        print(f"\n===== rr {f} vs 2.0 =====")
        print(f"A. SHARED {len(shared)} fills: {moved.sum()} changed R "
              f"(target geometry). shared R {b.r_multiple.sum():+.1f} -> {j.r_multiple.sum():+.1f} "
              f"({j.r_multiple.sum()-b.r_multiple.sum():+.1f}R)")
        tgt_changed = (b.target_name != j.target_name).sum()
        print(f"   target_name changed on {tgt_changed} shared fills")
        R = J.loc[resc]
        print(f"B. RESCUED {len(resc)} fills (absent at 2.0): {R.r_multiple.sum():+.1f}R, "
              f"win {(R.dollars>0).mean()*100 if len(R) else 0:.0f}%  "
              f"[2025 {R[R.yr=='2025'].r_multiple.sum():+.1f}R / "
              f"2026 {R[R.yr=='2026'].r_multiple.sum():+.1f}R]")
        L = base.loc[lost]
        print(f"   (lost {len(lost)} fills present only at 2.0: {L.r_multiple.sum():+.1f}R — slot reshuffle)")


if __name__ == "__main__":
    main()
