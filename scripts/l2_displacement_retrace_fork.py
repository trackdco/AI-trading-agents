#!/usr/bin/env python3
"""RETRACE-FORK management rule on the displacement census, FIT ONLY.

The (m,theta) MAE cut ladder is dead (era-inconsistent, sacrifice-dominated —
see the cuts study). This tests the STRUCTURAL version — ANGUS's fork: after a
market-at-close entry, a retrace to the OLD LIMIT LEVEL (entry_ref) is the
regime signal — "that retrace IS the old strategy's fill". Unlike a theta line,
the fork line is the structure the trade was built on, and it is knowable at T.

    RULE (grace m): from minute m after entry onward, if price trades back to
    entry_ref, exit at that bar's CLOSE. Stop stays the candle extreme.
    Priority within a bar: STOP > FORK > TARGET (same conservatism as the cuts).

Arms: 2R-or-stop and EOD-hold, each with fork at grace m in {0,3,5,10}, plus
uncut baselines. Netting 1 tick + $5/RT. Reported per era x scope with fork%,
mean fork R, and sacrifice (forked trades that would have won / survived).
entry_ref merged from the L0 census (the L2 'entry' column is NaN on non-outcome
statuses and is NOT the reference level). Era 2025 = discover, 2026 = confirm.
HOLDOUT NOT TOUCHED.

    python -m scripts.l2_displacement_retrace_fork
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
COST_1T = 0.25 + 0.25


def main() -> None:
    A = build()
    P = A[A.risk >= 2.0].copy()
    P["T"] = pd.to_datetime(P["T"], utc=True)

    L0 = pd.read_parquet(ROOT / "output/l0_triggers_fit.parquet",
                         columns=["ts", "tf", "direction", "entry_ref"])
    L0 = L0.drop_duplicates(["ts", "tf", "direction"])
    P = P.merge(L0, on=["ts", "tf", "direction"], how="left", validate="m:1")
    n_ref = P.entry_ref.notna().sum()
    print(f"entry_ref coverage: {n_ref:,}/{len(P):,}")
    P = P[P.entry_ref.notna()]

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
            risk, ref = r.risk, float(r.entry_ref)
            stop = r.entry - sgn * risk
            fav = (hi - r.entry) / risk if sgn > 0 else (r.entry - lo) / risk
            closeR = sgn * (cl - r.entry) / risk
            stopped = (lo <= stop) if sgn > 0 else (hi >= stop)
            touched = (lo <= ref) if sgn > 0 else (hi >= ref)
            n = len(hi)
            stop_i = int(np.argmax(stopped)) if stopped.any() else n
            tgt_hits = np.flatnonzero(fav[:stop_i] >= 2.0)
            tgt_i = int(tgt_hits[0]) if len(tgt_hits) else n
            eod_r = float(closeR[-1])
            base = {"era": r.era, "sess": r.sess, "day": day, "risk": risk,
                    "ref_dist": abs(r.entry - ref) / risk}
            r2_base = 2.0 if tgt_i < n else (-1.0 if stop_i < n else eod_r)
            rh_base = -1.0 if stop_i < n else eod_r
            rows.append({**base, "m": -1, "arm": "2R", "r": r2_base,
                         "fork": False, "sac": False})
            rows.append({**base, "m": -1, "arm": "hold", "r": rh_base,
                         "fork": False, "sac": False})
            for m in MS:
                j0 = int(np.searchsorted(tmin, m, side="left"))
                hits = np.flatnonzero(touched[j0:])
                fork_i = int(j0 + hits[0]) if len(hits) else n
                fork_r = float(closeR[fork_i]) if fork_i < n else np.nan
                ev = min(stop_i, fork_i, tgt_i)
                if ev == n:
                    r2, kind, sac = eod_r, "eod", False
                elif stop_i == ev:
                    r2, kind, sac = -1.0, "stop", False
                elif fork_i == ev:
                    r2, kind, sac = fork_r, "fork", tgt_i < n
                else:
                    r2, kind, sac = 2.0, "tgt", False
                rows.append({**base, "m": m, "arm": "2R", "r": r2,
                             "fork": kind == "fork", "sac": sac})
                ev = min(stop_i, fork_i)
                if ev == n:
                    rh, kindh = eod_r, "eod"
                elif stop_i == ev:
                    rh, kindh = -1.0, "stop"
                else:
                    rh, kindh = fork_r, "fork"
                sach = kindh == "fork" and stop_i == n
                rows.append({**base, "m": m, "arm": "hold", "r": rh,
                             "fork": kindh == "fork", "sac": sach})
    D = pd.DataFrame(rows)
    D["r_net"] = D.r - COST_1T / D.risk
    out = ROOT / "output/l2_displacement_fork.parquet"
    D.to_parquet(out, index=False)

    md = D[D.m == 0].ref_dist.median()
    print(f"fork-line distance from entry, median: {md:.3f}R of the candle risk")
    for scope, M in (("ALL", D), ("GOLD", D[D.sess == "gold"])):
        for arm in ("2R", "hold"):
            print(f"\n===== [{scope}] {arm} arm — retrace fork =====")
            print(f"  {'era':<5}{'rule':<8}{'meanR':>8}{'net':>8}{'WR':>7}{'fork%':>7}"
                  f"{'forkR':>8}{'sac%':>7}")
            for era in ("2025", "2026"):
                b = M[(M.era == era) & (M.arm == arm) & (M.m == -1)]
                print(f"  {era:<5}{'uncut':<8}{b.r.mean():>+8.3f}{b.r_net.mean():>+8.3f}"
                      f"{(b.r>0).mean()*100:>6.1f}%")
                for m in MS:
                    d = M[(M.era == era) & (M.arm == arm) & (M.m == m)]
                    if len(d) == 0:
                        continue
                    fk = d[d.fork]
                    sac = fk.sac.mean() * 100 if len(fk) else 0.0
                    print(f"  {era:<5}m{m:<7}{d.r.mean():>+8.3f}{d.r_net.mean():>+8.3f}"
                          f"{(d.r>0).mean()*100:>6.1f}%{d.fork.mean()*100:>6.1f}%"
                          f"{fk.r.mean():>+8.3f}{sac:>6.1f}%")
    print(f"\nrow-level -> {out}")
    print("HOLDOUT NOT TOUCHED.")


if __name__ == "__main__":
    main()
