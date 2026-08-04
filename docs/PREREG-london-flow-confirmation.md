# PRE-REGISTRATION — LDN-FLOW-01: does order-flow confirmation at entry separate winners from losers?

Filed per `docs/VALIDATION-PROCESS.md` §1, **BEFORE any flow-vs-outcome number is
computed**. Git timestamp is the declaration. Trial family: **LDN-FLOW-01**.

Feasibility done first (`scripts/ldn_flow01_events.py`, and the flow-coverage count):
flow spans 2025-06-02 → 2026-07-20, giving **141 pooled events in 2025 and 107 in 2026** —
clear of the n ≥ 30 floor in both eras.

---

## 1. Why this test exists, and what it is NOT

The request is precise and worth restating: *order-flow confirmation **at entry**, used
properly, should remove unnecessary losers.* That is a real, falsifiable claim and it is
what is tested here.

**What this is not:** an attempt to rescue LDN-TRAP-01 or LDN-VWAP-01. Both are closed —
one FAIL, one INCONCLUSIVE with three findings against. Bolting filters onto a dead
candidate until one produces a positive number is the single most reliable way to
manufacture a fake edge, and it is precisely what DSR exists to deflate.

**What this is:** a test of *flow confirmation as a mechanism*, using those two closed
event sets as the substrate because they are the only well-characterised London fade
populations we have. The deliverable is knowledge about whether flow confirmation earns
its place at entry — which is useful to every future candidate regardless of what happens
to these two. If flow separates winners from losers here, that is a general finding worth
building on. If it does not, that is equally general and saves the desk from wiring flow
into entries on faith.

A PASS here does **not** revive either candidate. It authorises a fresh, properly
pre-registered candidate built on flow from the start.

## 2. The claim (falsifiable)

> Conditional on a London fade event having fired, order flow measured at or before the
> entry minute `t` carries information about whether that event goes on to win or lose.

Sharpened into the form actually tested: **each declared flow measure has non-zero rank
correlation with the event's outcome, in the declared direction, in both eras.**

## 3. Threshold-free by design — the key methodological commitment

The obvious way to run this is to pick a flow threshold ("enter only if delta > X") and
compare. **That is a search**, and with four measures and a handful of thresholds each it
would be a 20–40 trial sweep dressed up as one test.

Instead the primary is **threshold-free**:

- **Spearman rank correlation** ρ between each flow measure at `t` and the outcome.
- **AUC** for winner/loser separation, reported alongside.

If ρ ≈ 0, **no threshold on that measure can filter losers** — the question is answered
completely with zero threshold search. Only if a measure shows real separating power does
picking a cut become a legitimate follow-up, and that follow-up needs its own prereg.

One concession to practical readability, declared here and not searched: a **median
split** on each measure, reporting mean outcome in the top vs bottom half. The median is
the least-searched threshold that exists — it is not chosen to flatter anything.

## 4. The four flow measures — chosen on mechanism, declared with their signs

Data: `output/fp_minutes.parquet` — per-minute `b` (bid volume), `a` (ask volume), `vol`,
`delta`. **Sign convention verified empirically, not assumed:** `delta = b − a` and
correlates **+0.64** with same-minute (close − open) across 369,045 minutes, so positive
delta = aggressive buying. That check is recorded here because getting it backwards would
invert every conclusion.

Lookback **L = 5 minutes**, ending at and including `t`. Declared, not searched — 5 is the
standard footprint reading window. The event's own push is a median of 0–1 minutes, far
too short to measure anything across, which is why a fixed lookback is used at all.
Robustness at L = 3 and L = 10 is declared in §7 as a **fragility check, not as
additional hypotheses**.

`dir` = +1 if the trade is long, −1 short (the fade direction, already fixed by the event).

| # | measure | definition | mechanism | declared sign |
|---|---|---|---|---|
| 1 | **CONFIRM** | `delta[t] × dir` | Aggressive flow in the entry minute is going my way — the literal reading of "confirmation at entry" | **positive** ρ |
| 2 | **ABSORB** | `sum(delta[t−L+1 … t]) × dir` | Price pushed against me but net aggression over the window was on my side — the classic absorption/divergence signature | **positive** ρ |
| 3 | **EFFORT** | `sum(vol[t−L+1 … t]) / (range in ticks + 1)` | Size traded per tick of movement. Heavy effort, no result = someone is absorbing | **positive** ρ |
| 4 | **TRAPPED** | `−(delta[push-start minute]) × dir / (mean vol over L + 1)` | The minute that made the extreme was driven by one-sided aggression *against* my direction — those are the trapped participants whose exit is the fade | **positive** ρ |

All four are predicted **positive**. Any measure coming back significantly *negative* is
itself a finding and will be reported as such, not quietly dropped.

## 5. Causality audit (required, per `VERDICT-LDN-SWP-01.md` §4)

