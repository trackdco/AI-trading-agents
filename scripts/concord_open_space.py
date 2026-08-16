#!/usr/bin/env python3
"""CONCORD>=7 x OPEN-SPACE, the conditional trail, and the open items.

  2  redundancy between the two conditions FIRST, then the conjunction:
     fights/day, own EV, blended EV, split-half, full account lab
  3  the CONDITIONAL TRAIL as ONE rule — 15m when no level ahead, the
     trigger's own timeframe when there is
  4a three-way including the weak >=3R-ONLY component on its own
  4b open-space-specific 3m-vs-5m redundancy, measured fresh

CONCORD convention, stated: the count is computed on the FULL London
reject stream at each TF (the natural parent), then subset — so ">=7"
means the same thing it meant in BR-26 rather than being re-based on a
subpopulation's own medians.

    python -m scripts.concord_open_space
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.htf_ma_account_lab as AL                             # noqa: E402
from scripts.htf_ltf_flow import concord                            # noqa: E402
from scripts.htf_ltf_report import (PAIRS as LP, assign as lassign,  # noqa: E402
                                    book as lbook, boot_mean, era)
from scripts.htf_room_gate import DD, FLOOR, grad                    # noqa: E402

OUT = ROOT / "output/htf_ma_census"
SEED, YEAR, NEAR = 20260807, 250, 5
CC = 7


def dboot(df, col, draws=2000):
    g = df.groupby("sess_day")[col].agg(["sum", "size"])
    s, n = g["sum"].to_numpy(), g["size"].to_numpy()
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(s), (draws, len(s)))
    c = n[i].sum(1)
    st = np.divide(s[i].sum(1), c, out=np.full(draws, np.nan), where=c > 0)
    return float(np.nanpercentile(st, 2.5)), float(np.nanpercentile(st, 97.5))


def score(day_r, label, nd):
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
    print(f"   {label:38s} {day_r.sum()/nd:7.3f} {w:7.2f} "
          f"{'$'+format(ms,'.0f'):>7s} {g*100:8.1f}% {dth*100:6.1f}% "
          f"{live:10,.0f}")
    return dict(rday=day_r.sum()/nd, worst=w, ms=ms, grad=g, live=live)


def main() -> None:
    days = sorted(pd.read_parquet(OUT / "levels_fit.parquet")
                  .sess_day.unique())
    nd = len(days)
    INC = pd.read_parquet(OUT / "incumbent_london.parquet")
    INC["t"] = pd.to_datetime(INC.t)
    INC["t_entry"] = pd.to_datetime(INC.t_entry)
    inc_day = INC.groupby("sess_day").out_ship.sum().reindex(
        days, fill_value=0.0)

    T = pd.read_parquet(OUT / "ltf_fit.parquet")
    T["t"] = pd.to_datetime(T.t)
    FL = pd.read_parquet(OUT / "ltf_flow.parquet")
    FL["t"] = pd.to_datetime(FL.t)
    T = T.merge(FL, on=["sess_day", "t", "tf", "locus", "arm", "side"],
                how="left")
    T["era"] = era(T)
    T["scid"] = lassign(T, pd.read_parquet(LP), 0.5)
    B = lbook(T)
    ST = pd.read_parquet(OUT / "structural_target.parquet")
    ST["t"] = pd.to_datetime(ST.t)

    S = {}
    for tf in (3, 5):
        g = B[(B.tf == tf) & (B.session == "LONDON") & (B.arm == "reject")
              & (B.risk >= FLOOR) & B.flowconf.notna()].copy()
        g["cc"] = concord(g).to_numpy()          # computed on the PARENT
        g["open"] = g.next_lvl_R.isna()
        g["hicc"] = g.cc >= CC
        # V1 == out_ship exactly (verified 0.00e+00), and out_ship is
        # COMPLETE on this population, whereas structural_target holds only
        # the ROOM-GATED subset (25.6% of these rows). Merging v1 from there
        # would silently NaN three quarters of the book.
        g["v1"] = g.out_ship
        # MERGE KEY MUST INCLUDE LOCUS. (sess_day, t, side) carries up to
        # 4 rows here — the same minute can trigger at several loci — so a
        # 3-key merge silently duplicates rows and inflates every downstream
        # count. Asserted, not assumed.
        stk = ST[ST.book == f"ROOM-GATED {tf}m"][
            ["sess_day", "t", "side", "locus", "v2"]]
        assert not stk.duplicated(["sess_day", "t", "side", "locus"]).any()
        n0 = len(g)
        g = g.merge(stk, on=["sess_day", "t", "side", "locus"], how="left")
        assert len(g) == n0, f"merge changed row count {n0} -> {len(g)}"
        S[tf] = g

    print("=" * 104)
    print("CONCORD>=7 x OPEN-SPACE, THE CONDITIONAL TRAIL, AND THE OPEN "
          "ITEMS. REPORT ONLY.")
    print("=" * 104)

    # ------------------------------------------------------------ 2a ---
    print("\n" + "=" * 104)
    print("2a. REDUNDANCY BETWEEN THE TWO CONDITIONS — checked, not assumed")
    print("    (entry-bar flow agreement vs whether a level lies ahead — "
          "different questions)")
    print("=" * 104)
    for tf in (3, 5):
        g = S[tf]
        a, b = g.hicc, g["open"]
        n11 = int((a & b).sum()); n10 = int((a & ~b).sum())
        n01 = int((~a & b).sum()); n00 = int((~a & ~b).sum())
        p_o = b.mean(); p_o_cc = b[a].mean() if a.any() else np.nan
        phi = ((n11*n00 - n10*n01)
               / np.sqrt(max((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00), 1)))
        print(f"\n   TF={tf}m  n={len(g)}")
        print(f"      {'':16s} {'open':>8s} {'level ahead':>12s}")
        print(f"      {'CONCORD>=7':16s} {n11:8d} {n10:12d}")
        print(f"      {'CONCORD<7':16s} {n01:8d} {n00:12d}")
        print(f"      P(open) = {p_o*100:.1f}%  |  P(open | CC>=7) = "
              f"{p_o_cc*100:.1f}%   phi = {phi:+.3f}")
        print(f"      -> {'INDEPENDENT ENOUGH TO STACK' if abs(phi) < 0.2 else 'CORRELATED — the conjunction is not two independent bites'}")

    # ------------------------------------------------------------ 2b ---
    print("\n" + "=" * 104)
    print("2b. THE FOUR CELLS, and the conjunction")
    print("=" * 104)
    for tf in (3, 5):
        g = S[tf]
        print(f"\n   -- TF={tf}m   (exit = V1 shipped/15m trail)")
        print(f"      {'cell':28s} {'n':>4s} {'/day':>6s} {'EV':>8s} "
              f"{'day-boot 95%':>20s}")
        for nm, sub in (("CC>=7 AND open  [conj]", g[g.hicc & g["open"]]),
                        ("CC>=7 only (level ahead)", g[g.hicc & ~g["open"]]),
                        ("open only (CC<7)", g[~g.hicc & g["open"]]),
                        ("neither", g[~g.hicc & ~g["open"]]),
                        ("-- open-space, all CC", g[g["open"]]),
                        ("-- CC>=7, all room", g[g.hicc])):
            if len(sub) < 5:
                print(f"      {nm:28s} {len(sub):4d}  thin")
                continue
            lo, hi = boot_mean(sub, "v1")
            print(f"      {nm:28s} {len(sub):4d} {len(sub)/nd:6.2f} "
                  f"{sub.v1.mean():+8.3f} [{lo:+.3f},{hi:+.3f}]"
                  + ("!" if lo > 0 else ""))

    # split-half on the conjunction
    print("\n   split-half on the CONJUNCTION (frozen split, seed 20260807, "
          "all 292 fit days)")
    rng = np.random.default_rng(SEED)
    H1 = set(np.array(days)[rng.permutation(len(days))[:len(days) // 2]])
    print(f"      {'pop':16s} {'H1 n':>5s} {'H1 EV':>8s} {'H1 95%':>20s} "
          f"{'H2 n':>5s} {'H2 EV':>8s} {'H2 95%':>20s}  verdict")
    for tf in (3, 5):
        c = S[tf][S[tf].hicc & S[tf]["open"]]
        a, b = c[c.sess_day.isin(H1)], c[~c.sess_day.isin(H1)]
        if len(a) < 5 or len(b) < 5:
            print(f"      conj {tf}m{'':9s} n1={len(a)} n2={len(b)} "
                  f"TOO THIN TO SPLIT")
            continue
        la, ha = dboot(a, "v1")
        lb, hb = dboot(b, "v1")
        ok = (np.sign(b.v1.mean()) == np.sign(a.v1.mean())
              and abs(b.v1.mean()) >= 0.5 * abs(a.v1.mean()))
        print(f"      conj {tf}m{'':9s} {len(a):5d} {a.v1.mean():+8.3f} "
              f"[{la:+.3f},{ha:+.3f}] {len(b):5d} {b.v1.mean():+8.3f} "
              f"[{lb:+.3f},{hb:+.3f}]  {'CONFIRMS' if ok else 'FAILS'}")

    # ------------------------------------------------------------ 3 ----
    print("\n" + "=" * 104)
    print("3. THE CONDITIONAL TRAIL AS ONE RULE — 15m when no level ahead, "
          "trigger TF when there is")
    print("=" * 104)
    print(f"   {'pop':16s} {'n':>4s} {'all-V1':>8s} {'all-V2':>8s} "
          f"{'CONDITIONAL':>12s} {'cond 95%':>20s} {'vs best fixed':>13s}")
    print("   NOTE: V2 exists only on the ROOM-GATED subset (the trail was "
          "only re-walked there),")
    print("   so this rule is evaluated on that population and the row count "
          "reflects it.")
    for tf in (3, 5):
        g = S[tf].dropna(subset=["v1", "v2"]).copy()
        g["cond"] = np.where(g["open"], g.v1, g.v2)
        lo, hi = boot_mean(g, "cond")
        best = max(g.v1.mean(), g.v2.mean())
        print(f"   room {tf}m{'':9s} {len(g):4d} {g.v1.mean():+8.3f} "
              f"{g.v2.mean():+8.3f} {g['cond'].mean():+12.3f} "
              f"[{lo:+.3f},{hi:+.3f}] {g['cond'].mean()-best:+13.3f}")
        n0 = len(S[tf])
        S[tf] = S[tf].merge(g[["sess_day", "t", "side", "locus", "cond"]],
                            on=["sess_day", "t", "side", "locus"], how="left")
        assert len(S[tf]) == n0, f"cond merge changed rows {n0}->{len(S[tf])}"

    # ------------------------------------------------------------ 4b ---
    print("\n" + "=" * 104)
    print("4b. OPEN-SPACE-SPECIFIC 3m vs 5m REDUNDANCY — measured fresh")
    print("    (the bundled population measured 41.9%; NOT assumed to carry)")
    print("=" * 104)
    o3 = S[3][S[3]["open"]].copy()
    o5 = S[5][S[5]["open"]].copy()
    for D in (o3, o5):
        D["t_entry"] = pd.to_datetime(D.t_entry)
    red = 0
    for r in o5.itertuples():
        c = o3[(o3.sess_day == r.sess_day) & (o3.direction == r.direction)
               & (o3.locus == r.locus)]
        if len(c) and (abs((c.t_entry - r.t_entry).dt.total_seconds())
                       <= NEAR * 60).any():
            red += 1
    print(f"   open-space 5m rows redundant with open-space 3m: "
          f"{red}/{len(o5)} = {red/max(len(o5),1)*100:.1f}%")
    print(f"   (bundled equivalent was 41.9%) -> "
          f"{'LOWER — the two open-space streams are more distinct' if red/max(len(o5),1) < 0.419 else 'similar or higher'}")

    # ------------------------------------------------------------ 4a ---
    print("\n" + "=" * 104)
    print("4a + 2c. ACCOUNT LAB — every component on its own, then combined")
    print("=" * 104)
    print(f"   {'book':38s} {'R/day':>7s} {'worst':>7s} {'maxsz':>7s} "
          f"{'SIM grad':>8s} {'death':>6s} {'LIVE $/yr':>10s}")
    res = {}
    res["inc"] = score(inc_day.to_numpy(), "1. incumbent alone", nd)
    for tf in (3, 5):
        g = S[tf]
        comps = (("open-space", g[g["open"]]),
                 (">=3R-ONLY (the weak arm)", g[~g["open"]]),
                 ("BUNDLED (open + >=3R)", g),
                 ("CONCORD>=7 AND open  [conj]", g[g.hicc & g["open"]]),
                 ("CONCORD>=7 OR open   [union]", g[g.hicc | g["open"]]))
        for nm, sub in comps:
            if len(sub) < 10:
                continue
            dr = (inc_day + sub.groupby("sess_day").v1.sum().reindex(
                days, fill_value=0.0)).to_numpy()
            res[f"{nm[:6]}{tf}"] = score(
                dr, f"inc + {nm} {tf}m ({len(sub)/nd:.2f}/d)", nd)
        # the conditional-trail version of the bundled stream
        dr = (inc_day + g.groupby("sess_day")["cond"].sum().reindex(
            days, fill_value=0.0)).to_numpy()
        score(dr, f"inc + BUNDLED {tf}m, CONDITIONAL trail", nd)

    print("\n   BLENDED EV of each combined book (incumbent rows + stream "
          "rows, one pooled mean):")
    for tf in (3, 5):
        g = S[tf]
        for nm, sub in (("open-space", g[g["open"]]),
                        ("CC>=7 AND open", g[g.hicc & g["open"]]),
                        ("CC>=7 OR open", g[g.hicc | g["open"]])):
            if len(sub) < 10:
                continue
            allr = np.concatenate([INC.out_ship.to_numpy(),
                                   sub.v1.to_numpy()])
            print(f"     {tf}m {nm:18s} n={len(allr):4d} "
                  f"{len(allr)/nd:5.2f}/day  blended EV "
                  f"{np.nanmean(allr):+.3f}")


if __name__ == "__main__":
    main()
