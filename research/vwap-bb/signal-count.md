# SIGNAL COUNT — VWAP/BB frozen spec

**VERDICT: FIRES.** Gate 6 reopens. Not because frequency came in low — it came in
*implausibly high* — but because **the count could not be measured.** The spec's trigger
definition does not determine a signal rate, so gate 6's load-bearing input remains
unestablished. The study design must be revisited before anything is built on it.

Not a backtest. No P&L, no stops, no targets, no equity, no verdict on edge. Workbench only;
the holdout was never addressed and the guard was never invoked. **N_trials remains 0** — a
signal count is a measurement, not a hypothesis test, and it is not logged as a trial.

---

## The headline

| Reading of the trigger rule | signals | per session |
|---|---|---|
| **A** — penetrate cluster top, any wick | 12,348 | **109.27** |
| **B** — penetrate cluster fully, any wick | 5,488 | **48.57** |
| **C** — penetrate fully + wick ≥ 50% of range | 3,906 | **34.57** |
| **D** — as C, plus cluster must hold ≥3 levels | 2,795 | **24.73** |
| *Angus, discretionary, in-scope hand log* | *19* | ***1.00*** |

Probe: 113 workbench sessions. Full 496-session run under reading A gave **93.59/session**,
confirming the probe is representative rather than a small-sample artefact.

**Every reading clears the 0.486 tripwire — by 50× to 225×. That is not reassurance, it is
the problem.** The tightest defensible reading still fires **25× more often** than the human
whose trading the spec was written to formalise.

---

## Why this is a measurement failure, not a result

The first run produced 93.6 signals/session. I did not report that as a finding. Instrumenting
it showed why:

```
7,520  1-minute evaluation bars
13,807 clusters detected          -> 1.84 clusters per bar
median cluster: 2 levels, 6.6 pts span
```

**A cluster exists on essentially every bar.** With 12 candidate levels — BB basis, daily VWAP
mid ±1/2/3σ, NY VWAP mid ±1σ, daily POC — inside a 10-point tolerance on an instrument whose
1-minute range is ~9.5 points, clustering is the default state, not a rare confluence. Early in
the session the daily VWAP σ bands are packed within a few points of each other, so the VWAP
family alone forms a cluster on its own almost continuously.

Given a cluster on every bar, the trigger rule is doing all the selection — and it is not
written tightly enough to do it. §3 says a rejection block is a candle that *"trades into the
cluster"*, *"CLOSES back on the trade side of all cluster levels"*, and *"leaves a wick
through/into them"*. Each phrase admits a range:

- *trades into* — touches the near edge? penetrates fully? penetrates by some depth?
- *leaves a wick* — any wick at all? a wick of material size relative to the bar?

Readings A→D above are all faithful to those words. They span **a factor of 4.4 between
themselves and 25–109× against the human benchmark.** Nothing in the document chooses between
them.

**This is a gate 4 failure that gate 4 did not catch.** Gate 4 tested for *unstated*
parameters and found five, all now frozen. It did not test whether the *stated* rules were
tight enough to determine behaviour. They are not — and the consequence is larger than
anything the five frozen parameters controlled.

---

## Filters not implemented, and why they do not rescue the number

Implemented: cluster detection (10 pt tolerance), rejection block, displacement (body through
≥2 levels, body/range ≥ 0.6, close in extreme quartile), confluence minimum (2 with-trend or
range, 3 counter-trend), HTF flag via 15m fractal N=2, MTF arbitration (highest TF wins on a
shared close minute), RTH 09:36 boundary, roll exclusion.

Not implemented, each of which would only *reduce* the count:

| Filter | Why omitted |
|---|---|
| §6.5 RR floor (skip if target < 1.5R) | Requires target selection from the full menu — that is outcome machinery |
| §7 location (no longs at HTF range top) | Needs HTF range extremes and an unstated threshold |
| §7 invalidation-at-entry | Marked "[Hypothesis — test]", not a settled rule |
| §5.5 T_cancel | Fill logic, not signal detection |
| Vault max 3/day, one-position-at-a-time | Requires trade duration, i.e. outcomes |

So all counts above are **upper bounds**. But the gap is 25–109×: these filters would need to
remove **96–99%** of signals to reach the hand log's rate. They are described as refinements,
not as the primary selector, and there is no reading on which they carry that load.

**A structural consequence worth stating plainly.** If the detector genuinely produces 25+
candidates per session and the Vault takes the first 3, then *the Vault's ordering rule is the
strategy* — and it is unspecified. A system that identifies one or two high-quality setups is
a different thing from one that generates dozens and truncates arbitrarily. The spec is
written as the former; every implementation I can derive from it behaves as the latter.

---

## Distribution, and why it matters for the bootstrap

Under reading A, across 496 workbench sessions:

| signals in session | sessions | share |
|---|---|---|
| 0 | 0 | 0.0% |
| 1 | 0 | 0.0% |
| 2 | 0 | 0.0% |
| **3+** | **496** | **100.0%** |

