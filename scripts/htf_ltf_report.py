#!/usr/bin/env python3
"""LTF CONJUNCTION CENSUS — the report (DECLARATIONS-ltf-trigger-recensus).

Reads output/htf_ma_census/ltf_fit.parquet and prints, in declaration order:

  0  pre-flight recap: cells, rows, powered-ness of every (A)^(B) cell
  1  the 168-cell (A)-only table, per session x TF x locus x arm, both eras
  2  D1a — (B)'s MARGINAL lift on the (A) population, per (session, TF),
     with the dual-currency (win-rate) column alongside
  3  D2 — stop width under BOTH rulers (W15 and points), per TF
  4  D6 — cost_R distribution and EV at 0.5 / 1.0 / 1.5 pt per round trip
  5  prediction check: fights/day, stop width, MFE-in-R, partial placement
  6  D4 — clustering valley re-derived per (TF, session)
  7  D7 — target-admissibility as a column
  8  D3 — TF sign-agreement across all four timeframes

Fights are structural, per (day, TF, locus, side), exactly as the 15m
census: two same-side triggers are one fight unless price left THAT locus
by >= X*W15 between them. X sensitivity {0.25, 0.5, 1.0, 2.0} throughout.

    python -m scripts.htf_ltf_report [--build-pairs] [--x 0.5]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_level_census import LOCI, level_series          # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402

FIT = ROOT / "output/htf_ma_census/ltf_fit.parquet"
PAIRS = ROOT / "output/htf_ma_census/ltf_cluster_pairs.parquet"
XS = [0.25, 0.5, 1.0, 2.0]
TFS = [1, 2, 3, 5, 15]      # 15 is the control column, never a candidate
SESS = ["LONDON", "NY_PRE", "NY_AM"]
SEED, DRAWS = 20260807, 2000
XDEC = 0.5                       # the declared X
BAR_B = 0.05                     # D1a: marginal lift bar for (B)


def era(d):
    return np.where(d.sess_day < "2026-01-01", "H2-2025", "H1-2026")


# --------------------------------------------------------- bootstrapping --
def _daysums(df, col):
    g = df.groupby("sess_day")[col].agg(["sum", "size"])
    return g["sum"].to_numpy(), g["size"].to_numpy()


def boot_mean(df, col="out_ship"):
    """Day-level bootstrap of a mean — same estimator/unit as the 15m
    report's boot_mean (resample session-days with replacement)."""
    s, n = _daysums(df, col)
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(s), (DRAWS, len(s)))
    tot, cnt = s[i].sum(1), n[i].sum(1)
    st = np.divide(tot, cnt, out=np.full(DRAWS, np.nan), where=cnt > 0)
    return float(np.nanpercentile(st, 2.5)), float(np.nanpercentile(st, 97.5))


def boot_lift(A, keep, col="out_ship"):
    """Day-level bootstrap of (B)'s MARGINAL lift, PAIRED on the day draw.

    D1a defines lift = q(EV_A - mu_fail)/(1-q) with q the share of (A)
    failing (B). That expression is algebraically identical to
    EV_kept - EV_A, so it is computed and resampled in that form: the SAME
    resampled days feed both terms, which is what makes the CI a CI on the
    difference rather than on two independent means."""
    days = np.array(sorted(A.sess_day.unique()))
    di = {d: i for i, d in enumerate(days)}
    sA = np.zeros(len(days)); nA = np.zeros(len(days))
    sK = np.zeros(len(days)); nK = np.zeros(len(days))
    for d, g in A.groupby("sess_day"):
        sA[di[d]] = g[col].sum(); nA[di[d]] = len(g)
    for d, g in keep.groupby("sess_day"):
        sK[di[d]] = g[col].sum(); nK[di[d]] = len(g)
    if len(days) < 3 or nK.sum() == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(days), (DRAWS, len(days)))
    evA = sA[i].sum(1) / np.maximum(nA[i].sum(1), 1)
    ck = nK[i].sum(1)
    evK = np.divide(sK[i].sum(1), ck, out=np.full(DRAWS, np.nan), where=ck > 0)
    st = evK - evA
    return float(np.nanpercentile(st, 2.5)), float(np.nanpercentile(st, 97.5))


