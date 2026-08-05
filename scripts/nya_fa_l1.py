#!/usr/bin/env python3
"""NYA-FA-01 — L1 mechanics, first declared expressions (trial 2).

FAIL branch (F-expressions), per prereg:
  F1  enter at the re-entry close (price closes back inside the composite),
      direction toward the composite POC; stop beyond the excursion extreme;
      target comp POC; time-stop 15:55.
  F2  as F1 but target = POC or 0.5x width from entry, whichever is nearer
      (geometry guard for wide composites).
ACCEPT branch (A-expressions):
  A1  after the 60-min window expires with no re-entry, enter on the first
      retest touch of the broken edge (limit at edge), direction with the
      break; stop = excursion-extreme mirror (1x initial excursion beyond
      the edge, capped 0.5x width); target 1.0x width beyond the edge;
      time-stop 15:55.
Costs: base 1pt and strict 2pt friction. Conservative intrabar tie-break.
$-at-$160-risk accounting (1/risk sizing) alongside points.

    python -m scripts.nya_fa_l1
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WINDOW = 60  # accept-branch window (minutes) — declared primary


def sim(direction, entry, stop, target, bars):
    """Conservative: stop before target inside a bar. Returns (pts, exit_reason)."""
    for hi, lo, cl in bars:
        if direction > 0:
            if lo <= stop:
                return stop - entry, "stop"
            if hi >= target:
                return target - entry, "target"
        else:
            if hi >= stop:
                return entry - stop, "stop"
            if lo <= target:
                return entry - target, "target"
    cl = bars[-1][2]
    return (cl - entry) if direction > 0 else (entry - cl), "time"


def report(T, label):
    if not len(T):
        print(f"  {label}: n=0"); return
    T = pd.DataFrame(T)
    for cost, cl in ((1.0, "base"), (2.0, "strict")):
        net = T.pts - cost
        r = net / T.risk
        gw, gl = net[net > 0].sum(), -net[net <= 0].sum()
        halves = " ".join(f"{h}:{x.sum():+.0f}" for h, x in net.groupby(T.era))
        print(f"  {label} [{cl}]: n={len(T)} WR {(net>0).mean():.0%} "
              f"{net.sum():+.0f}pts ${160*r.sum():+,.0f} PF {gw/max(gl,1e-9):.2f} | {halves}")


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert("America/New_York")
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]
    C = pd.read_parquet(ROOT / "output/nya_composites.parquet").set_index("day")

    F1, F2, A1 = [], [], []
    for d, r in R.groupby("gday"):
        if d not in C.index or not (C.loc[d, "comp_age"] >= 2):
            continue
        vah, val = float(C.loc[d, "comp_vah"]), float(C.loc[d, "comp_val"])
        poc, width = float(C.loc[d, "comp_poc"]), float(C.loc[d, "comp_vah"]) - float(C.loc[d, "comp_val"])
        if width <= 0:
            continue
        era = "23-24" if d[:4] in ("2023", "2024") else d[:4]
        r = r.sort_values("ts").reset_index(drop=True)
        elig = r[r.clock < "15:00"]
        out_up = elig[elig.close > vah]; out_dn = elig[elig.close < val]
        iu = out_up.index[0] if len(out_up) else None
        idn = out_dn.index[0] if len(out_dn) else None
        if iu is None and idn is None:
            continue
        if idn is None or (iu is not None and iu < idn):
            i0, side = iu, 1
        else:
            i0, side = idn, -1
        edge = vah if side > 0 else val
        after = r.loc[i0 + 1:]
        reent = after[(after.close < edge) if side > 0 else (after.close > edge)]
        i_re = reent.index[0] if len(reent) else None
        # prereg partition: FAIL = re-entry close within WINDOW; ACCEPT otherwise
        fail_in_window = i_re is not None and (i_re - i0) <= WINDOW
        seg = after.loc[:i_re] if i_re is not None else after
        ext = float((seg.high.max() - edge) if side > 0 else (edge - seg.low.min()))
        extreme = edge + side * ext

        if fail_in_window and r.loc[i_re].clock < "15:00":
            # FAIL branch: fade toward POC
            entry = float(r.loc[i_re].close)
            tail = r.loc[i_re + 1:]
            if not len(tail):
                continue
            bars = tail[["high", "low", "close"]].to_numpy()
            dirn = -side
            stop = extreme
            risk = abs(entry - stop)
            if risk < 2 or (side > 0 and entry <= poc) or (side < 0 and entry >= poc):
                continue
            pts, why = sim(dirn, entry, stop, poc, bars)
            F1.append(dict(pts=pts, risk=risk, era=era, extw=ext / width))
            t2 = poc if abs(entry - poc) <= 0.5 * width else entry - side * 0.5 * width
            pts, why = sim(dirn, entry, stop, t2, bars)
            F2.append(dict(pts=pts, risk=risk, era=era, extw=ext / width))
        else:
            # ACCEPT branch: window expired without a re-entry close -> retest
            # limit at the broken edge (later re-entries no longer disqualify;
            # they simply stop the trade out)
            iw = i0 + WINDOW
            post_w = after.loc[iw:]
            if not len(post_w):
                continue
            touch = post_w[(post_w.low <= edge) if side > 0 else (post_w.high >= edge)]
            if not len(touch) or touch.index[0] >= r.index[-1]:
                continue
            it = touch.index[0]
            entry = edge
            stop = edge - side * min(max(ext, 5.0), 0.5 * width)
            risk = abs(entry - stop)
            if risk < 2:
                continue
            target = edge + side * width
            bars = r.loc[it + 1:][["high", "low", "close"]].to_numpy()
            if not len(bars):
                continue
            pts, why = sim(side, entry, stop, target, bars)
            A1.append(dict(pts=pts, risk=risk, era=era))

    print(f"== NYA-FA-01 L1 (window {WINDOW}m) ==")
    report(F1, "F1 fail->POC, stop at extreme")
    report(F2, "F2 fail->min(POC, 0.5w)")
    report(A1, "A1 accept retest->1.0w")
    # first declared conditioning cut: extension depth (census live wire)
    T = pd.DataFrame(F2)
    if len(T):
        T["dq"] = pd.qcut(T.extw, 3, labels=["shallow", "mid", "deep"])
        print("-- F2 by extension-depth tercile (declared conditioner) --")
        for b, g in T.groupby("dq", observed=True):
            report(g.to_dict("records"), f"F2 ext-{b}")


if __name__ == "__main__":
    main()
