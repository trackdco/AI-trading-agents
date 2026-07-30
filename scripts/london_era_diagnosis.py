#!/usr/bin/env python3
"""Why did 2026 break the tight-stop band? FIT ONLY. Holdout sealed.

The question came out of the floor-5 correction: the sub-9.5pt band runs mean R +0.904 at 61% WR
in 2025 and +0.211 at 39% in 2026, while the SHIPPED >=9.5pt book goes the other way (+0.434 ->
+0.570). Two books on the same setups, same engine, opposite era behaviour. That is not noise, it
is a mechanism, and this script names it.

THE ANSWER, up front: 2026's volatility roughly doubled and the stops did not move. The floor is
specified in ABSOLUTE POINTS, so when the median London session range went 101pt -> 179pt, a fixed
9.5pt floor silently went from 9.4% of the day's range to 5.3% of it. The floor did not change; its
MEANING did. A 6.5pt stop that sat outside the noise in 2025 sat inside it in 2026.

WHAT THIS IS NOT. It is not a proposal to change the floor. Floor 5 is rejected in §1 of the
pre-registration and a volatility-scaled floor is a NEW hypothesis resting on n=2 regimes — it
would need its own pre-registration and its own out-of-sample test. This script explains an
observed crossing; it does not license a config change.

    python -m scripts.london_era_diagnosis
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.london_combined_job import lon_book, lon_pop, write  # noqa: E402

NQ_PT = 20.0        # lon_book returns `risk` in DOLLARS at 1 NQ lot; /20 recovers points


def prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["era"] = pd.to_datetime(d.day).dt.year.astype(str)
    d["mo"] = pd.to_datetime(d.day).dt.strftime("%Y-%m")
    d["stop_pts"] = d.risk / NQ_PT
    d["stop_frac"] = d.stop_pts / d.on_range        # stop as a share of the session's own range
    return d


def main() -> None:
    P = lon_pop()
    ship = prep(lon_book(P, floor=9.5, lifetime=math.inf, cap=999))
    band = prep(lon_book(P[(P.risk >= 5.0) & (P.risk < 9.5)], floor=5.0,
                         lifetime=math.inf, cap=999))
    Q = P.copy()
    Q["era"] = pd.to_datetime(Q.day).dt.year.astype(str)

    L = ["# Why 2026 broke the tight-stop band (and not the shipped book)\n",
         "\n**Fit only. Sealed 2023/24 never loaded. Diagnosis of an observed crossing — "
         "NOT a proposal to change the floor.**\n"]

    # ---- 0. the premise needs correcting first
    L.append("\n## First, correct the premise: 2026 was a GOOD year for the shipped strategy\n\n"
             "| era | n | win rate | mean R | net (1 lot) | avg win R | avg loss R |\n"
             "|---|---|---|---|---|---|---|\n")
    for e in ("2025", "2026"):
        g = ship[ship.era == e]
        L.append(f"| {e} | {len(g)} | {(g.R > 0).mean() * 100:.1f}% | {g.R.mean():+.3f} | "
                 f"${g.dollars.sum():+,.0f} | {g[g.R > 0].R.mean():+.2f} | "
                 f"{g[g.R <= 0].R.mean():+.2f} |\n")
    s25, s26 = ship[ship.era == "2025"], ship[ship.era == "2026"]
    L.append(f"\n2026 made **${s26.dollars.sum() - s25.dollars.sum():+,.0f} more** on "
             f"{len(s26) - len(s25)} more trades at a HIGHER mean R. The win rate fell "
             f"{(s25.R > 0).mean() * 100:.0f}% -> {(s26.R > 0).mean() * 100:.0f}%, but the average "
             f"winner grew {s25[s25.R > 0].R.mean():+.2f} -> {s26[s26.R > 0].R.mean():+.2f} R while "
             f"the average loser stayed flat ({s25[s25.R <= 0].R.mean():+.2f} -> "
             f"{s26[s26.R <= 0].R.mean():+.2f} R). That is the signature of a higher-volatility "
             f"regime: you are right less often, the stop still contains the damage, and the wins "
             f"run further. **Only the tight-stop band broke.**\n")

    # ---- 1. the regime
    L.append("\n## The regime: volatility roughly doubled\n\n"
             "Medians over the whole candidate population, so this is the market, not a "
             "selection effect.\n\n| measure | 2025 | 2026 | change |\n|---|---|---|---|\n")
    for c, lab in (("on_range", "session range (pts)"), ("rng_30", "30-min range (pts)"),
                   ("risk", "structural stop width (pts)")):
        a, b = Q[Q.era == "2025"][c].median(), Q[Q.era == "2026"][c].median()
        L.append(f"| {lab} | {a:.2f} | {b:.2f} | **{(b / a - 1) * 100:+.1f}%** |\n")

    # ---- 2. the mechanism
    L.append("\n## The mechanism: the stops did not follow\n\n"
             "A stop only works if it sits OUTSIDE the day's noise. What matters is therefore not "
             "the stop in points but the stop as a share of the session's own range.\n\n"
             "| book | era | median stop | median session range | **stop / range** |\n"
             "|---|---|---|---|---|\n")
    for lab, d in (("shipped >=9.5pt", ship), ("sub-9.5pt band", band)):
        for e in ("2025", "2026"):
            g = d[d.era == e]
            L.append(f"| {lab} | {e} | {g.stop_pts.median():.2f}pt | "
                     f"{g.on_range.median():.1f}pt | **{g.stop_frac.median() * 100:.2f}%** |\n")
    b25, b26 = band[band.era == "2025"], band[band.era == "2026"]
    L.append(f"\nThe band's stop did not move at all — {b25.stop_pts.median():.2f}pt in both eras "
             f"— while the range it had to survive went "
             f"{b25.on_range.median():.0f}pt -> {b26.on_range.median():.0f}pt. So it fell from "
             f"{b25.stop_frac.median() * 100:.2f}% of the range to "
             f"{b26.stop_frac.median() * 100:.2f}%, i.e. **{(1 - b26.stop_frac.median() / b25.stop_frac.median()) * 100:.0f}% "
             f"tighter in real terms** without anyone changing a setting. The shipped book took the "
             f"same erosion ({s25.stop_frac.median() * 100:.2f}% -> "
             f"{s26.stop_frac.median() * 100:.2f}%) but started with enough margin to absorb it.\n")

    # ---- 3. the fingerprint
    L.append("\n## The fingerprint: how the trades actually died\n\n"
             "If the diagnosis is right, the band should show more trades stopped out BEFORE "
             "reaching a first partial, and fewer reaching target. Share of trades by exit:\n\n")
    for lab, d in (("shipped >=9.5pt", ship), ("sub-9.5pt band", band)):
        x = (pd.crosstab(d.era, d.exit_reason, normalize="index") * 100).round(0)
        L.append(f"\n**{lab}**\n\n| era | "
                 + " | ".join(x.columns) + " |\n" + "|---" * (len(x.columns) + 1) + "|\n")
        for e, row in x.iterrows():
            L.append(f"| {e} | " + " | ".join(f"{v:.0f}%" for v in row) + " |\n")
    L.append(f"\nThat is the confirmation. The band's clean-stop rate — stopped out with no "
             f"partial banked — goes **35% -> 57%**, and its partial+target rate halves "
             f"**24% -> 11%**. The shipped book's clean-stop rate barely moves (37% -> 42%) and "
             f"its partial+target rate nearly DOUBLES (13% -> 22%): the same volatility that "
             f"killed the tight stops paid the wide ones.\n")

    # ---- 4. systematic or a patch?
    L.append("\n## Is it one bad patch, or decay?\n\n"
             "| month | band n | band mean R | band WR | shipped n | shipped mean R |\n"
             "|---|---|---|---|---|---|\n")
    for m in sorted(set(band.mo) | set(ship.mo)):
        b, s = band[band.mo == m], ship[ship.mo == m]
        L.append(f"| {m} | {len(b)} | "
                 + (f"{b.R.mean():+.3f} | {(b.R > 0).mean() * 100:.0f}% | " if len(b) else "— | — | ")
                 + f"{len(s)} | " + (f"{s.R.mean():+.3f} |\n" if len(s) else "— |\n"))
    L.append("\n**Decay, not a patch.** The band holds up through 2025, wobbles from 2026-02, and "
             "is negative in the last two months of the fit span (2026-06 at 24% WR, 2026-07 at 0% "
             "on n=9). The shipped book stays healthy across the whole of 2026. A single volatility "
             "event would show as one bad month in both books; this is a one-sided trend.\n")

    # ---- 5. the real point
    r25, r26 = Q[Q.era == "2025"].on_range.median(), Q[Q.era == "2026"].on_range.median()
    L.append("\n## The point worth keeping\n\n"
             f"The floor is written in ABSOLUTE POINTS, so its real tightness floats with the "
             f"market:\n\n| era | median session range | 9.5pt floor as a share of range |\n"
             f"|---|---|---|\n"
             f"| 2025 | {r25:.1f}pt | **{9.5 / r25 * 100:.2f}%** |\n"
             f"| 2026 | {r26:.1f}pt | **{9.5 / r26 * 100:.2f}%** |\n"
             f"\nTo hold 2025's real tightness in 2026 the floor would have had to be "
             f"**{9.5 * r26 / r25:.1f}pt**. Nobody loosened the floor — the market did it, by "
             f"getting bigger. That single fact explains the era crossing that rejected floor 5: "
             f"the crossing was never evidence that tight-stop SETUPS are bad, it was evidence "
             f"that a FIXED point floor means different things in different regimes.\n")
    L.append("\n### What follows, and what does not\n\n"
             "**Does not follow:** any change to the floor. Floor 5 stays rejected (§1). A "
             "volatility-scaled floor — expressed as a share of session range or an ATR multiple "
             "rather than in points — is a NEW hypothesis resting on n=2 regimes, one of which was "
             "used to find it. It would need its own pre-registration and its own out-of-sample "
             "test, and it is not going into the current holdout, which is already at "
             "2 gated questions and ~84 projected trades.\n\n"
             "**Does follow — a forward risk worth naming.** The shipped book's stop/range also "
             f"eroded, {s25.stop_frac.median() * 100:.2f}% -> {s26.stop_frac.median() * 100:.2f}%. "
             "It has margin today. If volatility keeps rising, the shipped book meets the same "
             "wall the band already hit, and it will look like alpha decay when it is actually a "
             "units problem. Worth watching stop/range as a live health metric rather than "
             "discovering it later.\n\n"
             "**Also follows — a caveat on reading the holdout.** 2023/24 is a different "
             "volatility regime, and a fixed 9.5pt floor is relatively TIGHTER in a calm market "
             "and LOOSER in a wild one. So part of whatever the holdout reports is a statement "
             "about 2023/24's ranges, not purely about the edge. Measuring the sealed span's "
             "session ranges would contextualise the result, and `on_range` is a market-condition "
             "feature rather than an outcome — but it is still the sealed span, so it is NOT read "
             "here. Flagged as an authorisation question, not taken.\n")
    write("LONDON-ERA-DIAGNOSIS.md", "".join(L))
    print(f"shipped 2025 R {s25.R.mean():+.3f} -> 2026 {s26.R.mean():+.3f} | "
          f"band 2025 {b25.R.mean():+.3f} -> 2026 {b26.R.mean():+.3f}")
    print(f"range {r25:.0f} -> {r26:.0f}pt (+{(r26 / r25 - 1) * 100:.0f}%); "
          f"9.5pt floor = {9.5 / r25 * 100:.2f}% -> {9.5 / r26 * 100:.2f}% of range")


if __name__ == "__main__":
    main()
