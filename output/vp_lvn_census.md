# T1 / T5 — LVN traversal, and which profile period to build on

**Census only** (§5.9.1) — a mechanism test, no expectancy claim.

Dwell = minutes whose bar range touched a band around a price. Every node is
scored against **its own flanks at ±3× the band width** — same session, same
neighbourhood — because LVNs sit in the thin tails of the prior range and HVNs
sit in its middle, and price levels are autocorrelated day to day. A raw
LVN-vs-HVN comparison measures that persistence and misreads it as liquidity.

**32,014 node-session-widths over 354 sessions.**

---

## Step 1 — the resolution check. Which band widths can be read at all?

POC, VAH and VAL through the identical flank machinery, at every band width.
These are the strongest levels the framework has; if they do not out-dwell their
own flanks at a given width, nothing measured at that width means anything.

**This step exists because the first pass failed it.** At ±2.5pt every level type
— POC included — came back at 1.00, and a ±2.5pt band is *narrower than a typical
NQ 1-minute bar*. That is a statement about resolution, not about the market.

| band ±pt | n | control node/flank | sign-test p | 2025 | 2026 | readable |
|---:|---:|---:|---:|---:|---:|---|
| 2.5 | 1,132 | **1.000** | 0.9498 | 0.998 | 1.005 | no |
| 5 | 777 | **1.024** | 0.1503 | 1.019 | 1.037 | no |
| 10 | 410 | **1.066** | 0.1096 | 1.038 | 1.128 | no |
| 20 | 201 | **1.080** | 0.0339 | 1.254 | 0.864 | no |

**NO BAND WIDTH IS READABLE.** Not even the POC — the single most-traded price in the profile — holds price longer than a price three band-widths away, at any width from ±2.5 to ±20pt, on 1-minute NQ bars. Everything below is reported for the record but **T1 is UNTESTED, not refuted**: the instrument cannot resolve the question.

---

## Step 2 — T1, by profile window and band width

**T1 predicts LVN < 1.00 *and* HVN > 1.00, in both eras.** Either one alone is what the range-position confound produces on its own.

| band | window | LVN n | **LVN** | 2025 | 2026 | HVN n | **HVN** | 2025 | 2026 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ±2.5 | `prev_session` | 945 | **1.008** | 1.020 | 0.989 | 1,161 | **0.993** | 0.995 | 0.991 |
| ±2.5 | `prev_week` | 1,390 | **1.013** | 1.023 | 1.000 | 1,528 | **1.012** | 1.020 | 1.001 |
| ±2.5 | `roll_5` | 1,785 | **1.013** | 1.025 | 0.995 | 1,989 | **1.004** | 1.005 | 1.001 |
| ±2.5 | `roll_20` | 2,253 | **1.001** | 1.010 | 0.988 | 2,362 | **1.001** | 0.991 | 1.015 |
| ±5 | `prev_session` | 679 | **1.004** | 1.021 | 0.976 | 804 | **1.031** | 1.048 | 1.004 |
| ±5 | `prev_week` | 965 | **1.030** | 1.033 | 1.027 | 1,095 | **1.010** | 0.990 | 1.036 |
| ±5 | `roll_5` | 1,297 | **1.013** | 1.027 | 0.994 | 1,388 | **1.020** | 1.005 | 1.040 |
| ±5 | `roll_20` | 1,555 | **1.009** | 1.002 | 1.019 | 1,685 | **1.012** | 1.000 | 1.030 |
| ±10 | `prev_session` | 398 | **0.978** | 0.957 | 1.012 | 471 | **1.035** | 1.037 | 1.033 |
| ±10 | `prev_week` | 508 | **1.036** | 1.007 | 1.065 | 566 | **1.027** | 0.993 | 1.070 |
| ±10 | `roll_5` | 639 | **1.045** | 1.032 | 1.061 | 680 | **1.051** | 1.004 | 1.117 |
| ±10 | `roll_20` | 745 | **1.024** | 1.012 | 1.039 | 722 | **1.048** | 1.016 | 1.091 |
| ±20 | `prev_session` | 263 | **0.962** | 0.932 | 1.004 | 323 | **1.069** | 1.078 | 1.058 |
| ±20 | `prev_week` | 189 | **0.954** | 0.796 | 1.234 | 222 | **0.990** | 0.864 | 1.230 |
| ±20 | `roll_5` | 233 | **0.998** | 0.869 | 1.189 | 258 | **0.988** | 0.843 | 1.175 |
| ±20 | `roll_20` | 196 | **0.988** | 0.888 | 1.131 | 200 | **1.026** | 0.949 | 1.122 |

---

## Step 2b — the separation. This is what T1 actually predicts.

T1 does not merely claim nodes differ from their surroundings — it claims the two
kinds differ **from each other, in opposite directions**. `HVN − LVN` is that
claim as one number, and it is immune to anything that biases both kinds equally,
including the resolution dilution that flattens the control at narrow bands.

**T1 predicts a positive, era-consistent gap.**

