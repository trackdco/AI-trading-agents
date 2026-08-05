---
date: 2026-08-06
kind: order-flow research (Part A) + test spec (Part B)
strategy: ash-unicorn-sb (AM1 09:45–10:15 ET only)
baseline: n=37, WR 40.5%, avg +0.486R, expectancy +0.434R net, maxDD 3.0R
---

# Order flow vs `ash-unicorn-sb` — what would confirm, what would warn

## The structure we are confirming — and why it is NOT a fade

Every previous order-flow test in this repo was against a **fade** (London: trap-fade,
VWAP-σ, level-defense). This is a different animal, and the difference drives everything
below. His sequence has **four** distinct moments, each with its own flow question:

| # | moment | the question flow must answer |
|---|---|---|
| 1 | **the sweep** — price takes a swing high/low | was this a genuine trap, or real initiative? |
| 2 | **the MSS + displacement** — price breaks structure the other way | is this move backed by aggression, or hollow? |
| 3 | **the retracement into the FVG** — the entry | is the pullback *passive*, or is opposing size returning? |
| 4 | the run to 2R | (management, out of scope) |

**Moment 3 is the one nobody tests, and it is the entry.** That makes it the highest-value
target here.

Critically, **moment 2 is what his ES rule is doing.** He requires the structure shift on ES
*before* NQ and enters on the ES tap `[qngA8aIfV0M @ 08:01]` — a cross-market check that the
displacement is real rather than an NQ-only wick. **We have no ES data, so delta on the
displacement leg is the closest available substitute for the component we cannot compute.**

---

## Tool-by-tool

### 1. Delta on the displacement leg — **RANK 1**

**Hypothesis.** A real displacement is *initiative*: aggressive orders lifting/hitting
through levels, so signed delta over the MSS leg should agree strongly with the trade
direction. A displacement made on thin or contrary delta is a wick — price moved because
nobody was there, not because anybody wanted it.

- **CONFIRM:** cumulative delta over the displacement leg is strongly in the trade's
  direction, normalised by the session's typical minute.
- **WARN (skip):** displacement delta is flat or *against* the trade direction — the break
  is mechanical, not participatory.

**Why rank 1:** it is the direct substitute for the missing ES confirmation, which is a
*declared component of his model*, not an addition to it. Everything else on this list is a
bolt-on; this one fills a hole.

### 2. Retracement participation during the FVG fill — **RANK 2**

**Hypothesis.** His entry is a pullback into a gap. A healthy pullback into an FVG is
**passive** — price drifts back on low volume because there is no supply/demand there (that
is *why* it is a gap). If the retracement arrives with heavy opposing aggression, the
displacement is being actively rejected and the gap will fail.

- **CONFIRM:** volume and opposing delta during the fill are LOW relative to the
  displacement leg — a drift, not a fight.
- **WARN (skip):** the fill carries volume comparable to or above the displacement, with
  delta against the trade — the other side has arrived.

**Why rank 2:** it is the most *specific to this entry mechanic* of anything on the list,
and it is untested anywhere in this repo. It is ranked below delta only because it is our
idea, not a stand-in for something he specifies.

### 3. CVD divergence at the sweep — **RANK 3**

**Hypothesis.** The canonical sweep-reversal read: price makes a new extreme but cumulative
delta does not, so the extreme was made without conviction.

- **CONFIRM:** price takes the level, CVD fails to make a matching extreme → trapped
  aggressors.
- **WARN:** CVD trends with price straight through the sweep → this is continuation, and the
  "sweep" is a breakout. Skip.

**Why rank 3, not 1:** the WARN branch here is genuinely valuable — it separates a sweep from
a breakout — but the MSS gate already does much of that work downstream (a real breakout
rarely then breaks structure the other way). Expect overlap with the existing filter rather
than new information.

### 4. Footprint absorption at the sweep level — **RANK 4**

**Hypothesis.** At the swept level, heavy aggressive volume with no price progress = a
passive participant absorbing, which is who reverses price.

- **CONFIRM:** high volume at the swept price with minimal excursion beyond it.
- **WARN:** the level is taken on modest volume with easy continuation — nobody defended it.

**Why rank 4 — prior evidence against.** We have measured absorption **twice** and it was
null both times: `LDN-FLOW-01` (minute-aggregate, AUC 0.45–0.56) and `LDN-DEF-01`
(price-level, all three measures FAIL, PBO 0.891 on the arm set). Both were on *fades*, so
this is not a settled question for a sweep-then-displace structure — but the base rate is
poor and it should not jump the queue ahead of untested ideas.

### 5. Resting-liquidity heatmap — **RANK 5, and BLOCKED**

**Hypothesis.** A resting wall beyond the sweep explains why the sweep failed; its
disappearance explains why the displacement ran.

