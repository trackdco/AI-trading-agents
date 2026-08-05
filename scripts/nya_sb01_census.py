#!/usr/bin/env python3
"""NYA-SB-01 census — exactly as declared in docs/PREREG-nya-silver-bullet.md (08:03:40Z).

Entry at the FVG fill, stop at the swept extreme, target 2R. One trade per macro window,
daily stop after 2 losses. Same-bar stop+target resolved AGAINST the trade.

NOT THE MODEL AS TAUGHT — order block, ES trigger and bias filter are omitted (prereg §1),
so a null cannot kill the candidate under §5.9.1.

    python -m scripts.nya_sb01_census
"""
from __future__ import annotations

import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.nya_sb01_feasibility import (  # noqa: E402
    MACROS, MSS_LOOKBACK, find_fvg, load_bars, session_extremes, swing_levels,
)

PHI = NormalDist()
BE_WR = 1.0 / 3.0        # break-even win rate at 1:2
MIN_N = 30


def build(offset_min: int = 0) -> pd.DataFrame:
    b = load_bars()
    by_day = {d: g.reset_index(drop=True) for d, g in b.groupby("day", sort=False)}
    days = sorted(by_day)
    rows = []
    for k, d in enumerate(days):
        g = by_day[d]
        prev = by_day[days[k - 1]] if k else g.iloc[0:0]
        losses = 0
        for name, m0, m1 in MACROS:
            if losses >= 2:
                break
            m0, m1 = m0 + offset_min, m1 + offset_min
            w = g[(g.mins >= m0) & (g.mins <= m1)].reset_index(drop=True)
            if len(w) < 20:
                continue
            hs, ls = swing_levels(g, m0)
            ext = session_extremes(g, prev)
            cands = ([(x, -1) for x in hs + [ext.get("asia_hi"), ext.get("lon_hi")] if x]
                     + [(x, +1) for x in ls + [ext.get("asia_lo"), ext.get("lon_lo")] if x])
            for lv, side in cands:
                hit = (w.high > lv) if side < 0 else (w.low < lv)
                if not hit.any():
                    continue
                s = int(hit.idxmax())
                seg = w.iloc[max(0, s - MSS_LOOKBACK):s + 1]
                post = w.iloc[s + 1:]
                if not len(seg) or not len(post):
                    continue
                ref = float(seg.low.min()) if side < 0 else float(seg.high.max())
                brk = (post.close < ref) if side < 0 else (post.close > ref)
                if not brk.any():
                    continue
                m = int(brk.idxmax())
                fv = find_fvg(w, m, side)
                if fv is None:
                    continue
                edge, far = fv
                fwd = w.iloc[m + 1:]
                fill = ((fwd.high >= edge) if side < 0 else (fwd.low <= edge))
                if not len(fwd) or not fill.any():
                    continue
                t = int(fill.idxmax())
                # PREREG AMENDMENT 2026-08-06 (see docs/PREREG-nya-silver-bullet.md §3a):
                # stop is the FVG's FAR edge — the structural invalidation of the
                # displacement — NOT the swept level. The swept level gave a median 58pt /
                # mean 93pt risk against his stated 27-53pt stops, so it contradicted source.
                entry, stop = edge, far
                risk = abs(entry - stop)
                if risk <= 0:
                    continue
                target = entry - 2 * risk if side < 0 else entry + 2 * risk
                # resolve bar by bar; stop assumed first on same-bar ambiguity
                out = None
                for _, bar in w.iloc[t + 1:].iterrows():
                    hit_stop = bar.high >= stop if side < 0 else bar.low <= stop
                    hit_tgt = bar.low <= target if side < 0 else bar.high >= target
                    if hit_stop:
                        out = -1.0; break
                    if hit_tgt:
                        out = 2.0; break
                if out is None:
                    last = float(w.close.iloc[-1])
                    out = float(((entry - last) if side < 0 else (last - entry)) / risk)
                rows.append({"day": d, "macro": name, "side": side, "risk_pts": risk,
                             "R": out, "win": out >= 2.0})
                if out <= -1.0:
                    losses += 1
                break
    return pd.DataFrame(rows)


def wr_test(x: np.ndarray) -> tuple[float, float, float]:
    n = len(x); wr = float(x.mean())
    se = np.sqrt(BE_WR * (1 - BE_WR) / n)
    return wr, se, float(1 - PHI.cdf((wr - BE_WR) / se)) if se > 0 else float("nan")


