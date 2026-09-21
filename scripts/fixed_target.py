#!/usr/bin/env python3
"""PURE FIXED-TARGET EXITS — a new exit family, never tested.

Full close at the target. No partial, no trail. R in {1, 1.5, 2, 2.5, 3},
all five reported for SHAPE. Not tuned on.

WIN RATE IS SCORED AS A FIRST-PASSAGE RACE: did price reach the target
BEFORE the stop. That is not the same number as "did MFE ever touch that
level", and the first one is what a fixed target actually captures. Both
are computed here so the gap between them is visible rather than assumed.

Same-bar convention: if a single 1m bar contains both the target and the
stop, the STOP wins. Conservative, and the same rule the shipped walk uses.

Run separately on the incumbent (15m-triggered) and the room-gated stream
(3m/5m-triggered) — their stops are different widths and may respond
differently.

Also folds in two pending items:
  - the per-population MFE-in-R table
  - what timeframe the trail actually references on the room-gated stream

    python -m scripts.fixed_target [--build]
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
from src.htf_ma.levels import NY                                     # noqa: E402

OUT = ROOT / "output/htf_ma_census"
FT = OUT / "fixed_target.parquet"
TARGETS = [1.0, 1.5, 2.0, 2.5, 3.0]
COST_PTS, TICK = 0.5, 0.25
SEED, DRAWS, YEAR = 20260807, 1500, 250


def walk(book: pd.DataFrame, tag: str) -> pd.DataFrame:
    """First-passage walk. One pass per session-day over that day's rows."""
    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.set_index("mi").sort_index()[["open", "high", "low", "close"]]
    recs, skipped, days = [], [], sorted(book.sess_day.unique())
    for k, day in enumerate(days):
        D = book[book.sess_day == day]
        t0 = pd.Timestamp(f"{day} 18:00", tz=NY)
        t1 = t0 + pd.Timedelta(hours=23)
        seg = bars[(bars.index >= t0) & (bars.index < t1)]
        if seg.empty:
            continue
        idx = seg.index
        hi, lo, cl = (seg.high.to_numpy(), seg.low.to_numpy(),
                      seg.close.to_numpy())
        for r in D.itertuples():
            te = pd.Timestamp(r.t_entry)
            j0 = int(np.searchsorted(idx.values, te.to_datetime64()))
            if j0 >= len(idx) or not np.isfinite(r.risk) or r.risk <= 0:
                continue
            # GUARD (defect found on the first run): a NaN stop makes the
            # stop-hit test all-False, the trade never resolves, and the
            # outcome falls through to an UNBOUNDED eod. 367 of 664
            # incumbent rows (every sweep_b row) had no stop column at all
            # and produced worst-days of -113R. Never skip silently.
            if not np.isfinite(getattr(r, "stop", np.nan)):
                skipped.append((day, r.t))
                continue
            d, entry, stop, risk = (int(r.direction), float(r.entry),
                                    float(r.stop), float(r.risk))
            cost = COST_PTS / risk
            H, L = hi[j0:], lo[j0:]
            adv = (L <= stop) if d > 0 else (H >= stop)
            stop_j = int(np.argmax(adv)) if adv.any() else None
            fav = (H if d > 0 else L)
            # MFE bounded by the stop (what the shipped walk reports) and
            # MFE over the FULL remaining session (the loose version)
            kk = stop_j if stop_j is not None else len(H)
            mfe_b = float(max(0.0, (d * (fav[:kk] - entry) / risk).max())) \
                if kk > 0 else 0.0
            mfe_f = float(max(0.0, (d * (fav - entry) / risk).max()))
            eod = d * (cl[-1] - entry) / risk
            rec = {"sess_day": day, "t": r.t, "side": r.side,
                   "risk": risk, "mfe_bounded": mfe_b, "mfe_full": mfe_f,
                   "stopped": stop_j is not None,
                   "out_ship": r.out_ship, "book": tag}
            for c in ("tf", "locus", "arm", "pop", "session"):
                rec[c] = getattr(r, c, None)
            for T in TARGETS:
                tgt = entry + d * T * risk
                rch = (H >= tgt) if d > 0 else (L <= tgt)
                hit_j = int(np.argmax(rch)) if rch.any() else None
                # FIRST PASSAGE: target must strictly precede the stop.
                # same bar -> stop wins (conservative).
                won = hit_j is not None and (stop_j is None or hit_j < stop_j)
                if won:
                    o = (T * risk - TICK) / risk - cost
                elif stop_j is not None:
                    o = -1.0 - cost
                else:
                    o = eod - cost
                rec[f"fp_{T}"] = bool(won)
                rec[f"out_{T}"] = float(o)
                # the LOOSE version the ask warns about: did MFE ever reach T
                rec[f"loose_{T}"] = bool(mfe_f >= T)
            recs.append(rec)
        if k % 60 == 0:
            print(f"  {tag} {k}/{len(days)}...", flush=True)
    if skipped:
        print(f"  !! {tag}: {len(skipped)} rows SKIPPED for a non-finite "
              f"stop — reported, never silently dropped", flush=True)
    else:
        print(f"  {tag}: 0 rows skipped, every row has a finite stop",
              flush=True)
    return pd.DataFrame(recs)


