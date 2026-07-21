#!/usr/bin/env python3
"""DIAGNOSTIC: why does the golden window (09:40-10:15) take ~8 trades/month when ~216
classified triggers/month exist there? Tally the engine's per-trigger verdict status to
locate the funnel collapse. Feeds ONLY golden-window-ts triggers so the fates are clean.
Reports; ships nothing.
"""
import sys
from collections import Counter
from datetime import time as dtime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load  # noqa: E402
from src.backtest.engine import load_backtest_config, simulate  # noqa: E402

NY = "America/New_York"
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
DATA = Path("data/reference/nq_1m_feb_jul2026.parquet")


def in_gold(ts):
    hm = str(ts)[11:16]
    try:
        h, m = int(hm[:2]), int(hm[3:5]); x = h * 60 + m
        return 9 * 60 + 40 <= x <= 10 * 60 + 15
    except Exception:
        return False


def main():
    allt = [t for t in load(["output/triggers_feb_ob.csv", "output/triggers_marjul_ob.csv"]) if in_gold(t.ts)]
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet(DATA)
    base = load_backtest_config().model_copy(update={
        "no_trade_start": None, "no_trade_end": None,
        "win_start": dtime(9, 40), "win_end": dtime(10, 15), "max_trades_per_day": 2})
    cnt = Counter()
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for tt, cfg in ((e3in, books(base)[0]), (e4in, books(base)[1])):
            _, verd, _ = simulate(seg, tt, cfg)
            for v in verd:
                cnt[getattr(v, "status", None) or v["status"]] += 1
    total = sum(cnt.values())
    print(f"=== GOLDEN-WINDOW TRIGGER FUNNEL (Feb-Jul, cap 2, E3/E4 split) ===")
    print(f"golden-window triggers fed: {total}  (~{total/6:.0f}/month)\n")
    for st, c in cnt.most_common():
        print(f"  {st:28s} {c:5d}  ({c / total * 100:4.1f}%)")
    taken = cnt.get("taken", 0)
    print(f"\n  -> TAKEN: {taken} ({taken/6:.1f}/month).  Biggest killers above.")


if __name__ == "__main__":
    main()
