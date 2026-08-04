#!/usr/bin/env python3
"""LDN-INV-01 trial 2 — the continuous asymmetry test declared in
docs/PREREG-london-inventory-fade-continuous.md (commit 3627bc3).

Runs EXACTLY the authorised specification, nothing else:

    window_ret = b0 + b_neg*min(prior_rth_ret,0) + b_pos*max(prior_rth_ret,0)

OLS, HC1 robust standard errors. Hinge fixed at zero (declared, not searched).
Primary window 03:00->04:00, declared before running; the other three are descriptive
and cannot carry the verdict.

Three-way decision rule per the prereg, with D = b_neg - b_pos and D25 the 2025 estimate:
  PASS         b_neg<0 (p<=.05 one-sided) AND D<0 (p<=.05 one-sided), BOTH era directions
  FAIL         validate-era 95% CI on D EXCLUDES D25 and contains 0 or is positive
  INCONCLUSIVE otherwise — CI contains both 0 and D25; report MDE and days needed

SEALED-SPAN GUARD: 2023/24 dropped and asserted gone. No holdout look.

    python -m scripts.ldn_inv01_continuous
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ldn_inv01_power import WINDOWS, fit_only, window_returns

PHI = NormalDist()
PRIMARY = "03:00->04:00"


def hinged_ols(y: np.ndarray, x: np.ndarray) -> dict:
    """OLS of y on [1, min(x,0), max(x,0)] with HC1 robust covariance."""
    X = np.column_stack([np.ones_like(x), np.minimum(x, 0.0), np.maximum(x, 0.0)])
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    e = y - X @ beta
    V = (n / (n - k)) * XtX_inv @ (X.T @ (X * (e**2)[:, None])) @ XtX_inv
    se = np.sqrt(np.diag(V))
    c = np.array([0.0, 1.0, -1.0])          # D = b_neg - b_pos
    D = float(c @ beta)
    seD = float(math.sqrt(c @ V @ c))
    return {"n": n, "b_neg": float(beta[1]), "se_neg": float(se[1]),
            "b_pos": float(beta[2]), "se_pos": float(se[2]), "D": D, "se_D": seD}


def one_sided_p(est: float, se: float) -> float:
    """P(estimate this negative or more, under the null of zero)."""
    return PHI.cdf(est / se) if se > 0 else float("nan")


def main() -> None:
    sub = fit_only(pd.read_parquet(ROOT / "output/london_day_features.parquet"))
    d = sub.merge(window_returns(), on="day", how="inner")
    d["era"] = pd.to_datetime(d.day).dt.year.astype(str)
    print(f"days after sealed-span guard: {len(d)} "
          f"(2025: {(d.era == '2025').sum()}, 2026: {(d.era == '2026').sum()})")
    print(f"PRIMARY WINDOW (declared pre-run): {PRIMARY}\n")

    fits: dict = {}
    for win in WINDOWS:
        for era in ("2025", "2026"):
            e = d[(d.era == era)].dropna(subset=[win, "prior_rth_ret"])
            fits[(era, win)] = hinged_ols(e[win].to_numpy(float),
                                          e.prior_rth_ret.to_numpy(float))

    print("=" * 92)
    print(f"PRIMARY: {PRIMARY}   (b_neg<0 = bad US days bought back; b_pos~0 = asymmetry)")
    print("=" * 92)
    print(f"{'era':>6} {'n':>5} {'b_neg':>9} {'(se)':>8} {'p1':>7} "
          f"{'b_pos':>9} {'(se)':>8} {'D=neg-pos':>11} {'(se)':>8} {'p1(D)':>7}")
    for era in ("2025", "2026"):
        f = fits[(era, PRIMARY)]
        print(f"{era:>6} {f['n']:>5} {f['b_neg']:>+9.3f} {f['se_neg']:>8.3f} "
              f"{one_sided_p(f['b_neg'], f['se_neg']):>7.3f} "
              f"{f['b_pos']:>+9.3f} {f['se_pos']:>8.3f} "
              f"{f['D']:>+11.3f} {f['se_D']:>8.3f} "
              f"{one_sided_p(f['D'], f['se_D']):>7.3f}")

    f25, f26 = fits[("2025", PRIMARY)], fits[("2026", PRIMARY)]
    D25 = f25["D"]
    lo, hi = f26["D"] - 1.96 * f26["se_D"], f26["D"] + 1.96 * f26["se_D"]
    print(f"\n  2025 asymmetry D25            {D25:+.3f}")
    print(f"  2026 asymmetry D26            {f26['D']:+.3f}   95% CI [{lo:+.3f}, {hi:+.3f}]")
    print(f"  CI excludes D25?              {'YES' if not (lo <= D25 <= hi) else 'no'}")
    print(f"  CI contains 0?                {'YES' if lo <= 0 <= hi else 'no'}")

    # ---- the three-way rule, applied exactly as declared
    pass_25 = (one_sided_p(f25["b_neg"], f25["se_neg"]) <= 0.05
               and one_sided_p(f25["D"], f25["se_D"]) <= 0.05)
    pass_26 = (one_sided_p(f26["b_neg"], f26["se_neg"]) <= 0.05
               and one_sided_p(f26["D"], f26["se_D"]) <= 0.05)
    excl = not (lo <= D25 <= hi)
    fail = excl and (lo <= 0 <= hi or f26["D"] > 0)

    # The prereg's fragility clause is an OVERRIDE: "if the fit is driven by <=3 days
    # (drop-top-3 per §2.5), it is dead REGARDLESS of the above." Evaluate it here so the
    # verdict reflects the declared rule rather than the three-way test alone.
    frag = {}
    for era in ("2025", "2026"):
        e = d[d.era == era].dropna(subset=[PRIMARY, "prior_rth_ret"])
        keep = e.loc[e[PRIMARY].abs().sort_values().index].iloc[:-3]
        g = hinged_ols(keep[PRIMARY].to_numpy(float), keep.prior_rth_ret.to_numpy(float))
        frag[era] = (fits[(era, PRIMARY)]["D"], g["D"],
                     np.sign(g["D"]) != np.sign(fits[(era, PRIMARY)]["D"]))
    fragile = any(v[2] for v in frag.values())

    verdict = ("FAIL (fragility override)" if fragile
               else "PASS" if (pass_25 and pass_26)
               else "FAIL" if fail else "INCONCLUSIVE ON POWER")

    print("\n" + "=" * 92)
    print(f"VERDICT (primary window, declared rule): {verdict}")
    print("=" * 92)
    print(f"  discover-2025 leg passes?     {pass_25}")
    print(f"  validate-2026 leg passes?     {pass_26}")
    print(f"  three-way test alone would be "
          f"{'PASS' if (pass_25 and pass_26) else 'FAIL' if fail else 'INCONCLUSIVE ON POWER'}")
    print(f"  FRAGILITY OVERRIDE fired?     {fragile}  "
          f"(sign flips on drop-top-3: "
          f"{', '.join(e for e, v in frag.items() if v[2]) or 'none'})")

    # ---- inverse era pass (§2.1) is the same two fits read the other way
    print(f"\n  inverse pass (discover-2026 -> validate-2025): "
          f"2026 leg {'passes' if pass_26 else 'FAILS'}, so the inverse direction "
          f"{'proceeds' if pass_26 else 'cannot start'}")

    # ---- mandatory power reporting
    mde = (PHI.inv_cdf(0.95) + PHI.inv_cdf(0.80)) * f26["se_D"]
    print("\n" + "=" * 92)
    print("POWER (mandatory per prereg)")
    print("=" * 92)
    for era in ("2025", "2026"):
        f = fits[(era, PRIMARY)]
        pw = 1 - PHI.cdf(PHI.inv_cdf(0.95) - abs(D25) / f["se_D"])
        print(f"  {era}: n={f['n']:>4}  se(D)={f['se_D']:.3f}  "
              f"power to detect D25 = {pw * 100:>3.0f}%")
    print(f"  2026 minimum detectable |D| @80% power: {mde:.3f} "
          f"({mde / abs(D25):.1f}x the 2025 estimate)")
    need = f26["n"] * (mde / abs(D25)) ** 2
    print(f"  2026 days needed to detect D25 @80%:   ~{need:,.0f} (have {f26['n']})")

    # ---- drop-top-3 fragility, primary window, both eras
    print("\n" + "=" * 92)
    print("FRAGILITY — drop-top-3 (per prereg / §2.5)")
    print("=" * 92)
    for era in ("2025", "2026"):
        e = d[d.era == era].dropna(subset=[PRIMARY, "prior_rth_ret"])
        keep = e.assign(_a=e[PRIMARY].abs()).sort_values("_a").iloc[:-3]
        g = hinged_ols(keep[PRIMARY].to_numpy(float), keep.prior_rth_ret.to_numpy(float))
        f = fits[(era, PRIMARY)]
        print(f"  {era}: D {f['D']:+.3f} -> {g['D']:+.3f} after dropping 3 largest-|ret| "
              f"days  ({'SIGN HOLDS' if np.sign(g['D']) == np.sign(f['D']) else 'SIGN FLIPS'})")

    # ---- companions, explicitly not verdict-eligible
    print("\n" + "=" * 92)
    print("DESCRIPTIVE COMPANIONS — not verdict-eligible (prereg §Specification)")
    print("=" * 92)
    for win in WINDOWS:
        if win == PRIMARY:
            continue
        a, b = fits[("2025", win)], fits[("2026", win)]
        print(f"  {win:>14}  2025 D {a['D']:>+8.3f} (p1 {one_sided_p(a['D'], a['se_D']):.3f})"
              f"   2026 D {b['D']:>+8.3f} (p1 {one_sided_p(b['D'], b['se_D']):.3f})")


if __name__ == "__main__":
    main()
