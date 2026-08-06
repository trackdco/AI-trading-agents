#!/usr/bin/env python3
"""Test 1 — permutation null on `W`, corrected for the 32-cell selection.

Authorised by docs/PREREG-london-W-scrutiny.md, committed before this file.

The honest question is not "is this cell's lift large?" but "how often does MY OWN
procedure — build 32 check x arm cells, keep the ones that survive every era, report
the one that also pays at strict cost in both — produce a result this good from noise?"

So each shuffle permutes the check labels WITHIN arm and era (preserving every n, every
era split, and the outcome distribution untouched) and re-runs the whole selection.

    python -m scripts.london_W_scrutiny [--shuffles N] [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-W-scrutiny.md"
SRC = ROOT / "output/london_obk_depth.parquet"
OUT_MD = ROOT / "output/london_W_scrutiny.md"

ERAS = ("2025", "2026")
ARMS = ("F1", "A/S1", "F2", "B/S1")
THIN = 15
SEED = 20260805
OBSERVED_LIFT = 0.734          # W on A/S1, 2025 — the smaller of the two eras


def r_of(pts: np.ndarray, risk: np.ndarray, cost: float) -> np.ndarray:
    return (pts - cost) / risk


def evaluate(checks: dict[str, np.ndarray], pts, risk, arm, era) -> tuple[float, int]:
    """Run the full selection. Returns (max era-consistent lift, count that pay)."""
    max_lift, n_pays = -np.inf, 0
    for chk, vals in checks.items():
        for a in ARMS:
            lifts, pays = [], []
            ok = True
            for e in ERAS:
                m = (arm == a) & (era == e) & ~np.isnan(vals)
                p = m & (vals == 1)
                f = m & (vals == 0)
                if p.sum() < THIN or f.sum() < THIN:
                    ok = False
                    break
                lifts.append(r_of(pts[p], risk[p], 1.0).mean()
                             - r_of(pts[f], risk[f], 1.0).mean())
                pays.append(r_of(pts[p], risk[p], 2.0).mean() > 0)
            if not ok:
                continue
            if all(v > 0 for v in lifts):
                max_lift = max(max_lift, min(lifts))   # weakest era = the claim's strength
                if all(pays):
                    n_pays += 1
    return max_lift, n_pays


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shuffles", type=int, default=10000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    T = pd.read_parquet(SRC)
    T = T[T["arm"].isin(ARMS)].reset_index(drop=True)
    chk_cols = [c for c in T.columns if c.startswith("chk_")]
    checks = {c: T[c].to_numpy(float) for c in chk_cols}
    pts, risk = T["pts"].to_numpy(float), T["risk"].to_numpy(float)
    arm, era = T["arm"].to_numpy(), T["era"].to_numpy()

    obs_lift, obs_pays = evaluate(checks, pts, risk, arm, era)
    print(f"observed: max era-consistent lift {obs_lift:+.3f}, cells that pay {obs_pays}")

    rng = np.random.default_rng(SEED)
    ge_lift = ge_pays = 0
    null_lifts, null_pays = [], []
    # shuffle WITHIN arm x era so every n, era split and outcome stay fixed
    groups = [np.flatnonzero((arm == a) & (era == e)) for a in ARMS for e in ERAS]
    for i in range(args.shuffles):
        sh = {}
        for c, v in checks.items():
            w = v.copy()
            for g in groups:
                w[g] = rng.permutation(w[g])
            sh[c] = w
        lift, pays = evaluate(sh, pts, risk, arm, era)
        null_lifts.append(lift if np.isfinite(lift) else np.nan)
        null_pays.append(pays)
        if np.isfinite(lift) and lift >= OBSERVED_LIFT:
            ge_lift += 1
        if pays >= 1:
            ge_pays += 1
        if (i + 1) % 2000 == 0:
            print(f"  {i+1}/{args.shuffles}  p_fw so far {ge_pays/(i+1):.4f}", flush=True)

    p_cell = ge_lift / args.shuffles
    p_fw = ge_pays / args.shuffles
    nl = np.array(null_lifts, dtype=float)
    nl = nl[np.isfinite(nl)]

    verdict = "PASS" if p_fw < 0.05 else "FAIL"
    L = ["# LDN-OBK-01 — `W` permutation null, selection-corrected", "",
         f"Authorised by `{PREREG}`. {args.shuffles:,} shuffles, seed `{SEED}`.",
         "Check labels permuted WITHIN arm and era, so every n, every era split and the",
         "outcome distribution are preserved exactly. Each shuffle re-runs the **entire**",
         "32-cell selection, because selecting the best of 32 is what actually happened.",
         "",
         "## Result", "",
         "| quantity | observed | null | p |",
         "|---|---:|---|---:|",
         f"| max era-consistent lift | **{obs_lift:+.3f}** | median {np.median(nl):+.3f}, "
         f"95th pct {np.percentile(nl, 95):+.3f} | {p_cell:.4f} |",
         f"| cells surviving every era AND paying at strict cost | **{obs_pays}** | "
         f"mean {np.mean(null_pays):.2f}, ≥1 in {100*p_fw:.1f}% of shuffles | "
         f"**{p_fw:.4f}** |",
         "",
         f"**Declared pass condition: family-wise p < 0.05. Result: {verdict} "
         f"(p = {p_fw:.4f}).**", ""]

    if verdict == "PASS":
        L += ["## Read", "",
              "The procedure that produced `W` does **not** produce a result this good",
              "from noise at anything like the observed rate. The lift survives its own",
              "selection correction — which is the specific thing a 'best of 32' finding",
              "usually fails.", "",
              "**This does not promote `W`** and does not make the strategy good. It",
              "clears exactly one hurdle: the result is unlikely to be an artifact of",
              "having looked at 32 cells. Tests 2-4 (event expansion, stop caps,",
              "state-conditional) now run, and n≈75 remains the weakest thing about it.", ""]
    else:
        L += ["## Read", "",
              "**My own search procedure produces a result this good from shuffled labels",
              f"in {100*p_fw:.1f}% of runs.** The `W` finding is therefore consistent with",
              "selection noise across 32 cells, and the per-cell number was never the",
              "right thing to quote.", "",
              "Per the prereg, tests 2-4 are NOT run — spending more search on a result",
              "that cannot clear its own selection correction only inflates the ledger",
              "denominator. **The kill is written.**", "",
              "## The two statistics disagree, and the declared one governs", "",
              f"The lift *magnitude* clears its own family-wise bar: +{obs_lift:.3f} sits",
              f"above {100*(1-p_cell):.1f}% of shuffled maxima (p={p_cell:.4f}). The",
              "*existence* of a cell that survives every era and pays does not: that",
              f"happens in {100*p_fw:.1f}% of shuffles.", "",
              "**They measure different claims, and the declared test matches the claim I",
              "actually made.** The headline reported out of the depth pass was *\"exactly",
              "one survivor pays at strict cost in both eras\"* — an existence claim about",
              "the output of a 32-cell search. That is the thing the family-wise null",
              "tests, and it fails. The magnitude statistic would support a different",
              "headline (*\"the lift is unusually large\"*) that I did not lead with.", "",
              "**Switching to the statistic that passes, after seeing which one passes, is",
              "the exact procedure this framework exists to prevent.** So it is not being",
              "switched. The magnitude result is recorded here because it is real",
              "information and someone may want it later — but re-opening `W` on that",
              "basis requires a NEW prereg declaring the magnitude criterion in advance,",
              "on an independent sample. It cannot be done by re-reading this table.", ""]

    text = "\n".join(L)
    print(text)
    if args.dry_run:
        print("--dry-run: nothing written")
        return 0

    OUT_MD.write_text(text)
    row = [{"family": "LDN-OBK-01", "era": "2025+2026", "prereg": PREREG,
            "trial": "W permutation null, selection-corrected (family-wise)",
            "stat_type": "mean", "estimate": round(float(p_fw), 5), "n": args.shuffles,
            "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"{verdict}: family-wise p={p_fw:.4f} vs declared 0.05; "
                        f"per-cell p={p_cell:.4f}; observed max lift {obs_lift:+.3f} "
                        f"vs null 95th pct {np.percentile(nl, 95):+.3f}")}]
    existing = trial_ledger.load()
    if not ((existing["family"] == "LDN-OBK-01")
            & (existing["trial"] == row[0]["trial"])).any():
        trial_ledger.record(row)
        print("recorded 1 trial")
    print(trial_ledger.summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
