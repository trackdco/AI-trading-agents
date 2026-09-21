#!/usr/bin/env python3
"""OPEN-SPACE RESTATEMENT — DECLARATIONS-open-space.md, written first.

Population: rows with NO other locus ahead of entry in the trade direction
as-of the decision bar (`next_lvl_R` undefined). Not "a lot of room" — no
obstacle at all. LONDON reject, TF 3m/5m, risk>=2pt, X=0.5W.

    python -m scripts.open_space
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.htf_ma_account_lab as AL                             # noqa: E402
from scripts.htf_ltf_report import (PAIRS as LP, XS, assign as       # noqa: E402
                                    lassign, book as lbook, boot_mean, era)
from scripts.htf_room_gate import DD, FLOOR, admissible, grad        # noqa: E402

OUT = ROOT / "output/htf_ma_census"
SEED, YEAR, NEAR = 20260807, 250, 5
COST = 0.5


def dboot(df, col="v", draws=2000):
    g = df.groupby("sess_day")[col].agg(["sum", "size"])
    s, n = g["sum"].to_numpy(), g["size"].to_numpy()
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(s), (draws, len(s)))
    c = n[i].sum(1)
    st = np.divide(s[i].sum(1), c, out=np.full(draws, np.nan), where=c > 0)
    return float(np.nanpercentile(st, 2.5)), float(np.nanpercentile(st, 97.5))


def score(bk, days, col, label, nd):
    dr = bk.groupby("sess_day")[col].sum().reindex(
        days, fill_value=0.0).to_numpy()
    w = float(dr.min())
    ms = max(50.0, 50.0 * np.floor((DD / abs(w)) / 50.0)) if w < 0 else 600.
    g, dth, _ = grad(dr, {"s_pre": ms, "s_post": ms})
    rng = np.random.default_rng(SEED)
    live = float(np.mean([
        (lambda x: sum(q for _, q in x["wd"]) - x["fees"])(
            AL.run_account(dr, rng.integers(0, len(dr), YEAR),
                           {"s_pre": ms, "s_post": ms},
                           payout_cap=10**9, payout_at=6000.))
        for _ in range(600)]))
    print(f"   {label:34s} {len(bk):5d} {len(bk)/nd:6.2f} "
          f"{bk[col].mean():+8.3f} {dr.sum()/nd:7.3f} {w:7.2f} "
          f"{'$'+format(ms,'.0f'):>7s} {g*100:8.1f}% {dth*100:6.1f}% "
          f"{live:10,.0f}")
    return dict(n=len(bk), fpd=len(bk)/nd, ev=bk[col].mean(),
                rday=dr.sum()/nd, worst=w, ms=ms, grad=g, live=live)


def main() -> None:
    days = sorted(pd.read_parquet(OUT / "levels_fit.parquet")
                  .sess_day.unique())
    nd = len(days)
    ST = pd.read_parquet(OUT / "structural_target.parquet")   # has v1 and v2
    ST["era"] = era(ST)
    INC = pd.read_parquet(OUT / "incumbent_london.parquet")
    INC["t"] = pd.to_datetime(INC.t)
    INC["t_entry"] = pd.to_datetime(INC.t_entry)

    print("=" * 100)
    print("OPEN-SPACE RESTATEMENT — DECLARATIONS-open-space.md. REPORT ONLY.")
    print("=" * 100)
    print("\nWhat yesterday's §2 open-space numbers were computed under: the V1")
    print("SHIPPED exit (75%@3R, trail on the 15m BB MA). Confirmed from the")
    print("source frame — the decomposition used the `v1` column throughout.")

    OS = {tf: ST[(ST.book == f"ROOM-GATED {tf}m") & ST.next_lvl_R.isna()]
          for tf in (3, 5)}

    # ------------------------------------------------------------ §2 ----
    print("\n" + "=" * 100)
    print("1. THE CONFIRMATION — frozen split, seed 20260807, over the FULL "
          "fit day universe")
    print("   Bar: Half 2 agrees in SIGN and is >= HALF the Half-1 magnitude. "
          "Pooled is not a confirmation.")
    print("=" * 100)
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(days))
    H1 = set(np.array(days)[perm[:len(days) // 2]])
    print(f"   split: {len(H1)} days in Half 1, {nd-len(H1)} in Half 2 "
          f"(defined on all {nd} fit days, so it does not move with the "
          f"population)")
    for exit_col, exn in (("v1", "V1 shipped/15m trail"),
                          ("v2", "V2 trail on trigger TF")):
        print(f"\n   -- exit {exn}")
        print(f"      {'pop':14s} {'n':>4s} {'H1 n':>5s} {'H1 EV':>8s} "
              f"{'H1 95%':>20s} {'H2 n':>5s} {'H2 EV':>8s} {'H2 95%':>20s}"
              f"  verdict")
        for tf in (3, 5):
            g = OS[tf].rename(columns={exit_col: "v"})
            a = g[g.sess_day.isin(H1)]
            b = g[~g.sess_day.isin(H1)]
            la, ha = dboot(a)
            lb, hb = dboot(b)
            ok = (np.sign(b.v.mean()) == np.sign(a.v.mean())) and \
                 (abs(b.v.mean()) >= 0.5 * abs(a.v.mean()))
            print(f"      open {tf}m{'':7s} {len(g):4d} {len(a):5d} "
                  f"{a.v.mean():+8.3f} [{la:+.3f},{ha:+.3f}] {len(b):5d} "
                  f"{b.v.mean():+8.3f} [{lb:+.3f},{hb:+.3f}]  "
                  f"{'CONFIRMS' if ok else 'FAILS'}")

    # ------------------------------------------------------------ §3 ----
    print("\n" + "=" * 100)
    print("2. EXIT: V1 vs V2 on this population")
    print("=" * 100)
    print(f"   {'pop':14s} {'n':>4s} {'V1 EV':>8s} {'V1 95%':>20s} "
          f"{'V2 EV':>8s} {'V2 95%':>20s} {'delta':>8s}")
    for tf in (3, 5):
        g = OS[tf]
        l1, h1 = boot_mean(g, "v1")
        l2, h2 = boot_mean(g, "v2")
        print(f"   open {tf}m{'':7s} {len(g):4d} {g.v1.mean():+8.3f} "
              f"[{l1:+.3f},{h1:+.3f}] {g.v2.mean():+8.3f} "
              f"[{l2:+.3f},{h2:+.3f}] {g.v2.mean()-g.v1.mean():+8.3f}")

    # ------------------------------------------------------------ §4 ----
    print("\n" + "=" * 100)
    print("3. FULL BATTERY")
    print("=" * 100)
    print(f"\n   fights/day and MFE-in-R (bounded by the stop)")
    print(f"   {'pop':14s} {'/day':>6s} {'p25':>6s} {'p50':>6s} {'p75':>6s} "
          f"{'p90':>6s} {'p95':>6s} {'P(>=3R)':>8s}")
    FT = pd.read_parquet(OUT / "fixed_target.parquet")
    for tf in (3, 5):
        key = OS[tf][["sess_day", "t", "side"]]
        m = FT[FT.book == f"ROOM-GATED {tf}m"].merge(key, on=["sess_day", "t",
                                                              "side"])
        q = m.mfe_bounded
        print(f"   open {tf}m{'':7s} {len(OS[tf])/nd:6.2f} " + " ".join(
            f"{q.quantile(x):6.2f}" for x in (.25, .5, .75, .9, .95))
            + f" {(q>=3).mean()*100:7.1f}%")

    print(f"\n   clustering-X sensitivity (the book is rebuilt at each X, "
          f"then open-space re-applied)")
    T = pd.read_parquet(OUT / "ltf_fit.parquet")
    T["t"] = pd.to_datetime(T.t)
    T["era"] = era(T)
    P = pd.read_parquet(LP)
    print(f"   {'X':>5s} " + " ".join(f"{f'TF={t}m':>20s}" for t in (3, 5)))
    for x in XS:
        Tx = T.copy()
        Tx["scid"] = lassign(Tx, P, x)
        Bx = lbook(Tx)
        cells = []
        for tf in (3, 5):
            g = Bx[(Bx.tf == tf) & (Bx.risk >= FLOOR)
                   & (Bx.session == "LONDON") & (Bx.arm == "reject")
                   & Bx.next_lvl_R.isna()]
            cells.append(f"{g.out_ship.mean():+.3f} ({len(g)/nd:.2f}/d)")
        print(f"   {x:5.2f} " + " ".join(f"{c:>20s}" for c in cells))

    print(f"\n   cost sensitivity (V1 exit)")
    print(f"   {'pop':14s} {'@0.5pt':>9s} {'@1.0pt':>9s} {'@1.5pt':>9s}")
    for tf in (3, 5):
        g = OS[tf]
        print(f"   open {tf}m{'':7s} {g.v1.mean():+9.3f} "
              f"{(g.v1 - 0.5/g.risk).mean():+9.3f} "
              f"{(g.v1 - 1.0/g.risk).mean():+9.3f}")

    print(f"\n   sensitivity: the 2pt risk floor REMOVED (BR-45 says it is "
          f"probably too low)")
    Tn = T.copy()
    Tn["scid"] = lassign(Tn, P, 0.5)
    Bn = lbook(Tn)
    print(f"   {'pop':14s} {'floor 2pt':>22s} {'NO floor':>22s}")
    for tf in (3, 5):
        w = Bn[(Bn.tf == tf) & (Bn.session == "LONDON") & (Bn.arm == "reject")
               & Bn.next_lvl_R.isna()]
        wf = w[w.risk >= FLOOR]
        print(f"   open {tf}m{'':7s} {f'{wf.out_ship.mean():+.3f} (n={len(wf)})':>22s} "
              f"{f'{w.out_ship.mean():+.3f} (n={len(w)})':>22s}")

    # ------------------------------------------------------------ §5 ----
    print("\n" + "=" * 100)
    print("4. REDUNDANCY / CONCURRENCY vs the incumbent — measured FRESH on "
          "this subset")
    print("=" * 100)
    B = lbook(T.assign(scid=lassign(T, P, 0.5)))
    ROOM = B[(B.risk >= FLOOR) & admissible(B) & (B.session == "LONDON")
             & (B.arm == "reject")]
    for c in ("t_entry", "t_exit"):
        ROOM[c] = pd.to_datetime(ROOM[c])
    print(f"   {'stream':22s} {'n':>5s} {'redundant':>10s} {'concurrent':>11s}"
          f"   (bundled measured 6.6%/22.2% at 3m — NOT assumed to carry)")
    streams = {}
    for tf in (3, 5):
        R = ROOM[(ROOM.tf == tf) & ROOM.next_lvl_R.isna()].copy()
        red = con = 0
        for r in R.itertuples():
            c = INC[(INC.sess_day == r.sess_day)
                    & (INC.direction == r.direction)]
            if not len(c):
                continue
            s = c[c.locus == r.locus]
            if len(s) and (abs((pd.to_datetime(s.t_entry) - r.t_entry)
                               .dt.total_seconds()) <= NEAR * 60).any():
                red += 1
            if ((pd.to_datetime(c.t_entry) <= r.t_exit)
                    & (pd.to_datetime(c.t_exit) >= r.t_entry)).any():
                con += 1
        streams[tf] = R
        print(f"   open-space {tf}m{'':8s} {len(R):5d} "
              f"{red/max(len(R),1)*100:9.1f}% {con/max(len(R),1)*100:10.1f}%")

    # ------------------------------------------------------------ §6 ----
    print("\n" + "=" * 100)
    print("5. ACCOUNT LAB — three-way, at each book's own carryable size")
    print("=" * 100)
    print(f"   {'book':34s} {'n':>5s} {'/day':>6s} {'EV':>8s} {'R/day':>7s} "
          f"{'worst':>7s} {'maxsz':>7s} {'SIM grad':>8s} {'death':>6s} "
          f"{'LIVE $/yr':>10s}")
    res = {}
    res["inc"] = score(INC, days, "out_ship", "1. incumbent alone", nd)
    for tf in (3, 5):
        bun = ROOM[ROOM.tf == tf]
        res[f"b{tf}"] = score(
            pd.concat([INC.rename(columns={"out_ship": "o"})[["sess_day", "o"]],
                       bun.rename(columns={"out_ship": "o"})[["sess_day", "o"]]],
                      ignore_index=True), days, "o",
            f"2. inc + BUNDLED room {tf}m", nd)
        os_ = streams[tf]
        res[f"o{tf}"] = score(
            pd.concat([INC.rename(columns={"out_ship": "o"})[["sess_day", "o"]],
                       os_.rename(columns={"out_ship": "o"})[["sess_day", "o"]]],
                      ignore_index=True), days, "o",
            f"3. inc + OPEN-SPACE only {tf}m", nd)
    print("\n   deltas vs the incumbent alone:")
    for k, lbl in (("b3", "bundled 3m"), ("o3", "open-space 3m"),
                   ("b5", "bundled 5m"), ("o5", "open-space 5m")):
        r, b = res[k], res["inc"]
        print(f"     +{lbl:16s} /day {r['fpd']-b['fpd']:+.2f}  "
              f"R/day {r['rday']-b['rday']:+.3f}  worst "
              f"{r['worst']-b['worst']:+.2f}  size {r['ms']-b['ms']:+,.0f}  "
              f"GRAD {(r['grad']-b['grad'])*100:+.1f}pp  LIVE "
              f"{r['live']-b['live']:+,.0f}")
    print("\n   PREDICTION 2 CHECK — open-space-only vs the BUNDLED "
          "combination:")
    for tf in (3, 5):
        o, b = res[f"o{tf}"], res[f"b{tf}"]
        print(f"     {tf}m  SIM grad {o['grad']*100:.1f}% vs {b['grad']*100:.1f}%"
              f"  -> {'open-space LOSES (as predicted)' if o['grad'] < b['grad'] else 'OPEN-SPACE WINS — this is the headline'}")
        print(f"     {tf}m  LIVE     ${o['live']:,.0f} vs ${b['live']:,.0f}"
              f"  -> {'bundled' if b['live'] > o['live'] else 'OPEN-SPACE'} wins the dollars")


if __name__ == "__main__":
    main()
