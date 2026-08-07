#!/usr/bin/env python3
"""NYA-FA-01 trial 9 — THE 23/24 CANDLE LOOK (§5.9.4: one look; on failure,
one diagnose-and-rebalance retest; fails again -> does not ship).

What is being looked at: the CANDLE SKELETON of the frozen spec — fail-branch
re-entry fade, S2 half-excursion stop, min(POC, 0.5w) target, DEEP-excursion
cohort (extw >= the FLOW-SPAN median, frozen before this look), with and
without the test_drive cut (trial 8's legal arm). The flow gate (G2) cannot
be evaluated on 23/24 candles — that is what the sealed flow months are for,
later, by written declaration.

Context already on the record (not part of this look): trial 2 showed the
RAW unconditioned F2 negative in 23-24 — raw ugliness is expected and was
never the question. The question: does the CONDITIONED skeleton hold?

    python -m scripts.nya_fa_2324_look
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WINDOW, FR = 60, 1.0
DEEP_MEDIAN_FLOWSPAN = None  # computed from flow events file — frozen input


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
    yr = " ".join(f"{y}:{x.sum():+.0f}" for y, x in net.groupby(T.year))
    print(f"  {label}: n={len(T)} WR {(net>0).mean():.0%} {net.sum():+.0f}pts "
          f"${160*r.sum():+,.0f} PF {gw/max(gl,1e-9):.2f} | {yr}")


def main() -> None:
    dm = float(pd.read_parquet(ROOT / "output/nya_fa_flow_events.parquet").extw.median())
    print(f"frozen deep threshold (flow-span median extw): {dm:.3f}")

    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00") & (B.gday < "2025-01-01")]
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")
    A = pd.read_parquet(ROOT / "output/amt_days.parquet").set_index("day")

    rows = []
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
        pts = sim(-side, entry, stop, t2, r.loc[i_re + 1:][["high", "low", "close"]].to_numpy())
        rows.append(dict(day=d, year=d[:4], pts=pts, risk=risk, extw=ext / width,
                         open_type=A.loc[d, "open_type"] if d in A.index else None))
    T = pd.DataFrame(rows)
    T.to_parquet(ROOT / "output/nya_fa_2324_look.parquet", index=False)
    print(f"== 23/24 LOOK — {len(T)} fail events ==")
    rep(T, "ungated (context)")
    deep = T[T.extw >= dm]
    rep(deep, "DEEP cohort (the skeleton)")
    rep(deep[deep.open_type != "test_drive"], "DEEP + test_drive cut (declared arm)")
    rep(T[T.extw < dm], "shallow (should be bad)")


if __name__ == "__main__":
    main()