**Blocked twice over:**
1. **The depth look-ahead defect** (`docs/FINDING-depth-snapshot-lookahead.md`): condensed
   snapshots are stamped at the start of a minute but hold end-of-minute state. NY depth
   measures **15.5 ticks** from the bar open vs **1.0 tick** from the close. Using it would
   read the book *after* the move it is meant to predict.
2. **One snapshot per minute** cannot see placement, cancellation or refill — the dynamics
   that make a heatmap informative. Static imbalance only.

Data *exists* (252 days covering 09:45–10:15 ET). It is unusable until the condenser is
fixed. **Marked: blocked — needs re-stamped depth condense.**

### 6. Volume profile / VWAP — **RANK 6, does not fit**

His levels are **swing highs/lows and session extremes**. Volume profile levels (POC, VA
edges) are a *different framework's* levels. Adding a VWAP or POC filter would not be
confirming his setup — it would be substituting someone else's.

Also directly measured against: `LDN-VT-01` found naked POCs are touched **49.1%** of the
time versus **50.9%** for an arbitrary level the same distance away. The profile map has no
demonstrated pull in this repo's own data.

**This is the "bolt on every indicator" failure mode and it is being declined explicitly.**

---

## Ranking summary

| rank | tool | testable now? |
|---|---|---|
| **1** | **displacement delta** | ✅ n=29 |
| **2** | **retracement participation** | ✅ n=29 |
| 3 | CVD divergence at the sweep | ✅ n=29 (not run — see below) |
| 4 | footprint absorption at the level | ✅ n=29, but base rate poor |
| 5 | resting-liquidity heatmap | ❌ **blocked** |
| 6 | volume profile / VWAP | ❌ declined — wrong framework |

Only ranks 1–2 are tested (Part B), per the brief's "top 1–2 tools".

---

## DATA REQUIREMENTS — stated exactly

| tool | data needed | granularity | held? |
|---|---|---|---|
| delta / CVD | aggressor-tagged trades, aggregated | per-minute signed volume | ✅ `output/fp_minutes.parquet`, **2025-06-01 → 2026-07-19** |
| retracement participation | same | per-minute volume + delta | ✅ same |
| footprint absorption | aggressor-tagged trades **by price level** | per (minute, price, side) | ✅ `data/reference/cvd/footprint_*.parquet`, same span |
| heatmap / resting liquidity | full order-book event stream (MBP/MBO) | **tick-level**, not snapshots | ❌ we hold 1 snapshot/min, and it is mis-stamped |
| volume profile / VWAP | OHLCV | 1-minute | ✅ (declined on fit, not data) |

### ⚠️ The binding constraint: **flow starts 2025-06-01, the baseline starts 2025-03-07**

**29 of the 37 baseline trades** fall inside the flow span. Any filtered result is measured
on **n=29 — below the n≥30 floor** — and is not comparable like-for-like to the 37-trade
baseline. Part B therefore reports the raw baseline **restricted to the same 29 trades** as
the honest comparator, alongside the full 37.

**To test at full sample we would need:** aggressor-tagged trade data for NQ covering
**2025-01-01 → 2025-05-31** — roughly 5 months, same Databento `GLBX.MDP3` trades feed the
existing footprint files came from.


---

# PART B — RESULTS

Ran 2026-08-06. Trades: `ash-unicorn-sb-orderflow-trades.csv`.

| filter | n | kept | win rate | avg R | expectancy | total R | maxDD |
|---|---|---|---|---|---|---|---|
| RAW baseline (all 37) | 37 | — | 40.5% | +0.486 | +0.434 | +18.0R | 3.0R |
| **RAW (29 flow-covered) ← comparator** | 29 | 100% | 44.8% | +0.621 | +0.563 | +18.0R | 2.0R |
| **F1** displacement delta > 0 | 29 | **100%** | 44.8% | +0.621 | +0.563 | +18.0R | 2.0R |
| **F2** retrace vol < displacement vol | **15** | **52%** | **73.3%** | **+1.333** | **+1.277** | +20.0R | **1.0R** |
| F1 + F2 | 15 | 52% | 73.3% | +1.333 | +1.277 | +20.0R | 1.0R |

## F1 — displacement delta: a VACUOUS filter, and that is the finding

**It removed zero trades.** All 29 setups have positive displacement delta (range +0.07 to
+1.01). The check is a tautology: the MSS + displacement gate already *requires* a
directional break, so signed delta over that leg agrees by construction.

**This is worth knowing.** The confirmation everyone reaches for first — "is the move backed
by delta?" — carries **no information beyond the price structure that defined the event**.
It is not that delta is uninformative; it is that this event definition has already used it.

It also means **delta cannot substitute for the missing ES check.** ES adds information
because it is a *different instrument*; NQ delta over an NQ displacement is not independent.

## F2 — retracement participation: the real result, on a thin sample

Removes 14 of 29. Kept: **73.3% WR, +1.333 avg R.** Rejected: **14.3% WR, −0.143 avg R.**

