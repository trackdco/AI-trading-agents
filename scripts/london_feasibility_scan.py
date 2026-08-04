#!/usr/bin/env python3
"""Feasibility scan of the six remaining London candidates. NOT A TEST.

WHAT THIS IS. For each candidate, how often does its trigger actually FIRE inside the true
London window (08:00-10:00 Europe/London, converted per day)? Nothing else. No outcome,
no return, no P&L, no direction is computed anywhere in this file — so no selection can
occur and no statistical power is spent. It is the counting exercise that §2.2's n-floors
presuppose, and it answers one question per candidate:

    can this candidate reach n >= 30 events per era, or is it untestable on our sample?

WHY IT MATTERS. LDN-INV-01 spent a diagnostic, a prereg and a census before anyone noticed
the validate era held 28 days per cell. Counting first is free and would have said so on
day one.

THIS IS NOT A PREREG AND AUTHORISES NOTHING. Each candidate still needs its own
pre-registration before any outcome is measured.

SEALED-SPAN GUARD: 2023/24 dropped and asserted gone.

    python -m scripts.london_feasibility_scan
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import fit_only
from scripts.ldn_swp01_london_only import london_window_et

FLOOR = 30


def scan() -> pd.DataFrame:
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(
        "America/New_York"))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    by_day = {d: g for d, g in bars.groupby("day", sort=False)}

    rows = []
    for r in sub.itertuples():
        g = by_day.get(r.day)
        if g is None:
            continue
        start, end = london_window_et(r.day)
        w = g[(g.ts >= start) & (g.ts <= end)]
        if len(w) < 30:
            continue
        o, hi, lo = w.close.iloc[0], w.high.max(), w.low.min()

        # --- euro-open-drive: does the London open print OUTSIDE the Asia range?
        drive_gate = bool(o > r.asia_hi or o < r.asia_lo)

        # --- vwap-sigma-rotation: does price touch +/-2 sigma of overnight VWAP?
        up2, dn2 = r.on_vwap_0255 + 2 * r.on_sigma_0255, r.on_vwap_0255 - 2 * r.on_sigma_0255
        sigma_touch = bool(hi >= up2 or lo <= dn2)

        # --- level-trap-fade: break a watched level then close back through it
        trap = False
        for lvl, side in ((r.on_hi_0300, +1), (r.on_lo_0300, -1),
                          (r.prior_rth_hi, +1), (r.prior_rth_lo, -1)):
            if pd.isna(lvl):
                continue
            if side > 0:
                brk = w.index[w.high > lvl]
                if len(brk) and (w.loc[brk[0]:, "close"] < lvl).any():
                    trap = True
            else:
                brk = w.index[w.low < lvl]
                if len(brk) and (w.loc[brk[0]:, "close"] > lvl).any():
                    trap = True
            if trap:
                break

        rows.append({"day": r.day, "era": r.day[:4], "drive_gate": drive_gate,
                     "sigma_touch": sigma_touch, "trap": trap})
    return pd.DataFrame(rows)


def main() -> None:
    d = scan()
    print("LONDON FEASIBILITY SCAN — event counts only, no outcomes measured")
    print(f"window: 08:00-10:00 Europe/London per day | days: {len(d)} "
          f"({', '.join(f'{e}: {(d.era == e).sum()}' for e in ('2025', '2026'))})\n")

    checks = [
        ("euro-open-drive", "drive_gate", "London open prints outside the Asia range"),
        ("vwap-sigma-rotation", "sigma_touch", "price touches +/-2 sigma of overnight VWAP"),
        ("level-trap-fade", "trap", "watched level broken then closed back through"),
    ]
    print(f"{'candidate':>22} {'2025':>7} {'2026':>7} {'rate':>7}  gate")
    print("-" * 88)
    for name, col, desc in checks:
        n25 = int(d[(d.era == '2025')][col].sum())
        n26 = int(d[(d.era == '2026')][col].sum())
        rate = d[col].mean()
        ok = "OK" if min(n25, n26) >= FLOOR else f"BELOW n>={FLOOR}"
        print(f"{name:>22} {n25:>7} {n26:>7} {rate * 100:>6.0f}%  {desc}  [{ok}]")

    print(f"\n{'candidate':>22}  status (no count possible yet)")
    print("-" * 88)
    fp = ROOT / "output/fp_minutes.parquet"
    span = "present" if fp.exists() else "MISSING locally"
    print(f"{'level-defense-flow':>22}  flow-essential, Jun-2025+ only. "
          f"output/fp_minutes.parquet: {span}.")
    print(f"{'':>22}  Thesis itself predicts an NY veto (depth/flow = the canon's own")
    print(f"{'':>22}  input family). Cheapest next step is the veto conversation, not a test.")
    print(f"{'value-traverse':>22}  needs a volume-at-price map (naked POC / value area) built")
    print(f"{'':>22}  from 1-min bars. Buildable, not built. Count needs the map first.")
    print(f"{'eu-macro-windows':>22}  needs the EU release calendar 2023-2026. ZERO data today.")
    print(f"{'':>22}  Build is the prerequisite; a null still pays (event dummies).")

    print("\nNOTE: these are UPPER BOUNDS on tradeable events. Each candidate layers further")
    print("gates (one-time-framing, rejection closes, level quality, regime splits) that only")
    print("reduce the count. A candidate near the floor here will fall under it in practice.")


if __name__ == "__main__":
    main()
