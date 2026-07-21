#!/usr/bin/env python3
"""BOOK-SUPPORT / ABSORPTION SIGNAL ON 2025 H2 (Angus 22 Jul). The decisive generalization
test: in 2026 the entry book-support read held out-of-fit (book AGAINST = absorption won 52%
vs book WITH 33%). Does it survive 2025's regime, or was it 2026-only like the CVD gate?

Runs the 2+2 canon trades on 2025 H2, reads the 2025 depth at each entry minute, splits by
whether the book was WITH or AGAINST the trade. Reports win rate + $/trade.

    python -m scripts.book_support_2025
"""
import glob
import sys
from datetime import time as dtime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.grade_window_cap import books, load                       # noqa: E402
from src.backtest.engine import load_backtest_config, simulate          # noqa: E402

NY = "America/New_York"
MONTHS = ["2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"]
PRE = (dtime(8, 0), dtime(9, 30))
GOLD = (dtime(9, 40), dtime(10, 15))
DEPTH = "data/reference/depth_2025"


def book_at(cache, path, minute):
    df = cache.get(path)
    if df is None:
        df = pd.read_csv(path, parse_dates=["ts"]); cache[path] = df
    m = df[(df.ts.dt.hour * 60 + df.ts.dt.minute).between(minute - 2, minute)]
    if not len(m):
        return None
    per = m.groupby(["ts", "side"])["size"].sum().unstack(fill_value=0)
    if "bid" not in per or "ask" not in per:
        return None
    bid, ask = per["bid"].mean(), per["ask"].mean()
    return (bid - ask) / (bid + ask) if (bid + ask) else 0.0


def main():
    allt = [t for t in load(["output/triggers_hist2326_ob.csv"]) if t.ts[:7] in MONTHS]
    vec = pd.read_csv("output/regime_vector.csv")
    war = {r.day for _, r in vec.iterrows() if pd.notna(r.imbal_share_20) and r.imbal_share_20 >= 0.5}
    df = pd.read_parquet("data/reference/nq_1m_master.parquet")
    df = df[df.ts_event >= pd.Timestamp("2025-06-15", tz=NY)].reset_index(drop=True)
    cfg0 = load_backtest_config()
    base = cfg0.model_copy(update={"no_trade_start": None, "no_trade_end": None})
    wins = [("pre", base.model_copy(update={"win_start": PRE[0], "win_end": PRE[1], "max_trades_per_day": 2, "max_stop_points": 20.0}), PRE),
            ("golden", base.model_copy(update={"win_start": GOLD[0], "win_end": GOLD[1], "max_trades_per_day": 2}), GOLD)]
    rows = []
    print("simulating 2025 H2 ...", flush=True)
    for m in MONTHS:
        trigs = [t for t in allt if t.ts[:7] == m]
        end = pd.Timestamp((pd.Timestamp(m + "-01", tz=NY) + pd.offsets.MonthBegin(1)).tz_localize(None), tz=NY)
        seg = df[df.ts_event <= end].reset_index(drop=True)
        e3in = [t for t in trigs if t.ts[:10] not in war]
        e4in = [t for t in trigs if t.ts[:10] in war and abs(t.close - t.stop_ref) <= 15.0]
        for wname, wcfg, wwin in wins:
            cfg_e3, cfg_e4 = books(wcfg)
            for tt, cfg in ((e3in, cfg_e3), (e4in, cfg_e4)):
                tr, _, _ = simulate(seg, tt, cfg)
                for r in tr:
                    ft = pd.Timestamp(r.fill_ts).time()
                    if not (wwin[0] <= ft < wwin[1]):
                        continue
                    rows.append(dict(date=r.trade_date, window=wname, fill_t=ft.strftime("%H:%M"),
                                     direction=r.direction, dollars=r.dollars, win=r.dollars > 0))
    T = pd.DataFrame(rows)
    didx = {Path(f).stem.split("_")[2]: f for f in glob.glob(f"{DEPTH}/nq_depth_*_ny.csv")}
    cache = {}
    bs = []
    for r in T.itertuples():
        p = didx.get(r.date)
        if not p:
            bs.append(np.nan); continue
        h, mnt = map(int, r.fill_t.split(":"))
        imb = book_at(cache, p, h * 60 + mnt)
        bs.append(imb * (1 if r.direction == "long" else -1) if imb is not None else np.nan)
    T["book_support"] = bs
    D = T.dropna(subset=["book_support"])
    print(f"\n### BOOK-SUPPORT SIGNAL ON 2025 H2 ({len(D)} trades with depth) ###\n")

    def rep(s, tag):
        if not len(s):
            print(f"  {tag:28s} (0)"); return
        print(f"  {tag:28s} {len(s):3d}t  win {s.win.mean()*100:2.0f}%  ${s.dollars.mean():+5.0f}/t  ${s.dollars.sum():+7,.0f}")
    rep(D[D.book_support < -0.05], "book AGAINST (absorption)")
    rep(D[D.book_support.abs() <= 0.05], "book NEUTRAL")
    rep(D[D.book_support > 0.05], "book WITH")
    print("\n  golden only:")
    g = D[D.window == "golden"]
    rep(g[g.book_support < -0.05], "  golden AGAINST")
    rep(g[g.book_support > 0.05], "  golden WITH")
    print("\n  reference 2026: AGAINST 52% win / +$400/t   WITH 33% / +$144/t  (held out-of-fit)")
    D.to_csv("output/book_support_2025.csv", index=False)


if __name__ == "__main__":
    main()
