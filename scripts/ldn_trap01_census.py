#!/usr/bin/env python3
"""LDN-TRAP-01 — level-trap-fade census, exactly as declared in
docs/PREREG-london-level-trap-fade.md (15:21:38Z).

Event: inside 08:00-10:00 Europe/London (converted per day), price trades >=4 ticks beyond
a watched level frozen at the open (ONH/ONL/PDH/PDL), then a 1-min CLOSE prints back
through it within <=15 minutes. The event completes at that reclaim minute t.

Outcome: (close at window end - close at t) x direction, direction = the fade (opposite the
break). Positive means the fade worked. Measured strictly from t forward — nothing defining
the event is drawn from the interval being measured (prereg §3 causality audit).

Fragility gate runs FIRST and is bar-independent.

SEALED-SPAN GUARD: 2023/24 dropped and asserted gone. No holdout look.

    python -m scripts.ldn_trap01_census
"""
from __future__ import annotations

import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import fit_only
from scripts.ldn_swp01_london_only import london_window_et

NY = "America/New_York"
PHI = NormalDist()
BREAK_TICKS, TICK = 4, 0.25          # >= 4 ticks = 1.00 NQ point, declared
RECLAIM_MIN = 15                     # declared
MIN_N = 30


def build() -> pd.DataFrame:
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    days = sorted(by_day)
    prev = {d: days[i - 1] for i, d in enumerate(days) if i}

    rows = []
    for r in sub.itertuples():
        g, pg = by_day.get(r.day), by_day.get(prev.get(r.day, ""))
        if g is None or pg is None:
            continue
        start, end = london_window_et(r.day)
        # ONH/ONL: 18:00 ET (D-1) -> the actual London open, frozen there
        on = pd.concat([pg[pg.ts >= pg.ts.dt.normalize() + pd.Timedelta(hours=18)],
                        g[g.ts < start]])
        w = g[(g.ts >= start) & (g.ts <= end)].reset_index(drop=True)
        if len(w) < 30 or not len(on):
            continue
        levels = [("ONH", float(on.high.max()), +1), ("ONL", float(on.low.min()), -1),
                  ("PDH", r.prior_rth_hi, +1), ("PDL", r.prior_rth_lo, -1)]

        best = None                      # first qualifying event of the day
        for name, lvl, side in levels:
            if lvl is None or pd.isna(lvl):
                continue
            buf = BREAK_TICKS * TICK
            brk = w.index[(w.high > lvl + buf) if side > 0 else (w.low < lvl - buf)]
            if not len(brk):
                continue
            b = int(brk[0])
            seg = w.iloc[b: b + RECLAIM_MIN + 1]
            back = seg.index[(seg.close < lvl) if side > 0 else (seg.close > lvl)]
            if not len(back):
                continue
            t = int(back[0])
            # revisit count: how many separate breaks of THIS level before t
            touches = int(((w.high.iloc[:t] > lvl + buf) if side > 0
                           else (w.low.iloc[:t] < lvl - buf)).sum())
            if best is None or t < best["t"]:
                best = {"day": r.day, "era": r.day[:4], "level": name, "t": t,
                        "direction": -side,
                        "signed_ret": (w.close.iloc[-1] - w.close.iloc[t]) * (-side),
                        "first_revisit": touches <= 1}
        if best:
            rows.append(best)
    return pd.DataFrame(rows)


def one_sided_p(x: np.ndarray) -> tuple[float, float, float]:
    m, se = float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x)))
    return m, se, (1 - PHI.cdf(m / se)) if se > 0 else float("nan")


def main() -> None:
    d = build()
    print("LDN-TRAP-01 — level-trap-fade, London session only (08:00-10:00 Europe/London)")
    print(f"events (first per day): {len(d)}  "
          f"{', '.join(f'{e}: {(d.era == e).sum()}' for e in ('2025', '2026'))}")
    print(f"by level: {dict(d.level.value_counts())}\n")

    # ---------------- FRAGILITY GATE FIRST ----------------
    print("=" * 84)
    print("FRAGILITY GATE (prereg §6) — before the primary is read")
    print("=" * 84)
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
        print(f"  {era}: " + " | ".join(parts))
    print(f"\n  GATE {'FIRES — family dead regardless of below' if fired else 'CLEAR'}")

    # ---------------- PRIMARY ----------------
    print("\n" + "=" * 84)
    print("PRIMARY — mean signed_ret (positive = the fade worked)")
    print("=" * 84)
    res = {}
    for era in ("2025", "2026"):
        x = d[d.era == era].signed_ret.to_numpy(float)
        m, se, p = one_sided_p(x)
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
    print("\n" + "=" * 84)
    print(f"VERDICT: {verdict}")
    print("=" * 84)

    # ---------------- SECONDARY + COMPANIONS ----------------
    print("\nSECONDARY (declared): first revisit vs second-or-later")
    for era in ("2025", "2026"):
        e = d[d.era == era]
        for lab, sel in (("first", e[e.first_revisit]), ("later", e[~e.first_revisit])):
            if len(sel) < 2:
                print(f"  {era} {lab:>5}: n={len(sel)} too small")
                continue
            m, se, p = one_sided_p(sel.signed_ret.to_numpy(float))
            print(f"  {era} {lab:>5}: mean {m:>+8.2f}  p1 {p:.3f}  n {len(sel)}")

    print("\nPER-LEVEL (descriptive companions, not verdict-eligible)")
    for lv in ("ONH", "ONL", "PDH", "PDL"):
        s = d[d.level == lv]
        if len(s) < 2:
            continue
        print(f"  {lv}: n {len(s):>3}  mean {s.signed_ret.mean():>+8.2f}")

    print("\nPOWER (mandatory)")
    for era, (m, se, p, n) in res.items():
        mde = (PHI.inv_cdf(0.95) + PHI.inv_cdf(0.80)) * se
        print(f"  {era}: n {n:>3}  se {se:.2f}  min detectable mean @80% = {mde:+.2f} pts")

    print(f"\nDistribution: median {d.signed_ret.median():+.2f}, "
          f"sd {d.signed_ret.std():.1f}, "
          f"share positive {100 * (d.signed_ret > 0).mean():.0f}%")


if __name__ == "__main__":
    main()
