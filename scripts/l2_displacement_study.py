#!/usr/bin/env python3
"""L2-STYLE STUDY of the displacement-entry census, top-down (ANGUS 2026-08-06).

"since we are changing the entire entry mechanism ... work top down from raw
entry triggers. splitting winners from losers. running stop caps."

No gates inherited from the sweep. This characterizes the RAW population under
the new entry (market at the open of the first 1m bar after the close-labeled
signal bar) exactly the way the original canon's L2 characterized the limit
census before any check existed:

  1. census: risk (candle-stop distance) distribution, kinds, sessions, eras
  2. STOP-CAP GRID: stop = entry -/+ min(candle_risk, K) for K in
     {5,7,10,15,20,30,uncapped}; every cap fully re-walked (stop-first, 1m bars,
     to 15:55). R is denominated in the EFFECTIVE risk. Costs netted at 1 tick
     + $5/RT — tighter stops pay proportionally more.
  3. WINNER/LOSER AUTOPSY (uncapped walk): eventual 2R-winners vs stopped-losers
     compared WHILE STILL OPEN at fixed checkpoints after entry — both cohorts
     conditioned identically (the survivorship guard from the canon's own
     autopsy lesson) — plus time-to-resolution.

Conventions per docs/FINDING-displacement-sweep.md §5: CLOSE label; gap-through-
stop (next open at/beyond stop) scored as an immediate -1R loss at every cap,
never dropped; population candle-risk >= 2pt with drops counted; era 2025 =
discover, 2026 = confirm, always split. FIT ONLY. HOLDOUT NOT TOUCHED.

    python -m scripts.l2_displacement_study
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

CAPS: list[float | None] = [5.0, 7.0, 10.0, 15.0, 20.0, 30.0, None]
CHECKPOINTS = [3, 5, 10, 15, 30]        # minutes after entry, while-open autopsy
COST_1T = 0.25 + 0.25                    # 1 tick slip + $5/RT at $20/pt, in points


def walk_cap(hi, lo, cl, entry: float, sgn: int, risk_eff: float):
    """Stop-first walk at effective risk. Returns (r_2r, r_hold, stop_i, tgt_i)."""
    stop = entry - sgn * risk_eff
    fav = (hi - entry) / risk_eff if sgn > 0 else (entry - lo) / risk_eff
    stopped = (lo <= stop) if sgn > 0 else (hi >= stop)
    n = len(hi)
    stop_i = int(np.argmax(stopped)) if stopped.any() else n
    tgt_i = None
    for i in range(stop_i):
        if fav[i] >= 2.0:
            tgt_i = i
            break
    if tgt_i is not None:
        r2 = 2.0
    elif stop_i < n:
        r2 = -1.0
    else:
        r2 = sgn * (cl[-1] - entry) / risk_eff
    rh = -1.0 if stop_i < n else sgn * (cl[-1] - entry) / risk_eff
    return r2, rh, stop_i, tgt_i


def main() -> None:
    A = build()                                   # cached walked frame: T, entry, risk
    P = A[A.risk >= 2.0].copy()
    print(f"census: {len(A):,} walked, {len(A)-len(P):,} sub-2pt dropped -> {len(P):,}")
    for era in ("2025", "2026"):
        d = P[P.era == era]
        q = d.risk.quantile
        print(f"  {era}: n={len(d):,} | candle risk p10/50/90 = "
              f"{q(.1):.1f}/{q(.5):.1f}/{q(.9):.1f}pt | >=30pt: {(d.risk>=30).mean()*100:.1f}% "
              f"| kinds {d.kind.value_counts().to_dict()}")

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.sort_values("mi")
    bars_by_day = {d: g for d, g in bars.groupby(bars.mi.dt.strftime("%Y-%m-%d"))}

    P["T"] = pd.to_datetime(P["T"], utc=True)
    cap_rows, aut_rows = [], []
    for day, g in P.groupby("day", sort=True):
        db = bars_by_day[day]
        mi = db.mi.dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()
        H, L_, C = db.high.to_numpy(), db.low.to_numpy(), db.close.to_numpy()
        end = (pd.Timestamp(f"{day} 15:55", tz=NY).tz_convert("UTC")
               .tz_localize(None).to_datetime64())
        for r in g.itertuples():
            t0 = r.T.tz_localize(None).to_datetime64()
            i0 = np.searchsorted(mi, t0, side="left")
            i1 = np.searchsorted(mi, end, side="right")
            if i1 <= i0:
                continue
            hi, lo, cl = H[i0:i1], L_[i0:i1], C[i0:i1]
            tmin = (mi[i0:i1] - mi[i0]) / np.timedelta64(60, "s")   # minutes from entry
            sgn = 1 if r.direction == "long" else -1
            base = {"era": r.era, "sess": r.sess, "kind": r.kind, "day": day}
            for K in CAPS:
                re_ = r.risk if K is None else min(r.risk, K)
                r2, rh, stop_i, tgt_i = walk_cap(hi, lo, cl, r.entry, sgn, re_)
                cap_rows.append({**base, "cap": "none" if K is None else str(int(K)),
                                 "risk_eff": re_, "capped": K is not None and r.risk > K,
                                 "r_2r": r2, "r_hold": rh,
                                 "r_2r_net": r2 - COST_1T / re_,
                                 "r_hold_net": rh - COST_1T / re_,
                                 "stopped": stop_i < len(hi)})
                if K is None:
                    adv = (r.entry - lo) / re_ if sgn > 0 else (hi - r.entry) / re_
                    res_i = stop_i if tgt_i is None else tgt_i
                    outcome = ("win2r" if tgt_i is not None
                               else ("loss" if stop_i < len(hi) else "unresolved"))
                    a = {**base, "outcome": outcome,
                         "res_min": tmin[res_i] if res_i < len(hi) else np.nan}
                    for ck in CHECKPOINTS:
                        k = int(np.searchsorted(tmin, ck, side="right"))
                        open_at = res_i >= k
                        a[f"open{ck}"] = open_at
                        a[f"mae{ck}"] = float(adv[:k].max()) if (open_at and k > 0) else np.nan
                    aut_rows.append(a)
    CAP = pd.DataFrame(cap_rows)
    AUT = pd.DataFrame(aut_rows)

    print("\n===== STOP-CAP GRID (fully re-walked; R in effective risk; net = 1 tick + comm) =====")
    for scope, M in (("ALL sessions", CAP), ("GOLD only", CAP[CAP.sess == "gold"])):
        print(f"\n[{scope}]")
        print(f"  {'era':<5}{'cap':>5}{'n':>7}{'capped%':>8}{'medRisk':>8}{'stop%':>7}"
              f"{'WR2R':>7}{'m2R':>8}{'m2Rnet':>8}{'mHold':>8}{'mHoldNet':>9}")
        for era in ("2025", "2026"):
            for K in CAPS:
                d = M[(M.era == era) & (M.cap == ("none" if K is None else str(int(K))))]
                if len(d) == 0:
                    continue
                wr = (d.r_2r >= 2.0).mean()
                print(f"  {era:<5}{('none' if K is None else int(K)):>5}{len(d):>7,}"
                      f"{d.capped.mean()*100:>7.1f}%{d.risk_eff.median():>8.2f}"
                      f"{d.stopped.mean()*100:>6.1f}%{wr*100:>6.1f}%"
                      f"{d.r_2r.mean():>+8.3f}{d.r_2r_net.mean():>+8.3f}"
                      f"{d.r_hold.mean():>+8.3f}{d.r_hold_net.mean():>+9.3f}")

    print("\n===== WINNER/LOSER AUTOPSY (uncapped; while-open at each checkpoint, both cohorts) =====")
    for era in ("2025", "2026"):
        d = AUT[AUT.era == era]
        W_, Lo = d[d.outcome == "win2r"], d[d.outcome == "loss"]
        un = (d.outcome == "unresolved").sum()
        print(f"\n  {era}: winners(2R) {len(W_):,} | stopped losers {len(Lo):,} | unresolved {un:,}")
        print(f"    time-to-resolution median: winners {W_.res_min.median():.0f}m | "
              f"losers {Lo.res_min.median():.0f}m")
        print(f"    {'ckpt':>5}{'W open%':>9}{'L open%':>9}{'W MAE med':>11}{'L MAE med':>11}"
              f"{'W MAE p75':>11}{'L MAE p75':>11}")
        for ck in CHECKPOINTS:
            w, l = W_[W_[f"open{ck}"]], Lo[Lo[f"open{ck}"]]
            if len(w) < 30 or len(l) < 30:
                continue
            print(f"    {ck:>4}m{W_[f'open{ck}'].mean()*100:>8.1f}%{Lo[f'open{ck}'].mean()*100:>8.1f}%"
                  f"{w[f'mae{ck}'].median():>11.3f}{l[f'mae{ck}'].median():>11.3f}"
                  f"{w[f'mae{ck}'].quantile(.75):>11.3f}{l[f'mae{ck}'].quantile(.75):>11.3f}")

    out = ROOT / "output/l2_displacement_caps.parquet"
    CAP.to_parquet(out, index=False)
    print(f"\nrow-level cap grid -> {out}")
    print("NOTE: census characterization, not a gate hunt. Era split is reporting "
          "discipline; nothing here is selected on 2026. HOLDOUT NOT TOUCHED.")


if __name__ == "__main__":
    main()
