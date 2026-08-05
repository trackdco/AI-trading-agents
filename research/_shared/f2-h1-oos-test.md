---
date: 2026-08-07
kind: STAGE 4 — pooled pre-registered F2 / H1 out-of-sample test
status: ⛔ HALTED AT STEP 0. The statistical test was NOT run.
script: scripts/f2_lookahead_audit.py
cards: [ash-unicorn-sb, zxck-10am-keyopen, orb-fvg-nyopen]
---

# Stage 4 — pooled F2 / H1 test: **HALTED AT STEP 0**

The brief ordered a look-ahead audit of `retrace_ratio` and `disp_delta_magnitude` **before** any
statistics, with a standing instruction:

> *"If either feature touches post-entry data on any card, STOP and report it — that would
> invalidate every F2 result to date, including the original ash-unicorn-sb finding."*

**It does. The audit failed. No H2 or H1 statistic was computed, and none appears below.**

---

## STEP 0 — the look-ahead audit

### The exact time boundary each feature reads up to

Read from the three implementations, not from their comments:

| card | displacement window | retracement window | F1 normaliser |
|---|---|---|---|
| `ash-unicorn-sb` | `[FVG start bar, MSS break bar]` | `(MSS break bar, **ENTRY BAR**]` | session median minute volume `[window open, **ENTRY BAR**]` |
| `zxck-10am-keyopen` | `[manipulation bar, close-through bar]` | `(close-through bar, **ENTRY BAR**]` | same shape |
| `orb-fvg-nyopen` | `[breakout bar, FVG third bar]` | `(FVG third bar, **ENTRY BAR**]` | same shape |

**All three end the retracement window at and *including* the entry minute.**

### The weaker question, which passes

*Does any window read a bar AFTER the entry bar?* **No.** The runtime asserts in all three scripts
are correct and they hold. If that were the only question, the features would be clean.

### The stronger question, which fails

*Does any window read data that did not exist AT THE ENTRY INSTANT?* **Yes, on all three cards.**

Footprint data is aggregated **per minute** (`ts_minute` — verified: the raw files carry no
sub-minute timestamp). The entry is an **intrabar limit fill**. So the entry minute's bucket spans
the fill, and including it in full pulls in **up to 59 seconds of post-fill tape.**

### How much of F2 is exposed

| card | n with F2 | median retracement length | trades where retracement = **1 minute** | share of retracement volume from the entry minute (mean / p50) |
|---|---|---|---|---|
| `ash-unicorn-sb` | 19 | 2 min | **3 of 19** | 40.2% / **24.9%** |
| `zxck-10am-keyopen` | 115 | **1 min** | **84 of 115 (73%)** | 82.0% / **100.0%** |
| `orb-fvg-nyopen` (locked arm) | 1558 | **1 min** | **784 of 1558 (50%)** | 65.1% / **100.0%** |

**On 73% of `zxck-10am-keyopen` trades and 50% of `orb-fvg-nyopen` trades, the retracement window
is a single minute — the entry minute — so 100% of F2's numerator is drawn from the bucket the
fill happened inside.** The split between pre-fill and post-fill volume within that minute is
**unknowable from the data we hold.**

### Can it be repaired by excluding the entry minute?

**No — for most trades there is nothing left.**

| card | F2_strict defined | becomes undefined | crosses the 1.0 threshold | Spearman ρ (F2 vs F2_strict) |
|---|---|---|---|---|
| `ash-unicorn-sb` | 16 | 3 | 3 | 0.909 |
| `zxck-10am-keyopen` | **31** | **84** | 3 | 0.952 |
| `orb-fvg-nyopen` | **774** | **784** | 47 | 0.988 |

> ### ⚠️ Do not read the high ρ as reassurance. It is a selection artefact.
> ρ can only be computed where `F2_strict` **exists** — i.e. on trades whose retracement lasted
> **two or more minutes**, which are precisely the **least contaminated** trades. The correlation
> is high on the clean subset and **undefined on the dirty one**. It says nothing about the 84 and
> 784 trades that are the problem.

### F1 / `disp_delta_magnitude` — nearly clean, but not clean

| card | displacement window touching the entry minute | session minutes to entry (p50) | normaliser shift if the entry minute is excluded (p50 / max) |
|---|---|---|---|
| `ash-unicorn-sb` | **0 of 24** | 12 | 2.65% / 12.5% |
| `zxck-10am-keyopen` | **0 of 115** | 6 | 4.54% / 30.1% |
| `orb-fvg-nyopen` | **0 of 1558** | 35 | 1.04% / 19.2% |

**F1's numerator is clean on every trade of every card** — the displacement leg always closes
before the entry minute. Its **denominator is not**: the session median minute volume is taken up
to *and including* the entry minute, which moves F1 by a median 1.0–4.5% and by as much as 30%.

**This one is trivially repairable** — drop the entry minute from the normaliser; 6–35 minutes
remain. It is reported rather than silently fixed because **re-specifying a pre-registered feature
mid-test is exactly the move this protocol exists to prevent.**

---

