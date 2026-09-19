#!/usr/bin/env python3
"""PHASE 1 — THE DIAGNOSIS. Report-only; nothing is acted on.

Per candidate book, NEVER pooled across books:

  A  column schema reconciliation for THIS book, stated first
  B  every column: winner vs loser, and magnitude quintile on out_ship
     (primary) with mfe_r alongside (secondary)
  C  two ways — naive trade-level, and DAY-CLUSTERED. A variable whose
     signal survives naive but dies clustered is a DAY PROPERTY wearing a
     trade's clothes, and is flagged as such
  D  within-day vs between-day VARIANCE DECOMPOSITION by name — the
     pseudo-replication check
  E  each book's OWN worst 3-5 days, identified fresh, and the diagnosis
     repeated with and without them
  F  dual currency on every row
  G  LAW 2 SCREEN: anything separating gets checked for mechanical
     coupling to risk / the R denominator before it is called behavioural

    python -m scripts.phase1_diagnose
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.htf_ltf_report import (PAIRS as LP, assign as lassign,  # noqa: E402
                                    book as lbook, era)
from scripts.htf_room_gate import FLOOR, admissible                  # noqa: E402

OUT = ROOT / "output/htf_ma_census"
SEED, DRAWS = 20260807, 2000
NWORST = 5

FLOW12 = ["flowconf", "volx", "closeloc", "rangex", "bp5opp", "d5_conf",
          "d15_conf", "d30_conf", "thru_delta_conf", "eff_result",
          "cvd_slope30", "delta_z"]
DEPTH6 = ["dep_thickness_vs_day", "dep_imbalance", "support_minus_resist",
          "support_wall_dist", "support_wall_size", "dep_thickness_delta_5m"]
GEOM = ["risk", "w15", "risk_w"]
D7 = ["next_lvl_R", "ceil5_between", "ceil5_fresh", "ceil60_between",
      "ceil60_fresh"]
INTRADE = ["it1_cum", "it1_concord", "it5_cum", "it5_concord", "it10_cum",
           "it10_concord", "it5_slope", "it10_slope"]
# variables MECHANICALLY coupled to risk or the R denominator (Law 2)
MECH = {"risk", "risk_w", "w15", "closeloc", "rangex", "next_lvl_R"}
# variables NOT KNOWABLE AT THE DECISION BAR — measured t+N minutes INTO the
# trade, so they are partly the outcome itself. Usable for exit/management
# rules (BR-22), never for entry selection or conviction sizing at entry.
POST_ENTRY = set(INTRADE)


def dboot_diff(df, col, mask, draws=DRAWS):
    """Day-clustered bootstrap of (mean | mask) - (mean | ~mask).

    Resamples SESSION-DAYS with replacement, not trades. A variable whose
    naive separation is really a day property collapses here."""
    d = df[["sess_day", col]].copy()
    d["m"] = mask.to_numpy()
    days = np.array(sorted(d.sess_day.unique()))
    di = {x: i for i, x in enumerate(days)}
    sA = np.zeros(len(days)); nA = np.zeros(len(days))
    sB = np.zeros(len(days)); nB = np.zeros(len(days))
    for x, g in d.groupby("sess_day"):
        a, b = g[g.m], g[~g.m]
        sA[di[x]], nA[di[x]] = a[col].sum(), len(a)
        sB[di[x]], nB[di[x]] = b[col].sum(), len(b)
    if len(days) < 5 or nA.sum() < 5 or nB.sum() < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(days), (draws, len(days)))
    ca, cb = nA[i].sum(1), nB[i].sum(1)
    ea = np.divide(sA[i].sum(1), ca, out=np.full(draws, np.nan), where=ca > 0)
    eb = np.divide(sB[i].sum(1), cb, out=np.full(draws, np.nan), where=cb > 0)
    st = ea - eb
    return float(np.nanpercentile(st, 2.5)), float(np.nanpercentile(st, 97.5))


def naive_diff_ci(df, col, mask, draws=DRAWS):
    """Trade-level bootstrap — the NAIVE one, resampling rows."""
    a = df.loc[mask.to_numpy(), col].to_numpy()
    b = df.loc[~mask.to_numpy(), col].to_numpy()
    if len(a) < 5 or len(b) < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    ia = rng.integers(0, len(a), (draws, len(a)))
    ib = rng.integers(0, len(b), (draws, len(b)))
    st = a[ia].mean(1) - b[ib].mean(1)
    return float(np.percentile(st, 2.5)), float(np.percentile(st, 97.5))


def var_decomp(df, v):
    """Within-day vs between-day variance of v. High between-day share =>
    the variable mostly indexes WHICH DAY it is, so trades are pseudo-
    replicates and the naive CI is too tight."""
    g = df[["sess_day", v]].dropna()
    if g[v].nunique() < 3 or g.sess_day.nunique() < 5:
        return np.nan
    gm = g.groupby("sess_day")[v].agg(["mean", "size"])
    gm = gm[gm["size"] >= 2]
    if len(gm) < 5:
        return np.nan
    grand = g[v].mean()
    between = float((gm["size"] * (gm["mean"] - grand) ** 2).sum())
    total = float(((g[v] - grand) ** 2).sum())
    return between / total if total > 0 else np.nan


def diagnose(name, D, cols, log):
    def P(*a):
        print(*a)
        log.append(" ".join(str(x) for x in a))

    D = D.copy()
    D["risk_w"] = D.risk / D.w15
    D["win"] = D.out_ship > 0
    nd = D.sess_day.nunique()
    P("\n" + "=" * 100)
    P(f"BOOK: {name}   n={len(D)}  days={nd}  {len(D)/nd:.2f}/day  "
      f"EV={D.out_ship.mean():+.3f}  win={D.win.mean()*100:.1f}%")
    P("=" * 100)

    have, partial = [], []
    for c in cols:
        if c not in D.columns:
            continue
        cov = D[c].notna().mean()
        if D[c].notna().sum() >= 40 and D[c].nunique() > 1:
            have.append(c)
            if cov < 0.90:
                partial.append((c, cov))
    miss = [c for c in cols if c not in D.columns]
    if miss:
        P(f"  COLUMNS ABSENT FROM THIS BOOK ({len(miss)}): "
          f"{', '.join(miss)}")
    thin = [c for c in cols if c in D.columns and c not in have]
    if thin:
        P(f"  COLUMNS PRESENT BUT UNUSABLE (all-NaN / constant / n<40): "
          f"{', '.join(thin)}")
    P(f"  diagnosing {len(have)} columns")
    if partial:
        P(f"  PARTIAL COVERAGE — these columns exist on only part of this "
          f"book, so the row below is a SUB-POPULATION finding, not a "
          f"book-level one:")
        for c, cov in sorted(partial, key=lambda x: x[1]):
            P(f"      {c:24s} present on {cov*100:5.1f}% of rows")

    # ---- E: this book's own worst days, found fresh --------------------
    dayr = D.groupby("sess_day").out_ship.sum().sort_values()
    worst = list(dayr.index[:NWORST])
    P(f"\n  THIS BOOK'S OWN WORST {NWORST} DAYS (found fresh, not inherited): "
      + ", ".join(f"{d}({dayr[d]:+.1f}R)" for d in worst))
    P(f"    they are {sum(dayr[d] for d in worst):+.1f}R of a "
      f"{D.out_ship.sum():+.1f}R book over {nd} days")

    rows = []
    for c in have:
        v = D[c]
        ok = v.notna()
        d = D[ok]
        vv = v[ok]
        # median split (or the natural 0/1 split for binaries)
        if vv.nunique() == 2:
            hi = vv == vv.max()
            desc = f"=={vv.max():g}"
        else:
            med = vv.median()
            hi = vv > med
            desc = f">{med:.3g}"
        if hi.sum() < 20 or (~hi).sum() < 20:
            continue
        ev_hi = d.loc[hi.to_numpy(), "out_ship"].mean()
        ev_lo = d.loc[~hi.to_numpy(), "out_ship"].mean()
        wr_hi = d.loc[hi.to_numpy(), "win"].mean() * 100
        wr_lo = d.loc[~hi.to_numpy(), "win"].mean() * 100
        mf_hi = d.loc[hi.to_numpy(), "mfe_r"].mean()
        mf_lo = d.loc[~hi.to_numpy(), "mfe_r"].mean()
        nlo, nhi_ = naive_diff_ci(d, "out_ship", hi)
        clo, chi_ = dboot_diff(d, "out_ship", hi)
        bshare = var_decomp(D, c)
        # without this book's own worst days
        d2 = d[~d.sess_day.isin(worst)]
        hi2 = hi[~d.sess_day.isin(worst).to_numpy()]
        ex = (d2.loc[hi2.to_numpy(), "out_ship"].mean()
              - d2.loc[~hi2.to_numpy(), "out_ship"].mean()) \
            if hi2.sum() > 10 and (~hi2).sum() > 10 else np.nan
        rows.append(dict(col=c, covg=float(D[c].notna().mean()),
                         split=desc, n_hi=int(hi.sum()),
                         ev_hi=ev_hi, ev_lo=ev_lo, d_ev=ev_hi - ev_lo,
                         nlo=nlo, nhi=nhi_, clo=clo, chi=chi_,
                         wr_hi=wr_hi, wr_lo=wr_lo, d_wr=wr_hi - wr_lo,
                         d_mfe=mf_hi - mf_lo, bshare=bshare, d_ex=ex))
    R = pd.DataFrame(rows)
    if R.empty:
        P("  no usable columns")
        return R.assign(book=name)
    R["naive_sig"] = (R.nlo > 0) | (R.nhi < 0)
    R["clust_sig"] = (R.clo > 0) | (R.chi < 0)
    R["dies"] = R.naive_sig & ~R.clust_sig
    R["dual_inv"] = np.sign(R.d_ev) != np.sign(R.d_wr)
    R["mech"] = R.col.isin(MECH)
    R["post"] = R.col.isin(POST_ENTRY)
    R["partial"] = R["covg"] < 0.90
    R = R.sort_values("d_ev", key=abs, ascending=False)

    P(f"\n  {'column':24s} {'split':>10s} {'n_hi':>5s} {'dEV':>7s} "
      f"{'naive 95%':>18s} {'CLUSTERED 95%':>18s} {'dWin':>6s} {'dMFE':>6s} "
      f"{'btw-day':>7s} {'flags'}")
    for r in R.itertuples():
        fl = []
        if r.dies:
            fl.append("DAY-PROPERTY")
        elif r.clust_sig:
            fl.append("SURVIVES")
        if r.dual_inv:
            fl.append("DUAL-INVERSION")
        if r.mech:
            fl.append("LAW2-MECHANICAL")
        if r.post:
            fl.append("POST-ENTRY(not knowable at the decision bar)")
        if r.partial:
            fl.append(f"PARTIAL-COVERAGE({r.covg*100:.0f}%)")
        if np.isfinite(r.d_ex) and abs(r.d_ex) < abs(r.d_ev) * 0.5:
            fl.append("WORST-DAY-CARRIED")
        P(f"  {r.col:24s} {r.split:>10s} {r.n_hi:5d} {r.d_ev:+7.3f} "
          f"[{r.nlo:+.3f},{r.nhi:+.3f}] [{r.clo:+.3f},{r.chi:+.3f}] "
          f"{r.d_wr:+6.1f} {r.d_mfe:+6.2f} "
          f"{(r.bshare*100 if np.isfinite(r.bshare) else float('nan')):6.1f}% "
          f" {' '.join(fl)}")

    # ---- magnitude quintiles on the survivors --------------------------
    # magnitude profiling is for ENTRY-USABLE survivors only
    surv = R[R.clust_sig & ~R.post & ~R.partial].head(6)
    if len(surv):
        P(f"\n  MAGNITUDE QUINTILES on out_ship (primary) for the "
          f"{len(surv)} day-clustered survivors:")
        for r in surv.itertuples():
            d = D[D[r.col].notna()].copy()
            try:
                d["q"] = pd.qcut(d[r.col], 5, labels=False, duplicates="drop")
            except ValueError:
                continue
            g = d.groupby("q").agg(ev=("out_ship", "mean"),
                                   mfe=("mfe_r", "mean"),
                                   wr=("win", "mean"), n=("win", "size"))
            if len(g) < 3:
                continue
            mono = (g.ev.is_monotonic_increasing or g.ev.is_monotonic_decreasing)
            P(f"    {r.col:22s} EV  " + "  ".join(
                f"Q{int(i)+1}={g.ev[i]:+.3f}" for i in g.index)
              + f"   {'MONOTONE' if mono else 'non-monotone'}")
            P(f"    {'':22s} MFE " + "  ".join(
                f"Q{int(i)+1}={g.mfe[i]:5.2f}" for i in g.index))
            P(f"    {'':22s} win " + "  ".join(
                f"Q{int(i)+1}={g.wr[i]*100:4.1f}%" for i in g.index)
              + f"   n/bin~{int(g.n.mean())}")
    else:
        P("\n  MAGNITUDE QUINTILES: no day-clustered survivor to profile.")
    return R.assign(book=name)


def main() -> None:
    log = []
    INC = pd.read_parquet(OUT / "incumbent_london.parquet")
    INC["t"] = pd.to_datetime(INC.t)
    D7F = pd.read_parquet(OUT / "incumbent_london_d7.parquet")
    D7F["t"] = pd.to_datetime(D7F.t)
    INC = INC.merge(D7F, on=["sess_day", "t", "side", "pop"], how="left")

    T = pd.read_parquet(OUT / "ltf_fit.parquet")
    T["t"] = pd.to_datetime(T.t)
    FL = pd.read_parquet(OUT / "ltf_flow.parquet")
    FL["t"] = pd.to_datetime(FL.t)
    T = T.merge(FL, on=["sess_day", "t", "tf", "locus", "arm", "side"],
                how="left")
    T["era"] = era(T)
    T["scid"] = lassign(T, pd.read_parquet(LP), 0.5)
    B = lbook(T)
    ROOM = B[(B.risk >= FLOOR) & admissible(B) & (B.session == "LONDON")
             & (B.arm == "reject")]

    books = {"INCUMBENT LONDON (composite+sweep_b)": INC,
             "ROOM-GATED LONDON reject 3m": ROOM[ROOM.tf == 3],
             "ROOM-GATED LONDON reject 5m": ROOM[ROOM.tf == 5]}
    for tf in (3, 5):
        R_ = ROOM[ROOM.tf == tf]
        C = pd.concat([INC.assign(src="inc"), R_.assign(src=f"room{tf}m")],
                      ignore_index=True)
        books[f"COMBINED incumbent + room {tf}m"] = C

    cols = FLOW12 + DEPTH6 + GEOM + D7 + INTRADE
    print("=" * 100)
    print("PHASE 1 — THE DIAGNOSIS.  REPORT ONLY. Nothing is acted on.")
    print(f"columns requested: {len(cols)}  "
          f"(flow12 {len(FLOW12)}, depth6 {len(DEPTH6)}, geom {len(GEOM)}, "
          f"D7 {len(D7)}, in-trade {len(INTRADE)})")
    print("Each book diagnosed SEPARATELY. Never pooled across books.")
    print("=" * 100)

    allR = []
    for name, D in books.items():
        allR.append(diagnose(name, D, cols, log))
    A = pd.concat(allR, ignore_index=True)
    A.to_parquet(OUT / "phase1_diagnosis.parquet", index=False)

    print("\n" + "=" * 100)
    print("CROSS-BOOK SUMMARY — ranked by |dEV|, day-clustered survivors only")
    print("(listed per book; NOT pooled — a variable appearing in two books "
          "is two findings)")
    print("=" * 100)
    S = A[A.clust_sig].sort_values("d_ev", key=abs, ascending=False)
    if S.empty:
        print("   NOTHING survives day-clustering in any candidate book.")
    else:
        print(f"   {'book':38s} {'column':22s} {'dEV':>7s} "
              f"{'clustered 95%':>19s} {'dWin':>6s} {'btw-day':>7s} flags")
        for r in S.itertuples():
            fl = []
            if r.dual_inv:
                fl.append("DUAL-INVERSION")
            if r.mech:
                fl.append("LAW2-MECHANICAL")
            if r.post:
                fl.append("POST-ENTRY")
            if r.partial:
                fl.append(f"PARTIAL({r.covg*100:.0f}%)")
            if np.isfinite(r.d_ex) and abs(r.d_ex) < abs(r.d_ev) * 0.5:
                fl.append("WORST-DAY-CARRIED")
            print(f"   {r.book[:38]:38s} {r.col:22s} {r.d_ev:+7.3f} "
                  f"[{r.clo:+.3f},{r.chi:+.3f}] {r.d_wr:+6.1f} "
                  f"{(r.bshare*100 if np.isfinite(r.bshare) else float('nan')):6.1f}%"
                  f"  {' '.join(fl)}")
    nd_ = int(A.dies.sum())
    print(f"\n   variables significant NAIVELY but dead under day-clustering "
          f"(day properties): {nd_} of {len(A)}")
    print(f"   variables with a dual-currency inversion: "
          f"{int(A.dual_inv.sum())}")
    print(f"   variables flagged LAW-2 MECHANICAL: {int(A.mech.sum())}")
    print(f"   variables NOT KNOWABLE AT THE DECISION BAR (post-entry): "
          f"{int(A.post.sum())}")
    print(f"   variables on PARTIAL COVERAGE (sub-population findings): "
          f"{int(A.partial.sum())}")
    E = A[A.clust_sig & ~A.post & ~A.partial]
    print(f"\n   ENTRY-USABLE day-clustered survivors "
          f"(the only rows Phase 2 may consider): {len(E)}")


if __name__ == "__main__":
    main()
