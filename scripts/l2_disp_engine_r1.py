#!/usr/bin/env python3
"""ROUND 1 of the displacement exit engine — the declared arms, nothing else.

Prereg: docs/PREREG-displacement-canon.md §2. Families A-E (23 cells).
Family F (struct_event exits) is DEFERRED: no struct_ts exists for displacement
entries without an L1-events rebuild — recorded here, not silently dropped.

Back-ends, declared: A (time-stop), C (BE), D (trail), E (flow) run on the HOLD
back-end (candle stop / EOD 15:55) and are judged against the EOD-hold baseline.
B (partials) runs both back-ends (hold and 2R) and each is judged against its
own baseline. Partials assume the +1R leg fills at the touch minus 1 tick.
Cost simplification, declared: one 1-tick+$5/RT term on the whole trade
(r_net = r - 0.5pt/risk); the partial's extra leg cost is inside the leg slip.

SURVIVAL (prereg): a cell survives only if its net-1t meanR beats its baseline
in BOTH eras on BOTH the per-trade and episode-mean views. Expected false
survivors at 23 cells: ~1-2. Fewer or equal survivors than that reports
NOTHING SURVIVES. FIT ONLY. HOLDOUT NOT TOUCHED.

    python -m scripts.l2_disp_engine_r1
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_displacement_entry import NY          # noqa: E402
from scripts.build_l2_outcomes import load_bars          # noqa: E402
from scripts.honest_disp_depth import build              # noqa: E402

COST = 0.25 + 0.25          # points: 1 tick slip + $5/RT at $20/pt
TICK = 0.25

A_CELLS = [(m, x) for m in (3, 5, 7, 10) for x in (0.0, 0.25, 0.5)]
B_CELLS = [(p, back) for p in (0.25, 0.50, 0.75) for back in ("hold", "2r")]
D_CELLS = [0.5, 1.0]
E_CELLS = [0.8, 0.9]


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default=None,
                    help="restrict population, e.g. displacement (PROGRAM 2: A/B only)")
    args = ap.parse_args()
    A = build()
    L2 = pd.read_parquet(ROOT / "output/l2_outcomes_fit.parquet",
                         columns=["ts", "tf", "direction", "pattern"])
    A = A.merge(L2.drop_duplicates(["ts", "tf", "direction"]),
                on=["ts", "tf", "direction"], how="left", validate="m:1")
    if args.kind:
        A = A[A.kind == args.kind]
        print(f"PROGRAM 2 population: kind={args.kind}, patterns "
              f"{A.pattern.value_counts().to_dict()}")
    P = A[A.risk >= 2.0].copy()
    P["T"] = pd.to_datetime(P["T"], utc=True)
    P = P.sort_values(["day", "direction", "T"], kind="mergesort").reset_index(drop=True)
    new = (P.day.ne(P.day.shift()) | P.direction.ne(P.direction.shift())
           | (P["T"] - P["T"].shift()).gt(pd.Timedelta(minutes=15)))
    P["episode"] = new.cumsum()

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.sort_values("mi")
    bars_by_day = {d: g for d, g in bars.groupby(bars.mi.dt.strftime("%Y-%m-%d"))}
    fp = pd.read_parquet(ROOT / "output/fp_minutes.parquet")

    recs = []
    for day, g in P.groupby("day", sort=True):
        db = bars_by_day[day]
        mi = db.mi.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()
        H, L_, C = db.high.to_numpy(), db.low.to_numpy(), db.close.to_numpy()
        end = (pd.Timestamp(f"{day} 15:55", tz=NY).tz_convert("UTC")
               .tz_localize(None).to_datetime64())
        try:
            fpd = fp.loc[day]
        except KeyError:
            fpd = None
        for r in g.itertuples():
            t0 = r.T.tz_localize(None).to_datetime64()
            i0 = np.searchsorted(mi, t0, side="left")
            i1 = np.searchsorted(mi, end, side="right")
            if i1 <= i0:
                continue
            hi, lo, cl = H[i0:i1], L_[i0:i1], C[i0:i1]
            tmin = (mi[i0:i1] - mi[i0]) / np.timedelta64(60, "s")
            sgn = 1 if r.direction == "long" else -1
            risk = r.risk
            stop = r.entry - sgn * risk
            fav = (hi - r.entry) / risk if sgn > 0 else (r.entry - lo) / risk
            closeR = sgn * (cl - r.entry) / risk
            stopped = (lo <= stop) if sgn > 0 else (hi >= stop)
            n = len(hi)
            stop_i = int(np.argmax(stopped)) if stopped.any() else n
            runfav = np.maximum.accumulate(fav)
            one_hits = np.flatnonzero(fav[:stop_i] >= 1.0)
            one_i = int(one_hits[0]) if len(one_hits) else n
            tgt_hits = np.flatnonzero(fav[:stop_i] >= 2.0)
            tgt_i = int(tgt_hits[0]) if len(tgt_hits) else n
            eod = float(closeR[-1])
            r_hold = -1.0 if stop_i < n else eod
            r_2r = 2.0 if tgt_i < n else r_hold
            base = {"era": r.era, "day": day, "risk": risk, "episode": r.episode,
                    "pattern": getattr(r, "pattern", None), "sess": r.sess}
            out = {"BASE_hold": r_hold, "BASE_2r": r_2r}
            # A: time-stop (hold back-end). Convention, declared: x>0 exits at
            # minute m when +xR was never touched by then; x=0.0 exits at minute
            # m when the position is not positive mark-to-market at that bar.
            for m, x in A_CELLS:
                k = int(np.searchsorted(tmin, m, side="left"))
                if k >= n:
                    out[f"A_m{m}_x{x}"] = r_hold
                elif stop_i <= k:
                    out[f"A_m{m}_x{x}"] = -1.0
                elif (runfav[k] < x) if x > 0.0 else (closeR[k] <= 0.0):
                    out[f"A_m{m}_x{x}"] = float(closeR[k])
                else:
                    out[f"A_m{m}_x{x}"] = r_hold
            # B: partial at +1R
            leg1 = (risk - TICK) / risk        # +1R touch, 1 tick slip on the leg
            for p, back in B_CELLS:
                full = r_hold if back == "hold" else r_2r
                if one_i >= n:
                    out[f"B_p{int(p*100)}_{back}"] = full
                else:
                    if back == "hold":
                        rb = -1.0 if stop_i < n else eod
                    else:
                        rb = 2.0 if tgt_i < n else (-1.0 if stop_i < n else eod)
                    out[f"B_p{int(p*100)}_{back}"] = p * leg1 + (1 - p) * rb
            # C: BE after +1R (hold back-end)
            if one_i >= n:
                out["C_be"] = r_hold
            else:
                seg_lo, seg_hi = lo[one_i + 1:], hi[one_i + 1:]
                behit = (seg_lo <= r.entry) if sgn > 0 else (seg_hi >= r.entry)
                out["C_be"] = 0.0 if behit.any() else eod
            # D: trail after +1R by d (hold back-end)
            for d in D_CELLS:
                if one_i >= n:
                    out[f"D_d{d}"] = r_hold
                else:
                    rr = None
                    peak = 1.0
                    worst = (lo - r.entry) / risk if sgn > 0 else (r.entry - hi) / risk
                    for k in range(one_i, n):
                        trail = peak - d
                        if worst[k] <= trail:
                            rr = max(trail, -1.0)
                            break
                        peak = max(peak, float(closeR[k]))
                    out[f"D_d{d}"] = rr if rr is not None else eod
            # E: post-entry opposing flow beyond pre-entry quantile (hold back-end)
            for q in E_CELLS:
                key = f"E_q{q}"
                if fpd is None:
                    out[key] = np.nan
                    continue
                ent_min = pd.Timestamp(mi[i0]).tz_localize("UTC").tz_convert(NY)
                pre = fpd.delta.loc[ent_min - pd.Timedelta(minutes=120):
                                    ent_min - pd.Timedelta(minutes=1)]
                if len(pre) < 30:
                    out[key] = np.nan
                    continue
                thr = float(pre.rolling(10).sum().abs().quantile(q))
                post = fpd.delta.loc[ent_min + pd.Timedelta(minutes=1):
                                     ent_min + pd.Timedelta(minutes=int(tmin[-1]))]
                if post.empty:
                    out[key] = r_hold
                    continue
                opp = -sgn * post.cumsum()
                bad = opp[opp > thr]
                if bad.empty:
                    out[key] = r_hold
                else:
                    k = int(np.searchsorted(tmin, (bad.index[0] - ent_min)
                                            / pd.Timedelta(minutes=1), side="left"))
                    out[key] = -1.0 if stop_i <= min(k, n - 1) else (
                        float(closeR[min(k, n - 1)]))
            recs.append({**base, **out})
    D_ = pd.DataFrame(recs)
    cells = [c for c in D_.columns if c[0] in "ABCDE" and "_" in c]
    for c in cells + ["BASE_hold", "BASE_2r"]:
        D_[c + "_net"] = D_[c] - COST / D_.risk
    tag = f"_{args.kind}" if args.kind else ""
    D_.to_parquet(ROOT / f"output/l2_disp_engine_r1{tag}.parquet", index=False)
    if args.kind:
        for pat in sorted(D_.pattern.dropna().unique()):
            for era in ("2025", "2026"):
                d = D_[(D_.pattern == pat) & (D_.era == era)]
                if len(d) == 0:
                    continue
                print(f"  pattern {pat} {era}: n={len(d):>5,} | hold net "
                      f"{d.BASE_hold_net.mean():+.3f} | 2R net {d.BASE_2r_net.mean():+.3f}")

    print(f"round 1: {len(D_):,} trades, {len(cells)} declared cells (F deferred)\n")
    print(f"{'cell':<16}{'base':<6}{'era':<6}{'n':>6}{'net':>8}{'baseNet':>9}"
          f"{'d(trade)':>9}{'d(ep)':>8}  beats")
    survivors = []
    for c in cells:
        bcol = "BASE_2r_net" if c.endswith("_2r") else "BASE_hold_net"
        ok_all = True
        lines = []
        for era in ("2025", "2026"):
            d = D_[(D_.era == era) & D_[c].notna()]
            dt = d[c + "_net"].mean() - d[bcol].mean()
            ep = (d.groupby("episode")[c + "_net"].mean().mean()
                  - d.groupby("episode")[bcol].mean().mean())
            ok = dt > 0 and ep > 0
            ok_all &= ok
            lines.append(f"{c:<16}{bcol[5:9]:<6}{era:<6}{len(d):>6,}"
                         f"{d[c+'_net'].mean():>+8.3f}{d[bcol].mean():>+9.3f}"
                         f"{dt:>+9.3f}{ep:>+8.3f}  {'Y' if ok else 'n'}")
        for ln in lines:
            print(ln)
        if ok_all:
            survivors.append(c)
    print(f"\nSURVIVORS (beat baseline net-1t, both eras, both views): "
          f"{len(survivors)}/{len(cells)} -> {survivors or 'NONE'}")
    print("Noise expectation ~1-2 of 23. At or below it, round 1 reports "
          "NOTHING SURVIVES (prereg kill line). HOLDOUT NOT TOUCHED.")


if __name__ == "__main__":
    main()
