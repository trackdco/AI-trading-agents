#!/usr/bin/env python3
"""PHASE 0 — overlap, the full 12-cell table, and the combination run.

Report-only. Nothing here ships.

  1  SCHEMA RECONCILIATION, stated before anything is computed
  2  OVERLAP, two separate measurements:
       redundancy  — same locus + same direction within 5 minutes
       concurrency — do the two positions' OPEN INTERVALS overlap
     If redundancy < 50% -> simple union, number stated. If high -> STOP,
     report, and do NOT invent a dedup rule overnight.
  3  the FULL 12-cell room-gate table, point estimates AND CIs for all 12
  4  COMBINATION: incumbent + the AS-TRADED room-gated LONDON reject
     stream only, through the full account lab

    python -m scripts.phase0_overlap
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.htf_ma_account_lab as AL                             # noqa: E402
from scripts.htf_ltf_report import (PAIRS as LPAIRS, assign as         # noqa: E402
                                    lassign, book as lbook, boot_lift,
                                    boot_mean, era)
from scripts.htf_ma_level_report import PAIRS, assign, book          # noqa: E402
from scripts.htf_room_gate import DD, FLOOR, THR, admissible, grad   # noqa: E402

OUT = ROOT / "output/htf_ma_census"
SESSIONS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (570, 630)}
NEAR = 5                         # minutes, the declared redundancy radius
SEED = 20260807


def hm(d):
    t = pd.to_datetime(d.t)
    return t.dt.hour * 60 + t.dt.minute


def incumbent() -> pd.DataFrame:
    """The BR-16/BR-23 composite, rebuilt from levels_fit so it CARRIES
    locus and t_exit (bc_frame has neither), then joined to bc_frame's
    features. Calibrated against bc_frame before use."""
    F = pd.read_parquet(OUT / "levels_fit.parquet")
    F5 = F.join(assign(F, pd.read_parquet(PAIRS), 0.5))
    ub = pd.concat([book(F5[F5.locus == "val"], "break"),
                    book(F5[F5.locus == "vwap_m1"], "break")]) \
        .drop_duplicates(["sess_day", "t", "side"]).assign(pop="union_break")
    rej = book(F5[F5.locus == "bbma15"], "reject").assign(pop="reject")
    comp = pd.concat([ub, rej], ignore_index=True)
    comp["t"] = pd.to_datetime(comp.t)
    for c in ("t_entry", "t_exit"):
        comp[c] = pd.to_datetime(comp[c])
    return comp


def main() -> None:
    print("=" * 78)
    print("PHASE 0 — OVERLAP, 12-CELL TABLE, COMBINATION.  REPORT ONLY.")
    print("=" * 78)

    # ------------------------------------------------------------ 1 -----
    print("\n" + "=" * 78)
    print("1. SCHEMA RECONCILIATION — stated before anything is run")
    print("=" * 78)
    C = pd.read_parquet(OUT / "bc_frame.parquet")
    C["t"] = pd.to_datetime(C.t)
    INC = incumbent()
    k = ["sess_day", "t", "side", "pop"]
    a = set(map(tuple, INC[k].astype(str).to_numpy()))
    b = set(map(tuple, C[k].astype(str).to_numpy()))
    print(f"   MISMATCH 1: bc_frame (the incumbent feature table) carries NO "
          f"`locus` and NO `t_exit`.")
    print(f"     -> rebuilt the composite from levels_fit, which has both.")
    print(f"        calibration vs bc_frame on (day,t,side,pop): "
          f"rebuilt {len(a)}, bc_frame {len(b)}, "
          f"identical={'YES' if a == b else 'NO'} "
          f"(only-rebuilt {len(a-b)}, only-bc {len(b-a)})")
    print(f"   MISMATCH 2: ltf_fit has geometry+D7 but NO flow/depth; "
          f"ltf_flow has the 12 flow features but no geometry. Joined on "
          f"(day,t,tf,locus,arm,side).")
    print(f"   MISMATCH 3: the DEPTH SIX exist ONLY on bc_frame. The LTF "
          f"population has no depth columns at all.")
    print(f"     -> Phase 1 can diagnose depth on the INCUMBENT only unless "
          f"depth is built for the LTF rows. Stated, not silently dropped.")
    print(f"   MISMATCH 4: `next_lvl_R` and the ceiling flags exist ONLY on "
          f"ltf_fit. The incumbent has no D7 geometry.")
    print(f"   MISMATCH 5 (CONVENTION, the important one): the incumbent's "
          f"BREAK arm enters on a RETEST of the level; the room-gated LTF "
          f"stream enters at the NEXT 1m OPEN. Combining them mixes two "
          f"entry conventions. The reject arms match (both next-1m-open).")

    INC = INC.merge(C.drop(columns=[c for c in C.columns
                                    if c in ("locus", "t_exit", "arm",
                                             "direction", "out_ship", "risk",
                                             "mfe_r", "w15", "session",
                                             "scid", "entry", "t_entry")]),
                    on=["sess_day", "t", "side", "pop"], how="left")
    INC["hm"] = hm(INC)
    INC["era"] = era(INC)
    SB = pd.read_parquet(OUT / "sweepb_london_frame.parquet")
    SB["t"] = pd.to_datetime(SB.t)
    SB["hm"] = hm(SB)
    SB["era"] = era(SB)
    a_, b_ = SESSIONS["LONDON"]
    inc_ldn = pd.concat([INC[(INC.hm >= a_) & (INC.hm <= b_)],
                         SB[(SB.hm >= a_) & (SB.hm <= b_)].assign(
                             pop="sweep_b", locus="sweep_b")],
                        ignore_index=True).drop_duplicates(
        ["sess_day", "t", "side"])
    print(f"\n   incumbent LONDON book (composite + sweep_b): "
          f"{len(inc_ldn)} fights")

    # room-gated stream, AS-TRADED construction
    T = pd.read_parquet(OUT / "ltf_fit.parquet")
    T["t"] = pd.to_datetime(T.t)
    T["era"] = era(T)
    T["scid"] = lassign(T, pd.read_parquet(LPAIRS), 0.5)
    B = lbook(T)
    for c in ("t_entry", "t_exit"):
        B[c] = pd.to_datetime(B[c])
    ROOM = B[(B.risk >= FLOOR) & admissible(B)]          # as-traded gate
    nd = T.sess_day.nunique()

    # ------------------------------------------------------------ 2 -----
    print("\n" + "=" * 78)
    print("2. OVERLAP — two separate measurements")
    print("=" * 78)
    print(f"   REDUNDANCY: a room-gated trade is redundant if an INCUMBENT "
          f"trade exists at the\n   SAME LOCUS, SAME DIRECTION, entry within "
          f"{NEAR} minutes.")
    print(f"   CONCURRENCY: separately, do the two positions' OPEN INTERVALS "
          f"[t_entry, t_exit] overlap.\n")
    inc_l = inc_ldn.copy()
    inc_l["t_entry"] = pd.to_datetime(inc_l.t_entry)
    inc_l["t_exit"] = pd.to_datetime(inc_l.t_exit)
    print(f"   {'stream':22s} {'n':>5s} {'redundant':>10s} {'concurrent':>11s}"
          f" {'new':>6s}")
    streams = {}
    for tf in (3, 5):
        R = ROOM[(ROOM.tf == tf) & (ROOM.session == "LONDON")
                 & (ROOM.arm == "reject")].copy()
        red = con = 0
        for r in R.itertuples():
            cand = inc_l[(inc_l.sess_day == r.sess_day)
                         & (inc_l.direction == r.direction)]
            if not len(cand):
                continue
            same = cand[cand.locus == r.locus]
            if len(same) and (abs((same.t_entry - r.t_entry)
                                  .dt.total_seconds()) <= NEAR * 60).any():
                red += 1
            ov = (cand.t_entry <= r.t_exit) & (cand.t_exit >= r.t_entry)
            if ov.any():
                con += 1
        streams[tf] = R
        print(f"   LONDON reject {tf}m{'':7s} {len(R):5d} "
              f"{red/max(len(R),1)*100:9.1f}% {con/max(len(R),1)*100:10.1f}% "
              f"{(len(R)-red)/max(len(R),1)*100:5.1f}%")
    # 3m vs 5m redundancy inside the room stream itself
    R3, R5 = streams[3], streams[5]
    r35 = 0
    for r in R5.itertuples():
        c = R3[(R3.sess_day == r.sess_day) & (R3.direction == r.direction)
               & (R3.locus == r.locus)]
        if len(c) and (abs((c.t_entry - r.t_entry).dt.total_seconds())
                       <= NEAR * 60).any():
            r35 += 1
    print(f"\n   INTERNAL: {r35/max(len(R5),1)*100:.1f}% of the 5m stream is "
          f"redundant with the 3m stream")
    print(f"   -> a CROSS-TF union still has no declared dedup rule, so the "
          f"combination below\n      is run with the 3m stream and the 5m "
          f"stream SEPARATELY, never unioned.")

    # ------------------------------------------------------------ 3 -----
    print("\n" + "=" * 78)
    print("3. THE FULL 12-CELL ROOM-GATE TABLE — all cells, estimates AND CIs")
    print("=" * 78)
    print(f"   {'sess':7s} {'tf':>3s} {'arm':6s} {'n_base':>7s} {'n_keep':>7s} "
          f"{'lift':>8s} {'H2 lift CI':>20s} {'H1 lift CI':>20s} "
          f"{'win k/c':>13s}  bar")
    for tf in (3, 5):
        for s in SESSIONS:
            for arm in ("reject", "break"):
                d = B[(B.tf == tf) & (B.session == s) & (B.arm == arm)
                      & (B.risk >= FLOOR)]
                kk = d[admissible(d)]
                cut = d.drop(kk.index, errors="ignore")
                if len(d) < 40 or len(kk) < 15:
                    print(f"   {s:7s} {tf:3d} {arm:6s} {len(d):7d} "
                          f"{len(kk):7d}  UNDERPOWERED")
                    continue
                lift = kk.out_ship.mean() - d.out_ship.mean()
                cis, ok = [], []
                for e in ("H2-2025", "H1-2026"):
                    lo, hi = boot_lift(d[d.era == e], kk[kk.era == e])
                    cis.append(f"[{lo:+.3f},{hi:+.3f}]" + ("!" if lo > 0 else " "))
                    ok.append(np.isfinite(lo) and lo > 0)
                print(f"   {s:7s} {tf:3d} {arm:6s} {len(d):7d} {len(kk):7d} "
                      f"{lift:+8.3f} {cis[0]:>20s} {cis[1]:>20s} "
                      f"{(kk.out_ship>0).mean()*100:5.1f}/"
                      f"{(cut.out_ship>0).mean()*100:5.1f}%  "
                      f"{'PASS' if (lift>=0.05 and all(ok)) else 'miss'}")

    # ------------------------------------------------------------ 4 -----
    print("\n" + "=" * 78)
    print("4. COMBINATION — incumbent LONDON + as-traded room-gated LONDON "
          "reject")
    print("   (LONDON only. NY is NOT combined, whatever the table above "
          "shows — it needs its own declaration.)")
    print("=" * 78)
    days = sorted(pd.read_parquet(OUT / "levels_fit.parquet").sess_day.unique())
    pols = (("flat @own max", None),
            ("cushion k=.05", {"s_pre": 150., "mode": "cushion", "k": 0.05,
                               "s_min": 150., "s_max": 300.}))
    print(f"   {'book':26s} {'n':>5s} {'/day':>6s} {'EV':>7s} "
          f"{'worst dayR':>10s} {'maxsize':>8s} {'GRAD@own':>9s} "
          f"{'GRAD cush':>10s} {'death':>7s} {'net':>9s}")

    def score(bk, label):
        dr = bk.groupby("sess_day").out_ship.sum().reindex(
            days, fill_value=0.0).to_numpy()
        w = float(dr.min())
        ms = max(50.0, 50.0 * np.floor((DD / abs(w)) / 50.0)) if w < 0 else 600.
        g1, d1, _ = grad(dr, {"s_pre": ms, "s_post": ms})
        g2, d2, n2 = grad(dr, pols[1][1])
        print(f"   {label:26s} {len(bk):5d} {len(bk)/len(days):6.2f} "
              f"{bk.out_ship.mean():+7.3f} {w:10.2f} "
              f"{'$'+format(ms,'.0f'):>8s} {g1*100:8.1f}% {g2*100:9.1f}% "
              f"{d2*100:6.1f}% {n2:9,.0f}")
        return dict(n=len(bk), fpd=len(bk)/len(days), ev=bk.out_ship.mean(),
                    worst=w, ms=ms, g_own=g1, g_cush=g2, death=d2, net=n2)

    base = score(inc_ldn, "incumbent LONDON")
    res = {}
    for tf in (3, 5):
        R = streams[tf]
        U = pd.concat([inc_ldn.assign(src="inc"),
                       R.assign(src=f"room{tf}m")], ignore_index=True)
        score(R, f"  room-gated {tf}m alone")
        res[tf] = score(U, f"COMBINED inc + room {tf}m")
    print("\n   deltas vs the incumbent alone:")
    for tf, r in res.items():
        print(f"     +room{tf}m: /day {r['fpd']-base['fpd']:+.2f}  "
              f"EV {r['ev']-base['ev']:+.3f}  worst dayR "
              f"{r['worst']-base['worst']:+.2f}  max size "
              f"{r['ms']-base['ms']:+,.0f}  GRAD@own "
              f"{(r['g_own']-base['g_own'])*100:+.1f}pp  GRAD cush "
              f"{(r['g_cush']-base['g_cush'])*100:+.1f}pp")

    for tf in (3, 5):
        pd.concat([inc_ldn.assign(src="inc"),
                   streams[tf].assign(src=f"room{tf}m")],
                  ignore_index=True).to_parquet(
            OUT / f"combined_london_{tf}m.parquet", index=False)
    inc_ldn.to_parquet(OUT / "incumbent_london.parquet", index=False)
    ROOM.to_parquet(OUT / "room_gated.parquet", index=False)
    print("\n   written: incumbent_london / room_gated / combined_london_{3,5}m")


if __name__ == "__main__":
    main()
