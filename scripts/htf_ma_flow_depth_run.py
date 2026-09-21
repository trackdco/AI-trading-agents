#!/usr/bin/env python3
"""ONE RUN — B (concordance / wall / depth) + C (in-trade census).

PREREG-flow-depth-intrade.md. One table walk: every feature column is
computed ONCE per session day (trigger flow, depth-at-decision, in-trade
flow at t+1/2/3/5/10), cached to parquet, and every candidate is scored off
that single frame. No per-candidate re-walk.

    python -m scripts.htf_ma_flow_depth_run [--build]
"""
from __future__ import annotations

import glob
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_level_report import PAIRS, assign, book         # noqa: E402
from scripts.htf_ma_mtable import FLOW_NAMES, flow_features         # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402

FRAME = ROOT / "output/htf_ma_census/bc_frame.parquet"
SEED, DRAWS = 20260807, 2000
NCAND = 10                       # Bonferroni divisor, declared in the prereg
HORIZONS = [1, 2, 3, 5, 10]
CONF_BIN = ["flowconf", "thru_delta_conf", "d5_conf", "d15_conf", "d30_conf"]
MAG = ["volx", "eff_result", "rangex"]
DEPTH_FEATS = ["dep_thickness_vs_day", "dep_imbalance",
               "support_minus_resist", "support_wall_dist",
               "support_wall_size", "dep_thickness_delta_5m"]


# ---------------------------------------------------------------- depth ----
def depth_index() -> dict:
    idx = {}
    for p in glob.glob(str(ROOT / "data/reference/depth_20*/nq_depth_*_ny.csv")):
        m = re.search(r"(20\d\d-\d\d-\d\d)", p)
        if m:
            idx.setdefault(m.group(1), {})["ny"] = p
    for p in glob.glob(str(ROOT / "data/reference/depth_london*/glbx-*.csv")):
        m = re.search(r"(20\d\d)(\d\d)(\d\d)", os.path.basename(p))
        if m:
            idx.setdefault(f"{m.group(1)}-{m.group(2)}-{m.group(3)}",
                           {})["mbp"] = p
    return idx


def load_book_frames(paths: dict):
    """-> list of (minute, DataFrame[price,size,side]) sorted by minute."""
    out = {}
    if "ny" in paths:
        d = pd.read_csv(paths["ny"])
        d["ts"] = pd.to_datetime(d.ts, utc=True).dt.tz_convert(NY).dt.floor("min")
        for t, g in d.groupby("ts"):
            out[t] = g[["price", "size", "side"]]
    if "mbp" in paths:
        cols = ["ts_event"] + [f"{s}_px_0{i}" for s in ("bid", "ask")
                               for i in range(10)] \
               + [f"{s}_sz_0{i}" for s in ("bid", "ask") for i in range(10)]
        try:
            d = pd.read_csv(paths["mbp"], usecols=lambda c: c in cols)
        except Exception:
            d = None
        if d is not None and len(d):
            d["ts"] = pd.to_datetime(d.ts_event, utc=True).dt.tz_convert(NY)\
                .dt.floor("min")
            d = d.groupby("ts").last()
            for t, r in d.iterrows():
                rows = []
                for i in range(10):
                    for s in ("bid", "ask"):
                        px, sz = r.get(f"{s}_px_0{i}"), r.get(f"{s}_sz_0{i}")
                        if pd.notna(px) and pd.notna(sz):
                            rows.append((float(px), float(sz), s))
                if rows:
                    out.setdefault(t, pd.DataFrame(
                        rows, columns=["price", "size", "side"]))
    return out


