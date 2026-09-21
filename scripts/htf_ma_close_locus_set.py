#!/usr/bin/env python3
"""CLOSING THE LOCUS SET — one pass, before holdout look #1 is spent.

The look is HALTED because the population is still moving. Five sections:

  1  POC and VAH re-censused PER WINDOW, per session, both arms, all four X
  2  POC as a CONFLUENCE PARTNER (cross-tab, no new pipeline) — distinct
     from confluence_count, which died as a count of any levels, pooled,
     under a different exit
  3  MFE-in-R per session + where the partial actually belongs
  4  the clustering valley re-run PER SESSION (X=0.5W was a pooled fallback)
  5  two-stage scoring (sim-stage rules vs live-stage rules) and the
     Bonferroni x15 restatement of the per-session selection table

    python -m scripts.htf_ma_close_locus_set [--build-poc]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.htf_ma_account_lab as AL                             # noqa: E402
from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_flow_depth_run import boot_mean                 # noqa: E402
from scripts.htf_ma_level_census import level_series                # noqa: E402
from scripts.htf_ma_level_report import PAIRS, assign, book         # noqa: E402
from scripts.htf_ma_session_books import concord                    # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402

POCF = ROOT / "output/htf_ma_census/poc_partner.parquet"
SESSIONS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (570, 630)}
XS = [0.25, 0.5, 1.0, 2.0]
TICK, COST = 0.25, 0.5
SEED, DRAWS, YEAR = 20260807, 1500, 250
NCELL = 15                       # 5 candidates x 3 sessions


def era(d):
    return np.where(d.sess_day < "2026-01-01", "H2-2025", "H1-2026")


def cell(g):
    lo, hi = boot_mean(g)
    return f"{g.out_ship.mean():+.3f}[{lo:+.3f},{hi:+.3f}]" + ("!" if lo > 0 else " ")


# ---------------------------------------------------------------- 1 + 2 ----
def build_poc_partner() -> pd.DataFrame:
    """POC value as-of the decision bar for every fit trigger, plus the
    declared partner flags. Causal: POC as-of the previous 1m close."""
    F = pd.read_parquet(ROOT / "output/htf_ma_census/levels_fit.parquet")
    F["t"] = pd.to_datetime(F.t)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    out = []
    days = sorted(F.sess_day.unique())
    for k, day in enumerate(days):
        D = F[F.sess_day == day]
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                    & (bars.index < t1)]
        if hist.empty:
            continue
        seg = hist[(hist.index >= t0) & (hist.index < t1)]
        if seg.empty:
            continue
        ma15, _ = bb_ma_asof(hist, 15)
        lv = level_series(hist, seg.index, ma15)
        idx = seg.index
        f15 = hist.resample("15min", label="right", closed="left").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last"}).dropna()
        f15 = f15[(f15.index > t0) & (f15.index <= t1)]
        for r in D.itertuples():
            j = int(np.searchsorted(idx.values,
                                    (r.t - pd.Timedelta(minutes=1)).to_datetime64()))
            j = min(max(j, 0), len(idx) - 1)
            poc = float(lv["poc"][j])
            rec = {"sess_day": day, "t": r.t, "locus": r.locus, "arm": r.arm,
                   "side": r.side, "n_attempts": r.n_attempts, "poc_px": poc}
            if r.t in f15.index and np.isfinite(poc) and r.w15 > 0:
                b = f15.loc[r.t]
                d = int(r.direction)
                # DECLARED: coincident = POC within 0.25W of the traded level
                rec["poc_coincident"] = abs(r.lvl_px - poc) <= 0.25 * r.w15
                # DECLARED: broken-with-trade = the decision bar closed
                # through POC in the trade direction, having been on the
                # other side at its open
                rec["poc_broken"] = bool((d * (b.close - poc) > 0)
                                         and (d * (b.open - poc) <= 0))
                rec["poc_ahead"] = bool(d * (poc - r.lvl_px) > 0)
            out.append(rec)
        if k % 60 == 0:
            print(f"  poc {k}/{len(days)}...", flush=True)
    P = pd.DataFrame(out)
    P.to_parquet(POCF, index=False)
    return P


def out_at_T(b, T):
    cr = COST / b.risk
    leg = 0.75 * (T - TICK / b.risk) + 0.25 * (b.out_trail + cr) - cr
    return pd.Series(np.where(b.mfe_r >= T, leg, b.out_trail), index=b.index)


def main() -> None:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/levels_fit.parquet")
    F["t"] = pd.to_datetime(F.t)
    F["hm"] = F.t.dt.hour * 60 + F.t.dt.minute
    F["era"] = era(F)
    P = pd.read_parquet(PAIRS)
    days_all = pd.Index(sorted(F.sess_day.unique()))
    nd = len(days_all)

    print("=" * 78)
    print("1. POC and VAH RE-CENSUSED PER WINDOW  (bar: E1.4 — both-era CI>0 "
          "at X=0.5W and sign positive at >=3 of 4 X)")
    print("=" * 78)
    FX = {x: F.join(assign(F, P, x)) for x in XS}
    verdicts = {}
    for sess, (a, b) in SESSIONS.items():
        print(f"\n-- {sess} {a//60:02d}:{a%60:02d}-{b//60:02d}:{b%60:02d} NY")
        for locus in ("poc", "vah"):
            for arm in ("reject", "break"):
                row, signs, both05 = [], [], False
                for x in XS:
                    W = FX[x][(FX[x].hm >= a) & (FX[x].hm <= b)]
                    bk = book(W[W.locus == locus], arm)
                    if len(bk) < 25:
                        row.append(f"X{x}: n={len(bk)} UND")
                        signs.append(np.nan)
                        continue
                    signs.append(np.sign(bk.out_ship.mean()))
                    if x == 0.5:
                        ok = []
                        for e, g in bk.groupby("era"):
                            lo, hi = boot_mean(g)
                            ok.append(lo > 0 and len(g) >= 12)
                        both05 = len(ok) == 2 and all(ok)
                        row.append(f"X0.5: n={len(bk):4d} {bk.out_ship.mean():+.3f} "
                                   + " ".join(f"{e}={cell(g)}"
                                              for e, g in bk.groupby("era")))
                    else:
                        row.append(f"X{x}: {bk.out_ship.mean():+.3f}")
                pos = int(np.nansum([s > 0 for s in signs]))
                v = "FOLLOW-UP EARNED" if (both05 and pos >= 3) else "park"
                verdicts[(sess, locus, arm)] = v
                print(f"   {locus:4s} {arm:7s} | " + " | ".join(row))
                print(f"   {'':4s} {'':7s} -> both-era@0.5W {both05}, "
                      f"positive {pos}/4  ==> {v}")

    print("\n" + "=" * 78)
    print("2. POC AS A CONFLUENCE PARTNER (distinct candidate from "
          "confluence_count)")
    print("=" * 78)
    PP = pd.read_parquet(POCF) if POCF.exists() else build_poc_partner()
    PP["t"] = pd.to_datetime(PP.t)
    key = ["sess_day", "t", "locus", "arm", "side", "n_attempts"]
    F5 = FX[0.5].merge(PP[key + ["poc_coincident", "poc_broken", "poc_ahead"]],
                       on=key, how="left")
    F5["poc_partner"] = (F5.poc_coincident.fillna(False)
                         | F5.poc_broken.fillna(False))
    print("  DECLARED: partner = POC within 0.25W of the traded level "
          "(coincident) OR the decision bar closed through POC with the "
          "trade (broken). Both as-of the decision bar.")
    for sess, (a, b) in SESSIONS.items():
        W = F5[(F5.hm >= a) & (F5.hm <= b)]
        print(f"\n-- {sess}")
        for locus, arm in (("val", "break"), ("bbma15", "reject"),
                           ("vwap_m1", "break")):
            bk = book(W[W.locus == locus], arm)
            if len(bk) < 40:
                print(f"   {locus:8s} {arm:7s} n={len(bk)} UNDERPOWERED")
                continue
            on = bk[bk.poc_partner]
            off = bk[~bk.poc_partner]
            if len(on) < 15 or len(off) < 15:
                print(f"   {locus:8s} {arm:7s} partner n={len(on)} — "
                      f"UNDERPOWERED")
                continue
            print(f"   {locus:8s} {arm:7s} n={len(bk):4d} | partner "
                  f"{len(on):4d} ({len(on)/len(bk)*100:4.1f}%) "
                  f"{cell(on)} | no-partner {len(off):4d} {cell(off)} | "
                  f"delta {on.out_ship.mean()-off.out_ship.mean():+.3f}")

    print("\n" + "=" * 78)
    print("3. MFE-in-R PER SESSION and where the 75%-at-3R partial belongs")
    print("=" * 78)
    SB = pd.read_parquet(ROOT / "output/htf_ma_census/sweepb_london_frame.parquet")
    SB["t"] = pd.to_datetime(SB.t)
    SB["hm"] = SB.t.dt.hour * 60 + SB.t.dt.minute
    SW = pd.read_parquet(ROOT / "output/htf_ma_census/sweep_fit.parquet")
    SW["t"] = pd.to_datetime(SW.t)
    SW["hm"] = SW.t.dt.hour * 60 + SW.t.dt.minute
    swl = SW[(SW.cell == "sweep_b") & (SW.hm >= 180) & (SW.hm <= 299)
             & SW.out_ship.notna() & (SW.risk > 0)]
    books = {}
    for sess, (a, b) in SESSIONS.items():
        W = FX[0.5][(FX[0.5].hm >= a) & (FX[0.5].hm <= b)]
        parts = [book(W[W.locus == "val"], "break"),
                 book(W[W.locus == "vwap_m1"], "break"),
                 book(W[W.locus == "bbma15"], "reject")]
        bk = pd.concat(parts).drop_duplicates(["sess_day", "t", "side"])
        if sess == "LONDON":
            bk = pd.concat([bk, swl]).drop_duplicates(["sess_day", "t", "side"])
        books[sess] = bk
    print(f"{'session':8s} {'n':>5s} {'p50':>6s} {'p75':>6s} {'p90':>6s} "
          f"{'p95':>6s} {'P(mfe>=3R)':>11s} | EV at partial T =")
    print(f"{'':8s} {'':5s} {'':6s} {'':6s} {'':6s} {'':6s} {'':11s} | "
          f"{'T=2':>7s} {'T=3':>7s} {'T=4':>7s} {'T=5':>7s} {'best':>6s}")
    for sess, bk in books.items():
        bk = bk[bk.mfe_r.notna() & (bk.risk > 0)]
        q = bk.mfe_r.quantile
        evs = {T: out_at_T(bk, T).mean() for T in (2, 3, 4, 5)}
        best = max(evs, key=evs.get)
        print(f"{sess:8s} {len(bk):5d} {q(.5):6.2f} {q(.75):6.2f} "
              f"{q(.9):6.2f} {q(.95):6.2f} {(bk.mfe_r>=3).mean()*100:10.1f}% | "
              + " ".join(f"{evs[T]:+7.3f}" for T in (2, 3, 4, 5))
              + f" {'T='+str(best):>6s}")
    print("  (the shipped exit is T=3, chosen on a POOLED table — 'best' "
          "above is that session's own optimum)")

    print("\n" + "=" * 78)
    print("4. CLUSTERING VALLEY RE-RUN PER SESSION")
    print("=" * 78)
    Pv = P.copy()
    Pv["t_b"] = pd.to_datetime(Pv.t_b)
    Pv["hm"] = Pv.t_b.dt.hour * 60 + Pv.t_b.dt.minute
    for sess, (a, b) in SESSIONS.items():
        e = Pv[(Pv.hm >= a) & (Pv.hm <= b)].exc_w.dropna()
        if len(e) < 200:
            print(f"  {sess:8s} n={len(e)} UNDERPOWERED")
            continue
        h, edges = np.histogram(e.clip(upper=3.0), bins=np.arange(0, 3.01, .1))
        sm = np.convolve(h, np.ones(3) / 3, mode="same")
        lo_i = int(np.argmax(edges[:-1] >= 0.2))
        hi_i = int(np.argmax(edges[:-1] >= 1.5))
        seg_ = sm[lo_i:hi_i]
        vi = int(np.argmin(seg_))
        interior = (0 < vi < len(seg_) - 1 and seg_[0] > seg_[vi] * 1.2
                    and seg_[-1] > seg_[vi] * 1.2)
        qs = " ".join(f"p{p}={e.quantile(p/100):.2f}" for p in (25, 50, 75, 90))
        if interior:
            print(f"  {sess:8s} n={len(e):5d} {qs} -> VALLEY FOUND at "
                  f"X={edges[lo_i+vi]+0.05:.2f}W")
        else:
            print(f"  {sess:8s} n={len(e):5d} {qs} -> no interior valley "
                  f"(monotone) — declared fallback X=0.50W stands")

    print("\n" + "=" * 78)
    print("5a. TWO CONFIGS x TWO STAGES — London")
    print("=" * 78)
    C = pd.read_parquet(ROOT / "output/htf_ma_census/bc_frame.parquet")
    C["t"] = pd.to_datetime(C.t)
    C["hm"] = C.t.dt.hour * 60 + C.t.dt.minute
    L = pd.concat([C[(C.hm >= 180) & (C.hm <= 299)],
                   SB[(SB.hm >= 180) & (SB.hm <= 299)]],
                  ignore_index=True).drop_duplicates(["sess_day", "t", "side"])
    L["CONCORD"] = concord(L)
    cut = (L.CONCORD < 7).fillna(False)
    cfgs = {"uncut": L, "CONCORD>=7": L[~cut]}

    def dayR(b):
        return b.groupby("sess_day").out_ship.sum().reindex(
            days_all, fill_value=0.0).to_numpy()

    def run(dR, sz, cap):
        pol = {"s_pre": float(sz), "s_post": float(sz)}
        rng = np.random.default_rng(SEED)
        runs = [AL.run_account(dR, rng.integers(0, len(dR), YEAR), pol,
                               payout_cap=cap, payout_at=6000.)
                for _ in range(DRAWS)]
        return (float(np.mean([r["end_state"] == "graduated" for r in runs])),
                float(np.mean([len(r["funded_deaths"]) > 0 for r in runs])),
                float(np.mean([sum(w for _, w in r["wd"]) - r["fees"]
                               for r in runs])))
    print("  SIM STAGE (5-payout cap, 250-day clock — the constraints that "
          "exist only pre-LucidLive)")
    print(f"{'config':12s} {'/day':>5s} {'EV':>7s} {'size':>5s} "
          f"{'GRAD':>7s} {'P(death)':>9s} {'net':>9s}")
    for lab, b in cfgs.items():
        dR = dayR(b)
        for sz in (150, 300, 450):
            if (dR <= -2000 / sz).sum():
                continue
            g, d_, n_ = run(dR, sz, 5)
            print(f"{lab:12s} {len(b)/nd:5.2f} {b.out_ship.mean():+7.3f} "
                  f"{sz:5d} {g*100:6.1f}% {d_*100:8.1f}% ${n_:8,.0f}")
    print("\n  LIVE STAGE PROXY (no payout cap, no graduation clock) — "
          "LucidLive terms are not public, so this is a PROXY: uncapped "
          "withdrawals on the same mechanics")
    print(f"{'config':12s} {'size':>5s} {'net/yr':>10s} {'P(death)':>9s} "
          f"{'$/day':>8s}")
    for lab, b in cfgs.items():
        dR = dayR(b)
        for sz in (150, 300, 450):
            if (dR <= -2000 / sz).sum():
                continue
            _, d_, n_ = run(dR, sz, None)
            print(f"{lab:12s} {sz:5d} ${n_:9,.0f} {d_*100:8.1f}% "
                  f"${dR.mean()*sz:7.0f}")

    print("\n" + "=" * 78)
    print("5b. BONFERRONI x15 RESTATEMENT of the per-session selection table")
    print("=" * 78)
    sess_books = {}
    for sess, (a, b) in SESSIONS.items():
        bk = books[sess].copy()
        cc = C[(C.hm >= a) & (C.hm <= b)]
        m = bk.merge(cc[["sess_day", "t", "side", "flowconf", "closeloc",
                         "dep_thickness_vs_day"] +
                        [c for c in cc.columns if c.startswith(("d5_", "d15_",
                         "d30_", "cvd_", "delta_z", "bp5", "volx", "eff_",
                         "rangex", "thru_"))]],
                     on=["sess_day", "t", "side"], how="left")
        if m.flowconf.notna().sum() > 30:
            m["CONCORD"] = concord(m)
        sess_books[sess] = m
    alpha = 0.05 / NCELL
    print(f"  alpha = 0.05/{NCELL} = {alpha:.4f}  ->  "
          f"{100*(1-alpha):.2f}% bootstrap interval on the LIFT")
    print(f"{'session':8s} {'candidate':22s} {'lift':>8s} "
          f"{'x15 CI on lift':>24s} survives")
    rng = np.random.default_rng(SEED)
    for sess, m in sess_books.items():
        EV = m.out_ship.mean()
        cands = [("CONCORD<7", m.get("CONCORD", pd.Series(np.nan, index=m.index)) < 7),
                 ("CONCORD<5", m.get("CONCORD", pd.Series(np.nan, index=m.index)) < 5),
                 ("closeloc<Q1", m.closeloc < m.closeloc.quantile(.25)),
                 ("S1 flowconf==0", m.flowconf == 0),
                 ("dep_thick_vs_day<Q1",
                  m.dep_thickness_vs_day < m.dep_thickness_vs_day.quantile(.25))]
        for lab, msk in cands:
            msk = msk.fillna(False)
            if msk.sum() < 12 or (~msk).sum() < 12:
                print(f"{sess:8s} {lab:22s}   n/a")
                continue
            q = msk.mean()
            lift = q * (EV - m.out_ship[msk].mean()) / (1 - q)
            # day-level bootstrap of the LIFT itself
            dl = {d: g for d, g in m.assign(_m=msk).groupby("sess_day")}
            ds = list(dl)
            st = []
            for _ in range(1200):
                pick = rng.choice(ds, len(ds), replace=True)
                sub = pd.concat([dl[d] for d in pick], ignore_index=True)
                mm = sub._m
                if mm.sum() < 5 or (~mm).sum() < 5:
                    continue
                qq = mm.mean()
                st.append(qq * (sub.out_ship.mean()
                                - sub.out_ship[mm].mean()) / (1 - qq))
            if len(st) < 200:
                print(f"{sess:8s} {lab:22s} {lift:+8.3f}   too thin")
                continue
            lo = float(np.percentile(st, 100 * alpha / 2))
            hi = float(np.percentile(st, 100 * (1 - alpha / 2)))
            surv = "YES" if lo > 0 else "no"
            print(f"{sess:8s} {lab:22s} {lift:+8.3f} "
                  f"[{lo:+.3f},{hi:+.3f}]".rjust(20) + f"   {surv}")


if __name__ == "__main__":
    main()
