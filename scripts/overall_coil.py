#!/usr/bin/env python3
"""OVERALL P&L with the coil stand-down applied to the CANON system (Angus 21 Jul).
Take the shipped canon (+$17,346: 54 pre + 28 golden, CVD-gated, 20pt pre cap) and stand
down the GOLDEN trades on days the heatmap coil fires (only where we have depth to read).
Pre-market is untouched -- coil is a golden-window signal. Honest before/after: overall,
per-month, win rate, and the in-fit (Feb-Apr) vs out-of-fit (May-Jul) split.

    python -m scripts.overall_coil
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
MONTHS = ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"]
TRAIN = {"2026-02", "2026-03", "2026-04"}


def summ(df):
    mg = df.groupby("month").dollars.sum()
    return dict(n=len(df), pnl=df.dollars.sum(), win=df.win.mean() * 100 if len(df) else 0,
                green=int((mg > 0).sum()), nmo=len(mg))


def line(tag, s):
    print(f"  {tag:26s} {s['n']:3d}t  ${s['pnl']:+9,.0f}  win {s['win']:2.0f}%  green {s['green']}/{s['nmo']}")


def main():
    W = pd.read_csv("output/window22_trades.csv")
    W = W[W.gated_kept].copy()                       # the canon 82
    C = pd.read_csv("output/coil_full.csv")[["date", "coil"]]
    W["date"] = W.date.astype(str)
    W = W.merge(C, on="date", how="left")            # coil NaN where no depth that day
    W["coil"] = W.coil.fillna(0).astype(int)

    # stand down golden trades on coil-fire days; pre-market untouched
    W["stood_down"] = (W.window == "golden") & (W.coil == 1)
    kept = W[~W.stood_down].copy()

    print("### OVERALL P&L — canon vs canon + coil golden stand-down (2026 Feb-Jul) ###\n")
    print("== whole system ==")
    line("canon (shipped)", summ(W))
    line("+ coil golden stand-down", summ(kept))
    dn = W[W.stood_down]
    print(f"\n  golden days stood down: {dn.date.nunique()}   trades removed: {len(dn)}   "
          f"${dn.dollars.sum():+,.0f} (of which winners ${dn[dn.win].dollars.sum():+,.0f}, "
          f"losers ${dn[~dn.win].dollars.sum():+,.0f})")

    print("\n== golden window only ==")
    line("canon golden", summ(W[W.window == "golden"]))
    line("+ coil stand-down", summ(kept[kept.window == "golden"]))
    print("\n== pre-market (untouched) ==")
    line("pre-market", summ(W[W.window == "pre"]))

    print("\n== per-month, whole system ==")
    print(f"  {'month':8s} {'canon':>16s}    {'+ coil stand-down':>18s}")
    for m in MONTHS:
        a = W[W.month == m]; b = kept[kept.month == m]
        fa = f"{len(a):2d}t ${a.dollars.sum():+7,.0f}"
        fb = f"{len(b):2d}t ${b.dollars.sum():+7,.0f}"
        mark = "GRN" if b.dollars.sum() > 0 else "red"
        print(f"  {m}  {fa:>16s}  ->  {fb:>16s}  {mark}")

    print("\n== in-fit vs out-of-fit split (threshold fit on Feb-Apr) ==")
    for tag, mos in (("TRAIN Feb-Apr", TRAIN), ("TEST  May-Jul", set(MONTHS) - TRAIN)):
        a = W[W.month.isin(mos)]; b = kept[kept.month.isin(mos)]
        print(f"  {tag}:  canon ${a.dollars.sum():+8,.0f}  ->  coil ${b.dollars.sum():+8,.0f}   "
              f"(Δ ${b.dollars.sum()-a.dollars.sum():+,.0f})")

    kept.to_csv("output/overall_coil_trades.csv", index=False)
    tot_c, tot_k = W.dollars.sum(), kept.dollars.sum()
    print(f"\n  OVERALL: ${tot_c:+,.0f}  ->  ${tot_k:+,.0f}   (Δ ${tot_k-tot_c:+,.0f}, "
          f"{len(W)-len(kept)} golden trades stood down)")


if __name__ == "__main__":
    main()
