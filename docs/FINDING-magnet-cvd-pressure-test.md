# FINDING — the magnet+CVD "60% lead" does not survive pressure-testing

**Author:** engine lane (Brake session, 20 Jul 2026). **Verdict: the magnet+CVD April result is a
fragile, outlier-driven, n=10, in-sample artifact. Do NOT buy Feb/Mar/May depth to chase it yet.**

Reproduce: `python3 scripts/magnet_cvd_pressure_test.py` **from the `claude/getting-started-6lwnvs`
worktree** (needs its journal + CVD + April depth). This branch (`brake-43x58e`) holds the script and
this write-up only; the data + champion pipeline live on getting-started.

## What was claimed (data-lane handoff)
magnet (resting wall on the target side) + CVD-confirm = **10 trades, 60% win, +$3,345, +1.01R** in
April. Billed as "the first 60% through selection" and the make-or-break lead.

## Reproduction
- Full Feb–Jul component numbers reproduce exactly (real-stop ≥6pt = 117t / 39% / +$14,512 / +0.47R;
  CVD+real-stop = 73t / 42% / +0.65R).
- The April magnet number **only reproduces after a bug fix**: `selection_signal_test.py:41` compared a
  cached DataFrame to the string `"miss"` (`if d == "miss"`) → `ValueError`. Fixed to
  `if isinstance(d, str)`. **The committed script crashes on the magnet path — the headline 60% came
  from code that doesn't currently run.** Port the one-line fix to getting-started.

## The three tests (all fail to support the lead)
1. **Outlier concentration.** The single best trade (Apr 30, +7.59R, +$1,665) is **50% of total P&L**.
   Remove it → avg collapses **+1.01R → +0.28R**. Median trade is **+0.47R**. The "money" is one tail.
2. **Win-rate CI.** 60% at n=10 (6W/4L) → Wilson 95% CI **[31%, 83%]**. The 33% base rate is inside it;
   60% is statistically indistinguishable from baseline at this sample size.
3. **Permutation (50k random 10-of-30 April subsets).**
   - P(random win% ≥ 60%) = **0.039** (win-rate selection looks mildly non-random)
   - P(random avgR ≥ 1.01) = **0.105** ← on expectancy (the metric the project optimizes), **not
     significant**. A random draw grabs the Apr-30 monster ~10% of the time and beats it.

## Does the magnet justify the depth buy?
| April subset | n | win | P&L | avgR | needs depth? |
|---|--:|--:|--:|--:|:--:|
| magnet + CVD | 10 | 60% | +$3,345 | +1.01R | **yes** |
| **CVD + real-stop** | 17 | 47% | +$3,055 | **+0.73R** | **no** |
| magnet + CVD + real-stop | 8 | 75% | +$3,455 | +1.67R | yes (n=8) |

The **depth-free** CVD+real-stop combo already gets +0.73R on 17 April trades and **+0.65R on 73 trades
full Feb–Jul**. The magnet's marginal lift over it is the fragile n=10, one-outlier part.

## Recommendation (for Angus)
- **Lean on the robust, depth-free signal:** CVD-confirm + ≥6pt real-stop (+0.65R, n=73, full sample).
  It reproduces, needs no purchase, and is the actual engine of the edge.
- **Hold off on the Feb/Mar/May depth buy** to chase the magnet — current evidence doesn't justify the
  cost. The magnet is *not disproven* (n=10 can't disprove either), but it is *not supported*.
- If depth is cheap, one additional month is a reasonable cheap confirmation — but the P&L case today
  rests on the depth-free combo, not the magnet.
- Carry the project's own frame forward: **optimize expectancy, not win rate.** The 60% headline is a
  win-rate mirage on one trade; expectancy says the magnet adds nothing significant yet.

---

## Follow-up — 09:45-10:15 window with proper absorption/exhaustion (Brake ask)

`python3 scripts/window_0945_1015_absorb_exhaust.py` (from getting-started worktree). Absorption/
exhaustion implemented properly (not the crude target-wall magnet): absorption = large resting wall
on the REJECTION side hit by opposing CVD and holding; exhaustion = CVD divergence over the 5-min
approach.

**Sample wall:** the window has only **5 April trades with depth** (28 full Feb-Jul). Heatmap =
April-only, so any absorption result is anecdotal.

Depth-free signals, full 28-trade window:
| cut | n | win | P&L | avgR |
|---|--:|--:|--:|--:|
| baseline | 28 | 43% | +$4,852 | **+0.48R** |
| CVD confirm | 11 | 36% | +$2,795 | +0.68R |
| exhaustion (CVD div) | 4 | 75% | +$3,690 | +1.69R |
| exhaustion + CVD | 2 | 100% | +$2,920 | +3.17R |
| real stop >=6pt | 23 | 48% | +$4,502 | +0.51R |

**Heatmap absorption fired on 0 of 5 April trades** — April's book is too thin (p99 size = 9) for a
MAG=15 wall to exist; absorption is untestable here, not just small-n.

**Conclusion:** the durable finding is the **window itself** — 09:45-10:15 baseline is +0.48R (n=28)
vs the champion's +0.22R overall, present in every month. Exhaustion's 75%/+1.69R is n=4 (its +CVD
combo n=2) — the same small-n mirage as the magnet; a hint to test on more data, not a result.
Recommend testing "prefer 09:45-10:15" as a standalone depth-free TIME rule on the full sample +
OOS, rather than stacking order-flow filters that collapse n to single digits.
