#!/usr/bin/env python3
"""NYA-LVL-01 — placebo-level null on the depth result.

Declared in docs/PREREG-level-interaction-depth.md BEFORE the depth pass ran.

We selected W-at-2R out of 5 checks x 5 payoffs. So the null re-runs the WHOLE
selection on placebo levels — six random lines drawn from the same day's pre-RTH
range, identical grammar, identical depth join — and takes the family-wise best cell.

    python -m scripts.nya_lvl_null [--perms N]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nya_lvl_census import load_bars  # noqa: E402
from scripts.nya_lvl_depth import STOP, attach, checks, depth_index  # noqa: E402
from scripts.nya_lvl_rebuild import build, score  # noqa: E402
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-level-interaction-depth.md"
RR = [1.0, 1.5, 2.0, 2.5, 3.0]
SEED = 20260805
THIN = 30


def best_cell(D, P, dep) -> float:
    """The family-wise max: best R/trade across every check x every payoff."""
    for r in RR:
        D[f"w{r}"] = (score(D, P, ("x", STOP, STOP * r, False)) - 1.0) > 0
    D = attach(D, dep)
    C = checks(D)
    cov = D["thick"].notna()
    best = -9.0
    for chk in C.columns:
        m = cov & (C[chk] == 1)
        if m.sum() < THIN:
            continue
        for r in RR:
            w = D.loc[m, f"w{r}"].mean()
            best = max(best, w * r - (1 - w))
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perms", type=int, default=100)
    args = ap.parse_args()

    bars = load_bars()
    dep = depth_index()
    print(f"depth days {len(dep)}", flush=True)
    D, P = build(bars)
    obs = best_cell(D.copy(), P, dep)
    print(f"OBSERVED family-wise best: {obs:+.4f} R/trade", flush=True)

    rng = np.random.default_rng(SEED)
    nulls = []
    for k in range(args.perms):
        Dp, Pp = build(bars, rng)
        if len(Dp) < 200:
            continue
        nulls.append(best_cell(Dp, Pp, dep))
        if (k + 1) % 10 == 0:
            arr = np.array(nulls)
            print(f"  perm {k+1}/{args.perms}  p={np.mean(arr >= obs):.4f}  "
                  f"null med {np.median(arr):+.3f}", flush=True)

    nb = np.array(nulls)
    p = float(np.mean(nb >= obs)) if len(nb) else float("nan")
    verdict = "PASS" if p <= 0.01 else "FAIL"
    txt = (
        "# NYA-LVL-01 — placebo null on the depth result\n\n"
        f"Authorised by `{PREREG}`, declared before the depth pass ran. "
        f"{len(nb)} permutations, seed {SEED}.\n\n"
        "Six random lines drawn from the same day's pre-RTH range, identical touch\n"
        "grammar, identical depth join, and the **whole 5-check x 5-payoff selection\n"
        "re-run** — because selecting W-at-2R out of that grid is what actually happened.\n\n"
        "| | value |\n|---|---:|\n"
        f"| observed family-wise best | **{obs:+.4f} R/trade** |\n"
        f"| null median | {np.median(nb):+.4f} |\n"
        f"| null 95th pct | {np.percentile(nb, 95):+.4f} |\n"
        f"| null 99th pct | {np.percentile(nb, 99):+.4f} |\n"
        f"| **family-wise p** | **{p:.4f}** |\n\n"
        f"**Declared bar p <= 0.01. Result: {verdict}.**\n\n"
        + ("The depth condition on the real six levels is not reproduced by random lines\n"
           "under an identical search. The selection survives its own correction.\n"
           if verdict == "PASS" else
           "Random lines in the same price zone reach the same best cell. The depth\n"
           "result does not survive its own selection correction.\n"))
    print(txt)
    (ROOT / "output/nya_lvl_null.md").write_text(txt)

    ex = trial_ledger.load()
    row = [{"family": "NYA-LVL-01", "era": "fit", "prereg": PREREG,
            "trial": "depth placebo null, family-wise",
            "stat_type": "mean", "estimate": round(p, 5), "n": len(nb),
            "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"{verdict}: p={p:.4f} vs declared 0.01; observed {obs:+.4f} "
                        f"vs null 95th {np.percentile(nb, 95):+.4f}")}]
    if not ((ex["family"] == "NYA-LVL-01") & (ex["trial"] == row[0]["trial"])).any():
        trial_ledger.record(row)
        print("recorded 1 trial")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
