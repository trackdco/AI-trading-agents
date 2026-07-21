#!/usr/bin/env python3
"""PER-TRADE BOOK SUPPORT x CVD (Angus 21 Jul). Not a day-level veto -- refine WHICH trades
we take. At each canon trade's entry minute, is the resting book (MBP-10, ~touch) stacked
WITH the trade or AGAINST it, and is that liquidity holding or being pulled? Cross it with
CVD (flow) to see which trades are the accurate ones.

  book_support = dir-oriented top-10 imbalance at the fill minute
                 (+ = bids back a long / asks back a short = book WITH you)
  hold_pull    = book total change over the 3 min into entry (+ building, - pulling)
  cvd          = the canon CVD (<=0 = absorption, already in the trade frame)

Reports win rate + $/trade split by book support, by CVD, and the 2x2 -- on the gated canon.

    python -m scripts.wall_refine
"""
import glob
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
DEPTH = "data/reference/depth_2026"


def depth_index():
    return {Path(f).stem.split("_")[2]: f for f in glob.glob(f"{DEPTH}/nq_depth_*_ny.csv")}


def book_at(path_cache, path, minute):
    df = path_cache.get(path)
    if df is None:
        df = pd.read_csv(path, parse_dates=["ts"])
        path_cache[path] = df
    # top-10 aggregate in a 3-min window ending at the fill minute
    m = df[(df.ts.dt.hour * 60 + df.ts.dt.minute).between(minute - 2, minute)]
    if not len(m):
        return None
    per = m.groupby(["ts", "side"])["size"].sum().unstack(fill_value=0)
    if "bid" not in per or "ask" not in per:
        return None
    bid, ask = per["bid"].mean(), per["ask"].mean()
    tot = per["bid"] + per["ask"]
    imbal = (bid - ask) / (bid + ask) if (bid + ask) else 0.0
    hold_pull = (tot.iloc[-1] - tot.iloc[0]) if len(tot) > 1 else 0.0
    return imbal, hold_pull


def main():
    W = pd.read_csv("output/window22_trades.csv")
    W = W[W.gated_kept].copy()
    W["date"] = W.date.astype(str)
    didx = depth_index()
    cache = {}
    rows = []
    for r in W.itertuples():
        p = didx.get(r.date)
        if not p:
            continue
        h, m = map(int, r.fill_t.split(":"))
        b = book_at(cache, p, h * 60 + m)
        if b is None:
            continue
        imbal, hp = b
        sgn = 1 if r.direction == "long" else -1
        rows.append(dict(date=r.date, window=r.window, direction=r.direction, dollars=r.dollars,
                         win=r.win, cvd=r.cvd, book_support=imbal * sgn, hold_pull=hp))
    D = pd.DataFrame(rows)
    print(f"### PER-TRADE BOOK SUPPORT x CVD ({len(D)} canon trades with depth) ###\n")

    def rep(s, tag):
        if not len(s):
            print(f"  {tag:34s}  (0)"); return
        print(f"  {tag:34s} {len(s):3d}t  win {s.win.mean()*100:2.0f}%  ${s.dollars.mean():+5.0f}/t  ${s.dollars.sum():+7,.0f}")

    print("== book support at entry (book WITH the trade vs AGAINST) ==")
    rep(D[D.book_support > 0.05], "book WITH  (support > +0.05)")
    rep(D[D.book_support.abs() <= 0.05], "book NEUTRAL")
    rep(D[D.book_support < -0.05], "book AGAINST (support < -0.05)")

    print("\n== CVD alone (already in canon) ==")
    rep(D[D.cvd <= 0], "CVD absorption (<=0)")
    rep(D[D.cvd > 0], "CVD hollow (>0)")

    print("\n== hold vs pull (book building/pulling into entry) ==")
    rep(D[D.hold_pull > 0], "book BUILDING")
    rep(D[D.hold_pull <= 0], "book PULLING")

    print("\n== 2x2: book support x CVD absorption ==")
    for bs, bl in ((D.book_support > 0, "book WITH"), (D.book_support <= 0, "book AGAINST")):
        for cv, cl in ((D.cvd <= 0, "CVD absorb"), (D.cvd > 0, "CVD hollow")):
            rep(D[bs & cv], f"{bl} + {cl}")

    print("\n== golden only: book support ==")
    g = D[D.window == "golden"]
    rep(g[g.book_support > 0], "golden book WITH")
    rep(g[g.book_support <= 0], "golden book AGAINST")

    # OUT-OF-FIT: does "book against wins more" hold on the held-out half?
    D["mo"] = D.date.str[:7]
    TRAIN = {"2026-02", "2026-03", "2026-04"}
    print("\n== OUT-OF-FIT validation: book-support separation, train vs test ==")
    for tag, s in (("TRAIN Feb-Apr", D[D.mo.isin(TRAIN)]), ("TEST May-Jul", D[~D.mo.isin(TRAIN)])):
        wf = s[s.book_support > 0.05]; ag = s[s.book_support < -0.05]
        print(f"  {tag}:  book WITH {len(wf):2d}t win {wf.win.mean()*100 if len(wf) else 0:2.0f}% ${wf.dollars.mean() if len(wf) else 0:+5.0f}/t"
              f"   |  book AGAINST {len(ag):2d}t win {ag.win.mean()*100 if len(ag) else 0:2.0f}% ${ag.dollars.mean() if len(ag) else 0:+5.0f}/t")

    print("\n== P&L of a conviction filter (skip book-WITH trades), train vs test ==")
    for tag, s in (("TRAIN Feb-Apr", D[D.mo.isin(TRAIN)]), ("TEST May-Jul", D[~D.mo.isin(TRAIN)]), ("ALL", D)):
        base = s.dollars.sum()
        kept = s[s.book_support <= 0.05].dollars.sum()   # drop book-WITH (support>+0.05)
        print(f"  {tag:14s}: all {len(s):2d}t ${base:+7,.0f} win {s.win.mean()*100:2.0f}%"
              f"  ->  skip book-WITH {len(s[s.book_support<=0.05]):2d}t ${kept:+7,.0f} win {s[s.book_support<=0.05].win.mean()*100:2.0f}%")
    D.to_csv("output/wall_refine.csv", index=False)
    print("\n-> output/wall_refine.csv")


if __name__ == "__main__":
    main()
