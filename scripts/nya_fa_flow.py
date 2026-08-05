#!/usr/bin/env python3
"""NYA-FA-01 — trial 3: flow-at-entry discriminator search + stop-geometry arms.

Flow span only (2025-06..2026-07). For every FAIL-branch event (60-min window,
same partition as nya_fa_l1), joins output/flow_minute_features.parquet and
tests the DECLARED discriminators (docs/PREREG-failed-auction.md):

  G1 edge-absorption   any absorb flag with absorb_side == -side (the
                       breakout side's aggression absorbed) in the excursion's
                       last 5 minutes through re-entry+2.
  G2 excursion delta   cumulative delta of the outside excursion opposes the
                       break (side * exc_delta < 0) — the chase wasn't paid.
  G3 CVD divergence    price extended beyond the edge but session CVD at
                       re-entry is BELOW its value at the break (long breaks;
                       mirror for shorts) — his Dec-30 pattern generalized.

Stop-geometry arms (declared, cure for the deep-cohort disease):
  S1 stop at excursion extreme (current)   S2 stop 0.5 x ext beyond entry
  S3 fixed 25 pt stop
All combinations reported gated vs ungated, era-split (25H2/26H1/26H2), base
friction; strict shown for the leading cell. Target: F2 rule (min(POC, 0.5w)).

    python -m scripts.nya_fa_flow
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WINDOW = 60


def sim(direction, entry, stop, target, bars):
    for hi, lo, cl in bars:
        if direction > 0:
            if lo <= stop: return stop - entry
            if hi >= target: return target - entry
        else:
            if hi >= stop: return entry - stop
            if lo <= target: return entry - target
    cl = bars[-1][2]
    return (cl - entry) if direction > 0 else (entry - cl)


def rep(rows, label, cost=1.0):
    if not rows:
        print(f"  {label}: n=0"); return
    T = pd.DataFrame(rows)
    net = T.pts - cost
    r = net / T.risk
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    halves = " ".join(f"{h}:{x.sum():+.0f}" for h, x in net.groupby(T.half))
    print(f"  {label}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r.sum():+,.0f} PF {gw/max(gl,1e-9):.2f} | {halves}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")
    FL = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    FL = FL.reset_index().rename(columns={"index": "mi", "mi": "mi"})
    FL["mi"] = pd.to_datetime(FL[FL.columns[0]]) if FL.columns[0] != "gday" else FL["mi"]

    fl_by_day = {d: g for d, g in FL.groupby("gday")}

    events = []
    for d, r in R.groupby("gday"):
        if d < "2025-06-02" or d not in C.index or not (C.loc[d, "comp_age"] >= 2) or d not in fl_by_day:
            continue
        vah, val = float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"])
        poc = float(C.loc[d, "comp_poc"])
        width = vah - val
        if width <= 0:
            continue
        half = d[:4] + ("H1" if d[5:7] < "07" else "H2")
        r = r.sort_values("ts").reset_index(drop=True)
        elig = r[r.clock < "15:00"]
        out_up = elig[elig.close > vah]; out_dn = elig[elig.close < val]
        iu = out_up.index[0] if len(out_up) else None
        idn = out_dn.index[0] if len(out_dn) else None
        if iu is None and idn is None:
            continue
        side = 1 if (idn is None or (iu is not None and iu < idn)) else -1
        i0 = iu if side > 0 else idn
        edge = vah if side > 0 else val
        after = r.loc[i0 + 1:]
        reent = after[(after.close < edge) if side > 0 else (after.close > edge)]
        i_re = reent.index[0] if len(reent) else None
        if i_re is None or (i_re - i0) > WINDOW or r.loc[i_re].clock >= "15:00":
            continue
        seg = after.loc[:i_re]
        ext = float((seg.high.max() - edge) if side > 0 else (edge - seg.low.min()))
        entry = float(r.loc[i_re].close)
        tail = r.loc[i_re + 1:]
        if not len(tail):
            continue
        if (side > 0 and entry <= poc) or (side < 0 and entry >= poc):
            continue
        f = fl_by_day[d]
        f = f.assign(minute=pd.to_datetime(f.iloc[:, 0]) if f.columns[0] not in ("gday",) else None)
        # clock-based join
        brk_clock, re_clock = r.loc[i0].clock, r.loc[i_re].clock
        exc = f[(f.clock >= brk_clock) & (f.clock <= re_clock)]
        pre_re = f[(f.clock > max(brk_clock, chr(0))) & (f.clock >= _sub5(re_clock)) & (f.clock <= _add2(re_clock))]
        exc_delta = float(exc.delta.sum()) if len(exc) else np.nan
        g1 = bool((pre_re.absorb & (pre_re.absorb_side == -side)).any()) if len(pre_re) else False
        g2 = bool(side * exc_delta < 0) if exc_delta == exc_delta else False
        cvd_b = float(exc.cvd.iloc[0]) if len(exc) else np.nan
        cvd_e = float(exc.cvd.iloc[-1]) if len(exc) else np.nan
        g3 = bool(side * (cvd_e - cvd_b) < 0) if len(exc) else False
        t2 = poc if abs(entry - poc) <= 0.5 * width else entry - side * 0.5 * width
        bars = tail[["high", "low", "close"]].to_numpy()
        extreme = edge + side * ext
        stops = {"S1_extreme": extreme,
                 "S2_halfext": entry + side * max(0.5 * ext, 5.0),
                 "S3_25pt": entry + side * 25.0}
        ev = dict(day=d, half=half, extw=ext / width, g1=g1, g2=g2, g3=g3)
        for sname, stp in stops.items():
            risk = abs(entry - stp)
            if risk < 2:
                continue
            ev[sname] = sim(-side, entry, stp, t2, bars)
            ev[sname + "_risk"] = risk
        events.append(ev)

    E = pd.DataFrame(events)
    E.to_parquet(ROOT / "output/nya_fa_flow_events.parquet", index=False)
    print(f"flow-span FAIL events: {len(E)} | gate rates: G1 {E.g1.mean():.0%} "
          f"G2 {E.g2.mean():.0%} G3 {E.g3.mean():.0%}")
    for sname in ("S1_extreme", "S2_halfext", "S3_25pt"):
        ok = E.dropna(subset=[sname])
        print(f"-- stop {sname} --")
        rep([dict(pts=x, risk=k, half=h) for x, k, h in
             zip(ok[sname], ok[sname + "_risk"], ok.half)], "ungated")
        for gname in ("g1", "g2", "g3"):
            gg = ok[ok[gname]]
            rep([dict(pts=x, risk=k, half=h) for x, k, h in
                 zip(gg[sname], gg[sname + "_risk"], gg.half)], f"gated {gname}")
        deep = ok[ok.extw >= ok.extw.median()]
        rep([dict(pts=x, risk=k, half=h) for x, k, h in
             zip(deep[sname], deep[sname + "_risk"], deep.half)], "deep-half")


def _sub5(clock: str) -> str:
    h, m = int(clock[:2]), int(clock[3:])
    t = h * 60 + m - 5
    return f"{t // 60:02d}:{t % 60:02d}"


def _add2(clock: str) -> str:
    h, m = int(clock[:2]), int(clock[3:])
    t = h * 60 + m + 2
    return f"{t // 60:02d}:{t % 60:02d}"


if __name__ == "__main__":
    main()
