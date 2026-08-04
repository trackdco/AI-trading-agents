#!/usr/bin/env python3
"""LDN-VT-01 — value-traverse leg (a), the naked-POC magnet, exactly as declared in
docs/PREREG-london-value-traverse.md (16:42:52Z).

Magnet: the nearest naked POC beyond the Asian extreme within REACH points. Naked = a POC
from one of the 20 sessions STRICTLY BEFORE the event day, never traded through by any
session between its formation and the event day. The event day never contributes.

Event: the first 1-min CLOSE inside 08:00-10:00 Europe/London printing beyond the Asian
extreme on the magnet side. Direction: toward the magnet. Outcome: (close at window end -
close at t) x direction, measured strictly from t forward.

Fragility gate runs FIRST and includes the reach ladder.
SEALED-SPAN GUARD: 2023/24 dropped via fit_only(). No holdout look.

    python -m scripts.ldn_vt01_census
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import fit_only
from scripts.ldn_swp01_london_only import london_window_et
from scripts.ldn_vt_profile_feasibility import day_profile, poc_and_va

NY = "America/New_York"
PHI = NormalDist()
REACH = 100.0                  # declared primary
REACH_LADDER = (50.0, 100.0, 200.0)
NAKED_LOOKBACK = 20
MIN_N = 30


def build(reach: float = REACH) -> pd.DataFrame:
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    all_days = sorted(by_day)

    pocs, hi_lo = {}, {}
    for d in all_days:
        g = by_day[d]
        m = g.ts.dt.hour * 60 + g.ts.dt.minute
        rth = g[(m >= 570) & (m <= 960)]
        hi_lo[d] = (float(g.high.max()), float(g.low.min()))
        if len(rth) >= 60:
            pocs[d] = poc_and_va(day_profile(rth))[0]

    rows = []
    for r in sub.itertuples():
        g = by_day.get(r.day)
        if g is None:
            continue
        start, end = london_window_et(r.day)
        w = g[(g.ts >= start) & (g.ts <= end)].reset_index(drop=True)
        if len(w) < 30:
            continue
        i = all_days.index(r.day)
        hist = [d for d in all_days[max(0, i - NAKED_LOOKBACK): i] if d in pocs]
        if len(hist) < 5:
            continue

        # naked POCs — never traded through by any session strictly before the event day
        naked = []
        for j, d in enumerate(hist):
            lvl = pocs[d]
            if not any(hi_lo[x][1] <= lvl <= hi_lo[x][0] for x in hist[j + 1:]):
                naked.append(lvl)

        cands = [(lvl - r.asia_hi, lvl, +1) for lvl in naked if lvl > r.asia_hi]
        cands += [(r.asia_lo - lvl, lvl, -1) for lvl in naked if lvl < r.asia_lo]
        cands = [c for c in cands if c[0] <= reach]
        if not cands:
            continue
        dist, magnet, side = min(cands)          # nearest magnet

        # entry: first close beyond the Asian extreme on the magnet side
        brk = w.index[(w.close > r.asia_hi) if side > 0 else (w.close < r.asia_lo)]
        if not len(brk):
            continue
        t = int(brk[0])
        fwd = w.iloc[t + 1:]
        if not len(fwd):
            continue

        touched = bool((fwd.high.max() >= magnet) if side > 0
                       else (fwd.low.min() <= magnet))
        # Distance-matched placebo, per prereg §6. The match must be on distance FROM THE
        # ENTRY PRICE — anchoring it to the opposite Asian extreme leaves the placebo far
        # further from price than the magnet, which measures "near things get touched more
        # than far things", i.e. exactly the confound the placebo exists to remove.
        entry_px = float(w.close.iloc[t])
        d_entry = abs(magnet - entry_px)
        placebo = entry_px - d_entry if side > 0 else entry_px + d_entry
        pl_touch = bool((fwd.low.min() <= placebo) if side > 0
                        else (fwd.high.max() >= placebo))

        rows.append({"day": r.day, "era": r.day[:4], "direction": side, "dist": dist,
                     "d_entry": d_entry,
                     "signed_ret": (w.close.iloc[-1] - w.close.iloc[t]) * side,
                     "touched": touched, "placebo_touched": pl_touch})
    return pd.DataFrame(rows)


def stats(x: np.ndarray) -> tuple[float, float, float]:
    m, se = float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x)))
    return m, se, (1 - PHI.cdf(m / se)) if se > 0 else float("nan")


def main() -> None:
    d = build()
    print("LDN-VT-01 leg (a) — naked-POC magnet, London 08:00-10:00 Europe/London")
    print(f"events (reach {REACH:.0f}pt): {len(d)}  "
          f"{', '.join(f'{e}: {int((d.era == e).sum())}' for e in ('2025', '2026'))}")
    print(f"magnet distance: median {d.dist.median():.1f} pts\n")

    print("=" * 86)
    print("FRAGILITY GATE (prereg §7) — before the primary is read")
    print("=" * 86)
    fired = []
    for era in ("2025", "2026"):
        s = d[d.era == era].signed_ret
        full = s.mean()
        o = s.abs().sort_values().index
        parts = [f"full {full:+.2f}"]
        for k in (1, 3, 5, 10):
            t = d.loc[o[:-k]].pipe(lambda f, e=era: f[f.era == e].signed_ret.mean())
            parts.append(f"drop{k} {t:+.2f}")
            if k <= 3 and np.isfinite(t) and np.sign(t) != np.sign(full):
                fired.append(f"{era}@drop{k}")
        q1, q99 = s.quantile([.01, .99])
        parts.append(f"wins1/99 {s.clip(q1, q99).mean():+.2f}")
        print(f"  {era} trim : " + " | ".join(parts))

    print("\n  reach ladder (declared fragility, not alternative primaries):")
    ladder_signs: dict[str, list[float]] = {"2025": [], "2026": []}
    for reach in REACH_LADDER:
        dr = build(reach)
        cells = []
        for era in ("2025", "2026"):
            s = dr[dr.era == era].signed_ret
            cells.append(f"{era} n={len(s):>3} mean {s.mean():+7.2f}")
            ladder_signs[era].append(float(np.sign(s.mean())))
        print(f"    reach {reach:>5.0f}pt : " + " | ".join(cells))
    for era, signs in ladder_signs.items():
        if len({s for s in signs if s != 0}) > 1:
            fired.append(f"{era}@reach-ladder")
    print(f"\n  GATE {'FIRES -> ' + ', '.join(fired) if fired else 'CLEAR'}")

    print("\n" + "=" * 86)
    print("PRIMARY — mean signed_ret (positive = price continued toward the magnet)")
    print("=" * 86)
    res = {}
    for era in ("2025", "2026"):
        x = d[d.era == era].signed_ret.to_numpy(float)
        m, se, p = stats(x)
        res[era] = (m, se, p, len(x))
        print(f"  {era}: mean {m:>+8.2f} pts  se {se:>6.2f}  p1 {p:.3f}  n {len(x)}"
              f"{'' if len(x) >= MIN_N else '  BELOW n>=30'}")

    m25, _, p25, n25 = res["2025"]
    m26, se26, p26, n26 = res["2026"]
    lo, hi = m26 - 1.96 * se26, m26 + 1.96 * se26
    print(f"\n  2026 95% CI [{lo:+.2f}, {hi:+.2f}]  contains 0: "
          f"{'YES' if lo <= 0 <= hi else 'no'}  excludes 2025 est ({m25:+.2f}): "
          f"{'YES' if not (lo <= m25 <= hi) else 'no'}")

    npass = (p25 <= 0.05 and p26 <= 0.05 and m25 > 0 and m26 > 0
             and min(n25, n26) >= MIN_N)
    fail = (not (lo <= m25 <= hi)) and (lo <= 0 <= hi or m26 < 0)
    verdict = ("FAIL (fragility)" if fired else "PASS" if npass
               else "FAIL" if fail else "INCONCLUSIVE ON POWER")
    print("\n" + "=" * 86)
    print(f"VERDICT: {verdict}")
    print("=" * 86)

    print("\nSECONDARY (declared) — do naked POCs actually attract?")
    print("  placebo = same distance FROM THE ENTRY PRICE, opposite direction")
    for era in ("2025", "2026"):
        s = d[d.era == era]
        n = len(s)
        mt, pt = s.touched.mean(), s.placebo_touched.mean()
        # paired difference: same day, same distance, opposite direction
        diff = s.touched.astype(float) - s.placebo_touched.astype(float)
        se = float(diff.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
        p = (1 - PHI.cdf(diff.mean() / se)) if se and se > 0 else float("nan")
        print(f"  {era}: magnet {100 * mt:>5.1f}%  placebo {100 * pt:>5.1f}%  "
              f"diff {100 * diff.mean():>+6.1f}pp  se {100 * se:.1f}pp  p1 {p:.3f}  "
              f"n {n}  (median distance from entry {s.d_entry.median():.0f} pts)")

    print("\nPOWER (mandatory)")
    for era, (m, se, p, n) in res.items():
        print(f"  {era}: n {n:>3}  se {se:.2f}  min detectable mean @80% = "
              f"{(PHI.inv_cdf(0.95) + PHI.inv_cdf(0.80)) * se:+.2f} pts")
    print(f"\nDistribution: median {d.signed_ret.median():+.2f}, "
          f"sd {d.signed_ret.std():.1f}, "
          f"share positive {100 * (d.signed_ret > 0).mean():.0f}%")


if __name__ == "__main__":
    main()
