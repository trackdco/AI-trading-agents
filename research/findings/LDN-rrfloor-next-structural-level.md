---
date: 2026-08-06
status: FINDING — the 2R floor was not what was wrong with London. Cutting it to the next
  structural level does exactly what it was asked to do mechanically and earns nothing:
  -3.69 -> -3.64 net pt/trade, +0.23 pt paired (T +0.84), and the gain does not survive
  into 2026. Neither arm is tradeable.
tags: [london, canon, rr_floor, targets, prop-objective, era-consistency, self-correction]
sources: ["output/l2_outcomes_london_fit_EC_rr0.parquet", "output/l2_outcomes_london_fit_EC.parquet",
          "output/london_rrfloor_compare.md", "scripts/l2_london_rrfloor_compare.py",
          "docs/HANDOFF-london-displacement-2026-08-06.md"]
---

# Cutting the 2R floor: the target-hit rate went up 10x and it bought nothing

ANGUS: *"fuck why is the 2 r floor instated. that needs to get cut"* ... *"btw it should be
the next structural level not 2r floor minimum etc"*.

Executed on the full fit book — 264 sessions, 2025-06-02 → 2026-07-15, EC displacement
entries, deduped `vs_first`, every trigger through the real `simulate()`. Handoff task #1.

## The ruling was right about the mechanism and it still does not pay

| | 2R floor (shipped) | next structural (rr0) |
|---|---:|---:|
| N setups | 719 | 667 |
| **net pt/trade** | **−3.69** | **−3.64** |
| T | −6.06 | −6.01 |
| **green days** | **32%** | **35%** |
| green days, all 264 sessions | 27% | 30% |
| median day | −12.1 pt | −8.1 pt |
| worst rolling 10d | −368 pt | **−414 pt** |
| **target-hit (pure)** | **2.9%** | **29.2%** |
| target-hit (incl. partial+target) | 13.2% | 42.3% |
| median RR at order | 3.07 | 1.52 |
| mean R | −0.146 | −0.146 |
| total | −2,656 pt | −2,427 pt |

The floor change did what Angus said it would. The trade now targets the next structural
level — median ordered RR falls 3.07 → 1.52 — and it reaches that target **ten times more
often**, 2.9% → 29.2%.

The book still loses three and a half points a trade.

## Why a 10x better hit rate is worth nothing

**A target hit used to be worth +21.14 pt net. Now it is worth +2.99 pt** (median +1.25).
The rate rose by exactly as much as the prize fell. That is not a coincidence to be
explained away — it is what pulling a target nearer *does*, and it is why a target-hit rate
quoted without the value of a hit is not a result.

The second half of the explanation is that the floor never governed the losing side:

| exit reason | 2R floor | rr0 |
|---|---:|---:|
| stop | 46.7% | 45.1% |
| partial+stop | 40.1% | 12.6% |
| partial+target | 10.3% | 13.0% |
| target | 2.9% | 29.2% |

**Flat stop-outs barely move (46.7% → 45.1%).** Almost half of London displacement entries
die without ever reaching a first structure, and no target policy can reach them. All the
churn is in the middle: trades that used to take a partial and then stop now simply hit a
nearer target instead.

Every ordered-RR bucket is negative, and the nearest targets are the *worst* ones:

| ordered RR | 2R floor | rr0 |
|---|---:|---:|
| <0.5R | — | **−4.83** (22%) |
| 0.5–1R | — | −2.36 (17%) |
| 1–1.5R | — | −2.29 (11%) |
| 1.5–2R | −7.22 (1%) | −3.29 (10%) |
| 2–3R | −4.29 (47%) | −5.78 (17%) |
| >3R | −3.05 (51%) | −2.70 (23%) |

Floor 0 admits a long tail of degenerate targets: **21% of the rr0 book is ordered with a
target under 0.5R**, p10 is 0.14R. Those hit 72% of the time and lose the most per trade.
A 0.4R target against a 1R stop needs a ~71% win rate before friction to break even.

## Paired, it is indistinguishable from zero

The two arms trade different populations (the floor moves `vetoed_rr_floor`, 95 → 284 on
displacements), so the headline difference mixes policy with composition. On the **626
setups both arms traded**, each trade its own control:

- per-trade delta **+0.23 pt**, paired **T +0.84**
- **66.3% of outcomes are byte-identical** — the floor changed nothing at all for two thirds
  of the book
- rr0 better on 18.2%, worse on 15.5%

## It does not survive out of sample — the thing that actually decides it

| | 2025 (150 sessions) | 2026 (114 sessions) |
|---|---|---|
| 2R floor | −2.44 pt, 31% green | −5.82 pt, 34% green |
| **rr0** | **−1.72 pt, 37% green** | **−6.78 pt, 32% green** |
| verdict | improves | **degrades** |

2025 improves on every line — net, green days, worst-10d (−315 → −254). 2026 gets worse on
every line — net, green days, worst-10d (−368 → −408), mean R (−0.215 → −0.269).

Discovery era up, validation era down. That is burn-list §8.1's signature ("92 filter cells,
not one net-positive in both eras") and it is the reason this is a kill rather than a
partial win. Had only 2025 been run, this would read as a success.

## The 3-session smoke test was the wrong sign

Handoff §5 recorded a 3-session probe at **+243 pt (rr0) vs −273 pt (2R)**. On 264 sessions
it is **−2,427 vs −2,656**. The handoff called it correctly at the time — *"three sessions
is not a result"* — and it was right to run the full book rather than act on it.