# --------------------------------------------------------------- fights --
def build_pairs(F: pd.DataFrame) -> pd.DataFrame:
    """Max excursion away from the LOCUS between consecutive same-side
    triggers, in W15 units — per (day, TF, locus, side)."""
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]
    out, days = [], sorted(F.sess_day.unique())
    for k, day in enumerate(days):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                    & (bars.index < t1)]
        seg = hist[(hist.index >= t0) & (hist.index < t1)]
        if hist.empty or seg.empty:
            continue
        ma15, _ = bb_ma_asof(hist, 15)
        idx = seg.index
        hi, lo = seg.high.to_numpy(), seg.low.to_numpy()
        lv = level_series(hist, idx, ma15)
        D = F[F.sess_day == day]
        for (tf, locus, side), g in D.groupby(["tf", "locus", "side"]):
            lvl = lv[locus]
            g = g.drop_duplicates("t").sort_values("t")
            ts, ws = g.t.to_list(), g.w15.to_list()
            for a in range(len(ts) - 1):
                i0 = int(np.searchsorted(idx.values,
                                         pd.Timestamp(ts[a]).to_datetime64()))
                i1 = int(np.searchsorted(idx.values,
                                         pd.Timestamp(ts[a + 1]).to_datetime64()))
                if i1 <= i0 or ws[a] <= 0:
                    continue
                m = np.nanmax(np.maximum(np.abs(hi[i0:i1] - lvl[i0:i1]),
                                         np.abs(lo[i0:i1] - lvl[i0:i1])))
                out.append({"sess_day": day, "tf": int(tf), "locus": locus,
                            "side": side, "t_b": ts[a + 1],
                            "exc_w": float(m) / ws[a]})
        if k % 60 == 0:
            print(f"  pairs {k}/{len(days)}...", flush=True)
    P = pd.DataFrame(out)
    P.to_parquet(PAIRS, index=False)
    return P


def assign(F: pd.DataFrame, P: pd.DataFrame, x: float) -> pd.Series:
    key = {(r.sess_day, int(r.tf), r.locus, r.side, pd.Timestamp(r.t_b)):
           r.exc_w for r in P.itertuples()}
    ids = {}
    for (day, tf, locus, side), g in F.groupby(
            ["sess_day", "tf", "locus", "side"], sort=False):
        g = g.sort_values("t")
        cid, seen = 0, None
        for r in g.itertuples():
            t = pd.Timestamp(r.t)
            if seen is not None and t != seen:
                e = key.get((day, int(tf), locus, side, t), np.nan)
                if not np.isfinite(e) or e >= x:
                    cid += 1
            seen = t
            ids[r.Index] = f"{day}:{tf}:{locus}:{side}:S{cid}"
    return pd.Series(ids, name="scid")


def book(F: pd.DataFrame) -> pd.DataFrame:
    """Executable first-of-fight book. Both arms enter at the next 1m open
    here, so there is no retest filter — every fight has a fill."""
    R = F[F.out_ship.notna() & (F.risk > 0)]
    return R.sort_values("t").groupby("scid", as_index=False).first()


def cell(g):
    lo, hi = boot_mean(g)
    return (f"{g.out_ship.mean():+.3f}[{lo:+.3f},{hi:+.3f}]"
            + ("!" if lo > 0 else " "))


