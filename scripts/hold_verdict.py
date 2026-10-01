"""Apply the ARMING adoption rule to the 2020-22 empire, unchanged.

The rule, as preregistered for the 2023-26 test (scripts/conviction_sizing.py):
  ADOPT if, after scaling the armed book so its max drawdown equals the flat
  book's, R/day improves by >= 5% in BOTH halves of the sample.
Drawdown-matched is the bar because the sizing dial already buys R/day for
drawdown at any multiple; a layer must beat that trade, not re-sell it.

Split at the midpoint of THIS sample (2021-07-02), the same way MID splits
2023-26. Also reports where the drawdown actually happened, because the
2020-22 empire's -39.4R is more than double the 2023-26 book's -18.1R and
that needs an explanation, not a shrug.
"""
import sys
from collections import defaultdict
import numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-user-AI-trading-agents/8561fb22-7a6d-585e-9576-98688737845d/scratchpad")
import hold_empire as HE   # noqa: E402  (reuses its loaders; prints its tables)

import scripts.conviction_sizing as CS  # noqa: E402


def series(arm):
    lv, sv, nv = HE.books(arm)
    kept = CS.rail_pass([lv, sv, nv])
    days = sorted(kept)
    v = np.array([sum(HE.net(t) for t in kept[d]) for d in days])
    return days, v, kept


def dd(v):
    eq = np.cumsum(v)
    return float((eq - np.maximum.accumulate(eq)).min())


print("\n" + "=" * 84)
print("ARMING VERDICT ON 2020-2022 — the preregistered rule, unchanged")
print("=" * 84)

dF, vF, kF = series(False)
dA, vA, kA = series(True)
assert dF == dA, "day grids differ"
MID = dF[len(dF) // 2]
print(f"\nsplit at {MID}  ({len(dF)} days, {sum(d < MID for d in dF)} / "
      f"{sum(d >= MID for d in dF)})")

scale = abs(dd(vF)) / abs(dd(vA))
vAs = vA * scale
print(f"drawdown-match scale for armed: x{scale:.4f}  "
      f"(maxDD {dd(vF):+.1f} vs {dd(vA):+.1f} -> {dd(vAs):+.1f})")

print(f"\n{'half':<10}{'flat R/day':>12}{'armed R/day':>14}{'armed dd-matched':>19}{'lift':>9}")
print("-" * 84)
ok = True
for nm, msk in (("IS", np.array([d < MID for d in dF])),
                ("OOS", np.array([d >= MID for d in dF]))):
    f, a = vF[msk].mean(), vAs[msk].mean()
    lift = a / f - 1
    ok &= lift >= 0.05
    print(f"{nm:<10}{f:>+12.3f}{vA[msk].mean():>+14.3f}{a:>+19.3f}{lift:>+9.1%}")
f, a = vF.mean(), vAs.mean()
print(f"{'FULL':<10}{f:>+12.3f}{vA.mean():>+14.3f}{a:>+19.3f}{a/f-1:>+9.1%}")
print(f"\nVERDICT: {'PASS - replicates' if ok else 'FAIL - does not replicate'}"
      f"  (bar: >= +5% drawdown-matched in BOTH halves)")

print("\n" + "=" * 84)
print("WHERE THE DRAWDOWN IS")
print("=" * 84)
for nm, d, v in (("flat", dF, vF), ("armed", dA, vA)):
    eq = np.cumsum(v)
    under = eq - np.maximum.accumulate(eq)
    i = int(under.argmin())
    j = int(np.maximum.accumulate(eq)[:i + 1].argmax())
    print(f"{nm:<7} maxDD {under[i]:+.1f}R   peak {d[j]} -> trough {d[i]} "
          f"({i - j} days)   worst single day {v.min():+.1f}R on {d[int(v.argmin())]}")
    yr = defaultdict(list)
    for dd_, x in zip(d, v):
        yr[dd_[:4]].append(x)
    print("        per-year maxDD: " + "   ".join(
        f"{k} {dd(np.array(x)):+.1f}" for k, x in sorted(yr.items())))
