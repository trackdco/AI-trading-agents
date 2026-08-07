#!/usr/bin/env python3
"""Session-by-session FVT breakdown on the CORRECTED model, 2023-2026.

Everything here is re-run after the per-day/full-dataset indexing bug documented in
research/findings/FVT-CORRECTED.md. Every number previously reported from
`scripts/fvt_model.run()` is void; these replace them.

FRICTION. 0.5 pt round trip, not the 2.0 pt inherited from the canon work. NQ is 0.25 pt/tick
at $5; commission runs about a tick round trip and slippage about a tick on a market order, so
0.5 pt is realistic and 2.0 pt was roughly 4x reality. The sensitivity is reported rather than
assumed, because at 1.0 pt the whole result more than halves.

BAR: positive in 2023, 2024, 2025 AND 2026 independently. Four eras, because three was already
shown to be anti-predictive on this exact strategy (FVT-TOMBSTONE.md) and two produced several
false positives before that.

    python -m scripts.fvt_sessions
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.fvt_model as F  # noqa: E402

YEARS = ("2023", "2024", "2025", "2026")
RRS = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)
FRIC = 0.5
LAB = {"AM": "NY AM 09:33", "PM": "NY PM 14:00", "E18": "6PM", "E20": "8PM", "LDN": "London 03:00"}


def book(b: pd.DataFrame, rr: float) -> pd.DataFrame:
    F.RR = rr
    F.WINDOWS = F.WINDOW_SETS["all"]
    T = F.run(b, 1, swing_n=1).sort_values(["day", "win", "hm"])
    T["attempt"] = T.groupby(["day", "win"]).cumcount() + 1
    T["yr"] = T.day.str[:4]
    X = T[(T.attempt == 1) & (T.phase == "cont")].copy()
    X["net"] = X.pts + F.FRICTION - FRIC          # undo the charged 2.0, apply 0.5
    return X


def main() -> int:
    b = F.load()
    nd = {y: b[b.day.str[:4] == y].day.nunique() for y in YEARS}
    ndall = sum(nd.values())
    L = ["# FVT session-by-session, corrected model, 2023–2026", "",
         "Re-run after the indexing bug in `research/findings/FVT-CORRECTED.md`. Every number",
         "previously reported from `fvt_model.run()` is void; these replace them.", "",
         f"Friction **{FRIC} pt** round trip (NQ: ~1 tick commission + ~1 tick slippage). The",
         "2.0 pt previously charged was inherited from the canon and ~4× reality.", "",
         f"{ndall} sessions. Bar: **positive in all four years independently.**", ""]

    best = {}
    for w in LAB:
        L += [f"## {LAB[w]}", "",
              "| RR | n | /day | net pt | win% | green | 2023 | 2024 | 2025 | 2026 | 4/4 |",
              "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|"]
        for rr in RRS:
            X = book(b, rr)
            S = X[X.win == w]
            if len(S) < 100:
                continue
            d = S.groupby("day").net.sum()
            ys = [S[S.yr == y].net.mean() for y in YEARS]
            ok = all(np.isfinite(v) and v > 0 for v in ys)
            if ok and (w not in best or S.net.mean() > best[w][1]):
                best[w] = (rr, S.net.mean(), len(S) / ndall, (d > 0).mean())
            L.append(f"| {rr:g} | {len(S):,} | {len(S)/ndall:.2f} | **{S.net.mean():+.2f}** | "
                     f"{(S.net>0).mean():.1%} | {(d>0).mean():.0%} | "
                     + " | ".join(f"{v:+.2f}" for v in ys)
                     + f" | {'**yes**' if ok else ''} |")
        L.append("")

    L += ["---", "", "## Every-year-positive cells, by session", "",
          "| session | best RR | /day | net pt | green days |", "|---|---:|---:|---:|---:|"]
    for w in LAB:
        if w in best:
            rr, n, pd_, g = best[w]
            L.append(f"| {LAB[w]} | {rr:g} | {pd_:.2f} | **{n:+.2f}** | {g:.0%} |")
        else:
            L.append(f"| {LAB[w]} | — | — | none clears four years | |")

    # combined book of the sessions that clear four years, each at its own best RR
    if best:
        parts = []
        for w, (rr, *_rest) in best.items():
            X = book(b, rr)
            parts.append(X[X.win == w])
        C = pd.concat(parts)
        d = C.groupby("day").net.sum()
        ys = [C[C.yr == y].net.mean() for y in YEARS]
        L += ["", "## Combined book — only the sessions that clear four years", "",
              "Each at its own best RR. **This is a selected combination and carries that",
              "selection**: five sessions and six RR values were inspected to build it.", "",
              "| n | /day | net pt | win% | green days | pts total | $ 1 contract |",
              "|---:|---:|---:|---:|---:|---:|---:|",
              f"| {len(C):,} | {len(C)/ndall:.2f} | **{C.net.mean():+.2f}** | "
              f"{(C.net>0).mean():.1%} | {(d>0).mean():.0%} | {C.net.sum():+,.0f} | "
              f"${C.net.sum()*20:+,.0f} |", "",
              "| year | n | /day | net pt | green days | pts |", "|---|---:|---:|---:|---:|---:|"]
        for y in YEARS:
            S = C[C.yr == y]
            dy = S.groupby("day").net.sum()
            L.append(f"| {y} | {len(S):,} | {len(S)/nd[y]:.2f} | **{S.net.mean():+.2f}** | "
                     f"{(dy>0).mean():.0%} | {S.net.sum():+,.0f} |")
        L += ["", "### Friction sensitivity — the load-bearing assumption", "",
              "| friction | net pt/trade | " + " | ".join(YEARS) + " |",
              "|---:|---:|" + "---:|" * len(YEARS)]
        g0 = C.net + FRIC
        for f in (0.25, 0.5, 1.0, 1.5, 2.0):
            yy = [g0[C.yr == y].mean() - f for y in YEARS]
            L.append(f"| {f:g} pt | **{g0.mean()-f:+.2f}** | "
                     + " | ".join(f"{v:+.2f}" for v in yy) + " |")

    text = "\n".join(L)
    print(text)
    (ROOT / "output/fvt_sessions.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