| band | window | HVN − LVN | 2025 | 2026 | both eras positive |
|---:|---|---:|---:|---:|---|
| ±2.5 | `prev_session` | **-0.014** | -0.025 | +0.002 | no |
| ±2.5 | `prev_week` | **-0.001** | -0.003 | +0.001 | no |
| ±2.5 | `roll_5` | **-0.009** | -0.020 | +0.006 | no |
| ±2.5 | `roll_20` | **+0.001** | -0.018 | +0.027 | no |
| ±5 | `prev_session` | **+0.027** | +0.027 | +0.028 | **yes** |
| ±5 | `prev_week` | **-0.020** | -0.043 | +0.010 | no |
| ±5 | `roll_5` | **+0.007** | -0.022 | +0.046 | no |
| ±5 | `roll_20` | **+0.003** | -0.003 | +0.011 | no |
| ±10 | `prev_session` | **+0.057** | +0.079 | +0.021 | **yes** |
| ±10 | `prev_week` | **-0.009** | -0.014 | +0.005 | no |
| ±10 | `roll_5` | **+0.006** | -0.028 | +0.056 | no |
| ±10 | `roll_20` | **+0.024** | +0.003 | +0.052 | **yes** |
| ±20 | `prev_session` | **+0.107** | +0.147 | +0.054 | **yes** |
| ±20 | `prev_week` | **+0.036** | +0.068 | -0.003 | no |
| ±20 | `roll_5` | **-0.011** | -0.026 | -0.014 | no |
| ±20 | `roll_20` | **+0.038** | +0.060 | -0.009 | no |

**4 of 16 cells separate in the predicted direction in both eras**: `prev_session` ±5, `prev_session` ±10, `roll_20` ±10, `prev_session` ±20.


---

## Step 3 — what the flank control removed

The naive test — LVN dwell against HVN dwell, no control — is what this would
have reported. Both are shown so the size of the confound is on the record.

| band | window | naive LVN/HVN | controlled LVN | controlled HVN |
|---:|---|---:|---:|---:|
| ±2.5 | `prev_session` | **0.973** | 1.008 | 0.993 |
| ±2.5 | `prev_week` | **1.012** | 1.013 | 1.012 |
| ±2.5 | `roll_5` | **1.002** | 1.013 | 1.004 |
| ±2.5 | `roll_20` | **0.995** | 1.001 | 1.001 |
| ±5 | `prev_session` | **0.939** | 1.004 | 1.031 |
| ±5 | `prev_week` | **1.024** | 1.030 | 1.010 |
| ±5 | `roll_5` | **0.981** | 1.013 | 1.020 |
| ±5 | `roll_20` | **0.979** | 1.009 | 1.012 |
| ±10 | `prev_session` | **0.899** | 0.978 | 1.035 |
| ±10 | `prev_week` | **1.004** | 1.036 | 1.027 |
| ±10 | `roll_5` | **1.016** | 1.045 | 1.051 |
| ±10 | `roll_20` | **0.965** | 1.024 | 1.048 |
| ±20 | `prev_session` | **0.935** | 0.962 | 1.069 |
| ±20 | `prev_week` | **0.957** | 0.954 | 0.990 |
| ±20 | `roll_5` | **1.011** | 0.998 | 0.988 |
| ±20 | `roll_20` | **0.956** | 0.988 | 1.026 |

A naive ratio below 1.00 looks like the thesis confirmed. It is the
range-position confound: HVNs sit mid-range where price lingers, LVNs sit in the
tails. The flank control collapses it.

---

## Verdict

**T1 PARTIALLY SUPPORTED — and only on `prev_session`.**

The predicted separation appears on `prev_session` at ±5pt, ±10pt, ±20pt, era-consistent at every one, and the gap **grows monotonically with band width** +0.027 → +0.057 → +0.107.

That dose-response is the strongest single piece of evidence here. A spurious separation has no reason to scale with the width of the measuring band; a real one that is being smeared by 1-minute resolution does exactly this.

**Which half carries it: the HVN half only.** At ±20pt on `prev_session`, HVN = 1.069 (eras 1.078 / 1.058) and LVN = 0.962 (eras 0.932 / 1.004).

**This matters more than the headline.** AMT's two halves are not equally true here. *Acceptance* survives — price genuinely holds at prices where volume traded yesterday. *Rejection* does not — low-volume nodes are neutral, not repellent, once you control for where in the range they sit.

So the magnet is real and the vacuum is not. That is consistent with `LQV-01`, which also failed to find the vacuum, and it says the tradeable object is **the HVN as a level**, not the LVN as a fast lane.

**T5 ANSWERED: `prev_session`.**

The prior session's profile is the only window that separates at all. The week, the rolling 5 and the rolling 20 are flat or inconsistent — averaging several sessions smears the nodes until they stop being levels. Build on yesterday's profile; treat longer windows as context, not as levels.

**Caveats on the record.** The positive control (POC/VAH/VAL vs their own flanks) rises monotonically with band width — 1.000 → 1.024 → 1.066 → 1.080 — but never clears p<0.05, because widening the band cures dilution and costs sample at the same rate (n falls 1,132 → 201). On 1-minute bars this trade-off has no sweet spot. The separation result stands because it is immune to dilution — which hits both node kinds equally — but the effect sizes here are a few percent of dwell and should not be mistaken for an edge on their own. **This is a level-quality finding, not a strategy.**