Binomial vs the 44.8% base rate: **11/15 wins, p = 0.0247.**

**Era split — both directions agree, the first filter in this repo to manage it:**

| era | all | F2-filtered |
|---|---|---|
| 2025 | n=19, WR 42%, +0.474R | **n=11, WR 64%, +1.091R** |
| 2026 | n=10, WR 50%, +0.900R | **n=4, WR 100%, +2.000R** |

### But read the total-R column before getting excited

| | n | total R |
|---|---|---|
| kept | 15 | **+20.0R** |
| rejected | 14 | **−2.0R** |
| all | 29 | +18.0R |

**The filter adds +2R of total profit.** It nearly doubles per-trade expectancy, but it does
so by removing 14 trades that collectively lost 2R — it *concentrates* the existing edge, it
does not create much new one.

Whether that is worth having depends on the account: for a funded account with a daily loss
limit and a consistency rule, halving trade count while removing the losers is valuable. In
raw R it is marginal.

## Honest limits

1. **n=15 in the filtered arm.** Half the n≥30 floor. 2026 holds **4 trades**. The 100% WR
   there is 4/4 and means nothing on its own.
2. **The comparator is 29, not 37** — flow starts 2025-06-01. Note the flow-covered subset
   already scores better than the full 37 (44.8% vs 40.5%), so part of the apparent lift is
   sample restriction, not filtering. **The honest comparison is 44.8% → 73.3%, not
   40.5% → 73.3%.**
3. **Trials: 2 filters × 2 eras = 4 arms**, to be appended to the merged ledger. The
   deflation bar at N=58 is +0.5636 and this has not been graded against it.
4. **Threshold not searched** — F2's cut is 1.0, the natural boundary (fill volume below
   displacement volume). No sweep was run over the ratio, deliberately.

## What would settle it

- **Aggressor-tagged trades for 2025-01-01 → 2025-05-31** would take the comparator from 29
  to 37 and the filtered arm from 15 to ~19.
- **A fixed depth condense** would unblock rank 5 (heatmap).
- **ES 1-minute** remains the single biggest gap — it is a component of his model, and F1
  demonstrates that NQ delta cannot stand in for it.

---

# REVISION 2026-08-07 — BACKFILL AUDIT: no re-run warranted

`scripts/ash_flow_coverage_audit.py`

**Result: 0 new flow-covered trades. The 29-trade numbers above stand unchanged.**

A backfill pass was run to recover any trade sitting inside owned aggressor-tagged data
that had never had derivations built. The audit checked coverage from both ends — the raw
`data/reference/cvd/footprint_*.parquet` files (which define the owned span) and the derived
`output/fp_minutes.parquet` frame the filters actually consume.

| | |
|---|---|
| trades in the log | 37 (2025-03-07 → 2026-07-15) |
| inside the owned aggressor span | **29** |
| of those, already derived | **29** |
| **recoverable (in span, no flow)** | **0** |
| before the owned span (unrecoverable) | 8 (2025-03-07 → 2025-05-29) |

`has_flow` and `day_in_fp` agree on all 37 rows. No trade was missing derivations for a
computational reason; the split is purely calendar. **29 was never a processing shortfall —
it is the count of trades that fall inside the data.**

## Two corrections to the assumed owned window

The brief assumed the owned span was **2025-07-01 → 2026-07-31**. The files say otherwise, in
both directions:

- **It starts 2025-06-01, not 2025-07-01.** `footprint_q3_2025.parquet` opens at
  2025-06-01 18:00 ET. That extra month is already banked — it is where the 2025-06-10 and
  2025-06-30 trades' flow came from. Widening the assumed window to the true one adds nothing
  because the derivation already used the true one.
- **It ends 2026-07-19, not 2026-07-31.** Moot: `nq_1m_master.parquet` ends 2026-07-15, so no
  trade can exist in the difference.

## The ceiling, stated

**Flow-covered can never exceed the number of trades falling inside the owned span.** Both
numbers are 29, so the sample is terminal within owned data. The eight uncovered trades
(2025-03-07 → 2025-05-29) sit before *every* non-sealed footprint file we hold and cannot be
recovered by reprocessing — only by a Databento `GLBX.MDP3` trades pull for a span that
predates all of them. No such pull was attempted (no `databento` client and no API key are
present in this environment), and no flow value was interpolated or imputed for any of them.

Even at the ceiling, **n = 29 with 8 losers** is well under the ~49 the autopsy's power
analysis needs for a *large* effect. At the observed 27.3 trades/year, +20 flow-covered
trades is **~9 months of forward accumulation**; the ~87 needed for a *medium* effect is
**~2.1 years**.

**Stage 4 was not re-run.** Re-running the identical filters on an identical 29-trade set
would have reproduced the table above to the decimal while creating the appearance of
independent confirmation.
