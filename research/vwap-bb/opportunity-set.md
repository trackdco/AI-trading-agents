# OPPORTUNITY SET CHARACTERISATION — VWAP/BB

**Run completed: 45,214 candidate records, 496 sessions, 0 failures, 1.3 minutes.**

**Read this first: the R-normalised half of this run is invalid and is quarantined below.**
The spec's own geometry — E1 entry at the BB MA, stop one tick beyond the trigger wick —
produces a **median R of 3.12 points against the hand log's 32.8**, with 17.9% of candidates
under 1 point and a minimum of 0.0125. Every `_R` field divides by that, so MFE/MAE in R,
the R-threshold hit rates, and the truncated-winner number are denominator artefacts, not
measurements of the opportunity set.

Everything denominated in **points, minutes or counts is valid** and is reported normally.

Measurement pass, not a backtest. No equity, no P&L, no selector adopted, no threshold tuned,
no configuration ranked. Workbench only — the holdout was never addressed and the guard
(`assert_workbench`, raising `HoldoutBreach`) was armed on every session read.
**N_trials remains 0.**

---

## 1. The invalidating defect

Gate 4 froze the stop buffer at **1 tick beyond the wick extreme** `[FIAT]`, reasoning from
§5.4's "beyond … never widened". spec-1 Step 8 names **E1** (limit at the BB MA) as the
default entry. Put together on a real trigger candle:

- the cluster sits at the BB MA (98% of candidates have `bb` in the cluster)
- the trigger candle's wick penetrates that cluster and closes back across it
- so the entry (BB MA) sits *inside* the candle, a short distance from its extreme
- R = |entry − wick extreme| − 1 tick, which collapses whenever penetration is shallow

Measured, reading A:

| | p5 | p25 | **p50** | p75 | p95 | min |
|---|---|---|---|---|---|---|
| R, points | 0.36 | 1.39 | **3.12** | 5.79 | 11.85 | **0.0125** |

Hand-log **hand-marked** stops: **8.25–65.0 points, median 32.8**. The spec geometry is roughly
**10× tighter than the human it was written to formalise.**

The consequence for the excursion fields is mechanical:

| subset | median MFE in R |
|---|---|
| R < 1 point | **21.8** |
| R > 10 points | 1.64 |
| all | 4.01 |

A median MFE of 4.01R against a 1R stop is not a property of the market. It is 1/R.

**This is not purely an implementation bug.** Two readings are available and I am not choosing
between them:

1. *My freeze is wrong.* "One tick beyond" is too literal; Angus placed stops structurally
   wider, and the correct buffer is something the spec does not state.
2. *The pairing is wrong.* E1 (entry at the level) with a stop just past a shallow wick is a
   degenerate combination in any reading, and the spec contains no minimum-stop rule to
   prevent it.

Either way it is a **gate 4 finding, not a measurement finding**, and it lands on the same
gate that is already reopened.

**Knock-on: the RR floor is not doing the work it appears to.** With median R = 3.12 points,
a target 4.7 points away clears 1.5R. Median `available_R_to_spec_target` is **4.84R**, and
26.4% of candidates exceed 10R. The floor is not selecting for good targets — it is selecting
for tiny stops. In the signal count it appeared to remove ~25% of candidates; that reduction
was real but it was not screening on target quality.

---

## 2. Valid results — points, minutes and counts

### Population

| reading | candidates | median R (pts) | median MFE (pts) | median MAE (pts) | hit spec stop | unresolved at close |
|---|---|---|---|---|---|---|
| A | 12,595 | 3.12 | 12.86 | 2.75 | 54.1% | 0.4% |
| B | 5,622 | 4.96 | 15.05 | 3.06 | 48.0% | 0.6% |
| C | 2,766 | 5.08 | 15.34 | 2.78 | 45.6% | 0.8% |
| D | 1,598 | 4.90 | 14.94 | 2.32 | 44.2% | 0.8% |

Per warm-up treatment; 22,581 records under `prior`, 22,633 under `rth`.

### E. Survival curve (reading A, n = 12,595)

| resolved within | cumulative |
|---|---|
| 5 min | **76.9%** |
| 10 min | 88.9% |
| 15 min | 93.8% |
| 30 min | 98.0% |
| 60 min | 99.3% |
| unresolved at close | **0.4%** |

**Valid as measured, but do not read it as the strategy's holding time.** Three-quarters of
candidates resolve inside five minutes *because the stop is three points away*. The hand log's
median trade resolves in ~30 minutes. When the stop widens to something resembling the human's,
this curve stretches — so it cannot be used for time-stop design in its current form. It is
reported because it is the cleanest evidence available that the stop geometry is wrong.

### A. Concurrency and blocking (first-come + one position at a time)

| reading | candidates | traded | per session | blocked | % blocked |
|---|---|---|---|---|---|
| A | 12,595 | 5,763 | 11.96 | 6,832 | **54.2%** |
| B | 5,622 | 3,049 | 6.49 | 2,573 | 45.8% |
| C | 2,766 | 2,026 | 4.46 | 740 | 26.8% |
| D | 1,598 | 1,224 | 3.25 | 374 | 23.4% |

How many candidates a single open position blocks (reading A): median **1**, max **35**;
1,345 positions block exactly one, 515 block two, and a long tail beyond.