def depth_at(books: dict, minute: pd.Timestamp, entry: float, d: int,
             day_med: float) -> dict:
    """Book features as-of the last snapshot <= minute (never after)."""
    keys = [k for k in books if k <= minute]
    if not keys:
        return {}
    b = books[max(keys)]
    bids = b[b.side.isin(["bid", "B"])]
    asks = b[b.side.isin(["ask", "A"])]
    bd, ad = bids["size"].sum(), asks["size"].sum()
    tot = bd + ad
    if tot <= 0:
        return {}
    f = {"dep_thickness": tot,
         "dep_imbalance": (bd - ad) / tot,
         "dep_thickness_vs_day": tot / day_med if day_med else np.nan}
    sup, res = (bd, ad) if d > 0 else (ad, bd)
    f["support_minus_resist"] = sup - res
    below, above = b[b.price < entry], b[b.price > entry]
    if len(below):
        w = below.loc[below["size"].idxmax()]
        f["dep_wall_below_d"] = float(entry - w.price)
        f["dep_wall_below_sz"] = float(w["size"])
    if len(above):
        w = above.loc[above["size"].idxmax()]
        f["dep_wall_above_d"] = float(w.price - entry)
        f["dep_wall_above_sz"] = float(w["size"])
    sd, ss = ("dep_wall_below_d", "dep_wall_below_sz") if d > 0 else \
             ("dep_wall_above_d", "dep_wall_above_sz")
    f["support_wall_dist"] = f.get(sd, np.nan)
    f["support_wall_size"] = f.get(ss, np.nan)
    k5 = [k for k in books if k <= minute - pd.Timedelta(minutes=5)]
    if k5:
        f["dep_thickness_delta_5m"] = tot - books[max(k5)]["size"].sum()
    return f


# ------------------------------------------------------------- in-trade ----
def intrade(fpd: pd.DataFrame, t_entry: pd.Timestamp, d: int,
            entry: float) -> dict:
    out = {}
    if fpd is None or not len(fpd):
        return out
    for N in HORIZONS:
        w = fpd[(fpd.index >= t_entry) & (fpd.index <= t_entry
                                          + pd.Timedelta(minutes=N))]
        if len(w) < 1:
            continue
        cum = float(w.delta.sum()) * d
        last = float(w.delta.iloc[-1]) * d
        buy = float(w.b.sum())
        sell = float(w.a.sum())
        ratio = ((buy - sell) / (buy + sell)) * d if (buy + sell) > 0 else 0.0
        sig = [cum > 0, last > 0, ratio > 0]
        if len(w) >= 3:
            cd = w.delta.cumsum().to_numpy()
            sl = float(np.polyfit(np.arange(len(cd)), cd, 1)[0]) * d
            sig.append(sl > 0)
            out[f"it{N}_slope"] = sl
        out[f"it{N}_cum"] = cum
        out[f"it{N}_last"] = last
        out[f"it{N}_ratio"] = ratio
        out[f"it{N}_concord"] = int(sum(bool(x) for x in sig))
        out[f"it{N}_nsig"] = len(sig)
        # adverse-at-N uses BAR data, added later (price, not flow)
    return out