def main() -> None:
    x = XDEC
    if "--x" in sys.argv:
        x = float(sys.argv[sys.argv.index("--x") + 1])
    F = pd.read_parquet(FIT)
    F["t"] = pd.to_datetime(F.t)
    F["era"] = era(F)
    nd = F.sess_day.nunique()
    P = (build_pairs(F) if ("--build-pairs" in sys.argv or not PAIRS.exists())
         else pd.read_parquet(PAIRS))

    print(f"LTF CONJUNCTION CENSUS — fit {F.sess_day.min()}..{F.sess_day.max()},"
          f" {nd} days, {len(F):,} triggers with outcomes")
    print(f"clustering: structural fights per (day, TF, locus, side), "
          f"declared X = {x}W15\n")

    books = {}
    for xx in XS:
        Fx = F.copy()
        Fx["scid"] = assign(Fx, P, xx)
        books[xx] = book(Fx)
    B = books[x]

    # ------------------------------------------------------------ 0 ------
    print("=" * 78)
    print("0. POWERED-NESS OF EVERY (A)^(B) CELL — stated before any EV is read")
    print("=" * 78)
    n = (B[B.condB].groupby(["session", "arm", "locus", "tf"]).size()
         .unstack("tf").reindex(columns=TFS).fillna(0).astype(int))
    print(n.to_string())
    tot = n.size
    print(f"\n  cells with < 100 first-of-fight (A)^(B) rows: "
          f"{int((n < 100).sum().sum())} of {tot}")
    print(f"  cells with <  50: {int((n < 50).sum().sum())}   "
          f"cells with <  30: {int((n < 30).sum().sum())}")
    print("  => a per-LOCUS verdict on (B) is not statistically available at "
          "this n.\n     D1a declares the (B) test per (SESSION, TF), which "
          "pools loci; that is\n     the unit verdicted in section 2. "
          "Per-locus numbers are reported, not judged.")

    # ------------------------------------------------------------ 1 ------
    print("\n" + "=" * 78)
    print(f"1. THE 168-CELL (A)-ONLY TABLE — executable first-of-fight book, "
          f"shipped exit, X={x}W")
    print("   bar (E1.4): both-era day-boot CI clear of zero, '!' marks a "
          "clearing CI")
    print("=" * 78)
    for arm in ("reject", "break"):
        print(f"\n### {arm.upper()} ARM")
        for s in SESS:
            print(f"\n-- {s}")
            print(f"   {'locus':9s} {'tf':>3s} {'n':>5s} {'/day':>6s} "
                  f"{'EV':>8s}   {'H2-2025':>22s} {'H1-2026':>22s}  both")
            for locus in LOCI:
                for tf in TFS:
                    g = B[(B.session == s) & (B.arm == arm)
                          & (B.locus == locus) & (B.tf == tf)]
                    if len(g) < 3:
                        print(f"   {locus:9s} {tf:3d} {len(g):5d}  "
                              f"UNDERPOWERED")
                        continue
                    e2 = g[g.era == "H2-2025"]
                    e1 = g[g.era == "H1-2026"]
                    c2, c1 = cell(e2), cell(e1)
                    both = c2.endswith("!") and c1.endswith("!")
                    print(f"   {locus:9s} {tf:3d} {len(g):5d} {len(g)/nd:6.2f} "
                          f"{g.out_ship.mean():+8.3f}   {c2:>22s} {c1:>22s}  "
                          f"{'YES' if both else '.'}")

    # ------------------------------------------------------------ 2 ------
    print("\n" + "=" * 78)
    print("2. D1a — (B)'s MARGINAL LIFT ON THE (A) POPULATION")
    print(f"   declared bar: lift >= {BAR_B:+.2f}R AND the day-boot CI on the "
          f"LIFT clear of zero in BOTH eras")
    print("   lift = q(EV_A - mu_fail)/(1-q) == EV_kept - EV_A  (identity; "
          "bootstrapped paired)")
    print("   dual currency (Law 3): win rate of kept vs failed alongside EV")
    print("=" * 78)
    verdicts = []
    for arm in ("reject", "break"):
        print(f"\n### {arm.upper()} ARM")
        print(f"   {'sess':7s} {'tf':>3s} {'n_A':>5s} {'q':>6s} {'EV_A':>8s} "
              f"{'EV_keep':>8s} {'EV_fail':>8s} {'lift':>8s} "
              f"{'H2 lift CI':>20s} {'H1 lift CI':>20s} {'win k/f':>13s}  bar")
        for s in SESS:
            for tf in TFS:
                A = B[(B.session == s) & (B.arm == arm) & (B.tf == tf)]
                K, Ff = A[A.condB], A[~A.condB]
                if len(A) < 30 or len(K) < 10 or len(Ff) < 10:
                    print(f"   {s:7s} {tf:3d} {len(A):5d}  UNDERPOWERED "
                          f"(keep {len(K)}, fail {len(Ff)})")
                    continue
                q = len(Ff) / len(A)
                evA, evK, evF = (A.out_ship.mean(), K.out_ship.mean(),
                                 Ff.out_ship.mean())
                lift = evK - evA
                ok = []
                cis = []
                for e in ("H2-2025", "H1-2026"):
                    Ae, Ke = A[A.era == e], K[K.era == e]
                    lo, hi = boot_lift(Ae, Ke)
                    cis.append(f"[{lo:+.3f},{hi:+.3f}]"
                               + ("!" if lo > 0 else " "))
                    ok.append(np.isfinite(lo) and lo > 0)
                wk = (K.out_ship > 0).mean() * 100
                wf = (Ff.out_ship > 0).mean() * 100
                passed = (lift >= BAR_B) and all(ok)
                verdicts.append((arm, s, tf, lift, passed))
                print(f"   {s:7s} {tf:3d} {len(A):5d} {q:6.3f} {evA:+8.3f} "
                      f"{evK:+8.3f} {evF:+8.3f} {lift:+8.3f} "
                      f"{cis[0]:>20s} {cis[1]:>20s} "
                      f"{wk:5.1f}/{wf:5.1f}%  "
                      f"{'PASS' if passed else 'miss'}")
    npass = sum(1 for v in verdicts if v[4])
    print(f"\n   (B) CLEARS ITS DECLARED BAR IN {npass} of {len(verdicts)} "
          f"(session x TF x arm) cells.")
    if npass == 0:
        print("   VERDICT: (B) ADDS NOTHING. Per D1a the shipped trigger "
              "stays (A)-only.")

    # ------------------------------------------------------------ 3 ------
    print("\n" + "=" * 78)
    print("3. D2 — STOP WIDTH UNDER BOTH RULERS (the scale law made visible)")
    print("=" * 78)
    print(f"   {'tf':>3s} {'n':>6s} {'pts p25':>8s} {'p50':>7s} {'p75':>7s} "
          f"{'W15 p25':>8s} {'p50':>7s} {'p75':>7s}")
    for tf in TFS + [None]:
        g = B if tf is None else B[B.tf == tf]
        if not len(g):
            continue
        r = g.risk
        w = g.risk / g.w15
        print(f"   {('all' if tf is None else tf):>3} {len(g):6d} "
              f"{r.quantile(.25):8.2f} {r.median():7.2f} {r.quantile(.75):7.2f} "
              f"{w.quantile(.25):8.3f} {w.median():7.3f} {w.quantile(.75):7.3f}")
    print("   (15m incumbent for reference: median stop 0.17W)")

    # ------------------------------------------------------------ 4 ------
    print("\n" + "=" * 78)
    print("4. D6 — COSTS RE-PRICED IN R. If costs eat the tighter-stop "
          "advantage, THAT IS THE FINDING.")
    print("=" * 78)
    print(f"   {'tf':>3s} {'cost_R p50':>10s} {'p75':>7s} {'p90':>7s}  "
          f"{'EV@0.5pt':>9s} {'EV@1.0pt':>9s} {'EV@1.5pt':>9s}")
    for tf in TFS:
        g = B[B.tf == tf]
        if not len(g):
            continue
        c = 0.5 / g.risk
        base = g.out_ship
        print(f"   {tf:3d} {c.median():10.3f} {c.quantile(.75):7.3f} "
              f"{c.quantile(.9):7.3f}  {base.mean():+9.3f} "
              f"{(base - 0.5 / g.risk).mean():+9.3f} "
              f"{(base - 1.0 / g.risk).mean():+9.3f}")
    print("   (the census already prices 0.5pt inside out_ship; the 1.0/1.5pt "
          "columns\n    subtract the additional 0.5/1.0pt of round-trip cost)")

    # ---------------------------------------------------------- 4b ------
    print("\n" + "=" * 78)
    print("4b. WHY — THE STOP RULE ITSELF (not declared; found in the data "
          "and reported)")
    print("    Stop = the trigger candle's extreme +- 1 tick. At 15m that is "
          "~10pt. At 1m the")
    print("    candle's own range can be a point, so 'risk' stops being a "
          "risk unit: the stop")
    print("    is inside the noise AND cost_R = 0.5/risk explodes. This is a "
          "mechanical")
    print("    consequence of the stop rule, not a fact about short "
          "timeframes.")
    print("=" * 78)
    print(f"   {'tf':>3s} {'risk p05':>8s} {'p10':>6s} {'p25':>6s} {'p50':>6s} "
          f"| {'share <2pt':>10s} {'EV|<2pt':>9s} | {'EV|>=2pt':>9s} "
          f"{'book EV':>9s}")
    for tf in TFS:
        g = B[B.tf == tf]
        if not len(g):
            continue
        lo_, hi_ = g[g.risk < 2.0], g[g.risk >= 2.0]
        print(f"   {tf:3d} {g.risk.quantile(.05):8.2f} "
              f"{g.risk.quantile(.10):6.2f} {g.risk.quantile(.25):6.2f} "
              f"{g.risk.median():6.2f} | {len(lo_)/len(g)*100:9.1f}% "
              f"{(lo_.out_ship.mean() if len(lo_) else np.nan):+9.3f} | "
              f"{(hi_.out_ship.mean() if len(hi_) else np.nan):+9.3f} "
              f"{g.out_ship.mean():+9.3f}")
    print("\n   EV by risk quintile WITHIN each TF (quintile edges computed "
          "inside the TF):")
    for tf in TFS:
        g = B[B.tf == tf].copy()
        if len(g) < 100:
            continue
        g["qq"] = pd.qcut(g.risk, 5, labels=False, duplicates="drop")
        r = g.groupby("qq").agg(ev=("out_ship", "mean"),
                                med=("risk", "median"))
        print(f"   TF={tf:2d}  " + "  ".join(
            f"Q{int(i)+1}({r.med[i]:5.1f}pt){r.ev[i]:+.3f}" for i in r.index))
    print("\n   NOTE on closeloc: for a long, stop = candle low, so "
          "risk ~ closeloc x range.")
    print("   A candle that closed near its own stop has a near-zero risk "
          "denominator, so")
    print("   closeloc's large positive rank correlation with outcome is "
          "PARTLY mechanical.")
    print("   Any future use of closeloc must be measured on a "
          "risk-floored population.")

    # ------------------------------------------------------------ 5 ------
    print("\n" + "=" * 78)
    print("5. THE DECLARED PREDICTION, CHECKED")
    print("=" * 78)
    print("\n   (1) fights/day, and (3)+(4) MFE-in-R and where the partial "
          "belongs")
    print(f"   {'sess':7s} {'tf':>3s} {'/day':>6s} {'MFE p50':>8s} {'p75':>7s} "
          f"{'p90':>7s} {'P(>=3R)':>8s} | EV at partial T=2/3/4/5   best")
    for s in SESS:
        for tf in TFS:
            g = B[(B.session == s) & (B.tf == tf)]
            if len(g) < 30:
                continue
            evs = []
            for T in (2, 3, 4, 5):
                hit = g.mfe_r >= T
                legT = (T * g.risk - 0.25) / g.risk
                v = np.where(hit, 0.75 * legT + 0.25 * g.out_trail,
                             g.out_trail) - 0.5 / g.risk
                evs.append(float(np.mean(v)))
            best = (2, 3, 4, 5)[int(np.argmax(evs))]
            print(f"   {s:7s} {tf:3d} {len(g)/nd:6.2f} "
                  f"{g.mfe_r.median():8.2f} {g.mfe_r.quantile(.75):7.2f} "
                  f"{g.mfe_r.quantile(.9):7.2f} {(g.mfe_r>=3).mean()*100:7.1f}% "
                  f"| " + " ".join(f"{e:+7.3f}" for e in evs) + f"   T={best}")
    print("   (15m per-session reference: LONDON p50 1.11 / p75 3.50, best "
          "T=5; NY_AM best T=3)")

    # ------------------------------------------------------------ 6 ------
    print("\n" + "=" * 78)
    print("6. D4 — CLUSTERING VALLEY RE-DERIVED PER (TF x SESSION), 12 cells")
    print("   a found valley overrides X=0.5W ONLY if present in BOTH eras")
    print("=" * 78)
    Fj = F.merge(P.rename(columns={"t_b": "t"}),
                 on=["sess_day", "tf", "locus", "side", "t"], how="inner")

    def valley(g):
        h, edges = np.histogram(g[g < 3.0], bins=30, range=(0, 3))
        it = h[1:-1]
        for i in range(1, len(it) - 1):
            if (it[i] < it[i - 1] and it[i] < it[i + 1]
                    and it[i] < 0.8 * max(it[:i + 1])):
                return (edges[i + 1] + edges[i + 2]) / 2
        return None

    for tf in TFS:
        for s in SESS:
            G = Fj[(Fj.tf == tf) & (Fj.session == s)].dropna(subset=["exc_w"])
            g = G.exc_w
            if len(g) < 100:
                print(f"   TF={tf} {s:7s} n={len(g):5d} — UNDERPOWERED")
                continue
            v = valley(g)
            v2 = valley(G[G.era == "H2-2025"].exc_w)
            v1 = valley(G[G.era == "H1-2026"].exc_w)
            head = (f"   TF={tf} {s:7s} n={len(g):5d} "
                    f"p50={g.median():.2f} p75={g.quantile(.75):.2f} "
                    f"p90={g.quantile(.90):.2f} p99={g.quantile(.99):.2f} -> ")
            if v is None:
                print(head + "no interior valley (monotone) — X=0.50W stands")
                continue
            pct = float((g < v).mean()) * 100
            both = (v2 is not None and v1 is not None
                    and abs(v2 - v1) <= 0.2 and abs(v - v2) <= 0.3)
            # a "valley" out in a decaying tail is a count artefact, not
            # structure: if it sits beyond p95 there is almost no mass there
            tail = pct >= 95.0
            print(head + f"candidate {v:.2f}W (at the {pct:.1f}th pct) | "
                  f"H2={v2 if v2 is None else round(v2,2)} "
                  f"H1={v1 if v1 is None else round(v1,2)} | "
                  + ("REJECTED: beyond p95, this is tail noise in a monotone "
                     "decay" if tail else
                     "both-era: YES — overrides X=0.5W" if both else
                     "both-era: NO — X=0.50W stands"))

    # ------------------------------------------------------------ 7 ------
    print("\n" + "=" * 78)
    print("7. D7 — TARGET-ADMISSIBILITY AS A COLUMN (never a filter this pass)")
    print("=" * 78)
    print(f"   {'tf':>3s} {'next_lvl_R p50':>14s} {'p25':>7s} {'p75':>7s} "
          f"{'no lvl ahead':>12s} {'ceil5':>7s} {'ceil5 fresh':>12s} "
          f"{'ceil60':>7s}")
    for tf in TFS:
        g = B[B.tf == tf]
        if not len(g):
            continue
        nl = g.next_lvl_R
        print(f"   {tf:3d} {nl.median():14.2f} {nl.quantile(.25):7.2f} "
              f"{nl.quantile(.75):7.2f} {nl.isna().mean()*100:11.1f}% "
              f"{g.ceil5_between.mean()*100:6.1f}% "
              f"{g[g.ceil5_between].ceil5_fresh.mean()*100:11.1f}% "
              f"{g.ceil60_between.mean()*100:6.1f}%")
    print("   'no lvl ahead' is a category, not missing data: the trade is "
          "heading into open space.")
    print("\n   EV split by admissibility (descriptive — declared NOT to be "
          "acted on this pass):")
    for tf in TFS:
        g = B[B.tf == tf]
        clear = g[g.next_lvl_R.isna() | (g.next_lvl_R >= 3.0)]
        block = g[g.next_lvl_R < 3.0]
        if len(clear) < 30 or len(block) < 30:
            continue
        print(f"   TF={tf}  room>=3R or open: n={len(clear):5d} "
              f"{clear.out_ship.mean():+.3f} | room<3R: n={len(block):5d} "
              f"{block.out_ship.mean():+.3f}")

    # ------------------------------------------------------------ 8 ------
    print("\n" + "=" * 78)
    print("8. D3 — TF SIGN AGREEMENT (a pooled verdict needs all four TFs "
          "to agree in sign)")
    print("=" * 78)
    for arm in ("reject", "break"):
        print(f"\n### {arm.upper()}")
        for s in SESS:
            row = []
            for tf in TFS:
                g = B[(B.session == s) & (B.arm == arm) & (B.tf == tf)]
                row.append(g.out_ship.mean() if len(g) >= 30 else np.nan)
            agree = (np.all(np.array(row) > 0) or np.all(np.array(row) < 0))
            print(f"   {s:7s} " + " ".join(f"{v:+7.3f}" for v in row)
                  + f"   sign-agreement: {'YES' if agree else 'NO'}")

    # X sensitivity ------------------------------------------------------
    print("\n" + "=" * 78)
    print("X-SENSITIVITY OF THE POOLED (A)-ONLY BOOK (A1 showed the "
          "convention is worth +-0.2R)")
    print("=" * 78)
    print(f"   {'X':>5s} " + " ".join(f"{f'TF={t}':>16s}" for t in TFS))
    for xx in XS:
        Bx = books[xx]
        cells = []
        for tf in TFS:
            g = Bx[Bx.tf == tf]
            cells.append(f"{g.out_ship.mean():+.3f} ({len(g)/nd:.2f}/d)")
        print(f"   {xx:5.2f} " + " ".join(f"{c:>16s}" for c in cells))


if __name__ == "__main__":
    main()
