#!/usr/bin/env python3
"""MECHANICAL coil AND absorption stand-down on REAL trades (Angus 22 Jul). Tests whether the
validated coil+absorption no-trade gate has +EV when applied as an overlay to the actual trade
substrate (allyears E3/E4 for 2025, chained MOMENTUM/ROTATION for 2026). Thresholds are out-of-fit
(other year's median). Result: +$16,455 recovered on 2025 (removes trades that are ~79% losers),
small -$1,848 drag on the already-profitable 2026 -> the bleed-stopper profile you want.

    python -m scripts.mechanical_standdown_trades
"""
import pandas as pd, numpy as np
from pathlib import Path

G = pd.read_csv("output/fe_full/labels.csv")[["day", "coil", "absorp_corr"]]
G["yr"] = G.day.str[:4].astype(int)
a = pd.read_csv("output/allyears_book_trades.csv")[["day", "book", "dollars"]]
c = pd.read_csv("output/chained_trades.csv")
c["book"] = c.book.map({"MOMENTUM": "E4", "ROTATION": "E3"})
c = c[["day", "book", "dollars"]]
T = pd.concat([a, c], ignore_index=True)
T = T[T.day.isin(set(G.day))].copy()
T["yr"] = T.day.str[:4].astype(int)
gate = G.set_index("day")


def flagged(day, tc, ta):
    if day not in gate.index:
        return False
    r = gate.loc[day]
    return (r.coil == r.coil) and (r.coil >= tc) and (r.absorp_corr >= ta)


print("=== MECHANICAL coil AND absorption STAND-DOWN on REAL trades (out-of-fit) ===\n")
for book in ["E3", "E4", "ALL"]:
    sub = T if book == "ALL" else T[T.book == book]
    print(f"--- {book} book ({len(sub)} trades) ---")
    for train, test in ((2026, 2025), (2025, 2026)):
        tr = G[G.yr == train]; te = sub[sub.yr == test].copy()
        if len(te) == 0:
            continue
        tc, ta = tr.coil.median(), tr.absorp_corr.median()
        te["flag"] = te.day.map(lambda d: flagged(d, tc, ta))
        base, kept = te.dollars.sum(), te[~te.flag].dollars.sum()
        rem = te[te.flag]
        rw, rl = int((rem.dollars > 0).sum()), int((rem.dollars <= 0).sum())
        mark = "+EV" if kept > base else "NO"
        print(f"  train{train}->test{test}: base ${base:+8,.0f} -> gated ${kept:+8,.0f}  "
              f"({mark} {kept-base:+,.0f})  [stood down {rem.day.nunique()}d/{len(rem)}t: {rw}W {rl}L]")
    print()
