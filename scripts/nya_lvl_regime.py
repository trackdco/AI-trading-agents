#!/usr/bin/env python3
"""NYA-LVL-01 stage 3a — the regime diagnostic. Is the stage-2 result an edge, or a
bet that NQ trended for 13 months?

Authorised by docs/PREREG-level-interaction-stage3.md, committed before this file.
Diagnosis, not a gate — no pass/fail bar. But its answer decides how the rest of
stage 3 is read.

    python -m scripts.nya_lvl_regime [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_lvl_census import RTH, load_bars  # noqa: E402
from scripts.nya_lvl_geometry import arm_grid, evaluate, paths  # noqa: E402
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-level-interaction-stage3.md"
OUT_MD = ROOT / "output/nya_lvl_regime.md"
ARM, ARM_STOP = "S10/TRAIL", 10.0
DEFAULT, DEF_STOP = "S20/T30", 20.0


def day_context(bars: pd.DataFrame) -> pd.DataFrame:
    """Per session: RTH open/close, absolute move, range, directional efficiency."""
    r = bars[(bars["min"] >= RTH[0]) & (bars["min"] < RTH[1])]
    g = r.groupby("day").agg(o=("open", "first"), c=("close", "last"),
                             hi=("high", "max"), lo=("low", "min"))
    path = r.assign(mv=r["close"].diff().abs()).groupby("day")["mv"].sum()
    g["net"] = g["c"] - g["o"]
    g["absmove"] = g["net"].abs()
    g["rng"] = g["hi"] - g["lo"]
    g["eff"] = g["absmove"] / path.reindex(g.index).replace(0, np.nan)
    return g.reset_index()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bars = load_bars()
    ev = paths(bars)
    d, lvl, day, typ, lad, ps = ev
    arms = [a for a in arm_grid() if a[0] in (ARM, DEFAULT)]
    res = evaluate(ev, arms, 1.0)

    ctx = day_context(bars).set_index("day")
    L = ["# NYA-LVL-01 stage 3a — regime diagnostic", "",
         f"Authorised by `{PREREG}`. **Diagnosis, not a gate.** Fit span, base cost.",
         "The question: is stage 2's result an edge, or a bet that NQ trended?", ""]
    ledger = []

    for label, stop in ((ARM, ARM_STOP), (DEFAULT, DEF_STOP)):
        net = res[label]
        df = pd.DataFrame({"day": day, "net": net, "side": d}).dropna()
        per_day = df.groupby("day")["net"].sum()
        J = ctx.join(per_day.rename("pnl"), how="inner").dropna(subset=["pnl"])

        L += [f"## {label}", "",
              "### 1. Does daily P&L track how far the market moved?", "",
              "| vs | correlation |", "|---|---:|"]
        for c, nm in (("absmove", "absolute RTH move |close-open|"),
                      ("rng", "RTH range"), ("eff", "directional efficiency")):
            L.append(f"| {nm} | **{J['pnl'].corr(J[c]):+.3f}** |")
        L.append("")

        L += ["### 2. P&L by directional-efficiency tercile", "",
              "A trend-capture model earns nearly everything in the top tercile.", "",
              "| efficiency | sessions | total pts | share of profit | mean/day |",
              "|---|---:|---:|---:|---:|"]
        J = J.copy()
        J["t"] = pd.qcut(J["eff"], 3, labels=["chop", "mid", "trend"])
        tot = J["pnl"].sum()
        for t, grp in J.groupby("t", observed=True):
            L.append(f"| {t} | {len(grp)} | {grp['pnl'].sum():+,.0f} | "
                     f"{100*grp['pnl'].sum()/tot:.0f}% | {grp['pnl'].mean():+.1f} |")
        L.append("")

        L += ["### 3. Long side vs short side", "",
              "A model that only earns on one side over a directional 13 months is a",
              "beta bet wearing a strategy label.", "",
              "| side | n | WR | total pts | mean R |", "|---|---:|---:|---:|---:|"]
        for s, nm in ((1, "long"), (-1, "short")):
            g = df[df["side"] == s]
            L.append(f"| {nm} | {len(g):,} | {(g['net']>0).mean():.0%} | "
                     f"{g['net'].sum():+,.0f} | {(g['net']/stop).mean():+.3f} |")
        L.append("")

        L += ["### 4. Monthly P&L vs NQ's own monthly move", "",
              "| month | NQ net pts | strategy pts |", "|---|---:|---:|"]
        J["m"] = J.index.str[:7]
        mm = J.groupby("m").agg(nq=("net", "sum"), st=("pnl", "sum"))
        for m, r in mm.iterrows():
            L.append(f"| {m} | {r.nq:+,.0f} | {r.st:+,.0f} |")
        cm = mm["nq"].corr(mm["st"])
        L += ["", f"**Correlation of monthly strategy P&L with NQ's monthly move: "
              f"{cm:+.3f}**", ""]

        ledger.append({
            "family": "NYA-LVL-01", "era": "fit", "prereg": PREREG,
            "trial": f"regime diagnostic {label} corr(pnl, absmove)",
            "stat_type": "rho", "estimate": round(float(J["pnl"].corr(J["absmove"])), 4),
            "n": len(J), "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"diagnosis only: corr with |move| "
                        f"{J['pnl'].corr(J['absmove']):+.3f}, with efficiency "
                        f"{J['pnl'].corr(J['eff']):+.3f}, monthly-vs-NQ {cm:+.3f}"),
        })

    text = "\n".join(L)
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    OUT_MD.write_text(text)
    existing = trial_ledger.load()
    already = set(zip(existing["family"], existing["trial"], existing["era"]))
    fresh = [r for r in ledger if (r["family"], r["trial"], r["era"]) not in already]
    if fresh:
        trial_ledger.record(fresh)
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
