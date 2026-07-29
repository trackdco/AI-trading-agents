#!/usr/bin/env python3
"""Why did the 20pt pre-market engine cap remove 0 trades when the CSV skip removed 7?
Runs the pre-market book with cap=None vs cap=20, dumps per-trade INTENDED risk
(limit-stop, known at order time) vs REALIZED risk_pts (entry-stop, post-fill), and the
entry variant, so we can see if the >20pt realized stops are market-entry slippage that
the causal cap legitimately cannot catch.
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load                       # noqa: E402
from src.backtest.engine import load_backtest_config, simulate          # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
PRE = (dtime(8, 0), dtime(9, 30))


def run(allt, war, df, cap):
    cfg0 = load_backtest_config()
    base = cfg0.model_copy(update={"no_trade_start": None, "no_trade_end": None})
    wcfg = base.model_copy(update={"win_start": PRE[0], "win_end": PRE[1],
                                   "max_trades_per_day": 2, "max_stop_points": cap})
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        cfg_e3, cfg_e4 = books(wcfg)
        for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                if not (PRE[0] <= ft < PRE[1]):
                    continue
                intended = abs(r.limit_price - r.stop_initial)
                realized = abs(r.entry - r.stop_initial)
                rows.append(dict(date=r.trade_date, fill=ft.strftime("%H:%M"), var=r.entry_variant,
                                 intended=round(intended, 1), realized=round(realized, 1),
                                 dollars=r.dollars))
    return pd.DataFrame(rows)


def main():
    allt = load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"])
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    off = run(allt, war, df, None)
    on = run(allt, war, df, 20.0)
    print(f"pre-market trades  cap OFF: {len(off)}   cap 20pt: {len(on)}")
    print(f"  vetoed by engine cap: {len(off) - len(on)}\n")
    print("=== pre trades with REALIZED stop > 20pt (what the CSV skip cut) ===")
    big = off[off.realized > 20].sort_values("realized", ascending=False)
    print(big.to_string(index=False))
    print(f"\n  of those, INTENDED risk (>20 = catchable by causal cap): "
          f"{int((big.intended > 20).sum())} of {len(big)}")
    print(f"  intended<=20 but realized>20 (market-entry slippage, NOT catchable): "
          f"{int((big.intended <= 20).sum())} of {len(big)}")
    print(f"  $ in the not-catchable slippage group: "
          f"${big[big.intended <= 20].dollars.sum():+,.0f}")


if __name__ == "__main__":
    main()
