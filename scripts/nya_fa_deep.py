#!/usr/bin/env python3
"""NYA-FA-01 trial 8 — the deep pass: wall-at-entry + remaining candle
variables (day type, open type), per the canon-parity reopening.

Wall read (first live use of output/depth_minutes.parquet): at the fail-
branch entry minute (re-entry close), the fade-supporting side's wall_ratio —
ask side for shorts (resistance above a failed upside break), bid side for
longs. Coverage is partial by construction (depth = 08:00-10:29 ET mornings);
events entering later have no read and are reported as such, never imputed.

Candle variables (full span, F2 base expression): day_type and open_type
(output/amt_days.parquet) — a cut must be bad in EVERY era to be legal
(wall-quality-cut precedent).

    python -m scripts.nya_fa_deep
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WINDOW, FR = 60, 1.0


def sim(direction, entry, stop, target, bars):
    for hi, lo, cl in bars:
        if direction > 0:
            if lo <= stop: return stop - entry
            if hi >= target: return target - entry
        else:
            if hi >= stop: return entry - stop
            if lo <= target: return entry - target
    cl = bars[-1][2] if len(bars) else entry
    return (cl - entry) if direction > 0 else (entry - cl)


def rep(T, label):
    if not len(T):
        print(f"  {label}: n=0"); return
    net = T.pts - FR
    r = net / T.risk
    gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
    key = T.era if "era" in T else T.half
    halves = " ".join(f"{h}:{x.sum():+.0f}" for h, x in net.groupby(key))
    print(f"  {label}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r.sum():+,.0f} PF {gw/max(gl,1e-9):.2f} | {halves}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")
    A = pd.read_parquet(ROOT / "output/amt_days.parquet").set_index("day")
    FL = pd.read_parquet(ROOT / "output/flow_minute_features.parquet")
    fl_by_day = {d: g for d, g in FL.groupby("gday")}
    D = pd.read_parquet(ROOT / "output/depth_minutes.parquet")
    D = D.assign(gday=pd.Series(D.index.date, index=D.index).astype(str),
                 clock=D.index.strftime("%H:%M"))
    d_by_day = {d: g.set_index("clock") for d, g in D.groupby("gday")}

    full, flow = [], []
    for d, r in R.groupby("gday"):
        if d not in C.index or not (C.loc[d, "comp_age"] >= 2):
            continue
        vah, val = float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"])
        poc, width = float(C.loc[d, "comp_poc"]), float(C.loc[d, "comp_vah"]) - float(C.loc[d, "comp_val"])
        if width <= 0:
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        if len(r) < 200:
            continue
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
        if (side > 0 and entry <= poc) or (side < 0 and entry >= poc):
            continue
        stop = entry + side * max(0.5 * ext, 5.0)
        risk = abs(entry - stop)
        if risk < 2:
            continue
        t2 = poc if abs(entry - poc) <= 0.5 * width else entry - side * 0.5 * width
        bars = r.loc[i_re + 1:][["high", "low", "close"]].to_numpy()
        pts = sim(-side, entry, stop, t2, bars)
        era = "23-24" if d[:4] in ("2023", "2024") else d[:4]
        rec = dict(day=d, era=era, half=d[:4] + ("H1" if d[5:7] < "07" else "H2"),
                   pts=pts, risk=risk,
                   day_type=A.loc[d, "day_type"] if d in A.index else None,
                   open_type=A.loc[d, "open_type"] if d in A.index else None)
        full.append(rec)
        if d >= "2025-06-02" and d in fl_by_day:
            f = fl_by_day[d]
            exc = f[(f.clock >= r.loc[i0].clock) & (f.clock <= r.loc[i_re].clock)]
            g2 = bool(side * float(exc.delta.sum()) < 0) if len(exc) else False
            wall = np.nan
            dep = d_by_day.get(d)
            eclock = r.loc[i_re].clock
            if dep is not None and eclock in dep.index:
                snap = dep.loc[eclock]
                wall = float(snap.ask_wall_ratio if side > 0 else snap.bid_wall_ratio)
            flow.append({**rec, "g2": g2, "extw": ext / width, "wall": wall})

    F = pd.DataFrame(full)
    print("== candle variables, F2 base, FULL SPAN (cut must be bad every era) ==")
    for var in ("day_type", "open_type"):
        for v, g in F.groupby(var):
            eras_neg = {e: (gg.pts - FR).sum() < 0 for e, gg in g.groupby("era")}
            tag = " [bad EVERY era]" if all(eras_neg.values()) and len(eras_neg) == 3 else ""
            rep(g, f"{var}={v}{tag}")
    FLW = pd.DataFrame(flow)
    FLW["deep"] = FLW.extw >= FLW.extw.median()
    spec = FLW[FLW.deep & FLW.g2]
    print(f"== wall-at-entry, flow span (coverage {FLW.wall.notna().mean():.0%} of {len(FLW)} events; "
          f"spec cohort {spec.wall.notna().mean():.0%} of {len(spec)}) ==")
    rep(spec, "spec (deep+G2/S2), all")
    rep(spec[spec.wall >= 3.0], "spec + wall>=3 (canon-style)")
    rep(spec[spec.wall < 3.0], "spec + wall<3")
    rep(spec[spec.wall.isna()], "spec, no wall data (post-10:29 entries)")


if __name__ == "__main__":
    main()
