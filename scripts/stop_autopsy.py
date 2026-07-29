#!/usr/bin/env python3
"""STOP AUTOPSY across years (Angus 22 Jul). Filter through stop sizes like we did for
pre-market/golden -- hunt the 100pt monster stops in 2023-2026, and test stops relative to
PRICE LEVEL (a 40pt stop at NQ 15k is a bigger move than at 25k). Runs E3+E4 books full
window (08:00-10:15, 2-cap), captures per-trade risk_pts + entry price + $.

    python -m scripts.stop_autopsy
"""
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books                              # noqa: E402
from src.backtest.engine import load_backtest_config, simulate          # noqa: E402
from src.engine.triggers import Trigger                                 # noqa: E402

NY = "America/New_York"
YEARS = [2023, 2024, 2025, 2026]
DAYDIR = Path("output/triggers_hist2326_days")


def load_year(y):
    import ast
    out = []
    for p in sorted(DAYDIR.glob(f"{y}-*.csv")):
        if p.stat().st_size == 0:
            continue
        for r in pd.read_csv(p).to_dict("records"):
            ct = r.get("cluster_types")
            r["cluster_types"] = ast.literal_eval(ct) if isinstance(ct, str) else []
            out.append(Trigger(**{k: v for k, v in r.items() if k != "session_day"}))
    return [t for t in out if t.pattern != "unclassified"]


def main():
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    base = load_backtest_config().model_copy(update={"win_end": dtime(10, 15), "max_trades_per_day": 2})
    cfg_e3, cfg_e4 = books(base)
    rows = []
    for y in YEARS:
        print(f"simulating {y} ...", flush=True)
        allt = load_year(y)
        for m in [f"{y}-{i:02d}" for i in range(1, 13)]:
            trigs = [t for t in allt if t.ts[:7] == m]
            if not trigs:
                continue
            end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
            start = pd.Timestamp(m + "-01", tz=NY) - pd.Timedelta(days=12)
            seg = df[(df.ts_event <= end) & (df.ts_event >= start)].reset_index(drop=True)
            e3in = [t for t in trigs if t.ts[:10] not in war]
            e4in = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
            for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
                tr, _, _ = simulate(seg, tt, cfg)
                for r in tr:
                    if not (dtime(8, 0) <= pd.Timestamp(r.fill_ts).time() < dtime(10, 15)):
                        continue
                    rows.append(dict(year=y, month=m, risk_pts=round(abs(r.entry - r.stop_initial), 1),
                                     entry=r.entry, dollars=r.dollars, win=r.dollars > 0))
    T = pd.DataFrame(rows)
    T["risk_bps"] = T.risk_pts / T.entry * 10000            # stop as bps of price (price-relative)
    T.to_csv("output/stop_autopsy.csv", index=False)

    print("\n### STOP-SIZE AUTOPSY 2023-2026 (E3+E4, 08:00-10:15) ###\n")
    print(f"{'year':5s} {'trades':>6s} {'medStop':>7s} {'p90':>5s} {'max':>5s} {'>50pt':>6s} {'>100pt':>7s} {'$>100pt':>9s} {'medBps':>7s} {'NQ~px':>7s}")
    for y in YEARS:
        s = T[T.year == y]
        if not len(s): continue
        over = s[s.risk_pts > 100]
        print(f"{y:5d} {len(s):6d} {s.risk_pts.median():7.0f} {s.risk_pts.quantile(.9):5.0f} "
              f"{s.risk_pts.max():5.0f} {int((s.risk_pts>50).sum()):6d} {len(over):7d} "
              f"{over.dollars.sum():+9,.0f} {s.risk_bps.median():7.0f} {s.entry.median():7.0f}")

    print("\n### effect of cutting monster stops, per year ###")
    print("  (fixed >100pt cut  vs  price-relative cut at >40 bps of price)")
    for y in YEARS:
        s = T[T.year == y]
        if not len(s): continue
        base_pnl = s.dollars.sum()
        cut100 = s[s.risk_pts <= 100].dollars.sum()
        cutbps = s[s.risk_bps <= 40].dollars.sum()
        print(f"  {y}: base ${base_pnl:+8,.0f}  |  cut>100pt ${cut100:+8,.0f} (Δ{cut100-base_pnl:+,.0f})  "
              f"|  cut>40bps ${cutbps:+8,.0f} (Δ{cutbps-base_pnl:+,.0f})  [cut {int((s.risk_bps>40).sum())} trades]")


if __name__ == "__main__":
    main()
