#!/usr/bin/env python3
"""How much of the exit headroom is capturable with NO judgment — just a trailing stop?

ANGUS 2026-07-27: *"im not worried heavily about cutting losers, theres more money in
capturing trades for what they are actually worth."* That reframes the +1R base rate:
72% of trades reaching +1R run at least 1R further, so the prior already says HOLD. No
discrimination is required to stay in — only a stop that follows.

This prices dumb trailing policies against the canon's own realized exits on exactly the
same fills. It matters because it sets the bar for any discretionary exit layer: an agent
must beat the best MECHANICAL trail, not the current book. If a constant trail captures
most of the room, judgment is not where the money is. If it does not, the residual is what
judgment has to earn.

    python -m scripts.trail_policies

Simulation, deliberately pessimistic where 1-minute bars are ambiguous:
  * ADVERSE-FIRST within every bar — the low is assumed to trade before the high on a
    long. Where a bar could both stop us out and make a new high, we take the stop. This
    understates every policy rather than flattering it.
  * the trail only ARMS at +1R; before that the original structural stop stands
  * flat at 16:00 ET (the engine's flatten belt), filled at the close
  * no slippage, no commission, no partials — a ceiling on each policy, but a FAIR one,
    since the canon baseline is priced from the same bars
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BARS = ROOT / "data/reference/nq_1m_master.parquet"
BOOK = ROOT / "output/canon_book.parquet"
NY = "America/New_York"
SESSION_END = 16 * 60
ARM_AT = 1.0            # R at which the trail arms


def load_bars() -> pd.DataFrame:
    b = pd.read_parquet(BARS)
    ts = pd.to_datetime(b["ts_event"], utc=True).dt.tz_convert(NY)
    return b.assign(ts=ts, day=ts.dt.strftime("%Y-%m-%d"),
                    mins=ts.dt.hour * 60 + ts.dt.minute).sort_values("ts")


def simulate(bars_day, fill_ts, entry, stop, sign, risk, trail_R, be_at=None):
    """Walk the bars applying a trailing stop. Returns realized R.

    trail_R: distance in R the stop follows behind the high-water mark, once armed.
             None = never trail (hold to the structural stop or the flatten belt).
    be_at:   R at which the stop first jumps to break-even, before the trail arms.
    """
    fwd = bars_day[(bars_day.ts >= fill_ts) & (bars_day.mins <= SESSION_END)]
    if fwd.empty:
        return np.nan
    cur_stop = stop
    hwm = 0.0
    armed = False
    for b in fwd.itertuples():
        hi = b.high if sign > 0 else b.low          # favourable extreme
        lo = b.low if sign > 0 else b.high          # adverse extreme

        # ADVERSE FIRST — pessimistic by construction
        if (lo <= cur_stop) if sign > 0 else (lo >= cur_stop):
            return sign * (cur_stop - entry) / risk

        r_hi = sign * (hi - entry) / risk
        hwm = max(hwm, r_hi)
        if be_at is not None and hwm >= be_at:
            cur_stop = max(cur_stop, entry) if sign > 0 else min(cur_stop, entry)
        if trail_R is not None:
            if hwm >= ARM_AT:
                armed = True
            if armed:
                t = entry + sign * (hwm - trail_R) * risk
                cur_stop = max(cur_stop, t) if sign > 0 else min(cur_stop, t)
    last = fwd.iloc[-1]
    return sign * (last.close - entry) / risk       # flat at the belt


def main() -> None:
    C = pd.read_parquet(BOOK)
    taken = C[C["size"] > 0].copy()
    bars = load_bars()
    by_day = {d: g for d, g in bars.groupby("day")}

    policies = {
        "canon (baseline)": None,
        "hold, structural stop": ("hold", None, None),
        "BE at 1R, no trail": ("t", None, 1.0),
        "trail 0.5R": ("t", 0.5, None),
        "trail 1.0R": ("t", 1.0, None),
        "trail 1.5R": ("t", 1.5, None),
        "trail 2.0R": ("t", 2.0, None),
        "BE at 1R + trail 1R": ("t", 1.0, 1.0),
        "BE at 1R + trail 1.5R": ("t", 1.5, 1.0),
    }

    rows = []
    for t in taken.itertuples():
        g = by_day.get(str(t.day))
        if g is None:
            continue
        sign = 1.0 if t.direction == "long" else -1.0
        risk = float(t.risk)
        if risk <= 0:
            continue
        rec = {"day": t.day, "win_": t.win_, "risk": risk, "size": t.size,
               "canon_R": float(t.R), "canon_dollars": float(t.dollars)}
        fill = pd.Timestamp(t.fill)
        for name, spec in policies.items():
            if spec is None:
                continue
            kind, tr, be = spec
            r = simulate(g, fill, float(t.entry), float(t.stop), sign, risk,
                         None if kind == "hold" else tr, be)
            rec[name] = r
        rows.append(rec)
    D = pd.DataFrame(rows).dropna(subset=["trail 1.0R"])
    if D.empty:
        raise SystemExit("no trades simulated")

    # dollars: R x risk x $20/pt (1 NQ) x the canon's own size multiplier
    def dollars(rcol):
        return (D[rcol] * D.risk * 20 * D["size"]).sum()

    base_d = (D.canon_dollars * D["size"]).sum()
    base_r = D.canon_R.sum()

    print(f"{len(D)} taken canon trades re-simulated on 1m bars "
          f"({D.day.nunique()} days)\n")
    print(f"{'policy':<26}{'total R':>10}{'$ (sized)':>14}{'vs canon':>12}"
          f"{'win rate':>10}{'median R':>10}")
    print("-" * 82)
    print(f"{'canon (baseline)':<26}{base_r:>10.1f}{base_d:>14,.0f}{'—':>12}"
          f"{(D.canon_R > 0).mean() * 100:>9.0f}%{D.canon_R.median():>10.2f}")
    for name in policies:
        if name == "canon (baseline)":
            continue
        d = dollars(name)
        print(f"{name:<26}{D[name].sum():>10.1f}{d:>14,.0f}{d - base_d:>+12,.0f}"
              f"{(D[name] > 0).mean() * 100:>9.0f}%{D[name].median():>10.2f}")

    best = max((n for n in policies if n != "canon (baseline)"), key=dollars)
    print("\nby window, best mechanical trail vs canon:")
    print(f"{'window':<8}{'n':>5}{'canon $':>12}{'best $':>12}{'delta':>12}   ({best})")
    print("-" * 55)
    for w in sorted(D.win_.dropna().unique()):
        g = D[D.win_ == w]
        cb = (g.canon_dollars * g["size"]).sum()
        bb = (g[best] * g.risk * 20 * g["size"]).sum()
        print(f"{w:<8}{len(g):>5}{cb:>12,.0f}{bb:>12,.0f}{bb - cb:>+12,.0f}")

    print("\n" + "=" * 82)
    print("WHAT THIS SETS. The best number here is the bar a discretionary exit layer must")
    print("beat — not the canon's current exit. If a constant trail already captures the")
    print("room, judgment is not where the money is. Whatever it leaves on the table versus")
    print("the 5.08R median MFE is the residual judgment has to earn.")
    print("\nADVERSE-FIRST bar handling makes every trail number PESSIMISTIC; real fills sit")
    print("somewhere above. Slippage and commission are excluded on both sides. And this is")
    print("all IN-FIT — it goes to the 2023/24 holdout before it means anything.")


if __name__ == "__main__":
    main()
