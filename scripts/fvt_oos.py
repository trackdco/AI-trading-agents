#!/usr/bin/env python3
"""Per-session FVT optimisation on 2024-2026, then the SAME grid on the sealed 2023.

ANGUS 2026-08-06: *"nah fuck the pbo we can see if its over fitted from testing what we
optimised in this 3 window span holds in 2023."*

Fair: a genuine out-of-sample test is stronger than PBO, which is only a proxy for it.

BUT THE HOLDOUT IS RUN AS A WHOLE GRID, NOT A SINGLE CONFIG. Testing only the fit-best config
on 2023 gives one number and cannot distinguish "this config is good" from "2023 was an easy
year". Running all 160 cells on both spans gives the **rank correlation** between fit
performance and holdout performance, which answers the overfitting question directly:

    strongly positive   the configs that won on 2024-26 also win in 2023 -> structural
    near zero           fit rankings carry no information about 2023 -> selection
    negative            fit-best is systematically bad OOS -> worse than useless

That is the same question PBO asks, answered on real untouched data instead of by resampling.

    python -m scripts.fvt_oos
"""

from __future__ import annotations

import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.fvt_model as F  # noqa: E402
from scripts.fvt_optimise import CAPS, CONTS, LAB, RRS, STOP_MULTS, entries, evaluate  # noqa: E402


def main() -> int:
    b = F.load()
    fit = b[b.day >= "2024-01-01"]
    oos = b[b.day.str[:4] == "2023"]
    nf, no = fit.day.nunique(), oos.day.nunique()
    print(f"FIT  {fit.day.min()} -> {fit.day.max()}  {nf} sessions", flush=True)
    print(f"OOS  {oos.day.min()} -> {oos.day.max()}  {no} sessions (never touched)", flush=True)
    Ef, Eo = entries(fit), entries(oos)
    print(f"entries: fit {len(Ef):,}  oos {len(Eo):,}", flush=True)

    grid = list(product(STOP_MULTS, RRS, CONTS, CAPS))
    rows = []
    for i, (sm, rr, ct, cap) in enumerate(grid):
        Df, Do = evaluate(Ef, sm, rr, ct, cap), evaluate(Eo, sm, rr, ct, cap)
        for w in LAB:
            Sf, So = Df[Df.win == w], Do[Do.win == w]
            if len(Sf) < 150 or len(So) < 50:
                continue
            es = [Sf[Sf.era == y].pts.mean() if (Sf.era == y).sum() > 30 else np.nan
                  for y in ("2024", "2025", "2026")]
            gf, go = Sf.groupby("day").pts.sum(), So.groupby("day").pts.sum()
            rows.append({"win": w, "cfg": f"stop×{sm} RR{rr} cont{ct}m cap{cap}",
                         "n_fit": len(Sf), "fit": Sf.pts.mean(), "fit_day": gf.sum() / nf,
                         "fit_green": (gf > 0).mean(),
                         "e24": es[0], "e25": es[1], "e26": es[2],
                         "all3": all(np.isfinite(x) and x > 0 for x in es),
                         "n_oos": len(So), "oos": So.pts.mean(),
                         "oos_day": go.sum() / no, "oos_green": (go > 0).mean()})
        if (i + 1) % 40 == 0:
            print(f"  [{i+1}/{len(grid)}]", flush=True)

    R = pd.DataFrame(rows)
    R.to_parquet(ROOT / "output/fvt_oos_grid.parquet", index=False)

    L = ["# FVT per-session optimisation → sealed 2023 holdout", "",
         f"Fit **2024-01-01 → {fit.day.max()}** ({nf} sessions). "
         f"Holdout **all of 2023** ({no} sessions, never touched).", "",
         f"{len(R)} cells scored on BOTH spans. Grid: stop×{STOP_MULTS}, RR{RRS}, "
         f"continuation {CONTS}m, attempt cap {CAPS}.", "",
         "## Best config per session, by fit", "",
         "| session | best config | n | /day | fit net | 2024 | 2025 | 2026 | **2023 OOS** |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for w in LAB:
        S = R[R.win == w]
        if S.empty:
            continue
        r = S.loc[S.fit.idxmax()]
        L.append(f"| {LAB[w]} | {r.cfg} | {r.n_fit:,.0f} | {r.n_fit/nf:.2f} | "
                 f"**{r.fit:+.2f}** | {r.e24:+.2f} | {r.e25:+.2f} | {r.e26:+.2f} | "
                 f"**{r.oos:+.2f}** |")

    L += ["", "## Does the ranking transfer? (the overfitting test)", "",
          "Spearman rank correlation between fit and 2023 net-per-trade across all cells in a",
          "session. Positive means the configs that won on 2024–26 also win in 2023.", "",
          "| session | cells | rank corr | fit-best → 2023 | cells 3/3 in fit | of those, % +ve in 2023 |",
          "|---|---:|---:|---:|---:|---:|"]
    for w in LAB:
        S = R[R.win == w]
        if len(S) < 20:
            continue
        # rank-correlate by hand: no scipy in this environment
        rc = S.fit.rank().corr(S.oos.rank())
        r = S.loc[S.fit.idxmax()]
        C = S[S.all3]
        L.append(f"| {LAB[w]} | {len(S)} | **{rc:+.3f}** | {r.oos:+.2f} | {len(C)} | "
                 + (f"{(C.oos>0).mean():.0%} |" if len(C) else "— |"))

    C = R[R.all3]
    L += ["", f"## The {len(C)} cells positive in all three fit years, ranked by fit", "",
          "| session | config | n fit | fit | 2024 | 2025 | 2026 | n 2023 | **2023** | 2023 green |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for _, r in C.sort_values("fit", ascending=False).head(15).iterrows():
        L.append(f"| {LAB[r.win]} | {r.cfg} | {r.n_fit:,.0f} | **{r.fit:+.2f}** | {r.e24:+.2f} | "
                 f"{r.e25:+.2f} | {r.e26:+.2f} | {r.n_oos:,.0f} | **{r.oos:+.2f}** | "
                 f"{r.oos_green:.0%} |")
    if len(C):
        L += ["", f"**Of the {len(C)} triple-consistent cells, {(C.oos>0).mean():.0%} stay "
              f"positive in 2023** (mean {C.oos.mean():+.2f} pt/trade).", ""]

    text = "\n".join(L)
    print(text)
    (ROOT / "output/fvt_oos.md").write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
