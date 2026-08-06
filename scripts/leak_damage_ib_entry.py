#!/usr/bin/env python3
"""LEAK DAMAGE — IB fade ENTRY lookahead (ANGUS 2026-08-06).

Found while verifying the claim "the shelf's entry trigger is clean". It is not.

nya_ivb_desk_run.build_trades:163-167 walks the 10:00-10:30 window:

    if row.close > ibh or row.close < ibl:   # abort BEFORE considering the touch
        break
    if row.high >= ibh: touch = (-1, i); break
    if row.low  <= ibl: touch = ( 1, i); break

The abort is evaluated on minute i's CLOSE, before the touch on minute i is
recorded. So when a minute BOTH touches the IB extreme AND closes beyond it, the
walk breaks and no trade is recorded — but live, a resting limit at that extreme
filled intra-minute, and price then closed through it. Those are precisely the
immediate-failure fades. The backtest uses end-of-minute information to decline
entries it could not have declined in real time.

Two live-implementable treatments of the dropped days:
  (a) FULL WALK   — take the fill, manage it with the frozen exit rules.
  (b) STAND-DOWN  — take the fill, exit at the close of the touch minute (the
      earliest moment the "closed beyond the IB" rule is actually knowable).
(b) is the charitable reading: it is the abort rule implemented honestly, as an
exit rather than as a refusal-to-enter.

    python -m scripts.leak_damage_ib_entry
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_ibc_desk_run import FIT0, FIT1, FR, NY  # noqa: E402


def walk(r, i0, side, entry, rng):
    """Frozen shelf management walk from the fill minute."""
    legacy = 0.25 * rng     # build_trades: risk = |entry-stop| = 0.25*rng
    stop_d = 0.5 * legacy   # build_shelf_trades: stop_d = 0.5*legacy
    H, L_, C = r.high.to_numpy(), r.low.to_numpy(), r.close.to_numpy()
    V = r.volume.clip(lower=0).to_numpy().astype(float)
    tp = (H + L_ + C) / 3
    cv = np.maximum(V.cumsum(), 1)
    vwap = (tp * V).cumsum() / cv
    sd = np.sqrt(np.clip((tp ** 2 * V).cumsum() / cv - vwap ** 2, 0, None))
    pnl = None
    for m in range(1, len(r) - i0):
        j = i0 + m
        hi, lo, cl = H[j], L_[j], C[j]
        adv = (hi - entry) if side < 0 else (entry - lo)
        if adv >= stop_d:
            pnl = -stop_d; break
        band = vwap[j] - side * sd[j]
        if side * (band - entry) >= 0.125 * legacy and \
           ((side < 0 and lo <= band) or (side > 0 and hi >= band)):
            pnl = side * (band - entry); break
        rn = (entry - cl) if side < 0 else (cl - entry)
        if m == 10 and rn < 0:
            pnl = rn; break
    if pnl is None:
        pnl = side * (C[-1] - entry)
    return (pnl - FR) / stop_d, stop_d


def main() -> None:
    B = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    ts = pd.to_datetime(B.ts_event).dt.tz_convert(NY)
    B = B.assign(ts=ts, clock=ts.dt.strftime("%H:%M"))
    B["gday"] = (B.ts + pd.Timedelta(hours=6)).dt.date.astype(str)
    R = B[(B.clock >= "09:30") & (B.clock < "16:00")]

    kept, drop_a, drop_b = [], [], []
    for d, r in R.groupby("gday"):
        if not (FIT0 <= d <= FIT1):          # SAME span as the shipped shelf book
            continue
        r = r.sort_values("ts").reset_index(drop=True)
        ib = r[r.clock < "10:00"]
        if len(ib) < 25 or len(r) < 200:
            continue
        ibh, ibl = ib.high.max(), ib.low.min()
        rng = ibh - ibl
        if rng <= 0:
            continue
        win = r[(r.clock >= "10:00") & (r.clock < "10:30")]
        for i, row in win.iterrows():
            beyond = row.close > ibh or row.close < ibl
            touches = row.high >= ibh or row.low <= ibl
            if beyond and touches:
                side = -1 if row.high >= ibh else 1
                entry = ibh if side < 0 else ibl
                Rv, stop_d = walk(r, i, side, entry, rng)
                drop_a.append(Rv)
                # stand-down: exit at the close of the touch minute
                pnl_b = side * (row.close - entry)
                drop_b.append((pnl_b - FR) / stop_d)
                break
            if beyond:
                break
            if touches:
                side = -1 if row.high >= ibh else 1
                entry = ibh if side < 0 else ibl
                kept.append(walk(r, i, side, entry, rng)[0])
                break

    kept = np.array(kept); da = np.array(drop_a); db = np.array(drop_b)

    def line(tag, x):
        if not len(x):
            print(f"  {tag}: none"); return
        print(f"  {tag}: n={len(x):3d} WR={100*(x>0).mean():5.1f}% "
              f"sumR={x.sum():+7.1f} meanR={x.mean():+.2f}")

    print(f"IB fade entry, fit span {FIT0}..{FIT1}\n")
    print("AS SHIPPED (backtest silently declines the touched-and-closed-beyond days):")
    line("recorded trades", kept)
    print(f"\nSILENTLY DROPPED — live would have been filled: n={len(da)} "
          f"({100*len(da)/(len(da)+len(kept)):.0f}% of all real fills)")
    line("(a) full walk ", da)
    line("(b) stand-down", db)
    print("\nHONEST TOTAL (what a live system actually trades):")
    line("(a) shipped + dropped, full walk ", np.concatenate([kept, da]))
    line("(b) shipped + dropped, stand-down", np.concatenate([kept, db]))


if __name__ == "__main__":
    main()