This is the section that killed LDN-SWP-01. Every flow measure reads minutes in
`[t−L+1, t]` — **at or before `t`**. The outcome is measured over `(t, window close]`.
The two intervals do not overlap at any point.

| variable | determined | before the outcome window? |
|---|---|---|
| event, direction, `t` | by the closed censuses, unchanged | ✅ |
| CONFIRM | minute `t` | ✅ |
| ABSORB, EFFORT | minutes `t−4 … t` | ✅ |
| TRAPPED | push-start minute, ≤ `t` | ✅ |
| outcome | over (`t`, window close] | ✅ |

`ldn_flow01_events.py` asserts `ts_push_start <= ts_entry` at build time. The test script
must additionally assert no flow minute used exceeds `t`.

## 6. Population, pooling and the outcome variable

**Substrate:** the LDN-TRAP-01 event set and the LDN-VWAP-01 gated event set, rebuilt
verbatim. `ldn_flow01_events.py` **asserts** the rebuild reproduces the published verdict
counts and means (161/−2.30, 89/−2.64, 77/−3.81, 38/−12.15) before anything proceeds. If
the event set drifts, the run aborts.

**Restricted to the flow span** — events before 2025-06-02 are dropped for want of data,
not for any property of theirs.

**Pooling:** the two candidates are pooled, because the question is about flow
confirmation as a general filter, and pooling buys the power that separate cells lack
(vwap alone is 42/31). To stop the wider-tailed candidate dominating, the outcome is
**standardised within candidate × era** (z-score) before pooling. Per-candidate splits are
reported as **descriptive companions, not verdict-eligible**.

**Eras:** discover 2025 (Jun–Dec), validate 2026 (Jan–Jul). Sign must agree in both.
**2023/24 sealed and untouched.** No holdout look.

## 7. Fragility check — runs FIRST, before the primary is read

- Spearman ρ recomputed with the 1, 3, 5 and 10 largest-|outcome| events removed.
- Recomputed at **L = 3 and L = 10**.

**A measure whose ρ changes sign at trim depth ≤ 3, or across the L ladder, is dead
regardless of its p-value.** Rank correlation is already outlier-resistant, so a sign flip
here means there is nothing there at all.

## 8. Decision rules — declared in advance

Let ρ₂₆ be the validate-era Spearman correlation for a given measure.

| outcome | condition |
|---|---|
| **PASS** | ρ in the declared (positive) direction at p ≤ 0.05 in **both** eras, fragility clear, n ≥ 30 per era |
| **FAIL** | validate-era 95% CI on ρ excludes the 2025 estimate **and** contains 0 — the equivalence form, not a bare failure to reject |
| **INCONCLUSIVE ON POWER** | neither; report the minimum detectable ρ at 80% power |

Absence is an equivalence claim. With n = 107 in the validate era the minimum detectable
ρ at 80% power is ≈ 0.27; that number will be reported explicitly so "no effect" can be
read as "no effect **larger than this**".

**Multiplicity:** four measures are tested. A single measure clearing p ≤ 0.05 with four
looks is a ~19% family-wise false-positive rate. Any PASS must therefore survive
**Holm–Bonferroni across the four**, and that is stated here rather than after seeing
which one wins.

## 9. Mandatory reporting

Event counts before and after the flow-span restriction; the full fragility ladder
whatever it shows; ρ, its CI, AUC and the median-split means for **all four** measures in
**both** eras — no measure dropped for being uninteresting; minimum detectable ρ; and the
per-candidate companion split.

## 10. Trial accounting

**8 trials** into LDN-FLOW-01 (4 measures × 2 era directions). London programme running
total: **24** (16 prior + 8). These count in the DSR denominator per §2.4. The median-split
readouts and per-candidate companions add **no** trials — they are re-descriptions of the
same eight statistics, not new tests.

## 11. Known limits

- **L0 structure only.** No stops, targets or costs. Flow confirmation is being tested as
  an *information* filter on an endpoint drift, not as a trade.
- Minute-aggregated footprint, not tick-by-tick. Real absorption reads at the price level
  within the minute; `fp_minutes` cannot see that. A null here does not clear tick-level
  or price-level footprint reading — it clears **minute-aggregate** flow only, and that
  limitation must be carried into any conclusion.
- The MBP-10 depth in `data/reference/depth_london/` is untouched here. Resting-liquidity
  measures (book imbalance, pulled bids, iceberg refill) are a **different family** needing
  their own prereg — they are not covered by any result from this one.
- The substrate is two closed London fade candidates. A finding here transfers to fades of
  a similar shape; it says nothing about continuation or breakout entries.
- NY-canon input-family overlap: **HIGH** — flow/depth is the canon's own input family.
  Anything that passes here goes straight to the pairwise correlation battery before it
  can be considered for deployment alongside the canon.
