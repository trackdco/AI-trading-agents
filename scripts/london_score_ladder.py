#!/usr/bin/env python3
"""SCORE LADDER for the London 10-13 UK book -- the Angus conviction structure.

Angus's canon does not size off a single variable. It grades each trade against a small set of
BINARY CHECKS measured at entry, sums them into a SCORE, and sizes off the score:

    scripts/canon_mechanical.py   NY      5 checks (W/F/Tp/G/C)      score<=2 -> 0 | 3 -> .5 | 4 -> 1 | 5 -> 1.5
    scripts/london_canon.py       LON 8-10  4 checks (W/FAR/ROOM/ASIA) score<=1 -> 0 | 2 -> .5 | 3 -> 1 | 4 -> 1.5

The validation criterion is NOT a p-value on any single check -- it is LADDER MONOTONICITY:
average outcome must rise with score, and it must do so in BOTH halves of the sample. Angus's
note on his golden campaign reads "Ladder monotone both years; reject pile (<=2) = -$31k/2yr
bleed" -- i.e. the bottom rung must be genuinely bad, not merely less good.

This module is the assembler. Register check functions, and it will:
  1. grade every signal, 2. report the ladder (n / WR / avgR / netR per score),
  3. test monotonicity overall and per half, 4. permutation-test the ladder's slope,
  5. apply the size ladder to the leakage-clean book C and report the economics,
  6. compare against flat sizing at MATCHED AVERAGE EXPOSURE, because a ladder that
     de-risks everything looks good against flat 1.0x for the wrong reason.

Checks are supplied by --checks pointing at a python file that defines CHECKS: a dict of
{NAME: (fn, description)} where fn(row) -> 1.0 / 0.0 / np.nan. Nothing is hardcoded here,
so the surviving checks from the mining workflows drop straight in.

    LONDON_SCRATCH=<dir> python3 scripts/london_score_ladder.py --checks scripts/<file>.py
"""
import argparse
import importlib.util
import os

import numpy as np
import pandas as pd

S = os.environ.get("LONDON_SCRATCH", os.path.expanduser("~/london_out"))
rng = np.random.default_rng(23)
SPLIT = "2026-01-13"
NPERM = 20_000


