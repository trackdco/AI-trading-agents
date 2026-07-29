#!/usr/bin/env python3
"""Generate the EXPANDED golden-window trade set (cap-killed, min-stop 15) with full per-trade
detail, saved to output/golden_expanded.csv, so heatmap/CVD feature studies can iterate on it
WITHOUT re-simming. This is the substrate for finding a selector that adds golden volume at
maintained quality. Includes the good 54%-quality trades AND the junk we need to filter out.
"""
import sys
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")
GOLD = (dtime(9, 40), dtime(10, 15))


def gw(ts):
    hm = str(ts)[11:16]
    try:
        h, m = int(hm[:2]), int(hm[3:5]); x = h * 60 + m
        return 9 * 60 + 40 <= x <= 10 * 60 + 15
    except Exception:
        return False


def main():
    allt = [t for t in load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]) if gw(t.ts)]
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    base = load_backtest_config().model_copy(update={"no_trade_start": None, "no_trade_end": None,
        "win_start": GOLD[0], "win_end": GOLD[1], "max_trades_per_day": 2, "post_open_min_stop": 15.0})
    cfg_e3, cfg_e4 = books(base)
    rows = []
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war]   # no 15pt cap
        for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
            tr, _, _ = simulate(seg, tt, cfg)
            for r in tr:
                ft = pd.Timestamp(r.fill_ts).time()
                if not (GOLD[0] <= ft < GOLD[1]):
                    continue
                rows.append(dict(day=r.trade_date, fill_ts=str(r.fill_ts), exit_ts=str(r.exit_ts),
                                 direction=r.direction, entry=r.entry, stop_initial=r.stop_initial,
                                 exit_price=r.exit_price, exit_reason=r.exit_reason, r_multiple=r.r_multiple,
                                 dollars=r.dollars, win=r.dollars > 0, pattern=r.pattern,
                                 risk_pts=abs(r.entry - r.stop_initial)))
    J = pd.DataFrame(rows).drop_duplicates(subset=["fill_ts", "direction", "entry"]).sort_values("fill_ts")
    J.to_csv("output/golden_expanded.csv", index=False)
    print(f"expanded golden trades: {len(J)}  ${J.dollars.sum():+,.0f}  win {J.win.mean()*100:.0f}%")
    print(f"winners: {J.win.sum()} (${J[J.win].dollars.sum():+,.0f})  losers: {(~J.win).sum()} (${J[~J.win].dollars.sum():+,.0f})")
    print(f"median risk: winners {J[J.win].risk_pts.median():.0f}pt  losers {J[~J.win].risk_pts.median():.0f}pt")


if __name__ == "__main__":
    main()
