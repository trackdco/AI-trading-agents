#!/usr/bin/env python3
"""LEAK DAMAGE — IB shelf conviction-tier lookahead (ANGUS 2026-08-06).

nya_ibc_desk_run.build_shelf_trades reads flow features AT THE FILL MINUTE:
`fl = F.loc[(day, clk)]` where clk is the fill minute. fp_minutes.delta is signed
volume summed over the WHOLE minute (indexed at minute start) and flow_features.cvd
is a cumsum INCLUSIVE of that minute. The touch is intra-minute, so the tier sees
order flow that had not happened yet. Same for band0, whose vwap/sd at k0 include
the fill minute's full volume and typical price.

  early       touch at exactly 10:00  CLEAN — it is the clock
  stretched   session cvd < 0         LEAKS
  delta_with  touch-minute delta > 0  LEAKS
  near_target band distance           LEAKS

HONEST = the last COMPLETE minute before the fill:
  edelta -> delta[m-1];  ecvd -> cvd[m] - delta[m];  band0 -> vwap/sd at k0-1.

The entry trigger and the management walk never read the fill minute's aggregate,
so each trade's R outcome is IDENTICAL under both. Only the tier — and therefore
the $300/$200 sizing — moves. That isolates the conviction layer exactly.

    python -m scripts.leak_damage_shelf
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_ibc_desk_run import FIT0, FIT1, FR, NY  # noqa: E402
from scripts.nya_ivb_desk_run import build_trades as build_A  # noqa: E402


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    F = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    F = F.reset_index().set_index(["gday", "clock"]).sort_index()
    days = {d: r.sort_values("ts").reset_index(drop=True) for d, r in R.groupby("gday")}

    out = []
    for t in [x for x in build_A() if FIT0 <= x["day"] <= FIT1]:
        r = days.get(t["day"])
        if r is None:
            continue
        k0 = int((r.ts == t["fill"]).idxmax()) if (r.ts == t["fill"]).any() else None
        if k0 is None or k0 == 0:
            continue
        side, e, legacy = t["side"], t["entry"], t["risk"]
        stop_d = 0.5 * legacy
        H, L_, C = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()
        V = r.volume.clip(lower=0).to_numpy().astype(float)
        tp = (H + L_ + C) / 3
        cv = np.maximum(V.cumsum(), 1)
        vwap = (tp * V).cumsum() / cv
        sd = np.sqrt(np.clip((tp ** 2 * V).cumsum() / cv - vwap ** 2, 0, None))
        clk = r.clock.iloc[k0]

        # --- leaky (shipped) conviction inputs ---
        band0_l = vwap[k0] - side * sd[k0]
        try:
            fl = F.loc[(t["day"], clk)]
            edelta_l, ecvd_l = float(fl.delta) * side, float(fl.cvd) * side
            dmin = float(fl.delta)
        except KeyError:
            edelta_l = ecvd_l = dmin = np.nan
        # --- honest: last COMPLETE minute before the fill ---
        band0_h = vwap[k0 - 1] - side * sd[k0 - 1]
        prev = r.clock.iloc[k0 - 1]
        try:
            fp = F.loc[(t["day"], prev)]
            edelta_h = float(fp.delta) * side
        except KeyError:
            edelta_h = np.nan
        # cvd is an inclusive cumsum, so cvd through m-1 is exactly cvd[m] - delta[m]
        ecvd_h = (ecvd_l - dmin * side) if ecvd_l == ecvd_l else np.nan

        def score_of(ecvd, edelta, band0):
            return (int(clk == "10:00")
                    + (int(ecvd < 0) if ecvd == ecvd else 0)
                    + (int(edelta > 0) if edelta == edelta else 0)
                    + int(side * (e - band0) / stop_d >= -1.7874))
        s_l = score_of(ecvd_l, edelta_l, band0_l)
        s_h = score_of(ecvd_h, edelta_h, band0_h)

        # --- outcome: identical under both (entry + management never read minute k0) ---
        pnl, kind = None, "eod"
        for m in range(1, len(r) - k0):
            j = k0 + m
            hi, lo, cl = H[j], L_[j], C[j]
            adv = (hi - e) if side < 0 else (e - lo)
            if adv >= stop_d:
                pnl, kind = -stop_d, "stop"; break
            band = vwap[j] - side * sd[j]
            if side * (band - e) >= 0.125 * legacy and \
               ((side < 0 and lo <= band) or (side > 0 and hi >= band)):
                pnl, kind = side * (band - e), "band"; break
            r_now = (e - cl) if side < 0 else (cl - e)
            if m == 10 and r_now < 0:
                pnl, kind = r_now, "scratch"; break
        if pnl is None:
            pnl = side * (C[-1] - e)
        mech_R = (pnl - FR) / stop_d
        out.append(dict(day=t["day"], clk=clk, mech_R=mech_R, kind=kind,
                        score_leak=s_l, score_hon=s_h,
                        tier_leak="CONFIRMED" if s_l >= 3 else "BASE",
                        tier_hon="CONFIRMED" if s_h >= 3 else "BASE"))

    T = pd.DataFrame(out)
    print(f"shelf trades: {len(T)}  (fit span {FIT0}..{FIT1})\n")

    for tag, col in (("leaky (shipped)", "tier_leak"), ("honest", "tier_hon")):
        c = T[T[col] == "CONFIRMED"].mech_R
        b = T[T[col] == "BASE"].mech_R
        print(f"{tag}:")
        print(f"   CONFIRMED n={len(c):3d} WR={100*(c>0).mean() if len(c) else 0:.1f}% "
              f"sumR={c.sum():+.1f} $={360*c.sum():+,.0f}")
        print(f"   BASE      n={len(b):3d} WR={100*(b>0).mean() if len(b) else 0:.1f}% "
              f"sumR={b.sum():+.1f} $={180*b.sum():+,.0f}")
        tot = 360 * c.sum() + 180 * b.sum()
        sep = ((c > 0).mean() - (b > 0).mean()) * 100 if len(c) and len(b) else float("nan")
        print(f"   TOTAL $={tot:+,.0f} | tier separation (CONF-BASE WR) {sep:+.1f}pp\n")

    flip = T.tier_leak.ne(T.tier_hon)
    print(f"tier flips: {int(flip.sum())}/{len(T)} ({100*flip.mean():.1f}%)")
    dn = T[(T.tier_leak == "CONFIRMED") & (T.tier_hon == "BASE")]
    up = T[(T.tier_leak == "BASE") & (T.tier_hon == "CONFIRMED")]
    print(f"  CONFIRMED only thanks to the leak: n={len(dn)} "
          f"WR={100*(dn.mech_R>0).mean() if len(dn) else 0:.1f}% sumR={dn.mech_R.sum():+.1f}")
    print(f"  newly CONFIRMED when honest:       n={len(up)} "
          f"WR={100*(up.mech_R>0).mean() if len(up) else 0:.1f}% sumR={up.mech_R.sum():+.1f}")
    allR = T.mech_R
    print(f"\nbase rate, no tier at all: n={len(allR)} WR={100*(allR>0).mean():.1f}% "
          f"sumR={allR.sum():+.1f}")
    T.to_parquet(ROOT / "output/leak_damage_shelf.parquet")
    print("wrote output/leak_damage_shelf.parquet")


if __name__ == "__main__":
    main()