def main() -> None:
    d = build()
    d["era"] = np.where(d.day < "2026-01-01", "2025H2", "2026H1")
    print("NYA-SB-01 CENSUS — ash10hazard silver bullet, NQ, Jul-2025 -> Jul-2026")
    print("NOT THE MODEL AS TAUGHT (prereg §1): no order block, no ES trigger, no bias filter\n")
    print(f"trades: {len(d)}  {dict(d.era.value_counts())}")

    print("\n" + "=" * 78)
    print("FRAGILITY GATE (prereg §7) — before the primary is read")
    print("=" * 78)
    fired = []
    for era in ("2025H2", "2026H1"):
        s = d[d.era == era]
        full = s.win.mean()
        parts = [f"full {100*full:.1f}%"]
        for k in (1, 3, 5):
            o = s.R.sort_values().index
            trimmed = s.drop(list(o[:k]) + list(o[-k:]))
            parts.append(f"trim{k} {100*trimmed.win.mean():.1f}%")
        print(f"  {era}: " + " | ".join(parts))
        per = s.groupby("macro").win.agg(["mean", "size"])
        print(f"    by window: " + ", ".join(
            f"{i} {100*r['mean']:.0f}% (n={int(r['size'])})" for i, r in per.iterrows()))
        if (full > BE_WR) and (per["mean"] > BE_WR).sum() <= 1:
            fired.append(f"{era}: carried by one window")
    print(f"\n  GATE {'FIRES -> ' + '; '.join(fired) if fired else 'CLEAR'}")

    print("\n" + "=" * 78)
    print(f"PRIMARY — win rate at 2R vs the {100*BE_WR:.1f}% break-even bar")
    print("=" * 78)
    res = {}
    for era in ("2025H2", "2026H1"):
        s = d[d.era == era]
        wr, se, p = wr_test(s.win.to_numpy(float))
        lo, hi = wr - 1.96 * se, wr + 1.96 * se
        res[era] = (wr, se, p, len(s), lo, hi)
        print(f"  {era}: WR {100*wr:5.1f}%  n {len(s):>3}  p1 {p:.3f}  "
              f"95% CI [{100*lo:.1f}%, {100*hi:.1f}%]"
              f"{'' if len(s) >= MIN_N else '  BELOW n>=30'}")
        print(f"           mean {s.R.mean():+.3f}R   total {s.R.sum():+.1f}R")

    w25, _, p25, n25, _, _ = res["2025H2"]
    w26, _, p26, n26, lo26, hi26 = res["2026H1"]
    npass = p25 <= .05 and p26 <= .05 and min(n25, n26) >= MIN_N and not fired
    fail = (not (lo26 <= w25 <= hi26)) and hi26 <= BE_WR
    verdict = ("FAIL (fragility)" if fired else "PASS" if npass
               else "FAIL" if fail else "INCONCLUSIVE ON POWER")
    print("\n" + "=" * 78)
    print(f"VERDICT: {verdict}")
    print("=" * 78)
    print("Per prereg §1 + §5.9.1, a FAIL here CANNOT kill the candidate — three declared")
    print("components are omitted. It reads as 'mechanisable core insufficient alone'.")

    print("\nSECONDARY — does the macro gate earn its place? (same stack, +1h offset)")
    o = build(offset_min=60)
    o["era"] = np.where(o.day < "2026-01-01", "2025H2", "2026H1")
    for era in ("2025H2", "2026H1"):
        a, b_ = d[d.era == era], o[o.era == era]
        print(f"  {era}: macro {100*a.win.mean():5.1f}% (n={len(a)})   "
              f"offset {100*b_.win.mean():5.1f}% (n={len(b_)})   "
              f"diff {100*(a.win.mean()-b_.win.mean()):+5.1f}pp")

    print(f"\nPOWER: min detectable WR @80% = "
          + ", ".join(f"{e} {100*(BE_WR + (PHI.inv_cdf(.95)+PHI.inv_cdf(.80))*res[e][1]):.1f}%"
                      for e in ("2025H2", "2026H1")))
    print(f"\nR distribution: mean {d.R.mean():+.3f}  median {d.R.median():+.2f}  "
          f"total {d.R.sum():+.1f}R over {len(d)} trades")


if __name__ == "__main__":
    main()
