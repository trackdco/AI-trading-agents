#!/usr/bin/env python3
"""HOLDOUT LOOK #1 — the bar-only venue. ONE LOOK. NO RE-RUNS.

Executes DECLARATIONS-holdout-look-1.md exactly: H1-H5, two blocks, both
must pass, Bonferroni x5, UNDERPOWERED below 100 fights in a block.

R4 compliance, in order:
  R4.2  the ENTRY GATE runs on the SEALED build FIRST. If it fails, nothing
        is read and the look is not spent.
  R4.1  sealed tables come from the committed builders (levels_sealed /
        sweep_sealed, written unread at commit 13e79a2f). Builder SHA logged.
  R4.3  unit = 18:00-anchored session day; windows by NY clock, same minutes
  R4.4  fights structural X=0.5W, NOT re-tuned here
  R4.6  day bootstrap, 2000 draws, seed 20260807, widened to the x5 level

    python -m scripts.holdout_look_1 --confirm-spend
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_l2_outcomes import load_bars                     # noqa: E402
from scripts.htf_ma_level_census import day_rows, level_series      # noqa: E402
from scripts.htf_ma_mtable import flow_features                     # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                        # noqa: E402

OUT = ROOT / "output/htf_ma_census"
SEALED = ROOT / "output/sealed"
SESSIONS = {"LONDON": (180, 299), "NY_PRE": (480, 569), "NY_AM": (570, 630)}
SEED, DRAWS, X = 20260807, 2000, 0.5
NCLAIM = 5                       # Bonferroni x5 -> two-sided 99% interval
ALPHA = 0.05 / NCLAIM
UNDERPOWERED_N = 100
FLOW_VENUE = {"2023-07", "2023-09", "2023-11", "2024-03", "2024-04", "2024-10"}
BLOCK_A = {f"2023-{m:02d}" for m in (1, 2, 3, 4, 5, 6, 8, 10, 12)}
BLOCK_B = ({f"2024-{m:02d}" for m in (1, 2, 5, 6, 7, 8, 9, 11, 12)}
           | {f"2025-{m:02d}" for m in (1, 2, 3, 4, 5)})


def boot_ci(df, col="out_ship", alpha=ALPHA):
    """Day bootstrap widened to the x5-corrected level (R4.6)."""
    g = df.groupby("sess_day")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(), g["count"].to_numpy()
    if len(s) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(s), (DRAWS, len(s)))
    c = n[i].sum(1)
    st = np.divide(s[i].sum(1), c, out=np.full(DRAWS, np.nan), where=c > 0)
    return (float(np.nanpercentile(st, 100 * alpha / 2)),
            float(np.nanpercentile(st, 100 * (1 - alpha / 2))))


def build_pairs(F, bars):
    """Structural-fight excursions on the SEALED span. Same procedure as
    fit (max excursion from the LOCUS between consecutive same-side
    triggers, in W units); X is NOT re-tuned."""
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
        for (locus, side), g in D.groupby(["locus", "side"]):
            lvl = lv[locus]
            g = g.drop_duplicates("t").sort_values("t")
            ts, ws = g.t.to_list(), g.w15.to_list()
            for a in range(len(ts) - 1):
                i0 = int(np.searchsorted(idx.values,
                                         pd.Timestamp(ts[a]).to_datetime64()))
                i1 = int(np.searchsorted(idx.values,
                                         pd.Timestamp(ts[a+1]).to_datetime64()))
                if i1 <= i0 or ws[a] <= 0:
                    continue
                m = np.nanmax(np.maximum(np.abs(hi[i0:i1] - lvl[i0:i1]),
                                         np.abs(lo[i0:i1] - lvl[i0:i1])))
                out.append({"sess_day": day, "locus": locus, "side": side,
                            "t_b": ts[a+1], "exc_w": float(m) / ws[a]})
        if k % 100 == 0:
            print(f"  pairs {k}/{len(days)}...", flush=True)
    return pd.DataFrame(out)


def assign(F, P, x=X):
    key = {(r.sess_day, r.locus, r.side, pd.Timestamp(r.t_b)): r.exc_w
           for r in P.itertuples()}
    ids = {}
    for (day, locus, side), g in F.groupby(["sess_day", "locus", "side"],
                                           sort=False):
        g = g.sort_values("t")
        cid, seen = 0, None
        for r in g.itertuples():
            t = pd.Timestamp(r.t)
            if seen is not None and t != seen:
                e = key.get((day, locus, side, t), np.nan)
                if not np.isfinite(e) or e >= x:
                    cid += 1
            seen = t
            ids[r.Index] = f"{day}:{locus}:{side}:S{cid}"
    return pd.Series(ids, name="scid")


def book(F, arm):
    R = F[(F.arm == arm) & F.out_ship.notna() & (F.risk > 0)]
    if arm == "break":
        R = R[R.retested.astype("boolean").fillna(False)]
    return R.sort_values("t").groupby("scid", as_index=False).first()


# ---------------------------------------------------------- R4.2 GATE ----
def entry_gate(bars, days):
    """The same three probes as the fit gate, on SEALED days. Must PASS
    before a single sealed outcome is read."""
    EPS = 1e-9
    t1n = t1bad = t1moved = t2n = t2f = t3n = t3f = 0
    for day in days:
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        win = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                   & (bars.index < t1)]
        seg = win[(win.index >= t0) & (win.index < t1)]
        if win.empty or seg.empty:
            continue
        idx, op = seg.index, seg.open.to_numpy()
        for locus in ("bbma15", "val", "vwap_m1"):
            rows = day_rows(win, day, [locus])
            rej = [r for r in rows if r["arm"] == "reject"]
            brk = [r for r in rows if r["arm"] == "break" and r["retested"]]
            pick = ([rej[i] for i in sorted({0, len(rej)//2, len(rej)-1})]
                    if rej else []) + \
                   ([brk[i] for i in sorted({0, len(brk)//2, len(brk)-1})]
                    if brk else [])
            for r in pick:
                t = pd.Timestamp(r["t"])
                j0 = int(np.searchsorted(idx.values, t.to_datetime64()))
                prior = win[win.index < t]
                if prior.empty:
                    continue
                pc = float(prior.close.iloc[-1])
                if r["arm"] == "reject":
                    t2n += 1
                    if j0 >= len(idx) or abs(r["entry"] - op[j0]) > EPS:
                        t2f += 1
                t1n += 1
                wf = win.copy()
                m = wf.index >= t
                wf.loc[m, ["open", "high", "low", "close"]] = pc
                wf.loc[m, "volume"] = 1
                mt = [x for x in day_rows(wf, day, [locus])
                      if x["t"] == r["t"] and x["arm"] == r["arm"]
                      and x["side"] == r["side"]
                      and x["n_attempts"] == r["n_attempts"]]
                if mt and np.isfinite(mt[0]["entry"]):
                    ef = mt[0]["entry"]
                    if abs(ef - pc) > EPS:
                        t1bad += 1
                    if abs(ef - r["entry"]) > EPS:
                        t1moved += 1
                if r["arm"] == "break" and np.isfinite(r["entry"]) \
                        and not pd.isna(r.get("t_fill")):
                    jf = int(np.searchsorted(
                        idx.values, pd.Timestamp(r["t_fill"]).to_datetime64()))
                    if jf >= len(idx) or idx[jf] != pd.Timestamp(r["t_fill"]):
                        continue
                    wf2 = win.copy()
                    tsf = idx[jf]
                    c_old = float(wf2.loc[tsf, "close"])
                    c_new = float(wf2.loc[tsf, "open"])
                    if abs(c_new - c_old) < EPS:
                        c_new = (float(wf2.loc[tsf, "high"])
                                 + float(wf2.loc[tsf, "low"])) / 2.0
                    if abs(c_new - c_old) < EPS:
                        continue
                    t3n += 1
                    wf2.loc[tsf, "close"] = c_new
                    mt2 = [x for x in day_rows(wf2, day, [locus])
                           if x["t"] == r["t"] and x["arm"] == "break"
                           and x["side"] == r["side"]
                           and x["n_attempts"] == r["n_attempts"]]
                    if mt2 and np.isfinite(mt2[0]["entry"]) \
                            and abs(mt2[0]["entry"] - r["entry"]) > EPS:
                        t3f += 1
    ok = (t1bad == 0 and t1moved > 0 and t2f == 0 and t3f == 0)
    print(f"   T1 {t1n} probes (bad {t1bad}, moved {t1moved}) | "
          f"T2 {t2f}/{t2n} fail | T3 {t3f}/{t3n} fail  -> "
          f"{'PASS' if ok else 'FAIL'}")
    return ok


def blk(d):
    m = d.sess_day.str[:7]
    return np.where(m.isin(BLOCK_A), "A",
                    np.where(m.isin(BLOCK_B), "B", "EXCLUDED"))


def verdict(g, name, bar_lift=None, base=None):
    """EV>0 AND x5-corrected lower bound >0. <100 fights = UNDERPOWERED."""
    n = len(g)
    if n < UNDERPOWERED_N:
        return f"{name:26s} n={n:5d}  UNDERPOWERED (<{UNDERPOWERED_N})", None
    if bar_lift is None:
        lo, hi = boot_ci(g)
        ev = g.out_ship.mean()
        p = ev > 0 and lo > 0
        return (f"{name:26s} n={n:5d}  EV {ev:+.3f}  x5 CI "
                f"[{lo:+.3f},{hi:+.3f}]  -> {'PASS' if p else 'FAIL'}"), p
    lift = g.out_ship.mean() - base.out_ship.mean()
    days = np.array(sorted(base.sess_day.unique()))
    di = {d: i for i, d in enumerate(days)}
    sA = np.zeros(len(days)); nA = np.zeros(len(days))
    sK = np.zeros(len(days)); nK = np.zeros(len(days))
    for d, q in base.groupby("sess_day"):
        sA[di[d]], nA[di[d]] = q.out_ship.sum(), len(q)
    for d, q in g.groupby("sess_day"):
        sK[di[d]], nK[di[d]] = q.out_ship.sum(), len(q)
    rng = np.random.default_rng(SEED)
    i = rng.integers(0, len(days), (DRAWS, len(days)))
    ca, ck = nA[i].sum(1), nK[i].sum(1)
    st = (np.divide(sK[i].sum(1), ck, out=np.full(DRAWS, np.nan), where=ck > 0)
          - np.divide(sA[i].sum(1), ca, out=np.full(DRAWS, np.nan), where=ca > 0))
    lo = float(np.nanpercentile(st, 100 * ALPHA / 2))
    hi = float(np.nanpercentile(st, 100 * (1 - ALPHA / 2)))
    p = lift >= bar_lift and lo > 0
    return (f"{name:26s} n={n:5d}  lift {lift:+.3f}  x5 CI "
            f"[{lo:+.3f},{hi:+.3f}]  -> {'PASS' if p else 'FAIL'}"), p


def main() -> None:
    if "--confirm-spend" not in sys.argv:
        print("refusing: this SPENDS holdout look #1. "
              "pass --confirm-spend to proceed.")
        sys.exit(2)
    sha = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--",
         "scripts/htf_ma_level_census.py", "scripts/htf_ma_sweep_locus.py"],
        capture_output=True, text=True, cwd=ROOT).stdout.strip()
    print("=" * 96)
    print("HOLDOUT LOOK #1 — BAR-ONLY VENUE. ONE LOOK. NO RE-RUNS.")
    print(f"R4.1 builder SHA: {sha}")
    print("=" * 96)

    L = pd.concat([pd.read_parquet(SEALED / "levels_sealed.parquet"),
                   pd.read_parquet(OUT / "levels_gray.parquet")],
                  ignore_index=True)
    L["t"] = pd.to_datetime(L.t)
    L["blk"] = blk(L)
    L = L[L.blk != "EXCLUDED"]
    S = pd.read_parquet(SEALED / "sweep_sealed.parquet")
    S = S[S.cell == "sweep_b"].copy()
    S["t"] = pd.to_datetime(S.t)
    S["blk"] = blk(S)
    S = S[S.blk != "EXCLUDED"]
    print(f"\nvenue: bar-only months only. flow venue "
          f"({sorted(FLOW_VENUE)}) EXCLUDED — never touched by this look.")
    print(f"Block A months {len(BLOCK_A)} | Block B months {len(BLOCK_B)}")
    print(f"sealed+gray rows in venue: levels {len(L):,} | sweep_b {len(S):,}")

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close",
                                              "volume"]]

    print("\n" + "=" * 96)
    print("R4.2 — ENTRY GATE ON THE SEALED BUILD (runs BEFORE any row is read)")
    print("=" * 96)
    gdays = sorted(L.sess_day.unique())[::40]
    print(f"   probing {len(gdays)} sealed days across both blocks")
    if not entry_gate(bars, gdays):
        print("\n   GATE FAILED — no sealed row read, look NOT spent.")
        sys.exit(1)

    print("\n" + "=" * 96)
    print("BUILDING THE SEALED BOOKS (X=0.5W, not re-tuned)")
    print("=" * 96)
    P = build_pairs(L, bars)
    L = L.join(assign(L, P))
    ub = pd.concat([book(L[L.locus == "val"], "break"),
                    book(L[L.locus == "vwap_m1"], "break")]) \
        .drop_duplicates(["sess_day", "t", "side"])
    rej = book(L[L.locus == "bbma15"], "reject")
    comp = pd.concat([ub.assign(pop="union_break"),
                      rej.assign(pop="reject")], ignore_index=True)
    for D in (comp, S):
        D["hm"] = pd.to_datetime(D.t).dt.hour * 60 + pd.to_datetime(D.t).dt.minute
    books = {}
    for nm, (a, b) in SESSIONS.items():
        c = comp[(comp.hm >= a) & (comp.hm <= b)]
        if nm == "LONDON":
            sw = S[(S.hm >= a) & (S.hm <= b)]
            c = pd.concat([c, sw.assign(pop="sweep_b")], ignore_index=True) \
                .drop_duplicates(["sess_day", "t", "side"])
        books[nm] = c
    print(f"   LONDON {len(books['LONDON'])} | NY_PRE {len(books['NY_PRE'])} "
          f"| NY_AM {len(books['NY_AM'])} fights")

    # H5 needs closeloc, recomputed with the SAME formula (flow_features)
    rejbook = rej.copy()
    rejbook["hm"] = pd.to_datetime(rejbook.t).dt.hour * 60 \
        + pd.to_datetime(rejbook.t).dt.minute
    cl = []
    for day, g in rejbook.groupby("sess_day"):
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                    & (bars.index < t1)]
        if hist.empty:
            continue
        f15 = hist.resample("15min", label="right", closed="left").agg(
            {"open": "first", "high": "max", "low": "min",
             "close": "last"}).dropna()
        for r in g.itertuples():
            ts = pd.Timestamp(r.t)
            if ts not in f15.index:
                continue
            f = flow_features(None, ts - pd.Timedelta(minutes=15), ts,
                              int(r.direction), None, bar_ohlc=f15.loc[ts])
            cl.append({"sess_day": day, "t": r.t, "side": r.side,
                       "closeloc": f["closeloc"]})
    CL = pd.DataFrame(cl)
    rejbook = rejbook.merge(CL, on=["sess_day", "t", "side"], how="left")
    q1 = float(pd.read_parquet(OUT / "bc_frame.parquet")
               .query("pop=='reject'").closeloc.quantile(0.25))
    print(f"   H5 closeloc Q1 taken from FIT ({q1:.4f}) — not re-derived on "
          f"the holdout")

    print("\n" + "=" * 96)
    print(f"THE FIVE CLAIMS — Bonferroni x{NCLAIM}, two-sided "
          f"{(1-ALPHA)*100:.0f}% interval, BOTH blocks must pass")
    print("=" * 96)
    results = {}
    for h, nm, getter in (
            ("H1", "LONDON base rate", lambda b: books["LONDON"][books["LONDON"].blk == b]),
            ("H2", "NY_PRE base rate", lambda b: books["NY_PRE"][books["NY_PRE"].blk == b]),
            ("H3", "NY_AM base rate", lambda b: books["NY_AM"][books["NY_AM"].blk == b]),
            ("H4", "sweep_b LONDON alone", lambda b: (
                lambda s: s[(s.hm >= 180) & (s.hm <= 299) & (s.blk == b)])(S)),
    ):
        print(f"\n{h} — {nm}")
        outs = []
        for b in ("A", "B"):
            line, p = verdict(getter(b), f"  Block {b}")
            print(f"   {line}")
            outs.append(p)
        results[h] = outs
    print(f"\nH5 — closeloc cut (keep closeloc >= fit Q1), bar lift >= +0.04R")
    outs = []
    for b in ("A", "B"):
        base = rejbook[(rejbook.blk == b) & rejbook.closeloc.notna()]
        keep = base[base.closeloc >= q1]
        line, p = verdict(keep, f"  Block {b}", bar_lift=0.04, base=base)
        print(f"   {line}")
        outs.append(p)
    results["H5"] = outs

    print("\n" + "=" * 96)
    print("VERDICT — a claim passes only if BOTH blocks pass")
    print("=" * 96)
    for h, o in results.items():
        if any(x is None for x in o):
            v = "UNDERPOWERED (neither passed nor failed)" if all(
                x is None for x in o) else "UNDERPOWERED in one block"
        elif all(o):
            v = "PASS"
        else:
            v = "FAIL (permanent for this venue)"
        print(f"   {h}: {v}")


if __name__ == "__main__":
    main()
