# PRE-REGISTRATION — NYA-LVL-01 stage 2 — geometry, then the discriminant

**Committed BEFORE any of it runs.** Authorised by Angus 2026-08-05 off the stage-1 raw
card (`output/nya_lvl_census.md`, `research/FUNNEL.md`). Fit span only.

---

## PLAIN LANGUAGE — what this stage does and why in this order

Stage 1 found the trade happens constantly — 4,759 of them — and every version loses
money. It also found *why*, and it is not subtle:

- **Half of all winners never go a single tick against you.**
- **Half of all losers never show a profit at all.**
- Winners run to **+27**. Losers run to **−62**, and one in ten to **−159**.

And what the taught rules do with that: **take 16 off the winners and give 48 to the
losers.** The arithmetic is backwards. That is why a 61% win rate produces a losing
strategy.

So this stage fixes the arithmetic first, and only then looks for an edge. Running the
order-flow tests before this would tell us which trades survive a bad stop — not which
trades are good. Those are different questions and only the second one is worth
anything.

---

## Stage 2a — the geometry grid

**Declared default, named on mechanism BEFORE any numbers (§6.0.1):**
**stop 20 points, target 30 points.**

The reasoning, and it comes from the stage-1 MFE/MAE, not from a search: winners have a
median adverse excursion of **0.0** and a 10th-percentile of **−34.8**, so a 20-point
stop sits beyond where most winners ever go while cutting the median loser (−62.4) at
under a third of its full run. Winners' median favourable excursion is **+27.1**, so a
30-point target sits just past where the median winner gets to. That is 1.5R.

**This default holds regardless of what the grid shows.** No cell may displace it on
in-sample rank. Displacement requires PBO < 0.5 on the arm matrix **and** holdout
adjudication, per §6.0.1 — and no holdout look is spent at this stage.

**The declared grid — frozen here, it may not grow:**

| axis | values |
|---|---|
| stop (points) | 10, 15, 20, 25, 30, 40 |
| target (points) | 15, 20, 25, 30, 40, 50 |
| special exits | `T_LADDER` (next level), `TRAIL_BE` (stop to break-even at +1R, then trail 15pts) |

= **6 × 8 = 48 cells.** Run on Version B (raw touch — his current teaching and the larger
sample).

## Stage 2b — the early-cut overlay (what losers share that winners don't)

Stage 1's cleanest signal: **losers have a median favourable excursion of exactly 0.0.**
They never go green. So the simplest possible discriminant is time-to-green.

**Declared arms, applied ONLY to the default geometry** so the search does not multiply:
exit at market if the trade is not green at **t+5**, **t+15**, **t+30** minutes.
**3 arms.**

## Stage 2c — Version A vs Version B at the default geometry

**1 comparison.** Stage 1 showed break-then-retest (PF 0.87, n=1,133) beating raw touch
(PF 0.43, n=4,759). Both remain taught arms and neither is promoted here.

**Total declared arms this stage: 48 + 3 + 1 = 52.** The null below is family-wise across
all 52 by construction.

---

## The null — placebo levels, and it tests the family's actual premise

The premise of this whole family is that **those six lines are special**. The honest null
is therefore not a shuffle of outcomes but a shuffle of *levels*:

> For each session, replace the six real levels with **six random price levels drawn
> uniformly from that day's pre-RTH observed range**, keep the touch grammar identical,
> keep the entry rule identical, and **re-run the entire 52-arm search**. Record the best
> cell found.

If random lines in the same price zone produce the same best-cell result as the real six,
then nothing about pre-market and prior-day structure is doing any work, and the family
is a geometry exercise rather than a strategy.

- **Statistic:** the best R-per-trade across all 52 arms (family-wise max, per §2.3 —
  re-running the *search* under the null, not re-scoring the winner).
- **200 permutations**, seed `20260805`. §2.3 proposes ≥1,000; this null requires a full
  re-scan of every session per permutation, so 200 is the honest compute budget and the
  limitation is stated on the card rather than hidden.
- **Bar: family-wise p ≤ 0.01** (§2.3).

## Era discipline (§2.1)

- **Discover 2025, validate 2026.**
- **Inverse pass required:** discover 2026, validate 2025. A cell survives only if it
  holds in **both** directions. The swap doubles the trial count and both passes go on
  the ledger.
- **Half-year reporting mandatory** (§5.11-5): 2025H1/H2, 2026H1/H2.
- **§2.2 minimum n:** ≥30 per era cell for a direction claim, ≥100 pooled for a magnitude
  claim. Cells below those are reported as underpowered, never as confirmation.
- **Effective N:** stage 1 measured ~70% unique entry timing, so significance uses the
  overlap-corrected count, not the raw 4,759.

## Costs

1.0 pt base and 2.0 pt strict, both always reported. Conservative intrabar: stop checked
before target. **A cell that only works at base cost does not count as working.**

## What may and may not come out of this stage

- **It may not promote anything.** The default is frozen and only §6.0.1's route can move
  it.
- **It may not kill the family** — the full declared search (flow, depth, conviction) is
  not complete until stage 3.
- It **can** establish whether the six levels beat random lines, which is the premise
  test, and whether a sane geometry turns the raw negative into something worth
  conditioning.

## Spans

Fit **2025-06-03 → 2026-07-15** only. **Sealed 2023/24 NOT touched. Holdout look: NO.**

## Artifacts

`scripts/nya_lvl_geometry.py` · `output/nya_lvl_geometry.md` · trials to
`output/trial_ledger.parquet` · card refreshed in `research/FUNNEL.md`.
