#!/usr/bin/env python3
"""CHOP DETECTOR (Angus, 20 Jul): 2025's entire leak is trading both-books-lose days.
Measure how much of that chop is catchable PRE-OPEN vs how much genuinely needs the
intraday read -- with the 2026-first constraint (never hurt the live year).

Key finding: on TRADEABLE days, 2025 champion P&L (+$26,320) ~= 2026 (+$27,838). The
whole 2025 hole is the both-lose days (-$42,282 if traded). So 2025 is a pure stand-down
problem. But trailing both-lose rate does NOT separate 2025 from 2026 (2026 chop_20=0.53
> 2025's 0.49), so a naive chop gate taxes the live year. Only a VIX-filtered version is
2026-safe -- and it still only recovers ~38% of the bleed pre-open (62% needs intraday).

    python -m scripts.chop_detector
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    b = pd.read_csv("output/allyears_daily_books_r1r2.csv")
    v = pd.read_csv("output/regime_vector.csv")
    vix = pd.read_csv("data/reference/vix_daily.csv", parse_dates=["date"])
    vix["day"] = vix.date.dt.strftime("%Y-%m-%d")
    d = b.merge(v, on="day", how="left").merge(vix[["day", "vix"]], on="day", how="left")
    d = d.sort_values("day").reset_index(drop=True)
    d["y"] = d.day.str[:4]
    d["champ_pl"] = np.where(d.imbal_share_20 >= 0.5, d.E4, d.E3)
    d["both_lose"] = ((d.E3 <= 0) & (d.E4 <= 0)).astype(int)
    d["chop_20"] = d.both_lose.rolling(20).mean().shift(1)       # trailing chop, walk-forward
    d["vix_ma20"] = d.vix.rolling(20).mean().shift(1)

    def peryear(flat, label):
        pl = np.where(flat, 0.0, d.champ_pl)
        s = {y: g.pl.sum() for y, g in pd.DataFrame({"y": d.y, "pl": pl}).groupby("y")}
        print(f"{label:36s} " + "  ".join(f"{y}:${s.get(y,0):+7,.0f}" for y in ["2023","2024","2025","2026"]) + f"  ALL ${sum(pl):+,.0f}")

    peryear(np.zeros(len(d), bool), "always trade")
    peryear((d.chop_20 > 0.5).fillna(False).values, "chop_20>0.5 (naive - taxes 2026)")
    peryear(((d.chop_20 > 0.5) & (d.vix > d.vix_ma20)).fillna(False).values, "chop>0.5 AND vix>ma (2026-safe)")
    peryear(d.both_lose.astype(bool).values, "PERFECT (oracle both-lose)")

    g = d[d.y == "2025"]
    bleed = g[g.both_lose == 1].champ_pl.sum()
    caught = g[(g.both_lose == 1) & (g.chop_20 > 0.5)].champ_pl.sum()
    print(f"\n2025 both-lose bleed if traded: ${bleed:+,.0f}")
    print(f"  pre-open catchable (chop>0.5): {caught/bleed*100:.0f}%  |  needs intraday: {(1-caught/bleed)*100:.0f}%")


if __name__ == "__main__":
    main()