## ⛔ VERDICT ON STEP 0 — the test may not proceed

**`retrace_ratio` is not a pre-entry feature.** A rule of the form *"take the trade if F2 < 1.0"*
is **not implementable**: at the moment the limit fills you do not yet know the entry minute's
volume. It becomes knowable only at that minute's close, up to 59 seconds later.

**And the contamination is not neutral — it biases toward FALSE POSITIVES.** The entry minute's
volume is mechanically related to what price did immediately after the fill, which is related to
whether the trade reached target or stop. An association between F2 and outcome can therefore be
manufactured by the measurement itself.

### What this does and does not overturn

| result | effect of the defect |
|---|---|
| **The original `ash-unicorn-sb` F2 finding** (52.6% → 72.7% WR, filtered arm n=11) | ⚠️ **SERIOUSLY UNDERMINED.** It is a *positive* discrimination result on a contaminated feature, which is exactly what this contamination can manufacture. It is also the least contaminated card (24.9% median) and the smallest sample, so neither the defect nor the data settles it. **Treat as unproven.** |
| **The H2 out-of-sample FAILURE on `zxck-10am-keyopen`** (rev b: ordering not observed, p=0.9105, δ +0.235) | ✅ **STANDS, and stands more firmly.** The contamination should have *helped* H2 succeed. It failed anyway, on the most contaminated card in the set. A negative result under a bias favouring positives is stronger than it looked. |
| **Every card's R, expectancy, bound and verdict** | **UNAFFECTED.** Flow was computed and applied to nothing on all three cards. No baseline, funnel, bound or verdict reads F1 or F2. |

**No pre-registered statistic was computed.** The three-bucket medians, the filter-form table,
H1 medians, Holm correction, Cliff's delta and the power calculation are all **absent by
instruction**, not by omission.

---

## What was locked before the halt — preserved for whoever resumes

### STEP 1 — the ORB primary arm, locked before any F2 result was inspected

`orb-fvg-nyopen` has four arms. **One primary arm was fixed on grounds independent of F2** — the
most standard reading of the posted rules:

> ## `arm_brk = close` · `arm_entry = retrace` · `arm_stop = fvg`

Recorded in `scripts/f2_lookahead_audit.py` as `ORB_ARM`, and used for every figure above. The
other three arms are **sensitivity only** and may never be substituted for it.

*Grounds, all independent of any outcome:* retrace-into-the-FVG is the standard ICT reading of
"enter on confirmation" and is the only one of the two entry readings for which F2 **exists at
all** (formation entry has an empty retracement window by construction); the 3-bar FVG stop is the
structural reading of "that candle" that is not arithmetically degenerate; close-through is the
only breakout reading that produces no ambiguous sessions.

### STEP 2 — sample construction, as it would have run

| set | composition | raw n | sessions (effective n) | independence |
|---|---|---|---|---|
| **PRIMARY** (out-of-sample) | `zxck-10am-keyopen` decidable + `orb-fvg-nyopen` locked arm | **1673** | **403** | see below |
| **SECONDARY** (contaminated) | + `ash-unicorn-sb`'s 19 | 1692 | 422 | the hypothesis was born on the ash trades |

**The raw n is a fiction and would have been reported as one.** `orb-fvg-nyopen` fires **5.4
setups per session** into a single 60-minute window, overlapping, mostly same-direction. Its 1558
rows carry roughly **288 sessions** of information. `zxck-10am-keyopen` is one trade per session,
so its 115 are 115.

**Effective n ≈ 403, not 1673 — the clustering discards about 76% of the apparent sample.** All
inference was to be clustered on session date, per dataset as well as pooled, precisely because a
pooled average can hide two cards behaving oppositely.

---

## NEW HYPOTHESES LOGGED — untested, for future data

Recorded so nothing found here leaks into a test it was not pre-registered for.

**N1 · A sub-minute-clean retracement feature.** F2 measured on trades-level data with the
retracement window closing at the **fill timestamp** rather than the fill *minute*. **Requires a
raw tick/trades pull** — every footprint file we hold is minute-aggregated. **Untested. This is
the only thing that would settle H2 properly.**

**N2 · Retracement DURATION as a feature in its own right.** The audit incidentally shows that
retracement length varies enormously between cards (p50 of 1 minute on two cards, 2 on the third)
and that a one-minute retracement is the majority case on both out-of-sample cards. Whether a
fast retracement differs in outcome from a slow one **was never a hypothesis, has not been
tested, and must not be read off this document.** **Untested.**

**N3 · F1 with a clean normaliser.** Exclude the entry minute from the session median. Cheap,
and it makes `disp_delta_magnitude` genuinely pre-entry. **Untested — a re-specification of a
pre-registered feature, so it needs its own prereg.**

---

## What would settle H2

**Raw NQ trade data with timestamps, for the trades in these three logs.** With it, the
retracement window can close at the fill instant and F2 becomes a real pre-entry feature.
Without it, **H2 cannot be tested at any sample size** — the effective n of 403 assembled here is
ample, and it is not the binding constraint. The data is.