Traded-vs-blocked excursion profiles are **near-identical in points** (median MFE 12.86 vs
12.71 under A). First-come selection is not picking better candidates than it discards — but
note this comparison inherits the short-resolution artefact, so it is weaker evidence than it
looks and should be re-derived once the stop geometry is settled.

### Overlap — is the earliest candidate also the strongest?

| reading | time-rank-1 == conviction-rank-1 |
|---|---|
| A | **38.8%** |
| B | 47.7% |
| C | 54.6% |
| D | **65.3%** |

Under the loosest reading the earliest candidate is the highest-conviction one on **fewer than
two sessions in five**. The selector question is therefore *not* small — first-come and
best-conviction disagree on the majority of sessions.

### C. Conviction distribution

§9's score is **3-valued**, not continuous — confluence ≥ 3, with-trend, target ≥ 2R.
Deciles are undefined on a 4-point scale, so it is reported by level:

| reading | score 1 | score 2 | score 3 |
|---|---|---|---|
| A | 8.8% | 65.7% | 25.5% |
| D | 11.8% | 51.3% | 36.9% |

Two-thirds of candidates sit on a single value. **As a ranking key, §9 cannot separate the
population it would be asked to rank** — under reading A it would need to choose 3 from ~8,277
candidates sharing score 2. That is an observation about the score's resolution, not about
whether higher scores perform better; the performance question is quarantined with the rest of
the R-normalised material.

### F. Hygiene

- **Roll contamination: 0 candidates flagged** across all four readings. Roll sessions and the
  session after each are excluded upstream, and no surviving candidate's lookback spans a
  contract change. A clean pass on a hazard worth suspecting.
- **Unresolved at close: 0.4–0.8%.** Negligible.
- **Warm-up treatment: no material difference.** Reading A, `prior` 12,595 candidates vs `rth`
  12,625 — a 0.2% difference, with identical median MFE/MAE in points. Consistent with the
  signal count's −0.8% and confirms the pre-open bias is second-order.
- **Year-to-year: stable.** 2023 and 2024 medians agree to within 3% on every points-denominated
  measure.

---

## 3. Quarantined — do not cite

Computed and present in the parquet, but invalid as characterisations of the opportunity set:

`mfe_R`, `mae_R`, `reached_1R`, `reached_1_5R`, `reached_2R`, `reached_3R`, and analysis **D**
(truncated winners, which returned 29.8–44.1% but is a ratio of two R-normalised quantities).

They are retained rather than deleted so the defect is reproducible and so the fields refill
correctly once the stop geometry is settled. The parquet carries `stop_distance_points`, so
every R field can be recomputed against a corrected stop without re-running the detector.

---

## 4. B. Implementability — recorded as instructed

A **ranking** selector ("highest conviction of the session") requires knowing every candidate
before choosing, which is lookahead and **not tradeable**. Only two forms are implementable in
real time:

1. **first-come** — take the next qualifying candidate
2. **first-to-clear-a-threshold** — take the next candidate whose conviction exceeds a
   pre-committed bar

The conviction-rank slices in the raw output are diagnostic only. **No session-best ranking in
this run is a candidate rule**, and none should be presented as one.

Given §9's 3-level resolution, form 2 collapses toward form 1 in practice: a threshold of
"score ≥ 3" admits 25.5% of candidates under reading A and still leaves the cap binding on
most sessions.

---

## 5. Accounting

| | |
|---|---|
| Candidates characterised | **45,214** (22,581 `prior` + 22,633 `rth`; ×4 readings) |
| Sessions processed | **496** of 539 |
| Sessions skipped | 43 — holiday/short 21, roll 8, session-after-roll 8, mixed contract 6 |
| Sessions failed | **0** |
| Runtime | **1.3 minutes** (20-session probe projected 5.5; single-pass-over-bars for all four readings is what kept it there) |
| Holdout | never addressed; guard armed on every session |
| N_trials | **0** |

**N_trials accounting.** This run is measurement. Any selector decision made *on the basis of
these results* increments N_trials to 1 and must be recorded as such **at the time the decision
is made**, not retrospectively.

## What surprised me

**The stop geometry, and that it survived three gates.** Gate 1 passed sizing using trigger-candle
*range* as a stop proxy — median 9.5–21.5 points by timeframe. The spec's actual entry-to-stop
distance is 3.12 points. Gate 1's verdict is unaffected in direction (a smaller stop is a
smaller loss, so sizing passes more comfortably), but the proxy was measuring a different
quantity than the spec produces, and nothing since caught it. It took computing R per candidate
against a real entry to see that the spec generates stops an order of magnitude tighter than
the human it was derived from.

Two smaller ones. **Blocking is milder than expected** — I anticipated long holds starving the
session, and instead 77% resolve in five minutes, though that is itself the defect showing
through. And **the overlap rate falls as the reading tightens** (38.8% → 65.3% from A to D):
stricter triggers produce fewer, more similar candidates, so first-come and best-conviction
converge. If the selector question is uncomfortable, a tighter trigger reading shrinks it —
which is a real structural relationship between two decisions that looked independent.

---

## Reproducing

```bash
cd research/star-trading/tools
python3 alpha_data.py            # front-month cache (~19s)
python3 vwapbb_opportunity.py    # detector + excursion -> candidates.parquet (~1.3 min)
python3 vwapbb_analyse.py        # all analyses
```

Per-session JSON shards are written under `research/vwap-bb/data/_shards/` and the run is
resumable — a restart skips sessions already written.