Maximum in one session: **183**. There is no zero-signal session anywhere in two years — on
its own sufficient to reject the detector as a representation of a strategy whose author
traded on 15 of 19 sessions and skipped days deliberately.

The brief asked whether a mean of 1.0 is built from zeros and clusters, because that changes
the bootstrap. The question cannot be answered: the realised distribution is not a mean of 1.0
in any form.

## By year — stable, which rules out a regime artefact

| year | signals | sessions | per session |
|---|---|---|---|
| 2023 | 22,284 | 237 | 94.03 |
| 2024 | 22,266 | 239 | 93.16 |
| 2025 (Jan) | 1,872 | 20 | 93.60 |

Flat to within 1%. The count is a property of the rule set, not of a particular market regime.

## By time of day (reading A, 30-minute buckets, ET)

| bucket | signals | | bucket | signals |
|---|---|---|---|---|
| 09:30 | 3,973 | | 13:00 | 3,253 |
| 10:00 | **4,819** | | 13:30 | 2,982 |
| 10:30 | 4,172 | | 14:00 | 3,185 |
| 11:00 | 4,076 | | 14:30 | 2,999 |
| 11:30 | 3,727 | | 15:00 | 3,144 |
| 12:00 | 3,491 | | 15:30 | 3,308 |
| 12:30 | 3,107 | | 16:00 | 186 |

Peaks 10:00–10:30 and sags midday — the right *shape*, at the wrong *magnitude*. The detector
is responding to genuine intraday structure; it is simply firing on far too much of it.

## Sessions skipped

| reason | sessions |
|---|---|
| holiday / short session | 21 |
| roll session | 8 |
| session after roll | 8 |
| mixed contract in session | 6 |
| **total skipped** | **43** |

496 of 539 workbench sessions scanned.

## Anomaly candidates, flagged for eyeball rather than accepted

Highest counts: 2024-09-23 (183), 2024-04-16 (173), 2024-07-23 (170), 2023-01-10 (163),
2023-03-24 (159), 2024-03-28 (159), 2024-04-10 (159), 2024-05-29 (159).

These are not outliers against a sane baseline — they are the top of a distribution whose
*median* session already carries ~90 signals. Listed for completeness; the anomaly is the
whole distribution, not these dates.

---

## Warm-up check

Reported twice as requested. **No choice is made between them** — this is a measurement for
the study design.

| variant | signals | per session |
|---|---|---|
| **A** — BB(20)/ATR(20) warmed from prior bars (as currently specified) | 46,422 | **93.593** |
| **B** — BB(20) warmed from RTH bars only, later first-signal bar | 46,021 | **92.784** |
| **difference** | −401 | **−0.81%** |

Anchored VWAPs keep their defined anchors in both variants (18:00 daily, 09:30 NY) — those are
definitions, not warm-up choices. Only the rolling lookback changes.

**The warm-up effect is −0.8%, and almost all of it sits in the 09:30 bucket** (3,973 → 3,554,
−10.5%), which is exactly where the contaminated lookback is. Later buckets are unchanged to
within noise.

This is a genuine, if small, result: the pre-open bias is **real and localised to the first
half hour**, but at −0.8% overall it is not what separates 93 signals from 1. It is a
second-order effect on a first-order problem, and it should be recorded as such rather than
treated as the explanation.

---

## Reconciling the tripwire figure

The brief gives 0.486/session; my last pass computed 0.513. Both are right for different
corrections:

| correction | n at p₁ = 0.50 | tripwire on 539 sessions |
|---|---|---|
| ÷4 (largest axis **after V3 struck**) | 262 | **0.486** |
| ÷5 (largest axis before V3 struck) | 277 | 0.513 |

0.486 follows from the V3 removal flagged in the previous pass — management axis 5 → 4. The
brief's figure is the current one and is used throughout. The distinction does not affect the
verdict: measured counts exceed both by two orders of magnitude.

---

## VERDICT

**FIRES.**

Read literally, every configuration clears 0.486 by 50–225× and gate 6 would hold. **That
reading would be wrong**, and recording it as CLEARS is the exact failure the runbook was
written to prevent — a gate read charitably because the number happened to fall on the
comfortable side.

Gate 6 asks whether the workbench holds enough trades to resolve p₁ = 0.50. That question
takes trade frequency as input. This run establishes that **the frozen spec does not have a
trade frequency** — it has a range spanning 25–109 signals per session depending on how three
phrases in §3 are read, against a human benchmark of 1.0. An input that varies by 100× across
faithful readings is not an input.

Gate 6 therefore reopens, and the study design must be revisited before any backtest is run.

Nothing was tuned to change the count. The sensitivity table exists to characterise the
measurement's dependence on interpretation, not to select among readings — no reading was
adopted, and none should be adopted without an explicit ruling. **N_trials remains 0.**

---

## Reproducing

```bash
cd research/star-trading/tools
python3 alpha_data.py        # front-month cache (~19s)
python3 vwapbb_signals.py    # full workbench scan, both warm-up variants (~20 min)
```

Reading A is what `vwapbb_signals.py` implements. Readings B–D were measured in a probe
harness over 113 sessions; both are described in full above.
