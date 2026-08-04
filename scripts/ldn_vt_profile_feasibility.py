#!/usr/bin/env python3
"""FEASIBILITY for london-value-traverse legs (a) naked-POC and (c) LVN. NOT A TEST.

`ldn_remaining_feasibility.py` showed leg (b) — the 80% rule — collapses to 4/1 events.
That is only one of the candidate's three composable pieces, so calling the whole
candidate on it would be unfair. This file builds the volume-at-price machinery the other
two legs need and counts them.

Counts only. No outcome, return or direction is computed. No power spent, no trial.

VOLUME-AT-PRICE: built from 1-min bars by distributing each bar's volume uniformly across
its [low, high] range into 1-point buckets. This is the approximation the thesis itself
specifies and flags ("volume-at-price is an approximation from 1-min OHLCV — the fidelity
question goes on the trial ledger").

  leg (a) naked POC — a prior session's POC never traded through since it formed, sitting
                      beyond the Asian extreme so the rotation has a magnet to run at.
  leg (c) LVN       — a low-volume node in the rolling composite that London enters.

Both "reach" and "how low is low" are free parameters the thesis does not pin, so both are
reported as LADDERS rather than as point definitions.

SEALED-SPAN GUARD: 2023/24 dropped via fit_only(). No holdout look.

    python -m scripts.ldn_vt_profile_feasibility
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import fit_only
from scripts.ldn_swp01_london_only import london_window_et

NY = "America/New_York"
FLOOR = 30
BUCKET = 1.0            # 1-point price buckets
VA_SHARE = 0.70         # value area = 70% of volume around the POC
NAKED_LOOKBACK = 20     # sessions of POC history to carry, per the thesis
REACH_LADDER = (50, 100, 200)      # points from the Asian extreme to the magnet
LVN_PCTL_LADDER = (10, 20, 30)     # "low volume" = below this percentile of the composite


def day_profile(g: pd.DataFrame) -> dict[float, float]:
    """Volume distributed uniformly across each bar's range into 1-pt buckets."""
    prof: dict[float, float] = defaultdict(float)
    lo = np.floor(g.low.to_numpy() / BUCKET) * BUCKET
    hi = np.floor(g.high.to_numpy() / BUCKET) * BUCKET
    vol = g.volume.to_numpy(float)
    for a, b, v in zip(lo, hi, vol):
        n = int((b - a) / BUCKET) + 1
        if n <= 0 or not np.isfinite(v):
            continue
        share = v / n
        for k in range(n):
            prof[a + k * BUCKET] += share
    return prof


def poc_and_va(prof: dict[float, float]) -> tuple[float, float, float]:
    if not prof:
        return float("nan"), float("nan"), float("nan")
    prices = np.array(sorted(prof))
    vols = np.array([prof[p] for p in prices])
    poc = float(prices[int(vols.argmax())])
    order = np.argsort(-vols)
    target, run, chosen = VA_SHARE * vols.sum(), 0.0, []
    for i in order:
        chosen.append(prices[i])
        run += vols[i]
        if run >= target:
            break
    return poc, float(min(chosen)), float(max(chosen))


def main() -> None:
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    all_days = sorted(by_day)

    # RTH profile per day (09:30-16:00 ET), for POC history and the composite
    print("building daily volume-at-price profiles ...")
    profs, pocs = {}, {}
    for d in all_days:
        g = by_day[d]
        rth = g[(g.ts.dt.hour * 60 + g.ts.dt.minute >= 570)
                & (g.ts.dt.hour * 60 + g.ts.dt.minute <= 960)]
        if len(rth) < 60:
            continue
        p = day_profile(rth)
        profs[d] = p
        pocs[d] = poc_and_va(p)[0]

    rows = []
    for r in sub.itertuples():
        g = by_day.get(r.day)
        if g is None:
            continue
        start, end = london_window_et(r.day)
        w = g[(g.ts >= start) & (g.ts <= end)]
        if len(w) < 30:
            continue
        i = all_days.index(r.day)
        hist = [d for d in all_days[max(0, i - NAKED_LOOKBACK): i] if d in pocs]
        if len(hist) < 5:
            continue

        # ---- leg (a): naked POCs — never traded through since they formed
        naked = []
        for j, d in enumerate(hist):
            lvl = pocs[d]
            later = hist[j + 1:]
            touched = any(by_day[x].low.min() <= lvl <= by_day[x].high.max()
                          for x in later)
            if not touched:
                naked.append(lvl)

        # magnet = a naked POC beyond the Asian extreme, on either side
        dists = []
        for lvl in naked:
            if lvl > r.asia_hi:
                dists.append(lvl - r.asia_hi)
            elif lvl < r.asia_lo:
                dists.append(r.asia_lo - lvl)
        best = min(dists) if dists else np.inf

        # ---- leg (c): LVN in the rolling composite that London enters
        comp: dict[float, float] = defaultdict(float)
        for d in hist:
            for p, v in profs[d].items():
                comp[p] += v
        cp = np.array(sorted(comp))
        cv = np.array([comp[p] for p in cp])
        lo_w = np.floor(w.low.min() / BUCKET) * BUCKET
        hi_w = np.floor(w.high.max() / BUCKET) * BUCKET
        in_w = (cp >= lo_w) & (cp <= hi_w)
        lvn_hit = {}
        for pct in LVN_PCTL_LADDER:
            thresh = np.percentile(cv, pct)
            lvn_hit[pct] = bool((cv[in_w] <= thresh).any())

        rows.append({"day": r.day, "era": r.day[:4], "n_naked": len(naked),
                     "magnet_dist": best,
                     **{f"lvn_{p}": lvn_hit[p] for p in LVN_PCTL_LADDER}})

    d = pd.DataFrame(rows)
    print(f"\ndays evaluated: {len(d)} "
          f"({', '.join(f'{e}: {int((d.era == e).sum())}' for e in ('2025', '2026'))})")
    print(f"naked POCs carried per day: median {d.n_naked.median():.0f}, "
          f"max {d.n_naked.max():.0f}")

    print("\n" + "=" * 78)
    print("LEG (a) — a naked POC beyond the Asian extreme, within reach")
    print("=" * 78)
    print(f"{'reach':<40}{'2025':>6}{'2026':>6}  floor n>={FLOOR}")
    print("-" * 78)
    for reach in REACH_LADDER:
        m = d.magnet_dist <= reach
        n25 = int(m[d.era == "2025"].sum())
        n26 = int(m[d.era == "2026"].sum())
        print(f"{f'naked POC within {reach} pts of the Asian extreme':<40}"
              f"{n25:>6}{n26:>6}  {'OK' if min(n25, n26) >= FLOOR else 'UNTESTABLE'}")

    print("\n" + "=" * 78)
    print("LEG (c) — London enters a low-volume node of the rolling composite")
    print("=" * 78)
    print(f"{'LVN definition':<40}{'2025':>6}{'2026':>6}  floor n>={FLOOR}")
    print("-" * 78)
    for pct in LVN_PCTL_LADDER:
        m = d[f"lvn_{pct}"]
        n25 = int(m[d.era == "2025"].sum())
        n26 = int(m[d.era == "2026"].sum())
        print(f"{f'composite volume below p{pct}':<40}"
              f"{n25:>6}{n26:>6}  {'OK' if min(n25, n26) >= FLOOR else 'UNTESTABLE'}")

    print("\nTHIS IS NOT A VERDICT. No outcome measured, no trial recorded.")


if __name__ == "__main__":
    main()
