#!/usr/bin/env python3
"""Compare baseline vs fixed champion journals to measure the entry-timing fix's impact."""
import sys
import pandas as pd
import os as _os
S=_os.environ.get("LONDON_SCRATCH", _os.path.expanduser("~/london_out"))
WT=_os.environ.get("LONDON_WT", f"{S}/canon_wt")
_os.makedirs(S, exist_ok=True)
def summ(J, label):
    w = (J.r > 0).mean() * 100
    print(f"  {label:9s} {len(J):3d}t  ${J.dollars.sum():+8,.0f}  win {w:4.1f}%  "
          f"netR {J.r.sum():+6.1f}  exp {J.r.mean():+.3f}R")
    return dict(n=len(J), d=J.dollars.sum(), w=w, R=J.r.sum(), e=J.r.mean())


def main():
    B = pd.read_csv(f"{S}/champ_baseline.csv")
    F = pd.read_csv(f"{S}/champ_fixed.csv")
    print("=" * 68)
    print("ENTRY-TIMING FIX — champion (E3+V8 non-WAR / E4 WAR, 08:00-10:15, max2/day)")
    print("=" * 68)
    b = summ(B, "BASELINE"); f = summ(F, "FIXED")
    print(f"\n  DELTA    {f['n']-b['n']:+3d}t  ${f['d']-b['d']:+8,.0f}  "
          f"win {f['w']-b['w']:+4.1f}pp  netR {f['R']-b['R']:+6.1f}  exp {f['e']-b['e']:+.3f}R")

    print("\nBY ARM:")
    for arm in ["E3", "E4"]:
        print(f"  [{arm}]")
        summ(B[B.arm == arm], "  base"); summ(F[F.arm == arm], "  fixed")
    print("\nBY MONTH (net $ base -> fixed):")
    for m in sorted(set(B.mo) | set(F.mo)):
        bd, fd = B[B.mo == m].dollars.sum(), F[F.mo == m].dollars.sum()
        bn, fn = (B.mo == m).sum(), (F.mo == m).sum()
        print(f"  {m}: {bn:2d}t ${bd:+7,.0f}  ->  {fn:2d}t ${fd:+7,.0f}   (Δ${fd-bd:+,.0f})")

    print("\nEXIT-REASON MIX (baseline -> fixed):")
    br = B.reason.value_counts(); fr = F.reason.value_counts()
    for k in sorted(set(br.index) | set(fr.index)):
        print(f"  {k:28s} {br.get(k,0):3d} -> {fr.get(k,0):3d}")

    # rough trade match on (date, arm, dir) to find added/removed days
    bk = B.groupby(["date", "arm", "dir"]).size()
    fk = F.groupby(["date", "arm", "dir"]).size()
    only_f = fk.index.difference(bk.index)
    only_b = bk.index.difference(fk.index)
    print(f"\n(date,arm,dir) groups only in FIXED (fix added): {len(only_f)}")
    print(f"(date,arm,dir) groups only in BASELINE (fix removed): {len(only_b)}")


if __name__ == "__main__":
    main()
