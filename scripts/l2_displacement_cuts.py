#!/usr/bin/env python3
"""EARLY-CUT LADDER on the displacement census — the autopsy's mandate, FIT ONLY.

docs/L2-displacement-census.md §3: in-trade structure is the one ERA-STABLE thing
in this population (losers resolve in ~3m median; open winners carry ~0.14R less
adverse excursion at every checkpoint, both eras). This measures the obvious rule
family that structure suggests:

    CUT RULE (m, theta): from minute m after entry onward, if the running adverse
    excursion has reached theta*R, exit at that bar's CLOSE. Stop stays the
    candle extreme (validated by the cap grid — caps rejected). Within a bar the
    priority is STOP > CUT > TARGET (conservative: an intrabar stop-out cannot be
    preempted by a close-executed cut; a same-bar cut forgoes a same-bar target).

Grid: m in {0,3,5,10} x theta in {0.5,0.6,0.7,0.8}, against both base arms
(2R-or-stop, EOD-hold), plus the uncut baselines. Netting: 1 tick + $5/RT as
everywhere. Reported per era x scope (ALL, gold): meanR gross/net, WR, % cut,
mean R of cut exits, and the SACRIFICE RATE — of the trades the rule cut, how
many would have gone on to hit 2R uncut. Era 2025 = discover, 2026 = confirm.
HOLDOUT NOT TOUCHED.

    python -m scripts.l2_displacement_cuts
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

MS = [0, 3, 5, 10]
THETAS = [0.5, 0.6, 0.7, 0.8]
COST_1T = 0.25 + 0.25


def main() -> None:
    A = build()
    P = A[A.risk >= 2.0].copy()
    P["T"] = pd.to_datetime(P["T"], utc=True)

    bars = load_bars()
    bars["mi"] = pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY)
    bars = bars.sort_values("mi")
    bars_by_day = {d: g for d, g in bars.groupby(bars.mi.dt.strftime("%Y-%m-%d"))}

    rows = []
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
            tmin = (mi[i0:i1] - mi[i0]) / np.timedelta64(60, "s")
            sgn = 1 if r.direction == "long" else -1
            risk = r.risk
            stop = r.entry - sgn * risk
            fav = (hi - r.entry) / risk if sgn > 0 else (r.entry - lo) / risk
            adv = (r.entry - lo) / risk if sgn > 0 else (hi - r.entry) / risk
            radv = np.maximum.accumulate(adv)
            closeR = sgn * (cl - r.entry) / risk
            stopped = (lo <= stop) if sgn > 0 else (hi >= stop)
            n = len(hi)
            stop_i = int(np.argmax(stopped)) if stopped.any() else n
            tgt_hits = np.flatnonzero(fav[:stop_i] >= 2.0)
            tgt_i = int(tgt_hits[0]) if len(tgt_hits) else n
            eod_r = float(closeR[-1])
            base = {"era": r.era, "sess": r.sess, "day": day, "risk": risk}
            # uncut baselines
            r2_base = 2.0 if tgt_i < n else (-1.0 if stop_i < n else eod_r)
            rh_base = -1.0 if stop_i < n else eod_r
            rows.append({**base, "m": -1, "theta": np.nan, "arm": "2R",
                         "r": r2_base, "cut": False, "sac": False})
            rows.append({**base, "m": -1, "theta": np.nan, "arm": "hold",
                         "r": rh_base, "cut": False, "sac": False})
            for m in MS:
                j0 = int(np.searchsorted(tmin, m, side="left"))
                for th in THETAS:
                    hits = np.flatnonzero(radv[j0:] >= th)
                    cut_i = int(j0 + hits[0]) if len(hits) else n
                    cut_r = float(closeR[cut_i]) if cut_i < n else np.nan
                    # 2R arm: priority stop > cut > target at the same index
                    ev = min(stop_i, cut_i, tgt_i)
                    if ev == n:
                        r2 = eod_r
                        kind2, sac = "eod", False
                    elif stop_i == ev:
                        r2, kind2, sac = -1.0, "stop", False
                    elif cut_i == ev:
                        r2, kind2 = cut_r, "cut"
                        sac = tgt_i < n            # would have hit 2R uncut
                    else:
                        r2, kind2, sac = 2.0, "tgt", False
                    rows.append({**base, "m": m, "theta": th, "arm": "2R",
                                 "r": r2, "cut": kind2 == "cut", "sac": sac})
                    # hold arm: stop > cut, else EOD
                    ev = min(stop_i, cut_i)
                    if ev == n:
                        rh, kindh = eod_r, "eod"
                    elif stop_i == ev:
                        rh, kindh = -1.0, "stop"
                    else:
                        rh, kindh = cut_r, "cut"
                    sach = kindh == "cut" and stop_i == n   # cut a never-stopped hold
                    rows.append({**base, "m": m, "theta": th, "arm": "hold",
                                 "r": rh, "cut": kindh == "cut", "sac": sach})
    D = pd.DataFrame(rows)
    D["r_net"] = D.r - COST_1T / D.risk
    out = ROOT / "output/l2_displacement_cuts.parquet"
    D.to_parquet(out, index=False)

    for scope, M in (("ALL", D), ("GOLD", D[D.sess == "gold"])):
        for arm in ("2R", "hold"):
            print(f"\n===== [{scope}] {arm} arm — cut ladder "
                  f"(sacrifice = cut trades that would have {'hit 2R' if arm=='2R' else 'survived to EOD'}) =====")
            print(f"  {'era':<5}{'rule':<10}{'meanR':>8}{'net':>8}{'WR':>7}{'cut%':>7}"
                  f"{'cutR':>8}{'sac%':>7}")
            for era in ("2025", "2026"):
                b = M[(M.era == era) & (M.arm == arm) & (M.m == -1)]
                print(f"  {era:<5}{'uncut':<10}{b.r.mean():>+8.3f}{b.r_net.mean():>+8.3f}"
                      f"{(b.r>0).mean()*100:>6.1f}%")
                for m in MS:
                    for th in THETAS:
                        d = M[(M.era == era) & (M.arm == arm) & (M.m == m)
                              & (M.theta == th)]
                        if len(d) == 0:
                            continue
                        cut = d[d.cut]
                        sac = cut.sac.mean() * 100 if len(cut) else 0.0
                        print(f"  {era:<5}m{m:<2}θ{th:<5}{d.r.mean():>+8.3f}"
                              f"{d.r_net.mean():>+8.3f}{(d.r>0).mean()*100:>6.1f}%"
                              f"{d.cut.mean()*100:>6.1f}%{cut.r.mean():>+8.3f}{sac:>6.1f}%")
    print(f"\nrow-level -> {out}")
    print("NOTE: rule family suggested by an era-stable structure, but every "
          "(m,theta) cell above is a tested hypothesis — the survivor must hold "
          "in BOTH eras and will face multiplicity honestly. HOLDOUT NOT TOUCHED.")


if __name__ == "__main__":
    main()
