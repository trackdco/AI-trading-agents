#!/usr/bin/env python3
"""LDN-VWAP-01 — vwap-sigma-rotation leg 1, exactly as declared in
docs/PREREG-london-vwap-sigma-rotation.md (15:35:56Z).

Anchor: VWAP + realised sigma over 18:00 ET (D-1) -> the London open, frozen at the open.
Gate: skip days whose London open prints outside the Asia range (the candidate's drive-open
exclusion). Event: first +/-2 sigma touch inside 08:00-10:00 Europe/London, then a 1-min
CLOSE back inside the band BEFORE two consecutive closes beyond it. Two-consecutive-beyond
first = acceptance -> day EXCLUDED (the thesis says stand down), not counted as a loss.
Outcome: (close at window end - close at t) x fade direction, measured from t forward.

Fragility gate runs FIRST and is bar-independent.
SEALED-SPAN GUARD: 2023/24 dropped and asserted gone. No holdout look.

    python -m scripts.ldn_vwap01_census
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
SIGMA_MULT = 2.0
MIN_N = 30


def build() -> tuple[pd.DataFrame, dict]:
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    bars = pd.read_parquet(ROOT / "data/reference/nq_1m_master.parquet")
    bars = bars.assign(ts=pd.to_datetime(bars.ts_event, utc=True).dt.tz_convert(NY))
    bars["day"] = bars.ts.dt.strftime("%Y-%m-%d")
    by_day = {d: g.reset_index(drop=True) for d, g in bars.groupby("day", sort=False)}
    days = sorted(by_day)
    prev = {d: days[i - 1] for i, d in enumerate(days) if i}

    rows, tally = [], {"no_touch": 0, "acceptance": 0, "drive_open": 0, "ok": 0}
    for r in sub.itertuples():
        g, pg = by_day.get(r.day), by_day.get(prev.get(r.day, ""))
        if g is None or pg is None:
            continue
        start, end = london_window_et(r.day)
        on = pd.concat([pg[pg.ts >= pg.ts.dt.normalize() + pd.Timedelta(hours=18)],
                        g[g.ts < start]])
        w = g[(g.ts >= start) & (g.ts <= end)].reset_index(drop=True)
        if len(w) < 30 or len(on) < 60 or on.volume.sum() <= 0:
            continue

        vwap = float((on.close * on.volume).sum() / on.volume.sum())
        sigma = float(np.sqrt((((on.close - vwap) ** 2) * on.volume).sum()
                              / on.volume.sum()))
        if sigma <= 0:
            continue
        up, dn = vwap + SIGMA_MULT * sigma, vwap - SIGMA_MULT * sigma

        drive = bool(w.close.iloc[0] > r.asia_hi or w.close.iloc[0] < r.asia_lo)

        hit_up = w.index[w.high >= up]
        hit_dn = w.index[w.low <= dn]
        if not len(hit_up) and not len(hit_dn):
            tally["no_touch"] += 1
            continue
        i_up = hit_up[0] if len(hit_up) else len(w)
        i_dn = hit_dn[0] if len(hit_dn) else len(w)
        i, side = (int(i_up), +1) if i_up <= i_dn else (int(i_dn), -1)

        # forward scan: rejection close inside the band before two consecutive beyond
        t, run = None, 0
        for j in range(i, len(w)):
            c = w.close.iloc[j]
            beyond = (c > up) if side > 0 else (c < dn)
            if beyond:
                run += 1
                if run >= 2:
                    break
            else:                          # a close back inside the band
                t = j
                break
        if t is None:
            tally["acceptance"] += 1
            continue
        if drive:
            tally["drive_open"] += 1
        tally["ok"] += 1
        rows.append({"day": r.day, "era": r.day[:4], "gated": not drive,
                     "direction": -side,
                     "signed_ret": (w.close.iloc[-1] - w.close.iloc[t]) * (-side)})
    return pd.DataFrame(rows), tally


def stats(x: np.ndarray) -> tuple[float, float, float]:
    m, se = float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x)))
    return m, se, (1 - PHI.cdf(m / se)) if se > 0 else float("nan")


def main() -> None:
    d, tally = build()
    G = d[d.gated]                                     # the candidate's own specification
    print("LDN-VWAP-01 leg 1 — London session only (08:00-10:00 Europe/London)")
    print(f"day disposition: {tally}")
    print(f"  acceptance-excluded days: {tally['acceptance']} "
          f"({100 * tally['acceptance'] / max(1, tally['acceptance'] + tally['ok']):.0f}% "
          f"of touch days) — London accepting beyond 2 sigma this often is itself evidence")
    print(f"\ngated events (primary): {len(G)}  "
          f"{', '.join(f'{e}: {(G.era == e).sum()}' for e in ('2025', '2026'))}")
    print(f"ungated total: {len(d)}\n")

    print("=" * 84)
    print("FRAGILITY GATE (prereg §7) — before the primary is read")
    print("=" * 84)
    fired = []
    for era in ("2025", "2026"):
        s = G[G.era == era].signed_ret
        if len(s) < 12:
            print(f"  {era}: n={len(s)} too small for the ladder")
            continue
        full = s.mean()
        o = s.abs().sort_values().index
        parts = [f"full {full:+.2f}"]
        for k in (1, 3, 5, 10):
            t = G.loc[o[:-k]].pipe(lambda f, e=era: f[f.era == e].signed_ret.mean())
            parts.append(f"drop{k} {t:+.2f}")
            if k <= 3 and np.isfinite(t) and np.sign(t) != np.sign(full):
                fired.append(f"{era}@drop{k}")
        q1, q99 = s.quantile([.01, .99])
        parts.append(f"wins1/99 {s.clip(q1, q99).mean():+.2f}")
        print(f"  {era}: " + " | ".join(parts))
    print(f"\n  GATE {'FIRES — family dead regardless of below' if fired else 'CLEAR'}")

    print("\n" + "=" * 84)
    print("PRIMARY — gated, mean signed_ret (positive = reversion worked)")
    print("=" * 84)
    res = {}
    for era in ("2025", "2026"):
        x = G[G.era == era].signed_ret.to_numpy(float)
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
    print("\n" + "=" * 84)
    print(f"VERDICT: {verdict}")
    print("=" * 84)

    print("\nSECONDARY (declared): does the regime gate earn its place?")
    for era in ("2025", "2026"):
        for lab, sel in (("gated  ", G[G.era == era]),
                         ("ungated", d[d.era == era])):
            if len(sel) < 2:
                continue
            m, se, p = stats(sel.signed_ret.to_numpy(float))
            print(f"  {era} {lab}: mean {m:>+8.2f}  p1 {p:.3f}  n {len(sel)}")

    print("\nPOWER (mandatory)")
    for era, (m, se, p, n) in res.items():
        print(f"  {era}: n {n:>3}  se {se:.2f}  min detectable mean @80% = "
              f"{(PHI.inv_cdf(0.95) + PHI.inv_cdf(0.80)) * se:+.2f} pts")
    print(f"\nDistribution (gated): median {G.signed_ret.median():+.2f}, "
          f"sd {G.signed_ret.std():.1f}, share positive "
          f"{100 * (G.signed_ret > 0).mean():.0f}%")


if __name__ == "__main__":
    main()
