#!/usr/bin/env python3
"""STRUCTURAL-TARGET EXITS — target = the next level, as an actual price.

The target is reconstructed to a PRICE, not left abstract:

    target_px = entry + direction * next_lvl_R * risk

which is exactly the next locus ahead as-of the decision bar. Admissibility
floor swept at 1.5R / 2R / 3R, reported for shape.

FOUR VARIANTS, kept separate so it is clear which change does the work.
All four scored on the SAME population at each floor:

  V1  SHIPPED       75% at fixed 3R, remainder trailed on the 15m BB MA
  V2  RE-ANCHORED   75% at fixed 3R, remainder trailed on the TRIGGER'S OWN
                    timeframe BB MA  (isolates the trail-timeframe change)
  V3  STRUCTURAL    structural target, FULL CLOSE, no trail
                    (isolates the target change)
  V4  STRUCTURAL+   75% at the level, remainder trailed on the trigger's own
                    timeframe  (both changes together)

First-passage scoring throughout. Same-bar -> stop wins.

Primary population: room-gated LONDON reject at 3m and 5m. The incumbent
runs alongside as a REFERENCE ONLY — and for it "the trigger's own
timeframe" is 15m, so V2 must reproduce V1 exactly. That is the control.

    python -m scripts.structural_target [--build]
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
from scripts.htf_ltf_report import (PAIRS as LP, assign as lassign,  # noqa: E402
                                    book as lbook, boot_mean, era)
from scripts.htf_room_gate import DD, FLOOR, admissible, grad        # noqa: E402
from src.htf_ma.levels import NY, bb_ma_asof                         # noqa: E402

OUT = ROOT / "output/htf_ma_census"
ST = OUT / "structural_target.parquet"
FLOORS = [1.5, 2.0, 3.0]
COST_PTS, TICK = 0.5, 0.25
SEED, YEAR = 20260807, 250


def trail_frames(hist, t0, t1, idx, tf):
    """Per-TF trail machinery: the stop each completed TF bar would propose
    (NaN if that bar did not close through its own TF BB MA in the trade
    direction), and the 1m position at which it goes live."""
    ma, _ = bb_ma_asof(hist, tf)
    f = hist.resample(f"{tf}min", label="right", closed="left").agg(
        {"open": "first", "high": "max", "low": "min",
         "close": "last"}).dropna()
    f = f[(f.index > t0) & (f.index <= t1)]
    m = ma.reindex(f.index - pd.Timedelta(minutes=1)).to_numpy()
    c, l, h = f.close.to_numpy(), f.low.to_numpy(), f.high.to_numpy()
    up = np.isfinite(m) & (c > m)
    dn = np.isfinite(m) & (c < m)
    return {"pos": np.searchsorted(idx.values, f.index.values),
            "up": np.where(up, l - TICK, np.nan),
            "dn": np.where(dn, h + TICK, np.nan)}


def run_trail(TR, j0, d, entry, stop, risk, hi, lo, cl, N1):
    """The shipped trail rule, with the reference frame passed in.
    Returns (trail_R, j_trail) exactly as the 15m walk computes it."""
    tstop, trail, j_trail = stop, None, None
    cand = TR["up"] if d > 0 else TR["dn"]
    pos = TR["pos"]
    b = int(np.searchsorted(pos, j0, side="right"))
    lo_j = j0
    while lo_j < N1:
        hi_j = min(int(pos[b]) + 1, N1) if b < len(pos) else N1
        if hi_j > lo_j:
            adv = ((lo[lo_j:hi_j] <= tstop) if d > 0
                   else (hi[lo_j:hi_j] >= tstop))
            if adv.any():
                j_trail = lo_j + int(np.argmax(adv))
                trail = d * (tstop - entry) / risk
                break
        if b >= len(pos):
            break
        c = cand[b]
        if np.isfinite(c) and d * (c - tstop) > 0:
            tstop = float(c)
        lo_j, b = max(lo_j, hi_j), b + 1
    if trail is None:
        trail, j_trail = d * (cl[-1] - entry) / risk, N1 - 1
    return trail, j_trail


def walk(book: pd.DataFrame, tag: str, trig_tf: int) -> pd.DataFrame:
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close"]]
    recs, skipped, days = [], 0, sorted(book.sess_day.unique())
    for k, day in enumerate(days):
        D = book[book.sess_day == day]
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        hist = bars[(bars.index >= t0 - pd.Timedelta(hours=30))
                    & (bars.index < t1)]
        seg = hist[(hist.index >= t0) & (hist.index < t1)]
        if hist.empty or seg.empty:
            continue
        idx = seg.index
        hi, lo, cl = (seg.high.to_numpy(), seg.low.to_numpy(),
                      seg.close.to_numpy())
        N1 = len(idx)
        TR15 = trail_frames(hist, t0, t1, idx, 15)
        TRtf = TR15 if trig_tf == 15 else trail_frames(hist, t0, t1, idx,
                                                       trig_tf)
        for r in D.itertuples():
            te = pd.Timestamp(r.t_entry)
            j0 = int(np.searchsorted(idx.values, te.to_datetime64()))
            if j0 >= N1 or not np.isfinite(r.risk) or r.risk <= 0:
                continue
            if not np.isfinite(getattr(r, "stop", np.nan)):
                skipped += 1
                continue
            d, entry, stop, risk = (int(r.direction), float(r.entry),
                                    float(r.stop), float(r.risk))
            cost = COST_PTS / risk
            H, L = hi[j0:], lo[j0:]
            adv = (L <= stop) if d > 0 else (H >= stop)
            stop_j = int(np.argmax(adv)) if adv.any() else None
            eod = d * (cl[-1] - entry) / risk
            fav = H if d > 0 else L

            def first_passage(TR_mult):
                """j index (relative to j0) of first touch of entry+d*T*risk,
                or None; and whether it strictly precedes the stop."""
                tgt = entry + d * TR_mult * risk
                rch = (H >= tgt) if d > 0 else (L <= tgt)
                j = int(np.argmax(rch)) if rch.any() else None
                return j, (j is not None and (stop_j is None or j < stop_j))

            tr15, _ = run_trail(TR15, j0, d, entry, stop, risk, hi, lo, cl, N1)
            trtf, _ = run_trail(TRtf, j0, d, entry, stop, risk, hi, lo, cl, N1)
            _, w3 = first_passage(3.0)
            leg3 = (3.0 * risk - TICK) / risk

            rec = {"sess_day": day, "t": r.t, "side": r.side, "risk": risk,
                   "book": tag, "tf": trig_tf,
                   "locus": getattr(r, "locus", None),
                   "next_lvl_R": float(getattr(r, "next_lvl_R", np.nan)),
                   "stopped": stop_j is not None, "fp3": bool(w3),
                   "out_ship_col": float(r.out_ship)}
            # V1 shipped (15m trail) / V2 re-anchored (trigger-TF trail)
            rec["v1"] = (0.75 * leg3 + 0.25 * tr15 if w3 else tr15) - cost
            rec["v2"] = (0.75 * leg3 + 0.25 * trtf if w3 else trtf) - cost
            # V3 / V4 structural — only defined when a level lies ahead
            nl = rec["next_lvl_R"]
            if np.isfinite(nl) and nl > 0:
                jS, wS = first_passage(nl)
                legS = (nl * risk - TICK) / risk
                rec["fpS"] = bool(wS)
                rec["v3"] = (legS - cost) if wS else (
                    (-1.0 - cost) if stop_j is not None else eod - cost)
                rec["v4"] = ((0.75 * legS + 0.25 * trtf) if wS else trtf) - cost
            else:
                rec["fpS"] = False
                rec["v3"] = rec["v4"] = np.nan
            recs.append(rec)
        if k % 60 == 0:
            print(f"  {tag} {k}/{len(days)}...", flush=True)
    print(f"  {tag}: {skipped} rows skipped for a non-finite stop", flush=True)
    return pd.DataFrame(recs)


def build() -> pd.DataFrame:
    INC = pd.read_parquet(OUT / "incumbent_london.parquet")
    D7F = pd.read_parquet(OUT / "incumbent_london_d7.parquet")
    for D in (INC, D7F):
        D["t"] = pd.to_datetime(D.t)
    INC = INC.merge(D7F[["sess_day", "t", "side", "pop", "next_lvl_R"]],
                    on=["sess_day", "t", "side", "pop"], how="left")
    INC["t_entry"] = pd.to_datetime(INC.t_entry)
    T = pd.read_parquet(OUT / "ltf_fit.parquet")
    T["t"] = pd.to_datetime(T.t)
    T["t_entry"] = pd.to_datetime(T.t_entry)
    T["era"] = era(T)
    T["scid"] = lassign(T, pd.read_parquet(LP), 0.5)
    B = lbook(T)
    R = B[(B.risk >= FLOOR) & admissible(B) & (B.session == "LONDON")
          & (B.arm == "reject")]
    F = pd.concat([walk(R[R.tf == 3], "ROOM-GATED 3m", 3),
                   walk(R[R.tf == 5], "ROOM-GATED 5m", 5),
                   walk(INC, "INCUMBENT 15m (ref)", 15)], ignore_index=True)
    F.to_parquet(ST, index=False)
    print(f"written: structural_target.parquet ({len(F):,} rows)")
    return F


def main() -> None:
    F = build() if ("--build" in sys.argv or not ST.exists()) \
        else pd.read_parquet(ST)
    days = sorted(pd.read_parquet(OUT / "levels_fit.parquet")
                  .sess_day.unique())
    nd = len(days)
    VN = {"v1": "V1 shipped 75%@3R+15m trail",
          "v2": "V2 3R + trail on trigger TF",
          "v3": "V3 structural, full close",
          "v4": "V4 structural 75% + TF trail"}

    print("\n" + "=" * 96)
    print("STRUCTURAL-TARGET EXITS — four variants, first-passage scored. "
          "REPORT ONLY.")
    print("=" * 96)

    print("\n" + "=" * 96)
    print("CONTROLS")
    print("=" * 96)
    I = F[F.book.str.startswith("INCUMBENT")]
    d1 = np.abs(I.v1 - I.v2).max()
    print(f"   C1  For the incumbent the trigger TF IS 15m, so V2 must "
          f"reproduce V1 exactly.")
    print(f"       max |V1-V2| = {d1:.2e}  -> "
          f"{'PASS' if d1 < 1e-9 else 'FAIL'}")
    d2 = np.abs(I.v1 - I.out_ship_col).max()
    print(f"   C2  V1 recomputed here vs the stored out_ship column: "
          f"max diff {d2:.2e}")
    print(f"       -> {'PASS (the walk reproduces the shipped pipeline)' if d2 < 1e-6 else 'differs — see note'}")
    for b, g in F.groupby("book", sort=False):
        wt = min(g[v].min() for v in ("v1", "v2", "v3", "v4"))
        bound = -(1.0 + (COST_PTS / g.risk).max())
        print(f"   C3  {b:22s} worst single trade {wt:+7.3f} bound "
              f"{bound:+7.3f} -> {'OK' if wt >= bound - 1e-6 else 'VIOLATED'}")

    print("\n" + "=" * 96)
    print("POPULATION AT EACH ADMISSIBILITY FLOOR (structural variants need a "
          "level AHEAD)")
    print("=" * 96)
    print(f"   {'book':22s} {'n_all':>6s} {'open space':>11s} " + " ".join(
        f"{'n>='+str(f)+'R':>9s}" for f in FLOORS))
    for b, g in F.groupby("book", sort=False):
        opn = g.next_lvl_R.isna().mean() * 100
        print(f"   {b:22s} {len(g):6d} {opn:10.1f}% " + " ".join(
            f"{int((g.next_lvl_R >= f).sum()):9d}" for f in FLOORS))
    print("   'open space' rows have NO level ahead, so V3/V4 are undefined "
          "for them and they\n   are excluded from the floor populations "
          "rather than given a substitute target.")

    print("\n" + "=" * 96)
    print("THE FOUR VARIANTS, per floor. PRIMARY = room-gated 3m/5m.")
    print("=" * 96)
    rows = []
    for b, g0 in F.groupby("book", sort=False):
        for fl in FLOORS:
            g = g0[g0.next_lvl_R >= fl]
            if len(g) < 40:
                print(f"\n   -- {b} @ floor {fl}R : n={len(g)} UNDERPOWERED")
                continue
            print(f"\n   -- {b}  @ admissibility floor {fl}R   n={len(g)}  "
                  f"{len(g)/nd:.2f}/day  median target "
                  f"{g.next_lvl_R.median():.2f}R")
            print(f"      {'variant':32s} {'win%':>6s} {'EV':>8s} "
                  f"{'day-boot 95%':>20s} {'R/day':>7s} {'worst':>7s}")
            for v, nm in VN.items():
                if g[v].isna().all():
                    continue
                lo_, hi_ = boot_mean(g, v)
                dr = g.groupby("sess_day")[v].sum().reindex(days,
                                                            fill_value=0.0)
                wr = (g.fpS if v in ("v3", "v4") else g.fp3).mean() * 100
                print(f"      {nm:32s} {wr:5.1f}% {g[v].mean():+8.3f} "
                      f"[{lo_:+.3f},{hi_:+.3f}] {g[v].sum()/nd:7.3f} "
                      f"{dr.min():7.2f}")
                rows.append((b, fl, v, nm, g[v].mean(), g[v].sum() / nd,
                             float(dr.min()), len(g)))

    print("\n" + "=" * 96)
    print("WHICH CHANGE DOES THE WORK — deltas against V1, room-gated only")
    print("=" * 96)
    R = pd.DataFrame(rows, columns=["book", "floor", "v", "nm", "ev", "rday",
                                    "worst", "n"])
    for b in [x for x in R.book.unique() if x.startswith("ROOM")]:
        for fl in FLOORS:
            s = R[(R.book == b) & (R.floor == fl)].set_index("v")
            if "v1" not in s.index:
                continue
            base = s.loc["v1"]
            print(f"   {b} @{fl}R  " + "  ".join(
                f"{v}: EV {s.loc[v].ev - base.ev:+.3f} / R day "
                f"{s.loc[v].rday - base.rday:+.3f}"
                for v in ("v2", "v3", "v4") if v in s.index))

    print("\n" + "=" * 96)
    print("ACCOUNT LAB — sim graduation and live proxy, room-gated primary")
    print("=" * 96)
    print(f"   {'book':22s} {'floor':>5s} {'variant':32s} {'R/day':>7s} "
          f"{'worst':>7s} {'maxsz':>7s} {'SIM grad':>9s} {'LIVE $/yr':>10s}")
    for b, g0 in F.groupby("book", sort=False):
        for fl in FLOORS:
            g = g0[g0.next_lvl_R >= fl]
            if len(g) < 40:
                continue
            for v, nm in VN.items():
                if g[v].isna().all():
                    continue
                dr = g.groupby("sess_day")[v].sum().reindex(
                    days, fill_value=0.0).to_numpy()
                w = float(dr.min())
                ms = max(50.0, 50.0 * np.floor((DD / abs(w)) / 50.0)) \
                    if w < 0 else 600.
                gg, _, _ = grad(dr, {"s_pre": ms, "s_post": ms})
                rng = np.random.default_rng(SEED)
                live = float(np.mean([
                    (lambda x: sum(q for _, q in x["wd"]) - x["fees"])(
                        AL.run_account(dr, rng.integers(0, len(dr), YEAR),
                                       {"s_pre": ms, "s_post": ms},
                                       payout_cap=10**9, payout_at=6000.))
                    for _ in range(500)]))
                print(f"   {b:22s} {fl:5.1f} {nm:32s} {dr.sum()/nd:7.3f} "
                      f"{w:7.2f} {'$'+format(ms,'.0f'):>7s} {gg*100:8.1f}% "
                      f"{live:10,.0f}")


if __name__ == "__main__":
    main()