def load_checks(path):
    spec = importlib.util.spec_from_file_location("checkmod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "CHECKS"):
        raise SystemExit(f"{path} defines no CHECKS dict")
    return mod.CHECKS


def grade(F, CHECKS):
    out = F.copy()
    for name, (fn, _) in CHECKS.items():
        out[name] = out.apply(fn, axis=1).astype(float)
    cols = list(CHECKS)
    # a NaN check is a check that could not be evaluated -- it must not silently count as 0.
    out["n_eval"] = out[cols].notna().sum(axis=1)
    out["score"] = out[cols].sum(axis=1, skipna=True)
    return out, cols


def ladder(D, label):
    print(f"\n  {label}: n={len(D)}")
    print(f"    {'score':>5} {'n':>4} {'WR':>5} {'avgR':>7} {'netR':>8}")
    rows = []
    for s in sorted(D.score.dropna().unique()):
        g = D[D.score == s]
        rows.append((s, len(g), (g.R > 0).mean() * 100, g.R.mean(), g.R.sum()))
        print(f"    {s:>5.0f} {len(g):>4} {(g.R>0).mean()*100:>4.0f}% "
              f"{g.R.mean():>+7.2f} {g.R.sum():>+8.2f}")
    return rows


def monotone(rows, min_n=3):
    """Monotone in avgR across rungs that have at least min_n trades."""
    use = [(s, a) for s, n, _, a, _ in rows if n >= min_n]
    if len(use) < 3:
        return None
    vals = [a for _, a in use]
    return all(x < y for x, y in zip(vals, vals[1:]))


def slope_perm(D):
    """Permutation p on the score->R slope. Shuffles R against score."""
    s, r = D.score.values.astype(float), D.R.values
    ok = np.isfinite(s) & np.isfinite(r)
    s, r = s[ok], r[ok]
    if len(s) < 20 or np.std(s) == 0:
        return np.nan, np.nan
    obs = np.polyfit(s, r, 1)[0]
    cnt = 0
    for _ in range(NPERM):
        if np.polyfit(s, rng.permutation(r), 1)[0] >= obs:
            cnt += 1
    return obs, (cnt + 1) / (NPERM + 1)


SIZE_LADDERS = {
    # 4-5 check ladders (Angus's, for when a score has that many rungs)
    "angus_ny":  {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.5, 4: 1.0, 5: 1.5},
    "angus_lon": {0: 0.0, 1: 0.0, 2: 0.5, 3: 1.0, 4: 1.5},
    "gentle":    {0: 0.5, 1: 0.5, 2: 0.75, 3: 1.0, 4: 1.25, 5: 1.5},
    "no_veto":   {0: 0.5, 1: 0.5, 2: 1.0, 3: 1.0, 4: 1.5, 5: 1.5},
    # 2-check ladders -- a 3-rung score cannot use the ones above, which zero out
    # everything below 3 and would flatten the whole book to no size at all.
    "2ck_soft":  {0: 0.5, 1: 1.0, 2: 1.5},
    "2ck_veto":  {0: 0.0, 1: 1.0, 2: 1.5},
    "2ck_flat1": {0: 0.5, 1: 1.0, 2: 1.0},
}


def economics(C, cols):
    base = C.R.sum()
    print(f"\n  book C flat 1.0x: {len(C)} trades  netR {base:+.2f}  "
          f"WR {(C.R>0).mean()*100:.0f}%")
    print(f"\n  {'ladder':<12} {'netR':>8} {'vs flat':>8} {'avg size':>9} "
          f"{'netR/exposure':>14} {'vs flat @same':>14}")
    print("  " + "-" * 70)
    for name, lad in SIZE_LADDERS.items():
        w = C.score.map(lad).fillna(0.0).values
        net = (C.R.values * w).sum()
        avg = w.mean()
        # the honest benchmark: flat sizing at the SAME average exposure
        matched = base * avg
        print(f"  {name:<12} {net:>+8.2f} {net-base:>+8.2f} {avg:>9.2f} "
              f"{(net/avg if avg else np.nan):>+14.2f} {net-matched:>+14.2f}")
    print("\n  'vs flat @same' is the column that matters: it removes the de-risking effect and")
    print("  asks whether the ladder puts size where the money actually is. Positive = real skill.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checks", required=True)
    ap.add_argument("--features", default=f"{S}/london_depth_features.csv")
    args = ap.parse_args()

    F = pd.read_csv(args.features)
    CHECKS = load_checks(args.checks)
    print(f"signals {len(F)}   checks {len(CHECKS)}: {', '.join(CHECKS)}")
    for n, (_, d) in CHECKS.items():
        print(f"    {n:<12} {d}")

    D, cols = grade(F, CHECKS)
    inc = D[D.n_eval < len(cols)]
    if len(inc):
        print(f"\n  WARNING {len(inc)} signals could not evaluate every check "
              f"(NaN inputs). Their score is a SUM OVER FEWER CHECKS and is not comparable.")
        print(f"    affected days: {sorted(set(inc.day))[:8]}{' ...' if len(set(inc.day)) > 8 else ''}")

    print("\n" + "=" * 72)
    print("THE LADDER")
    print("=" * 72)
    full = ladder(D, "all signals")
    h1 = ladder(D[D.day < SPLIT], "H1 (frozen-threshold half)")
    h2 = ladder(D[D.day >= SPLIT], "H2 (held-out half)")

    print(f"\n  monotone in avgR?   all={monotone(full)}   H1={monotone(h1)}   H2={monotone(h2)}")
    print("  (a ladder that is monotone overall but NOT in H2 is a fit, not an edge)")

    b, p = slope_perm(D)
    print(f"\n  score->R slope {b:+.3f} R per rung   permutation p={p:.4f}")
    b2, p2 = slope_perm(D[D.day >= SPLIT])
    print(f"  H2 only        {b2:+.3f} R per rung   permutation p={p2:.4f}   <- the honest one")

    print("\n" + "=" * 72)
    print("ECONOMICS on book C (leakage-clean)")
    print("=" * 72)
    economics(D[D.in_C].copy(), cols)

    out = f"{S}/london_scored.csv"
    D.to_csv(out, index=False)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