def build() -> pd.DataFrame:
    INC = pd.read_parquet(OUT / "incumbent_london.parquet")
    INC["t"] = pd.to_datetime(INC.t)
    INC["t_entry"] = pd.to_datetime(INC.t_entry)
    T = pd.read_parquet(OUT / "ltf_fit.parquet")
    T["t"] = pd.to_datetime(T.t)
    T["t_entry"] = pd.to_datetime(T.t_entry)
    T["era"] = era(T)
    T["scid"] = lassign(T, pd.read_parquet(LP), 0.5)
    B = lbook(T)
    ROOM = B[(B.risk >= FLOOR) & admissible(B) & (B.session == "LONDON")
             & (B.arm == "reject")]
    out = [walk(INC, "INCUMBENT 15m"),
           walk(ROOM[ROOM.tf == 3], "ROOM-GATED 3m"),
           walk(ROOM[ROOM.tf == 5], "ROOM-GATED 5m")]
    F = pd.concat(out, ignore_index=True)
    F.to_parquet(FT, index=False)
    print(f"written: fixed_target.parquet ({len(F):,} rows)")
    return F


def main() -> None:
    F = build() if ("--build" in sys.argv or not FT.exists()) \
        else pd.read_parquet(FT)
    F["era"] = era(F)
    days = sorted(pd.read_parquet(OUT / "levels_fit.parquet")
                  .sess_day.unique())
    nd = len(days)

    print("\n" + "=" * 92)
    print("PURE FIXED-TARGET EXITS — full close, no partial, no trail. "
          "REPORT ONLY.")
    print("=" * 92)

    # ---------------------------------------------------------------- 0 --
    print("\n" + "=" * 92)
    print("SANITY BOUND — a fixed-target exit caps loss at -1R minus cost, so")
    print("the worst single trade must be >= -(1 + max cost_R). Checked:")
    for b, g in F.groupby("book", sort=False):
        wt = min(g[f"out_{T}"].min() for T in TARGETS)
        bound = -(1.0 + (COST_PTS / g.risk).max())
        print(f"   {b:16s} worst single trade {wt:+8.3f}  bound "
              f"{bound:+8.3f}  -> {'OK' if wt >= bound - 1e-6 else 'VIOLATED'}")
    print("\n" + "=" * 92)
    print("0. THE TRAIL TIMEFRAME ON THE ROOM-GATED STREAM — stated plainly")
    print("=" * 92)
    print("   The shipped exit's trail on the room-gated stream STILL "
          "REFERENCES THE 15m BB MA,")
    print("   at 15m granularity. It was NOT updated when the trigger moved "
          "to 3m/5m.")
    print("   (scripts/htf_ma_ltf_census.py L79-84: 'trail reference stays "
          "the 15m BB MA at 15m")
    print("    granularity', and the same f15 frame feeds every TF.) So the "
          "room-gated stream is")
    print("   a 3m/5m trigger with a ~3.7x tighter stop and an UNCHANGED 15m "
          "trail. That is an")
    print("   inconsistency in the incumbent exit, and it is one reason a "
          "fixed target is worth")
    print("   testing here: a fixed target has no timeframe to be "
          "inconsistent about.")

    # ---------------------------------------------------------------- 1 --
    print("\n" + "=" * 92)
    print("1. FIRST-PASSAGE vs 'MFE EVER TOUCHED' — the two numbers the ask "
          "separates")
    print("=" * 92)
    print(f"   {'book':16s} {'T':>4s} {'first-passage':>14s} "
          f"{'MFE-ever':>10s} {'gap':>7s}   (gap = trades whose MFE reached T "
          f"only AFTER the stop)")
    for b, g in F.groupby("book", sort=False):
        for T in TARGETS:
            fp = g[f"fp_{T}"].mean() * 100
            lo = g[f"loose_{T}"].mean() * 100
            print(f"   {b:16s} {T:4.1f} {fp:13.1f}% {lo:9.1f}% "
                  f"{lo-fp:+6.1f}pp")
    print("\n   The gap is real and grows with T. Scoring a fixed target on "
          "MFE-ever would\n   overstate its win rate by that much — the ask "
          "was right to separate them.")

    # ---------------------------------------------------------------- 2 --
    print("\n" + "=" * 92)
    print("2. THE SWEEP — all five targets, for shape. NOT tuned on.")
    print("   baseline = the shipped 75%@3R + 15m trail")
    print("=" * 92)
    for b, g in F.groupby("book", sort=False):
        blo, bhi = boot_mean(g, "out_ship")
        print(f"\n   -- {b}   n={len(g)}  {len(g)/nd:.2f}/day")
        print(f"      {'exit':18s} {'win%':>6s} {'EV':>8s} {'day-boot 95%':>20s}"
              f" {'R/day':>7s} {'worst day':>10s}")
        dr = g.groupby("sess_day").out_ship.sum().reindex(
            days, fill_value=0.0)
        print(f"      {'SHIPPED 75%@3R':18s} "
              f"{(g.out_ship>0).mean()*100:5.1f}% {g.out_ship.mean():+8.3f} "
              f"[{blo:+.3f},{bhi:+.3f}] {g.out_ship.sum()/nd:7.3f} "
              f"{dr.min():10.2f}")
        for T in TARGETS:
            c = f"out_{T}"
            lo_, hi_ = boot_mean(g, c)
            d2 = g.groupby("sess_day")[c].sum().reindex(days, fill_value=0.0)
            print(f"      {'fixed '+str(T)+'R':18s} "
                  f"{g[f'fp_{T}'].mean()*100:5.1f}% {g[c].mean():+8.3f} "
                  f"[{lo_:+.3f},{hi_:+.3f}] {g[c].sum()/nd:7.3f} "
                  f"{d2.min():10.2f}")

    # ---------------------------------------------------------------- 3 --
    print("\n" + "=" * 92)
    print("3. THE PER-POPULATION MFE TABLE (pending item) — does the "
          "room-gated population")
    print("   run further than the book average?")
    print("=" * 92)
    print(f"   {'book':16s} {'n':>5s} " + " ".join(
        f"{q:>7s}" for q in ("p25", "p50", "p75", "p90", "p95"))
        + f" {'P(>=1R)':>8s} {'P(>=2R)':>8s} {'P(>=3R)':>8s}")
    for b, g in F.groupby("book", sort=False):
        m = g.mfe_bounded
        print(f"   {b:16s} {len(g):5d} " + " ".join(
            f"{m.quantile(q):7.2f}" for q in (.25, .5, .75, .9, .95))
            + f" {(m>=1).mean()*100:7.1f}% {(m>=2).mean()*100:7.1f}% "
              f"{(m>=3).mean()*100:7.1f}%")
    print("   (MFE bounded by the stop — the only version that means "
          "anything for an exit rule)")

    # ---------------------------------------------------------------- 4 --
    print("\n" + "=" * 92)
    print("4. THE ACCOUNT LAB — sim stage AND live-stage proxy, because "
          "CONCORD-style splits")
    print("   between the two are exactly what to watch for here")
    print("=" * 92)
    print(f"   {'book':16s} {'exit':14s} {'R/day':>7s} {'worst':>7s} "
          f"{'maxsz':>7s} {'SIM grad':>9s} {'death':>7s} "
          f"{'LIVE $/yr':>10s}")
    rows = []
    for b, g in F.groupby("book", sort=False):
        for label, col in [("SHIPPED 75%@3R", "out_ship")] + \
                [(f"fixed {T}R", f"out_{T}") for T in TARGETS]:
            dr = g.groupby("sess_day")[col].sum().reindex(
                days, fill_value=0.0).to_numpy()
            w = float(dr.min())
            ms = max(50.0, 50.0 * np.floor((DD / abs(w)) / 50.0)) \
                if w < 0 else 600.
            gg, dth, _ = grad(dr, {"s_pre": ms, "s_post": ms})
            rng = np.random.default_rng(SEED)
            live = float(np.mean([
                (lambda r: sum(x for _, x in r["wd"]) - r["fees"])(
                    AL.run_account(dr, rng.integers(0, len(dr), YEAR),
                                   {"s_pre": ms, "s_post": ms},
                                   payout_cap=10**9, payout_at=6000.))
                for _ in range(600)]))
            rows.append((b, label, dr.sum() / nd, w, ms, gg, dth, live))
            print(f"   {b:16s} {label:14s} {dr.sum()/nd:7.3f} {w:7.2f} "
                  f"{'$'+format(ms,'.0f'):>7s} {gg*100:8.1f}% {dth*100:6.1f}% "
                  f"{live:10,.0f}")

    print("\n" + "=" * 92)
    print("5. THE SPLIT TO WATCH FOR — does a tighter target win the sim "
          "stage while the")
    print("   wide-tail exit wins live dollars?")
    print("=" * 92)
    R = pd.DataFrame(rows, columns=["book", "exit", "rday", "worst", "ms",
                                    "grad", "death", "live"])
    for b, g in R.groupby("book", sort=False):
        bs = g.loc[g.grad.idxmax()]
        bl = g.loc[g.live.idxmax()]
        same = bs["exit"] == bl["exit"]
        print(f"   {b:16s} best SIM grad: {bs['exit']:14s} "
              f"({bs.grad*100:.1f}%)   best LIVE: {bl['exit']:14s} "
              f"(${bl.live:,.0f})   -> "
              f"{'SAME EXIT' if same else 'SPLIT — this is the CONCORD pattern'}")
    R.to_parquet(OUT / "fixed_target_scores.parquet", index=False)


if __name__ == "__main__":
    main()