def build() -> pd.DataFrame:
    F = pd.read_parquet(ROOT / "output/htf_ma_census/levels_fit.parquet")
    P = pd.read_parquet(PAIRS)
    F5 = F.join(assign(F, P, 0.5))
    val = book(F5[F5.locus == "val"], "break")
    vm1 = book(F5[F5.locus == "vwap_m1"], "break")
    ub = pd.concat([val, vm1]).drop_duplicates(["sess_day", "t", "side"])
    rej = book(F5[F5.locus == "bbma15"], "reject")
    comp = pd.concat([ub.assign(pop="union_break"), rej.assign(pop="reject")],
                     ignore_index=True)
    comp["t"] = pd.to_datetime(comp.t)
    comp["t_entry"] = pd.to_datetime(comp.t_entry)
    print(f"composite: {len(comp)} fights over "
          f"{comp.sess_day.nunique()} days", flush=True)

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    fp = pd.read_parquet(ROOT / "output/fp_minutes_full.parquet").sort_index()
    didx = depth_index()

    recs = []
    days = sorted(comp.sess_day.unique())
    for k, day in enumerate(days):
        D = comp[comp.sess_day == day]
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                    & (bars.index < t1)]
        if hist.empty:
            continue
        seg = hist[(hist.index >= t0) & (hist.index < t1)]
        fpd = fp[(fp.index >= t0 - pd.Timedelta(hours=30)) & (fp.index < t1)]
        f15 = hist.resample("15min", label="right", closed="left").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last"}).dropna()
        f15 = f15[(f15.index > t0) & (f15.index <= t1)]
        fp15 = fpd.resample("15min", label="right", closed="left").agg(
            {"vol": "sum", "delta": "sum"}).dropna() if len(fpd) else None
        # depth books for the two covered calendar dates this session spans
        books = {}
        med = {}
        for cal in {t0.strftime("%Y-%m-%d"),
                    (t0 + pd.Timedelta(days=1)).strftime("%Y-%m-%d")}:
            if cal in didx:
                bb = load_book_frames(didx[cal])
                books.update(bb)
        if books:
            tot = [v["size"].sum() for v in books.values()]
            med_all = float(np.median(tot)) if tot else np.nan
        else:
            med_all = np.nan

        for r in D.itertuples():
            rec = {"sess_day": day, "t": r.t, "pop": r.pop, "arm": r.arm,
                   "side": r.side, "direction": int(r.direction),
                   "out_ship": r.out_ship, "mfe_r": r.mfe_r, "risk": r.risk,
                   "w15": r.w15, "session": r.session, "scid": r.scid,
                   "entry": r.entry, "t_entry": r.t_entry}
            if r.t in f15.index:
                b_ = f15.loc[r.t]
                rec.update(flow_features(
                    fpd, r.t - pd.Timedelta(minutes=15), r.t,
                    int(r.direction),
                    fp15[fp15.index < r.t] if fp15 is not None else None,
                    bar_ohlc=b_, prior_ohlc=f15[f15.index < r.t]))
            if books and pd.notna(r.entry):
                dm = r.t - pd.Timedelta(minutes=1)
                rec.update(depth_at(books, dm, float(r.entry),
                                    int(r.direction), med_all))
            if pd.notna(r.t_entry):
                rec.update(intrade(fpd, r.t_entry, int(r.direction),
                                   float(r.entry)))
                # adverse-at-N from BARS (price state, the conditioner)
                for N in HORIZONS:
                    tN = r.t_entry + pd.Timedelta(minutes=N)
                    s = seg[(seg.index >= r.t_entry) & (seg.index <= tN)]
                    if len(s):
                        rec[f"px{N}"] = float(s.close.iloc[-1])
                        rec[f"adv{N}"] = bool(
                            int(r.direction) * (s.close.iloc[-1] - r.entry) < 0)
            recs.append(rec)
        if k % 40 == 0:
            print(f"  {k}/{len(days)} days...", flush=True)
    X = pd.DataFrame(recs)
    X.to_parquet(FRAME, index=False)
    print(f"frame: {len(X):,} rows x {len(X.columns)} cols -> {FRAME}")
    return X


# --------------------------------------------------------------- scoring ---
def boot_mean(df, col="out_ship", draws=DRAWS, alpha=0.05):
    g = df.groupby("sess_day")[col].agg(["sum", "size"])
    s, n = g["sum"].to_numpy(), g["size"].to_numpy()
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(s), (draws, len(s)))
    st = s[i].sum(1) / np.maximum(n[i].sum(1), 1)
    return (float(np.percentile(st, 100 * alpha / 2)),
            float(np.percentile(st, 100 * (1 - alpha / 2))))


