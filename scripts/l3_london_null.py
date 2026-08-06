#!/usr/bin/env python3
"""L3 LONDON — the family-wise permutation null over the WHOLE trial search.

Declared in docs/PREREG-london-canon-rebuild.md §8 BEFORE this ran.

The trial tested 49 candidates (45 features + the 4 shipped checks) and reported the best
three. So the null re-runs the entire selection, not the winner: shuffle `dollars_1lot`
WITHIN ERA — preserving each era's base win rate, destroying only the feature-to-outcome
association — re-run the identical 49-candidate search, and take the family-wise maximum
|WR gap| among era-consistent survivors.

TWO BARS, BOTH DECLARED IN ADVANCE, BOTH MUST PASS:
  1. family-wise p <= 0.01
  2. the 2026 era must clear its OWN null independently -- Appendix A's London tightening,
     because London has no hand-log ground truth: "same-direction-only is INCONCLUSIVE in
     London, and INCONCLUSIVE blocks"

Masks are computed ONCE from the features (they do not depend on outcomes), so a
permutation is just a re-scoring. That is what makes 1,000 shuffles of a 49-candidate
search cheap.

    python -m scripts.l3_london_null [--perms 1000]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.l3_london_trial import MIN_CELL, SKIP, derive  # noqa: E402
from src.validation import trial_ledger  # noqa: E402

PREREG = "docs/PREREG-london-canon-rebuild.md"
OUT_MD = ROOT / "output/l3_london_null.md"
SEED = 20260805
BAR_P = 0.01


def masks(F: pd.DataFrame) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """hi/lo membership per candidate. Outcome-independent, so computed once."""
    out = {}
    cands = [c for c in F.columns
             if (c.startswith("chk_") or (c not in SKIP and not c.startswith("dep_")
                                          and not c.startswith("p1_")))
             and c != "chk_W_late" and pd.api.types.is_numeric_dtype(F[c])
             and F[c].notna().sum() > 4 * MIN_CELL]
    for c in sorted(set(cands)):
        s = F[c]
        u = s.dropna().unique()
        if len(u) <= 1:
            continue
        if len(u) == 2:
            hi, lo = (s == max(u)).to_numpy(), (s == min(u)).to_numpy()
        else:
            q = s.quantile([1 / 3, 2 / 3])
            if q.iloc[0] == q.iloc[1]:
                continue
            hi, lo = (s > q.iloc[1]).to_numpy(), (s < q.iloc[0]).to_numpy()
        out[c] = (np.nan_to_num(hi).astype(bool), np.nan_to_num(lo).astype(bool))
    return out


def family_max(win: np.ndarray, M: dict, e25: np.ndarray, e26: np.ndarray
               ) -> tuple[float, float]:
    """(family-wise max |gap| among era-consistent survivors, the 2026 max |gap|)."""
    best, best26 = 0.0, 0.0
    for hi, lo in M.values():
        g = {}
        ok = True
        for era, m in (("25", e25), ("26", e26)):
            a, b = hi & m, lo & m
            if a.sum() < MIN_CELL or b.sum() < MIN_CELL:
                ok = False
                break
            g[era] = win[a].mean() - win[b].mean()
        if not ok or g["25"] == 0 or g["26"] == 0:
            continue
        if np.sign(g["25"]) != np.sign(g["26"]):
            continue
        gap = abs(win[hi].mean() - win[lo].mean())
        best = max(best, gap)
        best26 = max(best26, abs(g["26"]))
    return best, best26


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perms", type=int, default=1000)
    ap.add_argument("--arm", default="vs_first")
    ap.add_argument("--features", default="output/l3_features_london_fit.parquet")
    ap.add_argument("--kind", default="all",
                    choices=["all", "displacement", "rejection_block"])
    a = ap.parse_args()

    F = pd.read_parquet(ROOT / a.features)
    F = F[F[a.arm]].copy()
    if a.kind != "all":
        F = F[F["kind"] == a.kind].copy()
    F["era"] = F.day.str[:4]
    F = derive(F).reset_index(drop=True)
    M = masks(F)
    win = (F.dollars_1lot.to_numpy(float) > 0).astype(float)
    e25 = (F.era == "2025").to_numpy()
    e26 = (F.era == "2026").to_numpy()
    obs, obs26 = family_max(win, M, e25, e26)
    print(f"{len(M)} candidates in the search | observed family-wise max |WR gap| "
          f"{obs:.4f} | 2026 {obs26:.4f}", flush=True)

    rng = np.random.default_rng(SEED)
    nulls, nulls26 = [], []
    for k in range(a.perms):
        w = win.copy()
        for m in (e25, e26):                 # shuffle WITHIN era: base rates preserved
            idx = np.flatnonzero(m)
            w[idx] = win[rng.permutation(idx)]
        b, b26 = family_max(w, M, e25, e26)
        nulls.append(b)
        nulls26.append(b26)
        if (k + 1) % 100 == 0:
            print(f"  perm {k+1}/{a.perms}  p={np.mean(np.array(nulls) >= obs):.4f}  "
                  f"p26={np.mean(np.array(nulls26) >= obs26):.4f}", flush=True)

    nb, nb26 = np.array(nulls), np.array(nulls26)
    p = float(np.mean(nb >= obs))
    p26 = float(np.mean(nb26 >= obs26))
    pass1, pass2 = p <= BAR_P, p26 <= BAR_P
    verdict = "PASS" if (pass1 and pass2) else "FAIL"

    L = ["# LDN-CAN-01 — L3 family-wise permutation null", "",
         f"Declared in `{PREREG}` §8 before this ran. {len(nb)} permutations, seed {SEED}.",
         "", f"**{len(M)} candidates** in the search. `dollars_1lot` shuffled WITHIN ERA so",
         "each era's base win rate is preserved and only the feature-to-outcome association",
         "is destroyed. The entire selection is re-run each time and the family-wise",
         "maximum |WR gap| among era-consistent survivors is recorded.", "",
         "| statistic | observed | null median | null 95th | null 99th | **p** | bar | result |",
         "|---|---:|---:|---:|---:|---:|---:|---|",
         f"| family-wise max \\|WR gap\\| | **{obs:.1%}** | {np.median(nb):.1%} | "
         f"{np.percentile(nb, 95):.1%} | {np.percentile(nb, 99):.1%} | **{p:.4f}** | "
         f"≤{BAR_P} | {'**PASS**' if pass1 else '**FAIL**'} |",
         f"| 2026 alone (London tightening) | **{obs26:.1%}** | {np.median(nb26):.1%} | "
         f"{np.percentile(nb26, 95):.1%} | {np.percentile(nb26, 99):.1%} | **{p26:.4f}** | "
         f"≤{BAR_P} | {'**PASS**' if pass2 else '**FAIL**'} |", "",
         f"## VERDICT: {verdict}", ""]
    if verdict == "PASS":
        L += ["The trial's separation is not reproduced by shuffled outcomes under an",
              "identical search, and the 2026 era clears its own null independently.",
              "**The survivors may proceed to L4** — still as a default-plus-challengers",
              "structure, with nothing promoted on in-sample rank (§6.0.1).", ""]
    else:
        L += ["**A search of this size produces separation this large from noise more often",
              f"than the declared bar allows.** No L3 feature enters L4 on this evidence —",
              "including `ROOM`, the strongest survivor.", "",
              "Per §5.9.2 this is not yet an expectancy kill for the family: the geometry",
              "and policy classes (L4) have not been searched. It closes the FEATURE class",
              "at these definitions, on this population.", ""]
    L += ["**Both bars were declared in `" + PREREG + "` §8 before any p-value existed.**",
          "Choosing the statistic that passes after seeing which one passes is the failure",
          "that closed `LDN-PO3-01`'s depth pass at family-wise p = 0.42.", ""]

    text = "\n".join(L)
    print(text)
    (OUT_MD if a.kind == "all"
     else OUT_MD.with_name(f"l3_london_null_{a.kind}.md")).write_text(text)

    row = [{"family": "LDN-CAN-01", "era": "fit", "prereg": PREREG,
            "trial": ("L3 family-wise permutation null over the search"
                      + (f" ({a.kind})" if a.kind != "all" else "")),
            "stat_type": "mean", "estimate": round(p, 5), "n": len(nb),
            "t_stat": 0.0, "effect": 0.0,
            "verdict": (f"{verdict}: family-wise p={p:.4f} (obs {obs:.1%} vs null 95th "
                        f"{np.percentile(nb, 95):.1%}); 2026-alone p={p26:.4f}; "
                        f"both bars declared at 0.01 before the run")}]
    ex = trial_ledger.load()
    if not ((ex["family"] == "LDN-CAN-01") & (ex["trial"] == row[0]["trial"])).any():
        trial_ledger.record(row)
        print("recorded 1 trial")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
