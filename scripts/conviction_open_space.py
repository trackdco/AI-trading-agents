#!/usr/bin/env python3
"""CONVICTION SIZING ON OPEN-SPACE. Report-only, nothing adopted.

Open-space is BINARY, so there is no ladder to build — the honest object is
a single multiplier M on the open-space rows, layered ON TOP of the existing
size policy, never replacing it. Everything else stays at 1x.

BOTH READINGS, kept separate:
  A  COMBINED   incumbent + open-space, M applied to the open-space rows
  B  STANDALONE open-space alone, M applied to the whole stream

Multiplier sweep M in {1.0, 1.25, 1.5, 2.0, 2.5, 3.0}, full account lab per
multiplier, plus the Law-7 arithmetic computed FROM THE REAL LOSS
DISTRIBUTION rather than from an assumed -1R.

    python -m scripts.conviction_open_space
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.htf_ma_account_lab as AL                             # noqa: E402
from scripts.htf_ltf_report import (PAIRS as LP, assign as lassign,  # noqa: E402
                                    book as lbook, boot_mean, era)
from scripts.htf_room_gate import DD, FLOOR, grad                    # noqa: E402

OUT = ROOT / "output/htf_ma_census"
MULTS = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
SEED, YEAR = 20260807, 250


def lab(day_r, label, nd):
    w = float(day_r.min())
    ms = max(50.0, 50.0 * np.floor((DD / abs(w)) / 50.0)) if w < 0 else 600.
    g, dth, _ = grad(day_r, {"s_pre": ms, "s_post": ms})
    rng = np.random.default_rng(SEED)
    live = float(np.mean([
        (lambda x: sum(q for _, q in x["wd"]) - x["fees"])(
            AL.run_account(day_r, rng.integers(0, len(day_r), YEAR),
                           {"s_pre": ms, "s_post": ms},
                           payout_cap=10**9, payout_at=6000.))
        for _ in range(600)]))
    print(f"   {label:34s} {day_r.sum()/nd:7.3f} {w:8.2f} "
          f"{'$'+format(ms,'.0f'):>7s} {g*100:8.1f}% {dth*100:6.1f}% "
          f"{live:10,.0f} {day_r.sum()/nd*ms:9,.0f}")
    return dict(rday=day_r.sum()/nd, worst=w, ms=ms, grad=g, live=live,
                dpd=day_r.sum()/nd*ms)


def main() -> None:
    days = sorted(pd.read_parquet(OUT / "levels_fit.parquet")
                  .sess_day.unique())
    nd = len(days)
    INC = pd.read_parquet(OUT / "incumbent_london.parquet")
    inc_day = INC.groupby("sess_day").out_ship.sum().reindex(
        days, fill_value=0.0)
    T = pd.read_parquet(OUT / "ltf_fit.parquet")
    T["t"] = pd.to_datetime(T.t)
    T["era"] = era(T)
    T["scid"] = lassign(T, pd.read_parquet(LP), 0.5)
    B = lbook(T)
    OS = {tf: B[(B.tf == tf) & (B.session == "LONDON") & (B.arm == "reject")
               & (B.risk >= FLOOR) & B.next_lvl_R.isna()] for tf in (3, 5)}

    print("=" * 104)
    print("CONVICTION SIZING ON OPEN-SPACE. REPORT ONLY — nothing adopted.")
    print("=" * 104)
    print("\nOpen-space is BINARY. There is no 3+ tier ladder to build, so the")
    print("Phase-2 precondition (which required tier-to-tier differentiation)")
    print("does NOT apply and is not claimed. This is a single multiplier on a")
    print("binary condition, which is a different and weaker object.")

    # ------------------------------------------------------------------
    print("\n" + "=" * 104)
    print("LAW 7 ARITHMETIC, FROM THE REAL LOSS DISTRIBUTION")
    print("=" * 104)
    print("   What a multiplier M on a subset can be worth, before it is built.")
    print("   Book R/day(M) = R/day(base) + (M-1) x R/day(open-space).")
    print("   The constraint is the WORST DAY, which grows with M only on days")
    print("   the open-space stream actually lost — so it is read from the")
    print("   realised day-level loss distribution, not from an assumed -1R.\n")
    for tf in (3, 5):
        o = OS[tf]
        od = o.groupby("sess_day").out_ship.sum().reindex(days, fill_value=0.0)
        base = inc_day
        tot = base + od
        neg = od[od < 0]
        print(f"   TF={tf}m  open-space stream: {len(o)} trades, "
              f"{len(o)/nd:.2f}/day, EV {o.out_ship.mean():+.3f}")
        print(f"      R/day contribution        {od.sum()/nd:+.3f}  "
              f"(base book {base.sum()/nd:+.3f})")
        print(f"      days the stream LOST      {len(neg)} of {nd} "
              f"({len(neg)/nd*100:.1f}%)")
        print(f"      its loss days: mean {neg.mean():+.3f}R  "
              f"p05 {neg.quantile(.05):+.3f}R  worst {neg.min():+.3f}R")
        wd = tot.idxmin()
        print(f"      book worst day {tot.min():+.3f}R on {wd}; the stream "
              f"contributed {od[wd]:+.3f}R of it")
        for M in (1.5, 2.0, 3.0):
            t2 = base + M * od
            print(f"      M={M:<4} -> R/day {t2.sum()/nd:+.3f} "
                  f"({(t2.sum()/nd)/(tot.sum()/nd)-1:+.1%}), worst day "
                  f"{t2.min():+.3f}R "
                  f"({t2.min()/tot.min()-1:+.1%} deeper)")
        print()

    # ------------------------------------------------------------------
    for reading, label in (("A", "COMBINED — incumbent + open-space, M on "
                                 "the open-space rows only"),
                           ("B", "STANDALONE — open-space alone, M on the "
                                 "whole stream")):
        print("=" * 104)
        print(f"READING {reading}: {label}")
        print("=" * 104)
        print(f"   {'config':34s} {'R/day':>7s} {'worst':>8s} {'maxsz':>7s} "
              f"{'SIM grad':>8s} {'death':>6s} {'LIVE $/yr':>10s} {'$/day':>9s}")
        for tf in (3, 5):
            od = OS[tf].groupby("sess_day").out_ship.sum().reindex(
                days, fill_value=0.0)
            for M in MULTS:
                dr = ((inc_day + M * od) if reading == "A"
                      else (M * od)).to_numpy()
                lab(dr, f"{tf}m  M={M}", nd)
            print()

    print("=" * 104)
    print("SIZE-NEUTRAL COMPARISON — the only fair one")
    print("=" * 104)
    print("   Raising M raises R/day AND deepens the worst day, which lowers")
    print("   the max non-breaching size. $/day = R/day x max size holds both")
    print("   ends and is the column to read.\n")
    for tf in (3, 5):
        od = OS[tf].groupby("sess_day").out_ship.sum().reindex(
            days, fill_value=0.0)
        print(f"   {'TF='+str(tf)+'m':10s} " + " ".join(
            f"{'M='+str(M):>12s}" for M in MULTS))
        row = []
        for M in MULTS:
            dr = (inc_day + M * od).to_numpy()
            w = float(dr.min())
            ms = max(50.0, 50.0*np.floor((DD/abs(w))/50.0)) if w < 0 else 600.
            row.append(f"${dr.sum()/nd*ms:,.0f}")
        print(f"   {'$/day':10s} " + " ".join(f"{c:>12s}" for c in row))
        best = MULTS[int(np.argmax([float(x[1:].replace(',', ''))
                                    for x in row]))]
        print(f"   -> best M on $/day: {best}\n")


if __name__ == "__main__":
    main()