def main() -> None:
    X = build() if ("--build" in sys.argv or not FRAME.exists()) \
        else pd.read_parquet(FRAME)
    X["era"] = np.where(X.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    sp = pd.read_csv(ROOT / "output/htf_ma_census/cutstudy_split.csv",
                     dtype=str)
    h1 = set(sp[sp.half == "1"].sess_day)
    ALPHA = 0.05 / NCAND                      # Bonferroni x10, declared
    EV = X.out_ship.mean()
    print(f"\ncomposite EV {EV:+.3f}R over {len(X):,} fights | "
          f"Bonferroni x{NCAND} -> CI at {100*(1-ALPHA):.1f}%")

    # ---- B1 CONCORDANCE COUNT ----------------------------------------
    med = {c: X[c].median() for c in MAG}
    agree = pd.DataFrame(index=X.index)
    for c in CONF_BIN:
        agree[c] = (X[c] == 1).astype(float)
    agree["bp5opp"] = (X["bp5opp"] == 0).astype(float)
    for c in ("cvd_slope30", "delta_z"):
        agree[c] = (X[c] > 0).astype(float)
    for c in MAG:
        agree[c] = (X[c] >= med[c]).astype(float)
    agree["closeloc"] = (X["closeloc"] >= 0.5).astype(float)
    X["CONCORD"] = agree.sum(axis=1)
    print("\n=== B1 — FLOW CONCORDANCE COUNT (monotone first, Law 8) ===")
    print(f"{'arm':12s} {'CONCORD':>8s} {'n':>6s} {'EV':>8s} "
          f"{'H2-2025':>9s} {'H1-2026':>9s}")
    for arm, g in X.groupby("arm"):
        for lo_, hi_ in ((0, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 12)):
            s = g[(g.CONCORD >= lo_) & (g.CONCORD <= hi_)]
            if len(s) < 40:
                continue
            e2 = {e: gg.out_ship.mean() for e, gg in s.groupby("era")}
            lab = f"{lo_}-{hi_}" if lo_ != hi_ else f"{lo_}"
            print(f"{arm:12s} {lab:>8s} {len(s):6d} {s.out_ship.mean():+8.3f} "
                  f"{e2.get('H2-2025',np.nan):+9.3f} "
                  f"{e2.get('H1-2026',np.nan):+9.3f}")
        rho = g[["CONCORD", "out_ship"]].corr(method="spearman").iloc[0, 1]
        print(f"{arm:12s} {'spearman':>8s} {len(g):6d} {rho:+8.3f}")

    print("\n  -- B1 gate arithmetic (Law 7), per threshold, whole book --")
    print(f"{'cut CONCORD <':>14s} {'q':>6s} {'muCut':>8s} {'lift':>8s} "
          f"{'EVafter':>8s} {'H1 lift':>8s} {'H2 lift':>8s} verdict")
    for thr in range(4, 9):
        m = X.CONCORD < thr
        q = m.mean()
        if q < 0.02 or q > 0.7:
            continue
        mu = X.out_ship[m].mean()
        lift = q * (EV - mu) / (1 - q)
        lifts = {}
        for hn, dset in (("h1", h1), ("h2", None)):
            sub = X[X.sess_day.isin(h1)] if dset else X[~X.sess_day.isin(h1)]
            mm = sub.CONCORD < thr
            qq = mm.mean()
            lifts[hn] = qq * (sub.out_ship.mean()
                              - sub.out_ship[mm].mean()) / (1 - qq)
        v = "SURVIVOR-h1" if lifts["h1"] >= 0.05 else "lift<bar"
        print(f"{thr:>14d} {q*100:5.1f}% {mu:+8.3f} {lift:+8.3f} "
              f"{X.out_ship[~m].mean():+8.3f} {lifts['h1']:+8.3f} "
              f"{lifts['h2']:+8.3f} {v}")

    # ---- B2 / B3 DEPTH ------------------------------------------------
    E = X[X.dep_imbalance.notna()].copy()
    print(f"\n=== B2/B3 — DEPTH, eligible subpopulation ===")
    print(f"  eligible {len(E)} of {len(X)} ({len(E)/len(X)*100:.1f}%) | "
          f"EV {E.out_ship.mean():+.3f} vs book {EV:+.3f}")
    if len(E) > 80:
        lo, hi = boot_mean(E, alpha=ALPHA)
        print(f"  eligible base rate {E.out_ship.mean():+.3f} "
              f"[{lo:+.3f},{hi:+.3f}] (x{NCAND}-corrected)")
        wall = (E.dep_wall_below_d < 2.75) | (E.support_wall_size == 0)
        print(f"\n  B2 wall-quality cut  `dep_wall_below_d<2.75 OR WALLSZ==0`")
        print(f"{'arm':12s} {'cut%':>6s} {'muCut':>8s} {'kept EV':>8s} "
              f"{'elig lift':>10s} {'book lift':>10s} {'cutWin%':>8s}")
        for arm, g in E.groupby("arm"):
            m = ((g.dep_wall_below_d < 2.75) | (g.support_wall_size == 0))
            if m.sum() < 20 or (~m).sum() < 20:
                print(f"{arm:12s}  UNDERPOWERED (cut {m.sum()}/{len(g)})")
                continue
            q = m.mean()
            mu = g.out_ship[m].mean()
            el = q * (g.out_ship.mean() - mu) / (1 - q)
            qb = m.sum() / len(X)
            bl = qb * (EV - mu) / (1 - qb)
            print(f"{arm:12s} {q*100:5.1f}% {mu:+8.3f} "
                  f"{g.out_ship[~m].mean():+8.3f} {el:+10.3f} {bl:+10.3f} "
                  f"{(g.out_ship[m]>0).mean()*100:7.1f}%")
        print("\n  B3 depth features, bottom-quartile cut (edges on half 1)")
        print(f"{'feature':24s} {'cut%':>6s} {'muCut':>8s} {'elig lift':>10s} "
              f"{'book lift':>10s}")
        E1 = E[E.sess_day.isin(h1)]
        for c in DEPTH_FEATS:
            if c not in E or E[c].notna().sum() < 80:
                print(f"{c:24s}  absent/underpowered")
                continue
            thr = E1[c].quantile(.25) if len(E1) > 40 else E[c].quantile(.25)
            m = E[c] < thr
            if m.sum() < 20:
                continue
            q, mu = m.mean(), E.out_ship[m].mean()
            el = q * (E.out_ship.mean() - mu) / (1 - q)
            qb = m.sum() / len(X)
            bl = qb * (EV - mu) / (1 - qb)
            print(f"{c:24s} {q*100:5.1f}% {mu:+8.3f} {el:+10.3f} {bl:+10.3f}")

    # ---- C IN-TRADE ---------------------------------------------------
    print("\n=== C1 — IN-TRADE: do flow signals separate recoverers? ===")
    print(f"{'N':>3s} {'underwater':>10s} {'P(recov)':>9s} | "
          f"{'flag=cum>0':>11s} {'prec':>6s} {'recall':>7s} | "
          f"{'CONCORD>=3':>11s} {'prec':>6s} {'recall':>7s}")
    for N in HORIZONS:
        a, c = f"adv{N}", f"it{N}_cum"
        if a not in X or c not in X:
            continue
        U = X[(X[a] == True) & X[c].notna()]              # noqa: E712
        if len(U) < 60:
            continue
        rec = U.out_ship > 0
        base = rec.mean()
        row = f"{N:3d} {len(U):10d} {base*100:8.1f}% |"
        for lab, flag in (("cum>0", U[c] > 0),
                          ("conc>=3", U.get(f"it{N}_concord", 0) >= 3)):
            if flag.sum() < 10:
                row += f" {'--':>11s} {'--':>6s} {'--':>7s} |"
                continue
            prec = rec[flag].mean()
            recall = flag[rec].mean()
            row += (f" {flag.mean()*100:10.1f}% {prec*100:5.1f}% "
                    f"{recall*100:6.1f}% |")
        print(row)
    print("\n  EV of underwater trades by IN-CONCORD (t+5), both arms:")
    U = X[(X.adv5 == True) & X.it5_concord.notna()]        # noqa: E712
    for k, g in U.groupby("it5_concord"):
        if len(g) < 30:
            continue
        print(f"    concord {int(k)}: n={len(g):5d} EV {g.out_ship.mean():+.3f} "
              f"| P(recover) {(g.out_ship>0).mean()*100:.1f}%")

    print("\n=== C2 — the +2R-then-stopped tell (prior: expect little) ===")
    T = X[(X.mfe_r >= 2.0) & X.it10_cum.notna()]
    for lab, g in (("finished POSITIVE", T[T.out_ship > 0]),
                   ("finished NEGATIVE", T[T.out_ship <= 0])):
        if len(g) < 30:
            continue
        print(f"  {lab:20s} n={len(g):5d} | it5_cum {g.it5_cum.mean():+9.1f} "
              f"| it10_cum {g.it10_cum.mean():+9.1f} | "
              f"it10_concord {g.it10_concord.mean():.2f}")


if __name__ == "__main__":
    main()
