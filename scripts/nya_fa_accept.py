#!/usr/bin/env python3
"""NYA-FA-01 trial 5 — accept-branch conditioning (flow span).

Accept events (no re-entry close within 60 min of the composite break):
retest-limit entry at the broken edge after window expiry, with the break,
target 1.0 width, stop mirror of initial excursion (capped 0.5 width) — the
declared A1 expression. Declared gates tested: C1 excursion delta CONFIRMS
the break (side * exc_delta > 0); C2 CVD net-change over the excursion
confirms; D depth (excursion >= median). Full-span ungated A1 was ~flat
(trial 2: PF 1.02-1.04, n=62); this asks whether flow separates it.

    python -m scripts.nya_fa_accept
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
    fl_by_day = {d: g for d, g in FL.groupby("gday")}

    events = []
    for d in sorted(set(R[R.gday >= "2025-06-02"].gday) & set(fl_by_day)):
        if d not in C.index or not (C.loc[d, "comp_age"] >= 2):
            continue
        r = R[R.gday == d].sort_values("ts").reset_index(drop=True)
        vah, val = float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"])
        width = vah - val
        if width <= 0 or len(r) < 200:
            continue
        half = d[:4] + ("H1" if d[5:7] < "07" else "H2")
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
        if i_re is not None and (i_re - i0) <= WINDOW:
            continue  # fail branch, not ours
        seg = after.loc[:i_re] if i_re is not None else after
        ext = float((seg.high.max() - edge) if side > 0 else (edge - seg.low.min()))
        post_w = after.loc[i0 + WINDOW:]
        if not len(post_w):
            continue
        touch = post_w[(post_w.low <= edge) if side > 0 else (post_w.high >= edge)]
        if not len(touch):
            continue
        it = touch.index[0]
        entry = edge
        stop = edge - side * min(max(ext, 5.0), 0.5 * width)
        risk = abs(entry - stop)
        if risk < 2:
            continue
        bars = r.loc[it + 1:][["high", "low", "close"]].to_numpy()
        if not len(bars):
            continue
        pts = sim(side, entry, stop, edge + side * width, bars)
        f = fl_by_day[d]
        brk_clock = r.loc[i0].clock
        w_end = r.loc[min(i0 + WINDOW, r.index[-1])].clock
        exc = f[(f.clock >= brk_clock) & (f.clock <= w_end)]
        exc_delta = float(exc.delta.sum()) if len(exc) else 0.0
        c1 = bool(side * exc_delta > 0)
        cvd_d = float(exc.cvd.iloc[-1] - exc.cvd.iloc[0]) if len(exc) else 0.0
        c2 = bool(side * cvd_d > 0)
        events.append(dict(day=d, half=half, pts=pts, risk=risk, extw=ext / width,
                           c1=c1, c2=c2))
    E = pd.DataFrame(events)
    E.to_parquet(ROOT / "output/nya_fa_accept_events.parquet", index=False)
    print(f"flow-span ACCEPT events: {len(E)} | C1 {E.c1.mean():.0%} C2 {E.c2.mean():.0%}")
    rep(E.to_dict("records"), "A1 ungated")
    rep(E[E.c1].to_dict("records"), "A1 + C1 delta-confirm")
    rep(E[E.c2].to_dict("records"), "A1 + C2 cvd-confirm")
    deep = E[E.extw >= E.extw.median()]
    rep(deep.to_dict("records"), "A1 deep-half")
    rep(E[E.c1 & (E.extw >= E.extw.median())].to_dict("records"), "A1 + C1 + deep")


if __name__ == "__main__":
    main()
