#!/usr/bin/env python3
"""PER-SESSION BOOKS — scored, selected and risk-budgeted SEPARATELY.

Three books. Never pooled, never averaged.

    LONDON   03:00-04:59 NY   composite + sweep_b
    NY_PRE   08:00-09:29 NY   composite only
    NY_AM    09:30-10:30 NY   composite only

sweep_b is included in LONDON ONLY, on two declared grounds: (1) its NY
cell is era-asymmetric (H2-2025 +0.247 clears, H1-2026 +0.095 does not)
while its London cell clears both; (2) sweep_b is conditioned on a prior
stop-out, and that conditionality is not something to carry into the
session where most of the frequency would come from.

Risk metric (declared): the DAILY TOTAL R per session book against the
$2,000 EOD drawdown expressed in R at each candidate size. The question is
whether a SINGLE SESSION can breach, not whether positions overlap.

    python -m scripts.htf_ma_session_books [--build]
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
from scripts.htf_ma_flow_depth_run import (CONF_BIN, DEPTH_FEATS,   # noqa: E402
                                           HORIZONS, MAG, boot_mean,
                                           depth_at, depth_index,
                                           intrade, load_book_frames)
from scripts.htf_ma_mtable import flow_features                     # noqa: E402
from src.htf_ma.levels import NY                                    # noqa: E402

SWEEP_FRAME = ROOT / "output/htf_ma_census/sweepb_london_frame.parquet"
SESSIONS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (570, 630)}
SIZES = [150, 300, 450, 600]
DD_USD = 2000.0
SEED, DRAWS, YEAR = 20260807, 1500, 250


# ------------------------------------------------------------ sweep_b -----
def cluster_sweepb() -> pd.DataFrame:
    S = pd.read_parquet(ROOT / "output/htf_ma_census/sweep_fit.parquet")
    S = S[(S.cell == "sweep_b") & S.out_ship.notna() & (S.risk > 0)].copy()
    S["t"] = pd.to_datetime(S.t)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    key = {}
    for day, D in S.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        seg = bars[(bars.index >= t0) & (bars.index < t0 + pd.Timedelta(hours=23))]
        if seg.empty:
            continue
        idx, hi, lo = seg.index, seg.high.to_numpy(), seg.low.to_numpy()
        for side, g in D.groupby("side"):
            g = g.sort_values("t")
            ts, ws, rp = g.t.tolist(), g.w15.tolist(), g.ref_px.tolist()
            for a in range(len(ts) - 1):
                i0 = int(np.searchsorted(idx.values, ts[a].to_datetime64()))
                i1 = int(np.searchsorted(idx.values, ts[a + 1].to_datetime64()))
                if i1 <= i0 or ws[a] <= 0 or not np.isfinite(rp[a]):
                    continue
                m = np.nanmax(np.maximum(np.abs(hi[i0:i1] - rp[a]),
                                         np.abs(lo[i0:i1] - rp[a])))
                key[(day, side, ts[a + 1])] = m / ws[a]
    ids = {}
    for (d, s), g in S.groupby(["sess_day", "side"], sort=False):
        g = g.sort_values("t")
        cid, seen = 0, None
        for r in g.itertuples():
            t = pd.Timestamp(r.t)
            if seen is not None and t != seen:
                e = key.get((d, s, t), np.nan)
                if not np.isfinite(e) or e >= 0.5:
                    cid += 1
            seen = t
            ids[r.Index] = f"{d}:{s}:S{cid}"
    S["scid"] = pd.Series(ids)
    return S.sort_values("t").groupby("scid", as_index=False).first()


def build_sweepb_features() -> pd.DataFrame:
    """Same feature code path as bc_frame, restricted to LONDON sweep_b."""
    SB = cluster_sweepb()
    SB["hm"] = SB.t.dt.hour * 60 + SB.t.dt.minute
    SB = SB[(SB.hm >= 180) & (SB.hm < 300)].copy()
    SB["t_entry"] = pd.to_datetime(SB.t_entry)
    print(f"sweep_b LONDON fights: {len(SB)}", flush=True)
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    fp = pd.read_parquet(ROOT / "output/fp_minutes_full.parquet").sort_index()
    didx = depth_index()
    recs = []
    days = sorted(SB.sess_day.unique())
    for k, day in enumerate(days):
        D = SB[SB.sess_day == day]
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
        books = {}
        for cal in {t0.strftime("%Y-%m-%d"),
                    (t0 + pd.Timedelta(days=1)).strftime("%Y-%m-%d")}:
            if cal in didx:
                books.update(load_book_frames(didx[cal]))
        med = float(np.median([v["size"].sum() for v in books.values()])) \
            if books else np.nan
        for r in D.itertuples():
            rec = {"sess_day": day, "t": r.t, "pop": "sweep_b", "arm": "sweep",
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
                rec.update(depth_at(books, r.t - pd.Timedelta(minutes=1),
                                    float(r.entry), int(r.direction), med))
            if pd.notna(r.t_entry):
                rec.update(intrade(fpd, r.t_entry, int(r.direction),
                                   float(r.entry)))
                for N in HORIZONS:
                    s = seg[(seg.index >= r.t_entry)
                            & (seg.index <= r.t_entry + pd.Timedelta(minutes=N))]
                    if len(s):
                        rec[f"adv{N}"] = bool(int(r.direction)
                                              * (s.close.iloc[-1] - r.entry) < 0)
            recs.append(rec)
        if k % 60 == 0:
            print(f"  sweep_b {k}/{len(days)}...", flush=True)
    X = pd.DataFrame(recs)
    X.to_parquet(SWEEP_FRAME, index=False)
    return X


# ------------------------------------------------------------- scoring ----
def concord(X: pd.DataFrame) -> pd.Series:
    a = pd.DataFrame(index=X.index)
    for c in CONF_BIN:
        a[c] = (X[c] == 1).astype(float)
    a["bp5opp"] = (X["bp5opp"] == 0).astype(float)
    for c in ("cvd_slope30", "delta_z"):
        a[c] = (X[c] > 0).astype(float)
    for c in MAG:
        a[c] = (X[c] >= X[c].median()).astype(float)
    a["closeloc"] = (X["closeloc"] >= 0.5).astype(float)
    return a.sum(axis=1)


def grad(days: np.ndarray, pol: dict) -> tuple:
    rng = np.random.default_rng(SEED)
    seqs = [rng.integers(0, len(days), YEAR) for _ in range(DRAWS)]
    runs = [AL.run_account(days, s, pol, payout_at=6000.) for s in seqs]
    return (float(np.mean([r["end_state"] == "graduated" for r in runs])),
            float(np.mean([len(r["funded_deaths"]) > 0 for r in runs])),
            float(np.mean([sum(w for _, w in r["wd"]) - r["fees"]
                           for r in runs])))


def main() -> None:
    C = pd.read_parquet(ROOT / "output/htf_ma_census/bc_frame.parquet")
    C["t"] = pd.to_datetime(C.t)
    if "--build" in sys.argv or not SWEEP_FRAME.exists():
        SB = build_sweepb_features()
    else:
        SB = pd.read_parquet(SWEEP_FRAME)
    SB["t"] = pd.to_datetime(SB.t)
    for D in (C, SB):
        D["hm"] = D.t.dt.hour * 60 + D.t.dt.minute
        D["era"] = np.where(D.sess_day < "2026-01-01", "H2-2025", "H1-2026")
    all_days = pd.Index(sorted(C.sess_day.unique()))
    nd = len(all_days)

    books = {}
    for name, (a, b) in SESSIONS.items():
        comp = C[(C.hm >= a) & (C.hm <= b)]
        if name == "LONDON":
            sw = SB[(SB.hm >= a) & (SB.hm <= b)]
            bk = pd.concat([comp, sw], ignore_index=True)\
                .drop_duplicates(["sess_day", "t", "side"])
        else:
            bk = comp.copy()
        books[name] = bk

    print(f"\n{'='*78}\nPER-SESSION BOOKS — scored separately, never pooled "
          f"({nd} session-days)\n{'='*78}")
    for name, bk in books.items():
        d = bk.groupby("sess_day").out_ship.sum().reindex(all_days,
                                                          fill_value=0.0)
        n = bk.groupby("sess_day").size().reindex(all_days, fill_value=0)
        lo, hi = boot_mean(bk)
        comp_n = int((bk["pop"] == "sweep_b").sum()) if "pop" in bk.columns else 0
        print(f"\n-- {name}  ({SESSIONS[name][0]//60:02d}:"
              f"{SESSIONS[name][0]%60:02d}-{SESSIONS[name][1]//60:02d}:"
              f"{SESSIONS[name][1]%60:02d} NY)"
              + (f"  [incl. {comp_n} sweep_b]" if comp_n else ""))
        print(f"   {len(bk)} fights | {len(bk)/nd:.2f}/day | "
              f"EV {bk.out_ship.mean():+.3f} [{lo:+.3f},{hi:+.3f}]")
        for era, g in bk.groupby("era"):
            l2, h2 = boot_mean(g)
            print(f"     {era}: {g.out_ship.mean():+.3f} [{l2:+.3f},{h2:+.3f}]"
                  + ("!" if l2 > 0 else ""))
        print(f"   trades/day median {n.median():.0f} p90 {n.quantile(.9):.0f}"
              f" max {n.max()} | zero-days {(n==0).sum()}/{nd}")
        print(f"   DAILY R: mean {d.mean():+.2f} | p05 {d.quantile(.05):+.2f}"
              f" | p01 {d.quantile(.01):+.2f} | WORST {d.min():+.2f} | "
              f"P(day>0) {(d>0).mean()*100:.0f}%")

    print(f"\n{'='*78}\nRISK: can a SINGLE SESSION breach the $2,000 EOD "
          f"drawdown?\n{'='*78}")
    print(f"{'book':8s} {'size':>5s} {'DD in R':>8s} {'worst day R':>12s} "
          f"{'worst $':>9s} {'breach days':>12s} {'P(breach/day)':>14s}")
    for name, bk in books.items():
        d = bk.groupby("sess_day").out_ship.sum().reindex(all_days,
                                                          fill_value=0.0)
        for sz in SIZES:
            ddr = DD_USD / sz
            br = (d <= -ddr).sum()
            print(f"{name:8s} {sz:5d} {ddr:8.2f} {d.min():+12.2f} "
                  f"{d.min()*sz:+9,.0f} {br:9d}/{nd} "
                  f"{br/nd*100:13.2f}%"
                  + ("   <-- BREACHES" if br else ""))

    print(f"\n{'='*78}\nP(GRADUATE) per session book, at its own frequency"
          f"\n{'='*78}")
    pols = (("flat 150", {"s_pre": 150., "s_post": 150.}),
            ("cushion k=.05", {"s_pre": 150., "mode": "cushion", "k": 0.05,
                               "s_min": 150., "s_max": 300.}))
    print(f"{'book':8s} {'policy':16s} {'GRAD':>7s} {'P(death)':>9s} "
          f"{'net':>9s}")
    for name, bk in books.items():
        d = bk.groupby("sess_day").out_ship.sum().reindex(
            all_days, fill_value=0.0).to_numpy()
        for pn, pol in pols:
            g, dth, net = grad(d, pol)
            print(f"{name:8s} {pn:16s} {g*100:6.1f}% {dth*100:8.1f}% "
                  f"${net:8,.0f}")

    print(f"\n{'='*78}\nSELECTION VARIABLES RE-SCORED PER SESSION\n{'='*78}")
    print("  lift = q*(EV-muCut)/(1-q) within that session's own book")
    for name, bk in books.items():
        bk = bk.copy()
        if bk.flowconf.notna().sum() > 30:
            bk["CONCORD"] = concord(bk)
        EV = bk.out_ship.mean()
        print(f"\n-- {name}  (book EV {EV:+.3f}, n={len(bk)})")
        print(f"   {'variable':26s} {'q':>6s} {'muCut':>8s} {'lift':>8s} "
              f"{'EVafter':>8s}")
        cands = [("S1 flowconf==0", bk.flowconf == 0),
                 ("CONCORD<5", bk.get("CONCORD", pd.Series(np.nan,
                                                           index=bk.index)) < 5),
                 ("CONCORD<7", bk.get("CONCORD", pd.Series(np.nan,
                                                           index=bk.index)) < 7),
                 ("closeloc<Q1", bk.closeloc < bk.closeloc.quantile(.25))]
        for c in DEPTH_FEATS:
            if c in bk and bk[c].notna().sum() >= 40:
                cands.append((f"{c}<Q1", bk[c] < bk[c].quantile(.25)))
        for lab, m in cands:
            m = m.fillna(False)
            if m.sum() < 15 or (~m).sum() < 15:
                print(f"   {lab:26s}   n/a (bin {int(m.sum())})")
                continue
            q, mu = m.mean(), bk.out_ship[m].mean()
            print(f"   {lab:26s} {q*100:5.1f}% {mu:+8.3f} "
                  f"{q*(EV-mu)/(1-q):+8.3f} {bk.out_ship[~m].mean():+8.3f}")
        # in-trade recovery, per session
        if "adv5" in bk and "it5_cum" in bk:
            U = bk[(bk.adv5 == True) & bk.it5_cum.notna()]      # noqa: E712
            if len(U) >= 40:
                rec = U.out_ship > 0
                fl = U.it5_cum > 0
                print(f"   in-trade t+5: underwater n={len(U)} "
                      f"P(recover) {rec.mean()*100:.1f}% | flag fires "
                      f"{fl.mean()*100:.0f}% precision "
                      f"{rec[fl].mean()*100:.1f}% recall "
                      f"{fl[rec].mean()*100:.1f}%")


if __name__ == "__main__":
    main()