## Three corrections to the handoff, all load-bearing

1. **§3.2 — `working_target != target_level` on 100% of outcomes is NOT evidence the walkout
   moved the target.** `working = level − sgn*front_run` unconditionally, so that column
   differs on 100% of outcomes in *both* arms, including the one with walkout off. Verified:
   `|working − target_level|` sits within half a tick of `front_run` (2.5) on every outcome
   in both books. The walkout's real signature is the RR distribution (min 2.00 vs 0.00).

2. **§5 — the partial did not move.** `rr_floor_partial` is gated to
   `mgmt_variant in ("V5","V6")` (`src/backtest/engine.py:990`); London runs **V8**, where
   the partial books at the first structure regardless. Setting `rr_floor_partial` to
   `min(0, 1.5) = 0` was inert. The floor moved the target only — which is *why* the exit
   mix could shift so far without the stop share moving.

3. **§3.2 — "142 trades vetoed by `rr_floor`"** is the whole book. With B2 removed
   (§3.1) the displacement-only figure is **95**, rising to **284** under floor 0 —
   the floor-0 veto catches first-menu levels that sit behind the entry, which the
   walkout used to step past.

Also worth recording: the census is complete and reconciles (2,657 displacement candidates
in both arms), and the engine held both floors exactly — RR-at-order min **2.00** in the 2R
arm, **0.00** in the rr0 arm, neither ever violated.

## Method note — the dedup had to be re-derived, not inherited

`build_l2_outcomes_london` joins the setup flags off L1, which grouped the **E3 limit** walk.
The rr0 arm vetoes a different set again, so **302 non-outcome rows arrived carrying
`vs_first`** — 302 setups that would have been represented by a trigger this arm never
traded, silently. `l2_london_dedup_arm --rr-floor 0` re-derives it (1,347 VWAP-ruled setups
vs the 2R arm's 1,399); `l2_london_rrfloor_compare` now refuses to score a book that has
not been.

## What this closes and what it opens

**Closed.** The 2R floor is not why London loses. It is not worth another arm: it is
R-neutral (mean R −0.146 in both), paired-insignificant, and era-inconsistent. Angus's
instinct that the floor was distorting target selection was correct — median ordered RR of
**3.07** on a nominal "2R minimum" proves the walkout was choosing ~3R targets — but fixing
it does not reach the problem.

**Open, and where the evidence now points.** ~45% of displacement entries stop out flat
regardless of target policy, and that share is invariant to everything tested here. The
losing side is the whole question. Two facts already in hand and not yet used:

- EC market entries slip a median **+0.75 pt** past their reference, p90 **+7.25 pt**,
  against a median risk of 11.5 pt. Identical in both arms, so it did not affect this
  comparison — but it is a large uncosted drag on the entry itself.
- `daily_context` (handoff §6) is built, causal, and still unjoined. Handoff §12 step 2.

**Neither arm goes near the prop bar.** Both fail net (≥4pt), T (≥2), green (≥55%) and both
years red. Nothing here is shippable; this settles a mechanism, not a strategy.

---

## ADDENDUM 2026-08-07 — the floor result was redistributive, not neutral

Prompted by Angus asking why the profitable population only yields ~1.7 pt/day. Splitting
BOTH books by whether price ever retraced to the trigger level (L1's E3 walk = the limit
that would or would not have filled):

| population | 2R floor | rr0 (nearest level) | change |
|---|---:|---:|---:|
| **RAN (never retraced)** | 104 tr, **+8.06**/tr, **+839 pt** | 99 tr, **+4.58**/tr, **+453 pt** | **−386 pt** |
| **RETRACED** | 615 tr, −5.68/tr, −3,495 pt | 568 tr, −5.07/tr, −2,880 pt | **+614 pt** |

Cutting the floor took **386 pt off the population that pays** and gave **614 pt back to the
one that does not**. Net +228 — precisely the flat headline (−2,656 → −2,427).

So "the floor changed nothing" understates it. The floor change is REDISTRIBUTIVE: a nearer
target pays the trades that retrace (banked before price comes back) and caps the trades
that run. They cancel because the losing population is 6× larger. Mechanically visible in
the exit mix of the RAN population alone — under the 2R floor it is 56% partial+stop / 32%
partial+target with a median ordered RR of 3.02; under rr0 it is 54% target / 28%
partial+target at RR 1.16. Same trades, cashed out earlier.

**The correct target policy is conditional on which population the trade is in** — far for
runners, near for retracers — and that is the same unresolvable-at-entry question as
everything else in this file. A single global floor cannot be right for both, which is why
every global setting of it measures as a wash.

### Why the ceiling is what it is

Even with perfect foresight and the BETTER (2R) target policy, the RAN population yields
**+839 pt over 264 sessions = 3.18 pt/day** on ~88 traded sessions. Against Angus's stated
50 pt/day:

- 50 pt/day at +8.06/trade needs **~6.2 trades/day** of that quality. London supplies
  **0.39/day**. Short by 16×.
- If EVERY London displacement setup (3.20/day) performed like the best population, the
  session would yield **~26 pt/day** — still half the objective, in a scenario that cannot
  occur.

This is a session-size constraint, not a strategy defect: a 2-hour window yielding ~3
setups/day cannot reach 50 pt/day under any target policy. Recorded because it bounds every
future London arm before it is run, and it is the strongest argument for London never being
a standalone answer to the objective.
